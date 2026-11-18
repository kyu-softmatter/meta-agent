"""S5 Build: a bundle from the template plus the Designer's outputs, and the build card.

Skills and subagents (plan.md 14-31, 14-34; tasks/010): the skills a specification names are copied from
the library into the bundle's skills/<id>@v<n>/ unchanged, and each subagent it names becomes
.claude/agents/<name>.md with the skills and the side effects it may use. The caller reads the library
(src/skills/catalogue.take) and hands the rows in; this stage imports no sibling stage (plan.md 7). What
check B11 would fail in the finished bundle is refused here, before anything is written: a held skill (it
is named in the specification's skills and held[], and stays out of the bundle), a skill whose tool the
bundle does not have or that uses a skill the specification does not name, a skill that says it only reads
and calls a tool that changes something, a subagent whose side effects do not cover its skills, and a
second subagent that may change a device.

The session skills (plan.md 14-37(i); tasks/015): a template of version v3 or later carries them under
.claude/skills/, and the build copies them unchanged. One of them, run-skill, sends the bundle's session
to src/run_skill.py, and it is the only one that names a script under src/ (B15). The build renders its
library/ folder from the manifests of the skills it copied: index.md, and one reference page
per library skill. A page is rendered, never written by hand, and is not a trigger: the sentence that
says when a skill applies stays in CLAUDE.md (B8).
"""
import difflib
import json
import os
import re
import shutil

from .. import cards

WRITER = "operator"        # the one subagent that may list write_device (plan.md 14-34(e))
SESSION_SKILL = "run-skill"   # the one session skill that names the runner, from template v3 on (tasks/015)
SIDE_EFFECTS = ("none", "read_device", "write_device")

TEXT_EXT = (".md", ".json", ".py", ".jsonl", ".txt", ".toml")


def render(text, fill):
    for k, v in fill.items():
        text = text.replace("{{%s}}" % k, v)
    left = [t for t in text.split("{{")[1:] if "}}" in t]
    if left:
        raise ValueError("unfilled placeholders: %s" % [t.split("}}")[0] for t in left])
    return text


def field(name, prop, required=False):
    """`name` (type, unit, required; what the contract says of it; the values it enumerates): one input or output
    of a tool contract. The unit is the one the contract names; a field with none is printed with none, never with
    a guessed one."""
    parts = [str(prop.get("type", "any"))]
    if prop.get("unit"):
        parts.append(str(prop["unit"]))
    if required:
        parts.append("required")
    text = ", ".join(parts)
    if prop.get("description"):
        text += "; " + str(prop["description"]).rstrip(".")
    values = prop.get("enum") or (prop.get("items") or {}).get("enum")
    if values:
        # the values a contract enumerates, so that a session need not guess them (test run 20261116-6); a number, or
        # a word with a digit, is not printed, since CLAUDE.md carries no number its snapshot does not (B6), and the
        # contract is named instead
        words = [v for v in values if isinstance(v, str) and not any(ch.isdigit() for ch in v)]
        if len(words) == len(values):
            text += "; one of %s" % ", ".join("`%s`" % v for v in words)
        else:
            text += "; one of the values its contract lists"
    if "default" in prop:
        # what the tool takes when the input is left out (test run electromagnetics/20261117-2, em-8: a session guessed
        # it); a number or a word with a digit is not printed (B6), and the contract is named instead
        d = prop["default"]
        if isinstance(d, str) and not any(ch.isdigit() for ch in d):
            text += "; left out, it is `%s`" % d
        else:
            text += "; left out, it is the default its contract states"
    return "`%s` (%s)" % (name, text)


def default_problems(tool_contracts):
    """An optional input of a tool contract that names neither a parameter row nor a default: what the tool takes when
    the input is left out is then known to its adapter alone, and a session asked to run the tool guesses it (test run
    electromagnetics/20261117-2, em-8). Top-level inputs only, as the Tools section prints them."""
    out = []
    for tc in tool_contracts:
        ins = (tc or {}).get("inputs") or {}
        required = set(ins.get("required") or [])
        for k, prop in sorted((ins.get("properties") or {}).items()):
            if k in required or not isinstance(prop, dict):
                continue
            if prop.get("row") is None and "default" not in prop:
                out.append("tool %s: the optional input %s names neither a row nor a default" % (tc.get("name"), k))
    return out


def gate_line(tc):
    """Where the gate is and which file opens it (test run 20261116-8: a session could not tell which of the two
    envelope files opened a tool's gate)."""
    gate = tc.get("safety_gate") or {}
    if tc.get("side_effects") == "network":
        installer = (tc.get("installs_from") or {}).get("installer")
        hosts = [f.get("host") for f in tc.get("fetches_from") or [] if isinstance(f, dict)]
        opened = []
        if isinstance(tc.get("installs_from"), dict):
            opened.append("as the one install, where it lists this tool's installer and channel under `package_sources`")
        if hosts:   # a read of data from named hosts (tasks/023): each host listed under data_sources with the same access
            opened.append("as a read of data, where it lists every host this tool fetches from (%s) under `data_sources` "
                          "with the same access" % ", ".join("`%s`" % h for h in hosts))
        return ("asked of every call, at %s; opened by the lab's execution permission in `envelope/execution_permission.json`, "
                "%s" % (gate.get("place", "src/gate.py"), " and ".join(opened) or "as the one install, where it lists this "
                        "tool's installer and channel")
                + ("; the installer `%s` must already be on the computer, and putting it there is the person's step" % installer
                   if installer else ""))
    if not gate.get("required"):
        return "not required (" + gate.get("place", "no side effects") + ")"
    if gate.get("opens_by") == "execution_permission":
        return "required, at %s; opened by the lab's execution permission in `envelope/execution_permission.json`" % gate.get("place", "src/gate.py")
    return "required, at %s; opened by the safety values in `envelope/safety.json`" % gate.get("place", "src/gate.py")


def tools_section(tool_contracts):
    out = []
    for tc in tool_contracts:
        ins = ", ".join(field(k, v, k in (tc.get("inputs") or {}).get("required", []))
                        for k, v in sorted(((tc.get("inputs") or {}).get("properties") or {}).items()))
        outs = ", ".join(field(k, v) for k, v in sorted(((tc.get("outputs") or {}).get("properties") or {}).items()))
        gate = tc.get("safety_gate") or {}
        out.append("### `%s`\n\n%s\n\n- input: %s\n- output: %s\n- errors it may return: %s\n- side effects: %s; idempotent: %s\n- gate: %s"
                   % (tc["name"], tc["description"], ins or "none", outs or "none",
                      ", ".join("`%s`" % e for e in tc.get("errors", [])), tc.get("side_effects"),
                      "yes" if tc.get("idempotent") else "no",
                      gate_line(tc)))
    return "\n\n".join(out) if out else "This agent has no callable tool."


def workflow_section(order, tool_names):
    """The order in which the workflow calls the tools (test run 20261117-2: a session read the order off the tools'
    descriptions). `order` is the request's list of tool names, or None where it gave none; a name that is not a tool
    of the bundle is refused before anything is written."""
    if not order:
        return ("The request this agent was built for gave no order in which its workflow calls the tools. Each tool's "
                "description says what it takes and what it gives; an order you read from the descriptions is an "
                "inference, and you say that it is one when you report it.")
    unknown = [n for n in order if n not in tool_names]
    if unknown:
        raise ValueError("the workflow names %s, which this bundle does not have as tools" % ", ".join(unknown))
    if len(set(order)) != len(order):
        raise ValueError("the workflow names a tool twice: %s" % ", ".join(order))
    steps = ", then ".join("`%s`" % n for n in order)
    rest = [n for n in tool_names if n not in order]
    text = ("The workflow calls the tools in this order, each through the runner and each once the one before it has "
            "answered: %s. The order is the one the request this agent was built for gave. A task or the person may ask "
            "for part of it, and a step may be called again on its own." % steps)
    if rest:
        text += " Outside the order: %s, called when a task asks for it." % ", ".join("`%s`" % n for n in rest)
    return text


def handed_problems(where, skill_ref, tool_name, data, rows, tools, skills, row_names, kind=None):
    """What is wrong with handing one tool output field and some parameter rows to one skill: the skill is one the bundle
    carries (and of `kind` where one is asked), the tool returns the field, the data's input is the skill's, every other
    input of the skill is handed by a row, and every row is one the bundle carries."""
    out = []
    skill = skills.get(skill_ref)
    if skill is None:
        return ["%s: the skill %s is not one this bundle carries" % (where, skill_ref)]
    if kind and skill.get("kind") != kind:
        out.append("%s: %s is of kind %s; a decision is taken by a %s" % (where, skill_ref, skill.get("kind"), kind))
    inputs = [x["name"] for x in skill.get("inputs") or []]
    tc = tools.get(tool_name)
    if tc is None:
        out.append("%s: the data's tool %s is not a tool of this bundle" % (where, tool_name))
    elif data.get("field") not in ((tc.get("outputs") or {}).get("properties") or {}):
        out.append("%s: %s returns no field %s" % (where, tool_name, data.get("field")))
    if data.get("input") not in inputs:
        out.append("%s: %s has no input %s for the data" % (where, skill_ref, data.get("input")))
    for name in inputs:
        if name != data.get("input") and name not in rows:
            out.append("%s: the input %s of %s is handed by no row; a criterion is a row" % (where, name, skill_ref))
    for name, row in sorted(rows.items()):
        if name not in inputs:
            out.append("%s: %s has no input %s" % (where, skill_ref, name))
        if row not in row_names:
            out.append("%s: the row %s is not a row of envelope/parameters.json" % (where, row))
    return out


def decision_problems(decisions, tool_contracts, skill_rows, row_names):
    """Every reason a request's decisions cannot be written into a bundle. A decision is {decision, skill, data: {tool,
    field, input}, rows: {skill input: row}}: a diagnostic skill the bundle carries, judging one output field of one of
    its tools, every other input of the skill handed by a parameter row the bundle carries (design ask
    20261117-design-macbook-20261116-1-8; the person, 2026-11-17)."""
    tools = {tc.get("name"): tc for tc in tool_contracts}
    skills = {r["ref"]: r for r in skill_rows}
    out = []
    for i, d in enumerate(decisions or []):
        where = "decisions[%d] (%s)" % (i, d.get("decision"))
        if not str(d.get("decision") or "").strip():
            out.append("%s: no words say what is decided" % where)
        elif any(ch.isdigit() for ch in str(d["decision"])):
            out.append("%s: the words carry a digit, and CLAUDE.md carries no number its snapshot does not" % where)
        data = d.get("data") or {}
        out += handed_problems(where, d.get("skill"), data.get("tool"), data, d.get("rows") or {}, tools, skills, row_names,
                               kind="diagnostic")
    return out


def analysis_problems(scientific_tasks, tool_contracts, skill_rows, row_names):
    """Every reason a scientific task's analysis cannot run in the bundle (intake schema, 23bb51b): {skill, data: {field,
    input}, rows, output}, handed the field of the task's own call, every other input by a row the bundle carries, and
    the output the reference judges one the skill gives."""
    tools = {tc.get("name"): tc for tc in tool_contracts}
    skills = {r["ref"]: r for r in skill_rows}
    out = []
    for i, task in enumerate(scientific_tasks or []):
        a = task.get("analysis") if isinstance(task, dict) else None
        if not a:
            continue
        where = "scientific_tasks[%d] (%s), its analysis" % (i, task.get("id"))
        data = a.get("data") or {}
        out += handed_problems(where, a.get("skill"), (task.get("call") or {}).get("tool"), data, a.get("rows") or {},
                               tools, skills, row_names)
        skill = skills.get(a.get("skill"))
        if skill is not None and a.get("output") not in [o["name"] for o in skill.get("outputs") or []]:
            out.append("%s: %s gives no output %s" % (where, a.get("skill"), a.get("output")))
    return out


def decisions_section(decisions, tool_contracts, skill_rows, row_names):
    """The decisions the request names, each with the diagnostic skill that takes it, the tool output it judges and the
    row that hands each criterion; or a sentence that the request named none. Refused before anything is written where
    decision_problems finds a reason."""
    if not decisions:
        return ("The request this agent was built for named no decision of this kind. Where a run calls for one, and no "
                "diagnostic skill here takes it on a row's criterion, you report the data and say that the decision is the "
                "person's.")
    faults = decision_problems(decisions, tool_contracts, skill_rows, row_names)
    if faults:
        raise ValueError("the decisions of this request cannot be built: " + "; ".join(faults))
    lines = []
    for d in decisions:
        data = d["data"]
        handed = ", ".join("`%s` from the row `%s`" % (k, v) for k, v in sorted(d.get("rows", {}).items()))
        lines.append("- %s: run `%s` on the field `%s` that `%s` returns, as its `%s`%s." % (
            str(d["decision"]).rstrip(".")[:1].upper() + str(d["decision"]).rstrip(".")[1:], d["skill"], data["field"],
            data["tool"], data["input"], (", with " + handed) if handed else ""))
    return "\n".join(lines)


BUILDER_PATH_RE =re.compile(r"(?<![\w/.-])(?:(?:docs|meta_agent|contracts)/[\w./@-]*[\w/]|plan\.md)")


def builder_paths(value, bundle_path):
    """The paths of the builder's repository that a JSON value names in its strings and that the bundle does not carry."""
    found = []
    def walk(v):
        if isinstance(v, str):
            for m in BUILDER_PATH_RE.finditer(v):
                p = m.group(0).rstrip("/.")
                if p not in found and not os.path.exists(os.path.join(bundle_path, *p.split("/"))):
                    found.append(p)
        elif isinstance(v, dict):
            for k in sorted(v):
                walk(v[k])
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(value)
    return found


QUESTION_RE = re.compile(r"(?<![\w-])questions? (\d+)(?!\w)", re.IGNORECASE)


def builder_cards(value, ids):
    """The ids of the builder's cards (`ids`, the cards the build read) that a JSON value names in its strings."""
    text = []
    def walk(v):
        if isinstance(v, str):
            text.append(v)
        elif isinstance(v, dict):
            for k in sorted(v):
                walk(v[k])
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(value)
    joined = "\n".join(text)
    return [i for i in sorted(set(ids or ())) if i and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(i), joined)]


def builder_questions(value, questions):
    """The numbers of the intake's questions for the person (`questions`, {n: question}) that a JSON value names as
    'question <n>' in its strings (runs electromagnetics/20261117-2, em-7, and dft/20261117-2, dft-5)."""
    found = []
    def walk(v):
        if isinstance(v, str):
            for m in QUESTION_RE.finditer(v):
                n = int(m.group(1))
                if n in (questions or {}) and n not in found:
                    found.append(n)
        elif isinstance(v, dict):
            for k in sorted(v):
                walk(v[k])
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(value)
    return sorted(found)


def questions_by_number(intake):
    """{n: question} from an intake's questions_for_the_person: the question as it was asked and its answer, if any."""
    out = {}
    for q in (intake or {}).get("questions_for_the_person") or []:
        if isinstance(q, dict) and isinstance(q.get("n"), int) and isinstance(q.get("question"), str):
            out[q["n"]] = {k: q[k] for k in ("question", "answer") if k in q}
    return out


def builder_records(paths, words=None, card_ids=(), question_ns=(), questions=None):
    """One entry per path: the record is the builder's and is not here; a person's words recorded in it, quoted. Then
    one per card id named, and one per question named, quoting the question and the person's answer where there was one."""
    out = []
    for p in paths:
        e = {"path": p, "in_this_bundle": False,
             "whose": "a record of the builder's repository; it is not in this bundle and is not looked for here"}
        quoted = [dict(w) for w in (words or {}).get(p, [])]
        if quoted:
            e["words"] = quoted
        else:
            e["words_here"] = "none: what the item rests on is what it says in its own words"
        out.append(e)
    for i in card_ids:
        out.append({"card": i, "in_this_bundle": False,
                    "whose": "a card of the builder's repository, named by its id; it is not in this bundle and is not "
                             "looked for here"})
    for n in question_ns:
        q = (questions or {}).get(n) or {}
        e = {"question": n, "in_this_bundle": False,
             "whose": "a question the builder put to the person in its intake, which is not in this bundle",
             "asked": q.get("question")}
        a = q.get("answer")
        if isinstance(a, dict):
            e["answer"] = {k: a[k] for k in ("verbatim", "date", "gloss") if k in a}
        else:
            e["answer_here"] = "none: the person had not answered it when this bundle was built"
        out.append(e)
    return out


def mark_builder_records(bundle_path, words=None, subs=("validation/interface", "validation/scientific", "replay"),
                         files=("TEMPLATE.json", "envelope/parameters.json"), ids=(), questions=None):
    """Add builder_records to each task, replay item and named file that names a record the bundle does not carry.
    `words` is {path: [{verbatim, date, gloss?}]}, the person's words the builder had for a record; `ids` the ids of the
    builder's cards the build read, and `questions` the intake's {n: question} (questions_by_number). The parameter rows
    are marked as a file: a row cites the material and the sheet it came from (run electromagnetics/20261117-2, em-7)."""
    marked = []
    targets = [os.path.join(bundle_path, f) for f in files]
    for sub in subs:
        d = os.path.join(bundle_path, *sub.split("/"))
        if os.path.isdir(d):
            targets += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".json")]
    for path in targets:
        if not os.path.isfile(path):
            continue
        item = cards.load_json(path)
        if not isinstance(item, dict):
            continue
        body = {k: v for k, v in item.items() if k != "builder_records"}
        paths = builder_paths(body, bundle_path)
        card_ids = builder_cards(body, ids)
        question_ns = builder_questions(body, questions)
        if paths or card_ids or question_ns:
            item["builder_records"] = builder_records(paths, words, card_ids, question_ns, questions)
            cards.write_json(path, item)
            marked.append(os.path.relpath(path, bundle_path).replace(os.sep, "/"))
    return marked


def words_by_record(*cards_in):
    """{recorded_in: [{verbatim, date, gloss?}]} from every dict in the given cards that carries verbatim and recorded_in."""
    out = {}
    def walk(v):
        if isinstance(v, dict):
            if isinstance(v.get("verbatim"), str) and isinstance(v.get("recorded_in"), str):
                w = {k: v[k] for k in ("verbatim", "date", "gloss") if k in v}
                if w not in out.setdefault(v["recorded_in"], []):
                    out[v["recorded_in"]].append(w)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    for c in cards_in:
        walk(c)
    return out


def must_not_section(items):
    return "\n".join("- %s." % (i[:1].upper() + i[1:]).rstrip(".") for i in items) if items else "- (nothing beyond the common rules)"


def skills_section(skills):
    """`skills` is a list of (name, trigger sentence); B8 looks for each name in backticks."""
    if not skills:
        return ("This agent has no library skill. A library skill, when a build adds one, is named here with the sentence "
                "that triggers it.")
    return "\n".join("- `%s`: %s" % (name, trigger) for name, trigger in skills)


def subagents_section(subagents):
    if not subagents:
        return "This agent has no subagents."
    lines = ["Each subagent is a file under `.claude/agents/` and works in its own context. It is not a seat: it writes no "
             "record and commits nothing; this agent reports and commits what a subagent returns. Only `%s` may be given "
             "a skill that changes a device." % WRITER,
             "",
             "Where a skill's line above says it is used by a subagent, that subagent's file lists it. A skill that "
             "changes a device is run by `%s` only. Any other skill you may run yourself through the runner, or give "
             "to the subagent that lists it: which of the two is a choice of level and of context, not a rule." % WRITER, ""]
    for a in subagents:
        lines.append("- `%s`: %s Skills: %s. Side effects: %s." % (
            a["name"], a["description"].rstrip(".") + ".", ", ".join("`%s`" % r for r in a["skills"]) or "none",
            ", ".join(a["side_effects"]) or "none"))
    return "\n".join(lines)


def front_value(text):
    """One line of front matter. A value YAML would not read as plain text (a colon and a space, a quote, a
    leading mark) is written as a quoted string."""
    text = " ".join(str(text).split())
    plain = text and ": " not in text and " #" not in text and '"' not in text and text[0] not in "[{>|*&!%@`'#-?:,"
    return text if plain else json.dumps(text, ensure_ascii=False)


def subagent_markdown(agent, rows):
    """.claude/agents/<name>.md: front matter name, description, skills, side_effects (what B11 reads), and a body."""
    lines = ["---", "name: %s" % agent["name"], "description: %s" % front_value(agent["description"]),
             "skills: [%s]" % ", ".join(agent["skills"]), "side_effects: [%s]" % ", ".join(agent["side_effects"]), "---", "",
             "# %s" % agent["name"], "", agent["description"].rstrip(".") + ".", "", "## Skills", ""]
    for ref in agent["skills"]:
        r = rows[ref]
        ins = ", ".join("`%s` (%s)" % (i["name"], i["unit"]) for i in r["inputs"]) or "none"
        lines.append("- `%s` (%s, %s): %s. Inputs: %s." % (ref, r["kind"], r["side_effect"], r["summary"], ins))
    if not agent["skills"]:
        lines.append("- none")
    lines += ["", "Read a skill's `SKILL.md` under `skills/` before taking it, and run it only through the runner:", "",
              "```", "python src/run_skill.py <id@vN> < inputs.json", "```", "",
              "Return what the runner printed, unchanged: the outputs, the tool calls and their verdicts.", "",
              "## What you do not do", "",
              "- Take a skill this file does not list, or run a skill's script yourself.",
              "- Type a number a skill would compute, or go on after a refusal: a refusal is returned as it is.",
              "- Write a record, a safety value or a threshold, or commit: you are not a seat.",
              ("- Start a step that changes the device unless the gate lets the call through; the gate is asked on every call."
               if "write_device" in agent["side_effects"] else "- Change a device: nothing you are given can."), ""]
    return "\n".join(lines)


def session_skill_dir(tree):
    """The folder of the session skill in a template or a bundle, or None before template v3."""
    d = os.path.join(tree, ".claude", "skills", SESSION_SKILL)
    return d if os.path.isfile(os.path.join(d, "SKILL.md")) else None


def _named(items):
    """`name` (unit): meaning, one line per input or output of a manifest."""
    out = []
    for i in items or []:
        line = "- `%s` (%s)" % (i["name"], i.get("unit", "1"))
        if i.get("meaning"):
            line += ": %s" % str(i["meaning"]).rstrip(".") + "."
        out.append(line)
    return out or ["- none"]


def skill_page(ref, manifest):
    """One reference page for one library skill, from its manifest and nothing else."""
    lines = ["# `%s`" % ref, "",
             "Rendered by the build from `skills/%s/skill.json`; never edited by hand. This page is reference and not a "
             "trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` "
             "is beside its manifest." % ref, "",
             "- **Gives:** %s." % str(manifest.get("summary", "")).rstrip("."),
             "- **Kind:** %s. **Side effect:** %s. **Status:** %s." % (manifest.get("kind"), manifest.get("side_effect"),
                                                                    manifest.get("status")),
             "- **Calls tools:** %s." % (", ".join("`%s`" % t for t in manifest.get("calls_tools") or []) or "none"),
             "- **Uses skills:** %s." % (", ".join("`%s`" % t for t in manifest.get("uses_skills") or []) or "none")]
    if manifest.get("validity"):
        lines.append("- **Valid for:** %s." % str(manifest["validity"]).rstrip("."))
    lines += ["", "## Inputs", ""] + _named(manifest.get("inputs"))
    lines += ["", "## Outputs", ""] + _named(manifest.get("outputs"))
    lines += ["", "## Run", "", "```", "python src/run_skill.py %s < inputs.json" % ref, "```", ""]
    return "\n".join(lines)


def library_index(manifests):
    """library/index.md: every library skill of the bundle with its page. `manifests` is [(ref, manifest)]."""
    lines = ["# Library skills of this agent", ""]
    if not manifests:
        lines += ["This agent has no library skill. When a build gives it one, the skill is listed here with its page.", ""]
        return "\n".join(lines)
    lines += ["Rendered by the build from the manifests under `skills/`; never edited by hand. Each skill has a page "
              "beside this file, named after it.", ""]
    for ref, m in manifests:
        lines.append("- `%s` (%s, %s, %s): %s. Page: `%s.md`." % (ref, m.get("kind"), m.get("side_effect"), m.get("status"),
                                                               str(m.get("summary", "")).rstrip("."), ref))
    lines.append("")
    return "\n".join(lines)


def add_pages(bundle_path, refs):
    """Render the session skill's library/ from the manifests the bundle carries. Nothing before template v3."""
    sdir = session_skill_dir(bundle_path)
    if sdir is None:
        return []
    manifests = [(ref, cards.load_json(os.path.join(bundle_path, "skills", ref, "skill.json"))) for ref in refs]
    cards.write_text(os.path.join(sdir, "library", "index.md"), library_index(manifests))
    for ref, m in manifests:
        cards.write_text(os.path.join(sdir, "library", ref + ".md"), skill_page(ref, m))
    return [ref for ref, _ in manifests]


READ_ONLY_TOOLS = (None, "none", "reads_instrument")


def check_drawing(skills, subagents, tool_effects, template_path):
    """Refuse what B11 would fail. `skills` are the library's rows for the skills the bundle is to carry and
    `tool_effects` is {tool name: its contract's side_effects} for the tools the bundle has."""
    rows, faults = {r["ref"]: r for r in skills}, []
    if skills and not os.path.isfile(os.path.join(template_path, "src", "run_skill.py")):
        faults.append("the template %s has no src/run_skill.py; skills need template v2 or later" % os.path.basename(template_path))
    for ref, r in sorted(rows.items()):
        if r["status"] == "held":
            faults.append("%s is held: it stays in the library and is named in the specification's held[], not in a bundle" % ref)
        for t in r["calls_tools"]:
            if t not in tool_effects:
                faults.append("%s calls the tool %s, which this bundle does not have" % (ref, t))
            elif r["side_effect"] == "read_device" and tool_effects[t] not in READ_ONLY_TOOLS:
                faults.append("%s says it only reads the device and calls %s, a tool with side effects %s" % (ref, t, tool_effects[t]))
        for other in r["uses_skills"]:
            if other not in rows:
                faults.append("%s uses %s, which the specification does not name" % (ref, other))
    writers = []
    for a in subagents:
        unknown = [e for e in a["side_effects"] if e not in SIDE_EFFECTS]
        if unknown:
            faults.append("subagent %s: side_effects %s are not %s" % (a["name"], unknown, " | ".join(SIDE_EFFECTS)))
        if "write_device" in a["side_effects"]:
            writers.append(a["name"])
            if a["name"] != WRITER:
                faults.append("subagent %s lists write_device; only %s may" % (a["name"], WRITER))
        for ref in a["skills"]:
            if ref not in rows:
                faults.append("subagent %s names %s, which the specification's skills do not" % (a["name"], ref))
            elif rows[ref]["side_effect"] != "none" and rows[ref]["side_effect"] not in a["side_effects"]:
                faults.append("subagent %s names %s, which is %s, and its side_effects are %s"
                              % (a["name"], ref, rows[ref]["side_effect"], a["side_effects"] or "none"))
    if len(writers) > 1:
        faults.append("%s all list write_device; one subagent alone may change a device" % ", ".join(writers))
    if len({a["name"] for a in subagents}) != len(subagents):
        faults.append("a subagent is named twice")
    if faults:
        raise ValueError("the skills and subagents of this specification cannot be built: " + "; ".join(faults))
    return rows


def add_skills(bundle_path, rows, subagents):
    """Copy each skill's folder unchanged and write the subagents' files."""
    for ref, r in sorted(rows.items()):
        shutil.copytree(r["folder"], os.path.join(bundle_path, "skills", ref), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    gk = os.path.join(bundle_path, "skills", ".gitkeep")
    if rows and os.path.exists(gk):
        os.remove(gk)
    for a in subagents:
        cards.write_text(os.path.join(bundle_path, ".claude", "agents", a["name"] + ".md"), subagent_markdown(a, rows))


def skill_id(ref):
    return ref.split("@v")[0]


def adaptation_row(folder, common, agreement):
    """The library row of a skill a build adapted from a common one (the person, 2026-11-18; tasks/025): a next version of
    a skill of the template's common set, saying adapted_from, naming its engine and not common itself. The agreement
    skill, which the bundle's own checks run, is not adapted. Raises ValueError for anything else."""
    from ..skills import catalogue as catalogue_mod
    m = cards.load_json(os.path.join(folder, "skill.json"))
    ref = "%s@v%d" % (m.get("id"), m.get("version") or 0)
    source = m.get("adapted_from")
    faults = []
    if source not in common:
        faults.append("%s says adapted_from %r, which is not a skill of the template's common set" % (ref, source))
    elif source == agreement:
        faults.append("%s adapts the agreement skill %s, which the bundle's own checks run and which is not adapted" % (ref, source))
    else:
        if skill_id(source) != m.get("id"):
            faults.append("%s is not a version of %s" % (ref, skill_id(source)))
        if (m.get("version") or 0) <= int(source.split("@v")[1]):
            faults.append("%s is not a later version than %s" % (ref, source))
    if m.get("common"):
        faults.append("%s is adapted, so it is not itself common" % ref)
    if not ((m.get("applies_to") or {}).get("engines")):
        faults.append("%s names no engine under applies_to.engines" % ref)
    if os.path.basename(os.path.normpath(folder)) != ref:
        faults.append("the folder of %s is named %s" % (ref, os.path.basename(os.path.normpath(folder))))
    if faults:
        raise ValueError("an adaptation cannot be built: " + "; ".join(faults))
    return dict(catalogue_mod.entry(folder, os.path.dirname(os.path.normpath(folder))), folder=folder)


def with_common(skills, common, adaptations, agreement):
    """The skills a simulation bundle carries: those the specification names, then each skill of the template's common set
    that it does not name in any version, an adaptation taking the place of the common skill it adapts."""
    from ..skills import catalogue as catalogue_mod
    adapted = [adaptation_row(f, common, agreement) for f in adaptations]
    by_id = {skill_id(r["ref"]): r for r in adapted}
    if len(by_id) != len(adapted):
        raise ValueError("two adaptations of one common skill")
    named = {skill_id(r["ref"]) for r in skills}
    out = list(skills)
    for ref in common:
        i = skill_id(ref)
        if i in by_id:
            if i in named:
                raise ValueError("the specification names %s and an adaptation of it is given as well" % i)
            out.append(by_id[i])
        elif i not in named:
            out.append(catalogue_mod.take([ref])[0])
    return out


def adaptations_section(bundle_path):
    """The lines of the difference from the template that name each skill a build adapted from a common one."""
    lines = []
    root = os.path.join(bundle_path, "skills")
    for name in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        path = os.path.join(root, name, "skill.json")
        if os.path.isfile(path):
            m = cards.load_json(path)
            if m.get("adapted_from"):
                lines.append("adapted   skills/%s  from %s, for %s" % (name, m["adapted_from"],
                                                                     ", ".join((m.get("applies_to") or {}).get("engines") or [])))
    return lines


def refinement_problems(tasks, tools, envelope, template_path):
    """What keeps a scientific task's refinement from running in this bundle (the intake card's refinement, template v23):
    a template that does not judge one, a skill the library lacks, an input the called tool does not take, a row the
    bundle's parameters do not hold, or a task that does not state one field."""
    from ..skills import catalogue as catalogue_mod
    out = []
    meta = os.path.join(template_path, "TEMPLATE.json")
    m = cards.load_json(meta) if os.path.isfile(meta) else {}
    if not m.get("tolerance_rule") or m.get("version") in (None,) or int(str(m.get("version", "v0"))[1:] or 0) < 23:
        out.append("the template %s does not judge a refinement; it needs v23 or later" % m.get("version"))
    rows = {r.get("name") for r in ((envelope.get("parameters") or {}).get("rows") or []) if isinstance(r, dict)}
    contracts = {t["name"]: t["contract"] for t in tools}
    for t in tasks:
        ref, tid = t["refinement"], t.get("id")
        stated = (t.get("measure") or {}).get("stated")
        if not isinstance(stated, dict) or len(stated) != 1:
            out.append("%s: a refinement judges one stated field" % tid)
        if catalogue_mod.find(ref.get("skill") or "") is None:
            out.append("%s: the library has no skill %s" % (tid, ref.get("skill")))
        props = ((contracts.get((t.get("call") or {}).get("tool")) or {}).get("inputs") or {}).get("properties") or {}
        if not ref.get("inputs"):
            out.append("%s: a refinement names at least one input of the finer run" % tid)
        for name, row in sorted((ref.get("inputs") or {}).items()):
            if name not in props:
                out.append("%s: the tool takes no input %s" % (tid, name))
            if row not in rows:
                out.append("%s: no row %s hands the finer run its %s" % (tid, row, name))
        third = ref.get("third_inputs")
        keys = ("ratio_row",) if third else ("ratio_row", "order_row")
        for key in keys:
            if ref.get(key) not in rows:
                out.append("%s: no row %s for its %s" % (tid, ref.get(key), key))
        if third:
            if not m.get("order_skill"):
                out.append("%s: the template %s does not observe an order from a third run; it needs v25 or later" % (tid, m.get("version")))
            for name, row in sorted(third.items()):
                if name not in props:
                    out.append("%s: the tool takes no input %s for the third run" % (tid, name))
                if row not in rows:
                    out.append("%s: no row %s hands the third run its %s" % (tid, row, name))
    return out


def stated_unit(task, tools, skills):
    """The unit of the one field a scientific task states: the analysis skill's output unit where the task measures
    through one, else the unit the called tool's contract declares for that output, else '1'."""
    stated = (task.get("measure") or {}).get("stated") or {}
    field = next(iter(stated))
    analysis = task.get("analysis") if isinstance(task.get("analysis"), dict) else None
    if analysis:
        for r in skills:
            if r.get("ref") == analysis.get("skill"):
                for o in r.get("outputs") or []:
                    if o.get("name") == field and o.get("unit"):
                        return o["unit"]
    tool = ((task.get("call") or {}).get("tool"))
    for t in tools:
        if t["name"] == tool:
            prop = (((t["contract"].get("outputs") or {}).get("properties") or {}).get(field) or {})
            if prop.get("unit"):
                return prop["unit"]
    return "1"


def with_rule_tolerance(task, rule, tools, skills):
    """The task with a tolerance derived by the person's standing rule of 2026-11-18, where the person gave none and the
    task states one field (a tolerance judges one field): the rule's skill runs through the runner on the reference as
    the task prints it (measure.printed), else on the stored number, with the stated uncertainty where the task gives
    one (measure.stated_uncertainty). The task records how the tolerance came under tolerance_derivation. A task the
    rule gives no tolerance for is left as it is, undecided."""
    stated = (task.get("measure") or {}).get("stated")
    if task.get("tolerance") or not isinstance(stated, dict) or len(stated) != 1:
        return task
    if isinstance(task.get("refinement"), dict):
        # its tolerance is derived when it runs, from the run's own error (template v23); the build hands it the unit
        return dict(task, tolerance_unit=stated_unit(task, tools, skills))
    from ..skills import runner as runner_mod
    field, value = next(iter(stated.items()))
    printed = ((task.get("measure") or {}).get("printed") or {}).get(field)
    printed_from = "measure.printed"
    if not isinstance(printed, str):
        printed, printed_from = (repr(value) if not isinstance(value, bool) else None), "the stored number"
    uncertainty = ((task.get("measure") or {}).get("stated_uncertainty") or {}).get(field)
    inputs = {"printed": printed, "stated_uncertainty": uncertainty}
    from ..skills import catalogue as catalogue_mod
    folder = catalogue_mod.find(rule["skill"])
    names = {i.get("name") for i in (cards.load_json(os.path.join(folder, "skill.json")).get("inputs") or [])} if folder else set()
    if "run_numerical_error" in names:
        # the run's own error is not known when the bundle is built, before any run: the half-digit branch applies, and
        # the skill's output says the run's error was not estimated (the person's amended rule of 2026-11-18)
        inputs["run_numerical_error"] = None
    if "run_error_from" in names:
        inputs["run_error_from"] = None      # no run's error at build time, so nothing says how one was estimated
    record = runner_mod.run(rule["skill"], inputs)
    out = record.get("outputs") or {}
    if record.get("verdict") != "ran" or out.get("tolerance") is None:
        return task
    t = dict(task)
    t["tolerance"] = {"value": out["tolerance"], "unit": stated_unit(task, tools, skills), "chosen_by": "rule",
                      "rule": rule["rule"], "derived_by": "computed:%s" % rule["skill"], "from": out["from"]}
    t["tolerance_derivation"] = {"skill": rule["skill"], "inputs": record.get("inputs"), "outputs": out,
                                 "printed_from": printed_from if out["from"] == "last_printed_digit" else None}
    return t


def compose(template_path, bundle_path, fill, tools, capabilities, envelope, interface_tasks,
            scientific_tasks, replay_items, skills=None, subagents=None, workflow=None, words=None, decisions=None,
            ids=None, questions=None, simulation=False, adaptations=None, tool_kind=None, engine=None):
    """Write the bundle. `tools` is a list of {name, contract, adapter_source, errors:[contract]}.

    `workflow` is the request's order of tool names, or None, and fills the Workflow section of a template that has
    one. `words` is {record path: [the person's words]}: each task, replay item and TEMPLATE.json that names a record
    of the builder's repository the bundle does not carry is marked with builder_records, quoting them; so is each that
    names one of `ids` (the builder's cards the build read) or one of `questions` (the intake's {n: question}).
    An optional input of a tool that names neither a row nor a default is refused before anything is written.

    `skills` is the library's rows for the `<id>@v<n>` the specification names, in the specification's order
    (src/skills/catalogue.take: each row carries its `folder`), and `subagents` the specification's list of
    {name, description, skills, side_effects}. The drawing is checked before anything is written, and one
    that B11 would fail raises ValueError."""
    if os.path.exists(bundle_path):
        raise FileExistsError("bundle exists: %s (a rebuild is a new build id)" % bundle_path)
    skills, subagents = list(skills or []), list(subagents or [])
    # a template that names an agreement skill (v16 on) has src/validate_tasks.py take each scientific task's agreement
    # from it, so every bundle with a scientific task carries it (cfd-7: the agreement is a library skill's output)
    meta = os.path.join(template_path, "TEMPLATE.json")
    agreement = cards.load_json(meta).get("agreement_skill") if os.path.isfile(meta) else None
    if agreement and scientific_tasks and agreement not in {r["ref"] for r in skills}:
        from ..skills import catalogue as catalogue_mod
        skills.append(catalogue_mod.take([agreement])[0])
    refining = [t for t in scientific_tasks or [] if isinstance(t.get("refinement"), dict)]
    if refining:
        faults = refinement_problems(refining, tools, envelope, template_path)
        if faults:
            raise ValueError("a scientific task's refinement cannot run in this bundle: " + "; ".join(faults))
        from ..skills import catalogue as catalogue_mod
        need = [t["refinement"]["skill"] for t in refining] + [cards.load_json(meta)["tolerance_rule"]["skill"]]
        if any(t["refinement"].get("third_inputs") for t in refining):
            need.append(cards.load_json(meta)["order_skill"])
        for ref in need:
            if ref not in {r["ref"] for r in skills}:
                skills.append(catalogue_mod.take([ref])[0])
    interval = cards.load_json(meta).get("interval_skill") if os.path.isfile(meta) else None
    if interval and interval not in {r["ref"] for r in skills} and any(
            isinstance(t.get("tolerance"), dict) and "interval" in t["tolerance"] for t in scientific_tasks or []):
        # a task judged by an interval the person gave needs the skill that judges it (cfd-19)
        from ..skills import catalogue as catalogue_mod
        skills.append(catalogue_mod.take([interval])[0])
    common = (cards.load_json(meta).get("common_skills") if os.path.isfile(meta) else None) or []
    if common and simulation:
        skills = with_common(skills, common, adaptations or [], agreement)
    elif adaptations:
        raise ValueError("an adaptation of a common skill is built only into a simulation bundle of a template that carries "
                         "the common set")
    rule = (cards.load_json(meta).get("tolerance_rule") if os.path.isfile(meta) else None) or None
    if rule and scientific_tasks:
        scientific_tasks = [with_rule_tolerance(t, rule, tools, skills) for t in scientific_tasks]
    rows = check_drawing(skills, subagents, {t["name"]: t["contract"].get("side_effects") for t in tools}, template_path)
    fill = dict(fill)
    if skills:
        users = {r["ref"]: [a["name"] for a in subagents if r["ref"] in a["skills"]] for r in skills}
        fill["skills_section"] = skills_section(
            [(r["ref"], r["description"].rstrip(".") + "."
              + (" Used by %s." % ", ".join("`%s`" % u for u in users[r["ref"]]) if users[r["ref"]] else "")) for r in skills])
    fill.setdefault("subagents_section", subagents_section(subagents))
    fill.setdefault("workflow_section", workflow_section(workflow, [t["name"] for t in tools]))
    row_names = {r.get("name") for r in (envelope.get("parameters") or {}).get("rows") or [] if isinstance(r, dict)}
    fill.setdefault("decisions_section", decisions_section(decisions, [t["contract"] for t in tools], skills, row_names))
    faults = analysis_problems(scientific_tasks, [t["contract"] for t in tools], skills, row_names)
    if faults:
        raise ValueError("the scientific tasks' analyses cannot run in this bundle: " + "; ".join(faults))
    faults = default_problems([t["contract"] for t in tools])
    if faults:
        raise ValueError("a tool's input is left to its adapter: " + "; ".join(faults))
    shutil.copytree(template_path, bundle_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    add_skills(bundle_path, rows, subagents)
    add_pages(bundle_path, [r["ref"] for r in skills])
    claude = cards.read_text(os.path.join(bundle_path, "CLAUDE.md"))
    cards.write_text(os.path.join(bundle_path, "CLAUDE.md"), render(claude, fill))
    if tool_kind:
        # what kind of tool the agent is for (the intake's tool.kind), which bundle check B18 reads to know a simulation
        # bundle (the design role's ask 20261118-design-macbook-20261117-1-8; tasks/025)
        capabilities = dict(capabilities, tool_kind=tool_kind)
    if engine:
        # the engine's id in contracts/registry/engines.json, which bundle check B9 reads where a package source is
        # allowed for named engines alone (the design role's message of 2026-11-18; 3a0c4ec)
        capabilities = dict(capabilities, engine=engine)
    cards.write_json(os.path.join(bundle_path, "CAPABILITIES.json"), capabilities)
    for name, content in envelope.items():
        cards.write_json(os.path.join(bundle_path, "envelope", name + ".json"), content)
    for t in tools:
        tdir = os.path.join(bundle_path, "tools", t["name"])
        cards.write_json(os.path.join(tdir, "tool.json"), t["contract"])
        cards.write_text(os.path.join(tdir, "adapter.py"), t["adapter_source"])
        # one file per contract: the first of a category is errors/<category>.json, which the runner returns itself,
        # and each later one errors/<category>.<code>.json, so that no contract of the intake is lost (cfd-2, dft-2)
        seen = set()
        for e in t.get("errors", []):
            name = e["category"] if e["category"] not in seen else "%s.%s" % (e["category"], e["code"])
            seen.add(e["category"])
            cards.write_json(os.path.join(tdir, "errors", name + ".json"), e)
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
    mark_builder_records(bundle_path, words, ids=ids or (), questions=questions)
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
    adapted = adaptations_section(bundle_path)
    if adapted:
        lines.extend(["", "# skills adapted from the common library (a next version each, made by this build for its engine)"] + adapted)
    lines.append("")
    for rel in sorted(t_files & b_files):
        tp, bp = os.path.join(template_path, rel), os.path.join(bundle_path, rel)
        if rel.endswith(TEXT_EXT) and cards.sha256_file(tp) != cards.sha256_file(bp):
            a = cards.read_text(tp).splitlines(keepends=True)
            b = cards.read_text(bp).splitlines(keepends=True)
            lines.extend(l.rstrip("\n") for l in difflib.unified_diff(a, b, "template/" + rel, "bundle/" + rel))
            lines.append("")
    return "\n".join(lines) + "\n"


def make_build_card(build_id, rid, spec, lab_profile_ref, template_name, diff_path, bundle_rel, sha, seat, now=None,
                    parent_build=None):
    card = cards.skeleton("build", build_id, seat, cards.now_iso(now), rid=rid)
    card["spec_ref"] = spec["id"]
    card["lab_profile_ref"] = lab_profile_ref
    card["template_version"] = template_name
    card["diff_from_template"] = diff_path
    card["bundle_path"] = bundle_rel
    card["bundle_sha256"] = sha
    card["held"] = list(spec.get("held", []))
    card["gate_verdict"] = {"interface": "not_run", "scientific": "not_run", "validation_report_ref": None}
    card["lineage"] = {"parent_build": parent_build, "candidate_of": 1, "k": 1}
    card["landed_at"] = None
    return card
