# echo (fixture) — a scientific agent

A minimal bundle cut from the echo build for the rejected fixtures of the B checks.

## Tools

### `echo`

Returns the given text and its character count. Call it through `python src/run_tool.py echo`.

## Procedure

- `python src/replay.py`, then `python src/validate_tasks.py`; report what they printed.
- Every number you report is read off a run. You invent no number and set no threshold.

## What this agent does not do

- Write outside this directory, or into `envelope/safety.json`, `CLAUDE.md` or `.claude/`.

## Skills

This agent has no skills.
