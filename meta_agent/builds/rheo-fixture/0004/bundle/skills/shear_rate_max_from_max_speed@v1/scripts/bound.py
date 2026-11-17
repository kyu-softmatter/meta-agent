"""Upper bound on the shear rate of a cone-and-plate geometry from the top angular velocity."""


def bound(inputs):
    return {"shear_rate_max": inputs["max_angular_velocity"] / inputs["cone_angle"]}
