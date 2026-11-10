# meta-agent

One agent, `meta_agent/`, that builds scientific agents and maintains them. The design record is `plan.md`; the Korean plan it came from is frozen at `docs/origin/PLAN.ko.md` and is not edited. Before writing anything, read `plan.md` sections 3 (MP1–MP13), 6 (cards), 8 (checks) and 9 (seats).

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

## Where things are

- `contracts/tools/` — `seats.py` (names, role rows, the self-registration rule), read by the validator and `bootstrap.py seat`; `contracts/tests/` — their tests (`python -m unittest discover -s contracts/tests`).
- `contracts/` — schemas, vocabularies (`claim_kinds.json`, `grades.json`, `units.json`, `case_classes.json`), `registry/`, `seats.json`, `records.json`, `validate.py`, `examples/` and `examples/rejected/`, `hooks/`.
- `meta_agent/` — the agent. Its own `CLAUDE.md` says what it does and does not do.
- `docs/ideas/` — the person's words and decisions, dated. `docs/reference/` — reference cases. `docs/origin/` — the frozen Korean plan.

## Setup on a new clone

```
git config core.hooksPath contracts/hooks
git config committer.name "seat:<role>-<machine>-<YYYYMMDD>-<n>"
git config committer.email "<role>-<machine>-<YYYYMMDD>-<n>@seat.invalid"
set PYTHONUTF8=1   (or export PYTHONUTF8=1)
python contracts/validate.py
python bootstrap.py check
python bootstrap.py install node rea --yes
git config meta-agent.machine <tag>     (the tag the person gave this computer)
python bootstrap.py seat <role>         (the next free seat name here and its entry; --write adds it)
```

External tools are pinned in `tools.lock.json` and never vendored. `bootstrap.py` fetches them from their own sources into the user's tools home and changes no PATH or agent configuration; `.mcp.json` starts REA through it, and Claude Code asks once before it starts a project server. REA's tools are for binaries and runtime behaviour, and only under an `analysis_permission` (plan.md 5.1 S2).

Register the seat in `contracts/seats.json` before its first commit; an unregistered committer is reported, not refused, and gets no path check at all. Until `meta_agent/tasks/009` lands the self-registration check, `contracts/` is the design seat's alone, so a `meta-…` or `harness-…` session asks the design seat on its computer to add its entry.
