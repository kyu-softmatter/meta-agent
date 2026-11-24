---
name: run-skill
description: Find what does the work a task needs, a library skill or a callable tool, run it through its runner and report what the runner printed. Use whenever a task needs a quantity computed or estimated, a device found, read or changed, a tool called, or data analysed, before any value goes into a report or a record, and when nothing here gives what the task needs.
---

# Run a library skill, or a tool no skill calls

Whatever this agent computes, reads from a device or does to a device is a library skill under `skills/`, and a library skill is reached one way, through the runner of skills. Where no library skill stands in front of a callable tool, the tool is called through the runner of tools, as the section on a tool no skill calls says. Every command is run from this agent's directory. The rules are in `CLAUDE.md`; this is the procedure.

1. **Find the skill.** `library/index.md`, beside this file, lists every library skill this agent has and names a page for each: what the skill gives, what it needs and in which units, the tools it calls, whether it changes a device. The sentence for the skill in `CLAUDE.md` says when it applies. A page is reference: you open it when you look for a skill, and nothing loads it for you.
2. **Write the inputs.** One JSON object, one key per input the page names, in the page's units. An input is read off a run, a source or a card, and you say which. You never type a value because it seems right.
3. **Run it.**
   ```
   python src/run_skill.py <id@vN> < inputs.json
   ```
   The runner compares the inputs and the outputs with the skill's manifest, sends every device call through `src/run_tool.py`, where the gate is asked each time, and prints what it ran. It writes no file unless you add `--record <file>`: then it also writes what it printed to that file, which must not exist yet. Name a file in the folder named runs.
4. **Report what it printed,** unchanged: the outputs, the tool calls and their verdicts. A refusal is reported as a refusal and is not tried another way. A skill that is held is refused until a person releases it. A failure is one line in `failures.jsonl`, with the keys `CLAUDE.md` names.

## What the status a runner ends with means

- `python src/run_skill.py`: `0` the skill ran; `3` the runner refused it before any of its code ran, and the record's `why` says what it refused; `4` the skill ran and failed; `2` this agent has no such skill; `1` the command was not understood, or the file `--record` names exists already.
- `python src/run_tool.py`: `0` the tool answered or returned an error contract, and the error is in the output; `2` this agent has no such tool; `1` the command did not name one tool.

A status other than `0` from the runner of skills is reported with the record it printed, and is not a reason to try the skill another way.

## When the task needs a tool and no library skill calls it

`library/index.md` says so: it lists no skill, or none whose page names the tool. Then call the tool itself, through the runner of tools, with one JSON object for the inputs its contract (`tools/<name>/tool.json`) names:

```
python src/run_tool.py <tool> [--out runs/<file>.json] < input.json
```

The runner asks the gate, checks the input against the contract and prints the output or an error contract. Report what it printed, unchanged. An error contract is reported as it is, and a refusal by the gate is a refusal. The runner of tools writes a file only when it is told to: when its output is to be kept, name a new file ending in `.json` in the folder named runs with `--out`, and the runner writes it whole once the call has returned. Do not send the output to a file with the shell, which can leave an empty file behind.

## When a task has you make a replay item's call

Make the call through the runner, as above, with the item's `call.input` as the input. Do not compare what came back with the item's `expected` by eye: `python src/replay.py` makes the same call and makes that comparison, and prints one line per item. Report what your call printed beside the line the script printed for that item.

## When no skill gives what the task needs

Do not compute it yourself and do not write a script for it. Say what is missing: the quantity or the procedure, what it would be worked out from, and why the task needs it. Write that as one line in `failures.jsonl` and report it. A further library skill is built by the Meta-Agent, with its source and its worked cases, and comes with a new build that a person brings here.

## When a skill needs an input that nothing here gives

Supply no value for it, and do not let another value stand in for it: a value the device reports about itself is not the value a specification states. Run the skill without the input when you want the runner's own refusal on record. Say what the task needed, where you looked, and what would settle it: a source, a measurement, the person. Write that as one line in `failures.jsonl` and report it, as for a missing skill. Where the build gave the input a row of `envelope/parameters.json` with no value, its note naming the skill and the input, the value is the person's: their words in a task, or an assignment's quote of them, and never one you choose.

## What a session may change

- `failures.jsonl`, by adding lines at its end.
- The folder named runs in this directory: the inputs it wrote for a runner, the records the runner of skills wrote there with `--record`, and the output of a runner that it kept. The folder is not built with the agent; the session makes it when it first writes there.

## What a session never changes

- `envelope/safety.json`. A person writes safety values, at the destination.
- `CLAUDE.md` and anything under `.claude/`, this skill and its pages included.
- Anything under `skills/`, `tools/`, `src/`, `validation/` or `replay/`, and `CAPABILITIES.json`, `envelope/snapshot.json` and `envelope/parameters.json`. They are what this agent was built with; a change to any of them is a new build, never an edit in place, and an expected verdict is never edited to make a run pass.
- A value a skill would give, a threshold or a limit. None is typed, into a report, a record or a skill's result.
