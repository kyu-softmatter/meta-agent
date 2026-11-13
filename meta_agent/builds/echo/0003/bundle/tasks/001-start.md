# 001 — Start

**Status:** open. **Opened:** by the Meta-Agent at build time.

**Goal:** prove this bundle works where it landed, without the Meta-Agent.

**Do:**
- `python src/gate.py --self-check`
- `python src/replay.py`
- `python src/validate_tasks.py`

**Done when:** all three have printed their last lines and you have reported them verbatim. The first two end with an OK line. The third ends with a verdict line, and it ends with a failure status whenever the overall verdict is not `pass`: with a scientific task that prints `undecided` that is expected and is not a failure of this bundle. Such a task waits for a person's tolerance; do not choose one.

**Must not:** edit `envelope/safety.json`, `CLAUDE.md` or `.claude/`; invent a number; mark `not_run` as done.
