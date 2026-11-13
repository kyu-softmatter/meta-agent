# 001 — Start

**Status:** open. **Opened:** by the Meta-Agent at build time.

**Goal:** prove this bundle works where it landed, without the Meta-Agent.

**Do:**
- `python src/gate.py --self-check`
- `python src/replay.py`
- `python src/validate_tasks.py`

**Done when:** all three print their OK or verdict lines and you have reported them verbatim. A scientific task that prints `undecided` waits for a person's tolerance; do not choose one.

**Must not:** edit `envelope/safety.json`, `CLAUDE.md` or `.claude/`; invent a number; mark `not_run` as done.
