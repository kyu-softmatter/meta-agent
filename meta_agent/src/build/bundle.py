"""S5 Build: a bundle from the template plus the Designer's outputs, and the build card."""
import difflib
import os
import shutil

from .. import cards

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
    if not skills:
        return "This agent has no skills. A skill, when one is added, is named here with the sentence that triggers it."
    return "\n".join("- `%s`: %s" % (name, trigger) for name, trigger in skills)


def compose(template_path, bundle_path, fill, tools, capabilities, envelope, interface_tasks,
            scientific_tasks, replay_items):
    """Write the bundle. `tools` is a list of {name, contract, adapter_source, errors:[contract]}."""
    if os.path.exists(bundle_path):
        raise FileExistsError("bundle exists: %s (a rebuild is a new build id)" % bundle_path)
    shutil.copytree(template_path, bundle_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
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
