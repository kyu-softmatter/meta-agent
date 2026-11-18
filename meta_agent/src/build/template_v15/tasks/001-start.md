# 001 — Start

**Status:** open. **Opened:** by the Meta-Agent at build time.

**Goal:** prove this bundle works where it landed, without the Meta-Agent.

**Do:**
- `python src/gate.py --self-check`
- `python src/replay.py`
- `python src/validate_tasks.py`
- Where a scientific task printed `not_run` because the environment of an engine is not made yet, and a tool here is the one install (its gate line in `CLAUDE.md` says so): that install is this agent's own next step. Call it through the runner as `CLAUDE.md` says, then run `python src/validate_tasks.py` again. Before the install, an interface task whose call starts the engine fails too, with the error that names the missing environment (category `unavailable`): that is the same want of an environment, not a fault of the tool, and the verdict after the install is the one that says whether the interface works. Where the install returns an error, report it as it is. Where the error names an installer that is not on the computer, putting it there is the person's step.

**Done when:** all three have printed their last lines and you have reported them verbatim, together with the install's output and the second verdict line where the bundle made its environment. The first ends with the line `gate: self-check ok`, and the second with a line that starts `replay:` and ends `OK`; each ends with a success status then. The third ends with a verdict line, and it ends with a failure status whenever the overall verdict is not `pass`. With a scientific task that prints `undecided` or `not_run` that is expected and is not a failure of this bundle. An `undecided` task waits for a person's tolerance; do not choose one. A `not_run` task waits for what its own note names. Neither is a pass.

**Must not:** edit `envelope/safety.json`, `CLAUDE.md` or `.claude/`; invent a number; mark `not_run` as done.
