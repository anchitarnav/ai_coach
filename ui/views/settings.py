"""Settings view — LLM provider config, API keys, preferences."""

import flet as ft
from services.llm_manager import detect_providers, get_available_models, set_api_key, PROVIDERS
from services.notifications import send_notification
from storage import settings as settings_db
from ui import theme


class SettingsView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
        self._page_ref = page_ref

        self.provider_list = ft.Column(spacing=12)
        self.model_dropdown = ft.Dropdown(
            label="Default Model", width=420,
            on_select=self._on_model_change,
        )
        self.status_text = ft.Text("", size=13, color=theme.SUCCESS)

        # ── Proactive coaching controls ────────────────────────
        self.proactive_switch = ft.Switch(
            label="Enable proactive coaching",
            value=True,
            on_change=self._on_proactive_toggle,
        )
        self.quiet_start = ft.TextField(
            label="Quiet hours start", hint_text="22:00", width=140,
            border_radius=theme.INPUT_RADIUS,
            on_blur=self._on_quiet_hours_change,
        )
        self.quiet_end = ft.TextField(
            label="Quiet hours end", hint_text="07:00", width=140,
            border_radius=theme.INPUT_RADIUS,
            on_blur=self._on_quiet_hours_change,
        )
        self.heartbeat_dropdown = ft.Dropdown(
            label="Check-in interval", width=200,
            options=[
                ft.dropdown.Option(key="900", text="15 minutes"),
                ft.dropdown.Option(key="1800", text="30 minutes"),
                ft.dropdown.Option(key="3600", text="1 hour"),
                ft.dropdown.Option(key="7200", text="2 hours"),
            ],
            value="900",
            on_select=self._on_heartbeat_change,
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    spacing=theme.SECTION_GAP,
                    controls=[
                        theme.heading("Settings", size=24),
                        theme.section_divider(),

                        # ── Providers section ─────────────────────────
                        theme.subheading("LLM Providers", size=17),
                        ft.Text(
                            "API keys are auto-detected from environment variables. "
                            "You can also configure them below for the current session.",
                            size=13, color=theme.TEXT_SECONDARY,
                        ),
                        self.provider_list,

                        theme.section_divider(),

                        # ── Model section ─────────────────────────────
                        theme.subheading("Default Model", size=17),
                        ft.Text(
                            "Select which model the coach uses by default.",
                            size=13, color=theme.TEXT_SECONDARY,
                        ),
                        self.model_dropdown,
                        self.status_text,

                        theme.section_divider(),

                        # ── Proactive coaching section ────────────────
                        theme.subheading("Proactive Coaching", size=17),
                        ft.Text(
                            "When enabled, the coach periodically checks your goals and commitments "
                            "and sends helpful nudges and reminders.",
                            size=13, color=theme.TEXT_SECONDARY,
                        ),
                        self.proactive_switch,
                        ft.Row(
                            controls=[self.quiet_start, self.quiet_end],
                            spacing=12,
                        ),
                        self.heartbeat_dropdown,

                        theme.section_divider(),

                        # ── Test notifications section ──────────────
                        theme.subheading("Notifications", size=17),
                        ft.Text(
                            "Send a test notification to verify macOS notifications are working.",
                            size=13, color=theme.TEXT_SECONDARY,
                        ),
                        ft.Button(
                            "Send Test Notification",
                            icon=ft.Icons.NOTIFICATIONS_ACTIVE,
                            on_click=self._on_test_notification,
                            color="#FFFFFF", bgcolor=theme.PRIMARY,
                        ),
                    ],
                ),
                padding=ft.Padding(left=theme.PAGE_PAD, right=theme.PAGE_PAD, top=theme.PAGE_PAD, bottom=40),
            )
        ]

    def did_mount(self):
        self._page_ref.run_task(self._load_settings)

    async def _load_settings(self):
        providers = detect_providers()
        self.provider_list.controls.clear()

        for p in providers:
            env_var = PROVIDERS[p.name]["env_var"]

            if p.available:
                status_row = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.SUCCESS, size=18),
                    ft.Text(p.display_name, size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                    theme.pill("Connected", theme.SUCCESS, "#ECFDF5"),
                ], spacing=8)
                body = ft.Text(f"{env_var} detected", size=12, color=theme.TEXT_MUTED)
            else:
                status_row = ft.Row([
                    ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=theme.TEXT_MUTED, size=18),
                    ft.Text(p.display_name, size=14, weight=ft.FontWeight.W_600, color=theme.TEXT),
                    theme.pill("Not configured", theme.TEXT_MUTED, theme.SURFACE_DIM),
                ], spacing=8)

                key_field = ft.TextField(
                    label=env_var, hint_text="Paste API key...",
                    password=True, can_reveal_password=True,
                    width=360, border_radius=theme.INPUT_RADIUS,
                )
                save_btn = ft.Button(
                    "Save", on_click=lambda e, pn=p.name, kf=key_field: self._page_ref.run_task(self._save_key, pn, kf),
                    color="#FFFFFF", bgcolor=theme.PRIMARY,
                )
                body = ft.Row([key_field, save_btn], spacing=8, vertical_alignment=ft.CrossAxisAlignment.END)

            self.provider_list.controls.append(
                theme.card(ft.Column(controls=[status_row, body], spacing=10))
            )

        # ── Model dropdown ────────────────────────────────────────────
        models = get_available_models()
        self.model_dropdown.options = [ft.dropdown.Option(m) for m in models] if models else [
            ft.dropdown.Option("No models available")
        ]

        current = await settings_db.get("default_model")
        if current and current in models:
            self.model_dropdown.value = current
        elif models:
            self.model_dropdown.value = models[0]

        # ── Proactive coaching settings ─────────────────────────
        proactive = await settings_db.get("proactive_enabled")
        self.proactive_switch.value = proactive != "false"

        qs = await settings_db.get("quiet_hours_start")
        qe = await settings_db.get("quiet_hours_end")
        if qs:
            self.quiet_start.value = qs
        if qe:
            self.quiet_end.value = qe

        hb = await settings_db.get("heartbeat_interval")
        if hb:
            self.heartbeat_dropdown.value = hb

        self.update()

    async def _save_key(self, provider_name: str, field: ft.TextField):
        key = field.value.strip()
        if not key:
            return
        set_api_key(provider_name, key)
        await settings_db.set(f"api_key_{provider_name}", key)
        self.status_text.value = f"API key for {provider_name} saved."
        field.value = ""
        await self._load_settings()

    async def _on_model_change(self, e):
        model = self.model_dropdown.value
        if model and "No models" not in model:
            await settings_db.set("default_model", model)
            self.status_text.value = f"Default model set to {model}"
            self.update()

    async def _on_proactive_toggle(self, e):
        val = "true" if self.proactive_switch.value else "false"
        await settings_db.set("proactive_enabled", val)

    async def _on_quiet_hours_change(self, e):
        start = self.quiet_start.value.strip()
        end = self.quiet_end.value.strip()
        if start:
            await settings_db.set("quiet_hours_start", start)
        if end:
            await settings_db.set("quiet_hours_end", end)

    async def _on_heartbeat_change(self, e):
        val = self.heartbeat_dropdown.value
        if val:
            await settings_db.set("heartbeat_interval", val)

    async def _on_test_notification(self, e):
        ok, detail = await send_notification(
            "AI Career Coach",
            "Notifications are working! You'll receive coaching nudges here.",
        )
        if ok:
            self.status_text.value = "Test notification sent — check your notification center."
            self.status_text.color = theme.SUCCESS
        else:
            self.status_text.value = f"Notification failed: {detail}"
            self.status_text.color = theme.ERROR
        self.update()
