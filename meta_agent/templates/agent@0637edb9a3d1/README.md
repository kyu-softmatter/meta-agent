# Bundle

A scientific agent built by the Meta-Agent. The directory is the agent: `CLAUDE.md` is its role and procedure, `.claude/settings.json` its guardrails, `tools/` its callable tools with their contracts, `envelope/` its safety values (null until a person sets them), knowledge snapshot and parameters, `skills/` the source code it takes when a task needs it, `.claude/skills/` the procedures a session loads when it reaches the work (`run-skill`, the one that sends it to the runner of those skills, with a page per skill; `classify-knowledge`; `choose-session-level`), `.claude/agents/` its subagents, `validation/` and `replay/` its gates, `src/` the deterministic scripts that run them.

Nothing in here needs the Meta-Agent. To check the bundle where it landed:

```
python src/gate.py --self-check
python src/replay.py
python src/validate_tasks.py
```
