---
name: shear_stress_min_from_min_torque
description: Lower bound on the shear stress of a cone-and-plate rheometer from its lowest torque. Take it when shear_stress is a parameter and the tool is a rotational rheometer with a cone.
---

# shear_stress_min_from_min_torque

**Gives:** the lowest shear stress the geometry turns into a torque the instrument can resolve.

**Needs:** two rows of the sheet, bound to `min_torque` and `cone_radius`.

**When it applies:** a rotational rheometer with a cone-and-plate geometry.

**What it never does:** treat the torque figure as a safety value: it is the specification's row, and what the instrument may be driven to is the person's.

Run it through the runner; never type its result.
