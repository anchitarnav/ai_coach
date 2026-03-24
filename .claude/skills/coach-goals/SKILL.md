---
name: coach-goals
description: >
  View, create, update, or archive career goals. Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[add | archive <id> | <id>]"
---

# Career Goals

@.claude/rules/coaching-persona.md

## Instructions

Based on `$ARGUMENTS`:

### No arguments
Run `python3 cli/db.py goals list` and display results as a formatted table with columns: ID, Title, Category, Priority (P1-P5). Add a coaching observation about their goals if relevant.

### `add` or `new`
Ask the user for:
- **Title** (required)
- **Description** (optional, but encouraged — ask a coaching question to draw it out)
- **Category**: leadership, technical, networking, communication, strategy, other
- **Priority**: 1 (Critical) to 5 (Someday)

Then run `python3 cli/db.py goals create --title "..." --description "..." --category "..." --priority N`.

### A number (e.g., `3`)
Run `python3 cli/db.py goals get $ARGUMENTS` to show full details. Offer to update or archive.

### `archive <id>`
Run `python3 cli/db.py goals update <id> --is_active 0`. Confirm to the user.

### `all`
Run `python3 cli/db.py goals list --all` to show both active and archived goals.
