---
name: harmonic_oscillation_period
description: The reduced mass, the angular frequency and the period of two masses joined by a harmonic bond, in an engine's own self-consistent units. Take it when a time step must resolve a bond's vibration, or a bond's period is wanted from its force constant and the masses it joins.
---

# harmonic_oscillation_period

**Gives:** `reduced_mass`, `angular_frequency` and `period`, in the engine's own units.

**Needs:** `force_constant` (the k of U = k (r - r0)^2 / 2), `mass_a` and `mass_b`, all in one self-consistent system of units.

**When it applies:** a harmonic bond between two point masses, moving classically, with no other force on them.

**What it does not say:** how many steps a period needs, or whether a classical treatment of the bond is sound. The first is a judgement, a row's; the second is not this skill's.

Run it through the runner; never type its result.
