---
name: shear_rate_max_from_max_speed
description: Upper bound on the shear rate of a cone-and-plate rheometer from its top angular velocity. Take it when shear_rate is a parameter and the tool is a rotational rheometer with a cone.
---

# shear_rate_max_from_max_speed

**Gives:** the maximum shear rate the geometry reaches when the instrument turns as fast as its specification allows.

**Needs:** two rows of the sheet, bound to `max_angular_velocity` and `cone_angle`. Each row has its own source; the bound is graded by the worse of them.

**When it applies:** a rotational rheometer with a cone-and-plate geometry and a small cone angle. For parallel plates the rate varies with the radius and another skill applies.

**What it returns:** `shear_rate_max`, a `computed` number whose basis is this skill, its version and the two rows.

**What it never does:** say whether the fluid stays in the gap at that rate (inertia) or whether the torque is measurable there; those are other bounds, and the interval is the highest floor and the lowest ceiling of all of them. It reaches no device.

Run it through the runner; never type its result.
