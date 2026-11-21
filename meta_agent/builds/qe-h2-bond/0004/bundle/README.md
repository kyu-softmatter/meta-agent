# Bundle

A scientific agent built by the Meta-Agent. The directory is the agent: `CLAUDE.md` is its role and procedure, `.claude/settings.json` its guardrails, `tools/` its callable tools with their contracts, `envelope/` its safety values (null until a person sets them), the lab's execution permission where the build copied one, its knowledge snapshot and parameters, `skills/` the source code it takes when a task needs it, `.claude/skills/` the procedures a session loads when it reaches the work (`run-skill`, the one that sends it to the runner of those skills, with a page per skill; `classify-knowledge`; `choose-session-level`), `.claude/agents/` its subagents where it has any (a bundle with none carries no such folder), `validation/` and `replay/` its gates, `src/` the deterministic scripts that run them, and `runs/`, made at the first run, what runs and installs leave. An agent that hands values to another agent, or takes values from one, also has `outbox/` (the hand-over cards it wrote), `inbox/` (what the bridge a person starts delivered, written by the bridge alone) and `received/` (one receipt per value it took), with `envelope/handovers.json` saying what it gives and takes and `envelope/units.json` the unit registry it converts by; `src/handover.py` writes and reads them. Any agent of this template may be a member of a hub agent beside it: an assignment the hub sent arrives in `inbox/<thread>/` like a hand-over, and the agent answers it with a result card in `outbox/`, written by `src/handover.py result` from `envelope/results.json`, what the build declared it may report from its tools' results.

Nothing in here needs the Meta-Agent. To check the bundle where it landed:

```
python src/gate.py --self-check
python src/replay.py
python src/validate_tasks.py
```
