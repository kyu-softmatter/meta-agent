---
name: water_viscosity_kestin_1978
description: Viscosity of liquid water at atmospheric pressure as a function of temperature, by the two correlating equations of Kestin, Sokolov and Wakeham. Take it when a row needs the viscosity of water between 265.15 K and 423.15 K, or beside another correlation of the same quantity to compare the two.
---

# water_viscosity_kestin_1978

**Gives:** the viscosity of liquid water at atmospheric pressure, a correlation: the row it gives says `value_kind: correlation`.

**Needs:** one row, bound to `temperature`, in kelvin.

**When it applies:** water from -8 to 150 degrees Celsius. It uses the paper's more accurate equation from 0 to 40 degrees Celsius and the wider one elsewhere, as the paper's own table does. Outside the range it stops and says so.

**What it rests on:** Eqs. (15) and (16) of the paper and the viscosity at 20 degrees Celsius it adopts, copied from the paper. It is an older analysis than the IAPWS release and rests on other measurements; the two side by side are a comparison, not an average.

**What it never does:** choose between itself and another correlation: both rows stand on the sheet and the difference is a row of its own.

Run it through the runner; never type its result.
