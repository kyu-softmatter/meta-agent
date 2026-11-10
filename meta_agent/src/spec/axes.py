"""S4 Specify: the six axes, their synthesis and the agent_spec (plan.md 5.1).

Each axis is its own card and names what it read. Conflicts between axes go
into the synthesis with the direction of concession; anything with an
unresolved scope, permission, side effect or validation goes to held[].
A4 and A5 carry what recall found in cases/ for their own signature, or the
gap naming where it looked (plan.md 14-27): the Designer searches and hands
the result in as `case_recall`.
"""
from .. import cards

TITLES = {"A1": "Boundary", "A2": "Interface", "A3": "Knowledge", "A4": "Parameters", "A5": "Safety", "A6": "Validation"}


def make_axes(goal, profile, brief, lab_profile_ref, bundle_dir, tool_contract, interface_tasks,
              scientific_tasks, seat, now=None, parameter_rows=None, safety_rows=None, case_recall=None):
    created = cards.now_iso(now)
    rid = goal["rid"]
    base = "spec-" + rid.replace("req-", "")
    reads = [goal["id"], profile["id"], brief["id"], lab_profile_ref]
    parameter_rows = list(parameter_rows or [])
    safety_rows = list(safety_rows or [])
    tool = tool_contract["name"]
    gate_needed = bool((tool_contract.get("safety_gate") or {}).get("required")) or tool_contract.get("side_effects") != "none"
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
                "name": tool,
                "inputs": sorted(((tool_contract.get("inputs") or {}).get("properties") or {}).keys()),
                "outputs": sorted(((tool_contract.get("outputs") or {}).get("properties") or {}).keys()),
                "errors": list(tool_contract.get("errors", [])),
                "side_effects": tool_contract.get("side_effects"),
            }],
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
                    + ("; %s requires one" % tool if gate_needed else "; %s has no side effects and requires none" % tool),
            "human_only": ["safety values", "hand-over (landed_at)", "the scientific tolerance"],
        },
        "A6": {
            "interface": [t["name"] for t in interface_tasks],
            "scientific": [t["name"] for t in scientific_tasks],
            "completion": "every interface task passes and every scientific task passes against a person's tolerance",
            "refusal": "an error contract or a gate refusal is reported as such; not_run and undecided are not passes",
        },
    }
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
    return axes, syn, spec
