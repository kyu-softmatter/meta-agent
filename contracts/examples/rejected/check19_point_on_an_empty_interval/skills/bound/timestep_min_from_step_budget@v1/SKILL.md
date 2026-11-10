---
name: timestep_min_from_step_budget
description: The smallest time step that still covers the simulated time within a budget of steps. A run with a budget of steps or of computing time.
---

# timestep_min_from_step_budget

**Gives:** the smallest time step that still covers the simulated time within a budget of steps.

**Needs:** `simulated_time`, `step_budget`. Each is a row of the sheet with its own source; a constant that is a judgement is such a row, never a number inside this skill, and the bound is graded by the worst of them.

**When it applies:** A run with a budget of steps or of computing time. Take it whenever time_step is a parameter and a budget is stated.

**What it does not say:** whether the run is stable at that step; the upper bounds say that.

Run it through the runner; never type its result.
