---
name: water_viscosity_iapws_sr6
description: Viscosity of liquid water at 0.1 MPa as a function of temperature, by the correlation of the IAPWS supplementary release SR6-08(2011). Take it when a row needs the viscosity of water between 253.15 K and 383.15 K at or near atmospheric pressure.
---

# water_viscosity_iapws_sr6

**Gives:** the viscosity of liquid water at 0.1 MPa, a correlation: the row it gives says `value_kind: correlation`.

**Needs:** one row, bound to `temperature`, in kelvin.

**When it applies:** water between 253.15 K and 383.15 K, at 0.1 MPa or, as the release says, anywhere between the saturation pressure and 0.3 MPa. Outside the temperature range it stops and says so: the release says the equation is not to be extrapolated.

**What it rests on:** Eq. (7) and Table 5 of the release, copied from the document; the release states 1 % for the stable liquid. That uncertainty is the correlation's and is not on the row: a row's `uncertainty` is what its input rows carry over.

**What it never does:** speak for a solution, a suspension or any liquid that is not water.

Run it through the runner; never type its result.
