---
name: timestep_max_from_courant
description: Upper bound on the time step of a grid-based solver from the Courant condition. Take it when time_step is a parameter and the engine advances a flow in time on a grid.
---

# timestep_max_from_courant

**Gives:** the largest step for which a fluid element crosses no more than the stated fraction of a cell.

**Needs:** three rows of the sheet. `courant_limit` is a judgement and is a row with its own source.

**When it applies:** a grid-based solver advancing a flow in time.

**What it never does:** hold the Courant limit: it depends on the scheme and is the row's.

Run it through the runner; never type its result.
