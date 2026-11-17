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
v4  changes text only, after a fresh session was watched working in a
    bundle of v3 (tasks/015): run-skill says how a tool that no library
    skill calls is called, and the start task says what the task
    validator's failure status means when a verdict is undecided.
v5  changes text only, after a fresh session was watched working in a
    copy of a rheometer-fixture bundle of v4 outside the repository
    (tasks/015): the start task covers a verdict of not_run as well as
    undecided, the envelope sentence says what a safety file with no
    entry means, the folder named runs is said to be made by the session,
    and an input that nothing in the bundle gives is reported like a
    missing skill.
v6  changes text and no script, after two fresh sessions worked in copies
    of bundles of v5 in a test run outside the repository (tasks/016):
    CLAUDE.md names the files a session found unexplained, says when a
    runner writes a record and what the status each runner and check
    ends with means, how a replay item made by hand is compared, which
    keys a line of failures.jsonl has, and that a grade is the builder's
    and is not derived in a bundle; run-skill repeats the procedure.
    From this version the builder writes units into the Tools section
    and tells, in CAPABILITIES.json, a claim about a tool the bundle
    does not carry from one about a tool it has (bundle.py, profile.py).
    Bundle check B16 judges a bundle of this version or later.
v7  changes one script and no text, after a session of a test run built
    the first agent on an engine (tasks/016): src/validate_tasks.py also
    judges a scientific task against the values a source states, carried
    by the task as measure.stated, and says not_run where the call was
    not made (the gate refused it, a permission was missing, what the
    tool needs was not there). One tolerance judges one stated field;
    several are judged together only by an exact tolerance.
v8  changes the gate, after the person's word that an engine tool opens
    by the lab's execution permission (tasks/016): src/gate.py opens a
    tool whose contract says safety_gate.opens_by execution_permission,
    and that starts a process or writes files, where the bundle's
    envelope/execution_permission.json is a level a person confirmed that
    reaches an engine or an instrument, and refuses it otherwise naming
    the level found; every other gated tool still waits for safety
    values. The Designer writes that file from the lab profile a build
    names, and none where the profile carries only words.

A version is materialized by the Designer when it builds, and by nothing
else: a folder under templates/ made by hand from a tree that then
changes is a version no build names and no session may remove.
"""
import os
import shutil

from .. import cards

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = {"v1": os.path.join(HERE, "template_v1"), "v2": os.path.join(HERE, "template_v2"),
           "v3": os.path.join(HERE, "template_v3"), "v4": os.path.join(HERE, "template_v4"),
           "v5": os.path.join(HERE, "template_v5"), "v6": os.path.join(HERE, "template_v6"),
           "v7": os.path.join(HERE, "template_v7"), "v8": os.path.join(HERE, "template_v8")}
LATEST = "v8"
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
