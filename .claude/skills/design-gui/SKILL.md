---
name: design-gui
description: Design the screen a person uses to run a built agent, as a specification derived from the agent's capabilities and tool contracts, with no judgement of its own. Use only when the goal or the lab's profile asks for a graphical interface, after the tool contracts exist. A graphical interface is optional and none is required.
---

# Design the GUI

The GUI is a person's way in to a validated model and runner. It is not a source of scientific judgement.

## First, whether one is wanted

The goal's GUI choice says: none, a parameter form, a domain visual editor, or the lab's own GUI reused. If it says none, or says nothing, stop here: do not design one.

## Do this

1. **Derive, never invent.** The specification (`contracts/schemas/gui_spec.schema.json`) is derived from the bundle's capabilities and from its tool contracts. Every input field maps to a tool parameter or to a capability item.
2. **No threshold lives in the GUI.** A limit, a range or a default comes from the envelope and the scientific core. A GUI file holds none.
3. **Validation is called, not copied.** The GUI's checking calls the scientific core's validator and has no rules of its own. A check that passes in the GUI does not make a condition valid.
4. **Compose from common parts.** A shared frame (project, parameters, validation, execution, results) and a domain editor per kind of model. A new component only for a visualisation nothing else gives.
5. **Changes go through the specification.** A proposal that changes the GUI changes the specification, never the GUI's files alone.

## Not built yet

No GUI, no common components and no check on a GUI exist in this repository, and its architecture is not decided (`plan.md 14-16`). Today this skill ends in a specification card, or in a line of the `agent_spec` saying none was asked for.

## Never

Let a field exist that maps to nothing. Put a number in a GUI file. Open anything but the local loopback from a GUI's runner.

Reference: `plan.md 5.7`.
