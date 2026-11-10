---
name: timestep_max_from_relaxation_time
description: The largest time step that still resolves the fluid's relaxation time. A viscoelastic simulation whose transient matters.
---

# timestep_max_from_relaxation_time

**Gives:** the largest time step that still resolves the fluid's relaxation time.

**Needs:** `relaxation_time`, `resolved_fraction`. Each is a row of the sheet with its own source; a constant that is a judgement is such a row, never a number inside this skill, and the bound is graded by the worst of them.

**When it applies:** A viscoelastic simulation whose transient matters. Take it when the stress evolution over time is what the request asks about.

**What it does not say:** anything about the grid; the Courant bound is another skill.

Run it through the runner; never type its result.
