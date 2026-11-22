---
name: hookean_dumbbell_oldroyd_b_constants
description: The relaxation time and the polymer viscosity of the Oldroyd-B fluid that a dilute solution of Hookean dumbbells is, from the bead drag, the spring constant, the number of dumbbells per volume and kT, in an engine's own units. Take it when a model of dumbbells is to be compared with the constants a run measured, or a run's settings are to be chosen for a relaxation time.
---

# hookean_dumbbell_oldroyd_b_constants

**Gives:** `relaxation_time` and `polymer_viscosity` of the dumbbells' Oldroyd-B fluid, in the engine's own units.

**Needs:** `bead_drag`, the drag coefficient of one bead; `spring_constant`, K of the spring force K R with no rest length; `dumbbells` and `volume`, whose ratio is the number of dumbbells per volume; `thermal_energy`, kT.

**When it applies:** non-interacting Hookean dumbbells with no hydrodynamic interaction between their beads, in an implicit solvent.

**What it does not say:** the solvent viscosity, which an implicit solvent does not give; whether the dumbbells are dilute; and whether a run agrees with it, which is a tolerance's.

Run it through the runner; never type its result.
