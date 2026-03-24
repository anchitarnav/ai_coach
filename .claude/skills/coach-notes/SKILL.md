---
name: coach-notes
description: >
  Manage reference notes — persistent documents like policies, frameworks, meeting notes.
  Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[new | search <query> | <id> | edit <id>]"
---

# Reference Notes

@.claude/rules/coaching-persona.md

## Instructions

Based on `$ARGUMENTS`:

### No arguments
Run `python3 cli/db.py notes list` and display as a table: ID, Title, Tags, Last Updated.

### `new` or `add`
Ask the user for:
- **Title** (required)
- **Content** (the note body — can be long, markdown supported)
- **Tags** (comma-separated, optional)

Then run `python3 cli/db.py notes create --title "..." --content "..." --tags "..."`.

### A number (e.g., `3`)
Run `python3 cli/db.py notes get $ARGUMENTS` and show the full note content.

### `search <query>`
Run `python3 cli/db.py notes search "<query>"` and display matching notes.

### `edit <id>`
Run `python3 cli/db.py notes get <id>` to show current content. Ask what to change. Then run `python3 cli/db.py notes update <id> --title "..." --content "..." --tags "..."` with updated fields.

### `delete <id>`
Run `python3 cli/db.py notes delete <id>`. Confirm before deleting.
