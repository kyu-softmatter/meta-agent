# `tolerance_from_reference@v5`

Rendered by the build from `skills/tolerance_from_reference@v5/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** a scientific task's tolerance by the person's standing rule, its branches in order: the reference's stated uncertainty; else the span of the quantity across suitable materials, as an acceptance interval; else the larger of half a unit in its last printed digit and the run's own numerical error, a two-grid estimate of that error entering three times over; for a reference the source gives as exact, the run's own error alone in that last branch.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** one reference value of one quantity. The stated uncertainty, where there is one, is taken as handed: which uncertainty a source states (a standard error, the spread between its refinement levels) is the reader's to say. The last printed digit is read off the text as printed, so a trailing zero counts and a number already stored as a float has lost its printed form; an integer printed with trailing zeros is read as printed. A run's numerical error is taken as handed, with how it was estimated: estimating it is another skill's, and a run error handed without run_error_from gives no tolerance. A reference marked exact is taken as the source gives it: whether a value is exact is the reader's to say from the source, and an exact reference with no run error estimated gives no tolerance. A span is taken as handed, its two edges as the span's skill gave them: finding the materials, saying how each compares and computing the span are not this skill's, and it widens the span by nothing. A span is taken before the printed digit and the run's error whether or not the reference is marked exact, and after a stated uncertainty. It judges nothing, a tolerance the person gave overrides it, and a pass the person gave by judgement stays as it is.

## Inputs

- `printed` (1): the reference value as its source prints it, as text, its last digit kept as printed (a trailing zero included); in the quantity's unit; it may be null for a reference marked exact.
- `stated_uncertainty` (1): the uncertainty the source states for that value, in the quantity's unit, or null where it states none.
- `run_numerical_error` (1): the run's own numerical error of the quantity, in its unit, as an estimating skill gave it through the runner (the difference between two resolutions, or the standard error of a series the run produced); null where it was not estimated.
- `run_error_from` (1): how the run's own error was estimated: two_grids (two resolutions, as discretization_error_from_two_resolutions gives it), three_or_more_grids, or series_standard_error; null where the run's error is null.
- `exact` (1): true where the source gives the reference as exact (an analytic value of the case's own settings, a defined constant), so that it has no printed digit to be uncertain in and the half-digit branch does not apply; false or null otherwise.
- `span_low` (1): the low edge of the span of the quantity across suitable materials, in the quantity's unit, as the span's skill gave it through the runner; null where it gave none or no material was handed.
- `span_high` (1): the high edge of that span, in the quantity's unit; null where there is none.

## Outputs

- `tolerance` (1): the tolerance about the reference, in the quantity's unit; null where the span gave an interval in its place, and null, with why, where the inputs give none.
- `interval_low` (1): the low edge of the acceptance interval, in the quantity's unit, where the span gave it: the measured value is to lie between the two edges, the edges as handed; else null.
- `interval_high` (1): the high edge of that interval; else null.
- `from` (1): stated_uncertainty, literature_span, last_printed_digit or run_numerical_error: which of the rule's ways gave it; null where none did.
- `run_error_estimated` (1): true when a run's numerical error was handed and weighed, false when it was not estimated and the half-digit branch alone applied, null where the stated uncertainty or the span was taken.
- `factor` (1): the factor the run's own error entered with: 3 for a two-grid estimate, 1 for three or more grids or a series' standard error; null where no run error was weighed.
- `why` (1): why no tolerance was given, or that the run's error was not estimated; else null.

## Run

```
python src/run_skill.py tolerance_from_reference@v5 < inputs.json
```
