"""Whether a mean squared displacement is diffusive: the exponent of its power law over windows of consecutive lags."""
import math


def _slope(xs, ys):
    lx, ly = [math.log(v) for v in xs], [math.log(v) for v in ys]
    n = len(lx)
    mx, my = math.fsum(lx) / n, math.fsum(ly) / n
    sxx = math.fsum((a - mx) ** 2 for a in lx)
    return math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx


def diagnostic(inputs):
    lags, msd, w, tol = list(inputs["lags"]), list(inputs["msd"]), inputs["window"], inputs.get("tolerance")
    if len(lags) != len(msd):
        raise ValueError("lags and msd have different lengths")
    if w < 2:
        raise ValueError("a window of fewer than two lags fits no exponent")
    if any(v <= 0 for v in lags + msd) or any(b <= a for a, b in zip(lags, lags[1:])):
        raise ValueError("the lags must be positive and rising, and the msd positive")
    starts = range(len(lags) - w + 1)
    exps = [_slope(lags[i:i + w], msd[i:i + w]) for i in starts]
    if not exps:
        return {"state": "undecided", "exponent": None, "diffusive_from": None, "windows": 0}
    if tol is None:
        return {"state": "undecided", "exponent": exps[-1], "diffusive_from": None, "windows": len(exps)}
    ok = [abs(a - 1.0) <= tol for a in exps]
    first = None
    for i in range(len(ok) - 1, -1, -1):
        if not ok[i]:
            break
        first = i
    return {"state": "diffusive" if ok[-1] else "not_diffusive", "exponent": exps[-1],
            "diffusive_from": lags[first] if first is not None else None, "windows": len(exps)}
