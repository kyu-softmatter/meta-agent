# Hub

A hub agent built by the Meta-Agent beside the agents it coordinates. The directory is the hub: `CLAUDE.md` is its role and procedure, `.claude/settings.json` its guardrails, `.claude/skills/` the procedures a session loads (`run-hub`, the work; `choose-session-level`), `members.json` the agents it coordinates, each in a folder of its own beside this one, `question/` the person's questions and their agreement to each list of assignments, `assignments/` what each member was asked, `inbox/` the results the bridge carried back, `sessions/` the members' sessions this hub opened and the drafts of its own session, and `src/` its one script, `hub.py`, and the bridge it carries through, `bridge.py`.

The hub has no tool, no gate and no library skill: it runs no engine and no instrument and computes no value. Each member stands alone without it.

Place each member's folder where `members.json` says, relative to this one, as the build named it. To see what the hub finds there:

```
python src/hub.py members
python src/hub.py status
```
