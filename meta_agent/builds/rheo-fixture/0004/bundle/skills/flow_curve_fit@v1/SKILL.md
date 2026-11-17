---
name: flow_curve_fit
description: Fits a power law to a flow curve, shear stress against shear rate. Take it when a steady shear sweep has been measured and the question is how the stress scales with the rate.
---

# flow_curve_fit

**Gives:** the consistency and the flow index of `stress = consistency * rate ^ flow_index`, by least squares of the logarithm of the stress on the logarithm of the rate, with the root-mean-square residual of that fit and the number of points. They are `computed` numbers; `basis` says how.

**Needs:** `shear_rate` and `shear_stress`, two lists of the same length, handed in as inputs. It opens no file.

**When it applies:** a monotonic flow curve without a yield stress or a plateau. It fits what it is given: choosing the points, and judging whether a power law describes them, is the caller's, with the residual in hand.

**What it never does:** drop a point, judge the residual against a threshold, or reach a device. Fewer than two points, lists of different lengths, a rate or a stress that is not positive, or a single rate repeated give no fit and say why.
