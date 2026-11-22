# `power_law_exponent_along_sweep@v3`

Rendered by the build from `skills/power_law_exponent_along_sweep@v3/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** whether a quantity changes along a sweep, by the exponent of a power law fitted to it and that exponent's standard error, against a tolerance and a multiple it is handed.
- **Kind:** diagnostic. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a quantity that goes as a power of the swept value over the sweep, with errors alike on every point; three points or more.

## Inputs

- `sweep` (1): the values the sweep took, all positive, in one unit.
- `values` (1): the quantity at each value of the sweep, all positive, in one unit.
- `tolerance` (1): the largest size of the exponent that counts as not changing; null when none is chosen.
- `multiple` (1): how many standard errors the exponent must clear the tolerance by, on either side; null when none is chosen.

## Outputs

- `state` (1): changes | does_not_change | undecided.
- `exponent` (1): the least-squares slope of the logarithm of the values on the logarithm of the sweep; null below three points.
- `exponent_standard_error` (1): the slope's standard error, the residual sum over n - 2 over the sum of squared deviations, rooted; null below three points.
- `points` (count): how many points were fitted.

## Run

```
python src/run_skill.py power_law_exponent_along_sweep@v3 < inputs.json
```
