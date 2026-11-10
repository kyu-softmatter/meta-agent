---
name: timestep_max_from_relaxation_time
description: Upper bound on the time step of a viscoelastic simulation from the relaxation time of the constitutive model. Take it when time_step is a parameter and the transient of a viscoelastic fluid is what is computed.
---

# timestep_max_from_relaxation_time

**Gives:** the largest step that spans no more than the stated fraction of the relaxation time.

**Needs:** two rows of the sheet. `resolved_fraction` is a judgement and is a row with its own source.

**When it applies:** a viscoelastic simulation whose transient is the result.

**What it never does:** hold the fraction, or decide that the transient matters: a steady result reached by time marching is the reason a caller gives for not applying it.

Run it through the runner; never type its result.
