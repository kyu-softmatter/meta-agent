"""Lower bound on the shear rate of a cone-and-plate geometry from the lowest angular velocity."""


def bound(inputs):
    return {"shear_rate_min": inputs["min_angular_velocity"] / inputs["cone_angle"]}
