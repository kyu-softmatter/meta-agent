---
name: timestep_max_from_courant
description: Upper bound on the time step of a solver that advances advection or a wave in time on a grid or a mesh, from the Courant condition. Take it when time_step is a parameter and the method steps a field in time on a grid or a mesh, whatever program does it.
---

# timestep_max_from_courant

**Gives:** the largest step for which the signal crosses no more than the stated fraction of a cell in one step.

**Needs:** three rows of the sheet. `courant_limit` is a judgement and is a row with its own source. `velocity` is the largest speed at which the solution carries information: the flow's largest velocity for advection, the wave's speed for a wave equation. `cell_size` is the smallest cell or element along that direction.

**When it applies:** a grid- or mesh-based method advancing a field in time, by finite volumes, finite elements or finite differences. Not a method without a grid, such as particles or Monte Carlo; there, say it is not applied and why.

**What it never does:** hold the Courant limit: it depends on the scheme and is the row's.

Run it through the runner; never type its result.
