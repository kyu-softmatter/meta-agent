# `timestep_max_from_courant@v2`

Rendered by the build from `skills/timestep_max_from_courant@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the largest time step the Courant condition allows on a grid.
- **Kind:** bound. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** explicit or semi-implicit time stepping of advection or of waves on a grid or a mesh, whatever program does it; not for a method without a grid (particles, Monte Carlo), where the condition does not arise. The limit itself depends on the scheme and is an input.

## Inputs

- `courant_limit` (1): the Courant number the scheme is run below; a judgement that depends on the scheme, bound to a row with its own source.
- `cell_size` (m): the smallest cell or element of the grid or mesh, along the direction the signal travels.
- `velocity` (m/s): the largest speed at which the solution carries information across the grid: the largest flow velocity for advection, the wave speed for a wave equation.

## Outputs

- `time_step_max` (s): the upper bound on the time step from the Courant condition.

## Run

```
python src/run_skill.py timestep_max_from_courant@v2 < inputs.json
```
