---
name: same_measurand
description: Whether a measured value and a reference value are values of one measurand, judged on the conditions each states and on how each run ended, against the ends a row hands it. Take it before a measured value's difference from a reference is taken or reported, whenever the two come from separate runs or sources, as a run's output and the reference output its maker ships do.
---

# same_measurand

**Gives:** `same`, `different` or `undecided`; the conditions the two state with different values, the conditions only one of them states, and the runs whose end is not among the ends handed; and why, in words.

**Needs:** the conditions each value was obtained under, as the run's output and the reference state them, under the same names; how each run ended, as its engine or instrument reports it, or null where nothing states it; and the ends a run may have for its value to be compared, from a row, or null where none is chosen.

**When it applies:** before the agreement of a pair is taken: a run against the reference output of the same example, a value against a published one, two runs of one system. A pair it calls `different` has no agreement to report: report the pair, the skill's answer and why. A pair it calls `undecided` is reported with what would settle it.

**What it never does:** choose which conditions define the measurand or which ends are acceptable; read a run's output; take the difference of the two values or judge it.

Run it through the runner; never type its result.
