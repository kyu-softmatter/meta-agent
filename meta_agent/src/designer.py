"""The Agent Designer: S1 to S7 on one request (plan.md 5.1).

    python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat> [--build-id 0001] [--now ISO] [--root DIR]

Reads the intake (the person's paragraph, the tool's documentation reading,
the contracts and tasks the seat wrote from it) and writes, in order:
requests/<rid>/agent_goal.json, tool_profile.json (+ .md), knowledge_brief.json,
v2_agent_goal.json, spec_a1..a6.json, synthesis.json, agent_spec.json; then
builds/<agent>/<build_id>/{bundle/, validation_report.json, build.json,
diff_from_template.txt}. It stops there: hand-over is the person's.
"""
import argparse
import os
import sys

from . import cards
from .build import bundle as bundle_mod
from .build import template as template_mod
from .intake import goal as goal_mod
from .knowledge import brief as brief_mod
from .spec import axes as axes_mod
from .tooling import profile as profile_mod
from .validate import gate as gate_mod

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # meta_agent/
REPO = os.path.dirname(ROOT)


def rel_repo(path, root):
    """A repository-relative, posix path for a file under the working root."""
    base = os.path.dirname(root)
    return os.path.relpath(path, base).replace(os.sep, "/")


def profile_markdown(profile):
    lines = ["# tool_profile %s" % profile["id"], "",
             "Tool `%s` (%s), read from %s. Analysis permission: %s." % (
                 profile["tool"]["name"], profile["tool"]["kind"], profile["tool"].get("source", "no document"),
                 "none; binaries and runtime were not analysed" if not profile.get("analysis_permission") else "granted"),
             "", "## Claims", ""]
    for c in profile["claims"]:
        loci = ", ".join(e["locus"] for e in c.get("evidence", [])) or "no locus"
        lines.append("- **%s** (%s): %s; at %s%s" % (c["kind"], c["basis"], c["claim"], loci,
                                                     ("; requires: " + c["requires"]) if c.get("requires") else ""))
    lines += ["", "## Gaps", ""]
    for g in profile["gaps"]:
        lines.append("- %s (%s)%s" % (g["what"], g["reason"], ("; requires: " + g["requires"]) if g.get("requires") else ""))
    if not profile["gaps"]:
        lines.append("- none")
    lines += ["", "Parameter candidates: %s." % (", ".join("`%s`" % p for p in profile["parameter_candidates"]) or "none"), ""]
    return "\n".join(lines)


def run(intake, seat, build_id="0001", now=None, root=ROOT):
    rid = intake["rid"]
    agent = intake["agent_name"]
    req_dir = os.path.join(root, "requests", rid)
    created = cards.now_iso(now)
    out = {"rid": rid, "files": []}

    def put(path, data):
        if isinstance(data, str):
            cards.write_text(path, data)
        else:
            cards.write_json(path, data)
        out["files"].append(rel_repo(path, root))

    # S1 intake -> agent_goal (no numbers)
    goal = goal_mod.make_goal(intake, seat, created)
    put(os.path.join(req_dir, "agent_goal.json"), goal)

    # S2 tool understanding from documentation -> tool_profile
    profile = profile_mod.make_profile(intake, seat, created)
    put(os.path.join(req_dir, "tool_profile.json"), profile)
    put(os.path.join(req_dir, "tool_profile.md"), profile_markdown(profile))

    # S3 recall / scan -> knowledge_brief, v2_agent_goal
    brief, case_refs, case_gaps = brief_mod.make_brief(goal, root, seat, created)
    put(os.path.join(req_dir, "knowledge_brief.json"), brief)
    kb_refs = [{"id": e["id"], "version": e["version"], "hash": e["hash"]} for e in brief["entries"]]
    goal2 = goal_mod.attach_recall(goal, kb_refs, brief["gaps"], case_refs, case_gaps, seat, created)
    put(os.path.join(req_dir, "v2_agent_goal.json"), goal2)

    # S4 specify -> six axes, synthesis, agent_spec
    build_dir = os.path.join(root, "builds", agent, build_id)
    bundle_path = os.path.join(build_dir, "bundle")
    bundle_rel = rel_repo(bundle_path, root)
    contract = intake["tool_contract"]
    axes, syn, spec = axes_mod.make_axes(goal2, profile, brief, goal["lab_profile_ref"], bundle_rel, contract,
                                         intake["interface_tasks"], intake["scientific_tasks"], seat, created)
    for a in axes:
        put(os.path.join(req_dir, "spec_%s.json" % a["axis"].lower()), a)
    put(os.path.join(req_dir, "synthesis.json"), syn)
    put(os.path.join(req_dir, "agent_spec.json"), spec)

    # S5 build -> bundle from the versioned template
    template_name, template_path = template_mod.materialize(os.path.join(root, "templates"))
    adapter_source = cards.read_text(os.path.join(root, intake["tool"]["adapter_source"]))
    tools = [{"name": contract["name"], "contract": contract, "adapter_source": adapter_source,
              "errors": intake.get("error_contracts", [])}]
    fill = {
        "agent_name": agent,
        "template": template_name,
        "rid": rid,
        "purpose": goal["purpose"],
        "science_task": goal["science_task"],
        "tools_section": bundle_mod.tools_section([contract]),
        "must_not": bundle_mod.must_not_section(goal["must_not"]),
        "skills_section": bundle_mod.skills_section([]),
        "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % agent,
    }
    capabilities = profile_mod.capabilities(profile, agent)
    envelope = {
        "safety": {row["name"]: None for row in (intake.get("safety_rows") or [])},
        "snapshot": {"kb_version": brief["kb_version"], "entries": brief["entries"], "numbers": []},
        "parameters": {"rows": list(intake.get("parameter_rows") or [])},
    }
    sha = bundle_mod.compose(template_path, bundle_path, fill, tools, capabilities, envelope,
                             intake["interface_tasks"], intake["scientific_tasks"], intake["replay_items"])
    out["files"].append(bundle_rel + "/")
    diff_text = bundle_mod.diff_from_template(template_path, bundle_path)
    put(os.path.join(build_dir, "diff_from_template.txt"), diff_text)

    # S6 validate -> the bundle's own gates, read off a fresh process; validation_report
    build_id_full = "build-%s-%s" % (agent, build_id)
    report = gate_mod.run_bundle(bundle_path)
    vr, iface_v, sci_v = gate_mod.make_validation_report(report, build_id_full, rid, bundle_rel, seat, created)
    put(os.path.join(build_dir, "validation_report.json"), vr)
    build = bundle_mod.make_build_card(build_id_full, rid, spec, goal["lab_profile_ref"], template_name,
                                       "diff_from_template.txt", bundle_rel, sha, seat, created)
    build["gate_verdict"] = {"interface": iface_v, "scientific": sci_v, "validation_report_ref": vr["id"]}
    build["status"] = "validated" if vr["overall"] == "pass" else "draft"
    build["note"] = "replay: %d item(s), %s; hand-over (landed_at) is the person's" % (
        len(report["replay"]["items"]), "all as expected" if report["replay"]["ok"] else "NOT as expected")
    put(os.path.join(build_dir, "build.json"), build)

    # S7 hand over: stop here
    out.update(template=template_name, bundle_sha256=sha, gates={"interface": iface_v, "scientific": sci_v, "overall": vr["overall"]},
               replay_ok=report["replay"]["ok"], replay_items=len(report["replay"]["items"]), held=spec["held"],
               build_id=build_id_full, validation_report=vr["id"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intake", required=True)
    ap.add_argument("--seat", required=True)
    ap.add_argument("--build-id", default="0001")
    ap.add_argument("--now", default=None)
    ap.add_argument("--root", default=ROOT, help="the meta_agent/ tree to write under (tests use a copy)")
    args = ap.parse_args(argv)
    intake = cards.load_json(args.intake)
    out = run(intake, args.seat, args.build_id, args.now, os.path.abspath(args.root))
    for f in out["files"]:
        print("wrote  %s" % f)
    print("template %s" % out["template"])
    print("bundle   %s" % out["bundle_sha256"])
    print("gates    interface %(interface)s, scientific %(scientific)s; overall %(overall)s" % out["gates"])
    print("replay   %d item(s) %s" % (out["replay_items"], "as expected" if out["replay_ok"] else "NOT as expected"))
    print("held     %s" % (out["held"] or "nothing"))
    print("stopped after S6: the bundle waits under builds/ for the person's hand-over (landed_at)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
