---
name: timestep_max_from_courant
description: The largest time step the Courant condition allows on a grid. A grid-based flow solver that advances in time.
---

# timestep_max_from_courant

**Gives:** the largest time step the Courant condition allows on a grid.

**Needs:** `courant_limit`, `cell_size`, `velocity`. Each is a row of the sheet with its own source; a constant that is a judgement is such a row, never a number inside this skill, and the bound is graded by the worst of them.

**When it applies:** A grid-based flow solver that advances in time. Take it whenever time_step is a parameter of such an engine.

**What it does not say:** whether a step this large resolves the fluid's own time scales; that is another bound.

Run it through the runner; never type its result.
