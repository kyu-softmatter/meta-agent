"""Lower bound on the shear stress of a cone-and-plate geometry from the lowest torque."""
import math


def bound(inputs):
    return {"shear_stress_min": 3.0 * inputs["min_torque"] / (2.0 * math.pi * inputs["cone_radius"] ** 3)}
