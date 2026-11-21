---
name: harmonic_well_fit
description: The potential constant, the rest position and the energy at the minimum of a harmonic well, fitted by least squares to energies computed or measured at several positions about a minimum, with the residual and whether the minimum lies inside the points. Take it when a bond, a trap or any well is to be handed on as the harmonic potential an engine takes.
---

# harmonic_well_fit

**Gives:** `force_constant` (k), `rest_position` (x0) and `well_energy` (U0) of U = U0 + k (x - x0)^2 / 2, the residual standard deviation, whether x0 lies inside the positions handed, and a state: `fitted`, `no_minimum` or `not_fitted`.

**Needs:** `points`, the energy curve as pairs of a position and the energy there, each part in one unit throughout. k comes out in the unit of the energies over the square of the unit of the positions; x0 in the unit of the positions.

**When it applies:** points about a minimum, close enough that the well is harmonic over them. The form is the harmonic bond of an MD engine, so k and x0 are what that engine means by its potential constant and rest length.

**What it does not say:** which points to take, or whether the residual is small enough. Both are the caller's; a criterion is a person's.

Run it through the runner; never type its result.
