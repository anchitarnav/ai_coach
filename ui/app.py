"""Main app shell — navigation, routing, view management."""

import flet as ft

from services.coach_loop import CoachLoop
from storage import nudges as nudges_db
from ui import theme
from ui.components.nudge_banner import NudgeBanner
from ui.views.chat import ChatView
from ui.views.goals import GoalsView
from ui.views.memory import MemoryView
from ui.views.diary import DiaryView
from ui.views.notifications import NotificationsView
from ui.views.settings import SettingsView


NAV_ITEMS = [
    ("Chat",          ft.Icons.CHAT_BUBBLE_OUTLINE,      ft.Icons.CHAT_BUBBLE),
    ("Goals",         ft.Icons.FLAG_OUTLINED,             ft.Icons.FLAG),
    ("Memory",        ft.Icons.PSYCHOLOGY_OUTLINED,       ft.Icons.PSYCHOLOGY),
    ("Diary",         ft.Icons.BOOK_OUTLINED,             ft.Icons.BOOK),
    ("Notifications", ft.Icons.NOTIFICATIONS_OUTLINED,    ft.Icons.NOTIFICATIONS),
    ("Settings",      ft.Icons.SETTINGS_OUTLINED,         ft.Icons.SETTINGS),
]

NOTIF_INDEX = 4


class CoachApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "AI Career Coach"
        self.page.window.width = 1140
        self.page.window.height = 780
        theme.configure_page(self.page)

        # Store self on page.data so other views can access start_nudge_chat
        self.page.data = self

        self.current_view_index = 0
        self._views: dict[int, ft.Control] = {}

        # ── Sidebar ──────────────────────────────────────────────────
        self._nav_buttons: list[ft.Container] = []
        nav_controls: list[ft.Control] = []

        # Logo / brand header
        nav_controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.AUTO_AWESOME, color=theme.PRIMARY, size=24),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                padding=ft.Padding(left=0, right=0, top=24, bottom=16),
            )
        )

        for idx, (label, icon, icon_sel) in enumerate(NAV_ITEMS):
            btn = self._build_nav_button(idx, label, icon, icon_sel)
            self._nav_buttons.append(btn)
            nav_controls.append(btn)

        sidebar = ft.Container(
            content=ft.Column(
                controls=nav_controls,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=72,
            bgcolor=theme.SURFACE,
            border=ft.Border(right=ft.BorderSide(1, theme.BORDER)),
            padding=ft.Padding(left=8, right=8, top=0, bottom=16),
        )

        # ── Nudge banner + content area ─────────────────────────────
        self._nudge_banner = NudgeBanner(self.page)
        self._content_view = ft.Column(expand=True)

        content_column = ft.Column(
            expand=True, spacing=0,
            controls=[self._nudge_banner, self._content_view],
        )

        # ── Notification badge (must be set up before _show_view) ──
        self._notif_badge_text = ft.Text("", size=9, color="#FFFFFF", weight=ft.FontWeight.W_700)
        self._notif_badge = ft.Container(
            content=self._notif_badge_text,
            bgcolor=theme.ERROR,
            border_radius=8,
            width=16, height=16,
            alignment=ft.Alignment(0, 0),
            visible=False,
        )
        notif_btn = self._nav_buttons[NOTIF_INDEX]
        icon_col = notif_btn.content
        icon_widget = icon_col.controls[0]
        icon_col.controls[0] = ft.Stack(
            controls=[icon_widget, ft.Container(content=self._notif_badge, left=14, top=0)],
            width=22, height=22,
        )

        self.page.add(
            ft.Row(expand=True, spacing=0, controls=[sidebar, content_column])
        )

        self._init_all_views()
        self._show_view(0)

        # ── Coach loop ──────────────────────────────────────────────
        self._coach_loop = CoachLoop(on_nudge=self._on_new_nudge)
        self.page.run_task(self._start_loop)

    async def _start_loop(self):
        # Refresh banner/badge first (uses DB), then start loop to avoid concurrent DB access
        await self._nudge_banner.refresh()
        await self._refresh_badge()
        self._coach_loop.start()

    # ── Navigation ────────────────────────────────────────────────────

    def _build_nav_button(self, idx: int, label: str, icon, icon_sel) -> ft.Container:
        is_active = idx == self.current_view_index
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon_sel if is_active else icon,
                        color=theme.PRIMARY if is_active else theme.TEXT_MUTED,
                        size=22,
                    ),
                    ft.Text(
                        label,
                        size=10,
                        weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400,
                        color=theme.PRIMARY if is_active else theme.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.PRIMARY_LIGHT if is_active else None,
            border_radius=10,
            padding=ft.Padding(left=6, right=6, top=10, bottom=8),
            width=56,
            on_click=lambda e, i=idx: self.page.run_task(self._on_nav_click, i),
            ink=True,
        )

    def _refresh_nav(self):
        for idx, (label, icon, icon_sel) in enumerate(NAV_ITEMS):
            is_active = idx == self.current_view_index
            btn = self._nav_buttons[idx]
            btn.bgcolor = theme.PRIMARY_LIGHT if is_active else None
            col = btn.content
            # For notifications tab, the icon is wrapped in a Stack
            if idx == NOTIF_INDEX:
                stack = col.controls[0]
                icon_widget = stack.controls[0]
            else:
                icon_widget = col.controls[0]
            icon_widget.name = icon_sel if is_active else icon
            icon_widget.color = theme.PRIMARY if is_active else theme.TEXT_MUTED
            col.controls[1].weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400
            col.controls[1].color = theme.PRIMARY if is_active else theme.TEXT_MUTED

    def _init_all_views(self):
        """Pre-create all views so tab switching is instant."""
        factories = [ChatView, GoalsView, MemoryView, DiaryView, NotificationsView, SettingsView]
        for idx, factory in enumerate(factories):
            self._views[idx] = factory(self.page)

    def _show_view(self, index: int):
        self.current_view_index = index
        self._refresh_nav()
        self._content_view.controls = [self._views[index]]
        self.page.update()

    async def _on_nav_click(self, index: int):
        # Fire-and-forget memory curation when leaving chat
        if self.current_view_index == 0:
            chat_view: ChatView = self._views[0]
            self.page.run_task(chat_view.end_conversation)

        self._show_view(index)

        # Refresh badge when leaving notifications tab
        if index != NOTIF_INDEX:
            await self._refresh_badge()

    # ── Nudge / notification helpers ──────────────────────────────────

    async def _on_new_nudge(self, count: int):
        """Called by CoachLoop when new nudges are created."""
        await self._nudge_banner.refresh()
        self._update_badge(count)
        self.page.update()

    async def _refresh_badge(self):
        count = await nudges_db.count_pending()
        self._update_badge(count)
        self.page.update()

    def _update_badge(self, count: int):
        if count > 0:
            self._notif_badge_text.value = str(count) if count < 100 else "99+"
            self._notif_badge.visible = True
        else:
            self._notif_badge.visible = False

    def start_nudge_chat(self, chat_context: str):
        """Switch to chat view and start a nudge-driven conversation."""
        self._show_view(0)
        chat_view: ChatView = self._views[0]
        self.page.run_task(chat_view.start_from_nudge, chat_context)
