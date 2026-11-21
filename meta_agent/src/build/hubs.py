"""The hub template and the builder of a hub bundle (meta_agent/tasks/033; the person, 2026-11-20, 'A hub bundle
(Recommended)', 'Assign freely, carry on my word (Recommended)', 'Ask once per question (Recommended)').

    python -m meta_agent.src.build.hubs --name <hub> --member <agent>/<NNNN> --member <agent>/<NNNN> [...]
                                        --purpose "<what the hub is for, in words>" --lab-profile <id> --seat <seat>
                                        [--build-id NNNN] [--now ISO] [--root meta_agent]

The template's source trees live in hub_template_v<N>/ beside this file, one folder per version, as the agent
template's do; `materialize` copies a version to templates/hub@<hash>/, and a build names that folder, which bundle
check B19 reads the bridge's bytes from.

v1  the first hub (tasks/033): CLAUDE.md, README.md, TEMPLATE.json, run-hub and choose-session-level, src/hub.py and a
    copy of contracts/tools/bridge.py as src/bridge.py, question/, assignments/, inbox/, sessions/, failures.jsonl, and
    .claude/settings.json; no tool, gate, envelope or library skill.

A build makes builds/<hub>/<NNNN>/ beside the engine builds of one request: the bundle, its build card, the difference
from the template. members.json names each member by its agent, its build, its folder ../<agent>-<NNNN> (the name a run
gives the bundle, which is where the person places it beside the hub) and the sha256 of its build card. The builder
refuses a member whose bundle is not the digest its build card states, one whose template cannot answer an assignment
(the agent template before v35, which has no results_file), fewer than two members, and two members of one agent.
Its gate is the hub's own: in a temporary folder laid out as the members' folders say, `python src/hub.py members` must
find each member there, holding the build members.json names and able to answer an assignment. The hub computes
nothing, so its scientific gate is not_run.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from .. import cards

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # meta_agent/
REPO = os.path.dirname(ROOT)
SOURCES = {"v1": os.path.join(HERE, "hub_template_v1")}
LATEST = "v1"
BRIDGE = os.path.join(REPO, "contracts", "tools", "bridge.py")
BUILD_ID = re.compile(r"^[0-9]{4}$")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,60}$")
NUM_RE = re.compile(r"(?<![\w./:+-])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w/:%-])")   # as check 24 and B19 read one


def template_name(root=None):
    return "hub@" + cards.sha256_tree(root or SOURCES[LATEST]).split(":", 1)[1][:12]


def materialize(templates_root, root=None):
    root = root or SOURCES[LATEST]
    name = template_name(root)
    dest = os.path.join(templates_root, name)
    if not os.path.isdir(dest):
        shutil.copytree(root, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return name, dest


def member_entry(root, build):
    """{agent, build, folder, build_card_sha256, bundle} for one member build, or ValueError naming why it cannot be one."""
    parts = build.split("/")
    if len(parts) != 2 or not NAME_RE.match(parts[0]) or not BUILD_ID.match(parts[1]):
        raise ValueError("a member is named <agent>/<NNNN>, not %r" % build)
    card_path = os.path.join(root, "builds", parts[0], parts[1], "build.json")
    if not os.path.isfile(card_path):
        raise ValueError("%s has no build card at %s" % (build, os.path.relpath(card_path, REPO)))
    card = cards.load_json(card_path)
    bundle = os.path.join(REPO, *card["bundle_path"].split("/"))
    if not os.path.isdir(bundle):
        bundle = os.path.join(os.path.dirname(card_path), "bundle")
    if cards.sha256_tree(bundle) != card.get("bundle_sha256"):
        raise ValueError("%s: its bundle is not the digest its build card states; a member is a build as it was made" % build)
    t = cards.load_json(os.path.join(bundle, "TEMPLATE.json"))
    if t.get("template") != "agent" or not t.get("results_file"):
        raise ValueError("%s is of template %s %s, which cannot answer an assignment; it needs the agent template v35 or "
                         "later" % (build, t.get("template"), t.get("version")))
    return {"agent": parts[0], "build": build, "folder": "../%s-%s" % (parts[0], parts[1]),
            "build_card_sha256": "sha256:" + cards.sha256_file(card_path), "bundle": bundle, "card": card}


def members_section(entries):
    lines = ["This hub's members, as the build found them:", ""]
    for e in entries:
        lines.append("- `%s`, build `%s`, in the folder `%s` beside this one." % (e["agent"], e["build"], e["folder"]))
    return "\n".join(lines)


def gate(bundle, entries):
    """The hub's own gate: lay the hub and copies of its members out as members.json says, and have src/hub.py read them.
    Returns (verdict, what it printed)."""
    tmp = tempfile.mkdtemp(prefix="hub-gate-")
    try:
        hub_dir = os.path.join(tmp, "hub")
        shutil.copytree(bundle, hub_dir)
        for e in entries:
            shutil.copytree(e["bundle"], os.path.normpath(os.path.join(hub_dir, e["folder"])))
        p = subprocess.run([sys.executable, os.path.join("src", "hub.py"), "members"], cwd=hub_dir,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.stdout.decode("utf-8", "replace")
        try:
            report = json.loads(out)
        except ValueError:
            return "fail", out + p.stderr.decode("utf-8", "replace")
        ok = p.returncode == 0 and len(report["members"]) == len(entries) and all(
            m.get("there") and m.get("holds_this_build") and m.get("answers_assignments") for m in report["members"])
        return ("pass" if ok else "fail"), out
    finally:
        shutil.rmtree(tmp, True)


def build(name, members, purpose, lab_profile, seat, build_id=None, now=None, root=ROOT, rid=None):
    """Make builds/<name>/<NNNN>/ and return what was written. Raises ValueError before anything is written."""
    if not NAME_RE.match(name or ""):
        raise ValueError("a hub's name is lower-case words joined by hyphens, not %r" % name)
    if not isinstance(purpose, str) or not purpose.strip():
        raise ValueError("say in words what the hub is for")
    if NUM_RE.search(purpose):
        raise ValueError("the hub's purpose carries a number: a hub's CLAUDE.md holds no number (B19)")
    if len(members or []) < 2:
        raise ValueError("a hub coordinates two members at least")
    entries = [member_entry(root, b) for b in members]
    agents = [e["agent"] for e in entries]
    if len(set(agents)) != len(agents):
        raise ValueError("two members are builds of one agent: %s" % agents)
    if name in agents:
        raise ValueError("the hub's name %s is a member's" % name)
    builds = os.path.join(root, "builds", name)
    have = sorted(n for n in (os.listdir(builds) if os.path.isdir(builds) else []) if BUILD_ID.match(n))
    build_id = build_id or "%04d" % (int(have[-1]) + 1 if have else 1)
    if not BUILD_ID.match(build_id):
        raise ValueError("a build id is four digits, not %r" % build_id)
    out_dir = os.path.join(builds, build_id)
    if os.path.exists(out_dir):
        raise FileExistsError("build exists: %s (a rebuild is a new build id)" % os.path.relpath(out_dir, REPO))
    template_root = SOURCES[LATEST]
    if cards.sha256_file(os.path.join(template_root, "src", "bridge.py")) != cards.sha256_file(BRIDGE):
        raise ValueError("the template's src/bridge.py is not the bytes of contracts/tools/bridge.py: a new template "
                         "version carries the bridge as it now is")
    tname, tpath = materialize(os.path.join(root, "templates"), template_root)
    created = cards.now_iso(now)
    bundle = os.path.join(out_dir, "bundle")
    shutil.copytree(tpath, bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    hub_build = "%s/%s" % (name, build_id)
    fill = {"hub_name": name, "template": tname, "rid": rid or "none: a hub is built over the builds it coordinates",
            "purpose": purpose.strip(), "members_section": members_section(entries)}
    text = cards.read_text(os.path.join(bundle, "CLAUDE.md"))
    for k, v in fill.items():
        text = text.replace("{{%s}}" % k, v)
    if "{{" in text:
        raise ValueError("CLAUDE.md keeps a placeholder after the fill")
    cards.write_text(os.path.join(bundle, "CLAUDE.md"), text)
    mcard = cards.skeleton("hub_members", "members-%s" % name, seat, created)
    for k in ("kb_refs", "kb_gaps", "case_refs", "case_gaps", "rid"):
        mcard.pop(k, None)
    mcard.update({"hub": {"agent": name, "build": hub_build},
                  "members": [{k: e[k] for k in ("agent", "build", "folder", "build_card_sha256")} for e in entries]})
    cards.write_json(os.path.join(bundle, "members.json"), mcard)
    verdict, printed = gate(bundle, entries)
    diff = ["# diff from template", "# template: %s" % tname, ""]
    t_files, b_files = set(cards.tree_files(tpath)), set(cards.tree_files(bundle))
    diff += ["added     %s" % r for r in sorted(b_files - t_files)]
    diff += ["removed   %s" % r for r in sorted(t_files - b_files)]
    diff += ["modified  %s" % r for r in sorted(t_files & b_files)
             if cards.sha256_file(os.path.join(tpath, r)) != cards.sha256_file(os.path.join(bundle, r))]
    cards.write_text(os.path.join(out_dir, "diff_from_template.txt"), "\n".join(diff) + "\n")
    parent = None
    if have:
        parent = cards.load_json(os.path.join(builds, have[-1], "build.json"))["id"]
    bcard = cards.skeleton("build", "build-%s-%s" % (name, build_id), seat, created)
    if rid:
        bcard["rid"] = rid
    bcard.update({"spec_ref": mcard["id"], "lab_profile_ref": lab_profile, "template_version": tname,
                  "diff_from_template": "diff_from_template.txt",
                  "bundle_path": os.path.relpath(bundle, REPO).replace(os.sep, "/"),
                  "bundle_sha256": cards.sha256_tree(bundle), "held": [],
                  "gate_verdict": {"interface": verdict, "scientific": "not_run", "validation_report_ref": None},
                  "lineage": {"parent_build": parent, "candidate_of": 1, "k": 1}, "landed_at": None,
                  "note": "a hub over %s (template %s); its specification is members.json, the card %s, and its gate is "
                          "src/hub.py members in a folder laid out as members.json says, which found every member there, "
                          "holding its build and able to answer an assignment: %s; the hub computes nothing, so its "
                          "scientific gate is not_run; the bridge copied as src/bridge.py is %s, the bytes of "
                          "contracts/tools/bridge.py; hand-over (landed_at) is the person's" % (
                              ", ".join(e["build"] for e in entries), tname, mcard["id"], verdict,
                              "sha256:" + cards.sha256_file(os.path.join(bundle, "src", "bridge.py")))})
    cards.write_json(os.path.join(out_dir, "build.json"), bcard)
    return {"build": hub_build, "dir": os.path.relpath(out_dir, REPO), "template": tname, "gate": verdict,
            "gate_printed": printed, "members": [{k: e[k] for k in ("agent", "build", "folder", "build_card_sha256")}
                                                 for e in entries]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--member", action="append", required=True, metavar="AGENT/NNNN")
    ap.add_argument("--purpose", required=True)
    ap.add_argument("--lab-profile", required=True)
    ap.add_argument("--seat", required=True)
    ap.add_argument("--rid")
    ap.add_argument("--build-id")
    ap.add_argument("--now")
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    try:
        out = build(a.name, a.member, a.purpose, a.lab_profile, a.seat, a.build_id, a.now, a.root, a.rid)
    except (ValueError, FileExistsError) as e:
        print("refused  %s" % e)
        return 3
    print(json.dumps({k: v for k, v in out.items() if k != "gate_printed"}, indent=2, ensure_ascii=False))
    return 0 if out["gate"] == "pass" else 4


if __name__ == "__main__":
    sys.exit(main())
