# `series_settled@v5`

Rendered by the build from `skills/series_settled@v5/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** whether a series of readings has settled, by the change between the means of its last two windows.
- **Kind:** diagnostic. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** readings under fixed conditions, in one unit; a last mean of zero gives no relative change.

## Inputs

- `series` (1): the readings in the order they were taken, all in one unit.
- `window` (count): how many readings each mean takes; null when no row gives it, which leaves the state undecided.
- `tolerance` (1): the largest relative change of the mean between the last two windows that counts as settled; null when none is chosen.

## Outputs

- `state` (1): settled | not_settled | undecided.
- `last_mean` (1): the mean of the last window, in the readings' unit; null when there are fewer than two windows.
- `relative_change` (1): the change between the last two windows' means over the last mean; null when it cannot be computed.

## Run

```
python src/run_skill.py series_settled@v5 < inputs.json
```
