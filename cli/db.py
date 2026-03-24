#!/usr/bin/env python3
"""CLI wrapper for AI Coach storage layer. Outputs JSON for Claude Code integration."""

import argparse
import asyncio
import json
import sys
import os
from datetime import date, datetime

# Add project root and venv site-packages to path so we can run without activating venv
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
_venv_site = os.path.join(_project_root, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(1, _venv_site)

from storage import goals as goals_db
from storage import memory as memory_db
from storage import diary as diary_db
from storage import notes as notes_db
from storage import commitments as commitments_db
from storage import nudges as nudges_db
from storage import scheduled_tasks as tasks_db
from storage import conversations as conv_db
from storage.database import close_db


def output(data):
    print(json.dumps(data, default=str, ensure_ascii=False, indent=2))


async def run(args):
    try:
        result = await dispatch(args)
        output(result)
    finally:
        await close_db()


async def dispatch(args):
    domain = args.domain
    action = args.action

    # --- Goals ---
    if domain == "goals":
        if action == "list":
            return await goals_db.get_all() if args.all else await goals_db.get_active()
        elif action == "get":
            return await goals_db.get_by_id(args.id)
        elif action == "create":
            gid = await goals_db.create(
                title=args.title,
                description=args.description or "",
                category=args.category or "",
                priority=args.priority or 3,
            )
            return {"id": gid, "status": "created"}
        elif action == "update":
            fields = {}
            if args.title is not None:
                fields["title"] = args.title
            if args.description is not None:
                fields["description"] = args.description
            if args.category is not None:
                fields["category"] = args.category
            if args.priority is not None:
                fields["priority"] = args.priority
            if args.is_active is not None:
                fields["is_active"] = args.is_active
            await goals_db.update(args.id, **fields)
            return {"id": args.id, "status": "updated"}
        elif action == "delete":
            await goals_db.delete(args.id)
            return {"id": args.id, "status": "deleted"}

    # --- Memories ---
    elif domain == "memories":
        if action == "list":
            return await memory_db.get_all(limit=args.limit or 100)
        elif action == "recent":
            return await memory_db.get_recent(days=args.days or 14)
        elif action == "search":
            return await memory_db.search(args.query)
        elif action == "add":
            mid = await memory_db.create(
                content=args.content,
                source=args.source or "user_added",
                tags=args.tags or "",
            )
            return {"id": mid, "status": "created"}
        elif action == "delete":
            await memory_db.delete(args.id)
            return {"id": args.id, "status": "deleted"}

    # --- Diary ---
    elif domain == "diary":
        if action == "list":
            return await diary_db.get_all(limit=args.limit or 50)
        elif action == "recent":
            return await diary_db.get_recent(days=args.days or 7)
        elif action == "get-by-date":
            return await diary_db.get_by_date(date.fromisoformat(args.date))
        elif action == "get":
            return await diary_db.get_by_id(args.id)
        elif action == "create":
            eid = await diary_db.create(
                entry_date=date.fromisoformat(args.date),
                content=args.content,
                mood=args.mood or "",
                title=args.title or "",
            )
            return {"id": eid, "status": "created"}
        elif action == "update":
            kwargs = {}
            if args.content is not None:
                kwargs["content"] = args.content
            if args.mood is not None:
                kwargs["mood"] = args.mood
            if args.title is not None:
                kwargs["title"] = args.title
            await diary_db.update(args.id, **kwargs)
            return {"id": args.id, "status": "updated"}
        elif action == "delete":
            await diary_db.delete(args.id)
            return {"id": args.id, "status": "deleted"}

    # --- Notes ---
    elif domain == "notes":
        if action == "list":
            return await notes_db.get_all(limit=args.limit or 100)
        elif action == "search":
            return await notes_db.search(args.query)
        elif action == "get":
            return await notes_db.get_by_id(args.id)
        elif action == "create":
            nid = await notes_db.create(
                title=args.title,
                content=args.content or "",
                tags=args.tags or "",
            )
            return {"id": nid, "status": "created"}
        elif action == "update":
            kwargs = {}
            if args.title is not None:
                kwargs["title"] = args.title
            if args.content is not None:
                kwargs["content"] = args.content
            if args.tags is not None:
                kwargs["tags"] = args.tags
            await notes_db.update(args.id, **kwargs)
            return {"id": args.id, "status": "updated"}
        elif action == "delete":
            await notes_db.delete(args.id)
            return {"id": args.id, "status": "deleted"}

    # --- Commitments ---
    elif domain == "commitments":
        if action == "pending":
            return await commitments_db.get_pending()
        elif action == "overdue":
            return await commitments_db.get_overdue()
        elif action == "list":
            return await commitments_db.get_all(limit=args.limit or 50)
        elif action == "create":
            cid = await commitments_db.create(
                what=args.what,
                due_date=args.due_date,
            )
            return {"id": cid, "status": "created"}
        elif action == "complete":
            await commitments_db.complete(args.id)
            return {"id": args.id, "status": "done"}
        elif action == "miss":
            await commitments_db.miss(args.id)
            return {"id": args.id, "status": "missed"}
        elif action == "cancel":
            await commitments_db.cancel(args.id)
            return {"id": args.id, "status": "cancelled"}

    # --- Nudges ---
    elif domain == "nudges":
        if action == "pending":
            return await nudges_db.get_pending()
        elif action == "history":
            return await nudges_db.get_history(limit=args.limit or 50)
        elif action == "snooze":
            await nudges_db.snooze(args.id, args.until)
            return {"id": args.id, "status": "snoozed", "until": args.until}
        elif action == "dismiss":
            await nudges_db.dismiss(args.id)
            return {"id": args.id, "status": "dismissed"}

    # --- Scheduled Tasks ---
    elif domain == "tasks":
        if action == "pending":
            return await tasks_db.get_pending()
        elif action == "create":
            tid = await tasks_db.create(
                wake_at=args.wake_at,
                context=args.context,
                source=args.source or "cli",
            )
            return {"id": tid, "status": "created"}
        elif action == "cancel":
            await tasks_db.cancel(args.id)
            return {"id": args.id, "status": "cancelled"}

    # --- Context ---
    elif domain == "context":
        if action == "snapshot":
            return await build_context_snapshot()

    return {"error": f"Unknown command: {domain} {action}"}


async def build_context_snapshot():
    """Build aggregated coaching context — mirrors CoachLoop._build_context()."""
    now = datetime.now()
    snapshot = {
        "timestamp": now.isoformat(),
        "day_of_week": now.strftime("%A"),
    }

    # Last conversation
    convs = await conv_db.get_all(limit=1)
    snapshot["last_conversation"] = convs[0]["started_at"] if convs else None

    # Active goals
    snapshot["active_goals"] = await goals_db.get_active()

    # Commitments
    snapshot["pending_commitments"] = await commitments_db.get_pending()
    snapshot["overdue_commitments"] = await commitments_db.get_overdue()

    # Recent memories (7 days, high relevance)
    snapshot["recent_memories"] = await memory_db.get_recent(days=7)

    # Recent diary (3 days)
    snapshot["recent_diary"] = await diary_db.get_recent(days=3)

    # Reference notes
    snapshot["notes"] = await notes_db.get_all(limit=20)

    # Pending scheduled tasks
    snapshot["fired_tasks"] = await tasks_db.get_pending()

    # Pending nudges
    snapshot["pending_nudges"] = await nudges_db.get_pending()

    return snapshot


def build_parser():
    parser = argparse.ArgumentParser(description="AI Coach CLI — database operations")
    sub = parser.add_subparsers(dest="domain", required=True)

    # --- Goals ---
    goals = sub.add_parser("goals")
    goals_sub = goals.add_subparsers(dest="action", required=True)

    g_list = goals_sub.add_parser("list")
    g_list.add_argument("--all", action="store_true", help="Include archived goals")

    g_get = goals_sub.add_parser("get")
    g_get.add_argument("id", type=int)

    g_create = goals_sub.add_parser("create")
    g_create.add_argument("--title", required=True)
    g_create.add_argument("--description")
    g_create.add_argument("--category")
    g_create.add_argument("--priority", type=int)

    g_update = goals_sub.add_parser("update")
    g_update.add_argument("id", type=int)
    g_update.add_argument("--title")
    g_update.add_argument("--description")
    g_update.add_argument("--category")
    g_update.add_argument("--priority", type=int)
    g_update.add_argument("--is_active", type=int, choices=[0, 1])

    g_delete = goals_sub.add_parser("delete")
    g_delete.add_argument("id", type=int)

    # --- Memories ---
    memories = sub.add_parser("memories")
    mem_sub = memories.add_subparsers(dest="action", required=True)

    m_list = mem_sub.add_parser("list")
    m_list.add_argument("--limit", type=int)

    m_recent = mem_sub.add_parser("recent")
    m_recent.add_argument("--days", type=int)

    m_search = mem_sub.add_parser("search")
    m_search.add_argument("query")

    m_add = mem_sub.add_parser("add")
    m_add.add_argument("--content", required=True)
    m_add.add_argument("--tags")
    m_add.add_argument("--source")

    m_delete = mem_sub.add_parser("delete")
    m_delete.add_argument("id", type=int)

    # --- Diary ---
    diary = sub.add_parser("diary")
    diary_sub = diary.add_subparsers(dest="action", required=True)

    d_list = diary_sub.add_parser("list")
    d_list.add_argument("--limit", type=int)

    d_recent = diary_sub.add_parser("recent")
    d_recent.add_argument("--days", type=int)

    d_get_date = diary_sub.add_parser("get-by-date")
    d_get_date.add_argument("date")

    d_get = diary_sub.add_parser("get")
    d_get.add_argument("id", type=int)

    d_create = diary_sub.add_parser("create")
    d_create.add_argument("--date", required=True)
    d_create.add_argument("--content", required=True)
    d_create.add_argument("--mood")
    d_create.add_argument("--title")

    d_update = diary_sub.add_parser("update")
    d_update.add_argument("id", type=int)
    d_update.add_argument("--content")
    d_update.add_argument("--mood")
    d_update.add_argument("--title")

    d_delete = diary_sub.add_parser("delete")
    d_delete.add_argument("id", type=int)

    # --- Notes ---
    notes = sub.add_parser("notes")
    notes_sub = notes.add_subparsers(dest="action", required=True)

    n_list = notes_sub.add_parser("list")
    n_list.add_argument("--limit", type=int)

    n_search = notes_sub.add_parser("search")
    n_search.add_argument("query")

    n_get = notes_sub.add_parser("get")
    n_get.add_argument("id", type=int)

    n_create = notes_sub.add_parser("create")
    n_create.add_argument("--title", required=True)
    n_create.add_argument("--content")
    n_create.add_argument("--tags")

    n_update = notes_sub.add_parser("update")
    n_update.add_argument("id", type=int)
    n_update.add_argument("--title")
    n_update.add_argument("--content")
    n_update.add_argument("--tags")

    n_delete = notes_sub.add_parser("delete")
    n_delete.add_argument("id", type=int)

    # --- Commitments ---
    commitments = sub.add_parser("commitments")
    commit_sub = commitments.add_subparsers(dest="action", required=True)

    commit_sub.add_parser("pending")
    commit_sub.add_parser("overdue")

    c_list = commit_sub.add_parser("list")
    c_list.add_argument("--limit", type=int)

    c_create = commit_sub.add_parser("create")
    c_create.add_argument("--what", required=True)
    c_create.add_argument("--due_date")

    c_complete = commit_sub.add_parser("complete")
    c_complete.add_argument("id", type=int)

    c_miss = commit_sub.add_parser("miss")
    c_miss.add_argument("id", type=int)

    c_cancel = commit_sub.add_parser("cancel")
    c_cancel.add_argument("id", type=int)

    # --- Nudges ---
    nudges = sub.add_parser("nudges")
    nudge_sub = nudges.add_subparsers(dest="action", required=True)

    nudge_sub.add_parser("pending")

    nu_history = nudge_sub.add_parser("history")
    nu_history.add_argument("--limit", type=int)

    nu_snooze = nudge_sub.add_parser("snooze")
    nu_snooze.add_argument("id", type=int)
    nu_snooze.add_argument("--until", required=True)

    nu_dismiss = nudge_sub.add_parser("dismiss")
    nu_dismiss.add_argument("id", type=int)

    # --- Scheduled Tasks ---
    tasks = sub.add_parser("tasks")
    tasks_sub = tasks.add_subparsers(dest="action", required=True)

    tasks_sub.add_parser("pending")

    t_create = tasks_sub.add_parser("create")
    t_create.add_argument("--wake_at", required=True)
    t_create.add_argument("--context", required=True)
    t_create.add_argument("--source")

    t_cancel = tasks_sub.add_parser("cancel")
    t_cancel.add_argument("id", type=int)

    # --- Context ---
    context = sub.add_parser("context")
    ctx_sub = context.add_subparsers(dest="action", required=True)
    ctx_sub.add_parser("snapshot")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run(args))
