---
name: analyse-physical-system
description: Work out the scales of the physical system a request is about (its extent, its smallest feature, its fastest and slowest timescales, its signal) as rough ranges, each given by a library skill and never by the model. Use when a request names a sample, a phenomenon or a model to be measured or simulated, before parameter ranges are estimated, and whenever the system or its conditions change.
---

# Analyse the physical system

What is wanted is orders of magnitude: the rough range of each key quantity of the system under study. The requirements of a measurement or a simulation follow from these, so this comes before `estimate-parameter-ranges`.

## Do this

1. **Name the system from the request.** The sample or the model, its material and its conditions, taken from the `agent_goal` and from sources that were read. A property you do not have a source for is a gap.
2. **List the scales that matter.** Its extent and its smallest feature; its fastest and its slowest timescale; the size of its signal; any other quantity the request turns on. Say why each matters for this request.
3. **Find a library skill for each.** `python -m meta_agent.src.skills list` shows what the library holds. One relation is one skill.
4. **Run it; never type its result.** `python -m meta_agent.src.skills run <id@vN> --inputs <file>`. Every input is a row with its own source. A judgement (a margin, a multiple) is an input row, not a number in the code.
5. **Give a range, not a point.** An estimate is two rows, a minimum and a maximum. Its grade follows its worst input.
6. **Where no skill gives the scale,** do not estimate it yourself. Either build the skill from a source with a worked case (`build-library-skill`), or record the gap and what would close it: a source, a measurement, or the person.
7. **Say what was neglected.** An approximate relation holds only under conditions; name them beside the range, and name the exact relation where one exists so that both can stand on the sheet.

## Writes

Computed rows of the request's `parameter_sheet`, each naming the skill that gave it and the rows it used, so that the gate can run the skill again.

## Not built yet

A card of its own for the rough-range pass and a skill kind for estimates of scale are designed in `meta_agent/tasks/011-rough-ranges-and-the-models-choice.md`. Until they land, scales are computed rows as above.

## Never

Write a number you worked out or remember. Give a single value where the relation is an estimate. Treat a vendor's or a paper's value for another sample as this system's.

Reference: `plan.md 5.3`, `plan.md 14-32`.
