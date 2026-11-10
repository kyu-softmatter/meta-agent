"""S4 Specify: the six axes, their synthesis and the agent_spec (plan.md 5.1).

Each axis is its own card and names what it read. Conflicts between axes go
into the synthesis with the direction of concession; anything with an
unresolved scope, permission, side effect or validation goes to held[].
A4 and A5 carry what recall found in cases/ for their own signature, or the
gap naming where it looked (plan.md 14-27): the Designer searches and hands
the result in as `case_recall`.

An agent may have several tools: `tool_contract` is one contract or a list of
them. The skills the agent is built with and the drawing of its subagents go
on the agent_spec, where the person sees them (plan.md 14-31(h)); a skill the
library holds is named in skills and in held[], and S5 leaves it out of the
bundle. The Designer reads the library and hands the rows in.
"""
from .. import cards

TITLES = {"A1": "Boundary", "A2": "Interface", "A3": "Knowledge", "A4": "Parameters", "A5": "Safety", "A6": "Validation"}


def make_axes(goal, profile, brief, lab_profile_ref, bundle_dir, tool_contract, interface_tasks,
              scientific_tasks, seat, now=None, parameter_rows=None, safety_rows=None, case_recall=None,
              skills=None, subagents=None):
    """`skills` are the library's rows (src/skills/catalogue.take) for the skills the request names, in its
    order; `subagents` is the request's drawing, [{name, description, skills, side_effects}]."""
    created = cards.now_iso(now)
    rid = goal["rid"]
    base = "spec-" + rid.replace("req-", "")
    reads = [goal["id"], profile["id"], brief["id"], lab_profile_ref]
    parameter_rows = list(parameter_rows or [])
    safety_rows = list(safety_rows or [])
    contracts = list(tool_contract) if isinstance(tool_contract, (list, tuple)) else [tool_contract]
    gated = [c["name"] for c in contracts
             if bool((c.get("safety_gate") or {}).get("required")) or c.get("side_effects") not in ("none", "reads_instrument")]
    gate_needed = bool(gated)
    tool = ", ".join(gated) if gated else ", ".join(c["name"] for c in contracts)
    if gated:
        gate_says = "; %s require%s one" % (tool, "s" if len(gated) == 1 else "")
    elif any(c.get("side_effects") == "reads_instrument" for c in contracts):
        gate_says = "; %s read the device or nothing, change nothing, and require none" % tool
    else:
        gate_says = "; %s has no side effects and requires none" % tool
    skills = list(skills or [])
    subagents = list(subagents or [])
    held_skills = [r["ref"] for r in skills if r["status"] == "held"]
    content = {
        "A1": {
            "directory": bundle_dir,
            "writes": ["failures.jsonl", "runs/"],
            "reads": ["envelope/", "tools/", "validation/", "replay/", "tasks/"],
            "forbidden": ["envelope/safety.json", "CLAUDE.md", ".claude/", "any path outside the bundle", "network hosts", "credentials"],
            "seat": "%s-<machine>-<YYYYMMDD>-<n>" % goal["tool"]["name"],
            "tier": 0,
        },
        "A2": {
            "cards_in": ["tasks/*.md"],
            "cards_out": ["the printed reports of src/replay.py and src/validate_tasks.py", "failures.jsonl lines"],
            "callable_tools": [{
                "name": c["name"],
                "inputs": sorted(((c.get("inputs") or {}).get("properties") or {}).keys()),
                "outputs": sorted(((c.get("outputs") or {}).get("properties") or {}).keys()),
                "errors": list(c.get("errors", [])),
                "side_effects": c.get("side_effects"),
            } for c in contracts],
            "gui_fields": [],
        },
        "A3": {
            "snapshot": [e["id"] for e in brief.get("entries", [])],
            "kb_version": brief["kb_version"],
            "gaps": [g["what"] for g in brief.get("gaps", [])],
        },
        "A4": {
            "rows": parameter_rows,
            "note": "rows come from the parameter sheet; a tool without physical parameters has none",
        },
        "A5": {
            "rows": safety_rows,
            "gate": "src/gate.py reads envelope/safety.json before any tool whose contract requires a gate"
                    + gate_says,
            "human_only": ["safety values", "hand-over (landed_at)", "the scientific tolerance"],
        },
        "A6": {
            "interface": [t["name"] for t in interface_tasks],
            "scientific": [t["name"] for t in scientific_tasks],
            "completion": "every interface task passes and every scientific task passes against a person's tolerance",
            "refusal": "an error contract or a gate refusal is reported as such; not_run and undecided are not passes",
        },
    }
    if skills or subagents:
        content["A2"]["skills"] = [{"ref": r["ref"], "kind": r["kind"], "side_effect": r["side_effect"], "status": r["status"],
                                    "calls_tools": list(r["calls_tools"])} for r in skills]
        content["A2"]["subagents"] = [a["name"] for a in subagents]
    axes = []
    for axis in ("A1", "A2", "A3", "A4", "A5", "A6"):
        c = cards.skeleton("spec_axis", "%s-%s" % (base, axis.lower()), seat, created, rid=rid)
        c["axis"] = axis
        c["title"] = TITLES[axis]
        c["content"] = content[axis]
        c["reads"] = list(reads)
        c["held"] = []
        if axis in (case_recall or {}):
            refs, gaps = case_recall[axis]
            if not (refs or gaps):
                raise ValueError("%s: recall must leave case_refs or case_gaps" % axis)
            c["case_refs"], c["case_gaps"] = list(refs), list(gaps)
        axes.append(c)
    # anything a person has not decided yet is held, not shipped
    held = []
    if goal.get("gui_choice") == "undecided":
        held.append("gui: the person has not chosen")
    if gate_needed and not safety_rows:
        held.append("%s: a gate is required but no safety row is named" % tool)
    for ref in held_skills:
        held.append({"item": "skill %s" % ref, "reason": "it changes a device (write_device): held in the library until a person "
                                                         "releases it, and left out of the bundle"})
    syn = cards.skeleton("synthesis", "syn-" + rid.replace("req-", ""), seat, created, rid=rid)
    syn["axis_refs"] = ["spec_%s.json" % a.lower() for a in TITLES]
    syn["conflicts"] = []
    syn["held"] = held
    spec = cards.skeleton("agent_spec", base, seat, created, rid=rid, status="validated" if not held else "held")
    spec["axis_refs"] = {a: "spec_%s.json" % a.lower() for a in TITLES}
    spec["synthesis_ref"] = "synthesis.json"
    spec["goal_ref"] = goal["id"]
    spec["tool_profile_ref"] = profile["id"]
    spec["lab_profile_ref"] = lab_profile_ref
    spec["held"] = list(held)
    if skills or subagents:
        spec["skills"] = [r["ref"] for r in skills]
        spec["subagents"] = [{"name": a["name"], "description": a["description"], "skills": list(a["skills"]),
                              "side_effects": list(a["side_effects"])} for a in subagents]
    return axes, syn, spec
