# meta-agent

One agent that builds scientific agents and keeps them working. It scans and distills the knowledge an agent needs, analyses the parameters of a simulation engine or an instrument, improves its own structure through a meta-harness, remembers what failed and what worked, and hands everything over as cards on disk.

**Status: planning. Nothing is built yet.**

- `PLAN.ko.md` is the plan, in Korean, which is the person's working language for planning. Its change log at the top names the current version. Once the plan is approved it is frozen under `docs/origin/` and an English `plan.md` becomes the record.
- Code, schemas, cards, instructions and memos are English.

Modeled on [soft-matter-agents](https://github.com/kyu-softmatter/soft-matter-agents): contracts on disk, seats as commit identities, deterministic checks with rejected fixtures. This repository holds one agent; a bridge connects it to others if that is ever needed.

License: MIT.
