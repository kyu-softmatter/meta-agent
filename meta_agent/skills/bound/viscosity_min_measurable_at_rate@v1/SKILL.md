---
name: viscosity_min_measurable_at_rate
description: Lower bound on the viscosity a cone-and-plate rheometer can measure at a given shear rate, from its lowest torque. Take it when viscosity is a parameter and a shear rate of the measurement is on the sheet.
---

# viscosity_min_measurable_at_rate

**Gives:** the smallest viscosity that still gives a torque above the instrument's floor at the shear rate named.

**Needs:** three rows of the sheet, bound to `min_torque`, `cone_radius` and `shear_rate`. The rate is a row with a value: the planned rate, or the lowest rate of a sweep.

**When it applies:** a rotational rheometer with a cone-and-plate geometry, when a shear rate of the measurement is known.

**What it never does:** choose the shear rate, or say that a sample is too thin: it gives the floor, and the row it is compared with is the caller's.

Run it through the runner; never type its result.
