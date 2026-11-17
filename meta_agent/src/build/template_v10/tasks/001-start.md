# 001 — Start

**Status:** open. **Opened:** by the Meta-Agent at build time.

**Goal:** prove this bundle works where it landed, without the Meta-Agent.

**Do:**
- `python src/gate.py --self-check`
- `python src/replay.py`
- `python src/validate_tasks.py`

**Done when:** all three have printed their last lines and you have reported them verbatim. The first ends with the line `gate: self-check ok`, and the second with a line that starts `replay:` and ends `OK`; each ends with a success status then. The third ends with a verdict line, and it ends with a failure status whenever the overall verdict is not `pass`. With a scientific task that prints `undecided` or `not_run` that is expected and is not a failure of this bundle. An `undecided` task waits for a person's tolerance; do not choose one. A `not_run` task waits for what its own note names. Neither is a pass.

**Must not:** edit `envelope/safety.json`, `CLAUDE.md` or `.claude/`; invent a number; mark `not_run` as done.
