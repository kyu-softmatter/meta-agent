"""The largest time step the Courant condition allows on a grid."""


def bound(inputs):
    return {"time_step_max": inputs["courant_limit"] * inputs["cell_size"] / inputs["velocity"]}
