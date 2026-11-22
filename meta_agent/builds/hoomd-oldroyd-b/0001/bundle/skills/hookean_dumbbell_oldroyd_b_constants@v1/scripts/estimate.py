"""A dilute solution of Hookean dumbbells is an Oldroyd-B fluid whose polymer stress has the relaxation time
lambda = zeta/(4K) and the viscosity eta_p = n kB T lambda (Morozov and Spagnolie 2015, section 4.4.3; the same relaxation
time in Hinch and Harlen, section 6), in whatever self-consistent units the inputs are in."""


def estimate(inputs):
    z, k, n, v, kt = (inputs[x] for x in ("bead_drag", "spring_constant", "dumbbells", "volume", "thermal_energy"))
    if not (z > 0 and k > 0 and n > 0 and v > 0 and kt > 0):
        raise ValueError("every input must be positive")
    lam = z / (4.0 * k)
    return {"relaxation_time": lam, "polymer_viscosity": (n / v) * kt * lam}
