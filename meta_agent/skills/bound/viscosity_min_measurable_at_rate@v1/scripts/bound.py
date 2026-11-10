"""Lower bound on the measurable viscosity at a shear rate: the stress at the lowest torque over the rate."""
import math


def bound(inputs):
    stress_floor = 3.0 * inputs["min_torque"] / (2.0 * math.pi * inputs["cone_radius"] ** 3)
    return {"viscosity_min": stress_floor / inputs["shear_rate"]}
