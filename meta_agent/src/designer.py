"""The Agent Designer: S1 to S7 on one request (plan.md 5.1).

    python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat> [--build-id 0001] [--now ISO] [--root DIR]
    python -m meta_agent.src.designer --recall meta_agent/requests/<rid> --seat <seat> [--now ISO] [--root DIR]
    python -m meta_agent.src.designer --bounds meta_agent/requests/<rid> [--root DIR]
    python -m meta_agent.src.designer --sheet meta_agent/requests/<rid> --seat <seat> [--now ISO] [--root DIR]

Reads the intake (the person's paragraph, the tool's documentation reading,
the contracts and tasks the seat wrote from it) and writes, in order:
requests/<rid>/agent_goal.json, tool_profile.json (+ .md), knowledge_brief.json,
v2_agent_goal.json, spec_a1..a6.json, synthesis.json, agent_spec.json; then
builds/<agent>/<build_id>/{bundle/, validation_report.json, build.json,
diff_from_template.txt}. It stops there: hand-over is the person's.

S3 searches cases/ with the goal's signature (src/cases/recall.py) and the result enters v2_agent_goal
as case_refs or case_gaps; S4 searches again for A4 (with the parameter names) and A5 (with the safety
rows), and each axis card records what it found or where it looked (plan.md 14-27).

An intake names one tool (`tool_contract`, `tool.adapter_source`, `error_contracts`) or several (`tools`,
a list of {contract, adapter_source, error_contracts}). It may name `skills` of the library
(skills/<kind>/<id>@v<n>/, read with src/skills/catalogue.py) and `subagents`, the drawing
[{name, description, skills, side_effects}]; both go on the agent_spec, a skill the library holds also
into held[], and S5 copies the skills that are not held into the bundle and writes the subagents
(plan.md 14-31, 14-34). A drawing check B11 would fail is refused before anything is written.

--sheet writes a request's parameter_sheet (plan.md 5.3, 14-30; tasks/007) from two files of its folder,
neither of which holds a bound: sheet_draft.json (the rows and the tool) and bounds_binding.json (every
bound skill that applies, as used with the row each input is bound to, or as not applied with the
reason). Code runs the skills (src/parameters/bounds.py through src/skills/runner.py) and writes
bounds[], interval and skills_considered[]; the same two files give the same sheet, and a second run
that changes nothing writes nothing. A draft row may ask for a lookup (src/sources/chemicals_adapter.py):
when the package answers, the row is the database's; when it is absent the row keeps the draft's value
and the sheet says so in degraded[]. --bounds lists the bound skills that apply to a draft, which is what
a model reads to write the binding.

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
from .parameters import bounds as bounds_mod
from .skills import catalogue as catalogue_mod
from .skills import runner as runner_mod
from .sources import chemicals_adapter as chemicals_mod
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
    contracts = [t["contract"] for t in intake.get("tools") or []] or [intake.get("tool_contract") or {}]
    inputs = sorted({k for c in contracts for k in ((c.get("inputs") or {}).get("properties") or {})})
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


def latest_file(req_dir, name):
    """(revision, path) of the highest revision of a file in a request folder: v<N>_<name>, or <name> for 1; (0, None) when absent."""
    found = []
    for fn in sorted(os.listdir(req_dir)) if os.path.isdir(req_dir) else []:
        m = re.match(r"^(?:v([0-9]+)_)?%s$" % re.escape(name), fn)
        if m:
            found.append((int(m.group(1) or 1), os.path.join(req_dir, fn)))
    return max(found) if found else (0, None)


def bound_skills(root):
    """The library's rows for its bound skills (what src/parameters/bounds.py is handed)."""
    return [r for r in catalogue_mod.build_index(os.path.join(root, "skills"))["skills"] if r["kind"] == "bound"]


def sheet_inputs(req_dir):
    out = []
    for name in ("sheet_draft.json", "bounds_binding.json"):
        _, path = latest_file(req_dir, name)
        if path is None:
            raise FileNotFoundError("no %s in %s" % (name, req_dir))
        out.append(path)
    return out


def looked_up(draft):
    """The draft with every row that asks for a lookup answered by the source or left as the draft has it.
    Returns (draft, degraded lines)."""
    draft = dict(draft, rows=[dict(r) for r in draft.get("rows") or []])
    degraded = []
    for row in draft["rows"]:
        request = row.pop("lookup", None)
        if not request:
            continue
        if request.get("source") != "chemicals":
            raise ValueError("row %s asks for a lookup in %r; the Designer has the chemicals adapter only" % (row.get("name"), request.get("source")))
        got, lines, gaps = chemicals_mod.lookup(request)
        if got is not None and got.get("unit") == row.get("unit"):
            for k in ("value", "source", "value_kind", "uncertainty", "conditions"):
                row[k] = got[k]
            row["note"] = got["note"]
            row.pop("grade", None)
        else:
            why = "; ".join(g["reason"] for g in gaps) or "no row came back"
            degraded.append("row %s keeps the draft's value (%s): %s" % (row.get("name"), row.get("source"), why))
        degraded.extend(l for l in lines if l not in degraded)
    return draft, degraded


def write_sheet(req_dir, seat, now=None, root=ROOT):
    """The request's parameter_sheet from its draft and its binding. Returns (path written or None, the sheet)."""
    draft_path, binding_path = sheet_inputs(req_dir)
    draft, degraded = looked_up(cards.load_json(draft_path))
    binding = cards.load_json(binding_path)
    library = os.path.join(root, "skills")
    rev, old_path = latest_file(req_dir, "parameter_sheet.json")
    path = os.path.join(req_dir, "parameter_sheet.json" if rev == 0 else "v%d_parameter_sheet.json" % (rev + 1))
    sheet = bounds_mod.apply(draft, binding, bound_skills(root), lambda ref, inputs: runner_mod.run(ref, inputs, library=library, now=now),
                             seat, now, sheet_path=path, tree=os.path.dirname(root))
    sheet["degraded"] = degraded
    sheet["note"] = ((sheet.get("note") or "").rstrip() + " Bounds, intervals and grades were written by src/parameters/bounds.py from %s "
                     "(sha256:%s) and %s (sha256:%s) of this folder." % (
                         os.path.basename(draft_path), cards.sha256_file(draft_path)[:16],
                         os.path.basename(binding_path), cards.sha256_file(binding_path)[:16])).strip()
    if rev:
        old = cards.load_json(old_path)
        if bounds_mod.same_sheet(old, sheet):
            return None, old
        sheet["revision"] = rev + 1
        sheet["supersedes"] = old["id"]
    cards.write_json(path, sheet)
    return path, sheet


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


def tools_of(intake, root):
    """[{name, contract, adapter_source, errors}] for the one tool or the several an intake names."""
    listed = intake.get("tools") or [{"contract": intake["tool_contract"], "adapter_source": intake["tool"]["adapter_source"],
                                      "error_contracts": intake.get("error_contracts", [])}]
    return [{"name": t["contract"]["name"], "contract": t["contract"],
             "adapter_source": cards.read_text(os.path.join(root, t["adapter_source"])),
             "errors": list(t.get("error_contracts", []))} for t in listed]


def run(intake, seat, build_id="0001", now=None, root=ROOT):
    rid = intake["rid"]
    agent = intake["agent_name"]
    req_dir = os.path.join(root, "requests", rid)
    created = cards.now_iso(now)
    out = {"rid": rid, "files": []}

    # read before anything is written: the tools, the skills of the library and the drawing of the subagents
    tools = tools_of(intake, root)
    contracts = [t["contract"] for t in tools]
    skill_rows = catalogue_mod.take(intake.get("skills") or [], os.path.join(root, "skills"))
    built_skills = [r for r in skill_rows if r["status"] != "held"]
    subagents = list(intake.get("subagents") or [])
    held_refs = {r["ref"] for r in skill_rows if r["status"] == "held"}
    given_held = ["%s names %s" % (a["name"], ref) for a in subagents for ref in a["skills"] if ref in held_refs]
    if given_held:
        raise ValueError("a held skill is given to a subagent only after a person has released it: " + "; ".join(given_held))
    bundle_mod.check_drawing(built_skills, subagents, {t["name"]: t["contract"].get("side_effects") for t in tools},
                             template_mod.SOURCE)

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
    axis_sigs = axis_signatures(goal_sig, intake)
    case_recall = {"A4": search_cases(axis_sigs["A4"], root, "a prior case for this agent's parameters"),
                   "A5": search_cases(axis_sigs["A5"], root, "a prior case for this agent's safety rows")}
    axes, syn, spec = axes_mod.make_axes(goal2, profile, brief, goal["lab_profile_ref"], bundle_rel,
                                         contracts if intake.get("tools") else contracts[0],
                                         intake["interface_tasks"], intake["scientific_tasks"], seat, created,
                                         case_recall=case_recall, skills=skill_rows, subagents=subagents)
    for a in axes:
        put(os.path.join(req_dir, "spec_%s.json" % a["axis"].lower()), a)
    put(os.path.join(req_dir, "synthesis.json"), syn)
    put(os.path.join(req_dir, "agent_spec.json"), spec)

    # S5 build -> bundle from the versioned template
    template_name, template_path = template_mod.materialize(os.path.join(root, "templates"))
    fill = {
        "agent_name": agent,
        "template": template_name,
        "rid": rid,
        "purpose": goal["purpose"],
        "science_task": goal["science_task"],
        "tools_section": bundle_mod.tools_section(contracts),
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
                             intake["interface_tasks"], intake["scientific_tasks"], intake["replay_items"],
                             skills=built_skills, subagents=subagents)
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
               skills=[r["ref"] for r in built_skills], subagents=[a["name"] for a in subagents],
               build_id=build_id_full, validation_report=vr["id"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intake")
    ap.add_argument("--recall", metavar="REQUEST_DIR", help="search cases/ again for an existing request's goal")
    ap.add_argument("--bounds", metavar="REQUEST_DIR", help="list the bound skills that apply to the request's sheet draft")
    ap.add_argument("--sheet", metavar="REQUEST_DIR", help="write the request's parameter_sheet from its draft and its binding")
    ap.add_argument("--seat")
    ap.add_argument("--build-id", default="0001")
    ap.add_argument("--now", default=None)
    ap.add_argument("--root", default=ROOT, help="the meta_agent/ tree to write under (tests use a copy)")
    args = ap.parse_args(argv)
    if [bool(args.intake), bool(args.recall), bool(args.bounds), bool(args.sheet)].count(True) != 1:
        ap.error("give --intake, --recall, --bounds or --sheet, one of them")
    if not args.seat and not args.bounds:
        ap.error("--seat is required")
    if args.bounds:
        root = os.path.abspath(args.root)
        _, draft_path = latest_file(os.path.abspath(args.bounds), "sheet_draft.json")
        if draft_path is None:
            ap.error("no sheet_draft.json in %s" % args.bounds)
        print(bounds_mod.listing(bound_skills(root), cards.load_json(draft_path)))
        return 0
    if args.sheet:
        root = os.path.abspath(args.root)
        try:
            path, sheet = write_sheet(os.path.abspath(args.sheet), args.seat, args.now, root)
        except bounds_mod.BindingError as e:
            print("refused  %s: %s" % (e.code, e))
            return 1
        print("wrote  %s" % rel_repo(path, root) if path else "nothing written: the draft and the binding give the sheet revision %d already is" % sheet["revision"])
        for row in sheet["rows"]:
            iv = row.get("interval")
            if iv:
                print("%-14s [%r, %r] %s  floor %s, ceiling %s%s" % (row["name"], iv["min"], iv["max"], iv["unit"], iv["min_from"], iv["max_from"],
                                                               "  EMPTY: no point" if iv["min"] is not None and iv["max"] is not None and iv["min"] > iv["max"] else ""))
        for line in sheet.get("degraded") or []:
            print("degraded  %s" % line)
        return 0
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
    if out["skills"] or out["subagents"]:
        print("skills   %s" % (", ".join(out["skills"]) or "none"))
        print("subagents %s" % (", ".join(out["subagents"]) or "none"))
    print("stopped after S6: the bundle waits under builds/ for the person's hand-over (landed_at)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
