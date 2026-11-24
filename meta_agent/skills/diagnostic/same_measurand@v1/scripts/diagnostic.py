"""Whether a measured value and a reference value are values of one measurand, as far as the conditions each states
and the way each run ended show it (meta_agent/failures.jsonl dft-19)."""
import math
from decimal import Decimal, InvalidOperation


def _as_decimal(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, float):
        return Decimal(repr(v)) if math.isfinite(v) else None
    if isinstance(v, str):
        try:
            d = Decimal(v.strip())
        except InvalidOperation:
            return None
        return d if d.is_finite() else None
    return None


def same_value(a, b):
    """Two stated values are the same where they are equal as numbers (a text that reads as a number is one), and
    otherwise where they are equal as written, a text's surrounding spaces aside."""
    da, db = _as_decimal(a), _as_decimal(b)
    if da is not None and db is not None:
        return da == db
    if isinstance(a, str) and isinstance(b, str):
        return a.strip() == b.strip()
    return a == b


def diagnostic(inputs):
    mc = inputs["measured_conditions"]
    rc = inputs["reference_conditions"]
    if not isinstance(mc, dict) or not isinstance(rc, dict):
        raise ValueError("measured_conditions and reference_conditions are objects of stated conditions")
    accept = inputs["accept_ends"]
    if accept is not None and not isinstance(accept, list):
        raise ValueError("accept_ends is a list of ends or null")
    ends = {"measured": inputs["measured_end"], "reference": inputs["reference_end"]}

    differing = sorted(k for k in mc if k in rc and not same_value(mc[k], rc[k]))
    one_sided = sorted(set(mc) ^ set(rc))
    not_accepted = sorted(side for side, end in ends.items()
                          if end is not None and accept is not None and end not in accept)
    unjudged = sorted(side for side, end in ends.items() if end is not None and accept is None)

    why = []
    if differing:
        why.append("the two state different values of %s" % ", ".join(differing))
    if not_accepted:
        why.append("%s ended %s, which is not among the ends handed" % (
            " and ".join(not_accepted), " and ".join(repr(ends[s]) for s in not_accepted)))
    if differing or not_accepted:
        state = "different"
    else:
        if one_sided:
            why.append("%s stated by one of the two only" % ", ".join(one_sided))
        if unjudged:
            why.append("%s states how its run ended and no accepted end was handed" % " and ".join(unjudged))
        if accept is not None and ends["measured"] is None:
            why.append("ends were handed and the measured run states none")
        state = "undecided" if why else "same"
    return {"state": state, "differing": differing, "one_sided": one_sided, "ends_not_accepted": not_accepted,
            "why": "; ".join(why) or None}
