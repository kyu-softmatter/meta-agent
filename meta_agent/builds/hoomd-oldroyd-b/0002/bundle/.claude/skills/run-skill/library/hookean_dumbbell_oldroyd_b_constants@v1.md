# `hookean_dumbbell_oldroyd_b_constants@v1`

Rendered by the build from `skills/hookean_dumbbell_oldroyd_b_constants@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the relaxation time and the polymer viscosity of a dilute solution of Hookean dumbbells as an Oldroyd-B fluid, in an engine's own units.
- **Kind:** estimate. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** Hookean springs of unbounded extension, beads with Stokes drag and no hydrodynamic interaction, dumbbells that do not interact (dilute); finite extensibility, excluded volume or hydrodynamic interaction change both constants, and this skill does not say by how much.

## Inputs

- `bead_drag` (engine_drag): zeta, the drag coefficient of one bead (the gamma of HOOMD-blue's Brownian method for the bead's type).
- `spring_constant` (engine_energy/engine_length^2): K of the spring force K R, a spring with no rest length (k of a harmonic bond U = k (r - r0)^2 / 2 with r0 = 0).
- `dumbbells` (count): the number of dumbbells, not of beads.
- `volume` (engine_length^3): the volume they are in.
- `thermal_energy` (engine_energy): the thermal energy.

## Outputs

- `relaxation_time` (engine_time): lambda = zeta / (4 K), the relaxation time of the dumbbells' upper-convected Maxwell stress.
- `polymer_viscosity` (engine_viscosity): eta_p = n kT lambda with n the dumbbells per volume.

## Run

```
python src/run_skill.py hookean_dumbbell_oldroyd_b_constants@v1 < inputs.json
```
