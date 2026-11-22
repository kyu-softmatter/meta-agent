# `oldroyd_b_startup_channel_velocity@v1`

Rendered by the build from `skills/oldroyd_b_startup_channel_velocity@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the start-up velocity of an Oldroyd-B fluid in a planar channel under a suddenly applied pressure gradient, by Waters and King's series.
- **Kind:** estimate. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** an incompressible Oldroyd-B fluid between infinite parallel plates, laminar and one-dimensional, starting from rest with no stress, under a gradient applied as a step; the series converges with the terms as one over the cube of the term's index, and a truncated series does not give zero velocity at t = 0 exactly; a solvent fraction of zero (the upper-convected Maxwell fluid) is within it.

## Inputs

- `half_width` (1): h, the distance from the centreline to a wall, in the length unit of one self-consistent system of units (SI for OpenFOAM).
- `density` (1): rho, mass per volume in that system.
- `solvent_viscosity` (1): eta_s, a dynamic viscosity in that system.
- `polymer_viscosity` (1): eta_p, a dynamic viscosity in that system.
- `relaxation_time` (1): lambda, a time in that system.
- `driving` (1): K = -dp/dx, the constant pressure gradient along the channel (force per volume) applied from time zero, in that system.
- `position` (1): y, the distance from the centreline at which the velocity is wanted, 0 <= |y| <= h, in the length unit.
- `times` (1): the times since the gradient was applied, zero or more, in the time unit.
- `terms` (count): how many terms of the series to sum, one or more.

## Outputs

- `velocity` (1): pairs [t, u], u the velocity along the channel at the position asked, in the velocity unit of the system.
- `elasticity_number` (1): E = lambda eta0 / (rho h^2), eta0 = eta_s + eta_p.
- `solvent_fraction` (1): beta = eta_s / eta0.
- `steady_mean_velocity` (1): K h^2 / (3 eta0), the mean over the channel of the steady velocity, in the velocity unit of the system.

## Run

```
python src/run_skill.py oldroyd_b_startup_channel_velocity@v1 < inputs.json
```
