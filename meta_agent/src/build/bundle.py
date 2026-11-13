"""S5 Build: a bundle from the template plus the Designer's outputs, and the build card.

Skills and subagents (plan.md 14-31, 14-34; tasks/010): the skills a specification names are copied from
the library into the bundle's skills/<id>@v<n>/ unchanged, and each subagent it names becomes
.claude/agents/<name>.md with the skills and the side effects it may use. The caller reads the library
(src/skills/catalogue.take) and hands the rows in; this stage imports no sibling stage (plan.md 7). What
check B11 would fail in the finished bundle is refused here, before anything is written: a held skill (it
is named in the specification's skills and held[], and stays out of the bundle), a skill whose tool the
bundle does not have or that uses a skill the specification does not name, a skill that says it only reads
and calls a tool that changes something, a subagent whose side effects do not cover its skills, and a
second subagent that may change a device.

The session skills (plan.md 14-37(i); tasks/015): a template of version v3 or later carries them under
.claude/skills/, and the build copies them unchanged. One of them, run-skill, sends the bundle's session
to src/run_skill.py, and it is the only one that names a script under src/ (B15). The build renders its
library/ folder from the manifests of the skills it copied: index.md, and one reference page
per library skill. A page is rendered, never written by hand, and is not a trigger: the sentence that
says when a skill applies stays in CLAUDE.md (B8).
"""
import difflib
import json
import os
import shutil

from .. import cards

WRITER = "operator"        # the one subagent that may list write_device (plan.md 14-34(e))
SESSION_SKILL = "run-skill"   # the one session skill that names the runner, from template v3 on (tasks/015)
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
        return ("This agent has no library skill. A library skill, when a build adds one, is named here with the sentence "
                "that triggers it.")
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


def front_value(text):
    """One line of front matter. A value YAML would not read as plain text (a colon and a space, a quote, a
    leading mark) is written as a quoted string."""
    text = " ".join(str(text).split())
    plain = text and ": " not in text and " #" not in text and '"' not in text and text[0] not in "[{>|*&!%@`'#-?:,"
    return text if plain else json.dumps(text, ensure_ascii=False)


def subagent_markdown(agent, rows):
    """.claude/agents/<name>.md: front matter name, description, skills, side_effects (what B11 reads), and a body."""
    lines = ["---", "name: %s" % agent["name"], "description: %s" % front_value(agent["description"]),
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


def session_skill_dir(tree):
    """The folder of the session skill in a template or a bundle, or None before template v3."""
    d = os.path.join(tree, ".claude", "skills", SESSION_SKILL)
    return d if os.path.isfile(os.path.join(d, "SKILL.md")) else None


def _named(items):
    """`name` (unit): meaning, one line per input or output of a manifest."""
    out = []
    for i in items or []:
        line = "- `%s` (%s)" % (i["name"], i.get("unit", "1"))
        if i.get("meaning"):
            line += ": %s" % str(i["meaning"]).rstrip(".") + "."
        out.append(line)
    return out or ["- none"]


def skill_page(ref, manifest):
    """One reference page for one library skill, from its manifest and nothing else."""
    lines = ["# `%s`" % ref, "",
             "Rendered by the build from `skills/%s/skill.json`; never edited by hand. This page is reference and not a "
             "trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` "
             "is beside its manifest." % ref, "",
             "- **Gives:** %s." % str(manifest.get("summary", "")).rstrip("."),
             "- **Kind:** %s. **Side effect:** %s. **Status:** %s." % (manifest.get("kind"), manifest.get("side_effect"),
                                                                    manifest.get("status")),
             "- **Calls tools:** %s." % (", ".join("`%s`" % t for t in manifest.get("calls_tools") or []) or "none"),
             "- **Uses skills:** %s." % (", ".join("`%s`" % t for t in manifest.get("uses_skills") or []) or "none")]
    if manifest.get("validity"):
        lines.append("- **Valid for:** %s." % str(manifest["validity"]).rstrip("."))
    lines += ["", "## Inputs", ""] + _named(manifest.get("inputs"))
    lines += ["", "## Outputs", ""] + _named(manifest.get("outputs"))
    lines += ["", "## Run", "", "```", "python src/run_skill.py %s < inputs.json" % ref, "```", ""]
    return "\n".join(lines)


def library_index(manifests):
    """library/index.md: every library skill of the bundle with its page. `manifests` is [(ref, manifest)]."""
    lines = ["# Library skills of this agent", ""]
    if not manifests:
        lines += ["This agent has no library skill. When a build gives it one, the skill is listed here with its page.", ""]
        return "\n".join(lines)
    lines += ["Rendered by the build from the manifests under `skills/`; never edited by hand. Each skill has a page "
              "beside this file, named after it.", ""]
    for ref, m in manifests:
        lines.append("- `%s` (%s, %s, %s): %s. Page: `%s.md`." % (ref, m.get("kind"), m.get("side_effect"), m.get("status"),
                                                               str(m.get("summary", "")).rstrip("."), ref))
    lines.append("")
    return "\n".join(lines)


def add_pages(bundle_path, refs):
    """Render the session skill's library/ from the manifests the bundle carries. Nothing before template v3."""
    sdir = session_skill_dir(bundle_path)
    if sdir is None:
        return []
    manifests = [(ref, cards.load_json(os.path.join(bundle_path, "skills", ref, "skill.json"))) for ref in refs]
    cards.write_text(os.path.join(sdir, "library", "index.md"), library_index(manifests))
    for ref, m in manifests:
        cards.write_text(os.path.join(sdir, "library", ref + ".md"), skill_page(ref, m))
    return [ref for ref, _ in manifests]


READ_ONLY_TOOLS = (None, "none", "reads_instrument")


def check_drawing(skills, subagents, tool_effects, template_path):
    """Refuse what B11 would fail. `skills` are the library's rows for the skills the bundle is to carry and
    `tool_effects` is {tool name: its contract's side_effects} for the tools the bundle has."""
    rows, faults = {r["ref"]: r for r in skills}, []
    if skills and not os.path.isfile(os.path.join(template_path, "src", "run_skill.py")):
        faults.append("the template %s has no src/run_skill.py; skills need template v2 or later" % os.path.basename(template_path))
    for ref, r in sorted(rows.items()):
        if r["status"] == "held":
            faults.append("%s is held: it stays in the library and is named in the specification's held[], not in a bundle" % ref)
        for t in r["calls_tools"]:
            if t not in tool_effects:
                faults.append("%s calls the tool %s, which this bundle does not have" % (ref, t))
            elif r["side_effect"] == "read_device" and tool_effects[t] not in READ_ONLY_TOOLS:
                faults.append("%s says it only reads the device and calls %s, a tool with side effects %s" % (ref, t, tool_effects[t]))
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
    rows = check_drawing(skills, subagents, {t["name"]: t["contract"].get("side_effects") for t in tools}, template_path)
    fill = dict(fill)
    if skills:
        users = {r["ref"]: [a["name"] for a in subagents if r["ref"] in a["skills"]] for r in skills}
        fill["skills_section"] = skills_section(
            [(r["ref"], r["description"].rstrip(".") + "."
              + (" Used by %s." % ", ".join("`%s`" % u for u in users[r["ref"]]) if users[r["ref"]] else "")) for r in skills])
    fill.setdefault("subagents_section", subagents_section(subagents))
    shutil.copytree(template_path, bundle_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    add_skills(bundle_path, rows, subagents)
    add_pages(bundle_path, [r["ref"] for r in skills])
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


def make_build_card(build_id, rid, spec, lab_profile_ref, template_name, diff_path, bundle_rel, sha, seat, now=None,
                    parent_build=None):
    card = cards.skeleton("build", build_id, seat, cards.now_iso(now), rid=rid)
    card["spec_ref"] = spec["id"]
    card["lab_profile_ref"] = lab_profile_ref
    card["template_version"] = template_name
    card["diff_from_template"] = diff_path
    card["bundle_path"] = bundle_rel
    card["bundle_sha256"] = sha
    card["held"] = list(spec.get("held", []))
    card["gate_verdict"] = {"interface": "not_run", "scientific": "not_run", "validation_report_ref": None}
    card["lineage"] = {"parent_build": parent_build, "candidate_of": 1, "k": 1}
    card["landed_at"] = None
    return card
