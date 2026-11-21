"""The period of two masses joined by a harmonic bond: the reduced mass mu = m1 m2 / (m1 + m2) (HyperPhysics, Reduced
Mass), the angular frequency omega = sqrt(k / mu) and the period T = 2 pi / omega (HyperPhysics, Simple Harmonic Motion),
in whatever self-consistent units the inputs are in."""
import math


def estimate(inputs):
    k, a, b = inputs["force_constant"], inputs["mass_a"], inputs["mass_b"]
    if not (k > 0 and a > 0 and b > 0):
        raise ValueError("the force constant and both masses must be positive")
    mu = a * b / (a + b)
    omega = math.sqrt(k / mu)
    return {"reduced_mass": mu, "angular_frequency": omega, "period": 2.0 * math.pi / omega}
