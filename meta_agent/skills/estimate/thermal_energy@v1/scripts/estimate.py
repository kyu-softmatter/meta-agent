"""The thermal energy k_B T, with the Boltzmann constant exact in the SI (NIST, 2022 CODATA recommended values)."""

BOLTZMANN_J_PER_K = 1.380649e-23     # exact; NIST CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?k


def estimate(inputs):
    t = inputs["temperature"]
    if not t > 0:
        raise ValueError("an absolute temperature is positive")
    return {"thermal_energy": BOLTZMANN_J_PER_K * t}
