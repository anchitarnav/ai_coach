#!/usr/bin/env python3
"""SessionStart hook: surfaces pending nudges and overdue commitments.

Uses synchronous sqlite3 (not aiosqlite) for speed — hooks must be fast.
Outputs nothing if there's nothing pending (no noise).
"""

import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path.home() / ".ai_coach" / "data.db"


def main():
    if not DB_PATH.exists():
        return

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=2)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        return

    try:
        messages = []

        # Pending nudges
        try:
            cursor = conn.execute(
                """SELECT message, priority FROM nudges
                   WHERE status IN ('pending', 'shown')
                     AND (snoozed_until IS NULL OR snoozed_until <= datetime('now'))
                   ORDER BY
                     CASE priority WHEN 'urgent' THEN 0 WHEN 'important' THEN 1 ELSE 2 END,
                     created_at ASC
                   LIMIT 5"""
            )
            nudges = cursor.fetchall()
        except sqlite3.Error:
            nudges = []

        # Overdue commitments
        try:
            today = date.today().isoformat()
            cursor = conn.execute(
                """SELECT what, due_date FROM commitments
                   WHERE status = 'pending' AND due_date < ?
                   ORDER BY due_date ASC
                   LIMIT 5""",
                (today,),
            )
            overdue = cursor.fetchall()
        except sqlite3.Error:
            overdue = []

        if not nudges and not overdue:
            return

        if nudges:
            messages.append(f"**{len(nudges)} pending nudge{'s' if len(nudges) != 1 else ''}:**")
            for n in nudges:
                priority_marker = {"urgent": "!!", "important": "!", "gentle": "~"}.get(n["priority"], "~")
                messages.append(f"  [{priority_marker}] {n['message']}")

        if overdue:
            messages.append(f"**{len(overdue)} overdue commitment{'s' if len(overdue) != 1 else ''}:**")
            for c in overdue:
                days = (date.today() - date.fromisoformat(c["due_date"])).days
                messages.append(f"  - {c['what']} ({days}d overdue)")

        messages.append("")
        messages.append("Use `/nudges`, `/commitments`, or `/coach-mode` to take action.")

        print("\n".join(messages))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
