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
v22 changes one script of the checks (cfd-19): src/validate_tasks.py judges a
    tolerance the person gave as an interval {low, high} by inclusion, its edges
    as written, through series_within_window@v3 (TEMPLATE.json interval_skill)
    run on the one measured value; the builder carries that skill into every
    bundle with such a task (bundle.py).
v23 changes one script of the checks, on the person's 'Yes, refine and
    derive' (2026-11-18) and the intake card's refinement field: a task that
    names a refinement and has no tolerance from the person is judged by the
    tolerance the rule derives from the run's own error, estimated from the run
    as built and a finer run through the refinement's skill; the finer result is
    judged, and the record names what was refined. The builder carries the
    refinement's and the rule's skills into such a bundle (bundle.py).
v24 changes one script of the checks, on the person's 'Yes, factor 3'
    (2026-11-18, rheotool-26): the rule's skill is tolerance_from_reference@v3,
    and src/validate_tasks.py hands it how the refinement's skill estimates the
    run's error (TEMPLATE.json run_error_from), so that a two-grid estimate
    enters three times over, Roache's factor of safety for two grids.

v25 changes one script of the checks and TEMPLATE.json (cfd-25; the intake card's
    third_inputs, 6c7a488): a refinement with a third, finer run observes the
    order from the three results by observed_order_of_convergence@v1 (order_skill,
    also in the common set), estimates the finest result's error at that order,
    judges the finest, and tells the rule's skill three_or_more_grids, so that no
    factor enters. The builder checks the third run's rows (bundle.py).

v26 changes one script of the checks and TEMPLATE.json (rheotool-28; the design
    role's reply f071852): a task marks a reference its source gives as exact
    (measure.exact), src/validate_tasks.py hands the mark to the rule's skill,
    now tolerance_from_reference@v4, and the half-digit branch does not apply to
    it: the run's own error alone gives the tolerance. The builder hands the
    mark too, and refuses it under a template whose rule's skill cannot take it.

v27 changes the gate, one script of the checks, .claude/settings.json and
    text (rheotool-22, -23, -29, -32): src/gate.py opens an install from a
    pair allowed for named engines alone only in a bundle of one of them, as
    check B9 does; src/validate_tasks.py prints each scientific task's
    tolerance and the run's own error; the hook runs the self-check by the
    project's path; the common set carries series_settled@v4.

v28 changes one script of the checks and text, on the person's amended and
    widened rule for tolerances (tasks/028): src/validate_tasks.py takes the
    rule's branches in order. A scientific task may carry materials
    (measure.materials: entries naming a material, how its system compares,
    and one value or one stated range); literature_span@v1 gives their span
    [lowest, highest] through the runner, and the rule's skill, now
    tolerance_from_reference@v5, takes it after a stated uncertainty and
    before the printed digit and the run's own error, as an acceptance
    interval, chosen_by rule, from literature_span. A refinement is run only
    where no earlier branch gave the tolerance. The builder derives the span
    for a task that names no refinement and refuses entries that do not name
    their material or say how it compares.

v29 changes text and the template's card, on the person's word that a
    source's stated uncertainty widens the span ('Widen by uncertainty',
    2026-11-19; tasks/028): an entry of measure.materials that gives a value
    may carry the uncertainty its material states for it, and the span's
    skill, now literature_span@v2, takes it as the value less and plus that
    uncertainty, one stated range. The builder refuses an uncertainty that is
    negative or stands beside a range, and any under an earlier template.

v30 adds src/engine_wait.py and changes one script of the checks and two
    texts, after round two of the GROMACS test (gmx-21, gmx-22, gmx-24,
    gmx-26, gmx-27; tasks/017): an adapter that starts an engine waits
    through it, so that a budget counts running time only and an engine
    paused from outside is not killed as hung; a call that gives up stops
    the engine with TERM first, and a stopped run comes back as timeout or
    cancelled, retryable, saying whether a call again resumes from a
    checkpoint. The builder refuses an adapter that waits with a wall-clock
    timeout under this template. src/validate_tasks.py prints every run of
    the agreement skill and takes it for a task the rule left undecided;
    tasks/001-start.md says what a scientific fail is once the call was made.

v31 changes TEMPLATE.json alone (rheotool-27; unit_of, 7a4b9fc): the
    agreement skill and the common set take the versions of measurement_error,
    series_maximum and series_settled whose outputs name the input whose unit
    they take, which the builder follows to the tool contract's unit.

v32 adds src/handover.py, a section of CLAUDE.md, three folders and the guardrails that keep
    them, on the person's words for two agents that hand values to each other (tasks/031): a
    build whose parameter rows declare a hand-over writes envelope/handovers.json (what it gives
    and takes, and what its engine's own units stand for) and envelope/units.json, the registry
    it converts by, and makes outbox/, inbox/ and received/; the script writes a hand-over card
    from a skill's record and the tool results it was taken from, and receives what the bridge a
    person starts delivered, one receipt per value, used only for a declared row through
    unit_convert@v1 and, into an engine's unit, a scale a person confirmed (handovers.py).

v33 changes one script and the Hand-overs text, after the bridge's first test standing alone
    (run multiscale/20261120-8; dftmd-13, dftmd-14): a hand-over card carries each value's
    definition, the meaning its skill's manifest gives the output, under conditions.definition,
    and the receipt and values show it, so that the receiving agent knows what a value is a value
    of without the producer's skill; the text says what the card's draft status and its grade are.

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
           "v21": os.path.join(HERE, "template_v21"),
           "v22": os.path.join(HERE, "template_v22"),
           "v23": os.path.join(HERE, "template_v23"),
           "v24": os.path.join(HERE, "template_v24"),
           "v25": os.path.join(HERE, "template_v25"),
           "v26": os.path.join(HERE, "template_v26"),
           "v27": os.path.join(HERE, "template_v27"),
           "v28": os.path.join(HERE, "template_v28"),
           "v29": os.path.join(HERE, "template_v29"),
           "v30": os.path.join(HERE, "template_v30"),
           "v31": os.path.join(HERE, "template_v31"),
           "v32": os.path.join(HERE, "template_v32"),
           "v33": os.path.join(HERE, "template_v33")}
LATEST = "v33"
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
