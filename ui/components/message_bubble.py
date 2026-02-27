"""Chat message bubble component."""

import flet as ft
from ui import theme


def message_bubble(role: str, content: str) -> ft.Container:
    """Styled message bubble — user on right (indigo), coach on left (teal)."""
    is_user = role == "user"

    avatar = ft.CircleAvatar(
        content=ft.Text(
            "Y" if is_user else "C",
            size=13,
            weight=ft.FontWeight.W_600,
            color="#FFFFFF",
        ),
        bgcolor=theme.PRIMARY if is_user else theme.ACCENT,
        radius=16,
    )

    bubble = ft.Container(
        content=ft.Column(
            tight=True,
            spacing=2,
            controls=[
                ft.Text(
                    "You" if is_user else "Coach",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=theme.PRIMARY if is_user else theme.ACCENT,
                ),
                ft.Markdown(
                    content,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                ),
            ],
        ),
        bgcolor=theme.USER_BUBBLE if is_user else theme.COACH_BUBBLE,
        border=ft.Border.all(1, "#DDD6FE" if is_user else "#CCFBF1"),
        border_radius=ft.BorderRadius(
            top_left=2 if not is_user else 16,
            top_right=2 if is_user else 16,
            bottom_left=16,
            bottom_right=16,
        ),
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        expand=True,
    )

    row_controls = [avatar, bubble] if not is_user else [bubble, avatar]

    return ft.Container(
        content=ft.Row(
            controls=row_controls,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        margin=ft.Margin(
            left=0 if not is_user else 48,
            right=48 if not is_user else 0,
            top=0,
            bottom=6,
        ),
    )
