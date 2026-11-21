"""Whether a series of readings has settled, by a relative tolerance it is handed.

v4: a window that is not a whole number of readings of at least one, null where no row gives it, says undecided as
too short a series does, where v3 raised on it (meta_agent/failures.jsonl rheotool-22)."""


def _count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


def diagnostic(inputs):
    series, w, tol = inputs["series"], inputs.get("window"), inputs.get("tolerance")
    if not _count(w) or len(series) < 2 * w:
        return {"state": "undecided", "last_mean": None, "relative_change": None}
    last = sum(series[-w:]) / w
    before = sum(series[-2 * w:-w]) / w
    change = None if last == 0 else abs(last - before) / abs(last)
    if tol is None or change is None:
        state = "undecided"
    else:
        state = "settled" if change <= tol else "not_settled"
    return {"state": state, "last_mean": last, "relative_change": change}
