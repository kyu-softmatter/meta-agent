---
name: end-session
description: Close a session's work. Sorts what went wrong into the places the next session will read, marks or releases the task, runs the gate and the tests, and reports. Use when a task is finished or given up, before reporting to the person or to a hub, and when the person asks what was learned.
---

# End a session

## Sort what went wrong

Go back through the session: every correction by the person, every refused check, every value that turned out wrong, every step that took more than one try. Each goes to a place that already exists. Add no new place.

| what it is | where it goes |
|---|---|
| a failure of a run, a build or a check | one line in `meta_agent/failures.jsonl`, append only |
| a cause you can show, with its evidence | a `case` card under `meta_agent/cases/`, then `python contracts/tools/cases.py index meta_agent/cases` |
| a step of a procedure that was wrong or missing | the session skill under `.claude/skills/` that holds the procedure |
| a rule that was unclear | the line of `CLAUDE.md` or `meta_agent/CLAUDE.md` it belongs to |
| a schema, a check or a vocabulary that should change | a note to the design role |

When the path is not your seat's, ask the role that owns it: `python contracts/tools/notes.py ask --seat <name> --to <role> "…"`, committed alone. Write a lesson as what to do next time, with the command or the file. Correct an existing line before adding one.

## Close the task

- **Finished.** The task card's status line says done with the date and your seat, and the row in `meta_agent/tasks/index.json` says done and names the last commit of the work. The index is the design role's; another role asks by note.
- **A design part landed and a part for another role remains.** The row says the design part is landed, so that `next` offers the task to that role.
- **Given up.** `python contracts/tools/tasks.py release <id> --seat <name> --why "…"`, committed alone.

## Run what judges it

```
python contracts/validate.py
python contracts/validate.py --expect-fail
python -m unittest discover -s contracts/tests
python -m unittest discover -s meta_agent/tests -t .
```

The second is needed when `contracts/` changed, the tests when code changed. Every number you report is read off these runs, and the verdict line names the tree it judged.

## Report

Ten lines or fewer, in the form the `open-sessions` skill gives: the task, what landed with its commit, the verdict line, what you asked and of whom, what comes next. Say plainly what is not done and what you did not check.

Whether a seat pushes on its own is not decided (`plan.md 14-29`). Ask the person before pushing.
