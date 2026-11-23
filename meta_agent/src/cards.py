"""Card skeletons, file writing and hashing shared by the Meta-Agent's stages.

Stages import this module from their parent package (`from .. import cards`);
no stage imports a sibling stage (plan.md 7).
"""
import datetime
import hashlib
import json
import os

SCHEMA_VERSION = "0.1"


def rel_posix(path, start, pathmod=os.path):
    """`path` relative to `start`, in posix form; where the two are on different drives (Windows, a working copy on D:
    and a temporary folder on C:), where no relative path exists, the absolute path in posix form (office-10)."""
    try:
        return pathmod.relpath(path, start).replace(pathmod.sep, "/")
    except ValueError:
        return pathmod.abspath(path).replace(pathmod.sep, "/")


def is_under(path, tree, pathmod=os.path):
    """Whether `path` lies in `tree` (both resolved first); a path on another drive than the tree is not (office-10)."""
    path, tree = pathmod.realpath(path), pathmod.realpath(tree)
    try:
        return pathmod.commonpath([path, tree]) == tree
    except ValueError:
        return False


def now_iso(now=None):
    """An ISO-8601 UTC timestamp; `now` overrides it for reproducible runs."""
    if now:
        return now
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def date_of(iso):
    return iso[:10]


def skeleton(card, card_id, seat, created_at, status="draft", revision=1, rid=None):
    """The common fields every card carries (contracts/schemas/common.schema.json)."""
    d = {
        "card": card,
        "schema_version": SCHEMA_VERSION,
        "id": card_id,
    }
    if rid:
        d["rid"] = rid
    d.update({
        "revision": revision,
        "author": seat,
        "created_at": created_at,
        "numbers": [],
        "assumptions": [],
        "kb_refs": [],
        "kb_gaps": [],
        "case_refs": [],
        "case_gaps": [],
        "degraded": [],
        "status": status,
    })
    return d


def write_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def tree_files(root, skip=(".git", "__pycache__")):
    """Sorted relative paths of every file under root, posix separators."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip)
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            out.append(os.path.relpath(full, root).replace(os.sep, "/"))
    return sorted(out)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root):
    """One digest over a directory: each file's path and content, in sorted order.

    Returns 'sha256:<64 hex>' as the build card's bundle_sha256 wants it.
    """
    h = hashlib.sha256()
    for rel in tree_files(root):
        h.update(rel.encode("utf-8") + b"\0")
        h.update(bytes.fromhex(sha256_file(os.path.join(root, rel))) + b"\0")
    return "sha256:" + h.hexdigest()


def git_text(data):
    """Whether git's `text=auto` takes these bytes for text, as its convert.c does: no NUL, no CR alone, and fewer
    bytes that do not print than one in 128 of those that do (a DOS end-of-file byte at the end not counted)."""
    if b"\0" in data or data.replace(b"\r\n", b"").count(b"\r"):
        return False
    printable = nonprintable = 0
    for c in data:
        if c in (10, 13):
            continue
        if c == 127 or (c < 32 and c not in (8, 9, 12, 27)):
            nonprintable += 1
        else:
            printable += 1
    if data.endswith(b"\x1a"):
        nonprintable -= 1
    return (printable >> 7) >= nonprintable


def lf_tree(root):
    """Write every file under root that git takes for text with LF line endings, as the repository's
    `* text=auto eol=lf` stores it, so that a digest taken over root is one its commit reproduces (office-2).
    A file git takes for binary is left as it was. Returns the relative paths rewritten, sorted."""
    out = []
    for rel in tree_files(root):
        path = os.path.join(root, rel)
        with open(path, "rb") as f:
            data = f.read()
        if b"\r\n" in data and git_text(data):
            with open(path, "wb") as f:
                f.write(data.replace(b"\r\n", b"\n"))
            out.append(rel)
    return out


def short_hash(text, n=12):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]
