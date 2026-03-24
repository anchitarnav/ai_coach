---
name: coach-reflect
description: >
  Guided reflection session pulling from goals, commitments, diary, and memories.
  Helps you step back and see patterns. Works standalone or within /coach-mode.
user-invocable: true
argument-hint: "[topic to reflect on]"
---

# Guided Reflection

@.claude/rules/coaching-persona.md

## Instructions

1. Run `python3 cli/db.py context snapshot` to gather full coaching context.

2. If `$ARGUMENTS` has a specific topic, focus the reflection on that topic while weaving in relevant context from the database.

3. If no arguments, structure the reflection around these areas:

   **Progress toward goals** — What moved forward recently? What's stalled?

   **Commitments** — What did you follow through on? What's overdue? What patterns do you see?

   **Diary themes** — What's been on your mind lately? Any emotional patterns?

   **Open questions** — What's unresolved? What decisions are you avoiding?

4. Ask open-ended coaching questions based on what you see in the data. Don't just summarize — provoke thought.

5. After the reflection conversation, save any important insights:
   - `python3 cli/db.py memories add --content "..." --tags "reflection,insight" --source "agent_curated"`

6. Track any new commitments that emerge:
   - `python3 cli/db.py commitments create --what "..." --due_date YYYY-MM-DD`
