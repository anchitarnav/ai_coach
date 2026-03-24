---
name: coach-weekly-review
description: >
  Structured weekly review of goals, commitments, diary themes, and next week planning.
  Best used on Friday afternoons or Monday mornings. Works standalone or within /coach-mode.
user-invocable: true
---

# Weekly Review

@.claude/rules/coaching-persona.md

## Instructions

1. Run `python3 cli/db.py context snapshot` to gather full coaching context.

2. Also run `python3 cli/db.py diary recent --days 7` and `python3 cli/db.py commitments list --limit 20` for the full week's data.

3. Walk through the review structure:

   ### Goal Progress
   For each active goal, summarize what happened this week. Reference specific diary entries and memories.

   ### Commitments Scorecard
   - Completed this week
   - Missed or overdue
   - Still pending
   Calculate a completion rate if there's enough data.

   ### Key Themes
   Patterns from diary entries — what came up repeatedly? Any emotional trends?

   ### Wins
   Ask the user to name their biggest win this week. Celebrate it.

   ### Next Week
   Help set 2-3 specific commitments for the coming week. Make them concrete and time-bound.

4. Ask the user to rate their week (1-10) and capture as a diary entry:
   - `python3 cli/db.py diary create --date YYYY-MM-DD --content "Weekly review: [summary]" --mood "..." --title "Week N Review"`

5. Save a review summary as memory:
   - `python3 cli/db.py memories add --content "Weekly review [date]: [key takeaways]" --tags "weekly-review" --source "agent_curated"`
