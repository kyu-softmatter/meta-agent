"""A row, the person's, for each input of a library skill a request names that nothing in its bundle gives (template v42;
meta_agent/tasks/034, rheo-5 of meta_agent/failures.jsonl: oldroyd_b_startup_channel_velocity@v1's `terms` had no row, so
neither the hub nor the person was asked for it, and the agent's comparison was held).

An input of a skill the request names is given when:
- a parameter row of the bundle bears its name, or names it under `gives_inputs`, a list of {skill, input} (a row the
  request names otherwise, such as a fit's window, that it means for the skill's input);
- a tool of the bundle returns an output field of its name;
- a hand-over the bundle writes declares it: a field of the tool results its record is read off (`record_inputs`), or
  one of a step's declared inputs (`steps`);
- a decision or a scientific task's analysis hands it to that skill, as the data or by a row.

The skills the template's own scripts run (its common set, the agreement, the tolerance rule, the span, the interval, the
order, the unit skill and those the run's own error is taken by) are handed their inputs by those scripts, and are not
judged here. Every other input gets a row with no value: its unit is the manifest's, its note names the skill and the
input and says what the input means, and `chosen_by` stays unset, so that a hub's `members` lists it as one the person
gives. Nothing here chooses a value. The build is refused where the manifest's unit is not a unit of contracts/units.json,
or where two skills take one input name in units of different dimensions, since one row cannot be both.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
UNITS = os.path.join(REPO, "contracts", "units.json")

FROM_VERSION = 42


def machinery(template_meta):
    """The refs the template's own scripts hand their inputs to."""
    m = template_meta or {}
    out = set(m.get("common_skills") or [])
    for k in ("agreement_skill", "interval_skill", "span_skill", "order_skill", "unit_skill"):
        if m.get(k):
            out.add(m[k])
    if isinstance(m.get("tolerance_rule"), dict) and m["tolerance_rule"].get("skill"):
        out.add(m["tolerance_rule"]["skill"])
    out |= set((m.get("run_error_from") or {}).keys())
    return out


def declared(handover_decl, decisions, scientific_tasks):
    """{(skill ref, input)} that a hand-over, a decision or an analysis declares."""
    out = set()
    for g in (handover_decl or {}).get("gives") or []:
        for inp in (g.get("record_inputs") or {}):
            out.add((g.get("skill"), inp))
        for st in g.get("steps") or []:
            for inp in (st.get("inputs") or {}):
                out.add((st.get("skill"), inp))
    handed = list(decisions or [])
    handed += [t.get("analysis") for t in scientific_tasks or [] if isinstance(t, dict) and isinstance(t.get("analysis"), dict)]
    for d in handed:
        if (d.get("data") or {}).get("input"):
            out.add((d.get("skill"), d["data"]["input"]))
        for inp in (d.get("rows") or {}):
            out.add((d.get("skill"), inp))
    return out


def _dim(units, u):
    return {k: v for k, v in ((units.get(u) or {}).get("dim") or {}).items() if v}


def rows_for(named, skills, rows, contracts, handover_decl=None, decisions=None, scientific_tasks=None, template_meta=None):
    """(new rows, faults): a row with no value for each input of a named skill nothing gives, and what refuses the build.
    `named` is the refs the request names, in its order; `skills` the library rows the bundle carries (ref, inputs);
    `rows` the bundle's parameter rows; `contracts` its tool contracts by name."""
    with open(UNITS, encoding="utf-8") as f:
        units = json.load(f)["units"]
    by_ref = {s["ref"]: s for s in skills or []}
    skip = machinery(template_meta)
    have = {r.get("name") for r in rows or [] if isinstance(r, dict)}
    faults = []
    row_gives = set()
    for r in rows or []:
        for g in (r.get("gives_inputs") or []) if isinstance(r, dict) else []:
            sk = by_ref.get((g or {}).get("skill"))
            if sk is None or (g or {}).get("input") not in {i.get("name") for i in sk.get("inputs") or []}:
                faults.append("the row %s gives the input %r of %r, which is no input of a skill the bundle carries" % (
                    r.get("name"), (g or {}).get("input"), (g or {}).get("skill")))
                continue
            row_gives.add((g["skill"], g["input"]))
    fields = set()
    for c in (contracts or {}).values():
        fields |= set((((c or {}).get("outputs") or {}).get("properties") or {}).keys())
    said = declared(handover_decl, decisions, scientific_tasks)
    new, order = {}, []
    for ref in named or []:
        if ref in skip or ref not in by_ref:
            continue
        for inp in by_ref[ref].get("inputs") or []:
            name, unit = inp.get("name"), inp.get("unit")
            if name in have or name in fields or (ref, name) in said or (ref, name) in row_gives:
                continue
            if not isinstance(units.get(unit), dict):
                faults.append("the input %s of %s is in %r, which contracts/units.json does not hold, so no row can be "
                              "written for it; nothing in the bundle gives it" % (name, ref, unit))
                continue
            if name in new:
                if _dim(units, new[name]["unit"]) != _dim(units, unit):
                    faults.append("the input %s is taken by %s in %s and by %s in %s, units of different dimensions; one "
                                  "row cannot give both" % (name, new[name]["for_skill_inputs"][0]["skill"],
                                                            new[name]["unit"], ref, unit))
                    continue
                new[name]["for_skill_inputs"].append({"skill": ref, "input": name, "meaning": inp.get("meaning")})
                continue
            order.append(name)
            new[name] = {"name": name, "value": None, "unit": unit,
                         "for_skill_inputs": [{"skill": ref, "input": name, "meaning": inp.get("meaning")}]}
    out = []
    for name in order:
        r = new[name]
        r["note"] = ("the person gives it: nothing in the bundle gives the input %s of %s (%s), so the build gave it this "
                     "row with no value (template v42)" % (
                         name, ", ".join(x["skill"] for x in r["for_skill_inputs"]), r["for_skill_inputs"][0]["meaning"]))
        out.append(r)
    return out, faults
