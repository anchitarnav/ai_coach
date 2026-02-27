"""Top-of-page banner showing the latest pending nudge."""

from datetime import datetime, timedelta

import flet as ft

from storage import nudges as nudges_db
from ui import theme


def _snooze_until(option: str) -> str:
    """Convert a snooze option label to an ISO timestamp."""
    now = datetime.now()
    if option == "1 hour":
        return (now + timedelta(hours=1)).isoformat()
    elif option == "4 hours":
        return (now + timedelta(hours=4)).isoformat()
    elif option == "Tomorrow 9 AM":
        tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        return tomorrow.isoformat()
    elif option == "Next week":
        days_ahead = 7 - now.weekday()  # Monday
        if days_ahead <= 0:
            days_ahead += 7
        next_mon = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        return next_mon.isoformat()
    return (now + timedelta(hours=1)).isoformat()


class NudgeBanner(ft.Container):
    def __init__(self, page_ref: ft.Page):
        super().__init__(visible=False)
        self._page_ref = page_ref
        self._current_nudge: dict | None = None

        self._message_text = ft.Text("", size=14, color=theme.TEXT, expand=True)
        self._priority_pill = theme.pill("gentle")

        talk_btn = ft.Button(
            "Let's talk",
            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
            on_click=self._on_talk,
            color=theme.PRIMARY,
            style=ft.ButtonStyle(padding=ft.Padding(left=12, right=12, top=0, bottom=0)),
        )
        snooze_btn = ft.PopupMenuButton(
            content=ft.Text("Snooze", size=13, color=theme.TEXT_SECONDARY),
            items=[
                ft.PopupMenuItem(content="1 hour", on_click=lambda e: self._page_ref.run_task(self._on_snooze, "1 hour")),
                ft.PopupMenuItem(content="4 hours", on_click=lambda e: self._page_ref.run_task(self._on_snooze, "4 hours")),
                ft.PopupMenuItem(content="Tomorrow 9 AM", on_click=lambda e: self._page_ref.run_task(self._on_snooze, "Tomorrow 9 AM")),
                ft.PopupMenuItem(content="Next week", on_click=lambda e: self._page_ref.run_task(self._on_snooze, "Next week")),
            ],
        )
        dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            icon_color=theme.TEXT_MUTED,
            tooltip="Dismiss",
            on_click=self._on_dismiss,
        )

        self.content = ft.Row(
            controls=[
                ft.Container(width=3, height=40, bgcolor=theme.ACCENT, border_radius=2),
                self._priority_pill,
                self._message_text,
                talk_btn,
                snooze_btn,
                dismiss_btn,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.bgcolor = theme.NOTIFICATION_BG
        self.padding = ft.Padding(left=12, right=8, top=8, bottom=8)
        self.border = ft.Border(bottom=ft.BorderSide(1, theme.BORDER))

    async def refresh(self) -> None:
        pending = await nudges_db.get_pending()
        if pending:
            nudge = pending[0]
            self._current_nudge = nudge
            self._message_text.value = nudge["message"]
            fg, bg = theme.PRIORITY_COLORS.get(nudge["priority"], theme.PRIORITY_COLORS["gentle"])
            self._priority_pill.content.value = nudge["priority"]
            self._priority_pill.content.color = fg
            self._priority_pill.bgcolor = bg
            if nudge["status"] == "pending":
                await nudges_db.show(nudge["id"])
            self.visible = True
        else:
            self._current_nudge = None
            self.visible = False
        self.update()

    def _on_talk(self, e):
        if self._current_nudge and hasattr(self._page_ref, "data") and self._page_ref.data:
            nudge = self._current_nudge
            self._page_ref.run_task(nudges_db.act_on, nudge["id"])
            self._page_ref.data.start_nudge_chat(nudge.get("chat_context", ""))
            self.visible = False
            self.update()

    async def _on_snooze(self, option: str):
        if self._current_nudge:
            until = _snooze_until(option)
            await nudges_db.snooze(self._current_nudge["id"], until)
            await self.refresh()

    def _on_dismiss(self, e):
        if self._current_nudge:
            self._page_ref.run_task(nudges_db.dismiss, self._current_nudge["id"])
            self.visible = False
            self._current_nudge = None
            self.update()
