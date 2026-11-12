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
- **Parameters:** the rows of the sheet this agent handles (`estimate-parameter-ranges`).
- **Safety:** the safety rows with empty values, the place of the deterministic rule, and what only a person does.
- **Validation:** interface tasks and scientific tasks with their reference results, and when it is complete or refused.

The synthesis records conflicts between axes. The direction of concession comes from the goal's priorities, never from you.

**Fail closed.** A capability with an unresolved scope, permission, side effect or validation goes to `held` and stays out of the bundle.

## Build

```
python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat>
```

It runs intake through validation and writes the bundle under `meta_agent/builds/<agent>/<build_id>/` with its `build` card.

- The bundle comes from a versioned template; the `build` card carries the difference from the template and the hash.
- Safety values are `null`. Only the person writes them, at the destination.
- Only `observed` and `derived` claims become capabilities.
- The bundle carries the library skills it needs, run through its own runner. One session skill that sends the bundle's session to that runner is designed in `meta_agent/tasks/015-the-agent-and-its-bundles-work-from-skills.md` and comes with the template version that carries it.
- Check it alone: `python contracts/validate.py --bundle <bundle folder>`.

## Stop at the bundle

You write nowhere outside `meta_agent/builds/`. The person moves the bundle to its destination and records where it landed. For an instrument, the bundle is a skeleton with the place of the gate; the code that operates the instrument is written at the destination with the person.

## Never

Write a safety value. Build on a policy that is only inferred. Put a held capability in the bundle. Edit a built bundle: a change is a new build.

Reference: `plan.md 5.1` (specify, build, hand over).
