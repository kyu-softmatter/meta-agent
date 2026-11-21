"""The largest time step that resolves a period into a stated number of steps: the period over that number. The number
is a judgement and an input; the skill holds none."""


def bound(inputs):
    period, n = inputs["period"], inputs["steps_per_period"]
    if not period > 0:
        raise ValueError("the period must be positive")
    if not (isinstance(n, int) and not isinstance(n, bool) and n > 0):
        raise ValueError("the steps per period are a positive count")
    return {"time_step_max": period / n}
