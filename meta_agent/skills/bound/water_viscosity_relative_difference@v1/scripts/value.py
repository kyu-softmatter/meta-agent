"""The relative difference between two values of one quantity."""


def value(inputs):
    reference = inputs["reference_viscosity"]
    return {"water_viscosity_relative_difference": (inputs["viscosity"] - reference) / reference}
