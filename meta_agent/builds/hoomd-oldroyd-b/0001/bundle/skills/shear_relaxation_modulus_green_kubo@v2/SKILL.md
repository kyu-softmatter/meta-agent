---
name: shear_relaxation_modulus_green_kubo
description: The shear relaxation modulus and the shear viscosity of a fluid from the autocorrelation of an off-diagonal stress at equilibrium, by the Green-Kubo relation, the viscosity integrated by the trapezoidal rule up to a time the caller names. Take it when a viscosity or a relaxation modulus is to be read from an equilibrium run's stress fluctuations.
---

# shear_relaxation_modulus_green_kubo

**Gives:** `modulus`, pairs of a time and the stress autocorrelation times the volume over kT; `viscosity`, its integral from zero to `end`; how many samples the integral took.

**Needs:** `correlation`, pairs of a lag time from zero and the off-diagonal stress autocorrelation (as `autocorrelation_of_series` gives it); `volume` of the system; `thermal_energy`, kT; `end`, the time up to which to integrate, one of the correlation's times.

**When it applies:** an equilibrium run in which the stress component handed is the full off-diagonal stress of the system.

**What it does not say:** where the integral has converged. The time up to which to integrate is the caller's, read off the modulus.

Run it through the runner; never type its result.
