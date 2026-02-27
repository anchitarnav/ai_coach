"""macOS native notifications via osascript."""

import asyncio
import shlex
import sys


async def send_notification(title: str, message: str) -> None:
    """Send a macOS notification. Fails silently on non-macOS or if permissions are missing."""
    if sys.platform != "darwin":
        return
    script = f'display notification {shlex.quote(message)} with title {shlex.quote(title)}'
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
    except Exception:
        pass
