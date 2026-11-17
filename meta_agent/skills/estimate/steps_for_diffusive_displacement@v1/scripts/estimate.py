"""The run time and the steps for a root mean squared displacement of a multiple of a size: MSD = 2 d D t."""
import math


def estimate(inputs):
    d, D, dt = inputs["dimensions"], inputs["diffusivity"], inputs["time_step"]
    if d < 1 or D <= 0 or dt <= 0:
        raise ValueError("dimensions, diffusivity and time_step must be positive")
    t = (inputs["multiple"] * inputs["size"]) ** 2 / (2.0 * d * D)
    return {"run_time": t, "steps": int(math.ceil(t / dt))}
