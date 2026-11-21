# `series_maximum@v3`

Rendered by the build from `skills/series_maximum@v3/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the largest value of a sampled series and the independent variable at which it is first reached.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a series as sampled: the largest sample, not the largest value between samples, since nothing here interpolates, so the maximum and its place are as fine as the sampling; where two samples hold the largest value the first is taken. It judges nothing: whether the maximum is near a reference is a tolerance a person chooses.

## Inputs

- `series` (1): the samples as a list of pairs, each the independent variable in its own unit (a run's time at each step, a spectrum's wavelength at each channel) and the value there in the quantity's unit.

## Outputs

- `found` (1): true when the series has a largest value; false, with why, when it is empty or a sample is not a pair.
- `maximum` (1): the largest value, in the quantity's unit.
- `at` (1): the independent variable at the first sample holding the largest value, in the independent variable's own unit, which no manifest of a series of any kind can name; the reader says it from the series it handed.
- `index` (count): that sample's place in the series, counted from zero.
- `points` (count): how many samples were handed.
- `why` (1): when found is false, why nothing was found.

## Run

```
python src/run_skill.py series_maximum@v3 < inputs.json
```
