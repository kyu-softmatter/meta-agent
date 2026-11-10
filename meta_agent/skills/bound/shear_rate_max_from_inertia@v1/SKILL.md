---
name: shear_rate_max_from_inertia
description: Upper bound on the shear rate of a cone-and-plate rheometer from fluid inertia, which drives a secondary flow at high speed. Take it when shear_rate is a parameter and the sample's viscosity and density are on the sheet.
---

# shear_rate_max_from_inertia

**Gives:** the shear rate at which the Reynolds number of the gap reaches the critical number given.

**Needs:** five rows of the sheet. `critical_reynolds_number` is a judgement and is a row with its own source, `literature:` when a source states it for the tolerated torque error, `assumed:` otherwise.

**When it applies:** a rotational rheometer with a cone-and-plate geometry and a sample whose viscosity and density are known or assumed.

**What it never does:** hold the critical number, or decide what torque error is tolerable: both are the row's.

Run it through the runner; never type its result.
