---
name: tolerance_from_reference
description: A scientific task's tolerance by the person's standing rule, from the reference as its source gives it: the uncertainty the source states, otherwise the larger of half a unit in the last digit the reference prints and the run's own numerical error where that was estimated, a two-grid estimate of it entering three times over. Take it when a scientific task compares a measured value with a reference and the person has given no tolerance for it.
---

# tolerance_from_reference

**Gives:** the tolerance, in the quantity's unit, which way of the rule gave it, whether the run's own error was weighed, and the factor it entered with.

**Needs:** the reference as its source prints it, as text; the uncertainty the source states for it, or null; the run's own numerical error as an estimating skill gave it, or null; and how it was estimated (two grids, three or more grids, or a series' standard error).

**When it applies:** a scientific task whose reference is one value of one quantity and for which the person gave no tolerance. A tolerance the person gave overrides it.

**What it never does:** judge the comparison, choose between two uncertainties a source states, or read digits off a number that was stored without its printed form.

Run it through the runner; never type its result.
