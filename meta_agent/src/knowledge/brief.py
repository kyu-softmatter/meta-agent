"""S3 Recall / Scan, the knowledge half: deterministic matching in knowledge/ (plan.md 5.1).

No model judgement here: an entry matches a need when every word of the
need appears in the entry's title or tags. What was searched is written
down whether or not anything was found, so a gap names where it looked.
The cases half is src/cases/recall.py, which the Designer calls beside this.
"""
import os
import re

from .. import cards

WORD = re.compile(r"[a-z0-9]+")


def words(text):
    return set(WORD.findall((text or "").lower()))


def rel_repo(path, root):
    """A repository-relative posix path: root is the meta_agent/ tree."""
    return os.path.relpath(path, os.path.dirname(os.path.abspath(root))).replace(os.sep, "/")


def kb_version(knowledge_root):
    """A pin over the knowledge tree's content; an absent tree pins to the empty digest."""
    if os.path.isdir(knowledge_root):
        return "kb@" + cards.sha256_tree(knowledge_root).split(":", 1)[1][:12]
    return "kb@" + cards.short_hash("")


def load_cards(root, card):
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in (".git", "__pycache__"))
        for fn in sorted(filenames):
            if fn.endswith(".json"):
                try:
                    d = cards.load_json(os.path.join(dirpath, fn))
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("card") == card:
                    out.append((os.path.join(dirpath, fn), d))
    return out


def recall_entries(needs, root):
    knowledge_root = os.path.join(root, "knowledge")
    entries_root = os.path.join(knowledge_root, "entries")
    searched = [rel_repo(p, root) for p in (entries_root, os.path.join(knowledge_root, "distilled")) if os.path.isdir(p)]
    found, gaps = [], []
    entries = load_cards(entries_root, "kb_entry")
    for need in needs:
        nw = words(need)
        hits = []
        for path, e in entries:
            hay = words(e.get("title")) | set(w for t in (e.get("tags") or []) for w in words(t))
            if nw and nw <= hay:
                hits.append({"id": e["id"], "version": str(e.get("version") or e.get("revision") or 1),
                             "hash": "sha256:" + cards.sha256_file(path), "path": rel_repo(path, root)})
        if hits:
            found.extend(h for h in hits if h not in found)
        else:
            gaps.append({"what": need, "searched": searched or [rel_repo(entries_root, root) + " (absent)"],
                         "reason": "no entry whose title or tags carry every word of the need" if entries else "no knowledge entries yet",
                         "requires": "a source record and a distilled entry for this need"})
    return found, gaps


def make_brief(goal, root, seat, now=None):
    """Return the knowledge_brief card; root is the meta_agent/ tree."""
    knowledge_root = os.path.join(root, "knowledge")
    needs = list(goal.get("knowledge_needs") or [])
    entries, kb_gaps = recall_entries(needs, root)
    brief = cards.skeleton("knowledge_brief", "kb-brief-" + goal["rid"].replace("req-", ""), seat, cards.now_iso(now), rid=goal["rid"])
    brief["need"] = needs
    brief["kb_version"] = kb_version(knowledge_root)
    brief["entries"] = entries
    brief["gaps"] = kb_gaps
    brief["status"] = "validated"
    if not needs:
        brief["note"] = "the goal names no knowledge need; the snapshot pins the knowledge version and copies no entry"
    return brief
