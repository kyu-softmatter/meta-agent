# `measurement_error@v3`

Rendered by the build from `skills/measurement_error@v3/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the measurement error of a measured value against a reference value, and its magnitude.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** two values of one quantity in one unit; it judges nothing: whether the magnitude is small enough is a tolerance a person chooses.

## Inputs

- `measured` (1): the measured quantity value, in the quantity's unit.
- `reference` (1): the reference quantity value it is compared with, in the same unit.

## Outputs

- `error` (1): the measured value minus the reference value, in the quantity's unit; its sign says on which side of the reference the measured value lies.
- `magnitude` (1): the absolute value of the error, in the quantity's unit: what a tolerance in that unit is compared with.

## Run

```
python src/run_skill.py measurement_error@v3 < inputs.json
```
