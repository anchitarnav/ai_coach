"""Diary view — write and browse diary entries."""

import flet as ft
from datetime import date
from storage import diary as diary_db
from ui import theme

MOODS = [
    ("", "—"),
    ("great", "Great"),
    ("good", "Good"),
    ("okay", "Okay"),
    ("stressed", "Stressed"),
    ("frustrated", "Frustrated"),
    ("reflective", "Reflective"),
    ("motivated", "Motivated"),
]

MOOD_EMOJI = {
    "great": "++",
    "good": "+",
    "okay": "~",
    "stressed": "!",
    "frustrated": "!!",
    "reflective": "?",
    "motivated": "^",
}


class DiaryView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref

        self.entries_list = ft.ListView(
            expand=True, spacing=10,
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=12, bottom=20),
        )

        # ── Entry form ────────────────────────────────────────────────
        self._selected_date = date.today()

        self._date_label = ft.Text(
            date.today().strftime("%A, %B %d"), size=13,
            color=theme.TEXT_SECONDARY, weight=ft.FontWeight.W_500,
        )
        self._date_picker = ft.DatePicker(
            first_date=date(2020, 1, 1),
            last_date=date.today(),
            value=date.today(),
            on_change=self._on_date_picked,
        )
        date_btn = ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=theme.TEXT_SECONDARY),
                self._date_label,
            ], spacing=4, tight=True),
            on_click=self._open_date_picker,
        )

        self.content_field = ft.TextField(
            hint_text="What happened today? What's on your mind?",
            multiline=True, min_lines=4, max_lines=10, expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        self.mood_dd = ft.Dropdown(
            label="Mood", width=170,
            options=[ft.dropdown.Option(k, text=v) for k, v in MOODS],
            value="",
        )
        save_btn = ft.Button(
            "Save Entry", icon=ft.Icons.SAVE, on_click=self._on_save,
            color="#FFFFFF", bgcolor=theme.PRIMARY,
        )

        form = ft.Container(
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row([
                        theme.subheading("New Entry"),
                        ft.Container(expand=True),
                        date_btn,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.content_field,
                    ft.Row([self.mood_dd, ft.Container(expand=True), save_btn],
                           vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
            padding=theme.PAGE_PAD,
            bgcolor=theme.SURFACE,
            border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER)),
        )

        header = ft.Container(
            content=theme.heading("Diary"),
            padding=ft.Padding(left=theme.PAGE_PAD, right=0, top=20, bottom=0),
        )

        self.controls = [form, header, self.entries_list]
        self._page_ref.overlay.append(self._date_picker)

    def did_mount(self):
        self._page_ref.run_task(self._load_entries)

    async def _load_entries(self):
        entries = await diary_db.get_all(limit=50)
        self.entries_list.controls.clear()

        if not entries:
            self.entries_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.BOOK_OUTLINED, size=36, color=theme.TEXT_MUTED),
                            ft.Text("No diary entries yet", size=14, color=theme.TEXT_MUTED),
                            ft.Text("Write your first entry above.", size=12, color=theme.TEXT_MUTED),
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

        for entry in entries:
            self.entries_list.controls.append(self._build_entry_card(entry))
        self.update()

    def _build_entry_card(self, entry: dict) -> ft.Container:
        """Build a read-only card for a diary entry."""
        mood = entry["mood"]
        mood_pill = theme.pill(mood, theme.ACCENT, theme.ACCENT_LIGHT) if mood else ft.Container(height=0)

        return theme.card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(entry["date"], size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                            mood_pill,
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED, icon_size=16,
                                icon_color=theme.TEXT_MUTED, tooltip="Edit",
                                on_click=lambda e, eid=entry["id"]: self._page_ref.run_task(self._start_edit, eid),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_size=16,
                                icon_color=theme.TEXT_MUTED, tooltip="Delete",
                                on_click=lambda e, eid=entry["id"]: self._page_ref.run_task(self._delete_entry, eid),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Markdown(
                        entry["content"], selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    ),
                ],
            ),
        )

    def _open_date_picker(self, e):
        self._date_picker.open = True
        self._page_ref.update()

    def _on_date_picked(self, e):
        picked = self._date_picker.value
        if picked:
            self._selected_date = date(picked.year, picked.month, picked.day)
            self._date_label.value = self._selected_date.strftime("%A, %B %d")
            self._date_label.update()

    async def _on_save(self, e):
        content = self.content_field.value.strip()
        if not content:
            return
        await diary_db.create(entry_date=self._selected_date, content=content, mood=self.mood_dd.value or "")
        self.content_field.value = ""
        self.mood_dd.value = ""
        await self._load_entries()

    async def _start_edit(self, entry_id: int):
        entry = await diary_db.get_by_id(entry_id)
        if not entry:
            return

        edit_field = ft.TextField(
            value=entry["content"],
            multiline=True, min_lines=4, max_lines=12, expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        edit_mood = ft.Dropdown(
            label="Mood", width=170,
            options=[ft.dropdown.Option(k, text=v) for k, v in MOODS],
            value=entry["mood"] or "",
        )

        edit_card = theme.card(
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(entry["date"], size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                            theme.pill("editing", theme.PRIMARY, "#EEF2FF"),
                            ft.Container(expand=True),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    edit_field,
                    ft.Row([
                        edit_mood,
                        ft.Container(expand=True),
                        ft.TextButton("Cancel", on_click=lambda e: self._page_ref.run_task(self._load_entries)),
                        ft.Button(
                            "Save", icon=ft.Icons.SAVE,
                            color="#FFFFFF", bgcolor=theme.PRIMARY,
                            on_click=lambda e, eid=entry_id, ef=edit_field, em=edit_mood:
                                self._page_ref.run_task(self._save_edit, eid, ef.value, em.value),
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                ],
            ),
        )

        entries = await diary_db.get_all(limit=50)
        self.entries_list.controls.clear()
        for e in entries:
            if e["id"] == entry_id:
                self.entries_list.controls.append(edit_card)
            else:
                self.entries_list.controls.append(self._build_entry_card(e))
        self.update()

    async def _save_edit(self, entry_id: int, content: str, mood: str):
        content = content.strip()
        if not content:
            return
        await diary_db.update(entry_id, content=content, mood=mood or "")
        await self._load_entries()

    async def _delete_entry(self, entry_id: int):
        await diary_db.delete(entry_id)
        await self._load_entries()
