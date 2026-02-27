"""AI Career Coach — main entry point."""

import flet as ft
from storage.database import get_db, close_db
from storage import settings as settings_db
from services.llm_manager import set_api_key, PROVIDERS


async def main(page: ft.Page):
    # Initialize database
    await get_db()

    # Restore any saved API keys into the environment
    for provider_name, info in PROVIDERS.items():
        saved_key = await settings_db.get(f"api_key_{provider_name}")
        if saved_key:
            set_api_key(provider_name, saved_key)

    # Import and create the app (after DB init)
    from ui.app import CoachApp
    CoachApp(page)


ft.run(main)
