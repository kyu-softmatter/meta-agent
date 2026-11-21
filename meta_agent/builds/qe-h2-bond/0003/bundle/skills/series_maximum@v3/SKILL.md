---
name: series_maximum
description: The largest value of a sampled series and the value of the independent variable at which it is first reached, with its place in the series. Take it when a run or a measurement gives a series against time, wavelength or another variable and the question is its peak and where the peak falls, as a benchmark's largest coefficient and its instant are.
---

# series_maximum

**Gives:** the largest value of the series, the independent variable at the first sample holding it, its place counted from zero, and how many samples there were.

**Needs:** one list of samples, each a pair of the independent variable and the value.

**When it applies:** any sampled series: a coefficient against the time of each step of a run, a spectrum's counts against the wavelength of each channel. The maximum is the largest sample, as fine as the sampling.

**What it never does:** interpolate between samples, or judge the maximum. Whether it is close enough to a reference is a tolerance a person chooses.

Run it through the runner; never type its result.
