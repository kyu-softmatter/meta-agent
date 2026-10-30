"""The versioned bundle template (plan.md 5.1 S5).

The source tree lives in template_v1/ next to this file. `materialize`
copies it to templates/agent@<hash>/, where the hash is over every file's
path and content, so a changed template gets a new name and an old one is
never edited in place.
"""
import os
import shutil

from .. import cards

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "template_v1")


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
