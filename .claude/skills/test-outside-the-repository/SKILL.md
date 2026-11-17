---
name: test-outside-the-repository
description: Test the Meta-Agent or a built bundle in a folder outside this repository that may be removed at any time, collect what the test sessions did, and bring what they showed back as records. Use when the person asks for a test of the agent or of a bundle, when a build or a template version is to be watched with a fresh session, when a collection is to be read for faults, and before a test folder is removed.
---

# Test outside the repository

A test is a *run*: a folder made from the committed head, in which sessions are opened, and which may be removed at any time. What the sessions did is kept in the log folder, which stays. Every command runs from the repository root.

## Make a run

1. **Know where.** `python contracts/tools/testfolder.py where` prints the test folder and the log folder of this computer. If one has not been said, ask the person; never choose a folder.
2. **Commit what is to be tested.** A run is the committed head and nothing else; the tool says how many uncommitted paths it left out.
3. **Make it.** `python contracts/tools/testfolder.py make` writes a clone of the repository, whose origin is a copy inside the run that never moves, and a copy of the newest build of every agent. `--bundle <build folder>` names builds instead, `--no-clone` and `--no-bundles` leave a part out. It prints the folder to open a session in for each. A run's name is never used again.

A bundle that a session built in the clone of an earlier run, and that is in no commit here, is tested standing alone from that clone: `python contracts/tools/testfolder.py make --no-clone --source <that run's repo folder> --bundle <its build folder>`. Make it before the earlier run is removed.

## Run the sessions

- **From the command line, with nobody present.** `python contracts/tools/testfolder.py session <run> <item> --brief <file> --model <model> --effort <effort>` runs one session in an item and waits for it; start it in the background when several run at once. It is given what the folder gives and nothing of the session that started it, and it runs in the permission mode the person chose for tests. What it was asked and what the command printed are kept in the log folder.
- **If the command says it could not log in,** the person signs the command-line `claude` in once at a terminal. A session never types a credential.
- **Through the application** only when the person wants to watch a session there, and only on a turn the person started. Such a session is also given the application's instructions for a session another one opened; say in your report which way each was run.
- **Fresh, always.** A fork carries this repository's conversation into the folder, and the test is of what the folder alone gives.
- **The brief** is what a user of the agent would say, and nothing of how. The briefs in use are files under `meta_agent/eval/briefs/`, one per kind of item, so that a later run is asked in the same words; a new one is added there. In a bundle: its start task and a question of the kind it was built for. In the clone: the role, and the person's request as the person gave it. Name no rule, skill or file of this repository to a bundle's session; a bundle stands alone.
- **The level** of each session comes from the `choose-session-level` skill, and the person's word holds over it. The collection says what each ran on.
- Leave the run alone while a session works in it.

## Collect, then read

`python contracts/tools/testfolder.py collect <run>` writes a new collection in the log folder and prints one line per session and per item. In it:

- `collection.json` — for each session what it was asked, the model, the skills it loaded, the files it wrote and which of them lie outside the folder it was opened in; for each bundle the files added, changed and removed; for the clone the commits, what is uncommitted and the gate's verdict line; and what the collection cannot show.
- `sessions/<item>/<session>.said.md` — what the session itself wrote to its reader, in order; its report is the last part. Start here: a session says what it could not find and what was unclear.
- `sessions/<item>/<session>.calls.jsonl` — every tool call in order, with the command, the file or the skill, and for a call that ended in an error the error's text. Read this before you rerun anything: it is the text of what the session ran.
- `sessions/<item>/<session>.jsonl` — the transcript as the application wrote it.
- `items/<item>/` — the changed files themselves, and for the clone the difference from the head it was made at.

A session removed from the application before the collection has left no transcript. Collect before a session is removed there.

## From a collection to the repository

Each fault goes where a failure goes, written by the seat that owns the path:

- a line in `meta_agent/failures.jsonl`, and a `case` when a cause is found (the `validate-and-record` skill);
- a fault in a bundle's text or scripts: a later template version, never an edit of a build;
- a check, a schema, a session skill or a `CLAUDE.md` that should change: a note to the design role, `python contracts/tools/notes.py ask --seat <your seat> --to design --task <id> "…"`, committed alone;
- what was watched and what was not: the task card.

Write a finding in your own words, and name the run, the collection and the session it was read from. Those are files on this computer and are not a record. Never commit a transcript, a calls file or a collection. A number in a test session's text is a model's and enters no card. A test decides no threshold.

## Remove

Remove a run when both roles have read its collection, not before. `python contracts/tools/testfolder.py wipe <run> --sessions` collects once more, removes the run's folder, and removes from the application's own folder the transcripts it has just collected of the sessions run in it; `--all` does it for every run that stands. A session the application lists is removed there, by the person's approval, before the run is. `python contracts/tools/testfolder.py status` lists every run, standing or removed, with its collections. The tool removes no folder but a run it made. A push from the clone ends in the run's own origin and goes with the run.
