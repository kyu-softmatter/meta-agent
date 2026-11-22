"""A value taken from one registered unit to another through the registry's entries it is handed (version 2).

The registry is multiplicative: a unit's si_factor takes a value in it to SI base units and its dim is its dimension
(contracts/units.json, the registry's note). So a value in unit F is in unit T after multiplication by
si_factor(F) / si_factor(T), and only when F and T have the same dimension. A unit with no si_factor, an engine's own
unit, has none until a scale says which registered unit it stands for. On the side the value goes to, that scale is
handed as stands_for, as in version 1; on the side it comes from (a value an engine computed in its own unit, v2), as
from_stands_for. The factor is then taken from and to the units the scales stand for. Whether a scale was confirmed by
a person is not this skill's to judge: its caller hands a scale only when it may. The skill opens nothing: its caller
reads the registry and hands the entries.
"""


def _dim(entry):
    return {k: v for k, v in (entry.get("dim") or {}).items() if v}


def _not(why, value):
    return {"state": "not_convertible", "why": why, "factor": None, "converted": None, "value": value}


def _side(entry, scale):
    """(the entry whose si_factor counts, None) or (None, why)."""
    if entry.get("si_factor") is None:
        if not isinstance(scale, dict) or scale.get("si_factor") is None:
            return None, "%s has no si_factor and no scale says which registered unit it stands for" % entry["name"]
        if _dim(scale) != _dim(entry):
            return None, "the scale's unit %s is not of %s's dimension" % (scale.get("name"), entry["name"])
        return scale, None
    if scale is not None:
        return None, "%s has its own si_factor and takes no scale" % entry["name"]
    return entry, None


def analysis(inputs):
    value, fu, tu = inputs["value"], inputs["from_unit"], inputs["to_unit"]
    su, fs = inputs["stands_for"], inputs.get("from_stands_for")
    for label, e in (("from_unit", fu), ("to_unit", tu)):
        if not isinstance(e, dict) or not e.get("name"):
            return _not("%s is not a registry entry with a name" % label, value)
    source, why = _side(fu, fs)
    if source is None:
        return _not(why, value)
    target, why = _side(tu, su)
    if target is None:
        return _not(why, value)
    if _dim(fu) != _dim(tu):
        return _not("%s and %s are not of one dimension" % (fu["name"], tu["name"]), value)
    factor = source["si_factor"] / target["si_factor"]
    return {"state": "converted", "factor": factor, "converted": value * factor, "value": value}
