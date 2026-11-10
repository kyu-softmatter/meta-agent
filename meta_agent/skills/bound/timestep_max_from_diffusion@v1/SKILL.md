---
name: timestep_max_from_diffusion
description: Upper bound on the time step of a grid-based solver from the diffusion of momentum or of a scalar. Take it when time_step is a parameter and diffusion is advanced explicitly, or is to be resolved in time.
---

# timestep_max_from_diffusion

**Gives:** the largest step for which the diffusion number stays below the stated limit.

**Needs:** three rows of the sheet. `diffusion_number_limit` is a judgement and is a row with its own source.

**When it applies:** a grid-based solver in which diffusion is advanced explicitly or must be resolved in time.

**What it never does:** hold the limit, or decide whether the solver treats diffusion implicitly: that is the reason a caller gives for not applying it.

Run it through the runner; never type its result.
