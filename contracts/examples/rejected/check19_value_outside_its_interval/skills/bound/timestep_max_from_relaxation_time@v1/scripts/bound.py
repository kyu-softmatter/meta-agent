"""The largest time step that still resolves the fluid's relaxation time."""


def bound(inputs):
    return {"time_step_max": inputs["resolved_fraction"] * inputs["relaxation_time"]}
