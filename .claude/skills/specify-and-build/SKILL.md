---
name: specify-and-build
description: Write an agent's specification on its six axes and assemble its bundle from a versioned template. Use when a request has its goal, its tool profile and its parameter sheet and the agent is to be specified or built, and when a specification changes and the bundle must be rebuilt.
---

# Specify the agent and build its bundle

## Before you start

The policy fields of the lab's profile must be `confirmed` by the person. If one is not, the build does not start: what depends on it is `held`.

## Specify, on six axes

Each axis is its own card and may be written in parallel with the others.

- **Boundary:** directories, the paths it may write, read and never touch, its seat, its tier.
- **Interface:** the cards it reads and writes, and its callable tools with their contracts (`design-tool-interface`).
- **Knowledge:** the entries copied into its envelope with their version pinned, and the gaps that remain.
- **Parameters:** the rows of the sheet this agent handles (`estimate-parameter-ranges`). They reach the bundle's parameter file through the intake's `parameter_rows`; an intake without them builds a bundle with none, and a contract input that names a row then fails the bundle's gate.
- **Safety:** the safety rows with empty values, the place of the deterministic rule, and what only a person does.
- **Validation:** interface tasks and scientific tasks with their reference results, and when it is complete or refused.

The synthesis records conflicts between axes. The direction of concession comes from the goal's priorities, never from you.

**Fail closed.** A capability with an unresolved scope, permission, side effect or validation goes to `held` and stays out of the bundle.

## Build

```
python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat>
```

It runs intake through validation and writes the bundle under `meta_agent/builds/<agent>/<build_id>/` with its `build` card.

**Rehearse first.** A build is a record and a card is never edited, so a run that the gate then fails leaves files to clear away. Run the Designer once with `--root <a scratch copy of meta_agent outside the repository>`, run `python contracts/validate.py` on that copy and `python contracts/validate.py --bundle` on its bundle, correct the intake by its next revision until both pass, and only then run it in the repository.

- The bundle comes from a versioned template; the `build` card carries the difference from the template and the hash.
- Safety values are `null`. Only the person writes them, at the destination.
- Only `observed` and `derived` claims become capabilities.
- The bundle carries the library skills it needs, run through its own runner. From template version v3 on it also carries its session skills: one that sends the bundle's session to that runner, with a page per library skill, and beside it the ones for choosing a session's level and for classifying a piece of knowledge.
- Check it alone: `python contracts/validate.py --bundle <bundle folder>`.

## Build an agent again

An agent that exists is built again from its specification as it stands, under a new build id, and the build before it is never edited:

```
python -m meta_agent.src.designer --rebuild meta_agent/requests/<rid> --seat <seat>
```

Do not run the first-build command on a request that already has its cards: it would write them again.

When the request itself has changed (a tool contract corrected, a skill or a subagent added), the change is the next revision of its intake, and the specification is written again from it before the build:

```
python -m meta_agent.src.designer --respecify meta_agent/requests/<rid> --seat <seat>
```

It writes the next revision of each card that differs and leaves the others. Then build again as above. A revision is a new file beside the one before it; no card is edited.

## Stop at the bundle

You write nowhere outside `meta_agent/builds/`. The person moves the bundle to its destination and records where it landed. For an instrument, the bundle is a skeleton with the place of the gate; the code that operates the instrument is written at the destination with the person.

## Never

Write a safety value. Build on a policy that is only inferred. Put a held capability in the bundle. Edit a built bundle: a change is a new build.

Reference: `plan.md 5.1` (specify, build, hand over).
