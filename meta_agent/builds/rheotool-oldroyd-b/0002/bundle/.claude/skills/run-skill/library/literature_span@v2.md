# `literature_span@v2`

Rendered by the build from `skills/literature_span@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the span of one quantity across suitable materials, branch 3 of the person's standing rule for tolerances: the interval from the lowest to the highest of the values and stated error ranges the materials give, a value stated with an uncertainty entering as the value less and plus that uncertainty, each entry naming its material and how its system compares; no span from fewer than two values and no stated range.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** one quantity, every entry in one unit: the skill converts nothing and cannot see a unit, so an entry in another unit is the reader's to convert through a skill first. Which materials are suitable, which of a material's numbers is its value for the quantity (its own result, not every row of its refinement study or of the solutions it collects), and whether two materials mean the same quantity are the reader's to say, in each entry's compares, after classify-knowledge; the skill takes the words as handed and refuses only their absence. A value a material states with an uncertainty enters as the range from the value less that uncertainty to the value plus it (the person, 2026-11-19, 'Widen by uncertainty'): the uncertainty is taken as the material states it, with no multiplier and no change of its kind, so a standard deviation and an expanded uncertainty enter alike and the entry's compares says which it is; an uncertainty stated relative to the value, or in another unit, is the reader's to bring to the quantity's unit through a skill first; an uncertainty of zero gives a range of no width, which still counts as a stated range. One value with its uncertainty is one stated range and gives a span by itself. Two materials that quote one number are one value, which the reader leaves out, not the skill. Two equal values give a span of no width. It judges nothing: the span is an acceptance interval only as the rule's next skill and the person's standing rule take it, a tolerance the person gave overrides it, and a pass the person gave by judgement stays as it is.

## Inputs

- `entries` (1): a list, one entry for each value or stated error range of the one quantity, every number in the quantity's unit. An entry is an object: material, the material card the number was read from (its path or id); compares, in words, how that material's system, quantity and engine compare with the task's, as written after classify-knowledge, and, where an uncertainty is given, what kind of uncertainty the material states (a standard deviation, an expanded uncertainty, a bound); and either value, one value the material gives for the quantity, with uncertainty beside it where the material states one for that value (a finite number not below zero, in the quantity's unit, as the material states it), or low and high, the two edges of one error range the material states, as it writes them.

## Outputs

- `low` (1): the lowest of the values and range edges, in the quantity's unit: as its entry gave it, or the entry's value less its uncertainty; null, with why, where there is no span.
- `high` (1): the highest of the values and range edges, in the quantity's unit: as its entry gave it, or the entry's value plus its uncertainty; null where there is no span.
- `lowest_from` (1): the material of the entry that gave the lowest; where two entries hold it, the first handed.
- `highest_from` (1): the material of the entry that gave the highest; where two entries hold it, the first handed.
- `values` (count): how many entries gave one value with no uncertainty.
- `ranges` (count): how many entries gave a stated range: two edges, or one value with its stated uncertainty.
- `why` (1): why there is no span; else null.

## Run

```
python src/run_skill.py literature_span@v2 < inputs.json
```
