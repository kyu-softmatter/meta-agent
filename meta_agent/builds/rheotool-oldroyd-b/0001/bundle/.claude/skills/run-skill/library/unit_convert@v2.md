# `unit_convert@v2`

Rendered by the build from `skills/unit_convert@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the factor between two registered units of one dimension, and a value converted by it, into or out of an engine's own unit only through the unit a scale says it stands for.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** multiplicative units only, as the registry holds them; offset units (Celsius) are not registered and a temperature is carried in kelvin.

## Inputs

- `value` (1): the value to convert, in from_unit.
- `from_unit` (1): the registry's entry of the value's unit: name, si_factor and dim, as the registry holds them.
- `to_unit` (1): the registry's entry of the unit the value is wanted in.
- `stands_for` (1): where to_unit has no si_factor, the registry's entry of the registered unit a confirmed scale says it stands for; null otherwise.
- `from_stands_for` (1): where from_unit has no si_factor (a value an engine computed in its own unit), the registry's entry of the registered unit a confirmed scale says it stands for; null otherwise.

## Outputs

- `state` (1): converted | not_convertible.
- `factor` (1): si_factor(from, or the unit its scale stands for) over si_factor(to, or the unit its scale stands for); null when not convertible.
- `converted` (1): the value times the factor, in to_unit; null when not convertible.
- `value` (1): the value handed, unchanged, in from_unit.
- `why` (1): why no factor exists; absent when converted.

## Run

```
python src/run_skill.py unit_convert@v2 < inputs.json
```
