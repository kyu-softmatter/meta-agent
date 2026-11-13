#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/session_skills.py -- what a session skill is and how it is judged
(plan.md 14-37; meta_agent/tasks/015).

  python contracts/tools/session_skills.py check SKILL_DIR     every problem check 24 would name, for one session skill
  python contracts/tools/session_skills.py list [TREE]         the session skills of a tree, with where each is named

Two things carry the word skill. A library skill is source code with a manifest and worked cases, in a
folder `<id>@v<n>/` under a folder named `skills/`; contracts/tools/skills.py and check 22 judge it. A
session skill is a procedure a session loads when its description matches what it is about to do: a folder
`.claude/skills/<name>/` holding a `SKILL.md`. This file judges the second kind, and the gate's check 24 and
bundle check B15 call it, so that the tool and the gate are one rule.

What check 24 asks of a session skill:

  - the folder holds a SKILL.md whose front matter has `name` and `description`; the name is the folder's;
  - what it tells a session to run or read exists: a path named in a code span or a code block, a script
    after `python`, a module after `python -m` whose package is in the tree. A token with a placeholder
    (`<`, `>`, `*`, `{`, an ellipsis) is not a path, and text inside double quotes is a message, not a path.
    A path is looked for from the folder that holds `.claude/` and from the skill's own folder;
  - a CLAUDE.md beside the `.claude/` folder, or one folder below it, names the skill in a code span: a
    session is told that the skill exists by a file it reads whole;
  - it carries no number outside code: a limit, a threshold or a count is the person's or a card's and is
    never a procedure's. Ordered-list markers and code are not read.

It cannot check that a rule is also in a CLAUDE.md; that stays the design seat's reading.

What B15 asks of a bundle built from template version v3 or later (the person, 2026-11-12: the agents
this agent builds work from skills): exactly one of its session skills names a script under `src/` that
exists, the bundle's runner, so that one skill and no more sends the session there; it may carry other
session skills beside it (how a session's model and effort are chosen, how a piece of knowledge is
classified); no library skill sits under `.claude/skills/`, since a page is not a trigger; and every
session skill passes what check 24 asks. A bundle of an earlier template is not judged by it.

Standard library only.
"""
import json
import os
import re
import sys

FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
FENCE_RE = re.compile(r"^[ \t]*```[^\n]*\n(.*?)^[ \t]*```[ \t]*$", re.S | re.M)
SPAN_RE = re.compile(r"`([^`\n]+)`")
QUOTED_RE = re.compile(r'"[^"\n]*"')
PATH_RE = re.compile(r"^(?:\.{1,2}/)?\.?[A-Za-z0-9_@-][A-Za-z0-9_.@-]*(?:/[A-Za-z0-9_.@-]+)*/?$")
MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
PLACEHOLDER = set("<>*{}|=…")
NUM_RE = re.compile(r"(?<![\w./:+-])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w/:%-])")
LIST_MARK_RE = re.compile(r"^\s*\d+\.\s", re.M)
URL_RE = re.compile(r"https?://\S+")
SRC_SCRIPT_RE = re.compile(r"\bsrc/[A-Za-z0-9_./-]+\.py\b")
VERSION_RE = re.compile(r"^v([1-9][0-9]*)$")
B15_FROM = 3
SKIP_DIRS = (".git", "__pycache__", "node_modules", ".venv", ".pixi", ".agent")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def front_matter(text):
    m = FRONT_RE.match(text)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def find_skills_dirs(tree, skip=()):
    """Every `.claude/skills` folder under the tree, as (root, skills_dir): root is the folder holding `.claude`."""
    out = []
    skip = [os.path.abspath(s) for s in skip]
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if any(os.path.abspath(root).startswith(s) for s in skip):
            dirs[:] = []
            continue
        sdir = os.path.join(root, ".claude", "skills")
        if os.path.isdir(sdir):
            out.append((root, sdir))
    return out


def skill_dirs(skills_dir):
    return [os.path.join(skills_dir, n) for n in sorted(os.listdir(skills_dir)) if os.path.isdir(os.path.join(skills_dir, n))]


def code_of(text):
    """The text a session would run or open: fenced blocks and code spans, double-quoted messages removed."""
    parts = [m.group(1) for m in FENCE_RE.finditer(text)]
    parts += SPAN_RE.findall(FENCE_RE.sub("", text))
    return [QUOTED_RE.sub(" ", p) for p in parts]


def prose_of(text):
    """What is left when code is taken out: where a number would be a statement of the skill's own."""
    t = FENCE_RE.sub("", text)
    t = SPAN_RE.sub(" ", t)
    t = URL_RE.sub(" ", t)
    return LIST_MARK_RE.sub(" ", t)


def _exists(root, skill_dir, token):
    return any(os.path.exists(os.path.join(base, *token.rstrip("/").split("/"))) for base in (root, skill_dir))


def _module_missing(root, module):
    parts = module.split(".")
    if not os.path.exists(os.path.join(root, parts[0])) and not os.path.exists(os.path.join(root, parts[0] + ".py")):
        return False  # not a package of this tree: the standard library or an installed one, not judged here
    base = os.path.join(root, *parts)
    return not (os.path.isfile(base + ".py") or os.path.isfile(os.path.join(base, "__main__.py"))
                or os.path.isfile(os.path.join(base, "__init__.py")))


def named_missing(root, skill_dir, text):
    """Paths, scripts and modules the skill names that are not there, in the order met, once each."""
    missing = []
    for chunk in code_of(text):
        tokens = []
        for t in chunk.split():
            t = t.strip("()[],;:")
            if len(t) > 1 and t.endswith(".") and not t.endswith(".."):
                t = t[:-1]   # a sentence's full stop, not part of a path
            tokens.append(t)
        for i, tok in enumerate(tokens):
            if not tok or PLACEHOLDER & set(tok):
                continue
            prev = tokens[i - 1] if i else ""
            prev2 = tokens[i - 2] if i > 1 else ""
            what = None
            if prev == "-m" and prev2.startswith("python"):
                if MODULE_RE.match(tok) and _module_missing(root, tok):
                    what = "the module %s" % tok
            elif "/" in tok and PATH_RE.match(tok):
                if not _exists(root, skill_dir, tok):
                    what = tok
            elif prev.startswith("python") and tok.endswith(".py") and PATH_RE.match(tok):
                if not _exists(root, skill_dir, tok):
                    what = tok
            if what and what not in missing:
                missing.append(what)
    return missing


def naming_files(root):
    """The CLAUDE.md files that may tell a session a skill exists: beside `.claude/`, or one folder below."""
    out = []
    here = os.path.join(root, "CLAUDE.md")
    if os.path.isfile(here):
        out.append(here)
    for n in sorted(os.listdir(root)):
        p = os.path.join(root, n, "CLAUDE.md")
        if n not in SKIP_DIRS and not n.startswith(".") and os.path.isfile(p):
            out.append(p)
    return out


def named_in(root, name):
    token = "`%s`" % name
    return [p for p in naming_files(root) if token in read(p)]


def problems(root, skill_dir):
    """Every problem of one session skill, as messages. `root` is the folder that holds `.claude/`."""
    folder = os.path.basename(os.path.normpath(skill_dir))
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(path):
        return ["no SKILL.md"]
    text = read(path)
    out = []
    fm = front_matter(text)
    if not FRONT_RE.match(text):
        out.append("SKILL.md has no front matter")
    name = fm.get("name")
    if not name:
        out.append("front matter has no name")
    elif name != folder:
        out.append("front matter name %r is not the folder's, %r" % (name, folder))
    elif not NAME_RE.match(name):
        out.append("name %r is not lower-case words joined by hyphens" % name)
    if not fm.get("description"):
        out.append("front matter has no description, so nothing says when the skill is loaded")
    for what in named_missing(root, skill_dir, text):
        out.append("names %s, which is not in the tree" % what)
    if not named_in(root, folder):
        out.append("no CLAUDE.md beside .claude/ or one folder below names `%s`" % folder)
    numbers = NUM_RE.findall(prose_of(text))
    if numbers:
        out.append("carries a number outside code (%s): a limit, a threshold or a count is not a procedure's"
                   % ", ".join(numbers[:5]))
    return out


def judge(tree, skip=()):
    """Check 24 over a tree: (path, message) per problem."""
    out = []
    for root, sdir in find_skills_dirs(tree, skip):
        for d in skill_dirs(sdir):
            for msg in problems(root, d):
                out.append((d, msg))
    return out


def template_version(bundle):
    try:
        data = json.loads(read(os.path.join(bundle, "TEMPLATE.json")))
    except (OSError, ValueError):
        return None
    m = VERSION_RE.match(str(data.get("version", ""))) if isinstance(data, dict) else None
    return int(m.group(1)) if m else None


def bundle_problems(bundle):
    """B15 over one bundle: (relative path, message) per problem. Empty for a bundle of an earlier template."""
    version = template_version(bundle)
    if version is None or version < B15_FROM:
        return []
    sdir = os.path.join(bundle, ".claude", "skills")
    dirs = skill_dirs(sdir) if os.path.isdir(sdir) else []
    out = []
    library = [d for d in dirs if os.path.isfile(os.path.join(d, "skill.json"))]
    for d in library:
        out.append((".claude/skills/%s" % os.path.basename(d),
                    "a library skill sits where a session loads skills: a page is not a trigger"))
    session = [d for d in dirs if d not in library]
    runners = []
    for d in session:
        rel = ".claude/skills/%s" % os.path.basename(d)
        for msg in problems(bundle, d):
            out.append((rel, msg))
        path = os.path.join(d, "SKILL.md")
        text = read(path) if os.path.isfile(path) else ""
        scripts = sorted(set(SRC_SCRIPT_RE.findall(text)))
        if [s for s in scripts if os.path.isfile(os.path.join(bundle, *s.split("/")))]:
            runners.append(os.path.basename(d))
    if not runners:
        out.append((".claude/skills", "a bundle of template v%d has %d session skill(s) and none names a script under src/ that exists: "
                    "nothing sends its session to the runner" % (version, len(session))))
    elif len(runners) > 1:
        out.append((".claude/skills", "%s all name a script under src/; exactly one session skill sends the session to the runner"
                    % ", ".join(runners)))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "list" and len(argv) <= 2:
        tree = os.path.abspath(argv[1] if len(argv) == 2 else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        for root, sdir in find_skills_dirs(tree, skip=[os.path.join(tree, "contracts", "examples")]):
            for d in skill_dirs(sdir):
                name = os.path.basename(d)
                where = [os.path.relpath(p, tree).replace(os.sep, "/") for p in named_in(root, name)]
                print("%-28s %s   named in %s" % (name, os.path.relpath(d, tree).replace(os.sep, "/"), ", ".join(where) or "no CLAUDE.md"))
        return 0
    if len(argv) != 2 or argv[0] != "check":
        print(__doc__)
        return 2
    skill_dir = os.path.abspath(argv[1])
    root = os.path.dirname(os.path.dirname(os.path.dirname(skill_dir)))  # <root>/.claude/skills/<name>
    found = problems(root, skill_dir)
    for msg in found:
        print(msg)
    if not found:
        print("nothing to say")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
