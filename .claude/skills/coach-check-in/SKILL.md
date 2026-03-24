---
name: coach-check-in
description: >
  On-demand proactive coaching check-in. Analyzes your current state and surfaces
  anything that needs attention. Works standalone or within /coach-mode.
user-invocable: true
---

# Coaching Check-In

@.claude/rules/coaching-persona.md

## Instructions

1. Run `python3 cli/db.py context snapshot` to gather full coaching context.

2. Analyze the context like a proactive coaching engine. Look for:
   - **Overdue commitments** — anything past its due date
   - **Approaching deadlines** — commitments due in the next 2 days
   - **Goal progress** — goals that haven't seen any activity recently
   - **Diary patterns** — stress, frustration, or repeated themes
   - **Fired scheduled tasks** — things the coach previously scheduled to check on

3. Follow these guidelines (from the proactive coaching system):
   - It's perfectly fine to report nothing. Don't nudge just because you can.
   - Surface at most 2 items that need attention.
   - Consider the day of week: lighter on weekends, more actionable on weekday mornings.
   - If the user was active recently, they probably don't need reminding.

4. Present findings directly and concisely. For each item:
   - What needs attention
   - Why it matters (connect to goals)
   - A suggested next action

5. Offer to dive deeper into any topic that surfaces.
