# `observed_order_of_convergence@v1`

Rendered by the build from `skills/observed_order_of_convergence@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the observed order of convergence of a quantity from three runs at a constant refinement ratio.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** three runs of one scheme on the same problem, each finer than the last by the same ratio, in the asymptotic range and converging monotonically; where the differences change sign there is no order to read. It keeps no safety factor (the person, 2026-11-18), and judges nothing.

## Inputs

- `coarse` (1): the quantity from the coarsest of the three runs, in its unit.
- `medium` (1): the same quantity from the middle run, in the same unit.
- `fine` (1): the same quantity from the finest run, in the same unit.
- `refinement_ratio` (1): the constant ratio of each run's spacing to the next finer one's, above 1.

## Outputs

- `observed` (1): true when an order was read from the three results; false, with why, when they do not converge monotonically or the inputs do not allow it.
- `order` (1): the observed order of convergence.
- `why` (1): why no order was read, or null.

## Run

```
python src/run_skill.py observed_order_of_convergence@v1 < inputs.json
```
