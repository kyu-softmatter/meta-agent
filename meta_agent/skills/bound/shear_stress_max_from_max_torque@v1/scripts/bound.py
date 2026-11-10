"""Upper bound on the shear stress of a cone-and-plate geometry from the highest torque."""
import math


def bound(inputs):
    return {"shear_stress_max": 3.0 * inputs["max_torque"] / (2.0 * math.pi * inputs["cone_radius"] ** 3)}
