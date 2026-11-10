---
name: shear_stress_max_from_max_torque
description: Upper bound on the shear stress of a cone-and-plate rheometer from its highest torque. Take it when shear_stress is a parameter and the tool is a rotational rheometer with a cone.
---

# shear_stress_max_from_max_torque

**Gives:** the highest shear stress the geometry turns into a torque the instrument can apply or bear.

**Needs:** two rows of the sheet, bound to `max_torque` and `cone_radius`.

**When it applies:** a rotational rheometer with a cone-and-plate geometry.

**What it never does:** treat the torque figure as a safety value: it is the specification's row, and what the instrument may be driven to is the person's.

Run it through the runner; never type its result.
