---
name: oldroyd_b_startup_channel_velocity
description: The velocity at one distance from the centreline of a planar channel against time, after a constant pressure gradient is suddenly applied to an Oldroyd-B fluid at rest, by Waters and King's series truncated at a number of terms the caller names; with the elasticity number, the solvent's share of the viscosity and the steady mean velocity. Take it as the analytical reference of a start-up channel flow simulation.
---

# oldroyd_b_startup_channel_velocity

**Gives:** `velocity`, pairs of a time and the velocity at the position asked; `elasticity_number`, `solvent_fraction` and `steady_mean_velocity`.

**Needs:** the channel's `half_width`, the fluid's `density`, `solvent_viscosity`, `polymer_viscosity` and `relaxation_time`, the `driving` pressure gradient (force per volume along the channel), the `position` from the centreline, the `times`, and `terms`, how many terms of the series to sum.

**When it applies:** an incompressible Oldroyd-B fluid at rest between two infinite parallel plates, driven from time zero by a constant pressure gradient, with no slip at the walls; the flow is one-dimensional throughout.

**What it does not say:** how many terms are enough, or how close a simulation must come. Both are the caller's.

Run it through the runner; never type its result.
