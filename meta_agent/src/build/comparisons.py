"""Two kinds of scientific task the template's checker takes from v34 on (tasks/032; the person, 2026-11-20).

- A held comparison, one that cannot be judged yet: held {reason, needs}, expected not_run, naming no reference
  function ('Held item, shown pending (Recommended)'; bundle check B5 prints it pending).
- A comparison in the reference's printed unit, where the reference is printed in another unit than the measured
  quantity: reference.unit names the printed unit and measure.unit the measured quantity's; the bundle's checker
  converts the measured values into the printed unit through the unit skill and the registry the bundle carries
  ('Compare in its printed unit (Recommended)'; check 12).

`problems` says what keeps such tasks from running in a bundle of a template, before anything is written; `needs_units`
says whether the bundle must carry the registry and the unit skill for them. Nothing here converts a value.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
UNITS = os.path.join(REPO, "contracts", "units.json")


def _version(template_meta):
    try:
        return int(str(template_meta.get("version") or "v0")[1:])
    except ValueError:
        return 0


def is_held(task):
    return isinstance(task, dict) and "held" in task


def printed_units(task):
    """(measured unit, printed unit) of a task compared in its reference's printed unit, or None."""
    if not isinstance(task, dict) or is_held(task):
        return None
    ref_unit = (task.get("reference") or {}).get("unit") if isinstance(task.get("reference"), dict) else None
    measured = (task.get("measure") or {}).get("unit")
    if ref_unit and measured and ref_unit != measured:
        return measured, ref_unit
    return None


def needs_units(tasks):
    return any(printed_units(t) for t in tasks or [])


def problems(tasks, tool_names, template_meta):
    with open(UNITS, "r", encoding="utf-8") as f:
        units = json.load(f)["units"]
    v = _version(template_meta)
    out = []
    for t in tasks or []:
        tid = t.get("id")
        if is_held(t):
            h = t["held"]
            if v < 34:
                out.append("%s: a held comparison needs template v34 or later; %s reports none" % (tid, template_meta.get("version")))
            if not isinstance(h, dict) or not all(isinstance(h.get(k), str) and h[k].strip() for k in ("reason", "needs")):
                out.append("%s: a held comparison says why it is held (held.reason) and what it needs to run (held.needs)" % tid)
            if t.get("expected_verdict") != "not_run":
                out.append("%s: a held comparison is expected not_run, not %r" % (tid, t.get("expected_verdict")))
            if (t.get("measure") or {}).get("reference_function"):
                out.append("%s: a held comparison names no reference function" % tid)
            if (t.get("call") or {}).get("tool") not in tool_names:
                out.append("%s: a held comparison's call names a tool of this bundle" % tid)
            continue
        ref_unit = (t.get("reference") or {}).get("unit") if isinstance(t.get("reference"), dict) else None
        if not ref_unit:
            continue
        measured = (t.get("measure") or {}).get("unit")
        if v < 34:
            out.append("%s: a reference with a printed unit needs template v34 or later" % tid)
        ru, mu = units.get(ref_unit), units.get(measured)
        if not isinstance(ru, dict) or ru.get("si_factor") is None:
            out.append("%s: the reference's unit %r is not a registered unit with an si_factor" % (tid, ref_unit))
        if not measured:
            out.append("%s: the reference names its printed unit and the task's measure.unit does not name the measured "
                       "quantity's, so nothing says what to convert from" % tid)
        elif not isinstance(mu, dict) or mu.get("si_factor") is None:
            out.append("%s: the measured unit %r is not a registered unit with an si_factor" % (tid, measured))
        elif isinstance(ru, dict) and {k: x for k, x in (ru.get("dim") or {}).items() if x} != \
                {k: x for k, x in (mu.get("dim") or {}).items() if x}:
            out.append("%s: %s and %s are not of one dimension" % (tid, measured, ref_unit))
        stated = (t.get("measure") or {}).get("stated")
        if not isinstance(stated, dict) or len(stated) != 1:
            out.append("%s: a comparison in a printed unit states one field" % tid)
    return out
