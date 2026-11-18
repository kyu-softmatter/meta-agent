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
v9  changes the gate, after a test run built an agent on an engine whose
    environment no tool of its bundle could make (tasks/016): the one
    network call a bundle may make is an install, by a tool whose contract
    names installs_from, where the permission reaches an engine and lists
    that installer and channel under package_sources; every other network
    tool is refused. CLAUDE.md says so, and .claude/settings.json denies a
    session's edit of envelope/execution_permission.json.
v10 changes text and the runner of tools, after round four's bundle was
    tested standing alone (tasks/016): CLAUDE.md says which envelope file
    opens which gate, that tool calls and the checks leave folders under
    runs/, that the install keeps its package cache there and that a
    measured value's grade is the builder's to derive; README.md and
    tasks/001-start.md say what the bundle carries and prints. The runner
    points the installers' caches at runs/cache before the install and
    refuses an output whose field of unit count is below zero.
v11 changes text and the runner of tools, after round five's bundle was
    tested standing alone (tasks/016): CLAUDE.md says that a record of the
    builder's repository a file names is not here and is marked by the build
    with builder_records, has a Workflow section the build fills with the
    request's order of tools, and says that the install never installs its
    installer; tasks/001-start.md says that the agent's own install follows
    a scientific not_run for want of an engine's environment. The runner
    returns an unavailable error naming the installer when it is not on PATH.
v12 changes text only, on the person's word of 2026-11-17 (tasks/016):
    CLAUDE.md has a Decisions section, filled by the build with each
    run-time decision the request names, the diagnostic skill that takes it,
    the tool output it judges and the row that hands each criterion; and
    says that a value a tool's output reports is read and not computed.
v13 changes one script (tasks/016): src/validate_tasks.py runs a
    scientific task's analysis, a library skill on the call's output with
    its other inputs from rows, through src/run_skill.py, and judges the
    skill's output; a row absent or null leaves the task not_run.
v14 changes text only, after the Meep bundle was tested standing alone
    (tasks/021, em-7 to em-9) beside the Quantum ESPRESSO bundle (dft-5):
    CLAUDE.md says that the build also marks a card of the builder's
    repository named by its id and a question put to the person named by
    its number, envelope/parameters.json among the files, quoting the
    question and its answer; tasks/001-start.md says that an interface task
    whose call starts the engine fails before the install as a scientific
    task is not_run. From this version the build refuses an optional input
    that names neither a row nor a default, and the Tools section prints
    the default (bundle.py).
v15 changes the gate, after round two of the Quantum ESPRESSO test held
    its fetch tools for want of a way to read data from hosts the person
    had allowed (tasks/023, dft-7): src/gate.py also opens a network tool
    whose contract names fetches_from, where the permission reaches an
    engine and lists every host it names under data_sources with the same
    access; an install and a read are each judged against their own list
    and neither opens the other. The runner looks for an installer only
    for a tool that names installs_from, and CLAUDE.md says which network
    calls the agent may make. The Designer copies data_sources from the
    lab profile into envelope/execution_permission.json.
v16 changes one script of the checks, the runner of tools and text, after the
    CFD test's clone and its bundle standing alone (tasks/019, cfd-2, cfd-7,
    cfd-10, cfd-11; dft-2): src/validate_tasks.py takes a scientific task's
    agreement from the library skill TEMPLATE.json names under
    agreement_skill (measurement_error@v1), through src/run_skill.py, and
    the build puts that skill into every bundle with a scientific task
    (bundle.py). A tool keeps every error contract of a category: the first
    is errors/<category>.json, which the runner returns itself, the others
    errors/<category>.<code>.json (bundle.py, run_tool.py). The start task
    says that replay, like an interface task, waits for the install and is
    run again after it, and that its Status line is the builder's; CLAUDE.md
    says so, that the builder's dates are in UTC, and that the agreement is
    the skill's output.
v17 changes the runner of tools, after round two of the CFD test (tasks/019,
    cfd-13): src/run_tool.py takes a type that is a list of JSON Schema
    types, such as an integer or null, and refuses a value of none of them
    with an error contract instead of raising. From this version the
    builder keeps each run of the agreement skill on the validation report,
    as a number whose source names the skill (src/validate/gate.py, cfd-14).
v18 changes text only, the bundle's classify-knowledge, to say what the
    builder's own says (the design role's ask 20261117-design-macbook-
    20261117-1-14, em-10; cfd-5, cfd-16 of tasks/019): spec is the maker's
    documentation, a tutorial or example page of the maker included; a
    quantity defined up to a constant is compared only once both share its
    zero; a tabled value is read against the source's raw series.
v19 changes one script of the checks and the start task, on the person's
    standing rule of 2026-11-18 for tolerances (the design role's ask
    20261118-design-macbook-20261117-1-5): src/validate_tasks.py judges by a
    tolerance a person chose or one the rule gave (chosen_by rule, naming the
    rule and the skill), alike. From this version the builder derives such a
    tolerance where the person gave none, by tolerance_from_reference@v1
    through the runner, from the reference as its task prints it (bundle.py).
v20 changes one script of the checks, on the person's word that every
    simulation bundle carries a common set of library skills (tasks/025):
    TEMPLATE.json names the set under common_skills; the builder puts it into
    every bundle whose tool is an engine, and an adaptation to the engine, a
    next version with adapted_from from the request's adapted/ folder, in place
    of the common one, which the difference from the template lists
    (bundle.py). src/validate_tasks.py reads the agreement skill's name from
    TEMPLATE.json (measurement_error@v2).
v21 changes TEMPLATE.json alone: the common set also carries
    discretization_error_from_two_resolutions@v1, the run's own numerical
    error from two resolutions, which the amended tolerance rule weighs
    (tasks/025).

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
           "v7": os.path.join(HERE, "template_v7"), "v8": os.path.join(HERE, "template_v8"),
           "v9": os.path.join(HERE, "template_v9"), "v10": os.path.join(HERE, "template_v10"),
           "v11": os.path.join(HERE, "template_v11"), "v12": os.path.join(HERE, "template_v12"),
           "v13": os.path.join(HERE, "template_v13"), "v14": os.path.join(HERE, "template_v14"),
           "v15": os.path.join(HERE, "template_v15"), "v16": os.path.join(HERE, "template_v16"),
           "v17": os.path.join(HERE, "template_v17"), "v18": os.path.join(HERE, "template_v18"),
           "v19": os.path.join(HERE, "template_v19"),
           "v20": os.path.join(HERE, "template_v20"),
           "v21": os.path.join(HERE, "template_v21")}
LATEST = "v21"
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
