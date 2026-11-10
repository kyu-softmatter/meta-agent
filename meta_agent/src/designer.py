"""The Agent Designer: S1 to S7 on one request (plan.md 5.1).

    python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat> [--build-id 0001] [--now ISO] [--root DIR]
    python -m meta_agent.src.designer --recall meta_agent/requests/<rid> --seat <seat> [--now ISO] [--root DIR]

Reads the intake (the person's paragraph, the tool's documentation reading,
the contracts and tasks the seat wrote from it) and writes, in order:
requests/<rid>/agent_goal.json, tool_profile.json (+ .md), knowledge_brief.json,
v2_agent_goal.json, spec_a1..a6.json, synthesis.json, agent_spec.json; then
builds/<agent>/<build_id>/{bundle/, validation_report.json, build.json,
diff_from_template.txt}. It stops there: hand-over is the person's.

S3 searches cases/ with the goal's signature (src/cases/recall.py) and the result enters v2_agent_goal
as case_refs or case_gaps; S4 searches again for A4 (with the parameter names) and A5 (with the safety
rows), and each axis card records what it found or where it looked (plan.md 14-27).

--recall runs S3's case search again on a request that already exists, against the store as it is
now: when the result differs from the latest goal revision's, it writes the next one
(v<N>_agent_goal.json; records are append-only), and when it is the same it writes nothing.
"""
import argparse
import os
import re
import sys

from . import cards
from .build import bundle as bundle_mod
from .build import template as template_mod
from .cases import recall as recall_mod
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


def search_cases(signature, root, what):
    """(case_refs, case_gaps) for a signature, searched in the working root's cases/ store."""
    store = os.path.join(root, "cases")
    return recall_mod.refs_and_gaps(recall_mod.recall(signature, store, rel_repo(store, root)), what)


def names_of(rows):
    return [r["name"] for r in rows or [] if isinstance(r, dict) and isinstance(r.get("name"), str) and r["name"]]


def axis_signatures(goal_sig, intake):
    """What A4 and A5 search with: the goal's signature, with the parameters each axis is about."""
    inputs = sorted(((intake.get("tool_contract") or {}).get("inputs") or {}).get("properties") or {})
    a4 = dict(goal_sig, parameter_names=sorted(set(goal_sig["parameter_names"]) | set(names_of(intake.get("parameter_rows"))) | set(inputs)))
    a5 = dict(goal_sig, parameter_names=sorted(set(names_of(intake.get("safety_rows")))))
    return {"A4": a4, "A5": a5}


GOAL_FILE = re.compile(r"^(?:v([0-9]+)_)?agent_goal\.json$")


def latest_goal(req_dir):
    """(revision, card) of the highest agent_goal revision in a request folder."""
    found = []
    for name in sorted(os.listdir(req_dir)):
        m = GOAL_FILE.match(name)
        if m:
            found.append((int(m.group(1) or 1), name))
    if not found:
        raise FileNotFoundError("no agent_goal in %s" % req_dir)
    rev, name = max(found)
    return rev, cards.load_json(os.path.join(req_dir, name))


def recall_again(req_dir, seat, now=None, root=ROOT):
    """S3's case search on an existing request; the next goal revision when the result changed, else None."""
    rev, goal = latest_goal(req_dir)
    case_refs, case_gaps = search_cases(goal_mod.signature_of(goal), root, "a prior case for this goal's signature")
    if case_refs == goal.get("case_refs", []) and case_gaps == goal.get("case_gaps", []):
        return None
    nxt = goal_mod.attach_recall(goal, goal.get("kb_refs", []), goal.get("kb_gaps", []), case_refs, case_gaps,
                                 seat, cards.now_iso(now), status=goal.get("status", "validated"))
    path = os.path.join(req_dir, "v%d_agent_goal.json" % (rev + 1))
    if os.path.exists(path):
        raise FileExistsError(path)
    cards.write_json(path, nxt)
    return path


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
    brief = brief_mod.make_brief(goal, root, seat, created)
    put(os.path.join(req_dir, "knowledge_brief.json"), brief)
    goal_sig = goal_mod.signature_of(goal)
    case_refs, case_gaps = search_cases(goal_sig, root, "a prior case for this goal's signature")
    kb_refs = [{"id": e["id"], "version": e["version"], "hash": e["hash"]} for e in brief["entries"]]
    goal2 = goal_mod.attach_recall(goal, kb_refs, brief["gaps"], case_refs, case_gaps, seat, created)
    put(os.path.join(req_dir, "v2_agent_goal.json"), goal2)

    # S4 specify -> six axes, synthesis, agent_spec
    build_dir = os.path.join(root, "builds", agent, build_id)
    bundle_path = os.path.join(build_dir, "bundle")
    bundle_rel = rel_repo(bundle_path, root)
    contract = intake["tool_contract"]
    axis_sigs = axis_signatures(goal_sig, intake)
    case_recall = {"A4": search_cases(axis_sigs["A4"], root, "a prior case for this agent's parameters"),
                   "A5": search_cases(axis_sigs["A5"], root, "a prior case for this agent's safety rows")}
    axes, syn, spec = axes_mod.make_axes(goal2, profile, brief, goal["lab_profile_ref"], bundle_rel, contract,
                                         intake["interface_tasks"], intake["scientific_tasks"], seat, created,
                                         case_recall=case_recall)
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
    ap.add_argument("--intake")
    ap.add_argument("--recall", metavar="REQUEST_DIR", help="search cases/ again for an existing request's goal")
    ap.add_argument("--seat", required=True)
    ap.add_argument("--build-id", default="0001")
    ap.add_argument("--now", default=None)
    ap.add_argument("--root", default=ROOT, help="the meta_agent/ tree to write under (tests use a copy)")
    args = ap.parse_args(argv)
    if bool(args.intake) == bool(args.recall):
        ap.error("give --intake or --recall, one of the two")
    if args.recall:
        root = os.path.abspath(args.root)
        path = recall_again(os.path.abspath(args.recall), args.seat, args.now, root)
        rev, goal = latest_goal(os.path.abspath(args.recall))
        print("wrote  %s" % rel_repo(path, root) if path else "nothing written: recall gives what revision %d already carries" % rev)
        print("case_refs %d, case_gaps %d (revision %d)" % (len(goal.get("case_refs", [])), len(goal.get("case_gaps", [])), rev))
        return 0
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
