# 002 — The echo agent on mock

**Status:** open (M1), after 001. **Opened:** 2026-10-29 by the design seat on the plan's instruction (plan.md 15-8).

**Seat:** the `meta-…` seat the person assigns.

**Goal:** run S1–S7 end to end on a tool that cannot hurt anything — an `echo` tool whose only capability is to return what it was given — and hand over a bundle that passes both gates without the Meta-Agent. This is the Designer's skeleton (plan.md 12, M1): `agent_goal` → `tool_profile` from documentation only → `agent_spec` with six axes → template v1 → bundle → interface gate B1–B9 → `validation_report`.

**Inputs:**
- `../../plan.md` 5.1 (S1–S7, the bundle table, the harness surface, the edit contract), 6.4 (error contract), 8 (B1–B10).
- `../../contracts/examples/requests/req-fixture-001/` and `../../contracts/examples/bundle/` — the shape of the cards and of a tool contract.
- The echo tool's "documentation": one page you write under `tests/fixtures/echo/README.md` stating its one command, its input and output, and one error it returns (`invalid_input` on an empty message).

**Done when (read off a run):**
- `templates/agent@<hash>/` exists with the harness surface, `tools/`, `validation/`, `envelope/` (safety `null`) and `replay/`.
- `builds/echo/0001/` holds the bundle, the `build` card with `bundle_sha256` and `diff_from_template`, and a `validation_report` whose interface section is all `pass` and whose scientific section has exactly one trivial task with a person-chosen tolerance and `pass`.
- The bundle handles one `replay/` item in a fresh session with the Meta-Agent absent, and the replay's expected verdict matches.
- The B checks exist in `../../contracts/validate.py --bundle <path>` for B1–B9 with one rejected fixture each (proposed to the design seat, landed by it; the fixtures are watched failing first).
- `python ../../contracts/validate.py` prints `0 failed`.

**Must not:** put a number in `agent_goal`; write a safety value; write outside `meta_agent/`; add an engine, a GUI or a dependency the echo tool does not need; land anything in `../../contracts/` yourself.

**Report:** ten lines or fewer — what ran, the gate verdicts, the validator's verdict line, which B checks are proposed and where their fixtures are.
