"""Viscosity at another temperature by the Arrhenius form, relative to a reference point."""
import math


def value(inputs):
    ratio = math.exp(inputs["activation_temperature"] * (1.0 / inputs["temperature"] - 1.0 / inputs["reference_temperature"]))
    return {"solvent_viscosity_at_run_temperature": inputs["reference_viscosity"] * ratio}
