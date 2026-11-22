"""The observed order of convergence of a quantity from three runs at a constant refinement ratio."""
import math


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def analysis(inputs):
    coarse, medium, fine, r = inputs["coarse"], inputs["medium"], inputs["fine"], inputs["refinement_ratio"]
    if not all(_num(v) for v in (coarse, medium, fine, r)):
        return {"observed": False, "why": "the four inputs are numbers"}
    if r <= 1:
        return {"observed": False, "why": "the refinement ratio is a coarser spacing over a finer one, above 1"}
    if medium == fine:
        return {"observed": False, "why": "the two finer results are equal, so no order can be read from them"}
    q = (coarse - medium) / (medium - fine)
    if q <= 0:
        return {"observed": False, "why": "the three results do not converge monotonically, so no order can be read from them"}
    return {"observed": True, "order": math.log(q) / math.log(r), "why": None}
