"""Render the wiki view and the card ontology from the cards (tasks/003, plan.md 5.2).

    python -m meta_agent.src.wiki [--root REPO] [--out DIR]

The cards are the record; this is a view of them. Every run rewrites the view from the cards in a fixed
order, so two runs on one tree write identical bytes. A page carries no number, claim or relation that no
card holds (check 18): numbers appear as the card's own values, card text appears verbatim in code spans,
and a link exists only where one record names the other.

Besides the pages and ontology.owl it writes graph.html (tasks/004): the same nodes and edges drawn in 3D
with a 2D switch by graph_template.html, which loads nothing from outside.

Nodes: one per card revision, named <id>@r<revision>, and one per artifact a card points at (a template
directory, a bundle directory). Edges: a revision N > 1 supersedes N - 1; any string field whose value is
another card's id (linked to that card's latest revision), the file name of a card in the same folder, a
template version or a bundle path.
"""
import argparse
import json
import os
import re
from collections import defaultdict
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

SKIP_PARTS = {"bundle", "templates", "src", "tests", ".claude", "envelope", "wiki", "__pycache__", ".git"}
NOT_A_REFERENCE = {"id", "card", "supersedes", "superseded_by"}
SUMMARY_KEYS = ("purpose", "science_task", "subject", "claim", "symbol", "lab_id", "rid", "environment",
                "overall", "gate_verdict", "held", "landed_at", "template_version", "bundle_sha256")
GAP_KEYS = ("gaps", "kb_gaps", "case_gaps")
NS = "https://github.com/kyu-softmatter/meta-agent/ontology#"
GRAPH_TEMPLATE = os.path.join(HERE, "graph_template.html")
OWN_FILES = (".md", ".owl", "graph.html")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def safe(text):
    return re.sub(r"[^A-Za-z0-9@._-]+", "-", text).strip("-")


def code(value):
    """A card value, verbatim, as one code span."""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "`%s`" % value.replace("`", "'").replace("\r", " ").replace("\n", " ")


def strings(obj, path=()):
    if isinstance(obj, dict):
        for k in sorted(obj):
            yield from strings(obj[k], path + (k,))
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v, path)
    elif isinstance(obj, str):
        yield path, obj


def relation_name(path):
    """The key a reference sits under; a short code such as A1 inside axis_refs names its parent."""
    keys = [k for k in path if isinstance(k, str)]
    for k in reversed(keys):
        if not re.match(r"^[A-Z][0-9]+$", k):
            return k
    return keys[-1] if keys else "ref"


def scan(root):
    """[(root-relative path, card)] for every card under meta_agent/, outside bundles, templates, src and tests."""
    meta = os.path.join(root, "meta_agent")
    found = []
    for d, dirs, files in os.walk(meta):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_PARTS)
        for name in sorted(files):
            if not name.endswith(".json"):
                continue
            p = os.path.join(d, name)
            try:
                data = load_json(p)
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(data, dict) and isinstance(data.get("card"), str) and data.get("id"):
                found.append((rel(p, root), data))
    return found


def node_of(card):
    return "%s@r%d" % (card["id"], card.get("revision", 1))


def build_graph(root):
    """(nodes, edges): nodes by name, edges as sorted (source, relation, target)."""
    cards = scan(root)
    nodes = {}
    latest = {}
    by_path = {}
    for p, c in cards:
        n = node_of(c)
        nodes[n] = {"kind": "card", "path": p, "card": c}
        by_path[p] = n
        cur = latest.get(c["id"])
        if cur is None or c.get("revision", 1) > nodes[cur]["card"].get("revision", 1):
            latest[c["id"]] = n
    edges = set()
    for p, c in cards:
        src = node_of(c)
        rev = c.get("revision", 1)
        if rev > 1:
            prev = "%s@r%d" % (c["id"], rev - 1)
            if prev in nodes:
                edges.add((src, "supersedes", prev))
        folder = p.rsplit("/", 1)[0]
        for path, val in strings(c):
            if path and path[-1] in NOT_A_REFERENCE:
                continue
            leaf = path[-1] if path else ""
            if leaf == "template_version":
                tdir = "meta_agent/templates/" + val
                if os.path.isdir(os.path.join(root, tdir)):
                    name = "template-" + safe(val)
                    nodes.setdefault(name, {"kind": "artifact", "path": tdir, "type": "template"})
                    edges.add((src, leaf, name))
                continue
            if leaf == "bundle_path":
                if os.path.isdir(os.path.join(root, val)):
                    tail = val[len("meta_agent/builds/"):] if val.startswith("meta_agent/builds/") else val
                    tail = tail[:-len("/bundle")] if tail.endswith("/bundle") else tail
                    name = "bundle-" + safe(tail)
                    nodes.setdefault(name, {"kind": "artifact", "path": val.rstrip("/"), "type": "bundle"})
                    edges.add((src, leaf, name))
                continue
            target = None
            if val in latest and val != c["id"]:
                target = latest[val]
            elif (folder + "/" + val) in by_path and by_path[folder + "/" + val] != src:
                target = by_path[folder + "/" + val]
            if target and nodes[target]["card"]["id"] != c["id"]:
                edges.add((src, relation_name(path), target))
    return nodes, sorted(edges)


def card_page(name, node, out_edges, in_edges):
    c = node["card"]
    lines = ["# %s" % name, "",
             "- card: %s" % code(c["card"]),
             "- revision: %s" % code(str(c.get("revision", 1))),
             "- status: %s" % code(c.get("status", "")),
             "- author: %s" % code(c.get("author", "")),
             "- created: %s" % code(c.get("created_at", "")),
             "- record: `%s`" % node["path"], ""]
    summary = [(k, c[k]) for k in SUMMARY_KEYS if k in c and c[k] not in (None, "", [], {})]
    tool = c.get("tool")
    if isinstance(tool, dict) and tool.get("name"):
        summary.append(("tool", tool["name"]))
    if summary:
        lines += ["## Summary", ""] + ["- %s: %s" % (k, code(v)) for k, v in summary] + [""]
    nums = [n for n in c.get("numbers", []) if isinstance(n, dict)]
    if nums:
        lines += ["## Numbers", ""]
        for n in nums:
            v = n.get("value")
            shown = repr(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else code(v)
            lines.append("- %s = %s, unit %s, grade %s, %s, source %s" % (
                code(n.get("name", "")), shown, code(n.get("unit", "")), code(n.get("grade", "")),
                code(n.get("value_kind", "")), code(n.get("source", ""))))
        lines.append("")
    claims = [x for x in c.get("claims", []) if isinstance(x, dict)]
    if claims:
        lines += ["## Claims", ""]
        lines += ["- %s from %s: %s" % (code(x.get("kind", "")), code(x.get("basis", "")), code(x.get("claim", "")))
                  for x in claims] + [""]
    gaps = []
    for k in GAP_KEYS:
        for g in c.get(k, []) or []:
            if isinstance(g, dict):
                gaps.append("- %s: %s" % (k, code(g.get("what") or g.get("need") or g.get("reason") or g)))
    if gaps:
        lines += ["## Gaps", ""] + gaps + [""]
    lines += ["## Points to", ""] + (["- %s: [[%s]]" % (r, t) for r, t in out_edges] or ["- nothing"]) + [""]
    lines += ["## Pointed to by", ""] + (["- [[%s]] via %s" % (s, code(r)) for r, s in in_edges] or ["- nothing"]) + [""]
    return "\n".join(lines)


def artifact_page(name, node, in_edges):
    lines = ["# %s" % name, "", "- artifact: %s" % code(node["type"]), "- record: `%s`" % node["path"], "",
             "## Pointed to by", ""] + ["- [[%s]] via %s" % (s, code(r)) for r, s in in_edges] + [""]
    return "\n".join(lines)


def index_page(nodes):
    groups = defaultdict(list)
    for name, n in nodes.items():
        groups[n["card"]["card"] if n["kind"] == "card" else "artifact: " + n["type"]].append(name)
    lines = ["# Index", "",
             "A view rendered from the cards under `meta_agent/` by `python -m meta_agent.src.wiki`. "
             "The cards are the record: never edit a page, render again.", ""]
    for g in sorted(groups):
        lines += ["## %s" % g, ""] + ["- [[%s]]" % n for n in sorted(groups[g])] + [""]
    return "\n".join(lines)


def ontology(root, nodes, edges):
    """RDF/XML: one owl:Class per card schema and artifact kind, one owl:ObjectProperty per (domain, relation, range)."""
    schemas = os.path.join(root, "contracts", "schemas")
    classes = {}
    if os.path.isdir(schemas):
        for f in sorted(os.listdir(schemas)):
            if f.endswith(".schema.json") and f != "common.schema.json":
                s = load_json(os.path.join(schemas, f))
                classes[f[:-len(".schema.json")]] = s.get("description", "")
    for n in nodes.values():
        key = n["card"]["card"] if n["kind"] == "card" else n["type"]
        classes.setdefault(key, "an artifact directory a card points at" if n["kind"] == "artifact" else "")
    kind = {name: (n["card"]["card"] if n["kind"] == "card" else n["type"]) for name, n in nodes.items()}
    props = sorted({(kind[s], r, kind[t]) for s, r, t in edges})
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
         '         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"',
         '         xmlns:owl="http://www.w3.org/2002/07/owl#">',
         '  <owl:Ontology rdf:about="%s">' % NS[:-1],
         '    <rdfs:label>meta-agent cards</rdfs:label>',
         '    <rdfs:comment>The card types of contracts/schemas and the references the cards under meta_agent/ hold, '
         'rendered by python -m meta_agent.src.wiki. A view, not a record.</rdfs:comment>',
         '  </owl:Ontology>']
    for k in sorted(classes):
        x.append('  <owl:Class rdf:about="%s%s">' % (NS, safe(k)))
        x.append('    <rdfs:label>%s</rdfs:label>' % escape(k))
        if classes[k]:
            x.append('    <rdfs:comment>%s</rdfs:comment>' % escape(classes[k]))
        x.append('  </owl:Class>')
    for d, r, t in props:
        x.append('  <owl:ObjectProperty rdf:about="%s%s">' % (NS, safe("%s.%s.%s" % (d, r, t))))
        x.append('    <rdfs:label>%s</rdfs:label>' % escape(r))
        x.append('    <rdfs:domain rdf:resource="%s%s"/>' % (NS, safe(d)))
        x.append('    <rdfs:range rdf:resource="%s%s"/>' % (NS, safe(t)))
        x.append('  </owl:ObjectProperty>')
    x.append("</rdf:RDF>")
    return "\n".join(x) + "\n", len(classes), len(props)


def graph_html(nodes, edges):
    """graph.html (tasks/004): the template with the same nodes and edges as the pages, nothing from outside."""
    data = {"nodes": [{"id": name, "card": n["card"]["card"] if n["kind"] == "card" else n["type"],
                       "status": n["card"].get("status", "") if n["kind"] == "card" else "artifact"}
                      for name, n in sorted(nodes.items())],
            "edges": [list(e) for e in edges]}
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
    with open(GRAPH_TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    assert template.count("__WIKI_GRAPH_DATA__") == 1
    return template.replace("__WIKI_GRAPH_DATA__", blob), len(data["nodes"]), len(data["edges"])


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def render(root=REPO, out=None):
    root = os.path.abspath(root)
    out = os.path.abspath(out or os.path.join(root, "meta_agent", "wiki"))
    nodes, edges = build_graph(root)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):  # the view's own files only; .obsidian/ and the like stay
        if f.endswith(OWN_FILES) and os.path.isfile(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    out_e, in_e = defaultdict(list), defaultdict(list)
    for s, r, t in edges:
        out_e[s].append((r, t))
        in_e[t].append((r, s))
    for name in sorted(nodes):
        n = nodes[name]
        text = card_page(name, n, out_e[name], in_e[name]) if n["kind"] == "card" else artifact_page(name, n, in_e[name])
        write(os.path.join(out, name + ".md"), text)
    write(os.path.join(out, "index.md"), index_page(nodes))
    owl, n_classes, n_props = ontology(root, nodes, edges)
    write(os.path.join(out, "ontology.owl"), owl)
    html, g_nodes, g_edges = graph_html(nodes, edges)
    write(os.path.join(out, "graph.html"), html)
    return {"out": out, "pages": len(nodes) + 1, "graph_nodes": g_nodes, "graph_edges": g_edges,
            "cards": sum(1 for n in nodes.values() if n["kind"] == "card"),
            "artifacts": sum(1 for n in nodes.values() if n["kind"] == "artifact"),
            "references": len(edges),
            "card_types": len({n["card"]["card"] for n in nodes.values() if n["kind"] == "card"}),
            "relations": len({r for _, r, _ in edges}), "classes": n_classes, "properties": n_props}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the wiki view and the card ontology from the cards.")
    ap.add_argument("--root", default=REPO, help="the repository root (default: this repository)")
    ap.add_argument("--out", default=None, help="the view's folder (default: <root>/meta_agent/wiki)")
    a = ap.parse_args(argv)
    r = render(a.root, a.out)
    where = rel(r["out"], os.path.abspath(a.root))
    print("wiki: %d pages (%d card revisions, %d artifacts, an index), %d references, %d card types, "
          "%d relation names -> %s/" % (r["pages"], r["cards"], r["artifacts"], r["references"], r["card_types"],
                                        r["relations"], where))
    print("ontology: %d classes, %d object properties -> %s/ontology.owl" % (r["classes"], r["properties"], where))
    print("map: %d nodes, %d edges, 3D with a 2D switch, no library -> %s/graph.html" % (
        r["graph_nodes"], r["graph_edges"], where))
    return 0
