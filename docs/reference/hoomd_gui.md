# Reference case: HOOMD_GUI

https://github.com/kyu-softmatter/HOOMD_GUI — the person's own repository. Registered here as the reference case for a particle-simulation GUI (plan.md 2.6, 5.7, 10). Code is not reused until the repository has a licence (plan.md 14-16).

## Fact check (README as read on 2026-10-29)

| Item | What the README says | Status |
|---|---|---|
| Nature | "idea sketch / concept document" for a GUI around HOOMD-blue | concept + skeleton |
| Implemented | a Pixi environment; a 2D particle editor (box, boundaries, particles, properties); browser-side checks; JSON import / export of the project document; a Local Runner | present |
| Not implemented | code generation; running HOOMD-blue | absent |
| Roadmap | move authoritative validation into a Python package, `hoomd_gui_core` | planned |
| First platform | macOS ARM64 | stated |
| Licence | none in the repository (GitHub reports no licence) | **undecided** — all rights reserved by default |
| Internal disagreement | the About text says the GUI is not implemented; the body describes the editor as working | the body is the more specific statement; verify by running it before relying on either |

The reading above is of the README only; the code was not executed. A verification with evidence belongs in a `material` card when the repository is dropped into `meta_agent/inbox/materials/`.

## What this repository takes from it (as principles, not code)

- **Visual modelling**: a model and its conditions are composed without writing code.
- **Transparent code generation**: it is visible how a GUI setting becomes execution code.
- **A separated scientific core**: the physics model and the validation logic live outside the GUI, so the CLI, Python and agents reuse the same validators. This is MP13: the GUI is not a source of scientific judgement, its input checks call the core's validators, and no threshold lives only in the GUI.
- **Reproducibility first** and **validation before execution**.
- **A versioned JSON project document** as the hand-over format.
- **A loopback-only Local Runner** as the safe default for anything that executes.

## What it does not settle

- The GUI architecture and stack for this repository (plan.md 14-16). The plan starts from a parameter form composed of common components, and a domain editor only when a request needs one.
- Whether the `web/` + `python/` split of HOOMD_GUI becomes the common frame's starting point. Decided after its licence exists.
- Anything about engines other than HOOMD-blue; the registry (`contracts/registry/engines.json`) lists them without ranking.

## Relation to the first testbed

The first testbed is the lab's rheometer and a rheology engine (plan.md 10). A GUI for either, if the lab wants one (`gui_preference`), would be a parameter form or an instrument panel derived from the capability specification; HOOMD_GUI's particle editor is the reference for the later particle-based case (HOOMD-blue, plan.md 14-20), not for the first one.
