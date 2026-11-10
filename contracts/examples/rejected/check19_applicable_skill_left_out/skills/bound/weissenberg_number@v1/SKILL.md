---
name: weissenberg_number
description: The Weissenberg number of a shear flow. Any sheet that carries a relaxation time and a shear rate.
---

# weissenberg_number

**Gives:** the Weissenberg number of a shear flow.

**Needs:** `relaxation_time`, `shear_rate`. Each is a row of the sheet with its own source; a constant that is a judgement is such a row, never a number inside this skill, and the bound is graded by the worst of them.

**When it applies:** Any sheet that carries a relaxation time and a shear rate. It is a value, not a bound: a row computed from two other rows.

**What it does not say:** whether the flow is stable at that number.

Run it through the runner; never type its result.
