# `autocorrelation_of_series@v2`

Rendered by the build from `skills/autocorrelation_of_series@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the time autocorrelation of a quantity sampled at a fixed interval, averaged over the time origins of each series and over independent series.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a stationary series sampled at equal intervals; no mean is subtracted, so a quantity whose mean is not zero gives the correlation of its full value, not of its fluctuation; the statistical error grows with the lag and this skill does not estimate it (the source's equations (7) and (8) do).

## Inputs

- `series` (1): one or more lists of values of one quantity, each sampled at the same interval from an equilibrium run; independent runs, or independent and alike components (xy, xz, yz of a stress).
- `interval` (1): the time between two consecutive values, in the unit of time of the run.
- `max_lag` (count): the largest lag, in samples, for which the correlation is computed; every series must be longer than it.

## Outputs

- `correlation` (1): pairs [lag time, C], lag time = lag x interval, C the mean over the series of the mean over time origins of a(t0) a(t0 + lag), in the square of the unit of the values.
- `series_averaged` (count): how many series were averaged.
- `pairs_at_max_lag` (count): the number of time origins the largest lag had in the shortest series.
- `state` (1): computed | not_computed.
- `why` (1): why nothing was computed; absent when computed.

## Run

```
python src/run_skill.py autocorrelation_of_series@v2 < inputs.json
```
