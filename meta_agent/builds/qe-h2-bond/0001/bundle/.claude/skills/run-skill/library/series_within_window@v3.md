# `series_within_window@v3`

Rendered by the build from `skills/series_within_window@v3/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** whether the mean of a series' last readings lies inside a band, between a lowest and a highest value it is handed.
- **Kind:** diagnostic. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** readings in one unit, the band in the same unit; the edges belong to the band.

## Inputs

- `series` (1): the readings in the order they were taken, all in one unit.
- `window` (count): how many of the last readings the mean takes.
- `low` (1): the lowest value inside the band, in the readings' unit; null when none is chosen.
- `high` (1): the highest value inside the band, in the readings' unit; null when none is chosen.

## Outputs

- `state` (1): within | below | above | undecided.
- `last_mean` (1): the mean of the last window, in the readings' unit; null when there are fewer readings than the window.

## Run

```
python src/run_skill.py series_within_window@v3 < inputs.json
```
