"""What a build gives to another agent and takes from one (template v32; meta_agent/tasks/031).

The request declares it on its parameter rows, so that no card of the design role changes for it:

- a row the agent hands over carries `handover.gives`: the thread, the receiving agent and its build, the library skill
  whose record the value is read off and the output it is, the tool output fields the skill's inputs are taken from
  (`record_inputs`), from each of several results or from one (`record_inputs_from`: each_result, the default, or
  one_result), the tool whose results those are (`record_tool`, template v34: the build copies what its contract says
  of each field into the declaration, and the card's definition names it), the field of a tool result that states the conditions (`conditions_field`), the conditions the
  request states in words (`conditions`), the skill states a hand-over is written on (`accept_states`) and what the
  values are for (`what`). The row's unit is the unit the value is handed in, and it has an si_factor: an engine's own
  unit means nothing outside its engine (check 25). The grade is derived here from contracts/grades.json for a
  computed value, never stated by the request.
- a row the agent takes carries `handover.takes`: the value's name in the hand-over, the thread and the agent it comes
  from. The row's unit is what the value is converted into.
- an engine scale is a row that carries `engine_scale` and no value: which registered unit one of the engine's own
  units stands for, its state and who confirmed it, as the request records the person's word. A scale of a composite
  unit names the scales it `rests_on`; it is confirmed only where each of them is, and the parts of the unit it
  stands for are the units they stand for. Scale rows go into envelope/handovers.json, not into the parameter rows.

`declaration` returns what the build writes (envelope/handovers.json, the rows of envelope/parameters.json, whether the
bundle needs the unit skill, the Hand-overs section) or raises ValueError naming every fault, before anything is
written. Nothing here converts a value or chooses a scale.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
UNITS = os.path.join(REPO, "contracts", "units.json")
GRADES = os.path.join(REPO, "contracts", "grades.json")
GIVE_KEYS = ("thread", "to_agent", "to_build", "skill", "output", "record_inputs", "record_inputs_from", "record_tool",
             "conditions_field", "conditions", "accept_states", "what")
SHARED = ("to_agent", "to_build", "skill", "record_inputs", "record_inputs_from", "record_tool", "conditions_field",
          "conditions", "accept_states", "what")


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _version(template_meta):
    try:
        return int(str(template_meta.get("version") or "v0")[1:])
    except ValueError:
        return 0


def derived_grade(source_kind, value_kind):
    for rule in _load(GRADES)["rules"]:
        if rule["source_kind"] == source_kind and value_kind in rule["value_kinds"] and not rule.get("retired_on"):
            return rule["grade"]
    raise ValueError("contracts/grades.json has no row for %s / %s" % (source_kind, value_kind))


def declares(rows):
    return any(isinstance(r, dict) and (isinstance(r.get("handover"), dict) or isinstance(r.get("engine_scale"), dict))
               for r in rows or [])


def declaration(rows, agent, build, template_meta, skills, contracts=None):
    """(handovers, parameter_rows, unit_skill or None, section) for rows that declare a hand-over; raises ValueError.
    `skills` is the library's rows for the skills the bundle carries (each with ref and outputs); `contracts` the
    bundle's tool contracts by name, from which a named record_tool's fields are described."""
    contracts = contracts or {}
    units = _load(UNITS)["units"]
    faults, gives, takes, scales, kept = [], {}, [], [], []
    by_ref = {s["ref"]: s for s in skills or []}
    for r in rows or []:
        if not isinstance(r, dict):
            kept.append(r)
            continue
        name = r.get("name")
        if isinstance(r.get("engine_scale"), dict):
            s = dict(r["engine_scale"])
            if "value" in r and r["value"] is not None:
                faults.append("scale row %s carries a value; a scale is a unit it stands for, not a number" % name)
            u, sf = units.get(s.get("unit")), units.get(s.get("stands_for"))
            if not isinstance(u, dict) or u.get("si_factor") is not None:
                faults.append("scale row %s: %r is not an engine's own unit of the registry" % (name, s.get("unit")))
            elif not isinstance(sf, dict) or sf.get("si_factor") is None:
                faults.append("scale row %s: %r is not a registered unit with an si_factor" % (name, s.get("stands_for")))
            elif {k: v for k, v in (u.get("dim") or {}).items() if v} != {k: v for k, v in (sf.get("dim") or {}).items() if v}:
                faults.append("scale row %s: %s and %s are not of one dimension" % (name, s.get("unit"), s.get("stands_for")))
            if s.get("state") not in ("confirmed", "inferred", "unknown"):
                faults.append("scale row %s: state %r is not confirmed, inferred or unknown" % (name, s.get("state")))
            if s.get("state") == "confirmed" and s.get("confirmed_by") != "human":
                faults.append("scale row %s: confirmed by %r; only a person confirms a scale" % (name, s.get("confirmed_by")))
            scales.append(s)
            continue
        h = r.get("handover")
        if not isinstance(h, dict):
            kept.append(r)
            continue
        if "gives" in h:
            g = h["gives"]
            unknown = sorted(set(g) - set(GIVE_KEYS))
            if unknown:
                faults.append("row %s gives with keys the declaration does not name: %s" % (name, ", ".join(unknown)))
            u = units.get(r.get("unit"))
            if not isinstance(u, dict) or u.get("si_factor") is None:
                faults.append("row %s is handed over in %r, which has no si_factor in the registry: an engine's own unit "
                              "means nothing outside its engine" % (name, r.get("unit")))
            skill = by_ref.get(g.get("skill"))
            if skill is None:
                faults.append("row %s is read off %s, which the bundle does not carry" % (name, g.get("skill")))
            elif g.get("output") not in {o["name"] for o in skill.get("outputs") or []}:
                faults.append("row %s is the output %r, which %s does not give" % (name, g.get("output"), g.get("skill")))
            elif skill and set(g.get("record_inputs") or {}) - {i["name"] for i in skill.get("inputs") or []}:
                faults.append("row %s takes inputs of %s from tool results that the skill does not name" % (name, g.get("skill")))
            if g.get("record_inputs_from", "each_result") not in ("each_result", "one_result"):
                faults.append("row %s reads its skill's inputs from %r, neither each_result nor one_result" % (
                    name, g.get("record_inputs_from")))
            if not g.get("thread") or not g.get("to_agent") or not g.get("to_build") or not g.get("what"):
                faults.append("row %s gives with no thread, receiving agent, receiving build or what" % name)
            entry = gives.setdefault(g.get("thread"), {"thread": g.get("thread"), "numbers": []})
            for k in SHARED:
                if k in entry and entry[k] != g.get(k):
                    faults.append("rows over thread %s disagree on %s" % (g.get("thread"), k))
                entry.setdefault(k, g.get(k))
            entry["numbers"].append({"name": name, "output": g.get("output"), "unit": r.get("unit"),
                                     "source_kind": "computed", "value_kind": "computed",
                                     "grade": derived_grade("computed", "computed")})
            continue
        if "takes" in h:
            t = h["takes"]
            if not isinstance(units.get(r.get("unit")), dict):
                faults.append("row %s takes a value into %r, which the registry does not hold" % (name, r.get("unit")))
            if not t.get("name") or not t.get("thread") or not t.get("from_agent"):
                faults.append("row %s takes with no name, thread or agent it comes from" % name)
            takes.append({"row": name, "name": t.get("name"), "thread": t.get("thread"), "from_agent": t.get("from_agent")})
            kept.append({k: v for k, v in r.items() if k != "handover"} | {"takes_handover": dict(t)})
            continue
        faults.append("row %s carries a handover that neither gives nor takes" % name)
    by_unit = {s.get("unit"): s for s in scales}
    for s in scales:
        rests = s.get("rests_on")
        if not rests:
            continue
        bases = [by_unit.get(b) for b in rests]
        if any(b is None for b in bases):
            faults.append("the scale of %s rests on %s, not all of which are scale rows" % (s.get("unit"), rests))
            continue
        if s.get("state") == "confirmed" and any(b.get("state") != "confirmed" for b in bases):
            faults.append("the scale of %s is confirmed while one it rests on is not" % s.get("unit"))
        parts = set((units.get(s.get("stands_for")) or {}).get("derived_from") or {})
        if parts != {b.get("stands_for") for b in bases}:
            faults.append("the scale of %s stands for %s, whose parts %s are not the units its bases stand for %s" % (
                s.get("unit"), s.get("stands_for"), sorted(parts), sorted(b.get("stands_for") for b in bases)))
    # a row that takes a value into an engine's unit no scale names is no fault: its value is held at run time
    script = template_meta.get("handover_script")
    unit_skill = template_meta.get("unit_skill") if takes else None
    if not script:
        faults.append("the parameter rows declare a hand-over and template %s has no handover_script; it needs v32 or "
                      "later" % template_meta.get("version"))
    for entry in gives.values():
        entry["to"] = {"agent": entry.pop("to_agent"), "build": entry.pop("to_build")}
        tool = entry.get("record_tool")
        if tool is None:
            entry.pop("record_tool", None)
            continue
        if _version(template_meta) < 34:
            faults.append("thread %s names the tool its skill's inputs came from, which template %s does not carry into the "
                          "card; it needs v34 or later" % (entry["thread"], template_meta.get("version")))
        props = ((contracts.get(tool) or {}).get("outputs") or {}).get("properties") or {}
        if tool not in contracts:
            faults.append("thread %s: record_tool %r is not a tool of this bundle" % (entry["thread"], tool))
            continue
        fields = {}
        for inp, field in sorted((entry.get("record_inputs") or {}).items()):
            desc = (props.get(field) or {}).get("description")
            if not desc:
                faults.append("thread %s: the field %s of %s carries no description to name the input %s by" % (
                    entry["thread"], field, tool, inp))
                continue
            fields[inp] = {"tool": tool, "field": field, "description": desc}
        entry["record_fields"] = fields
    if faults:
        raise ValueError("the hand-over this request declares cannot be built: " + "; ".join(faults))
    decl = {"note": "what this agent gives to another agent and takes from one, written by its build from the request's "
                    "parameter rows (template v32); src/handover.py reads it, and a value for a row not listed under "
                    "takes is held",
            "agent": {"agent": agent, "build": build}, "gives": list(gives.values()), "takes": takes,
            "engine_scales": scales}
    return decl, kept, unit_skill, section(decl)


def section(decl):
    lines = []
    for g in decl["gives"]:
        lines.append("This agent gives, over the thread `%s`, to `%s` (build `%s`): %s. Each value is the output of "
                     "`%s` named below, read off its record:" % (g["thread"], g["to"]["agent"], g["to"]["build"], g["what"],
                                                               g["skill"]))
        for n in g["numbers"]:
            lines.append("- `%s`, the output `%s`, handed over in `%s`." % (n["name"], n["output"], n["unit"]))
        if g.get("record_inputs"):
            one = g.get("record_inputs_from") == "one_result"
            lines.append("The skill's inputs are taken from the tool result%s named with `--runs`: %s." % (
                "" if one else "s", ", ".join("`%s` from %s `%s`" % (k, "the result's" if one else "each result's", v)
                                              for k, v in sorted(g["record_inputs"].items()))))
        if g.get("conditions_field"):
            lines.append("The conditions each value holds under are the results' `%s`, which must be the same in every "
                         "result." % g["conditions_field"])
        lines.append("")
    if decl["takes"]:
        lines.append("This agent takes, each into a row of `envelope/parameters.json`:")
        for t in decl["takes"]:
            lines.append("- the row `%s` takes `%s` over the thread `%s` from `%s`." % (t["row"], t["name"], t["thread"],
                                                                                       t["from_agent"]))
        lines.append("")
    if decl["engine_scales"]:
        lines.append("What this agent's engine's own units stand for, as the build recorded it:")
        for s in decl["engine_scales"]:
            who = " by %s" % s["confirmed_by"] if s.get("confirmed_by") else ""
            rests = " (from %s)" % ", ".join("`%s`" % b for b in s["rests_on"]) if s.get("rests_on") else ""
            lines.append("- `%s` stands for `%s`, %s%s%s." % (s["unit"], s["stands_for"], s["state"], who, rests))
        lines.append("A value into one of these units is used only where its scale is confirmed by a person; otherwise "
                     "it is held, and so is a value into an engine unit no scale names.")
        lines.append("")
    if not lines:
        return "This agent gives nothing to another agent and takes nothing from one."
    return "\n".join(lines).rstrip()


def no_handovers_section():
    return "This agent gives nothing to another agent and takes nothing from one: its build declares no hand-over."
