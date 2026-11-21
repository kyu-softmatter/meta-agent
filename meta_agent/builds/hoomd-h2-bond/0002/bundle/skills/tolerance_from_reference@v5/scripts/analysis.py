"""A scientific task's tolerance by the person's standing rule, as amended on 2026-11-18 and widened on 2026-11-19, its
branches in their order: the reference's stated uncertainty where the source states one; else the span [lowest,
highest] of the quantity across suitable materials, where the span's skill gave one, as an acceptance interval ('Yes,
add literature span', 'Min-max of values', 'Yes, widen it'); else the larger of half a unit in the last digit the
reference prints and the run's own numerical error, where that error was estimated, a two-grid estimate of it entering
three times over ('Yes, factor 3': the factor of safety of Roache's grid convergence index for a comparison of two
grids). An estimate from three or more grids, or from the standard error of a series, enters as it is.

v4: a reference the source gives as exact (an analytic value, a defined constant, a setting of the case itself) has no
printed digit to be uncertain in, so the half-digit branch does not apply to it and the run's own error alone gives the
tolerance; without that error it gives none (the design role's reply f071852 to rheotool-28, item a).

v5: the span is handed as its skill gave it, its two edges, and is taken before the printed digit and the run's error
and after a stated uncertainty. It is not a tolerance about the reference but an interval the measured value is to lie
in, so the tolerance is null and the interval's edges are given as handed; nothing is computed from them
(meta_agent/tasks/028)."""
from decimal import Decimal, InvalidOperation

# how the run's own error was estimated, and the factor it enters the rule with (the person, 2026-11-18)
FACTORS = {"two_grids": 3.0, "three_or_more_grids": 1.0, "series_standard_error": 1.0}


def _none(why):
    return {"tolerance": None, "interval_low": None, "interval_high": None, "from": None, "run_error_estimated": None,
            "factor": None, "why": why}


def _given(out):
    """An answer of a branch that gives a tolerance about the reference: it carries no interval."""
    return dict(out, interval_low=None, interval_high=None)


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) != float("inf")


def _positive(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def analysis(inputs):
    stated = inputs.get("stated_uncertainty")
    if stated is not None:
        if not _positive(stated):
            return _none("a stated uncertainty is a positive number")
        return _given({"tolerance": float(stated), "from": "stated_uncertainty", "run_error_estimated": None,
                       "factor": None, "why": None})
    low, high = inputs.get("span_low"), inputs.get("span_high")
    if low is not None or high is not None:
        if not (_number(low) and _number(high)):
            return _none("a span has a low and a high edge, both finite numbers")
        if low > high:
            return _none("the low edge of the span lies above its high edge")
        return {"tolerance": None, "interval_low": low, "interval_high": high, "from": "literature_span",
                "run_error_estimated": None, "factor": None, "why": None}
    run_error = inputs.get("run_numerical_error")
    if run_error is not None and not (_positive(run_error) or run_error == 0):
        return _none("a run's numerical error is a number not below zero")
    how = inputs.get("run_error_from")
    if run_error is not None and how not in FACTORS:
        return _none("a run's numerical error was handed without saying how it was estimated (run_error_from: %s)"
                     % ", ".join(sorted(FACTORS)))
    exact = inputs.get("exact")
    if exact not in (None, True, False):
        return _none("exact is true, false or null")
    if exact is True:
        if run_error is None:
            return _given({"tolerance": None, "from": None, "run_error_estimated": False, "factor": None,
                           "why": "the reference is exact, so no printed digit gives a tolerance, and the run's numerical "
                                  "error was not estimated"})
        factor = FACTORS[how]
        return _given({"tolerance": factor * float(run_error), "from": "run_numerical_error", "run_error_estimated": True,
                       "factor": factor, "why": None})
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
        return _given({"tolerance": half, "from": "last_printed_digit", "run_error_estimated": False, "factor": None,
                       "why": "the run's numerical error was not estimated, so half the last printed digit alone applies"})
    factor = FACTORS[how]
    weighed = factor * float(run_error)
    if weighed > half:
        return _given({"tolerance": weighed, "from": "run_numerical_error", "run_error_estimated": True, "factor": factor,
                       "why": None})
    return _given({"tolerance": half, "from": "last_printed_digit", "run_error_estimated": True, "factor": factor, "why": None})
