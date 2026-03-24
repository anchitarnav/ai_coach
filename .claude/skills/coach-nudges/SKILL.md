---
name: coach-nudges
description: >
  View and manage pending nudges from the proactive coaching system.
  Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[snooze <id> | dismiss <id>]"
---

# Nudge Management

@.claude/rules/coaching-persona.md

## Instructions

Based on `$ARGUMENTS`:

### No arguments
1. Run `python3 cli/db.py nudges pending` to get pending nudges.
2. Display each nudge with:
   - **Priority badge**: gentle / important / urgent
   - **Message**
   - **Created at**
3. For each nudge, offer actions:
   - **Talk** — Start a coaching conversation about this nudge's topic (use the nudge's `chat_context` field as context)
   - **Snooze** — Options: 1 hour, 4 hours, tomorrow 9 AM, next week Monday 9 AM
   - **Dismiss** — Remove permanently

### `snooze <id> [duration]`
Calculate the snooze-until timestamp based on duration (default 1 hour). Run `python3 cli/db.py nudges snooze <id> --until "ISO_TIMESTAMP"`.

### `dismiss <id>`
Run `python3 cli/db.py nudges dismiss <id>`. Confirm.

### `history`
Run `python3 cli/db.py nudges history` and display past nudges with their status.

### If user wants to "talk" about a nudge
Read the nudge's `chat_context` field and start a coaching conversation focused on that topic. Use the full coaching persona and access to all data tools.
