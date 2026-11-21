# contracts/examples/bridge

Two hand-overs between built agents, of two unrelated kinds (meta_agent/tasks/031; the person, 2026-11-20, "Rheometer → rheology engine (Recommended)"):

- `dft-md/`: a Quantum ESPRESSO agent hands the H2 bond's force constant and rest length to a HOOMD-blue agent, an engine to an engine. Both values are used, each into one of HOOMD-blue's own units through a scale marked as the person's.
- `rheometer-engine/`: a rheometer agent hands a measured viscosity and the sample's temperature to a rheology engine agent, an instrument to an engine. The viscosity is used, converted into the engine's unit; the temperature is held, since the engine's build declares no row for it.

In each, the producer's card is in its `outbox/`; the copy and its envelope in the receiver's `inbox/<thread>/` were made by running `contracts/tools/bridge.py carry` on these fixture folders, so their hashes are read off that run; the envelope's `released_by: human` is a fixture value, the tool having been run by the design seat that wrote this folder. The receiver's `envelope/handovers.json` declares the rows that take a hand-over, and its `received/` holds one receipt per value, each factor as `contracts/tools/units.py factor` printed it. Every value is a fixture and nothing more (`../README.md`). Check 25 judges these folders with the repository.
