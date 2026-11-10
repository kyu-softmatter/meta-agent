#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/sheets.py -- what a parameter sheet's bounds and computed rows must be
(plan.md 14-30, 14-12; meta_agent/tasks/007).

  python contracts/tools/sheets.py check SHEET.json [TREE]     what checks 4 and 19 would say about one sheet

The maximum and the minimum of a parameter come from skills written as source code: one reason per skill,
taken by the model, run by code. A sheet therefore says, per bound and per computed row, which skill gave
the number and which rows its inputs were bound to (`basis`), and this file runs the skill again on those
rows. It also holds what follows without a model: the grade of a computed number is the worst of E4 and
its inputs; the interval is the highest floor and the lowest ceiling; an empty interval carries no point;
every bound skill that applies to a row is on the sheet as used or as not applied with a reason; a
safety-relevant row has no value but a person's.

The library a sheet rests on is the nearest `skills/` folder at or above it. Standard library only; the
skills themselves are read and run through contracts/tools/skills.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cases as case_rules    # noqa: E402  (store_for: the nearest folder of a name at or above a card)
import skills as skill_rules  # noqa: E402

GRADES = ["E1", "E2", "E3", "E4", "E5"]
FLOOR = "E4"


def worst(grades):
    known = [g for g in grades if g in GRADES]
    return max(known, key=GRADES.index) if known and len(known) == len(list(grades)) else None


def rows_by_name(sheet):
    return {r.get("name"): r for r in sheet.get("rows") or [] if isinstance(r, dict)}


def computed_grade(sheet, basis):
    """The grade of a number computed from the rows a basis names: the worst of E4 and theirs, or None when
    a named row is missing or has no grade."""
    rows = rows_by_name(sheet)
    grades = [FLOOR]
    for row_name in (basis or {}).get("inputs", {}).values():
        row = rows.get(row_name)
        if not row or row.get("grade") not in GRADES:
            return None
        grades.append(row["grade"])
    return worst(grades)


def check4(sheet):
    """A safety-relevant row has no value but a person's, and no recommended point."""
    out = []
    for i, row in enumerate(sheet.get("rows") or []):
        if not (isinstance(row, dict) and row.get("safety_relevant")):
            continue
        label = "rows[%d] (%s)" % (i, row.get("name"))
        if row.get("value") is not None and row.get("author") != "human":
            out.append("%s: a safety value is null or written by a person (author: human); this one is %r by %r"
                       % (label, row.get("value"), row.get("author")))
        rec = row.get("recommendation") or {}
        if rec.get("point") is not None or rec.get("candidates"):
            out.append("%s: a safety-relevant row gets no recommended point or candidate; bounds may be attached as information" % label)
    return out


class _Library(object):
    def __init__(self, root):
        self.root = root
        self.dirs = {os.path.basename(d): d for d in skill_rules.find_skill_dirs(root)} if root else {}
        self.manifests = {ref: skill_rules.read_manifest(d) or {} for ref, d in self.dirs.items()}
        self._clean = {}

    def clean(self, ref):
        if ref not in self._clean:
            self._clean[ref] = not skill_rules.source_problems(self.dirs[ref], self.manifests[ref])
        return self._clean[ref]


def _recompute(lib, sheet, basis, want_sides, label, unit, value, uncertainty, parameter):
    """Problems of one number against the skill its basis names; (problems, manifest or None)."""
    ref = (basis or {}).get("skill")
    if ref not in lib.dirs:
        return ["%s: the skill %s is not in the library" % (label, ref)], None
    m = lib.manifests[ref]
    out = []
    if m.get("kind") != "bound" or m.get("side") not in want_sides:
        out.append("%s: %s is a %s skill of side %s, not %s" % (label, ref, m.get("kind"), m.get("side"), " or ".join(want_sides)))
        return out, m
    if m.get("parameter") != parameter:
        out.append("%s: %s bounds %s, and the row is %s" % (label, ref, m.get("parameter"), parameter))
    outputs = m.get("outputs") or [{}]
    if unit != outputs[0].get("unit"):
        out.append("%s: unit %s, and %s gives %s" % (label, unit, ref, outputs[0].get("unit")))
    rows = rows_by_name(sheet)
    bound_to = (basis or {}).get("inputs", {})
    inputs = {}
    for spec in m.get("inputs") or []:
        row = rows.get(bound_to.get(spec["name"]))
        if row is None:
            out.append("%s: input %s of %s is bound to no row of the sheet" % (label, spec["name"], ref))
        elif not isinstance(row.get("value"), (int, float)) or isinstance(row.get("value"), bool):
            out.append("%s: input %s is bound to %s, which has no value" % (label, spec["name"], row.get("name")))
        elif row.get("unit") != spec["unit"]:
            out.append("%s: input %s is in %s and the row %s is in %s" % (label, spec["name"], spec["unit"], row.get("name"), row.get("unit")))
        else:
            inputs[spec["name"]] = row["value"]
    extra = sorted(set(bound_to) - {s["name"] for s in m.get("inputs") or []})
    if extra:
        out.append("%s: the basis binds %s, which %s does not take" % (label, ", ".join(extra), ref))
    if out:
        return out, m
    if not lib.clean(ref):
        return ["%s: %s is not clean (check 22), so it is not run" % (label, ref)], m
    got, why = skill_rules.run_once(lib.dirs[ref], inputs)
    if got is None:
        return ["%s: %s could not be run: %s" % (label, ref, why)], m
    again = got.get(outputs[0].get("name"))
    tol = uncertainty if isinstance(uncertainty, (int, float)) and uncertainty > 0 else 1e-9 * max(abs(value), abs(again or 0.0))
    if not isinstance(again, (int, float)) or abs(again - value) > tol:
        out.append("%s: stated %r, and %s on the rows it names gives %r" % (label, value, ref, again))
    return out, m


def check19(sheet, path, tree):
    """Recompute and coverage: every problem of one sheet."""
    out = []
    rows = sheet.get("rows") or []
    considered = sheet.get("skills_considered") or []
    uses = bool(considered) or any(isinstance(r, dict) and (r.get("bounds") or r.get("basis") or r.get("interval")) for r in rows)
    computed = [(i, r) for i, r in enumerate(rows) if isinstance(r, dict) and r.get("value") is not None
                and (r.get("value_kind") == "computed" or str(r.get("source") or "").startswith("computed:"))]
    for i, r in computed:
        if not r.get("basis"):
            out.append("rows[%d] (%s): a computed row names the skill and the rows it was computed from (basis)" % (i, r.get("name")))
    root = case_rules.store_for(path, tree, "skills")
    if root is None:
        if uses:
            out.append("the sheet rests on skills and no skills/ library is at or above it")
        return out
    lib = _Library(root)
    used = set()
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        label = "rows[%d] (%s)" % (i, r.get("name"))
        if r.get("basis") and r.get("value") is not None:
            probs, m = _recompute(lib, sheet, r["basis"], ("value",), label, r.get("unit"), r["value"], r.get("uncertainty"), r.get("name"))
            out.extend(probs)
            used.add(r["basis"].get("skill"))
            want = "computed:%s" % r["basis"].get("skill")
            if r.get("source") != want:
                out.append("%s: source %s, and the basis says %s" % (label, r.get("source"), want))
            grade = computed_grade(sheet, r["basis"])
            if grade and r.get("grade") != grade:
                out.append("%s: grade %s, and the worst of E4 and its inputs is %s" % (label, r.get("grade"), grade))
        bounds = r.get("bounds") or []
        for j, b in enumerate(bounds):
            blabel = "%s bounds[%d]" % (label, j)
            probs, m = _recompute(lib, sheet, b.get("basis"), (b.get("side"),), blabel, b.get("unit"), b.get("value"), b.get("uncertainty"), r.get("name"))
            out.extend(probs)
            ref = (b.get("basis") or {}).get("skill")
            used.add(ref)
            if b.get("source") != "computed:%s" % ref:
                out.append("%s: source %s, and the basis says computed:%s" % (blabel, b.get("source"), ref))
            if b.get("unit") != r.get("unit"):
                out.append("%s: unit %s, and the row is in %s" % (blabel, b.get("unit"), r.get("unit")))
            grade = computed_grade(sheet, b.get("basis"))
            if grade is None:
                out.append("%s: an input row is missing or has no grade" % blabel)
            elif b.get("grade") != grade:
                out.append("%s: grade %s, and the worst of E4 and its inputs is %s" % (blabel, b.get("grade"), grade))
        interval = r.get("interval")
        if bounds or interval:
            floors = [b for b in bounds if b.get("side") == "min" and isinstance(b.get("value"), (int, float))]
            ceilings = [b for b in bounds if b.get("side") == "max" and isinstance(b.get("value"), (int, float))]
            lo = max(floors, key=lambda b: b["value"]) if floors else None
            hi = min(ceilings, key=lambda b: b["value"]) if ceilings else None
            if not isinstance(interval, dict):
                out.append("%s: bounds without an interval" % label)
            else:
                for end, b in (("min", lo), ("max", hi)):
                    want_v = b["value"] if b else None
                    want_f = b["basis"]["skill"] if b else None
                    if interval.get(end) != want_v or interval.get(end + "_from") != want_f:
                        out.append("%s: interval.%s is %r from %s, and the bounds give %r from %s (the highest floor, the lowest ceiling)"
                                   % (label, end, interval.get(end), interval.get(end + "_from"), want_v, want_f))
                if interval.get("unit") != r.get("unit"):
                    out.append("%s: the interval is in %s and the row in %s" % (label, interval.get("unit"), r.get("unit")))
            empty = lo is not None and hi is not None and lo["value"] > hi["value"]
            rec = r.get("recommendation") or {}
            if empty:
                if r.get("value") is not None or rec.get("point") is not None or rec.get("candidates"):
                    out.append("%s: the interval is empty (%s gives a floor of %r above %s's ceiling of %r) and the row carries a point; "
                               "an empty interval is a tradeoff or a gap, never a silent choice"
                               % (label, lo["basis"]["skill"], lo["value"], hi["basis"]["skill"], hi["value"]))
                if rec and rec.get("mode") not in ("tradeoff", "gap"):
                    out.append("%s: the interval is empty and the recommendation's mode is %s, not tradeoff or gap" % (label, rec.get("mode")))
            else:
                for what, v in (("value", r.get("value")), ("recommendation.point", rec.get("point"))):
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and \
                            ((lo is not None and v < lo["value"]) or (hi is not None and v > hi["value"])):
                        out.append("%s: %s %r lies outside the interval the bounds give" % (label, what, v))
    # coverage: what the model chose, and what it left out, is on the sheet
    tool = (sheet.get("tool_ref") or {}).get("registry_id")
    names = {r.get("name") for r in rows if isinstance(r, dict)}
    listed = {}
    for k, entry in enumerate(considered):
        ref = entry.get("skill")
        if ref in listed:
            out.append("skills_considered[%d]: %s is listed twice" % (k, ref))
        listed[ref] = entry
        if ref not in lib.dirs:
            out.append("skills_considered[%d]: %s is not in the library" % (k, ref))
        elif entry.get("verdict") == "used" and ref not in used:
            out.append("skills_considered[%d]: %s is said to be used and no bound or computed row rests on it" % (k, ref))
        elif entry.get("verdict") == "not_applied":
            if ref in used:
                out.append("skills_considered[%d]: %s is said not to apply and a number rests on it" % (k, ref))
            if not str(entry.get("why") or "").strip():
                out.append("skills_considered[%d]: %s is not applied and no reason is given" % (k, ref))
    for ref in sorted(r for r in used if r):
        if ref in lib.dirs and (ref not in listed or listed[ref].get("verdict") != "used"):
            out.append("%s gave a number of this sheet and is not in skills_considered as used" % ref)
    for ref, m in sorted(lib.manifests.items()):
        if m.get("kind") != "bound" or m.get("side") not in ("min", "max"):
            continue
        applies = m.get("applies_to") or {}
        tools = list(applies.get("instruments") or []) + list(applies.get("engines") or [])
        if not (set(applies.get("parameters") or []) & names) or (tools and tool not in tools):
            continue
        if ref not in listed:
            out.append("%s applies to this sheet (%s, %s) and is not in skills_considered: a skill is used or is not applied with a reason, never left out"
                       % (ref, ", ".join(sorted(set(applies.get("parameters") or []) & names)), tool or "any tool"))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) not in (2, 3) or argv[0] != "check":
        print(__doc__)
        return 2
    path = os.path.abspath(argv[1])
    tree = os.path.abspath(argv[2]) if len(argv) == 3 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(path, "r", encoding="utf-8") as f:
        sheet = json.load(f)
    found = ["check 4: " + m for m in check4(sheet)] + ["check 19: " + m for m in check19(sheet, path, tree)]
    for m in found:
        print(m)
    if not found:
        print("nothing to say")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
