---
name: choose-session-level
description: Work out which model and how much effort a subagent or a further session of this agent should run on, from the kind of work it does and what a mistake in it would cost. Use before a subagent or a session is started, when one failed at its level or was plainly more than its work needed, and when the person asks what each runs on.
---

# Choose the model and the effort of each session

A level is a model and an effort. It is chosen per session or subagent by the kind of work, never one level for all. More is not safer when code already checks the output, and less is not cheaper when the work has to be done again.

## Do this

1. **List what will be started** and say in one line what each does: this session too, since it also runs on a level.
2. **Give each the level of its kind of work,** from the table below. Go by the hardest thing it must do, not by its name.
3. **Move it one step where a reason below applies,** and write the reason.
4. **Set it.** A session takes its model and effort when it is started. A subagent takes its model from its own file, and those files are under `.claude/`, which a session does not edit: where a subagent's file names no model, give the level for the one call, or ask the person. A level above your own needs the person.
5. **Tell the person** the model and the effort of everything you started.
6. **Afterwards, say whether the level was right.** A session or a subagent that failed or had to be redone at its level is one line in `failures.jsonl`; one that was plainly more than its work needed is said in the report. Compare only like work with like.

## The levels

| level | the kind of work | model | effort |
|---|---|---|---|
| judgement | decides what others build on, or acts where a mistake is costly or cannot be undone: the purpose, a safety row, whether a range is accepted, why two results disagree, the choice of a method, an instrument operated live | the most capable the opener may give | `xhigh` |
| build | works to something written that code will judge: a library skill run through the runner, a simulation with its convergence checks, an analysis with a control | the most capable, or one below it | `high` |
| read | reads and records: literature, a comparison table, the record of what went wrong | a middle model | `medium` |
| run | runs a command and reports what it printed, moves or formats files | the cheapest | `low` |

Models, by name on the day this was written: `claude-fable-5-2` and `claude-opus-5-5` are the capable ones, `claude-sonnet-5-5` the middle one, `claude-haiku-5-5` the cheapest. Take the newest of the same kind when these are replaced. Efforts, in order: `low`, `medium`, `high`, `xhigh`, `max`.

## One step up

- Nothing but a person will check what it produces.
- It touches a device, a safety row or anything `held`, or it writes what the person will decide from.
- What it is asked cannot say what done looks like.
- The same work already failed one level down: say so, and where.
- `max` is for the hardest judgement only, and only on the person's word.

## One step down

- A deterministic check judges every output (the gate, a skill's worked cases, the replay and validation tasks), and a failure costs only another run.
- The work is a repetition of something already done once at the higher level.

Never step down a session or a subagent that operates an instrument, works on a safety row or records the person's decisions.

## The usual ones in this agent

- the subagent that holds the purpose, the one that holds safety, and the one that finds a range all accept: judgement.
- the one subagent or session that may change a device, and any session a person speaks to at the instrument: judgement.
- simulation and analysis of data: build. Comparison of experiment with simulation: judgement, since it decides what is run next.
- literature, and the record of what went wrong: read.

## What this is, and whose

These levels are a recommendation. They are not measured, and the cost is the person's: when the person names a model or an effort, theirs holds and is reported as theirs. A level decides nothing else: it grants no permission, releases nothing `held`, and changes no rule.
