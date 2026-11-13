# meta-agent

One agent, `meta_agent/`, that builds scientific agents and maintains them. The design record is `plan.md`; the Korean plan it came from is frozen at `docs/origin/PLAN.ko.md` and is not edited. Begin every session with the `begin-session` skill, before any other write: it seats you first, and on your first session here it has you read `plan.md` sections 3 (MP1–MP13), 6 (cards), 8 (checks) and 9 (seats). Every command in this file, in `meta_agent/CLAUDE.md` and in the session skills is run from the repository root.

## Rules that bind every session here

- English in every file. When recording the person's decision, quote their words verbatim (Korean included) with an English gloss, in `docs/ideas/<YYYYMMDD>.md`.
- Every hand-over is a card on disk. JSON is the record, MD is for people, and every number in an MD exists in a card of the same folder (check 3).
- A number is `{name, value, unit, source, grade, value_kind}`. The grade is derived from `contracts/grades.json`, never stated by hand. A model's number is E6 and enters nothing.
- Claims are `observed | derived | inferred | unknown`; settings are `confirmed | inferred | unknown`. An inference is a recommendation. Only a person confirms. Policy, permissions and publication scope are never inferred.
- The person alone writes safety values, grants analysis permission, chooses thresholds, releases `held`, hands bundles over, and names roles and machine tags. A session may seat itself under the person's standing rule of 2026-11-09 (`docs/ideas/20261109.md`, plan.md 9): a name of the pattern below on a machine tag already given, the role the person or its task names, the role's paths copied unchanged, registered in its own commit before any other work, `seated_by: self`.
- One working copy on `main`, no worktrees, and several seats may work in it at once: commit only the paths you name (never `git add -A`), and when another seat shares the folder set the committer for the commit itself (`GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`), not in the repository's configuration. Commit as your seat: committer `seat:<name>` <`<name>@seat.invalid`>, author the person. Your paths are in `contracts/seats.json`; a crossing fails check 6.
- The gate is `python contracts/validate.py`; run it before you start and before you report. The pre-commit hook runs `--staged`. Never `--no-verify`; if it ever happens, the commit message says so.
- A new check lands with its rejected fixture in the same commit, and the fixture is watched failing first. `--expect-fail` must reject both totals in full.
- Records are append-only; a change is a new file `v<N>_<name>` (check 7). Proposals land nothing.
- Every number you report is read off a run, and the verdict line names the judged tree.
- A testbed tests; it does not shape (the person, 2026-11-11, plan.md 10, 14-37). Nothing is developed now for the rheometer or its simulation engine. A general mechanism (a skill kind, a card, a check, a subagent drawing, a runner) counts as done only when it runs on fixtures of at least two unrelated kinds, one of them not rheology.
- This agent and the agents it builds work from skills (the person, 2026-11-12, `docs/ideas/20261112.md`). What a session does is in a session skill under `.claude/skills/`, loaded when it is needed; what binds it is in this file and in `meta_agent/CLAUDE.md`. A session skill holds no rule that is not also in one of the two, no number, no limit and no threshold (check 24). Every calculation of a quantity is a library skill, run through the runner; a session skill is never written per library skill.
- A session is opened fresh, with only its brief, or as a fork, which inherits a conversation. Either is its own seat: a fork never commits as the seat whose conversation it inherited. Between sessions a note is the record, and a message only points at a committed path.

## Session skills

- `begin-session` — at the start of every session, before any other write: the gate, the seat and its commit, the notes for your role, the task and its claim; and the setup of a clone that has none.
- `open-sessions` — when work is split over other sessions: fresh or fork, the brief, the report form, reading a report against its commit.
- `choose-session-level` — before a session or a subagent is opened: which model and how much effort, by the kind of work; a recommendation, and the person's word holds over it.
- `end-session` — when a task is finished or given up: where each lesson goes, closing the task, the gate and the tests, the report.

The skills for the Meta-Agent's own work are named in `meta_agent/CLAUDE.md`.

## Where things are

- `contracts/tools/` — `seats.py` (names, role rows, the self-registration rule), read by the validator and `bootstrap.py seat`; `seat_commit.py --seat <name> -m <message> <paths…>` commits as a seat, only the named paths, when other seats share the folder; `tasks.py list | next --role <role> | claim <id> --seat <name> | release` reads and takes the task queue (`meta_agent/tasks/index.json`, `claims/`); `skills.py check <skill folder>` says what check 22 would about one skill (manifest, source read, worked cases run), and `contracts/skill_kinds.json` lists the kinds; `sheets.py check <parameter_sheet.json>` says what checks 4 and 19 would about one sheet (bounds recomputed, the interval, what was left out, safety rows); `cases.py index <store>` writes a `cases/` or `knowledge/` store's index and holds what a condition tag and a reference mean (checks 5 and 8, and recall); `notes.py list --role <role> | ask | reply | withdraw` is how seats ask each other (`meta_agent/inbox/seats/`), and an ask without a reply shows as PENDING in the gate; `session_skills.py check <skill folder>` says what check 24 would about one session skill (front matter, the paths and commands it names, where it is named, no number); `contracts/tests/` — their tests (`python -m unittest discover -s contracts/tests`).
- `contracts/` — schemas, vocabularies (`claim_kinds.json`, `grades.json`, `units.json`, `case_classes.json`), `registry/`, `seats.json`, `records.json`, `validate.py`, `examples/` and `examples/rejected/`, `hooks/`.
- `.claude/skills/` — the session skills, one folder each with a `SKILL.md`.
- `meta_agent/` — the agent. Its own `CLAUDE.md` says what it does and does not do.
- `docs/ideas/` — the person's words and decisions, dated. `docs/reference/` — reference cases. `docs/origin/` — the frozen Korean plan.

## Commits and external tools

Commit with `seat_commit.py` always. `git config committer.name "seat:<name>"` and `committer.email` belong only to a clone one seat uses alone; never set them where another seat is working, since the repository holds one value.

External tools are pinned in `tools.lock.json` and never vendored. `bootstrap.py` fetches them from their own sources into the user's tools home and changes no PATH or agent configuration; `.mcp.json` starts REA through it, and Claude Code asks once before it starts a project server. REA's tools are for binaries and runtime behaviour, and only under an `analysis_permission` (plan.md 5.1 S2).

Register the seat in `contracts/seats.json` before its first commit; an unregistered committer is reported, not refused, and gets no path check at all. A session that seats itself runs `python bootstrap.py seat <role> --write` and commits `contracts/seats.json` alone with `seat_commit.py`; check 6 passes that one commit for any role when the entry follows the standing rule, and fails it otherwise.
