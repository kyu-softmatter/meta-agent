"""The span of one quantity across suitable materials, branch 3 of the person's standing rule for tolerances (the person,
2026-11-18, 'Yes, add literature span' and 'Min-max of values'; 2026-11-19, 'Yes, widen it'): the interval from the lowest
to the highest of the values, and of the edges of the error ranges, that the materials state for the quantity. No
statistic and no multiplier enters it. With fewer than two values and no stated range there is no span.

Each entry names the material it was read from and says how that material's system, quantity and engine compare with
the task's; an entry that says neither is not taken, and then no span is given at all, since which materials are
suitable is never left unsaid. Whether they are suitable is not judged here: the words are the reader's, and the span
is theirs to put to the person."""
import math


def _none(why, values=0, ranges=0):
    return {"low": None, "high": None, "lowest_from": None, "highest_from": None, "values": values, "ranges": ranges,
            "why": why}


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _words(v):
    return isinstance(v, str) and bool(v.strip())


def analysis(inputs):
    entries = inputs.get("entries")
    if not isinstance(entries, list):
        return _none("entries is a list, one entry for each value or stated range of the quantity")
    edges, values, ranges = [], 0, 0          # (the number, the material it came from), in the order handed
    for n, e in enumerate(entries, 1):
        if not isinstance(e, dict):
            return _none("entry %d is not an object" % n)
        if not _words(e.get("material")):
            return _none("entry %d names no material: every value comes from a material card" % n)
        if not _words(e.get("compares")):
            return _none("entry %d (%s) does not say how its material's system, quantity and engine compare with the "
                         "task's" % (n, e["material"]))
        has_value = e.get("value") is not None
        has_range = e.get("low") is not None or e.get("high") is not None
        if has_value == has_range:
            return _none("entry %d (%s) gives either one value or one range with a low and a high edge" % (n, e["material"]))
        if has_value:
            if not _number(e["value"]):
                return _none("entry %d (%s): the value is not a finite number" % (n, e["material"]))
            edges.append((e["value"], e["material"]))
            values += 1
        else:
            low, high = e.get("low"), e.get("high")
            if not (_number(low) and _number(high)):
                return _none("entry %d (%s): a range has a low and a high edge, both finite numbers" % (n, e["material"]))
            if low > high:
                return _none("entry %d (%s): the low edge of the range lies above its high edge" % (n, e["material"]))
            edges += [(low, e["material"]), (high, e["material"])]
            ranges += 1
    if ranges == 0 and values < 2:
        return _none("fewer than two values and no stated range: the materials give %d value%s of the quantity, so "
                     "there is no span" % (values, "" if values == 1 else "s"), values, ranges)
    lowest = min(edges, key=lambda p: p[0])     # the first entry that holds the lowest, where two hold it
    highest = max(edges, key=lambda p: p[0])
    return {"low": lowest[0], "high": highest[0], "lowest_from": lowest[1], "highest_from": highest[1],
            "values": values, "ranges": ranges, "why": None}
