# meta-agent

An agent that builds scientific agents for a lab's instruments and simulation engines, and automates the work around building and running them: **working out how a lab's materials and data are laid out, searching the related literature, keeping the workflow, convening the meeting in which a plan is settled, and building the skills an agent works with.** Everything it hands over is a card on disk, and a deterministic validator judges every card. A person decides (safety values, thresholds, what is released, what is handed over); the agent builds and proposes, and it never operates an instrument.

## What it automates

| | What is automated | How | Where it stands (read off the repository, 2026-11-11) |
|---|---|---|---|
| 1 | **Working out how a lab's materials and data are laid out** | Onboarding reads a lab's repositories, documents and tools and writes what it found, every item `inferred` with its evidence or `unknown`, and asks only what is unknown. A tool profile then states what an instrument or an engine takes and gives, each claim `observed`, `derived`, `inferred` or `unknown`. | Runs on fixtures: `meta_agent/src/onboarding/`, `meta_agent/src/tooling/`, three lab profiles and two requests under `meta_agent/`. Intake of dropped materials is open (`tasks/005`). |
| 2 | **Searching the related literature** | Materials a person drops, or sources a session retrieves, are recorded with their address, time and hash; what is found becomes entries with a source and a grade, and what is not found is a gap that names what was searched. A number is taken from a source that was read, never recalled. | Partly: three correlations of water were written from two sources read in a session, and a paper that could not be read is recorded as a gap. The working index over a lab's materials is open (`tasks/005`); no crawler exists and none is planned. |
| 3 | **Keeping the workflow** | Sessions seat themselves, claim a task, commit only their own paths, and ask each other through notes; the Designer takes a request from intake to a validated bundle in fixed steps; past cases are recalled before a card is written; the same gate runs on every commit and on GitHub. | Runs: seats, the task queue, notes and the gate (`tasks/009`); recall over 238 seed cases (`tasks/006`). The loop that improves built agents from their runs is open (`tasks/008`). |
| 4 | **Convening the meeting in which a plan is settled** | Inside a built agent, subagents each hold a position (the purpose of the experiment, the budget, what the instrument or the engine can deliver) with a safety guard among them; a mediator proposes a range all accept, and the plan goes to an operating subagent and then to an analysing one. | Designed (`plan.md` 14-32 to 14-36), not built: `tasks/011` to `014` are open, and each is done only when it runs on fixtures of two unrelated kinds, one of them not rheology (14-37). A built bundle today carries two subagents, `operator` and `analyst`. |
| 5 | **Building the skills an agent works with** | A capability is a skill written as source code, with the source it rests on and worked cases. The model chooses which skills apply and code runs them: every skill whose `applies_to` matches a request is on the sheet, as used or as not applied with a reason, and a silent omission fails the gate (`plan.md` 14-30, kept by the person on 2026-11-11). Kinds: parameter bounds and correlations, hardware connection, boot sequence, situation awareness, operable range, control, calibration, data analysis. | Runs on fixtures: 21 skills under `meta_agent/skills/`, each passing its worked cases; a parameter sheet whose every bound is recomputed by the gate; a fixture rheometer bundle that carries its skills and subagents (`tasks/010`, `007`). 17 of the 21 skills apply only to the rheometer or its engines, all six hardware skills among them; they are the testbed's examples, and nothing more is written for the rheometer until its testbed starts (14-37). No skill has been run against a device. |

**Status.** Onboarding and the Agent Designer run on fixtures (M1), and so do experience memory (M4, `tasks/006`) and parameter bounds from skills (M3, `tasks/007`). `contracts/` holds the schemas, the vocabularies, the seat table and the validator with seventeen card checks and ten bundle checks, an accepted example set, and 123 rejected fixtures, each of which the gate must refuse. Read off a run at `8b8faf9`: 331 cards and two bundles judged, 0 failed; 123 of 123 fixtures rejected; 57 and 162 tests pass. Open: the working index for materials (`005`), the meta-harness (`008`), and what a built agent does with its skills: rough ranges and the model's choice (`011`), the subagents' negotiation (`012`), the run from plan to report (`013`), the instrument's operable range (`014`). Recommended and not built: a bundle serves its tools as one MCP server whose every call passes the gate, and an adapter that needs a gate calls it at its own entry, since today a direct import reaches an adapter without the gate (`plan.md` 14-24; no tool built so far writes to a device). Nothing here has touched an instrument. The first testbed is a rheometer and a rheology simulation engine, as a pair; it tests the machinery and does not shape it (the person, 2026-11-11, `plan.md` 10): nothing is developed now for either, and a general mechanism (a skill kind, a card, a check, a subagent drawing, a runner) counts as done only when it runs on fixtures of two unrelated kinds, one of them not rheology.

## Read first

- [`plan.md`](plan.md) — the design record (English). Sections 3 (principles), 5 (specifications), 6 (cards), 8 (checks), 12 (milestones), 14 (open questions).
- [`docs/origin/PLAN.ko.md`](docs/origin/PLAN.ko.md) — the Korean plan v0.3.2 the record was written from, frozen on 2026-10-29.
- [`CLAUDE.md`](CLAUDE.md) — the rules that bind a session in this repository.
- [`meta_agent/CLAUDE.md`](meta_agent/CLAUDE.md) — what the agent does and does not do.

## The gate

```
python contracts/validate.py                 # judge the repository: 0 failed is the only pass
python contracts/validate.py --expect-fail   # every fixture in contracts/examples/rejected/ must be refused
python contracts/validate.py --staged        # what the pre-commit hook runs
python contracts/validate.py --bundle PATH   # the B checks on one built bundle
```

Install the hook once per clone with `git config core.hooksPath contracts/hooks`. Set `PYTHONUTF8=1` on Windows. The validator needs `jsonschema`; without it, it re-executes itself through `uv` when `uv` is present.

## The gate on GitHub

`.github/workflows/gate.yml` runs, on every push and pull request, what a seat runs on its computer: `python contracts/validate.py --commit-range <enforced_from>..HEAD` (the tree and the history), `--expect-fail`, and the two test suites. It holds no secret and can write nothing.

## Seats

A session commits as a seat, never as itself: committer `seat:<name>` <`<name>@seat.invalid`>, author the person. Three roles exist (`plan.md` 9, [`contracts/seats.json`](contracts/seats.json)). A session seats itself under the person's standing rule, or the person assigns a seat; check 6 fails a seat that is wider than its role and a commit that crosses its paths. Several seats work in the one working copy at the same time.

| Role | What it does | Paths it may write |
|---|---|---|
| `design` | The design record, the contracts and the gate, the person's decisions, the agent's instructions and settings, and the task queue. It opens and closes tasks; it writes no cards, builds or knowledge. | root files, `contracts/`, `docs/`, `.claude/`, `meta_agent/CLAUDE.md`, `meta_agent/.claude/`, and the `meta_agent/` skeleton (`tasks/`, `templates/`, `eval/`, the empty logs, the inbox's README, LINKS.md and drop/.gitkeep) |
| `meta` | The agent at work: onboarding, intake, requests, knowledge, cases, builds, and its own `src/` and `tests/`. | `meta_agent/`, except `meta_agent/CLAUDE.md` and `meta_agent/.claude/` |
| `harness` (from M5) | The meta-harness: incidents, proposals, proofs with fixtures and replay, the ledger and the library. | `meta_agent/harness/` |

Names are `<role>-<machine>-<YYYYMMDD>-<n>`; a new computer gets its tag from the person before its first seat. A session that sits down in a clone already set up runs

```
python bootstrap.py seat <role> --write                 # its seat's name and entry
python contracts/tools/seat_commit.py --seat <name> -m "contracts/seats: <name> seats itself" contracts/seats.json
python contracts/tools/notes.py list --role <role>      # what other seats asked of its role
python contracts/tools/tasks.py next --role <role>      # the task it may take; it claims it before it starts
```

and commits with `seat_commit.py`, which takes only the paths it is given and sets the committer for that one commit. The pre-commit gate judges the tree the commit would make, so what another seat has unfinished in the folder does not stop it.

## External tools

```
python bootstrap.py check                     # read-only: what this computer has and what it lacks
python bootstrap.py install node rea --yes    # Node.js and REA at the versions tools.lock.json pins
python bootstrap.py install harness2 --yes    # Linux or WSL only: harness2 at its pinned commit
```

REA, harness2 and Node.js are not in this repository. [`tools.lock.json`](tools.lock.json) pins them, with the SHA-256 of each Node.js archive; [`bootstrap.py`](bootstrap.py) fetches them from their own sources into the user's tools home (`%LOCALAPPDATA%\Programs` on Windows, `~/.local/opt` elsewhere) and touches no PATH, registry or agent configuration. Without `--yes` it only prints its plan. [`.mcp.json`](.mcp.json) starts REA as an MCP server through `python bootstrap.py run rea mcp`.

## Dropping materials

A link on one line is enough. Add a row to [`meta_agent/inbox/materials/LINKS.md`](meta_agent/inbox/materials/LINKS.md) or put a file into `meta_agent/inbox/materials/drop/`. The Meta-Agent classifies it, records the source and asks you to confirm (intake runs from M2). See [`meta_agent/inbox/materials/README.md`](meta_agent/inbox/materials/README.md).

## Layout

```
plan.md  CLAUDE.md  README.md  LICENSE  bootstrap.py  tools.lock.json  .github/workflows/gate.yml
contracts/   schemas/  registry/  units.json  grades.json  claim_kinds.json  case_classes.json  skill_kinds.json
             records.json  seats.json  validate.py  tools/  tests/  examples/  examples/rejected/  hooks/
meta_agent/  CLAUDE.md  README.md  tasks/  src/  tests/  skills/  cases/  profiles/  requests/  builds/
             templates/  inbox/materials/  inbox/seats/  failures.jsonl
docs/        ideas/  origin/  reference/
```

Modeled on [soft-matter-agents](https://github.com/kyu-softmatter/soft-matter-agents): cards, seats, a deterministic gate with rejected fixtures, a task queue and a failure log. One agent instead of four; a bridge connects it to others later if needed. On 2026-11-11 the person chose that in both repositories the model chooses which skills apply (`docs/ideas/20261111.md`); what changes in soft-matter-agents is decided there.

## License

MIT. Third-party code is called, not vendored: REA (MIT) as an analysis tool over MCP, RheoTool and OpenFOAM (GPL-3.0) out of process; harness2 (Apache-2.0) is a reference for structure only. See `plan.md` 14-10.
