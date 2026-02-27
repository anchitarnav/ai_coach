"""Design system — colors, spacing, and shared styles.

All UI files import from here so the look is consistent and easy to change.
Forces light mode with a professional, warm color palette.
"""

import flet as ft

# ── Brand palette ──────────────────────────────────────────────────────────
PRIMARY = "#4F46E5"        # Indigo-600  – primary actions, active nav
PRIMARY_LIGHT = "#EEF2FF"  # Indigo-50   – selected/hover backgrounds
ACCENT = "#0D9488"         # Teal-600    – coach avatar, success states
ACCENT_LIGHT = "#F0FDFA"   # Teal-50     – coach bubble bg

SURFACE = "#FFFFFF"
SURFACE_DIM = "#F8FAFC"    # Slate-50   – page/card background
BORDER = "#E2E8F0"         # Slate-200  – subtle dividers & card borders
BORDER_FOCUS = "#CBD5E1"   # Slate-300

TEXT = "#0F172A"           # Slate-900
TEXT_SECONDARY = "#475569" # Slate-600
TEXT_MUTED = "#94A3B8"     # Slate-400

USER_BUBBLE = "#EEF2FF"   # Indigo-50
COACH_BUBBLE = "#F0FDFA"  # Teal-50

ERROR = "#DC2626"          # Red-600
SUCCESS = "#059669"        # Emerald-600
WARNING = "#D97706"        # Amber-600

# ── Priority colors (for nudges/notifications) ───────────────────────────
PRIORITY_COLORS = {
    "gentle": ("#0D9488", "#F0FDFA"),     # Teal
    "important": ("#D97706", "#FFFBEB"),  # Amber
    "urgent": ("#DC2626", "#FEF2F2"),     # Red
}
NOTIFICATION_BG = "#F0F9FF"  # Light blue

# ── Spacing constants ──────────────────────────────────────────────────────
PAGE_PAD = 28
SECTION_GAP = 24
CARD_PAD = 16
CARD_RADIUS = 12
INPUT_RADIUS = 10

# ── Typography helpers ─────────────────────────────────────────────────────

def heading(text: str, size: int = 22) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.W_700, color=TEXT)


def subheading(text: str, size: int = 15) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.W_600, color=TEXT)


def caption(text: str) -> ft.Text:
    return ft.Text(text, size=12, color=TEXT_MUTED)


# ── Shared widget builders ─────────────────────────────────────────────────

def card(content: ft.Control, **kwargs) -> ft.Container:
    """Standard card container with border, radius, and padding."""
    return ft.Container(
        content=content,
        bgcolor=SURFACE,
        border=ft.Border.all(1, BORDER),
        border_radius=CARD_RADIUS,
        padding=CARD_PAD,
        **kwargs,
    )


def section_divider() -> ft.Container:
    return ft.Container(
        height=1,
        bgcolor=BORDER,
        margin=ft.Margin(left=0, right=0, top=4, bottom=4),
    )


def pill(label: str, color: str = PRIMARY, bg: str = PRIMARY_LIGHT) -> ft.Container:
    """Small colored badge / pill."""
    return ft.Container(
        content=ft.Text(label, size=11, weight=ft.FontWeight.W_500, color=color),
        bgcolor=bg,
        border_radius=6,
        padding=ft.Padding(left=8, right=8, top=3, bottom=3),
    )


def configure_page(page: ft.Page):
    """Apply global theme settings to the Flet page."""
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = SURFACE_DIM
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        font_family="Inter, SF Pro Text, -apple-system, system-ui, sans-serif",
    )
    page.padding = 0
