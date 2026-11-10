"""S5 Build: a bundle from the template plus the Designer's outputs, and the build card.

Skills and subagents (plan.md 14-31, 14-34; tasks/010): the skills a specification names are copied from
the library into the bundle's skills/<id>@v<n>/ unchanged, and each subagent it names becomes
.claude/agents/<name>.md with the skills and the side effects it may use. The caller reads the library
(src/skills/catalogue.take) and hands the rows in; this stage imports no sibling stage (plan.md 7). What
check B11 would fail in the finished bundle is refused here, before anything is written: a held skill (it
belongs in the specification's held[], not in a bundle), a skill whose tool the bundle does not have or
that uses a skill the specification does not name, a subagent whose side effects do not cover its skills,
and a second subagent that may change a device.
"""
import difflib
import os
import shutil

from .. import cards

WRITER = "operator"        # the one subagent that may list write_device (plan.md 14-34(e))
SIDE_EFFECTS = ("none", "read_device", "write_device")

TEXT_EXT = (".md", ".json", ".py", ".jsonl", ".txt", ".toml")


def render(text, fill):
    for k, v in fill.items():
        text = text.replace("{{%s}}" % k, v)
    left = [t for t in text.split("{{")[1:] if "}}" in t]
    if left:
        raise ValueError("unfilled placeholders: %s" % [t.split("}}")[0] for t in left])
    return text


def tools_section(tool_contracts):
    out = []
    for tc in tool_contracts:
        ins = ", ".join("`%s` (%s%s)" % (k, v.get("type", "any"), ", required" if k in (tc.get("inputs") or {}).get("required", []) else "")
                        for k, v in sorted(((tc.get("inputs") or {}).get("properties") or {}).items()))
        outs = ", ".join("`%s` (%s)" % (k, v.get("type", "any"))
                         for k, v in sorted(((tc.get("outputs") or {}).get("properties") or {}).items()))
        gate = tc.get("safety_gate") or {}
        out.append("### `%s`\n\n%s\n\n- input: %s\n- output: %s\n- errors it may return: %s\n- side effects: %s; idempotent: %s\n- gate: %s"
                   % (tc["name"], tc["description"], ins or "none", outs or "none",
                      ", ".join("`%s`" % e for e in tc.get("errors", [])), tc.get("side_effects"),
                      "yes" if tc.get("idempotent") else "no",
                      ("required, at " + gate.get("place", "src/gate.py")) if gate.get("required") else "not required (" + gate.get("place", "no side effects") + ")"))
    return "\n\n".join(out) if out else "This agent has no callable tool."


def must_not_section(items):
    return "\n".join("- %s." % (i[:1].upper() + i[1:]).rstrip(".") for i in items) if items else "- (nothing beyond the common rules)"


def skills_section(skills):
    """`skills` is a list of (name, trigger sentence); B8 looks for each name in backticks."""
    if not skills:
        return "This agent has no skills. A skill, when one is added, is named here with the sentence that triggers it."
    return "\n".join("- `%s`: %s" % (name, trigger) for name, trigger in skills)


def subagents_section(subagents):
    if not subagents:
        return "This agent has no subagents."
    lines = ["Each subagent is a file under `.claude/agents/` and works in its own context. It is not a seat: it writes no "
             "record and commits nothing; this agent reports and commits what a subagent returns. Only `%s` may be given "
             "a skill that changes a device." % WRITER, ""]
    for a in subagents:
        lines.append("- `%s`: %s Skills: %s. Side effects: %s." % (
            a["name"], a["description"].rstrip(".") + ".", ", ".join("`%s`" % r for r in a["skills"]) or "none",
            ", ".join(a["side_effects"]) or "none"))
    return "\n".join(lines)


def subagent_markdown(agent, rows):
    """.claude/agents/<name>.md: front matter name, description, skills, side_effects (what B11 reads), and a body."""
    lines = ["---", "name: %s" % agent["name"], "description: %s" % agent["description"],
             "skills: [%s]" % ", ".join(agent["skills"]), "side_effects: [%s]" % ", ".join(agent["side_effects"]), "---", "",
             "# %s" % agent["name"], "", agent["description"].rstrip(".") + ".", "", "## Skills", ""]
    for ref in agent["skills"]:
        r = rows[ref]
        ins = ", ".join("`%s` (%s)" % (i["name"], i["unit"]) for i in r["inputs"]) or "none"
        lines.append("- `%s` (%s, %s): %s. Inputs: %s." % (ref, r["kind"], r["side_effect"], r["summary"], ins))
    if not agent["skills"]:
        lines.append("- none")
    lines += ["", "Read a skill's `SKILL.md` under `skills/` before taking it, and run it only through the runner:", "",
              "```", "python src/run_skill.py <id@vN> < inputs.json", "```", "",
              "Return what the runner printed, unchanged: the outputs, the tool calls and their verdicts.", "",
              "## What you do not do", "",
              "- Take a skill this file does not list, or run a skill's script yourself.",
              "- Type a number a skill would compute, or go on after a refusal: a refusal is returned as it is.",
              "- Write a record, a safety value or a threshold, or commit: you are not a seat.",
              ("- Start a step that changes the device unless the gate lets the call through; the gate is asked on every call."
               if "write_device" in agent["side_effects"] else "- Change a device: nothing you are given can."), ""]
    return "\n".join(lines)


def check_drawing(skills, subagents, tool_names, template_path):
    """Refuse what B11 would fail. `skills` are the library's rows for the refs the specification names."""
    rows, faults = {r["ref"]: r for r in skills}, []
    if skills and not os.path.isfile(os.path.join(template_path, "src", "run_skill.py")):
        faults.append("the template %s has no src/run_skill.py; skills need template v2 or later" % os.path.basename(template_path))
    for ref, r in sorted(rows.items()):
        if r["status"] == "held":
            faults.append("%s is held: it stays in the library and is named in the specification's held[], not in a bundle" % ref)
        for t in r["calls_tools"]:
            if t not in tool_names:
                faults.append("%s calls the tool %s, which this bundle does not have" % (ref, t))
        for other in r["uses_skills"]:
            if other not in rows:
                faults.append("%s uses %s, which the specification does not name" % (ref, other))
    writers = []
    for a in subagents:
        unknown = [e for e in a["side_effects"] if e not in SIDE_EFFECTS]
        if unknown:
            faults.append("subagent %s: side_effects %s are not %s" % (a["name"], unknown, " | ".join(SIDE_EFFECTS)))
        if "write_device" in a["side_effects"]:
            writers.append(a["name"])
            if a["name"] != WRITER:
                faults.append("subagent %s lists write_device; only %s may" % (a["name"], WRITER))
        for ref in a["skills"]:
            if ref not in rows:
                faults.append("subagent %s names %s, which the specification's skills do not" % (a["name"], ref))
            elif rows[ref]["side_effect"] != "none" and rows[ref]["side_effect"] not in a["side_effects"]:
                faults.append("subagent %s names %s, which is %s, and its side_effects are %s"
                              % (a["name"], ref, rows[ref]["side_effect"], a["side_effects"] or "none"))
    if len(writers) > 1:
        faults.append("%s all list write_device; one subagent alone may change a device" % ", ".join(writers))
    if len({a["name"] for a in subagents}) != len(subagents):
        faults.append("a subagent is named twice")
    if faults:
        raise ValueError("the skills and subagents of this specification cannot be built: " + "; ".join(faults))
    return rows


def add_skills(bundle_path, rows, subagents):
    """Copy each skill's folder unchanged and write the subagents' files."""
    for ref, r in sorted(rows.items()):
        shutil.copytree(r["folder"], os.path.join(bundle_path, "skills", ref), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    gk = os.path.join(bundle_path, "skills", ".gitkeep")
    if rows and os.path.exists(gk):
        os.remove(gk)
    for a in subagents:
        cards.write_text(os.path.join(bundle_path, ".claude", "agents", a["name"] + ".md"), subagent_markdown(a, rows))


def compose(template_path, bundle_path, fill, tools, capabilities, envelope, interface_tasks,
            scientific_tasks, replay_items, skills=None, subagents=None):
    """Write the bundle. `tools` is a list of {name, contract, adapter_source, errors:[contract]}.

    `skills` is the library's rows for the `<id>@v<n>` the specification names, in the specification's order
    (src/skills/catalogue.take: each row carries its `folder`), and `subagents` the specification's list of
    {name, description, skills, side_effects}. The drawing is checked before anything is written, and one
    that B11 would fail raises ValueError."""
    if os.path.exists(bundle_path):
        raise FileExistsError("bundle exists: %s (a rebuild is a new build id)" % bundle_path)
    skills, subagents = list(skills or []), list(subagents or [])
    rows = check_drawing(skills, subagents, [t["name"] for t in tools], template_path)
    fill = dict(fill)
    if skills:
        users = {r["ref"]: [a["name"] for a in subagents if r["ref"] in a["skills"]] for r in skills}
        fill["skills_section"] = skills_section(
            [(r["ref"], r["description"].rstrip(".") + "."
              + (" Used by %s." % ", ".join("`%s`" % u for u in users[r["ref"]]) if users[r["ref"]] else "")) for r in skills])
    fill.setdefault("subagents_section", subagents_section(subagents))
    shutil.copytree(template_path, bundle_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    add_skills(bundle_path, rows, subagents)
    claude = cards.read_text(os.path.join(bundle_path, "CLAUDE.md"))
    cards.write_text(os.path.join(bundle_path, "CLAUDE.md"), render(claude, fill))
    cards.write_json(os.path.join(bundle_path, "CAPABILITIES.json"), capabilities)
    for name, content in envelope.items():
        cards.write_json(os.path.join(bundle_path, "envelope", name + ".json"), content)
    for t in tools:
        tdir = os.path.join(bundle_path, "tools", t["name"])
        cards.write_json(os.path.join(tdir, "tool.json"), t["contract"])
        cards.write_text(os.path.join(tdir, "adapter.py"), t["adapter_source"])
        for e in t.get("errors", []):
            cards.write_json(os.path.join(tdir, "errors", e["category"] + ".json"), e)
    gk = os.path.join(bundle_path, "tools", ".gitkeep")
    if tools and os.path.exists(gk):
        os.remove(gk)
    for sub, items in (("validation/interface", interface_tasks), ("validation/scientific", scientific_tasks), ("replay", replay_items)):
        d = os.path.join(bundle_path, *sub.split("/"))
        for item in items:
            cards.write_json(os.path.join(d, item["id"] + ".json"), item)
        gk = os.path.join(d, ".gitkeep")
        if items and os.path.exists(gk):
            os.remove(gk)
    return cards.sha256_tree(bundle_path)


def diff_from_template(template_path, bundle_path):
    """A readable record of what the build changed relative to the template."""
    t_files = set(cards.tree_files(template_path))
    b_files = set(cards.tree_files(bundle_path))
    lines = ["# diff from template", "# template: %s" % os.path.basename(template_path), ""]
    for rel in sorted(b_files - t_files):
        lines.append("added     %s" % rel)
    for rel in sorted(t_files - b_files):
        lines.append("removed   %s" % rel)
    for rel in sorted(t_files & b_files):
        tp, bp = os.path.join(template_path, rel), os.path.join(bundle_path, rel)
        if cards.sha256_file(tp) != cards.sha256_file(bp):
            lines.append("modified  %s" % rel)
    lines.append("")
    for rel in sorted(t_files & b_files):
        tp, bp = os.path.join(template_path, rel), os.path.join(bundle_path, rel)
        if rel.endswith(TEXT_EXT) and cards.sha256_file(tp) != cards.sha256_file(bp):
            a = cards.read_text(tp).splitlines(keepends=True)
            b = cards.read_text(bp).splitlines(keepends=True)
            lines.extend(l.rstrip("\n") for l in difflib.unified_diff(a, b, "template/" + rel, "bundle/" + rel))
            lines.append("")
    return "\n".join(lines) + "\n"


def make_build_card(build_id, rid, spec, lab_profile_ref, template_name, diff_path, bundle_rel, sha, seat, now=None):
    card = cards.skeleton("build", build_id, seat, cards.now_iso(now), rid=rid)
    card["spec_ref"] = spec["id"]
    card["lab_profile_ref"] = lab_profile_ref
    card["template_version"] = template_name
    card["diff_from_template"] = diff_path
    card["bundle_path"] = bundle_rel
    card["bundle_sha256"] = sha
    card["held"] = list(spec.get("held", []))
    card["gate_verdict"] = {"interface": "not_run", "scientific": "not_run", "validation_report_ref": None}
    card["lineage"] = {"parent_build": None, "candidate_of": 1, "k": 1}
    card["landed_at"] = None
    return card
