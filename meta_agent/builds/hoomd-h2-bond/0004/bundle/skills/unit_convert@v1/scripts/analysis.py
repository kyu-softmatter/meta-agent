"""A value taken from one registered unit to another through the registry's entries it is handed.

The registry is multiplicative: a unit's si_factor takes a value in it to SI base units and its dim is its dimension
(contracts/units.json, the registry's note). So a value in unit F is in unit T after multiplication by
si_factor(F) / si_factor(T), and only when F and T have the same dimension. A unit with no si_factor, an engine's own
unit, has none until a scale says which registered unit it stands for; that scale is handed as stands_for, and the
factor is then taken to the unit it stands for. Whether the scale was confirmed by a person is not this skill's to
judge: its caller hands a scale only when it may. The skill opens nothing: its caller reads the registry and hands
the entries.
"""


def _dim(entry):
    return {k: v for k, v in (entry.get("dim") or {}).items() if v}


def _not(why, value):
    return {"state": "not_convertible", "why": why, "factor": None, "converted": None, "value": value}


def analysis(inputs):
    value, fu, tu, su = inputs["value"], inputs["from_unit"], inputs["to_unit"], inputs["stands_for"]
    for label, e in (("from_unit", fu), ("to_unit", tu)):
        if not isinstance(e, dict) or not e.get("name"):
            return _not("%s is not a registry entry with a name" % label, value)
    if fu.get("si_factor") is None:
        return _not("%s has no si_factor: a value in it means nothing outside its engine" % fu["name"], value)
    target = tu
    if tu.get("si_factor") is None:
        if not isinstance(su, dict) or su.get("si_factor") is None:
            return _not("%s has no si_factor and no scale says which registered unit it stands for" % tu["name"], value)
        if _dim(su) != _dim(tu):
            return _not("the scale's unit %s is not of %s's dimension" % (su.get("name"), tu["name"]), value)
        target = su
    elif su is not None:
        return _not("%s has its own si_factor and takes no scale" % tu["name"], value)
    if _dim(fu) != _dim(target):
        return _not("%s and %s are not of one dimension" % (fu["name"], tu["name"]), value)
    factor = fu["si_factor"] / target["si_factor"]
    return {"state": "converted", "factor": factor, "converted": value * factor, "value": value}
