# `discretization_error_from_two_resolutions@v1`

Rendered by the build from `skills/discretization_error_from_two_resolutions@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the discretization error of a run's finer result, from the same quantity at two resolutions, and the value extrapolated to zero spacing.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** two runs of one scheme on the same problem in its asymptotic range, the quantity converging monotonically with the spacing at the order handed; higher-order terms are neglected, so the estimate is as good as that range holds. It says nothing of a modelling error, and judges nothing.

## Inputs

- `fine` (1): the quantity from the run at the finer resolution, in its unit.
- `coarse` (1): the same quantity from the run at the coarser resolution, in the same unit.
- `refinement_ratio` (1): the coarse spacing over the fine one (a mesh size, a time step, a grid cell), above 1.
- `order` (1): the order of convergence of the scheme, the formal one or one observed over three resolutions; a row with its own source.

## Outputs

- `estimated` (1): true when an error was estimated; false, with why, when the inputs do not allow it.
- `error` (1): the estimated discretization error of the finer result, its magnitude, in the quantity's unit: the run's own numerical error the tolerance rule weighs.
- `signed_correction` (1): the finer result's difference from the extrapolated value, with its sign.
- `extrapolated` (1): the value extrapolated to zero spacing.
- `why` (1): why no error was estimated, or null.

## Run

```
python src/run_skill.py discretization_error_from_two_resolutions@v1 < inputs.json
```
