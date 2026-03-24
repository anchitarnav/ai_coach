---
name: coach-memory
description: >
  Browse, search, or add coaching memories. Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[search <query> | add <content> | recent]"
---

# Coaching Memory

@.claude/rules/coaching-persona.md

## Instructions

Based on `$ARGUMENTS`:

### No arguments or `recent`
Run `python3 cli/db.py memories recent --days 14` and display results showing: content, source (user_added / agent_curated / diary_derived), tags, relevance score, date.

### `search <query>`
Run `python3 cli/db.py memories search "<query>"` and display results with relevance ranking.

### `add <content>`
Run `python3 cli/db.py memories add --content "<content>" --tags "" --source "user_added"`. Ask if they want to add tags.

### `all`
Run `python3 cli/db.py memories list` to show all memories.

### `delete <id>`
Run `python3 cli/db.py memories delete <id>`. Confirm before deleting.
