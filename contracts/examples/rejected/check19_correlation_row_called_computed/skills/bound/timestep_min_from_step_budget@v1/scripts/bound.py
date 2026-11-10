"""The smallest time step that still covers the simulated time within a budget of steps."""


def bound(inputs):
    return {"time_step_min": inputs["simulated_time"] / inputs["step_budget"]}
