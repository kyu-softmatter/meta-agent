"""Whether the mean of a series' last readings lies inside a band it is handed."""


def diagnostic(inputs):
    series, w = inputs["series"], inputs["window"]
    low, high = inputs.get("low"), inputs.get("high")
    if w < 1 or len(series) < w:
        return {"state": "undecided", "last_mean": None}
    last = sum(series[-w:]) / w
    if low is None or high is None:
        state = "undecided"
    elif low > high:
        raise ValueError("low must not lie above high")
    elif last < low:
        state = "below"
    elif last > high:
        state = "above"
    else:
        state = "within"
    return {"state": state, "last_mean": last}
