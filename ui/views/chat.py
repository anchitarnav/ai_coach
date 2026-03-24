"""Chat view — daily coaching conversation."""

import flet as ft

from agent.coach import create_coach_agent
from storage import conversations as conv_db
from storage import settings as settings_db
from services.memory_curator import curate_memories
from ui.components.message_bubble import message_bubble
from ui import theme

# Friendly labels for agent tool names
_TOOL_LABELS = {
    "get_active_goals": "Reviewing your goals",
    "search_memories": "Searching memories",
    "get_recent_memories": "Recalling recent context",
    "get_recent_diary_entries": "Reading diary entries",
    "add_memory": "Saving a memory",
    "get_today_info": "Checking today's date",
    "create_commitment": "Tracking a commitment",
    "get_pending_commitments": "Reviewing commitments",
    "schedule_followup": "Scheduling follow-up",
    "search_notes": "Searching notes",
    "get_note_by_id": "Reading a note",
}


def _thinking_bubble() -> tuple[ft.Container, ft.Text]:
    """Build a coach bubble with an animated thinking indicator. Returns (bubble, status_label)."""
    status_label = ft.Text("Thinking", size=13, color=theme.TEXT_MUTED, italic=True)

    indicator = ft.Container(
        content=ft.Row(
            controls=[
                ft.ProgressRing(width=14, height=14, stroke_width=2, color=theme.ACCENT),
                status_label,
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=0, right=0, top=4, bottom=4),
    )

    avatar = ft.CircleAvatar(
        content=ft.Text("C", size=13, weight=ft.FontWeight.W_600, color="#FFFFFF"),
        bgcolor=theme.ACCENT,
        radius=16,
    )

    bubble = ft.Container(
        content=ft.Column(
            tight=True, spacing=2,
            controls=[
                ft.Text("Coach", size=12, weight=ft.FontWeight.W_600, color=theme.ACCENT),
                indicator,
            ],
        ),
        bgcolor=theme.COACH_BUBBLE,
        border=ft.Border.all(1, "#CCFBF1"),
        border_radius=ft.BorderRadius(top_left=2, top_right=16, bottom_left=16, bottom_right=16),
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        expand=True,
    )

    container = ft.Container(
        content=ft.Row(
            controls=[avatar, bubble],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        margin=ft.Margin(left=0, right=48, top=0, bottom=6),
    )

    return container, status_label


class ChatView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page_ref = page_ref
        self.conversation_id: int | None = None
        self.is_responding = False

        # ── Conversation sidebar ──────────────────────────────────────
        self.conv_list = ft.ListView(spacing=2, expand=True, padding=8)

        new_conv_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ADD, size=16, color=theme.PRIMARY),
                    ft.Text("New chat", size=13, weight=ft.FontWeight.W_500, color=theme.PRIMARY),
                ],
                spacing=6,
            ),
            on_click=self._on_new_conversation,
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            border_radius=8,
            ink=True,
        )

        conv_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("Conversations", size=11, weight=ft.FontWeight.W_600,
                                        color=theme.TEXT_MUTED),
                        padding=ft.Padding(left=12, right=12, top=14, bottom=4),
                    ),
                    new_conv_btn,
                    self.conv_list,
                ],
                spacing=0,
            ),
            width=230,
            bgcolor=theme.SURFACE,
            border=ft.Border(right=ft.BorderSide(1, theme.BORDER)),
        )

        # ── Chat area ─────────────────────────────────────────────────
        self.chat_list = ft.ListView(
            expand=True, spacing=4, padding=ft.Padding(left=24, right=24, top=20, bottom=8),
            auto_scroll=True,
        )

        # Welcome placeholder — centered both horizontally and vertically
        self.welcome = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=40, color=theme.TEXT_MUTED),
                            ft.Text("What would you like to work on today?",
                                    size=16, color=theme.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("Ask your coach for daily priorities, talk through a challenge, or just reflect.",
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

        self.status_text = ft.Text("", size=12, color=theme.TEXT_MUTED)

        self.input_field = ft.TextField(
            hint_text="Message your coach...",
            autofocus=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            filled=True,
            expand=True,
            border_radius=theme.INPUT_RADIUS,
            on_submit=self._on_send,
        )
        self.send_btn = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD_ROUNDED,
            tooltip="Send",
            icon_color="#FFFFFF",
            bgcolor=theme.PRIMARY,
            icon_size=20,
            on_click=self._on_send,
        )

        input_bar = ft.Container(
            content=ft.Column(
                spacing=4,
                controls=[
                    self.status_text,
                    ft.Row(
                        controls=[self.input_field, self.send_btn],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
            ),
            padding=ft.Padding(left=24, right=24, bottom=16, top=8),
            bgcolor=theme.SURFACE,
            border=ft.Border(top=ft.BorderSide(1, theme.BORDER)),
        )

        self._chat_content = ft.Column(expand=True, spacing=0, controls=[self.welcome, input_bar])

        chat_area = ft.Container(content=self._chat_content, expand=True, bgcolor=theme.SURFACE_DIM)

        self.controls = [
            ft.Row(expand=True, spacing=0, controls=[conv_sidebar, chat_area])
        ]

    def _show_chat_list(self):
        """Switch from welcome screen to chat messages."""
        self._chat_content.controls[0] = ft.Container(content=self.chat_list, expand=True)
        self.update()

    def did_mount(self):
        self._page_ref.run_task(self._load_conversations)

    async def _load_conversations(self):
        convs = await conv_db.get_all(limit=30)
        self.conv_list.controls.clear()
        for c in convs:
            is_selected = c["id"] == self.conversation_id
            delete_btn = ft.IconButton(
                icon=ft.Icons.CLOSE_ROUNDED,
                icon_size=13,
                icon_color=theme.BORDER_FOCUS,
                tooltip="Delete conversation",
                style=ft.ButtonStyle(padding=4),
                on_click=lambda e, cid=c["id"]: self._page_ref.run_task(
                    self._delete_conversation, cid
                ),
            )
            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            c["title"],
                            size=13,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                            color=theme.PRIMARY if is_selected else theme.TEXT_SECONDARY,
                            expand=True,
                        ),
                        delete_btn,
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=theme.PRIMARY_LIGHT if is_selected else None,
                border_radius=8,
                padding=ft.Padding(left=12, right=2, top=4, bottom=4),
                on_click=lambda e, cid=c["id"]: self._page_ref.run_task(
                    self._switch_conversation, cid
                ),
                ink=True,
            )
            self.conv_list.controls.append(row)
        self.update()

    async def _switch_conversation(self, conversation_id: int):
        self.is_responding = False
        self.send_btn.disabled = False
        self.conversation_id = conversation_id
        messages = await conv_db.get_messages(conversation_id)
        self.chat_list.controls.clear()
        for msg in messages:
            self.chat_list.controls.append(message_bubble(msg["role"], msg["content"]))
        self._show_chat_list()
        await self._load_conversations()

    async def _delete_conversation(self, conversation_id: int):
        await conv_db.delete(conversation_id)
        if self.conversation_id == conversation_id:
            self.is_responding = False
            self.send_btn.disabled = False
            self.conversation_id = None
            self.chat_list.controls.clear()
            self._chat_content.controls[0] = self.welcome
        await self._load_conversations()

    async def _on_new_conversation(self, e):
        model = await settings_db.get("default_model")
        cid = await conv_db.create(title="New Conversation", model_used=model or "")
        self.conversation_id = cid
        self.chat_list.controls.clear()
        self._show_chat_list()
        await self._load_conversations()

    async def _on_send(self, e):
        text = self.input_field.value.strip()
        if not text or self.is_responding:
            return

        if self.conversation_id is None:
            model = await settings_db.get("default_model")
            self.conversation_id = await conv_db.create(title=text[:50], model_used=model or "")
            await self._load_conversations()

        my_conv = self.conversation_id

        self._show_chat_list()
        self.chat_list.controls.append(message_bubble("user", text))
        self.input_field.value = ""
        self.is_responding = True
        self.send_btn.disabled = True
        self.status_text.value = ""
        self.update()

        await conv_db.add_message(my_conv, "user", text)

        try:
            model = await settings_db.get("default_model")
            agent = create_coach_agent(model)

            history_msgs = await conv_db.get_messages(my_conv)
            from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
            message_history = []
            for msg in history_msgs[:-1]:
                if msg["role"] == "user":
                    message_history.append(ModelRequest(parts=[UserPromptPart(content=msg["content"])]))
                else:
                    message_history.append(ModelResponse(parts=[TextPart(content=msg["content"])]))

            # Show animated thinking indicator while agent works
            thinking_container, thinking_label = _thinking_bubble()
            self.chat_list.controls.append(thinking_container)
            self.update()

            # Use iter() to properly handle the full agent loop (model -> tools -> model -> ...)
            # run_stream() breaks early when it sees text, skipping tool execution.
            async with agent.iter(text, message_history=message_history) as agent_run:
                node = agent_run.next_node
                while not agent.is_end_node(node):
                    if self.conversation_id != my_conv:
                        return  # user switched away — stop updating UI
                    if agent.is_call_tools_node(node):
                        # Show which tools are being called
                        tool_calls = node.model_response.tool_calls
                        if tool_calls:
                            labels = [_TOOL_LABELS.get(tc.tool_name, tc.tool_name) for tc in tool_calls]
                            thinking_label.value = " / ".join(labels)
                            thinking_label.update()
                    elif agent.is_model_request_node(node):
                        thinking_label.value = "Composing response"
                        thinking_label.update()
                    node = await agent_run.next(node)
                response_text = agent_run.result.output

            # Always save the response to the correct conversation
            await conv_db.add_message(my_conv, "assistant", response_text)

            # Only update UI if still viewing the same conversation
            if self.conversation_id != my_conv:
                return

            idx = self.chat_list.controls.index(thinking_container)
            self.chat_list.controls[idx] = message_bubble("assistant", response_text)
            self.update()

            if len(history_msgs) <= 1:
                title = text[:50] + ("..." if len(text) > 50 else "")
                await conv_db.update_title(my_conv, title)
                await self._load_conversations()

        except Exception as ex:
            if self.conversation_id != my_conv:
                return
            self.chat_list.controls.append(
                ft.Container(
                    content=ft.Text(f"Error: {ex}", color=theme.ERROR, size=13),
                    padding=10,
                )
            )
        finally:
            if self.conversation_id == my_conv:
                self.is_responding = False
                self.send_btn.disabled = False
                self.status_text.value = ""
                self.update()

    async def end_conversation(self):
        if self.conversation_id is None:
            return
        try:
            model = await settings_db.get("default_model")
            result = await curate_memories(self.conversation_id, model)
            if result and result.memories:
                self.status_text.value = f"Saved {len(result.memories)} memories from this conversation"
                self.update()
        except Exception:
            pass

    async def start_from_nudge(self, chat_context: str):
        """Start a new conversation pre-loaded with nudge context."""
        model = await settings_db.get("default_model")
        self.conversation_id = await conv_db.create(
            title="Coach Check-in", model_used=model or ""
        )
        my_conv = self.conversation_id

        self.chat_list.controls.clear()
        self._show_chat_list()
        await self._load_conversations()

        # Use the nudge context as the prompt to the agent
        prompt = chat_context or "I'd like to check in on my progress."
        self.is_responding = True
        self.send_btn.disabled = True
        self.update()

        try:
            agent = create_coach_agent(model)
            thinking_container, thinking_label = _thinking_bubble()
            self.chat_list.controls.append(thinking_container)
            self.update()

            async with agent.iter(prompt) as agent_run:
                node = agent_run.next_node
                while not agent.is_end_node(node):
                    if self.conversation_id != my_conv:
                        return
                    if agent.is_call_tools_node(node):
                        tool_calls = node.model_response.tool_calls
                        if tool_calls:
                            labels = [_TOOL_LABELS.get(tc.tool_name, tc.tool_name) for tc in tool_calls]
                            thinking_label.value = " / ".join(labels)
                            thinking_label.update()
                    elif agent.is_model_request_node(node):
                        thinking_label.value = "Composing response"
                        thinking_label.update()
                    node = await agent_run.next(node)
                response_text = agent_run.result.output

            await conv_db.add_message(my_conv, "assistant", response_text)

            if self.conversation_id != my_conv:
                return

            idx = self.chat_list.controls.index(thinking_container)
            self.chat_list.controls[idx] = message_bubble("assistant", response_text)
            self.update()

        except Exception as ex:
            if self.conversation_id != my_conv:
                return
            self.chat_list.controls.append(
                ft.Container(
                    content=ft.Text(f"Error: {ex}", color=theme.ERROR, size=13),
                    padding=10,
                )
            )
        finally:
            if self.conversation_id == my_conv:
                self.is_responding = False
                self.send_btn.disabled = False
                self.update()
