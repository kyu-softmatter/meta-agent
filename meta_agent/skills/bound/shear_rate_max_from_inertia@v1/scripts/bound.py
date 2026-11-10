"""Upper bound on the shear rate of a cone-and-plate geometry from the secondary-flow (inertia) criterion."""
from dimensionless import reynolds_cone_plate


def bound(inputs):
    per_unit_rate = reynolds_cone_plate(inputs["density"], 1.0, inputs["cone_angle"], inputs["cone_radius"], inputs["viscosity"])
    return {"shear_rate_max": inputs["critical_reynolds_number"] / per_unit_rate}
