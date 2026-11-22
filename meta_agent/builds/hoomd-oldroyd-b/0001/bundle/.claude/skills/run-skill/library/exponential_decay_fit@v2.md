# `exponential_decay_fit@v2`

Rendered by the build from `skills/exponential_decay_fit@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the decay time and the amplitude of a single exponential decay fitted by least squares on the logarithm over a window the caller names.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a single exponential over the window; least squares on ln y weighs every point's relative error alike, so noise near zero, where ln y is wide, pulls the fit, and the window is the caller's to keep it out; a sum of exponentials gives an effective decay time that depends on the window.

## Inputs

- `points` (1): pairs [t, y] of a decaying signal, the time and the value each in one unit throughout.
- `window` (1): [t_first, t_last], the times between which (both included) the points are fitted, in the unit of the points' times.

## Outputs

- `decay_time` (1): tau of y = A exp(-t/tau), minus one over the fitted slope of ln y against t, in the unit of the points' times; null when not fitted or when the fitted slope is not negative.
- `amplitude` (1): A, the fitted value at t = 0, in the unit of the points' values.
- `residual_standard_deviation` (1): of ln y about the fitted line, the residual sum of squares over n - 2, rooted; null with two points.
- `points_fitted` (count): how many points lay in the window.
- `state` (1): fitted | not_decaying | not_fitted.
- `why` (1): why nothing was fitted; absent when fitted.

## Run

```
python src/run_skill.py exponential_decay_fit@v2 < inputs.json
```
