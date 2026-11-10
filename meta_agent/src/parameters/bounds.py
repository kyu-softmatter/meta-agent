"""The bounds pass: a sheet draft and a binding file in, a parameter_sheet with bounds and intervals out.

The model chooses and binds; code computes. A draft holds the rows (the inputs with their sources, the
parameters to be bounded with no value) and the tool; a binding file says, for every bound skill that
applies, `used` with the row each input is bound to, or `not_applied` with the reason. Neither file holds
a bound: apply() runs each used skill through the runner it is handed, on the values of the rows named,
and writes what came back as a `computed` bound with its basis. Nothing in this path lets a model type a
bound's value, a grade or a point.

    draft    {id, rid, tool, tool_ref: {kind, registry_id}, rows: [...], objectives?, search_tiers_used?, note?}
             an input row: name, value, unit, source, value_kind, uncertainty?, ...   (its grade is derived here)
             a row to be bounded: name, unit, value null, and whatever else the row carries
    binding  {skills: [{skill: "<id>@v<n>", verdict: used | not_applied, why, inputs: {<input>: <row name>}}]}
             run in this order, so a value skill is named before a bound that rests on the row it gives

What apply() does, in order: derives every input row's grade from contracts/grades.json; refuses a binding
that leaves an applicable bound skill out, gives no reason for a `not_applied`, or binds an input to a row
that is missing, has no value or has another unit (each a named error, a subclass of BindingError); runs
each used skill; propagates the input rows' uncertainties to first order (one run either side of each
input that states one) and, when there is an uncertainty, rounds the bound to the decimal place of the
uncertainty's second significant figure and states the uncertainty, which is then the tolerance of the
recomputation; grades the bound the worst of E4 and its input rows; takes the highest floor and the
lowest ceiling as the interval and names the two skills; on an empty interval writes no point and a
`tradeoff` naming the two bounds that collide. A row's value stays null unless a `value` skill gives it:
the choice inside an interval is tasks/011's. A row a `value` skill gives says what kind of value it is,
as the skill's manifest does (`value_kind`, `computed` when it says nothing): a correlation's row is
`correlation:<id>@v<n>` with value_kind `correlation`, so that a sheet keeps which value is a correlation. Before it returns the sheet it asks contracts/tools/sheets.py
what checks 4 and 19 would say, and a sheet with anything said about it is not returned.

This stage imports no sibling stage (plan.md 7): the caller hands in the library's rows for the bound
skills (src/skills/catalogue) and a function that runs one skill (src/skills/runner). The command is the
Designer's: python -m meta_agent.src.designer --sheet <request folder> --seat <seat>.
"""
import copy
import json
import math

from .. import cards
from . import GRADES_PATH, rules

NUMBER = (int, float)


class BindingError(ValueError):
    """The binding or the draft cannot be turned into a sheet; `code` names why."""
    code = "binding"


class UnknownSkill(BindingError):
    code = "unknown_skill"


class NotConsidered(BindingError):
    code = "not_considered"


class NoReason(BindingError):
    code = "no_reason"


class InputNotBound(BindingError):
    code = "input_not_bound"


class MissingRow(BindingError):
    code = "missing_row"


class NoValue(BindingError):
    code = "no_value"


class WrongUnit(BindingError):
    code = "wrong_unit"


class NoGrade(BindingError):
    code = "no_grade"


class SafetyRow(BindingError):
    code = "safety_row"


class SkillFailed(BindingError):
    code = "skill_failed"


class SheetRefused(BindingError):
    code = "sheet_refused"


def grade_table(path=GRADES_PATH):
    table = {}
    for rule in cards.load_json(path)["rules"]:
        for vk in rule["value_kinds"]:
            table[(rule["source_kind"], vk)] = rule["grade"]
    return table


def is_number(v):
    return isinstance(v, NUMBER) and not isinstance(v, bool) and math.isfinite(v)


def applicable(skills, row_names, tool_ref):
    """The bound skills that apply to a sheet, by the rule check 19 reads: a parameter of the skill is a row
    of the sheet, and the skill names no tool or names the sheet's."""
    tool = (tool_ref or {}).get("registry_id")
    out = []
    for r in skills:
        applies = r.get("applies_to") or {}
        tools = list(applies.get("instruments") or []) + list(applies.get("engines") or [])
        if r["kind"] == "bound" and set(applies.get("parameters") or []) & set(row_names) and (not tools or tool in tools):
            out.append(r)
    return out


def listing(skills, draft):
    """What a model reads to write the binding: each applicable skill, its side, its parameter and its inputs."""
    names = [r.get("name") for r in draft.get("rows") or []]
    lines = []
    for r in applicable(skills, names, draft.get("tool_ref")):
        lines.append("%s  [%s of %s]" % (r["ref"], r.get("side"), r.get("parameter")))
        lines.append("    %s" % r["summary"])
        lines.append("    inputs: %s" % ", ".join("%s (%s)" % (i["name"], i["unit"]) for i in r["inputs"]))
    lines.append("%d skill(s) apply to %s" % (len(lines) // 3, (draft.get("tool_ref") or {}).get("registry_id") or "this sheet"))
    return "\n".join(lines)


def _round_to_uncertainty(value, sigma):
    """(value, uncertainty) with the uncertainty at two significant figures, rounded up, and the value at
    the same decimal place; the rounding is never larger than the uncertainty it is stated with."""
    place = math.floor(math.log10(sigma)) - 1
    unit = 10.0 ** place
    u = math.ceil(sigma / unit - 1e-9) * unit
    digits = -place
    return round(value, digits), round(u, digits)


def _run(run, ref, inputs, output):
    record = run(ref, inputs)
    if record.get("verdict") != "ran":
        raise SkillFailed("%s did not run on %s: %s" % (ref, json.dumps(inputs, sort_keys=True), record.get("why")))
    value = (record.get("outputs") or {}).get(output)
    if not is_number(value):
        raise SkillFailed("%s returned %r for %s, not a number" % (ref, value, output))
    return value


def _compute(run, skill, bound_rows):
    """One skill on the rows it is bound to: (value, uncertainty or None)."""
    output = skill["outputs"][0]["name"]
    inputs = {name: row["value"] for name, row in bound_rows.items()}
    value = _run(run, skill["ref"], inputs, output)
    variance = 0.0
    for name, row in sorted(bound_rows.items()):
        u = row.get("uncertainty")
        if is_number(u) and u > 0:
            hi = _run(run, skill["ref"], dict(inputs, **{name: row["value"] + u}), output)
            lo = _run(run, skill["ref"], dict(inputs, **{name: row["value"] - u}), output)
            variance += ((hi - lo) / 2.0) ** 2
    if variance <= 0.0:
        return value, None
    return _round_to_uncertainty(value, math.sqrt(variance))


def apply(draft, binding, skills, run, seat, now=None, sheet_path=None, tree=None):
    """The parameter_sheet card for a draft and a binding. `skills` are the library's rows for its bound
    skills, `run(ref, inputs)` runs one and returns the runner's record, and `sheet_path` is where the card
    will lie (the library checks 4 and 19 read is the nearest skills/ at or above it)."""
    rows = copy.deepcopy(draft.get("rows") or [])
    names = [r.get("name") for r in rows]
    twice = sorted({n for n in names if names.count(n) > 1})
    if twice:
        raise BindingError("the draft names %s more than once" % ", ".join(twice))
    by_name = {r["name"]: r for r in rows}
    grades = grade_table()
    for r in rows:
        if r.get("value") is None:
            continue
        kind = str(r.get("source") or "").split(":", 1)[0]
        if kind in ("computed", "correlation"):
            raise BindingError("row %s: a %s value is written by a value skill, not by the draft" % (r["name"], kind))
        derived = grades.get((kind, r.get("value_kind")))
        if derived is None:
            raise NoGrade("row %s: no grade follows from source %r and value_kind %r (contracts/grades.json)"
                          % (r["name"], r.get("source"), r.get("value_kind")))
        if r.get("grade") not in (None, derived):
            raise NoGrade("row %s: the draft states grade %s and %s follows from its source; a grade is derived, never stated"
                          % (r["name"], r.get("grade"), derived))
        r["grade"] = derived

    library = {r["ref"]: r for r in skills}
    entries = list(binding.get("skills") or [])
    listed = [e.get("skill") for e in entries]
    twice = sorted({s for s in listed if listed.count(s) > 1})
    if twice:
        raise BindingError("the binding lists %s more than once" % ", ".join(twice))
    for e in entries:
        if e.get("skill") not in library:
            raise UnknownSkill("the binding names %s, which is not a bound skill of the library" % e.get("skill"))
        if e.get("verdict") not in ("used", "not_applied"):
            raise BindingError("%s: verdict %r is not used or not_applied" % (e["skill"], e.get("verdict")))
        if e["verdict"] == "not_applied" and not str(e.get("why") or "").strip():
            raise NoReason("%s is not applied and the binding gives no reason" % e["skill"])
    for r in applicable(skills, names, draft.get("tool_ref")):
        if r["ref"] not in listed:
            raise NotConsidered("%s applies to this sheet (%s) and the binding does not name it: a skill is used, "
                                "or is not applied with a reason, never left out" % (r["ref"], r.get("parameter")))

    for e in entries:
        if e["verdict"] != "used":
            continue
        skill = library[e["skill"]]
        target = by_name.get(skill.get("parameter"))
        if target is None:
            raise MissingRow("%s bounds %s, and the draft has no row of that name" % (skill["ref"], skill.get("parameter")))
        out_unit = skill["outputs"][0]["unit"]
        if target.get("unit") != out_unit:
            raise WrongUnit("%s gives %s and the row %s is in %s" % (skill["ref"], out_unit, target["name"], target.get("unit")))
        bound_to = dict(e.get("inputs") or {})
        wanted = [i["name"] for i in skill["inputs"]]
        extra = sorted(set(bound_to) - set(wanted))
        if extra:
            raise InputNotBound("%s does not take %s" % (skill["ref"], ", ".join(extra)))
        bound_rows = {}
        for spec in skill["inputs"]:
            row_name = bound_to.get(spec["name"])
            if row_name is None:
                raise InputNotBound("%s: input %s is bound to no row" % (skill["ref"], spec["name"]))
            row = by_name.get(row_name)
            if row is None:
                raise MissingRow("%s: input %s is bound to %s, which is not a row of the draft" % (skill["ref"], spec["name"], row_name))
            if not is_number(row.get("value")):
                raise NoValue("%s: input %s is bound to %s, which has no value" % (skill["ref"], spec["name"], row_name))
            if row.get("unit") != spec["unit"]:
                raise WrongUnit("%s: input %s is in %s and the row %s is in %s"
                                % (skill["ref"], spec["name"], spec["unit"], row_name, row.get("unit")))
            bound_rows[spec["name"]] = row
        value, uncertainty = _compute(run, skill, bound_rows)
        basis = {"skill": skill["ref"], "inputs": {name: row["name"] for name, row in bound_rows.items()}}
        grade = rules.computed_grade({"rows": rows}, basis)
        if grade is None:
            raise NoGrade("%s: an input row has no grade" % skill["ref"])
        if skill.get("side") == "value":
            if target.get("safety_relevant"):
                raise SafetyRow("%s would write a value on %s, a safety-relevant row: its value is a person's" % (skill["ref"], target["name"]))
            if target.get("value") is not None:
                raise BindingError("%s would write over the value the draft gives %s" % (skill["ref"], target["name"]))
            kind = skill.get("value_kind") or "computed"
            target.update(value=value, source="%s:%s" % (kind, skill["ref"]), grade=grade, value_kind=kind,
                          uncertainty=uncertainty, basis=basis)
        else:
            target.setdefault("bounds", []).append({
                "side": skill["side"], "value": value, "unit": out_unit, "source": "computed:%s" % skill["ref"],
                "grade": grade, "value_kind": "computed", "uncertainty": uncertainty, "basis": basis})

    for r in rows:
        bounds = r.get("bounds") or []
        if not bounds:
            continue
        floors = [b for b in bounds if b["side"] == "min"]
        ceilings = [b for b in bounds if b["side"] == "max"]
        lo = max(floors, key=lambda b: b["value"]) if floors else None
        hi = min(ceilings, key=lambda b: b["value"]) if ceilings else None
        r["interval"] = {"min": lo["value"] if lo else None, "max": hi["value"] if hi else None, "unit": r.get("unit"),
                         "min_from": lo["basis"]["skill"] if lo else None, "max_from": hi["basis"]["skill"] if hi else None}
        if lo is not None and hi is not None and lo["value"] > hi["value"]:
            if r.get("value") is not None:
                raise BindingError("row %s carries a value and its interval is empty (%s above %s)"
                                   % (r["name"], lo["basis"]["skill"], hi["basis"]["skill"]))
            r["recommendation"] = {
                "mode": "tradeoff", "point": None, "chosen_by": "human",
                "reason": "the interval is empty: %s gives a floor of %r %s, above the ceiling of %r %s from %s. No point is "
                          "written; which of the two gives way, or which input row is replaced, is the person's choice"
                          % (lo["basis"]["skill"], lo["value"], r.get("unit"), hi["value"], r.get("unit"), hi["basis"]["skill"])}

    sheet = cards.skeleton("parameter_sheet", draft["id"], seat, cards.now_iso(now), rid=draft.get("rid"))
    if draft.get("note"):
        sheet["note"] = draft["note"]
    if draft.get("tool"):
        sheet["tool"] = draft["tool"]
    sheet["search_tiers_used"] = list(draft.get("search_tiers_used") or [])
    sheet["rows"] = rows
    if draft.get("tool_ref"):
        sheet["tool_ref"] = dict(draft["tool_ref"])
    sheet["skills_considered"] = [{"skill": e["skill"], "verdict": e["verdict"], "why": str(e.get("why") or "")} for e in entries]
    if draft.get("objectives"):
        sheet["objectives"] = copy.deepcopy(draft["objectives"])
    if sheet_path is not None:
        said = ["check 4: " + m for m in rules.check4(sheet)] + ["check 19: " + m for m in rules.check19(sheet, sheet_path, tree)]
        if said:
            raise SheetRefused("the sheet would not pass: " + "; ".join(said))
    return sheet


SAME_BUT = ("revision", "supersedes", "created_at", "author")


def same_sheet(a, b):
    strip = lambda d: {k: v for k, v in d.items() if k not in SAME_BUT}
    return strip(a) == strip(b)
