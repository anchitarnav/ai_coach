"""Goals view — CRUD interface for career goals."""

import flet as ft
from storage import goals as goals_db
from ui import theme

CATEGORIES = ["leadership", "technical", "networking", "communication", "strategy", "other"]

PRIORITY_COLORS = {
    1: ("#DC2626", "#FEF2F2"),  # red
    2: ("#D97706", "#FFFBEB"),  # amber
    3: ("#4F46E5", "#EEF2FF"),  # indigo
    4: ("#0D9488", "#F0FDFA"),  # teal
    5: ("#6B7280", "#F9FAFB"),  # gray
}


class GoalsView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref

        self.goals_list = ft.ListView(expand=True, spacing=10,
                                       padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD,
                                                          top=12, bottom=20))

        # ── Add goal form ─────────────────────────────────────────────
        self.title_field = ft.TextField(
            label="Goal title", expand=True, border_radius=theme.INPUT_RADIUS,
        )
        self.desc_field = ft.TextField(
            label="Description (optional)", multiline=True, min_lines=2, max_lines=4,
            expand=True, border_radius=theme.INPUT_RADIUS,
        )
        self.category_dd = ft.Dropdown(
            label="Category", width=180,
            options=[ft.dropdown.Option(c) for c in CATEGORIES],
            value="leadership",
        )
        self.priority_dd = ft.Dropdown(
            label="Priority", width=130,
            options=[ft.dropdown.Option(str(i), text=f"P{i} — {'Critical' if i==1 else 'High' if i==2 else 'Medium' if i==3 else 'Low' if i==4 else 'Someday'}") for i in range(1, 6)],
            value="3",
        )

        add_btn = ft.Button(
            "Add Goal", icon=ft.Icons.ADD, on_click=self._on_add,
            color="#FFFFFF", bgcolor=theme.PRIMARY,
        )

        form = ft.Container(
            content=ft.Column(
                spacing=12,
                controls=[
                    theme.subheading("Add New Goal"),
                    self.title_field,
                    self.desc_field,
                    ft.Row([self.category_dd, self.priority_dd, add_btn],
                           vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
            padding=theme.PAGE_PAD,
            bgcolor=theme.SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER)),
        )

        # ── Header ────────────────────────────────────────────────────
        self.show_archived = False
        self.toggle_btn = ft.TextButton("Show archived", on_click=self._toggle_archived)

        header = ft.Container(
            content=ft.Row(
                controls=[theme.heading("Career Goals"), self.toggle_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=20, bottom=0),
        )

        self.controls = [form, header, self.goals_list]

    def did_mount(self):
        self._page_ref.run_task(self._load_goals)

    async def _load_goals(self):
        goals = await (goals_db.get_all() if self.show_archived else goals_db.get_active())
        self.goals_list.controls.clear()

        if not goals:
            self.goals_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FLAG_OUTLINED, size=36, color=theme.TEXT_MUTED),
                            ft.Text("No goals yet", size=14, color=theme.TEXT_MUTED),
                            ft.Text("Add your first career goal above to get started.",
                                    size=12, color=theme.TEXT_MUTED),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=40,
                )
            )
            self.update()
            return

        for g in goals:
            is_active = g["is_active"]
            pri = g["priority"]
            pri_fg, pri_bg = PRIORITY_COLORS.get(pri, PRIORITY_COLORS[3])

            actions = ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARCHIVE_OUTLINED if is_active else ft.Icons.UNARCHIVE_OUTLINED,
                        tooltip="Archive" if is_active else "Reactivate",
                        icon_size=18, icon_color=theme.TEXT_MUTED,
                        on_click=lambda e, gid=g["id"], a=is_active: self._page_ref.run_task(self._toggle_active, gid, a),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE, tooltip="Delete",
                        icon_size=18, icon_color=theme.TEXT_MUTED,
                        on_click=lambda e, gid=g["id"]: self._page_ref.run_task(self._delete_goal, gid),
                    ),
                ],
                spacing=0,
            )

            self.goals_list.controls.append(
                theme.card(
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        g["title"], size=15, weight=ft.FontWeight.W_600,
                                        color=theme.TEXT if is_active else theme.TEXT_MUTED,
                                        expand=True,
                                    ),
                                    theme.pill(f"P{pri}", pri_fg, pri_bg),
                                    theme.pill(g["category"] or "uncategorized"),
                                    actions,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(g["description"], size=13, color=theme.TEXT_SECONDARY)
                            if g["description"] else ft.Container(height=0),
                        ],
                    ),
                    opacity=1.0 if is_active else 0.55,
                )
            )
        self.update()

    async def _on_add(self, e):
        title = self.title_field.value.strip()
        if not title:
            return
        await goals_db.create(
            title=title,
            description=self.desc_field.value.strip(),
            category=self.category_dd.value or "",
            priority=int(self.priority_dd.value or "3"),
        )
        self.title_field.value = ""
        self.desc_field.value = ""
        self.category_dd.value = "leadership"
        self.priority_dd.value = "3"
        await self._load_goals()

    async def _toggle_active(self, goal_id: int, currently_active: bool):
        await goals_db.update(goal_id, is_active=not currently_active)
        await self._load_goals()

    async def _delete_goal(self, goal_id: int):
        await goals_db.delete(goal_id)
        await self._load_goals()

    async def _toggle_archived(self, e):
        self.show_archived = not self.show_archived
        self.toggle_btn.text = "Hide archived" if self.show_archived else "Show archived"
        await self._load_goals()
