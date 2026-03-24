"""Background coach loop — periodically runs the proactive agent."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from pathlib import Path

from agent.proactive import create_proactive_agent
from services.llm_manager import get_available_models
from services.notifications import send_notification
from storage import commitments as commitments_db
from storage import conversations as conv_db
from storage import diary as diary_db
from storage import goals as goals_db
from storage import memory as memory_db
from storage import notes as notes_db
from storage import nudges as nudges_db
from storage import scheduled_tasks as tasks_db
from storage import settings as settings_db

logger = logging.getLogger("coach_loop")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _handler = logging.FileHandler(str(Path.home() / ".ai_coach" / "coach_loop.log"))
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)

DEFAULT_HEARTBEAT = 900  # 15 minutes


class CoachLoop:
    def __init__(self, on_nudge: Callable[[int], Awaitable[None]]):
        self._on_nudge = on_nudge
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()

    async def _loop(self) -> None:
        try:
            await self._tick()
        except Exception:
            logger.exception("initial tick failed")

        while True:
            try:
                interval = await self._get_interval()
                await asyncio.sleep(interval)
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("tick failed")

    async def _get_interval(self) -> int:
        raw = await settings_db.get("heartbeat_interval")
        if raw:
            try:
                return int(raw)
            except ValueError:
                pass
        return DEFAULT_HEARTBEAT

    async def _tick(self) -> None:
        logger.info("tick starting...")

        # Check if proactive coaching is enabled
        enabled = await settings_db.get("proactive_enabled")
        if enabled == "false":
            logger.info("skipped: proactive coaching disabled")
            return

        # Check quiet hours
        if await self._in_quiet_hours():
            logger.info("skipped: quiet hours")
            return

        # Check if any LLM provider is available
        models = get_available_models()
        if not models:
            logger.info("skipped: no LLM providers available")
            return

        # Get fired scheduled tasks
        fired_tasks = await tasks_db.get_pending()
        logger.info(f"found {len(fired_tasks)} pending tasks, models: {models[:2]}")

        # Build context snapshot for the proactive agent
        context = await self._build_context(fired_tasks)

        # Call the proactive agent
        model = await settings_db.get("default_model")
        logger.info(f"calling proactive agent with model={model or models[0]}")
        agent = create_proactive_agent(model or models[0])
        result = await agent.run(context)
        decision = result.output
        logger.info(f"decision: {len(decision.nudges)} nudges, {len(decision.schedule)} scheduled, {len(decision.discard_task_ids)} discarded")

        # Process discarded tasks
        for task_id in decision.discard_task_ids:
            await tasks_db.update_status(task_id, "cancelled")

        # Mark fired tasks as fired
        for task in fired_tasks:
            await tasks_db.update_status(task["id"], "fired")

        # Create new scheduled tasks
        for sched in decision.schedule:
            await tasks_db.create(
                wake_at=sched.wake_at,
                context=sched.context,
                source=sched.source,
                related_goal_id=sched.related_goal_id,
            )

        # Create nudges (with deduplication)
        new_nudge_count = 0
        for nudge in decision.nudges:
            # Dedup: skip if a similar nudge is already pending
            fragment = nudge.message[:60]
            if await nudges_db.has_similar_pending(fragment):
                continue
            nudge_id = await nudges_db.create(
                message=nudge.message,
                chat_context=nudge.chat_context,
                priority=nudge.priority,
            )
            new_nudge_count += 1
            await send_notification("AI Career Coach", nudge.message)

        if new_nudge_count > 0:
            count = await nudges_db.count_pending()
            await self._on_nudge(count)

    async def _in_quiet_hours(self) -> bool:
        start = await settings_db.get("quiet_hours_start")
        end = await settings_db.get("quiet_hours_end")
        if not start or not end:
            return False
        try:
            now = datetime.now().time()
            s = datetime.strptime(start, "%H:%M").time()
            e = datetime.strptime(end, "%H:%M").time()
            if s <= e:
                return s <= now <= e
            else:
                # Crosses midnight (e.g., 22:00 - 07:00)
                return now >= s or now <= e
        except ValueError:
            return False

    async def _build_context(self, fired_tasks: list[dict]) -> str:
        now = datetime.now()
        parts = [
            f"Current time: {now.isoformat()} ({now.strftime('%A')})",
        ]

        # Last conversation timestamp
        convs = await conv_db.get_all(limit=1)
        if convs:
            parts.append(f"Last conversation: {convs[0]['started_at']}")
        else:
            parts.append("Last conversation: never")

        # Active goals
        goals = await goals_db.get_active()
        if goals:
            goal_lines = [f"  - [{g['id']}] {g['title']} (P{g['priority']}, {g['category']})" for g in goals]
            parts.append("Active goals:\n" + "\n".join(goal_lines))
        else:
            parts.append("Active goals: none")

        # Pending commitments
        commitments = await commitments_db.get_pending()
        if commitments:
            cl = [f"  - {c['what']}" + (f" (due {c['due_date']})" if c['due_date'] else "") for c in commitments]
            parts.append("Pending commitments:\n" + "\n".join(cl))

        # Overdue commitments
        overdue = await commitments_db.get_overdue()
        if overdue:
            ol = [f"  - {c['what']} (was due {c['due_date']})" for c in overdue]
            parts.append("OVERDUE commitments:\n" + "\n".join(ol))

        # Recent memories
        memories = await memory_db.get_recent(days=7)
        if memories:
            ml = [f"  - {m['content']}" for m in memories]
            parts.append("Recent memories (7 days):\n" + "\n".join(ml))

        # Recent diary entries
        entries = await diary_db.get_recent(days=3)
        if entries:
            dl = [f"  - [{e['date']}] {e['mood']}: {e['content'][:150]}" for e in entries]
            parts.append("Recent diary (3 days):\n" + "\n".join(dl))

        # Reference notes (all — persistent reference docs, not time-scoped)
        notes = await notes_db.get_all(limit=20)
        if notes:
            nl = [f"  - [#{n['id']}] {n['title']}: {n['content'][:200]}" for n in notes]
            parts.append("Reference notes:\n" + "\n".join(nl))

        # Fired scheduled tasks
        if fired_tasks:
            tl = [f"  - [id={t['id']}] {t['context']} (source: {t['source']})" for t in fired_tasks]
            parts.append("Fired scheduled tasks (your previous wake-ups):\n" + "\n".join(tl))

        return "\n\n".join(parts)
