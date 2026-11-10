"""The largest time step an explicit treatment of diffusion allows on a grid."""


def bound(inputs):
    return {"time_step_max": inputs["diffusion_number_limit"] * inputs["cell_size"] ** 2 / inputs["diffusivity"]}
