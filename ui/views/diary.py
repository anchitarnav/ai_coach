"""Diary view — list + detail split layout with AI processing."""

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


def _entry_display_title(entry: dict) -> str:
    """Return the title to display: AI-generated title or first line of content."""
    if entry.get("title"):
        return entry["title"]
    first_line = entry["content"].split("\n")[0]
    return first_line[:50] + ("..." if len(first_line) > 50 else "")


def _short_date(date_str: str) -> str:
    """Format a date string like 'Mar 12, 2026'."""
    try:
        d = date.fromisoformat(date_str)
        return d.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return date_str


class DiaryView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref
        self._selected_entry_id: int | None = None
        self._entries: list[dict] = []
        self._processing_ids: set[int] = set()

        # ── Date picker (shared between new/edit forms) ─────────────
        self._selected_date = date.today()
        self._date_picker = ft.DatePicker(
            first_date=date(2020, 1, 1),
            last_date=date.today(),
            value=date.today(),
            on_change=self._on_date_picked,
        )

        # ── Entry list sidebar ──────────────────────────────────────
        self._entry_list = ft.ListView(spacing=2, expand=True, padding=8)

        new_entry_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD, size=16, color=theme.PRIMARY),
                    ft.Text("New entry", size=13, weight=ft.FontWeight.W_500, color=theme.PRIMARY),
                ],
                spacing=6,
            ),
            on_click=lambda e: self._page_ref.run_task(self._show_new_entry_form),
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            border_radius=8,
            ink=True,
        )

        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Diary", size=11, weight=ft.FontWeight.W_600,
                                        color=theme.TEXT_MUTED),
                        padding=ft.Padding(left=12, right=12, top=14, bottom=4),
                    ),
                    new_entry_btn,
                    self._entry_list,
                ],
                spacing=0,
            ),
            width=280,
            bgcolor=theme.SURFACE,
            border=ft.Border(right=ft.BorderSide(1, theme.BORDER)),
        )

        # ── Detail pane ─────────────────────────────────────────────
        self._detail_container = ft.Container(expand=True, bgcolor=theme.SURFACE_DIM)
        self._show_empty_state()

        self.controls = [
            ft.Row(expand=True, spacing=0, controls=[sidebar, self._detail_container])
        ]
        self._page_ref.overlay.append(self._date_picker)

    def did_mount(self):
        self._page_ref.run_task(self._load_entries)

    # ── Entry list ──────────────────────────────────────────────────

    async def _load_entries(self):
        self._entries = await diary_db.get_all(limit=100)
        self._entry_list.controls.clear()

        if not self._entries:
            self._entry_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.BOOK_OUTLINED, size=28, color=theme.TEXT_MUTED),
                            ft.Text("No entries yet", size=12, color=theme.TEXT_MUTED),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=30,
                )
            )
        else:
            for entry in self._entries:
                self._entry_list.controls.append(self._build_list_item(entry))
        self.update()

    def _build_list_item(self, entry: dict) -> ft.Container:
        """Build a compact row for the entry list sidebar."""
        eid = entry["id"]
        is_selected = eid == self._selected_entry_id
        is_processing = eid in self._processing_ids
        mood = entry.get("mood", "")
        mood_sym = MOOD_EMOJI.get(mood, "")

        # Right side: processing spinner or mood symbol
        if is_processing:
            trailing = ft.ProgressRing(width=12, height=12, stroke_width=2, color=theme.ACCENT)
        elif mood_sym:
            trailing = ft.Text(mood_sym, size=12, color=theme.ACCENT, weight=ft.FontWeight.W_600)
        else:
            trailing = ft.Container(width=0)

        return ft.Container(
            content=ft.Column(
                spacing=2,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                _short_date(entry["date"]), size=11,
                                weight=ft.FontWeight.W_600, color=theme.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            trailing,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        _entry_display_title(entry),
                        size=13, max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        color=theme.TEXT if is_selected else theme.TEXT_SECONDARY,
                    ),
                ],
            ),
            bgcolor=theme.PRIMARY_LIGHT if is_selected else None,
            border_radius=8,
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            on_click=lambda e, _eid=eid: self._page_ref.run_task(self._on_entry_click, _eid),
            ink=True,
        )

    async def _on_entry_click(self, entry_id: int):
        self._selected_entry_id = entry_id
        await self._load_entries()  # re-render list to update highlight
        await self._show_detail(entry_id)

    # ── Detail pane states ──────────────────────────────────────────

    def _show_empty_state(self):
        """Placeholder when no entry is selected."""
        self._selected_entry_id = None
        self._detail_container.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.BOOK_OUTLINED, size=40, color=theme.TEXT_MUTED),
                            ft.Text("Select an entry or write a new one",
                                    size=16, color=theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("Click an entry on the left, or tap + to start writing.",
                                    size=13, color=theme.TEXT_MUTED,
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                ),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    async def _show_detail(self, entry_id: int):
        """Show full entry in the detail pane."""
        entry = await diary_db.get_by_id(entry_id)
        if not entry:
            self._show_empty_state()
            self.update()
            return

        mood = entry.get("mood", "")
        title_text = entry.get("title", "")
        is_processing = entry_id in self._processing_ids

        # Header row: title + actions
        header_controls = []
        if title_text:
            header_controls.append(
                ft.Text(title_text, size=20, weight=ft.FontWeight.W_700, color=theme.TEXT, expand=True)
            )
        else:
            header_controls.append(ft.Container(expand=True))

        header_controls.extend([
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED, icon_size=18,
                icon_color=theme.TEXT_MUTED, tooltip="Edit",
                on_click=lambda e, eid=entry_id: self._page_ref.run_task(self._show_edit_form, eid),
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE, icon_size=18,
                icon_color=theme.TEXT_MUTED, tooltip="Delete",
                on_click=lambda e, eid=entry_id: self._page_ref.run_task(self._delete_entry, eid),
            ),
        ])

        # Meta row: date + mood
        meta_controls = [
            ft.Text(_short_date(entry["date"]), size=13, color=theme.TEXT_SECONDARY,
                     weight=ft.FontWeight.W_500),
        ]
        if mood:
            meta_controls.append(theme.pill(mood, theme.ACCENT, theme.ACCENT_LIGHT))

        if is_processing:
            meta_controls.append(
                ft.Row(
                    controls=[
                        ft.ProgressRing(width=12, height=12, stroke_width=2, color=theme.ACCENT),
                        ft.Text("Processing...", size=12, color=theme.TEXT_MUTED, italic=True),
                    ],
                    spacing=6,
                )
            )

        content_col = ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[
                ft.Row(controls=header_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row(controls=meta_controls, spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Markdown(
                    entry["content"], selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                ),
            ],
        )

        self._detail_container.content = ft.Container(
            content=content_col,
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=20, bottom=20),
            expand=True,
        )
        self.update()

    # ── New entry form ──────────────────────────────────────────────

    async def _show_new_entry_form(self):
        self._selected_entry_id = None
        self._selected_date = date.today()
        self._date_picker.value = date.today()
        await self._load_entries()  # clear selection highlight
        self._show_entry_form(None)
        self.update()

    async def _show_edit_form(self, entry_id: int):
        entry = await diary_db.get_by_id(entry_id)
        if not entry:
            return
        try:
            self._selected_date = date.fromisoformat(entry["date"])
        except (ValueError, TypeError):
            self._selected_date = date.today()
        self._date_picker.value = self._selected_date
        self._show_entry_form(entry)
        self.update()

    def _show_entry_form(self, entry: dict | None):
        """Render the new/edit form in the detail pane."""
        is_edit = entry is not None

        date_label = ft.Text(
            self._selected_date.strftime("%A, %B %d"), size=13,
            color=theme.TEXT_SECONDARY, weight=ft.FontWeight.W_500,
        )
        # Store ref so date picker can update it
        self._form_date_label = date_label

        date_btn = ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=theme.TEXT_SECONDARY),
                date_label,
            ], spacing=4, tight=True),
            on_click=self._open_date_picker,
        )

        content_field = ft.TextField(
            hint_text="What happened today? What's on your mind?",
            value=entry["content"] if is_edit else "",
            multiline=True, min_lines=8, max_lines=20, expand=True,
            border_radius=theme.INPUT_RADIUS,
        )
        mood_dd = ft.Dropdown(
            label="Mood", width=170,
            options=[ft.dropdown.Option(k, text=v) for k, v in MOODS],
            value=entry["mood"] if is_edit else "",
        )

        if is_edit:
            entry_id = entry["id"]
            action_row = ft.Row([
                mood_dd,
                ft.Container(expand=True),
                ft.TextButton("Cancel",
                              on_click=lambda e, eid=entry_id: self._page_ref.run_task(self._on_entry_click, eid)),
                ft.Button(
                    "Save", icon=ft.Icons.SAVE,
                    color="#FFFFFF", bgcolor=theme.PRIMARY,
                    on_click=lambda e, eid=entry_id, cf=content_field, md=mood_dd:
                        self._page_ref.run_task(self._save_edit, eid, cf.value, md.value),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.END)
        else:
            action_row = ft.Row([
                mood_dd,
                ft.Container(expand=True),
                ft.Button(
                    "Save Entry", icon=ft.Icons.SAVE,
                    color="#FFFFFF", bgcolor=theme.PRIMARY,
                    on_click=lambda e, cf=content_field, md=mood_dd:
                        self._page_ref.run_task(self._on_save, cf.value, md.value),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.END)

        heading_text = "Edit Entry" if is_edit else "New Entry"
        if is_edit:
            heading_row = ft.Row([
                theme.subheading(heading_text),
                theme.pill("editing", theme.PRIMARY, theme.PRIMARY_LIGHT),
                ft.Container(expand=True),
                date_btn,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            heading_row = ft.Row([
                theme.subheading(heading_text),
                ft.Container(expand=True),
                date_btn,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        form_col = ft.Column(
            spacing=16,
            expand=True,
            controls=[heading_row, content_field, action_row],
        )

        self._detail_container.content = ft.Container(
            content=form_col,
            padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=20, bottom=20),
            expand=True,
        )

    # ── Date picker ─────────────────────────────────────────────────

    def _open_date_picker(self, e):
        self._date_picker.open = True
        self._page_ref.update()

    def _on_date_picked(self, e):
        picked = self._date_picker.value
        if picked:
            # DatePicker returns UTC — convert to local date to avoid off-by-one
            local = picked.astimezone()
            self._selected_date = local.date()
            if hasattr(self, "_form_date_label"):
                self._form_date_label.value = self._selected_date.strftime("%A, %B %d")
                self._form_date_label.update()

    # ── Save / Edit / Delete ────────────────────────────────────────

    async def _on_save(self, content_val: str, mood_val: str):
        content = content_val.strip()
        if not content:
            return
        entry_id = await diary_db.create(
            entry_date=self._selected_date,
            content=content,
            mood=mood_val or "",
        )
        # Select the new entry and show it
        self._selected_entry_id = entry_id
        self._processing_ids.add(entry_id)
        await self._load_entries()
        await self._show_detail(entry_id)
        # Fire-and-forget AI processing
        self._page_ref.run_task(self._run_processing, entry_id)

    async def _save_edit(self, entry_id: int, content_val: str, mood_val: str):
        content = content_val.strip()
        if not content:
            return
        await diary_db.update(entry_id, content=content, mood=mood_val or "")
        # Re-process to regenerate title
        self._processing_ids.add(entry_id)
        await self._load_entries()
        await self._show_detail(entry_id)
        self._page_ref.run_task(self._run_processing, entry_id)

    async def _delete_entry(self, entry_id: int):
        await diary_db.delete(entry_id)
        self._show_empty_state()
        await self._load_entries()
        self.update()

    # ── AI processing ───────────────────────────────────────────────

    async def _run_processing(self, entry_id: int):
        try:
            from services.diary_processor import process_diary_entry
            await process_diary_entry(entry_id)
        except Exception:
            pass  # Silently fail — title stays empty, first-line fallback is used
        finally:
            self._processing_ids.discard(entry_id)
            await self._load_entries()
            if self._selected_entry_id == entry_id:
                await self._show_detail(entry_id)
