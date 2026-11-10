---
name: water_density_iapws_sr6
description: Density of liquid water at 0.1 MPa as a function of temperature, by the specific-volume correlation of the IAPWS supplementary release SR6-08(2011). Take it when a row needs the density of water between 253.15 K and 383.15 K at or near atmospheric pressure.
---

# water_density_iapws_sr6

**Gives:** the density of liquid water at 0.1 MPa, a correlation: the row it gives says `value_kind: correlation`.

**Needs:** one row, bound to `temperature`, in kelvin.

**When it applies:** water between 253.15 K and 383.15 K at 0.1 MPa. Outside the temperature range it stops and says so. At standard atmospheric pressure the release gives a pressure term in its Eq. (6); this skill gives the value at 0.1 MPa and does not apply it.

**What it rests on:** Eq. (2), Eq. (4) and Table 1 of the release, copied from the document.

**What it never does:** speak for a solution, or for water under a pressure the release does not cover.

Run it through the runner; never type its result.
