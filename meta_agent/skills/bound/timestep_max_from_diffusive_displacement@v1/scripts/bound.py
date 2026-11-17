"""The largest time step for which the root mean squared displacement per step stays a fraction of a size."""


def bound(inputs):
    d, D = inputs["dimensions"], inputs["diffusivity"]
    if d < 1 or D <= 0:
        raise ValueError("dimensions and diffusivity must be positive")
    return {"time_step_max": (inputs["fraction"] * inputs["size"]) ** 2 / (2.0 * d * D)}
