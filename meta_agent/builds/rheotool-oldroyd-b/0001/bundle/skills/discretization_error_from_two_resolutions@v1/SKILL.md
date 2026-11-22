---
name: discretization_error_from_two_resolutions
description: The discretization error of a run's finer result, estimated from the same quantity at two resolutions and the scheme's order of convergence, with the value extrapolated to zero spacing. Take it when a run was made at two resolutions of a mesh, a grid or a time step and its own numerical error is wanted, as the tolerance rule weighs it.
---

# discretization_error_from_two_resolutions

**Gives:** the estimated error of the finer result, its signed correction, and the value extrapolated to zero spacing.

**Needs:** the quantity at the finer and at the coarser resolution, the ratio of their spacings, and the scheme's order of convergence, a row with its own source.

**When it applies:** two runs of one scheme on the same problem, close enough to converged that the quantity changes with the spacing at the order handed.

**What it never does:** estimate a modelling error, choose the order, or judge the result.

Run it through the runner; never type its result.
