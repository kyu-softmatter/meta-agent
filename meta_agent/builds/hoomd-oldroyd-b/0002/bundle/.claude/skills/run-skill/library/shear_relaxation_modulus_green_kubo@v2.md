# `shear_relaxation_modulus_green_kubo@v2`

Rendered by the build from `skills/shear_relaxation_modulus_green_kubo@v2/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the shear relaxation modulus and the Green-Kubo shear viscosity from the autocorrelation of an off-diagonal stress at equilibrium.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** linear response at equilibrium: the stress handed must be the system's whole off-diagonal stress, sampled densely enough for the trapezoidal rule; a kinetic part drawn afresh each step (as in Brownian dynamics) adds an uncorrelated spike at lag zero that the trapezoidal rule weighs by half a spacing, a bias the caller can see in the modulus.

## Inputs

- `correlation` (1): pairs [lag time, C] from lag time zero at a fixed spacing, C the autocorrelation of one off-diagonal stress component (or the mean over xy, xz, yz), in pressure squared of the run's units.
- `volume` (engine_length^3): the volume of the system whose stress was sampled.
- `thermal_energy` (engine_energy): the thermal energy of the run.
- `end` (1): the lag time up to which the viscosity is integrated, one of the correlation's lag times, in its unit of time.

## Outputs

- `modulus` (1): pairs [lag time, G], G = V C / kT, the shear relaxation modulus in pressure of the run's units.
- `viscosity` (engine_viscosity): V/kT times the trapezoidal integral of C from zero to end: the shear viscosity when end lies where the integral has levelled off.
- `samples_integrated` (count): how many lag times the integral took, zero and end included.
- `state` (1): computed | not_computed.
- `why` (1): why nothing was computed; absent when computed.

## Run

```
python src/run_skill.py shear_relaxation_modulus_green_kubo@v2 < inputs.json
```
