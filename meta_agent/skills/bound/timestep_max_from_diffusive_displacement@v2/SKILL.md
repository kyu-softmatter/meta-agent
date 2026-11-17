---
name: timestep_max_from_diffusive_displacement
description: The largest time step for which a particle's root mean squared displacement in one step stays a stated fraction of the smallest size in the system. Take it when time_step is a parameter of a stochastic run of diffusing particles, a colloid in a Brownian dynamics engine or a tracer molecule in a molecular dynamics engine alike.
---

# timestep_max_from_diffusive_displacement

**Gives:** the largest time step, `time_step_max`.

**Needs:** `fraction`, the margin; `size`, the smallest size; `diffusivity`, the largest diffusivity; `dimensions`. Each is a row with its own source; the fraction is a choice, and a person's.

**When it applies:** a run that moves particles by random displacements each step. Its smallest and fastest particle sets the bound.

**What it does not say:** the stability limit of a grid's explicit scheme, which is another skill.

Run it through the runner; never type its result.
