"""Memory view — browse, search, edit permanent memories."""

import flet as ft
from storage import memory as memory_db
from ui import theme

SOURCE_STYLES = {
    "agent_curated": ("Agent", "#7C3AED", "#F5F3FF"),
    "user_added":    ("Manual", "#2563EB", "#EFF6FF"),
    "diary_extract": ("Diary", "#D97706", "#FFFBEB"),
}


class MemoryView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref

        self.memory_list = ft.ListView(
            expand=True, spacing=10,
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=12, bottom=20),
        )

        # ── Search ────────────────────────────────────────────────────
        self.search_field = ft.TextField(
            hint_text="Search memories...", expand=True,
            on_submit=self._on_search, prefix_icon=ft.Icons.SEARCH,
            border_radius=theme.INPUT_RADIUS,
        )
        clear_btn = ft.TextButton("Clear", on_click=self._on_clear_search)

        # ── Add memory ────────────────────────────────────────────────
        self.new_memory_field = ft.TextField(
            hint_text="Add a new memory...", expand=True,
            multiline=True, min_lines=1, max_lines=3,
            border_radius=theme.INPUT_RADIUS,
        )
        self.new_tags_field = ft.TextField(
            hint_text="Tags (comma-separated)", width=220,
            border_radius=theme.INPUT_RADIUS,
        )
        add_btn = ft.Button(
            "Add", icon=ft.Icons.ADD, on_click=self._on_add,
            color="#FFFFFF", bgcolor=theme.PRIMARY,
        )

        header = ft.Container(
            content=ft.Column(
                spacing=12,
                controls=[
                    theme.heading("Memory"),
                    ft.Row([self.search_field, clear_btn]),
                    ft.Row([self.new_memory_field, self.new_tags_field, add_btn],
                           vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
            padding=theme.PAGE_PAD,
            bgcolor=theme.SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER)),
        )

        self.result_count = theme.caption("")

        self.controls = [
            header,
            ft.Container(content=self.result_count,
                         padding=ft.Padding(left=theme.PAGE_PAD, right=0, top=12, bottom=0)),
            self.memory_list,
        ]

    def did_mount(self):
        self._page_ref.run_task(self._load_memories)

    async def _load_memories(self):
        memories = await memory_db.get_all(limit=100)
        self._render_memories(memories)

    def _render_memories(self, memories: list[dict]):
        self.memory_list.controls.clear()
        self.result_count.value = f"{len(memories)} memories"

        if not memories:
            self.memory_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PSYCHOLOGY_OUTLINED, size=36, color=theme.TEXT_MUTED),
                            ft.Text("No memories yet", size=14, color=theme.TEXT_MUTED),
                            ft.Text("Memories are created from coaching conversations or added manually.",
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

        for m in memories:
            label, fg, bg = SOURCE_STYLES.get(m["source"], ("Other", theme.TEXT_SECONDARY, theme.SURFACE_DIM))

            tags_row = []
            if m["tags"]:
                for tag in m["tags"].split(","):
                    tag = tag.strip()
                    if tag:
                        tags_row.append(theme.pill(tag, theme.TEXT_SECONDARY, theme.SURFACE_DIM))

            self.memory_list.controls.append(
                theme.card(
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                controls=[
                                    theme.pill(label, fg, bg),
                                    theme.caption(f"{m['relevance_score']:.0%} relevance"),
                                    ft.Container(expand=True),
                                    theme.caption(m["created_at"][:16] if m["created_at"] else ""),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE, icon_size=16,
                                        icon_color=theme.TEXT_MUTED, tooltip="Delete",
                                        on_click=lambda e, mid=m["id"]: self._page_ref.run_task(self._delete_memory, mid),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(m["content"], size=13, color=theme.TEXT, selectable=True),
                            ft.Row(tags_row, spacing=4, wrap=True) if tags_row else ft.Container(height=0),
                        ],
                    ),
                )
            )
        self.update()

    async def _on_search(self, e):
        query = self.search_field.value.strip()
        if not query:
            await self._load_memories()
            return
        self._render_memories(await memory_db.search(query))

    async def _on_clear_search(self, e):
        self.search_field.value = ""
        await self._load_memories()

    async def _on_add(self, e):
        content = self.new_memory_field.value.strip()
        if not content:
            return
        await memory_db.create(content=content, source="user_added", tags=self.new_tags_field.value.strip())
        self.new_memory_field.value = ""
        self.new_tags_field.value = ""
        await self._load_memories()

    async def _delete_memory(self, memory_id: int):
        await memory_db.delete(memory_id)
        await self._load_memories()
