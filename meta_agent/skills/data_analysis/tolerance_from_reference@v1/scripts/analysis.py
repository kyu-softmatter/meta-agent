"""A scientific task's tolerance by the person's standing rule: the reference's stated uncertainty where the source
states one, otherwise half a unit in the last digit the reference prints."""
from decimal import Decimal, InvalidOperation


def _none(why):
    return {"tolerance": None, "from": None, "why": why}


def analysis(inputs):
    stated = inputs.get("stated_uncertainty")
    if stated is not None:
        if isinstance(stated, bool) or not isinstance(stated, (int, float)) or stated <= 0:
            return _none("a stated uncertainty is a positive number")
        return {"tolerance": float(stated), "from": "stated_uncertainty", "why": None}
    printed = inputs.get("printed")
    if not isinstance(printed, str) or not printed.strip():
        return _none("neither a stated uncertainty nor the reference as printed was handed")
    try:
        d = Decimal(printed.strip())
    except InvalidOperation:
        return _none("the reference as printed is not a number: %r" % printed)
    if not d.is_finite():
        return _none("the reference as printed is not a finite number: %r" % printed)
    unit = Decimal(1).scaleb(d.as_tuple().exponent)
    return {"tolerance": float(unit / 2), "from": "last_printed_digit", "why": None}
