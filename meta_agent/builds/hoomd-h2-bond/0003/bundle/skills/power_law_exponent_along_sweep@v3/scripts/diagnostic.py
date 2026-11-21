"""Whether a quantity changes along a sweep: the least-squares exponent of a power law and its standard error."""
import math


def diagnostic(inputs):
    xs, ys = list(inputs["sweep"]), list(inputs["values"])
    tol, k = inputs.get("tolerance"), inputs.get("multiple")
    n = len(xs)
    if n != len(ys):
        raise ValueError("sweep and values have different lengths")
    if any(v <= 0 for v in xs + ys):
        raise ValueError("a value of the sweep or of the quantity is not positive; its logarithm is not defined")
    if n < 3:
        return {"state": "undecided", "exponent": None, "exponent_standard_error": None, "points": n}
    lx, ly = [math.log(v) for v in xs], [math.log(v) for v in ys]
    mx, my = math.fsum(lx) / n, math.fsum(ly) / n
    sxx = math.fsum((a - mx) ** 2 for a in lx)
    if sxx == 0:
        raise ValueError("every point has the same value of the sweep")
    slope = math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx
    intercept = my - slope * mx
    residual = math.fsum((b - intercept - slope * a) ** 2 for a, b in zip(lx, ly))
    se = math.sqrt(residual / (n - 2) / sxx)
    if tol is None or k is None:
        state = "undecided"
    elif abs(slope) + k * se <= tol:
        state = "does_not_change"
    elif abs(slope) - k * se > tol:
        state = "changes"
    else:
        state = "undecided"
    return {"state": state, "exponent": slope, "exponent_standard_error": se, "points": n}
