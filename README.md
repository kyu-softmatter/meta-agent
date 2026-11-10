# meta-agent

One agent that builds scientific agents and keeps them improving: it reads a lab's environment first (onboarding), designs and validates an agent for a new instrument or simulation engine (Agent Designer), and improves built agents from the knowledge and experience they gather (meta-harness). Everything it hands over is a card on disk, and a deterministic validator judges every card.

**Status: M1 — onboarding and the Agent Designer run on fixtures.** Schemas, vocabularies, the registry seeds, the seat registry, the validator with ten card checks (18 judges wiki pages, `meta_agent/tasks/003`) and nine bundle checks (B1–B9), an accepted example set with a wiki example and its map, and fifty-seven rejected fixtures are in `contracts/`. `meta_agent/src/onboarding/` reads a lab and asks only what is unknown; `meta_agent/src/designer.py` takes a request from intake to a validated bundle under `meta_agent/builds/` (the echo agent is the first, `meta_agent/tasks/002`). Hand-over, safety values and tolerances stay the person's (`plan.md` 12).

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

A session commits as a seat, never as itself: committer `seat:<name>` <`<name>@seat.invalid`>, author the person. Three roles exist (`plan.md` 9, [`contracts/seats.json`](contracts/seats.json)); the person assigns one per session, and check 6 fails a commit that crosses its paths.

| Role | What it does | Paths it may write |
|---|---|---|
| `design` | The design record, the contracts and the gate, the person's decisions, the agent's instructions and settings, and the task queue. It opens and closes tasks; it writes no cards, builds or knowledge. | root files, `contracts/`, `docs/`, `.claude/`, `meta_agent/CLAUDE.md`, `meta_agent/.claude/`, and the `meta_agent/` skeleton (`tasks/`, `templates/`, `eval/`, the empty logs, the inbox's README, LINKS.md and drop/.gitkeep) |
| `meta` | The agent at work: onboarding, intake, requests, knowledge, cases, builds, and its own `src/` and `tests/`. | `meta_agent/`, except `meta_agent/CLAUDE.md` and `meta_agent/.claude/` |
| `harness` (from M5) | The meta-harness: incidents, proposals, proofs with fixtures and replay, the ledger and the library. | `meta_agent/harness/` |

Names are `<role>-<machine>-<YYYYMMDD>-<n>`; `office` is the office computer and `macbook` the MacBook Air, and a new computer gets its tag from the person before its first seat. A seat is registered in `contracts/seats.json` before its first commit (an unregistered committer is reported, not refused, and gets no path check). Adopt one in a clone with

```
git config committer.name "seat:<role>-<machine>-<YYYYMMDD>-<n>"
git config committer.email "<role>-<machine>-<YYYYMMDD>-<n>@seat.invalid"
```

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
plan.md  CLAUDE.md  README.md  LICENSE  pyproject.toml  .claude/settings.json
contracts/   schemas/  registry/  units.json  grades.json  claim_kinds.json  case_classes.json
             records.json  seats.json  validate.py  examples/  examples/rejected/  hooks/
meta_agent/  CLAUDE.md  README.md  .claude/  tasks/  failures.jsonl  envelope/  inbox/materials/
docs/        ideas/  origin/  reference/
```

Modeled on [soft-matter-agents](https://github.com/kyu-softmatter/soft-matter-agents): cards, seats, a deterministic gate with rejected fixtures, a task queue and a failure log. One agent instead of four; a bridge connects it to others later if needed.

## License

MIT. Third-party code is called, not vendored: REA (MIT) as an analysis tool over MCP, RheoTool and OpenFOAM (GPL-3.0) out of process; harness2 (Apache-2.0) is a reference for structure only. See `plan.md` 14-10.
