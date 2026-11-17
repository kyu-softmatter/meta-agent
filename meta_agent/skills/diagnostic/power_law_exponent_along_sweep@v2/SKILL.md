---
name: power_law_exponent_along_sweep
description: Whether a quantity changes along a sweep of another, by the exponent of a power law fitted through it and that exponent's standard error, judged against a tolerance and a multiple it is handed. Take it when a person asks whether something changes with size, with a setting or with time, a diffusivity along the particles' diameters or a peak's width along the integration time alike.
---

# power_law_exponent_along_sweep

**Gives:** `changes`, `does_not_change` or `undecided`, with the fitted exponent, its standard error and the number of points.

**Needs:** `sweep` and `values`, positive and of one length; `tolerance`, the largest exponent that still counts as no change; `multiple`, how many standard errors the exponent must clear that tolerance by. The two last are rows: a criterion is the person's, and this skill holds none of its own.

**When it applies:** a quantity read at three values of a sweep or more. It says `does_not_change` when the exponent with its margin stays inside the tolerance, `changes` when it stays outside, and `undecided` between, or without a criterion.

**What it does not say:** why the quantity changes, or which law it follows beyond the power fitted.

Run it through the runner; never type its result.
