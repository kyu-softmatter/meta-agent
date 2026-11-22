---
name: autocorrelation_of_series
description: The time autocorrelation of a quantity sampled at a fixed interval, averaged over the time origins of each series and then over independent series, without subtracting a mean. Take it when a transport coefficient or a relaxation is to be read from the fluctuations of an equilibrium run, such as a stress, a velocity or a current.
---

# autocorrelation_of_series

**Gives:** `correlation`, pairs of a lag time and the average product of the quantity at a time origin and one lag later, for every lag up to the one asked; how many series were averaged and how many pairs the largest lag had in the shortest series.

**Needs:** `series`, one or more lists of values of the same quantity at the same interval (independent runs, or components that are independent and alike); `interval`, the time between two values; `max_lag`, the largest lag in samples.

**When it applies:** a stationary series whose mean is zero by symmetry, such as an off-diagonal stress at equilibrium or a velocity component. The mean is not subtracted, as the source's estimator does not.

**What it does not say:** whether the series is long enough, whether it is stationary, or which lag is the last one worth trusting. Those are the caller's.

Run it through the runner; never type its result.
