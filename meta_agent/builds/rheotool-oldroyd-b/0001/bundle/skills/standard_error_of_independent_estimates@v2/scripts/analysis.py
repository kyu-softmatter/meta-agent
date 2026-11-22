"""The mean of independent estimates, their sample standard deviation and the standard error of the mean."""
import math


def analysis(inputs):
    xs = list(inputs["estimates"])
    n = len(xs)
    if n < 2:
        raise ValueError("a standard deviation needs two estimates or more")
    mean = math.fsum(xs) / n
    sd = math.sqrt(math.fsum((x - mean) ** 2 for x in xs) / (n - 1))
    return {"mean": mean, "standard_deviation": sd, "standard_error": sd / math.sqrt(n), "count": n}
