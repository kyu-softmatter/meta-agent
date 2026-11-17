# `read_ranges@v1`

Rendered by the build from `skills/read_ranges@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** reads the modes and the range of each quantity as the device itself reports them.
- **Kind:** hardware_range. **Side effect:** read_device. **Status:** usable.
- **Calls tools:** `ranges`.
- **Uses skills:** none.
- **Valid for:** a device whose ranges tool returns modes and rows of quantity, min, max and unit.

## Inputs

- `quantities` (1): the names of the quantities wanted; an empty list means all the device reports.

## Outputs

- `reported` (1): true when the device answered.
- `modes` (1): the modes the device lists.
- `ranges` (1): one row per quantity: quantity, min, max, unit, reported_by, tool.
- `missing` (1): wanted quantities the device did not report.
- `inconsistent` (1): quantities whose row lacks an end or a unit, or whose ends are reversed.
- `why` (1): why nothing was reported.
- `error` (1): the error contract the tool returned, unchanged.

## Run

```
python src/run_skill.py read_ranges@v1 < inputs.json
```
