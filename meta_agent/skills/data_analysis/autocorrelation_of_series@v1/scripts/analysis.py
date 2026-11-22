"""The time autocorrelation C(t) = <a(0) a(t)> of a series sampled at a fixed interval (Kim et al. 2018, arXiv:1807.08063,
equation (3)): for each series the mean over time origins of a(t0) a(t0 + lag), then the mean over the series. No mean is
subtracted. Nothing here chooses the largest lag or judges whether the series is long enough: both are the caller's."""
import math


def analysis(inputs):
    series = inputs.get("series") or []
    dt = inputs.get("interval")
    m = inputs.get("max_lag")
    out = {"correlation": None, "series_averaged": len(series), "pairs_at_max_lag": None, "state": "not_computed"}
    if not isinstance(m, int) or isinstance(m, bool) or m < 0:
        out["why"] = "max_lag is a count of samples, zero or more"
        return out
    if not isinstance(dt, (int, float)) or not dt > 0:
        out["why"] = "the interval must be positive"
        return out
    if not series or any(not isinstance(s, (list, tuple)) for s in series):
        out["why"] = "series is a list of one or more lists of values"
        return out
    shortest = min(len(s) for s in series)
    if shortest <= m:
        out["why"] = "a series of %d values holds no pair at lag %d" % (shortest, m)
        return out
    corr = []
    for lag in range(m + 1):
        per = []
        for s in series:
            v = [float(x) for x in s]
            per.append(math.fsum(v[i] * v[i + lag] for i in range(len(v) - lag)) / (len(v) - lag))
        corr.append([lag * float(dt), math.fsum(per) / len(per)])
    out.update({"correlation": corr, "pairs_at_max_lag": shortest - m, "state": "computed"})
    return out
