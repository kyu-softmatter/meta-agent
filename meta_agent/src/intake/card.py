"""S1 Intake: the request's first card (plan.md 5.1, 6.1, 14-39; contracts/schemas/intake.schema.json).

    python -m meta_agent.src.intake write   --rid <rid> --draft <file> --seat <seat> [--note "<what changed>"]
    python -m meta_agent.src.intake answer  --rid <rid> --n <n> --verbatim "<the person's words>" --date <YYYY-MM-DD>
                                            --seat <seat> [--gloss "<English>"] [--recorded-in <docs/ideas file>]
    python -m meta_agent.src.intake waiting --rid <rid>
    python -m meta_agent.src.intake check   <intake file>

A session writes no intake by a script of its own. It writes a *draft*: one JSON object that holds what
a session knows of the request and nothing the stage writes. The fields of a draft are the fields of the
schema but these, which are the stage's: card, schema_version, id, rid, revision, supersedes,
superseded_by, author, created_at, numbers, degraded, status, stage and revision_note.

`write` makes the card from the draft. The first time it writes requests/<rid>/intake.json, revision 1.
After that the draft holds only what changes: its fields take the place of the same fields of the latest
revision, a field given as null is taken out, and the card is written as the next revision,
v<N>_intake.json, with `--note` as its revision_note (records are append-only). Nothing is written when
the draft changes nothing.

The stage is not chosen, it follows from what the card carries: `specified` when it carries a tool
contract (tool_contract, or tools) and then it must carry the interface tasks and the replay items too;
`reading` otherwise. The Designer is run on a card at `specified` and refuses one at `reading`.

`answer` records what the person said to one question, verbatim, as the next revision. `waiting` prints
the questions that have no answer yet, each with what it is needed before; it writes nothing.

What is refused, before anything is written: a draft with a field the schema does not name or a field
that is the stage's; a card the schema would fail; a number in `numbers`, and a bare number in the words
a goal is made from (the paragraph, the science task, the destination, what it must not do, what it
needs, its parameters and priorities), since the model makes no numbers and a value read from a source
is a row of values_read with the place it was read; questions whose numbers are not 1, 2, 3, ... in
order; an answer to a question the card does not ask.

Read with the gate's own rules, as the card is read with the schema (test run 20261116-7): a scientific task
whose `tolerance` or `reference_spec` the validation report's schema would refuse, since the bundle's runner
carries both into that report as they are; a number check 3 would refuse on tool_profile.md, which the
Designer renders from the tool, its reading and its contracts (the page is rendered here as the Designer
renders it, and a number passes when a card of the request folder or the card itself carries it, the places
a reading was read included); and a number check B6 would refuse in the Tools section of the bundle's
CLAUDE.md, which is rendered from the contracts (B6 lets a number through only when the bundle's knowledge
snapshot carries it, and the snapshot is made at the build, so the stage lets none through). The number
rules, the units and the stripping are imported from contracts/validate.py and never copied.

And each contract a card carries, read with the gate's tool_contract and error_contract schemas, since the
bundle carries them as tools/<name>/tool.json and tools/<name>/errors/ and check 1 judges them there; and, where
the card is written into a request folder of a meta_agent/ tree, each adapter_source, which must be a file under
that tree, as the Designer reads it (test run 20261117-1, collect-1: a card named its adapters from the
repository root and the Designer did not find them).
"""
import importlib.util
import json
import os
import re

from .. import cards
from ..build import bundle as bundle_mod
from ..tooling import profile as profile_mod
from . import goal as goal_mod

META = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(META)
SCHEMAS = os.path.join(REPO, "contracts", "schemas")
STAGE_WRITES = ("card", "schema_version", "id", "rid", "revision", "supersedes", "superseded_by", "author", "created_at",
                "numbers", "degraded", "status", "stage", "revision_note")
CONTRACT_FIELDS = ("tool_contract", "tools")
REVISION = re.compile(r"^(?:v([0-9]+)_)?intake\.json$")


_GATE = []


def gate_rules():
    """contracts/validate.py, loaded once as a module, for the number rules of checks 3 and B6."""
    if not _GATE:
        spec = importlib.util.spec_from_file_location("meta_agent_gate_rules", os.path.join(REPO, "contracts", "validate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _GATE.append(mod)
    return _GATE[0]


class Refused(ValueError):
    """The stage wrote nothing; the message says every reason."""


def schema():
    return cards.load_json(os.path.join(SCHEMAS, "intake.schema.json"))


def session_fields():
    """The fields a draft may carry: the schema's, less the stage's own."""
    return [k for k in schema()["properties"] if k not in STAGE_WRITES]


def is_card(intake):
    """An intake of the card's shape. The two requests of before the card carry no `card` key and are read as they are."""
    return isinstance(intake, dict) and intake.get("card") == "intake"


def stage_of(fields):
    return "specified" if any(k in fields for k in CONTRACT_FIELDS) else "reading"


def latest(req_dir):
    """(revision, path) of the latest intake of a request folder; (0, None) when it has none."""
    found = []
    for fn in os.listdir(req_dir) if os.path.isdir(req_dir) else []:
        m = REVISION.match(fn)
        if m:
            found.append((int(m.group(1) or 1), os.path.join(req_dir, fn)))
    return max(found) if found else (0, None)


def validator(sch):
    """A validator of `sch` that resolves the references between the schemas of contracts/schemas/, or None
    without the jsonschema package."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    store = {}
    for fn in os.listdir(SCHEMAS):
        if fn.endswith(".schema.json"):
            s = cards.load_json(os.path.join(SCHEMAS, fn))
            store[s["$id"]] = s
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
        registry = Registry().with_resources([(uri, Resource.from_contents(s, default_specification=DRAFT202012))
                                              for uri, s in store.items()])
        return Draft202012Validator(sch, registry=registry)
    except ImportError:
        import jsonschema
        return Draft202012Validator(sch, resolver=jsonschema.RefResolver(base_uri=sch["$id"], referrer=sch, store=store))


def errors_of(v, instance, prefix=""):
    out = []
    for e in sorted(v.iter_errors(instance), key=lambda e: [str(p) for p in e.absolute_path]):
        where = "/".join([prefix] * bool(prefix) + [str(p) for p in e.absolute_path]) or "the card"
        out.append("%s: %s" % (where, e.message if len(e.message) < 240 else e.message[:240] + " ..."))
    return out


def schema_problems(card):
    """What the gate's check 1 would say of the card, read with the same schema. Without the jsonschema
    package only the required fields are looked at, and the gate is the judge."""
    sch = schema()
    v = validator(sch)
    if v is None:
        return ["%s is missing" % k for k in sch["required"] if k not in card]
    return errors_of(v, card)


def report_task_problems(card):
    """A scientific task's tolerance and reference_spec, read with the validation report's schema: the bundle's
    runner prints both as they are and S6 writes them into the report, where check 1 judges them."""
    vr = cards.load_json(os.path.join(SCHEMAS, "validation_report.schema.json"))
    task = vr["properties"]["scientific"]["properties"]["tasks"]["items"]["properties"]
    out = []
    for key, prop in (("tolerance", "tolerance"), ("reference_spec", "reference")):
        v = validator(dict(task[prop], **{"$id": vr["$id"]}))       # the report's base, so that its references resolve
        if v is None:
            return out
        for i, t in enumerate(card.get("scientific_tasks") or []):
            if isinstance(t, dict) and key in t:
                out += ["%s (the validation report's %s refuses it)" % (line, prop)
                        for line in errors_of(v, t[key], "scientific_tasks/%d/%s" % (i, key))]
    return out


def contract_problems(card):
    """Each contract the card carries, read with the schemas the gate reads it with in a bundle."""
    out = []
    tc = validator(cards.load_json(os.path.join(SCHEMAS, "tool_contract.schema.json")))
    ec = validator(cards.load_json(os.path.join(SCHEMAS, "error_contract.schema.json")))
    if tc is None or ec is None:
        return out
    if card.get("tools"):
        places = [("tools/%d/contract" % i, t.get("contract"), "tools/%d/error_contracts" % i, t.get("error_contracts"))
                  for i, t in enumerate(card["tools"]) if isinstance(t, dict)]
    elif isinstance(card.get("tool_contract"), dict):
        places = [("tool_contract", card["tool_contract"], "error_contracts", card.get("error_contracts"))]
    else:
        places = []
    for where, contract, ewhere, errors in places:
        if isinstance(contract, dict):
            out += ["%s (the gate's tool_contract schema refuses it)" % line for line in errors_of(tc, contract, where)]
        for j, e in enumerate(errors or []):
            out += ["%s (the gate's error_contract schema refuses it)" % line for line in errors_of(ec, e, "%s/%d" % (ewhere, j))]
    return out


def tree_of(req_dir):
    """The meta_agent/ tree a request folder is in, or None when the folder is not <tree>/requests/<rid>."""
    if not req_dir:
        return None
    req_dir = os.path.abspath(req_dir)
    parent = os.path.dirname(req_dir)
    return os.path.dirname(parent) if os.path.basename(parent) == "requests" else None


def adapter_problems(card, req_dir=None):
    """Each adapter_source must be a file under the tree the request is in, where the Designer reads it."""
    root = tree_of(req_dir)
    if root is None or card.get("stage") != "specified":
        return []
    if card.get("tools"):
        named = [("tools/%d/adapter_source" % i, t.get("adapter_source")) for i, t in enumerate(card["tools"]) if isinstance(t, dict)]
    else:
        named = [("tool/adapter_source", (card.get("tool") or {}).get("adapter_source"))]
    out = []
    for where, src in named:
        if not isinstance(src, str) or not src:
            out.append("%s: a specified card names the source of each adapter, under %s" % (where, os.path.basename(root)))
            continue
        if os.path.isfile(os.path.join(root, src)):
            continue
        line = "%s: %s is not a file under %s/, where the Designer reads it" % (where, src, os.path.basename(root))
        head = os.path.basename(root) + "/"
        if src.startswith(head) and os.path.isfile(os.path.join(root, src[len(head):])):
            line += "; it is named from the repository root, and under %s it is %s" % (head, src[len(head):])
        out.append(line)
    return out


def numbers_left(text, available, extra=()):
    """The numbers of a page that the gate's number rule would refuse: stripped as the gate strips, then each
    numeral not in `available`."""
    rules = gate_rules()
    for s in list(rules.STRIP_RES) + list(extra):
        text = s.sub(" ", text)
    out = []
    for m in rules.NUM_RE.finditer(text):
        try:
            val = float(m.group(0))
        except ValueError:
            continue
        if val not in available and m.group(0) not in out:
            out.append(m.group(0))
    return out


def contracts_of(card):
    tools = [t.get("contract") for t in card.get("tools") or [] if isinstance(t, dict) and isinstance(t.get("contract"), dict)]
    return tools or ([card["tool_contract"]] if isinstance(card.get("tool_contract"), dict) else [])


def page_problems(card, req_dir=None):
    """The numbers check 3 would refuse on tool_profile.md and check B6 in the Tools section of the bundle's
    CLAUDE.md, both rendered from the card as the Designer renders them."""
    rules = gate_rules()
    out = []
    try:
        profile = profile_mod.make_profile(card, card.get("author") or "the stage")
        page = profile_mod.markdown(profile)
    except (KeyError, TypeError, ValueError) as e:
        return ["tool_reading: the Designer could not make the tool profile from this card: %s" % e]
    available = set()
    near = [card, profile]
    for fn in sorted(os.listdir(req_dir)) if req_dir and os.path.isdir(req_dir) else []:
        if fn.endswith(".json"):
            try:
                data = cards.load_json(os.path.join(req_dir, fn))
            except ValueError:
                continue
            if isinstance(data, dict) and (isinstance(data.get("card"), str) or isinstance(data.get("artifact"), str)):
                near.append(data)
    for data in near:
        rules.json_numbers(data, available)
        rules.locus_numbers(data, available)
    for n in numbers_left(page, available):
        out.append("tool_reading: tool_profile.md would carry the number %s, which no card of the request folder carries, "
                   "and check 3 refuses it; a value read is a row of values_read with its place, and a claim names it "
                   "in words" % n)
    units = rules.unit_res(cards.load_json(os.path.join(rules.HERE, "units.json"))["units"])
    extra = [rules.FIELD_UNIT_ONE_RE] + ([units] if units else [])
    for c in contracts_of(card):
        try:
            section = bundle_mod.tools_section([c])
        except (KeyError, TypeError, AttributeError):
            continue                        # the schema's problems say what is wrong with the contract
        for n in numbers_left(section, set(), extra):
            out.append("tools: the Tools section of the bundle's CLAUDE.md would carry the number %s from the contract "
                       "of %s, and check B6 refuses a number the bundle's snapshot does not carry; the contract says it "
                       "in words, or a parameter row or an enumeration carries it" % (n, c.get("name")))
    return out


def problems(card, req_dir=None):
    """Every reason the stage would not write this card. `req_dir` is the request folder, whose cards check 3
    reads beside the card."""
    out = schema_problems(card)
    out += report_task_problems(card)
    out += contract_problems(card)
    out += page_problems(card, req_dir)
    if card.get("numbers"):
        out.append("numbers: the model makes no numbers; a value read from a source is a row of values_read")
    goal_like = dict(card, purpose=card.get("paragraph"))
    for field, number in goal_mod.numbers_in(goal_like):
        out.append("%s: the bare number %s; a goal is made from these words and carries no number" % (
            "paragraph" if field == "purpose" else field, number))
    asked = [q.get("n") for q in card.get("questions_for_the_person") or [] if isinstance(q, dict)]
    if asked != list(range(1, len(asked) + 1)):
        out.append("questions_for_the_person: the questions are numbered %s, not 1, 2, 3, ... in order" % asked)
    if card.get("stage") != stage_of(card):
        out.append("stage: the card says %r and carries what a card at %r carries" % (card.get("stage"), stage_of(card)))
    out += adapter_problems(card, req_dir)
    out += workflow_problems(card)
    out += row_problems(card, req_dir)
    out += decisions_problems(card, req_dir)
    for item, phrase in held_named(card.get("science_task"), card.get("held")):
        out.append("science_task: it names %s, which held[] holds (%s); a science task names what the bundle computes: "
                   "narrow it in this revision, or a person releases the item" % (phrase, item))
    return out


def decisions_problems(card, req_dir=None, library=None):
    """The decisions a card names, judged as the build judges them (bundle.decision_problems): each a diagnostic skill
    of the card's skills, on a field one of its tools returns, every criterion handed by a row the bundle will carry."""
    if not card.get("decisions"):
        return []
    from ..skills import catalogue as catalogue_mod
    try:
        rows = catalogue_mod.take(card.get("skills") or [], *([library] if library else []))
    except ValueError as e:
        return ["decisions: %s" % e]
    _, params = rows_given(card, req_dir)
    return bundle_mod.decision_problems(card["decisions"], contracts_of(card), rows,
                                        {r.get("name") for r in params if isinstance(r, dict)})


LEADING = ("the", "a", "an", "its", "their", "other", "all", "any")
SEGMENT_RE = re.compile(r"[(),;:]|\band\b|\bor\b", re.I)


def stem(token):
    return token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith("ss") else token


def words_of(text):
    """Lower-case word stems, hyphens, underscores and slashes read as spaces."""
    return [stem(t) for t in re.findall(r"[a-z0-9]+", re.sub(r"[-_/]", " ", str(text or "").lower()))]


def held_phrases(item):
    """The phrases a held item names: the item cut at brackets, commas, 'and' and 'or', each part without a leading
    article; a part counts when it has two words or more, or is one identifier (an underscore or an inner capital)."""
    out = []
    for part in SEGMENT_RE.split(str(item or "")):
        raw = part.strip()
        words = words_of(raw)
        while words and words[0] in LEADING:
            words = words[1:]
        if len(words) >= 2 or (len(words) == 1 and re.search(r"_|[a-z][A-Z]", raw)):
            out.append(words)
    return out


def held_named(science_task, held):
    """[(held item, the phrase in the science task)] for each item of held[] not yet released whose phrase the science
    task names (tasks/016, run 20261117-7, rheotool-2: a science task written at the first revision named quantities a
    later revision held, and the bundle's CLAUDE.md named what it does not compute)."""
    task = words_of(science_task)
    out = []
    for h in held or []:
        if isinstance(h, dict) and (h.get("released_by") or h.get("released_at")):
            continue
        item = h.get("item") if isinstance(h, dict) else h
        for words in held_phrases(item):
            n = len(words)
            if any(task[i:i + n] == words for i in range(len(task) - n + 1)):
                out.append((str(item), " ".join(words)))
    return out


ROW_IN_WORDS_RE = re.compile(
    r"\brow\s+(?!(?:of|in|from|that|which|a|an|the|for|is|it|its|given|named|per|by|with|to|and|or|as|at|on|whose|this|each)\b)"
    r"`?([a-z][a-z0-9_]*)`?", re.I)


def input_properties(schema, at="inputs"):
    """(place, property) for every property of a contract's input schema, at any depth."""
    out = []
    if isinstance(schema, dict):
        for key, prop in sorted((schema.get("properties") or {}).items()):
            if isinstance(prop, dict):
                here = "%s.%s" % (at, key)
                out.append((here, prop))
                out += input_properties(prop, here)
        if isinstance(schema.get("items"), dict):
            out += input_properties(schema["items"], at + "[]")
    return out


def named_rows(card):
    """{tool: [(place, row)]}: the parameter rows the card's contracts name under `row`, read as bundle check B17
    reads them."""
    rules = gate_rules().tool_contract_rules
    return {c.get("name"): rules.named_rows(c.get("inputs")) for c in contracts_of(card) if isinstance(c, dict)}


def newest_sheet(req_dir):
    """(file name, rows) of the request's newest parameter_sheet, or (None, None)."""
    if not req_dir or not os.path.isdir(req_dir):
        return None, None
    best, name = 0, None
    for f in os.listdir(req_dir):
        m = re.match(r"^(?:v(\d+)_)?parameter_sheet\.json$", f)
        if m and int(m.group(1) or 1) > best:
            best, name = int(m.group(1) or 1), f
    if name is None:
        return None, None
    return name, list(cards.load_json(os.path.join(req_dir, name)).get("rows") or [])


def rows_given(card, req_dir=None):
    """(where, rows) the bundle's parameter file is made from: the card's parameter_rows, or where it gives none
    the request's newest parameter_sheet (tasks/016, run 20261117-3), or (None, [])."""
    if card.get("parameter_rows"):
        return "the intake's parameter_rows", list(card["parameter_rows"])
    name, rows = newest_sheet(req_dir)
    if name:
        return "the request's newest parameter sheet %s" % name, rows
    return None, []


def row_problems(card, req_dir=None):
    """A contract input a row gives names it under `row`, where B17 reads it, and not in its description alone; and
    every row a contract names is one the bundle will carry (tasks/016, run 20261117-3)."""
    out = []
    for c in contracts_of(card):
        if not isinstance(c, dict):
            continue
        for place, prop in input_properties(c.get("inputs")):
            m = ROW_IN_WORDS_RE.search(str(prop.get("description") or ""))
            if m and not isinstance(prop.get("row"), str) and not prop.get("rows"):
                out.append("tools[%s].%s: its description names the row %s in words; a contract names it under row, "
                           "where the bundle's gate reads it" % (c.get("name"), place, m.group(1)))
    named = {row for pairs in named_rows(card).values() for _, row in pairs}
    if named and card.get("stage", "specified") == "specified":
        where, rows = rows_given(card, req_dir)
        have = {r.get("name") for r in rows if isinstance(r, dict)}
        missing = sorted(named - have)
        if missing:
            out.append("parameter rows: the contracts name %s, which %s; the bundle's parameter file is made from the "
                       "intake's parameter_rows, or where it gives none from the request's newest parameter sheet"
                       % (", ".join(missing), ("%s does not hold" % where) if where else
                          "neither the intake's parameter_rows nor a parameter sheet of the request gives"))
    return out


def workflow_problems(card):
    """The workflow, where a card gives one, names each of its tools once and no other (the Workflow section of
    the bundle renders it in this order; test run 20261117-2)."""
    order = card.get("workflow")
    if order is None:
        return []
    names = [c.get("name") for c in contracts_of(card) if isinstance(c, dict)]
    out = ["workflow: %r is not a tool of this card; its tools are %s" % (n, names) for n in order if n not in names]
    if len(set(map(str, order))) != len(order):
        out.append("workflow: a tool is named twice")
    return out


def make(rid, draft, seat, now=None, prior=None, prior_revision=0, note=None, req_dir=None):
    """The card a draft gives. `prior` is the latest intake of the request, a card or one of the records of
    before the card, and `prior_revision` its number. Returns the card, or None when the draft changes
    nothing of `prior`. Raises Refused and writes nothing."""
    if not isinstance(draft, dict):
        raise Refused("a draft is one JSON object")
    allowed = session_fields()
    faults = ["%s is written by the stage, not by a draft" % k for k in sorted(draft) if k in STAGE_WRITES]
    faults += ["%s is not a field of an intake" % k for k in sorted(draft) if k not in allowed and k not in STAGE_WRITES]
    if faults:
        raise Refused("; ".join(faults))
    fields = {k: v for k, v in (prior or {}).items() if k in allowed}
    for k, v in draft.items():
        if v is None and k != "analysis_permission":
            fields.pop(k, None)
        else:
            fields[k] = v
    if prior is not None and fields == {k: v for k, v in prior.items() if k in allowed}:
        return None
    if prior is not None and not (note or "").strip():
        raise Refused("a next revision says what changed and on whose word: give --note")
    card = {"card": "intake", "schema_version": cards.SCHEMA_VERSION, "id": "intake-" + rid.replace("req-", "", 1), "rid": rid,
            "revision": prior_revision + 1}
    if is_card(prior):
        card["supersedes"] = prior["id"]
    card.update({"author": seat, "created_at": cards.now_iso(now), "numbers": [], "degraded": [], "status": "draft",
                 "stage": stage_of(fields)})
    if prior is not None:
        card["revision_note"] = note.strip()
    for k in allowed:               # the schema's order, so that the same draft gives the same file
        if k in fields:
            card[k] = fields[k]
    found = problems(card, req_dir)
    if found:
        raise Refused("; ".join(found))
    return card


def write(req_dir, rid, draft, seat, now=None, note=None):
    """Write the card a draft gives into a request folder. Returns (path or None, card): no path when
    the draft changes nothing."""
    rev, path = latest(req_dir)
    prior = cards.load_json(path) if path else None
    if prior is not None and prior.get("rid") != rid:
        raise Refused("%s holds the intake of %r, not of %r" % (req_dir, prior.get("rid"), rid))
    card = make(rid, draft, seat, now, prior, rev, note, req_dir)
    if card is None:
        return None, prior
    target = os.path.join(req_dir, "intake.json" if rev == 0 else "v%d_intake.json" % (rev + 1))
    if os.path.exists(target):
        raise FileExistsError(target)
    cards.write_json(target, card)
    return target, card


def waiting(intake):
    """The questions of an intake that have no answer yet."""
    return [q for q in intake.get("questions_for_the_person") or [] if isinstance(q, dict) and not q.get("answer")]


def answer(req_dir, rid, n, verbatim, date, seat, gloss=None, recorded_in=None, now=None):
    """The person's words to question n, as the next revision of the request's intake."""
    rev, path = latest(req_dir)
    if path is None:
        raise Refused("no intake in %s" % req_dir)
    prior = cards.load_json(path)
    questions = json.loads(json.dumps(prior.get("questions_for_the_person") or []))
    hit = [q for q in questions if q.get("n") == n]
    if not hit:
        raise Refused("the intake asks no question %r; it asks %s" % (n, [q.get("n") for q in questions] or "none"))
    if hit[0].get("answer"):
        raise Refused("question %d has its answer already; an answer is not written over" % n)
    said = {"verbatim": verbatim, "date": date}
    if gloss:
        said["gloss"] = gloss
    if recorded_in:
        said["recorded_in"] = recorded_in
    hit[0]["answer"] = said
    return write(req_dir, rid, {"questions_for_the_person": questions}, seat, now,
                 note="the person's answer to question %d, in the person's words" % n)
