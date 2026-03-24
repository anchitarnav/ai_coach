"""Notes view — browse, search, and manage reference notes."""

import flet as ft
from storage import notes as notes_db
from ui import theme


class NotesView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref

        self.notes_list = ft.ListView(
            expand=True, spacing=10,
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=12, bottom=20),
        )

        # -- Search --
        self.search_field = ft.TextField(
            hint_text="Search notes...", expand=True,
            on_submit=self._on_search, prefix_icon=ft.Icons.SEARCH,
            border_radius=theme.INPUT_RADIUS,
        )
        clear_btn = ft.TextButton("Clear", on_click=self._on_clear_search)

        # -- New note form --
        self.title_field = ft.TextField(
            hint_text="Note title", expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        self.content_field = ft.TextField(
            hint_text="Paste content here...",
            multiline=True, min_lines=4, max_lines=10, expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        self.tags_field = ft.TextField(
            hint_text="Tags (comma-separated)", width=220,
            border_radius=theme.INPUT_RADIUS,
        )
        save_btn = ft.Button(
            "Save Note", icon=ft.Icons.SAVE, on_click=self._on_save,
            color="#FFFFFF", bgcolor=theme.PRIMARY,
        )

        form = ft.Container(
            content=ft.Column(
                spacing=12,
                controls=[
                    theme.subheading("New Note"),
                    self.title_field,
                    self.content_field,
                    ft.Row([self.tags_field, ft.Container(expand=True), save_btn],
                           vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
            padding=theme.PAGE_PAD,
            bgcolor=theme.SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER)),
        )

        search_row = ft.Container(
            content=ft.Row([self.search_field, clear_btn]),
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=12, bottom=0),
        )

        self.result_count = theme.caption("")

        self.controls = [
            form,
            search_row,
            ft.Container(content=self.result_count,
                         padding=ft.Padding(left=theme.PAGE_PAD, right=0, top=8, bottom=0)),
            self.notes_list,
        ]

    def did_mount(self):
        self._page_ref.run_task(self._load_notes)

    async def _load_notes(self):
        notes = await notes_db.get_all(limit=100)
        self._render_notes(notes)

    def _render_notes(self, notes: list[dict]):
        self.notes_list.controls.clear()
        self.result_count.value = f"{len(notes)} notes"

        if not notes:
            self.notes_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=36, color=theme.TEXT_MUTED),
                            ft.Text("No notes yet", size=14, color=theme.TEXT_MUTED),
                            ft.Text("Save reference documents, policies, or frameworks above.",
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

        for note in notes:
            self.notes_list.controls.append(self._build_note_card(note))
        self.update()

    def _build_note_card(self, note: dict) -> ft.Container:
        tags_row = []
        if note["tags"]:
            for tag in note["tags"].split(","):
                tag = tag.strip()
                if tag:
                    tags_row.append(theme.pill(tag, theme.TEXT_SECONDARY, theme.SURFACE_DIM))

        return theme.card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"#{note['id']}", size=13, weight=ft.FontWeight.W_700, color=theme.TEXT_MUTED),
                            ft.Text(note["title"], size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                            *tags_row,
                            ft.Container(expand=True),
                            theme.caption(note["updated_at"][:16] if note["updated_at"] else ""),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED, icon_size=16,
                                icon_color=theme.TEXT_MUTED, tooltip="Edit",
                                on_click=lambda e, nid=note["id"]: self._page_ref.run_task(self._start_edit, nid),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_size=16,
                                icon_color=theme.TEXT_MUTED, tooltip="Delete",
                                on_click=lambda e, nid=note["id"]: self._page_ref.run_task(self._delete_note, nid),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Markdown(
                        note["content"], selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    ),
                ],
            ),
        )

    # -- Search --

    async def _on_search(self, e):
        query = self.search_field.value.strip()
        if not query:
            await self._load_notes()
            return
        self._render_notes(await notes_db.search(query))

    async def _on_clear_search(self, e):
        self.search_field.value = ""
        await self._load_notes()

    # -- Create --

    async def _on_save(self, e):
        title = self.title_field.value.strip()
        if not title:
            return
        content = self.content_field.value.strip()
        tags = self.tags_field.value.strip()
        await notes_db.create(title=title, content=content, tags=tags)
        self.title_field.value = ""
        self.content_field.value = ""
        self.tags_field.value = ""
        await self._load_notes()

    # -- Edit --

    async def _start_edit(self, note_id: int):
        note = await notes_db.get_by_id(note_id)
        if not note:
            return

        edit_title = ft.TextField(
            value=note["title"], expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        edit_content = ft.TextField(
            value=note["content"],
            multiline=True, min_lines=4, max_lines=12, expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        edit_tags = ft.TextField(
            value=note["tags"], hint_text="Tags (comma-separated)", width=220,
            border_radius=theme.INPUT_RADIUS,
        )

        edit_card = theme.card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"#{note['id']}", size=13, weight=ft.FontWeight.W_700, color=theme.TEXT_MUTED),
                            theme.pill("editing", theme.PRIMARY, "#EEF2FF"),
                            ft.Container(expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    edit_title,
                    edit_content,
                    ft.Row([
                        edit_tags,
                        ft.Container(expand=True),
                        ft.TextButton("Cancel", on_click=lambda e: self._page_ref.run_task(self._load_notes)),
                        ft.Button(
                            "Save", icon=ft.Icons.SAVE,
                            color="#FFFFFF", bgcolor=theme.PRIMARY,
                            on_click=lambda e, nid=note_id, et=edit_title, ec=edit_content, etg=edit_tags:
                                self._page_ref.run_task(self._save_edit, nid, et.value, ec.value, etg.value),
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
        )

        notes = await notes_db.get_all(limit=100)
        self.notes_list.controls.clear()
        for n in notes:
            if n["id"] == note_id:
                self.notes_list.controls.append(edit_card)
            else:
                self.notes_list.controls.append(self._build_note_card(n))
        self.update()

    async def _save_edit(self, note_id: int, title: str, content: str, tags: str):
        title = title.strip()
        if not title:
            return
        await notes_db.update(note_id, title=title, content=content.strip(), tags=tags.strip())
        await self._load_notes()

    # -- Delete --

    async def _delete_note(self, note_id: int):
        await notes_db.delete(note_id)
        await self._load_notes()
