"""The versioned bundle template (plan.md 5.1 S5).

The source trees live in template_v<N>/ next to this file, one folder per
version; a changed template is a new folder and the old one stays.
`materialize` copies a version to templates/agent@<hash>/, where the hash
is over every file's path and content, so a changed template gets a new
name and an old one is never edited in place. A build uses the latest
version unless it names another.

v1  the first bundle (tasks/002).
v2  adds src/run_skill.py, the Skills section's runner and the Subagents
    section of CLAUDE.md (tasks/010).
v3  adds three session skills under .claude/skills/ (tasks/015): run-skill,
    the one that sends the bundle's session to src/run_skill.py and says
    what a session may and may not change, with library/ beside it, where
    a build renders one reference page per library skill; and
    classify-knowledge and choose-session-level, adapted to a bundle.
    Bundle check B15 judges a bundle of this version or later.
"""
import os
import shutil

from .. import cards

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = {"v1": os.path.join(HERE, "template_v1"), "v2": os.path.join(HERE, "template_v2"),
           "v3": os.path.join(HERE, "template_v3")}
LATEST = "v3"
SOURCE = SOURCES[LATEST]


def template_hash(root=SOURCE):
    digest = cards.sha256_tree(root)
    return digest.split(":", 1)[1][:12]


def template_name(root=SOURCE):
    return "agent@" + template_hash(root)


def materialize(templates_root, root=SOURCE):
    """Copy the template into templates_root/agent@<hash>/ unless it is already there.
    Returns (name, path)."""
    name = template_name(root)
    dest = os.path.join(templates_root, name)
    if not os.path.isdir(dest):
        shutil.copytree(root, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return name, dest
