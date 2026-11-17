---
name: diffusive_regime_from_msd
description: Whether a mean squared displacement is in its diffusive regime, where it grows in proportion to the lag, by the exponent fitted over windows of consecutive lags against a tolerance it is handed, and from which lag on it stays so. A particle in a simulation engine or a bead tracked under a microscope alike.
---

# diffusive_regime_from_msd

**Gives:** `diffusive`, `not_diffusive` or `undecided` over the last window, its exponent, the lag from which every window is diffusive, and how many windows were fitted.

**Needs:** `lags` and `msd`, positive and of one length; `window`, how many lags each fit takes; `tolerance`, how far from one the exponent may be and still count as diffusive. The window and the tolerance are rows: a criterion is the person's, and this skill holds none of its own.

**When it applies:** before a diffusivity is fitted to a mean squared displacement, to choose the lags the fit uses. An exponent below one is subdiffusive and above one superdiffusive or ballistic; neither is diffusive.

**What it does not say:** the diffusivity itself, which is a fit over the lags this skill finds.

Run it through the runner; never type its result.
