---
name: choose-session-level
description: Work out which model and how much effort each session or subagent should run on, from the kind of work it does and what a mistake in it would cost. Use before a session or a subagent is opened, when the open-sessions skill reaches its step on model and effort, when a bundle's subagents are given their models, when a session failed at a level or was plainly more than its work needed, and when the person asks what each session runs on.
---

# Choose the model and the effort of each session

A level is a model and an effort. It is chosen per session by the kind of work, never one level for all. More is not safer when code already checks the output, and less is not cheaper when the work has to be done again.

## Do this

1. **List what will be opened** and say in one line what each does: this session too, since it also runs on a level.
2. **Give each the level of its kind of work,** from the table below. Go by the hardest thing the session must do, not by its role's name.
3. **Move it one step where a reason below applies,** and write the reason.
4. **Set it.** A fresh session takes its model and effort when it is started. A fork starts on the opener's and is changed right after it starts. A subagent takes its model from its own file. A level above your own needs the person.
5. **Tell the person** every session's model and effort in the list of what was opened, and put them in the session's brief so that its report can name them.
6. **Afterwards, record whether the level was right** (the `end-session` skill): a session that failed or had to be redone at its level, and one that was plainly more than its work needed. Compare only like work with like.

## The levels

| level | the kind of work | model | effort |
|---|---|---|---|
| judgement | decides what others build on, or acts where a mistake is costly or cannot be undone: a schema, a check, a contract, a specification, a safety axis, the purpose, why two results disagree, the choice of a method, an instrument operated live | the most capable the opener may give | `xhigh` |
| build | builds to something written that code will judge: source with tests, a library skill with worked cases, a bundle from a template, a simulation with its convergence checks, an analysis with a control | the most capable, or one below it | `high` |
| read | reads and records: materials and literature, a discovery report, a comparison table, lessons, a rendered view, an index | a middle model | `medium` |
| run | runs a command and reports what it printed, moves or formats files | the cheapest | `low` |

Models, by name on the day this was written: `claude-fable-5-2` and `claude-opus-5-5` are the capable ones, `claude-sonnet-5-5` the middle one, `claude-haiku-5-5` the cheapest. Take the newest of the same kind when these are replaced. Efforts, in order: `low`, `medium`, `high`, `xhigh`, `max`.

## One step up

- Nothing but a person will check what the session produces.
- It touches a device, a safety row or anything `held`, or it writes what the person will decide from.
- Its brief cannot say what done looks like.
- The same work already failed one level down: say so, and where.
- `max` is for the hardest judgement only, and only on the person's word.

## One step down

- A deterministic check judges every output (the gate, worked cases, tests), and a failure costs only another run.
- The work is a repetition of something already done once at the higher level.

Never step down a session that operates an instrument, writes a safety axis or records the person's decisions.

## The usual sessions

In this repository:

- a `design` seat, and a `harness` seat: judgement.
- a `meta` seat: by the part of the pipeline it runs. `understand-purpose` and `specify-and-build` are judgement; `analyse-hardware`, `analyse-lab-environment`, `analyse-physical-system`, `estimate-parameter-ranges`, `design-tool-interface`, `build-library-skill` and `validate-and-record` are build; `research-materials` is read. `classify-knowledge` runs inside whichever of these is at work and takes its level.
- a hub that only opens, relays and checks: build.

In a built agent:

- the subagent that holds the purpose, the one that holds safety, and the one that finds a range all accept: judgement.
- the one subagent or session that may change a device, and any session a person speaks to at the instrument: judgement.
- simulation and analysis of data: build. Comparison of experiment with simulation: judgement, since it decides what is run next.
- literature, and the record of what went wrong: read.

## What this is, and whose

These levels are a recommendation. They are not measured, and the cost is the person's: when the person names a model or an effort for a session, theirs holds and is written down as theirs. A level decides nothing else: it grants no permission, releases nothing `held`, and changes no rule.
