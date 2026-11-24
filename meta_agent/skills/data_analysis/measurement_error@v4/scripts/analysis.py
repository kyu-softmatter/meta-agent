"""The measurement error of a measured value against a reference value, and its magnitude, taken in decimal on the
values as written, so that the error carries no digit that neither value has (v4; meta_agent/failures.jsonl dft-20)."""
import math
import re
from decimal import Decimal

WRITTEN = re.compile(r"^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$")


def _decimal(name, value):
    """A value as written: a text keeps its last digit as printed, a trailing zero included; a number is taken at the
    shortest decimal that gives it back, which is how it was written where it came from a text."""
    if isinstance(value, bool):
        raise ValueError("%s is a yes or no, not a value: %r" % (name, value))
    if isinstance(value, str):
        text = value.strip()
        if not WRITTEN.match(text):
            raise ValueError("%s is not a decimal number as written: %r" % (name, value))
        return Decimal(text)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("%s is not a finite number: %r" % (name, value))
        return Decimal(repr(value))
    raise ValueError("%s is neither a number nor a number as written: %r" % (name, value))


def _places(d):
    exp = d.as_tuple().exponent
    return -exp if exp < 0 else 0


def analysis(inputs):
    measured = _decimal("measured", inputs["measured"])
    reference = _decimal("reference", inputs["reference"])
    error = measured - reference          # decimal subtraction is exact: no binary rounding enters
    magnitude = abs(error)
    return {"error": float(error), "magnitude": float(magnitude),
            "error_written": format(error, "f"), "magnitude_written": format(magnitude, "f"),
            "places": _places(error), "places_common": min(_places(measured), _places(reference))}
