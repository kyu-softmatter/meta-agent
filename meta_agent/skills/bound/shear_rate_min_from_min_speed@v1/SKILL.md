---
name: shear_rate_min_from_min_speed
description: Lower bound on the shear rate of a cone-and-plate rheometer from its lowest controllable angular velocity. Take it when shear_rate is a parameter and the tool is a rotational rheometer with a cone.
---

# shear_rate_min_from_min_speed

**Gives:** the minimum shear rate the geometry reaches when the instrument turns as slowly as its specification says it can control.

**Needs:** two rows of the sheet, bound to `min_angular_velocity` and `cone_angle`.

**When it applies:** a rotational rheometer with a cone-and-plate geometry and a small cone angle.

**What it never does:** say that a stress is measurable at that rate: the torque floor is another skill, and the interval is the highest floor and the lowest ceiling of all of them.

Run it through the runner; never type its result.
