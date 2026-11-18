"""The largest value of a sampled series, the independent variable where it is first reached, and its place."""


def _none(why):
    return {"found": False, "why": why}


def analysis(inputs):
    series = inputs["series"]
    if not series:
        return _none("an empty series has no largest value")
    if any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in series):
        return _none("a sample is not a pair of the independent variable and the value")
    i = max(range(len(series)), key=lambda j: (series[j][1], -j))
    return {"found": True, "maximum": series[i][1], "at": series[i][0], "index": i, "points": len(series)}
