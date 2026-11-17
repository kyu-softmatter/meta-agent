"""Whether a series of readings has settled, by a relative tolerance it is handed."""


def diagnostic(inputs):
    series, w, tol = inputs["series"], inputs["window"], inputs.get("tolerance")
    if w < 1 or len(series) < 2 * w:
        return {"state": "undecided", "last_mean": None, "relative_change": None}
    last = sum(series[-w:]) / w
    before = sum(series[-2 * w:-w]) / w
    change = None if last == 0 else abs(last - before) / abs(last)
    if tol is None or change is None:
        state = "undecided"
    else:
        state = "settled" if change <= tol else "not_settled"
    return {"state": state, "last_mean": last, "relative_change": change}
