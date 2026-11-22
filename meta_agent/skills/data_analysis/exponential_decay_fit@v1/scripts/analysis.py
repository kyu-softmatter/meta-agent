"""A single exponential y = A exp(-t/tau), the relaxation of a Maxwell fluid's modulus (Morozov and Spagnolie 2015,
equation (1.51)), fitted by linear least squares of ln y against t (NIST/SEMATECH e-Handbook 4.4.3.1) over the points whose
time lies in the window the caller names. Nothing here chooses the window or drops a point."""
import math


def analysis(inputs):
    pts = inputs.get("points") or []
    w = inputs.get("window")
    out = {"decay_time": None, "amplitude": None, "residual_standard_deviation": None, "points_fitted": 0,
           "state": "not_fitted"}
    if not (isinstance(w, (list, tuple)) and len(w) == 2 and w[0] <= w[1]):
        out["why"] = "window is [t_first, t_last] with t_first <= t_last"
        return out
    if any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in pts):
        out["why"] = "each point is a pair: a time and a value"
        return out
    sel = [(float(t), float(y)) for t, y in pts if w[0] <= t <= w[1]]
    out["points_fitted"] = len(sel)
    if len(sel) < 2 or len(set(t for t, _ in sel)) < 2:
        out["why"] = "a line needs two distinct times in the window"
        return out
    if any(y <= 0 for _, y in sel):
        out["why"] = "a value in the window is not positive and has no logarithm"
        return out
    n = len(sel)
    ts, ls = [t for t, _ in sel], [math.log(y) for _, y in sel]
    tm, lm = math.fsum(ts) / n, math.fsum(ls) / n
    sxx = math.fsum((t - tm) ** 2 for t in ts)
    slope = math.fsum((t - tm) * (l - lm) for t, l in zip(ts, ls)) / sxx
    icpt = lm - slope * tm
    if n > 2:
        rss = math.fsum((l - icpt - slope * t) ** 2 for t, l in zip(ts, ls))
        out["residual_standard_deviation"] = math.sqrt(rss / (n - 2))
    out["amplitude"] = math.exp(icpt)
    if slope >= 0:
        out["state"] = "not_decaying"
        out["why"] = "the fitted slope of ln y is not negative"
        return out
    out["decay_time"] = -1.0 / slope
    out["state"] = "fitted"
    return out
