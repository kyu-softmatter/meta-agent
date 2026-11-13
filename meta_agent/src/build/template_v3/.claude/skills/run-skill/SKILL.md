---
name: run-skill
description: Run one of this agent's library skills through its runner and report what the runner printed. Use whenever a task needs a quantity computed or estimated, a device found, read or changed, or data analysed, before any value goes into a report or a record, and when no skill here gives what the task needs.
---

# Run a library skill

Whatever this agent computes, reads from a device or does to a device is a library skill under `skills/`, and a library skill is reached one way, through the runner. Every command is run from this agent's directory. The rules are in `CLAUDE.md`; this is the procedure.

1. **Find the skill.** `library/index.md`, beside this file, lists every library skill this agent has and names a page for each: what the skill gives, what it needs and in which units, the tools it calls, whether it changes a device. The sentence for the skill in `CLAUDE.md` says when it applies. A page is reference: you open it when you look for a skill, and nothing loads it for you.
2. **Write the inputs.** One JSON object, one key per input the page names, in the page's units. An input is read off a run, a source or a card, and you say which. You never type a value because it seems right.
3. **Run it.**
   ```
   python src/run_skill.py <id@vN> < inputs.json
   ```
   The runner compares the inputs and the outputs with the skill's manifest, sends every device call through `src/run_tool.py`, where the gate is asked each time, and prints what it ran.
4. **Report what it printed,** unchanged: the outputs, the tool calls and their verdicts. A refusal is reported as a refusal and is not tried another way. A skill that is held is refused until a person releases it. A failure is one line in `failures.jsonl`.

## When no skill gives what the task needs

Do not compute it yourself and do not write a script for it. Say what is missing: the quantity or the procedure, what it would be worked out from, and why the task needs it. Write that as one line in `failures.jsonl` and report it. A further library skill is built by the Meta-Agent, with its source and its worked cases, and comes with a new build that a person brings here.

## What a session may change

- `failures.jsonl`, by adding lines at its end.
- The folder named runs in this directory: the inputs it wrote for the runner and the records the runner wrote.

## What a session never changes

- `envelope/safety.json`. A person writes safety values, at the destination.
- `CLAUDE.md` and anything under `.claude/`, this skill and its pages included.
- Anything under `skills/`, `tools/`, `src/`, `validation/` or `replay/`, and `CAPABILITIES.json`, `envelope/snapshot.json` and `envelope/parameters.json`. They are what this agent was built with; a change to any of them is a new build, never an edit in place, and an expected verdict is never edited to make a run pass.
- A value a skill would give, a threshold or a limit. None is typed, into a report, a record or a skill's result.
