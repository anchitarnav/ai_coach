---
name: coach-journal
description: >
  Write a diary entry with mood tracking. Generates AI title, extracts memories
  and commitments. Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[your entry text]"
---

# Journal Entry

@.claude/rules/coaching-persona.md

## Instructions

### If `$ARGUMENTS` has content
Use it as the diary entry text. Ask for mood if not obvious from the text.

### If no arguments
Ask the user: "How was your day?" or "What's on your mind?" Gather their entry naturally through conversation. Ask for mood.

### Mood options
happy, neutral, stressed, frustrated, energized, reflective, anxious (or user's own word)

### Saving the entry
1. Run `python3 cli/db.py diary create --date YYYY-MM-DD --content "..." --mood "..."` with today's date.

2. **Generate a title** — a short, descriptive title (5-8 words) capturing the main theme. Examples: "Difficult 1:1 with manager", "Excited about new project lead role".

3. Run `python3 cli/db.py diary update <id> --title "generated title"`.

4. **Extract memories** worth saving — key decisions, work context, insights, relationship dynamics. For each:
   - Run `python3 cli/db.py memories add --content "..." --tags "tag1,tag2" --source "diary_derived"`

5. **Identify commitments** — things the user said they'll do. For each:
   - Run `python3 cli/db.py commitments create --what "..." --due_date YYYY-MM-DD`

6. **Schedule follow-ups** for things the coach should check back on:
   - Run `python3 cli/db.py tasks create --wake_at "ISO_TIMESTAMP" --context "..." --source "diary_processing"`

7. Give a brief coaching response acknowledging the entry. Keep it warm and concise.
