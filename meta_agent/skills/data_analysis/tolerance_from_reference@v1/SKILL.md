---
name: tolerance_from_reference
description: A scientific task's tolerance by the person's standing rule, from the reference as its source gives it: the uncertainty the source states, otherwise half a unit in the last digit the reference prints. Take it when a scientific task compares a measured value with a reference and the person has given no tolerance for it.
---

# tolerance_from_reference

**Gives:** the tolerance, in the quantity's unit, and which way of the rule gave it.

**Needs:** the reference as its source prints it, as text, and the uncertainty the source states for it, or null.

**When it applies:** a scientific task whose reference is one value of one quantity and for which the person gave no tolerance. A tolerance the person gave overrides it.

**What it never does:** judge the comparison, choose between two uncertainties a source states, or read digits off a number that was stored without its printed form.

Run it through the runner; never type its result.
