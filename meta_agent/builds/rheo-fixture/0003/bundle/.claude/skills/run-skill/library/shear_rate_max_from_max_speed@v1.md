# `shear_rate_max_from_max_speed@v1`

Rendered by the build from `skills/shear_rate_max_from_max_speed@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the highest shear rate a cone-and-plate geometry reaches at the instrument's top angular velocity.
- **Kind:** bound. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** small cone angles, where the shear rate is uniform across the gap; other limits (inertia, torque) are other skills.

## Inputs

- `max_angular_velocity` (rad/s): the top angular velocity the instrument's specification states.
- `cone_angle` (rad): the angle between the cone and the plate.

## Outputs

- `shear_rate_max` (1/s): the upper bound on the shear rate from the speed limit alone.

## Run

```
python src/run_skill.py shear_rate_max_from_max_speed@v1 < inputs.json
```
