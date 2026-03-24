"""macOS native notifications via osascript."""

import asyncio
import sys


def _applescript_quote(s: str) -> str:
    """Escape a string for AppleScript double-quoted literals."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


async def send_notification(title: str, message: str) -> tuple[bool, str]:
    """Send a macOS notification. Returns (success, detail_message)."""
    if sys.platform != "darwin":
        return False, "Not running on macOS"
    script = f'display notification {_applescript_quote(message)} with title {_applescript_quote(title)}'
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode().strip() if stderr else "Unknown error"
            return False, f"osascript exited {proc.returncode}: {err}"
        return True, "Notification sent"
    except Exception as exc:
        return False, f"Exception: {exc}"
