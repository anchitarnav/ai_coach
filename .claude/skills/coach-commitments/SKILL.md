---
name: coach-commitments
description: >
  View and manage commitments — things you said you'd do. Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[done <id> | cancel <id> | add <text> | overdue]"
---

# Commitment Tracking

@.claude/rules/coaching-persona.md

## Instructions

Based on `$ARGUMENTS`:

### No arguments
1. Run `python3 cli/db.py commitments overdue` and `python3 cli/db.py commitments pending` (in parallel).
2. Display grouped by urgency:
   - **Overdue** (bold, with days overdue)
   - **Due today**
   - **Due this week**
   - **Due later**
   - **No due date**
3. Add a brief coaching observation if there are overdue items.

### `done <id>`
Run `python3 cli/db.py commitments complete <id>`. Celebrate briefly.

### `cancel <id>`
Run `python3 cli/db.py commitments cancel <id>`. Acknowledge without judgment.

### `miss <id>`
Run `python3 cli/db.py commitments miss <id>`. Be supportive — ask what got in the way.

### `add <text>`
Ask for a due date if not included. Then run `python3 cli/db.py commitments create --what "<text>" --due_date YYYY-MM-DD`.

### `overdue`
Run `python3 cli/db.py commitments overdue` and display with coaching nudge.

### `all`
Run `python3 cli/db.py commitments list` to show all commitments including completed/missed.
