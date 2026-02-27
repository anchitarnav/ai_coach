"""Notifications view — browse and act on coach nudges."""

from datetime import datetime, timedelta

import flet as ft

from storage import nudges as nudges_db
from ui import theme


def _snooze_until(option: str) -> str:
    now = datetime.now()
    if option == "1 hour":
        return (now + timedelta(hours=1)).isoformat()
    elif option == "4 hours":
        return (now + timedelta(hours=4)).isoformat()
    elif option == "Tomorrow 9 AM":
        tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        return tomorrow.isoformat()
    elif option == "Next week":
        days_ahead = 7 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_mon = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        return next_mon.isoformat()
    return (now + timedelta(hours=1)).isoformat()


def _status_icon(status: str) -> ft.Icon:
    icons = {
        "acted_on": (ft.Icons.CHECK_CIRCLE, theme.SUCCESS),
        "dismissed": (ft.Icons.CANCEL_OUTLINED, theme.TEXT_MUTED),
        "snoozed": (ft.Icons.SNOOZE, theme.WARNING),
        "shown": (ft.Icons.VISIBILITY, theme.ACCENT),
        "pending": (ft.Icons.CIRCLE_OUTLINED, theme.PRIMARY),
    }
    name, color = icons.get(status, (ft.Icons.CIRCLE_OUTLINED, theme.TEXT_MUTED))
    return ft.Icon(name, size=16, color=color)


class NotificationsView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
        self._page_ref = page_ref

        self.pending_list = ft.Column(spacing=8)
        self.history_list = ft.Column(spacing=6)

        self.controls = [
            ft.Container(
                content=ft.Column(
                    spacing=theme.SECTION_GAP,
                    controls=[
                        theme.heading("Notifications", size=24),
                        theme.section_divider(),

                        theme.subheading("Pending", size=17),
                        self.pending_list,

                        theme.section_divider(),

                        theme.subheading("History", size=17),
                        self.history_list,
                    ],
                ),
                padding=ft.Padding(
                    left=theme.PAGE_PAD, right=theme.PAGE_PAD,
                    top=theme.PAGE_PAD, bottom=40,
                ),
            )
        ]

    def did_mount(self):
        self._page_ref.run_task(self._load_nudges)

    async def refresh(self):
        await self._load_nudges()

    async def _load_nudges(self):
        # Pending nudges
        pending = await nudges_db.get_pending()
        self.pending_list.controls.clear()
        if not pending:
            self.pending_list.controls.append(
                ft.Text("No pending notifications", size=13, color=theme.TEXT_MUTED, italic=True)
            )
        for n in pending:
            self.pending_list.controls.append(self._build_pending_card(n))

        # History
        history = await nudges_db.get_history(limit=30)
        # Filter out ones already shown in pending
        pending_ids = {n["id"] for n in pending}
        history = [h for h in history if h["id"] not in pending_ids]
        self.history_list.controls.clear()
        if not history:
            self.history_list.controls.append(
                ft.Text("No past notifications", size=13, color=theme.TEXT_MUTED, italic=True)
            )
        for n in history:
            self.history_list.controls.append(self._build_history_row(n))

        self.update()

    def _build_pending_card(self, nudge: dict) -> ft.Control:
        fg, bg = theme.PRIORITY_COLORS.get(nudge["priority"], theme.PRIORITY_COLORS["gentle"])

        talk_btn = ft.Button(
            "Let's talk",
            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
            on_click=lambda e, n=nudge: self._on_talk(n),
            color=theme.PRIMARY,
            style=ft.ButtonStyle(padding=ft.Padding(left=12, right=12, top=0, bottom=0)),
        )
        snooze_btn = ft.PopupMenuButton(
            content=ft.Text("Snooze", size=13, color=theme.TEXT_SECONDARY),
            items=[
                ft.PopupMenuItem(content="1 hour", on_click=lambda e, n=nudge: self._page_ref.run_task(self._on_snooze, n["id"], "1 hour")),
                ft.PopupMenuItem(content="4 hours", on_click=lambda e, n=nudge: self._page_ref.run_task(self._on_snooze, n["id"], "4 hours")),
                ft.PopupMenuItem(content="Tomorrow 9 AM", on_click=lambda e, n=nudge: self._page_ref.run_task(self._on_snooze, n["id"], "Tomorrow 9 AM")),
                ft.PopupMenuItem(content="Next week", on_click=lambda e, n=nudge: self._page_ref.run_task(self._on_snooze, n["id"], "Next week")),
            ],
        )
        dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=theme.TEXT_MUTED,
            tooltip="Dismiss",
            on_click=lambda e, n=nudge: self._page_ref.run_task(self._on_dismiss, n["id"]),
        )

        timestamp = ft.Text(
            nudge["created_at"][:16] if nudge.get("created_at") else "",
            size=11, color=theme.TEXT_MUTED,
        )

        return theme.card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            theme.pill(nudge["priority"], fg, bg),
                            timestamp,
                        ],
                        spacing=8,
                    ),
                    ft.Text(nudge["message"], size=14, color=theme.TEXT),
                    ft.Row(
                        controls=[talk_btn, snooze_btn, dismiss_btn],
                        spacing=8,
                    ),
                ],
            )
        )

    def _build_history_row(self, nudge: dict) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                controls=[
                    _status_icon(nudge["status"]),
                    ft.Text(
                        nudge["message"], size=13, color=theme.TEXT_SECONDARY,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
                    ),
                    ft.Text(
                        nudge["status"].replace("_", " "),
                        size=11, color=theme.TEXT_MUTED,
                    ),
                    ft.Text(
                        nudge["created_at"][:10] if nudge.get("created_at") else "",
                        size=11, color=theme.TEXT_MUTED,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=8, right=8, top=6, bottom=6),
            border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER)),
        )

    def _on_talk(self, nudge: dict):
        self._page_ref.run_task(nudges_db.act_on, nudge["id"])
        if hasattr(self._page_ref, "data") and self._page_ref.data:
            self._page_ref.data.start_nudge_chat(nudge.get("chat_context", ""))

    async def _on_snooze(self, nudge_id: int, option: str):
        until = _snooze_until(option)
        await nudges_db.snooze(nudge_id, until)
        await self._load_nudges()

    async def _on_dismiss(self, nudge_id: int):
        await nudges_db.dismiss(nudge_id)
        await self._load_nudges()
