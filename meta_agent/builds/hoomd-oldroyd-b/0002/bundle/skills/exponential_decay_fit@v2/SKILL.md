---
name: exponential_decay_fit
description: The decay time and the amplitude of a single exponential decay fitted to positive values of a series over a window the caller names, by least squares on the logarithm. Take it when a relaxation time is to be read from a relaxation modulus, a correlation or any signal expected to decay as one exponential.
---

# exponential_decay_fit

**Gives:** `decay_time` and `amplitude` of y = amplitude x exp(-t / decay_time), the residual standard deviation of the logarithm, and how many points were fitted.

**Needs:** `points`, pairs of a time and a value; `window`, the first and the last time to fit, both the caller's.

**When it applies:** a decay that is one exponential over the window, every value in it positive.

**What it does not say:** whether one exponential is the right model, or where the window should be. A value in the window that is not positive stops the fit; it is not dropped.

Run it through the runner; never type its result.
