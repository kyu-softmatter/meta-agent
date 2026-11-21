"""The discretization error of a run's finer result, estimated from the same quantity at two resolutions by generalized
Richardson extrapolation, and the extrapolated value at zero spacing."""


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def analysis(inputs):
    fine, coarse, r, p = inputs["fine"], inputs["coarse"], inputs["refinement_ratio"], inputs["order"]
    if not all(_num(v) for v in (fine, coarse, r, p)):
        return {"estimated": False, "why": "the four inputs are numbers"}
    if r <= 1:
        return {"estimated": False, "why": "the refinement ratio is the coarse spacing over the fine one, above 1"}
    if p <= 0:
        return {"estimated": False, "why": "the order of convergence is above 0"}
    correction = (fine - coarse) / (r ** p - 1)
    return {"estimated": True, "error": abs(correction), "signed_correction": correction,
            "extrapolated": fine + correction, "why": None}
