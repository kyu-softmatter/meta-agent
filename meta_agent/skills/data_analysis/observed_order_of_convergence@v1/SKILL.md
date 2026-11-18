---
name: observed_order_of_convergence
description: The observed order of convergence of a quantity from three runs, each finer than the last by the same refinement ratio. Take it when a run's own numerical error is to be estimated from a refinement and no source gives the scheme's order, or when the order a source gives is to be checked against the runs.
---

# observed_order_of_convergence

**Gives:** the order of convergence the three results show, or why they show none.

**Needs:** the quantity from the coarsest, the middle and the finest run, and their constant refinement ratio.

**When it applies:** three runs of one scheme on one problem, refined by the same ratio each time, converging monotonically.

**What it never does:** add a safety factor, take an order from a source, or judge the result.

Run it through the runner; never type its result.
