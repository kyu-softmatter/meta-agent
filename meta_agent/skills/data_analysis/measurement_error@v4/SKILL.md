---
name: measurement_error
description: The measurement error of a measured value against a reference value, and its magnitude, taken on the two values as written so that it carries no digit neither has. Take it whenever a measured value is compared with a reference value of the same quantity, as a scientific task's agreement is, once the two are shown to be values of one quantity.
---

# measurement_error

**Gives:** the error, the measured value minus the reference value, and its magnitude, the error without its sign; each as a number and as text to the decimal places the difference has; how many places the error has, and how many both values carry.

**Needs:** the measured value and the reference value, both in the quantity's unit. Hand each as the text it was printed as where there is one, so that a trailing zero counts; a number is taken at the shortest decimal that gives it back.

**When it applies:** any comparison of a measured value with a reference value of the same quantity: a run against a published value, a run's output against the reference output its maker ships, a computation against a stated one.

**What it never does:** judge the comparison, round the error, or say whether the two values are of one quantity. Whether the magnitude is small enough is a tolerance a person chooses; whether the two were made under the same conditions and by runs that ended as they should is decided before it is taken.

Run it through the runner; never type its result.
