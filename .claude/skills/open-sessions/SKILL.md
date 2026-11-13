---
name: open-sessions
description: Open other sessions for work that splits into tasks, each fresh or as a fork, give each its brief, and read what they report. Use when the person asks for work to be split, run in parallel or handed to another session, when a task has parts for more than one role, or when this conversation has grown long and the remaining work stands on files alone.
---

# Open sessions: one hub, one task per session

The session the person speaks to is the hub. It opens the others, relays, checks what they report and tells the person. It takes none of their tasks.

## Before opening any

- **The person's word.** Open sessions when the person asked for them or has said sessions may be opened for this work. Otherwise ask once.
- **A task card for each.** A session's task is a file under `meta_agent/tasks/` with its row in `meta_agent/tasks/index.json`. If the work has no card, the design role writes one first. A session without a card has nothing to stand on.
- **One writer per file.** Roles already have different paths. Where two sessions of one role would share a path, name each one's files in its brief.
- **Never two sessions on one task and role.** `python contracts/tools/tasks.py list` shows who holds what.

## Fresh or fork, chosen per session

- **Fresh** gets only its brief. It is the default, and always the choice once this conversation is long.
- **Fork** inherits this whole conversation. Use it only while the conversation is short and holds something the new session needs that is not yet on disk.
- Either way the new session is its own seat. A fork inherits your seat's name with the conversation and must not commit as you: its brief says to run `begin-session` first.

## The brief of a fresh session

It must stand alone. In this order:

1. `Read <path of the task card> first.`
2. The role, and: `Run the begin-session skill before any other write.`
3. The files it may write, where its role's paths are shared with another session.
4. What done looks like, taken from the task card's own lines.
5. Whom it reports to, and the report form below.

## Model and effort

Use the `choose-session-level` skill: a level per session by the kind of work, one step up or down for a stated reason. Tell the person which session runs on what, and put each session's level in its brief. A model or an effort the person names holds over the skill's.

## How sessions exchange

- **A note is the record.** Anything that crosses a path boundary, changes who does what, or must be readable by a later session is a note: `python contracts/tools/notes.py ask --seat <name> --to <role> "…"`, committed alone. An ask without a reply shows as pending in the gate.
- **A message only points.** Where the application lets sessions message each other, a message names a committed path and its commit. It carries no decision and no number that is not already in a committed file. Nothing may depend on messages: a session in a terminal or on another computer has notes only.
- **The report form**, the same from every session:
  ```
  task     <id and role>
  landed   <commit> <paths>
  verdict  <the validator's last line, read off a run>
  asks     <note id and the role asked, or nothing>
  next     <what comes next, and whose it is>
  ```

## When a session reports

Its report is its claim. Before you tell the person, read the commit (`git show --stat <commit>`) and run `python contracts/validate.py` yourself. Say what you checked and what you did not.

## What stays the person's

Seating outside the standing rule, safety values, thresholds, the release of anything `held`, hand-over, and whether anything is pushed. A hub decides none of these for the sessions it opened.
