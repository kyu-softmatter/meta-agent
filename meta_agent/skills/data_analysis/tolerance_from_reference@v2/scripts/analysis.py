"""A scientific task's tolerance by the person's standing rule, as amended on 2026-11-18: the reference's stated
uncertainty where the source states one; otherwise the larger of half a unit in the last digit the reference prints
and the run's own numerical error, where that error was estimated."""
from decimal import Decimal, InvalidOperation


def _none(why):
    return {"tolerance": None, "from": None, "run_error_estimated": None, "why": why}


def _positive(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def analysis(inputs):
    stated = inputs.get("stated_uncertainty")
    if stated is not None:
        if not _positive(stated):
            return _none("a stated uncertainty is a positive number")
        return {"tolerance": float(stated), "from": "stated_uncertainty", "run_error_estimated": None, "why": None}
    run_error = inputs.get("run_numerical_error")
    if run_error is not None and not (_positive(run_error) or run_error == 0):
        return _none("a run's numerical error is a number not below zero")
    printed = inputs.get("printed")
    if not isinstance(printed, str) or not printed.strip():
        return _none("neither a stated uncertainty nor the reference as printed was handed")
    try:
        d = Decimal(printed.strip())
    except InvalidOperation:
        return _none("the reference as printed is not a number: %r" % printed)
    if not d.is_finite():
        return _none("the reference as printed is not a finite number: %r" % printed)
    half = float(Decimal(1).scaleb(d.as_tuple().exponent) / 2)
    if run_error is None:
        return {"tolerance": half, "from": "last_printed_digit", "run_error_estimated": False,
                "why": "the run's numerical error was not estimated, so half the last printed digit alone applies"}
    if float(run_error) > half:
        return {"tolerance": float(run_error), "from": "run_numerical_error", "run_error_estimated": True, "why": None}
    return {"tolerance": half, "from": "last_printed_digit", "run_error_estimated": True, "why": None}
