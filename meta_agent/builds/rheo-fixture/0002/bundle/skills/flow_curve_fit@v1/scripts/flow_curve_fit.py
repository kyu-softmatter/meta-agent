"""A power law through a flow curve: least squares of ln(stress) on ln(rate)."""
import math


def _no(why):
    return {"fitted": False, "why": why}


def flow_curve_fit(inputs):
    rates, stresses = inputs["shear_rate"], inputs["shear_stress"]
    if len(rates) != len(stresses):
        return _no("shear_rate and shear_stress have different lengths")
    if len(rates) < 2:
        return _no("a line through fewer than two points is not a fit")
    if any(v <= 0 for v in rates) or any(v <= 0 for v in stresses):
        return _no("a rate or a stress is not positive; the logarithm is not defined")
    x = [math.log(v) for v in rates]
    y = [math.log(v) for v in stresses]
    n = len(x)
    mx, my = math.fsum(x) / n, math.fsum(y) / n
    sxx = math.fsum((a - mx) ** 2 for a in x)
    if sxx == 0:
        return _no("every point has the same rate")
    slope = math.fsum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    intercept = my - slope * mx
    rms = math.sqrt(math.fsum((b - (intercept + slope * a)) ** 2 for a, b in zip(x, y)) / n)
    return {"fitted": True, "flow_index": slope, "consistency": math.exp(intercept), "residual_rms_log": rms,
            "points": n, "value_kind": "computed",
            "basis": "least squares of ln(shear_stress) on ln(shear_rate) over %d points; flow_curve_fit@v1" % n}
