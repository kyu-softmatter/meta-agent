# `standard_error_of_independent_estimates@v2`

Rendered by the build from `skills/standard_error_of_independent_estimates@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the mean of independent estimates of one quantity, their standard deviation and the standard error of the mean.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** estimates that are independent of one another: blocks long beside the correlation time, or replicates from independent starts; with correlated estimates the standard error is too small.

## Inputs

- `estimates` (1): independent estimates of one quantity, all in one unit: one per block of a run, per subset of particles, per replicate or per scan subset.

## Outputs

- `mean` (1): the mean of the estimates, in their unit.
- `standard_deviation` (1): the sample standard deviation, with n - 1.
- `standard_error` (1): the standard deviation over the square root of the number of estimates.
- `count` (count): how many estimates were handed.

## Run

```
python src/run_skill.py standard_error_of_independent_estimates@v2 < inputs.json
```
