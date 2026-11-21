---
name: standard_error_of_independent_estimates
description: The mean of several independent estimates of one quantity, with their standard deviation and the standard error of the mean. Take it when a coefficient was fitted once per block of a run, per subset of particles, per replicate or per subset of scans, and its uncertainty is wanted.
---

# standard_error_of_independent_estimates

**Gives:** the mean, the sample standard deviation and the standard error of the mean, and how many estimates there were.

**Needs:** `estimates`, the independent estimates of one quantity in one unit. Each is a fit or a reading made on its own part of the data; this skill does not make them.

**When it applies:** estimates that do not depend on one another. Blocks of one run count as independent only when each is long beside the run's correlation time.

**What it does not say:** whether the blocks were long enough, or whether the uncertainty is small enough for a purpose; the second is a criterion, and a person's.

Run it through the runner; never type its result.
