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
"""
import json
import os
import re

from .. import cards
from . import goal as goal_mod

META = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(META)
SCHEMAS = os.path.join(REPO, "contracts", "schemas")
STAGE_WRITES = ("card", "schema_version", "id", "rid", "revision", "supersedes", "superseded_by", "author", "created_at",
                "numbers", "degraded", "status", "stage", "revision_note")
CONTRACT_FIELDS = ("tool_contract", "tools")
REVISION = re.compile(r"^(?:v([0-9]+)_)?intake\.json$")


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


def schema_problems(card):
    """What the gate's check 1 would say of the card, read with the same schema. Without the jsonschema
    package only the required fields are looked at, and the gate is the judge."""
    sch = schema()
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["%s is missing" % k for k in sch["required"] if k not in card]
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
        validator = Draft202012Validator(sch, registry=registry)
    except ImportError:
        import jsonschema
        validator = Draft202012Validator(sch, resolver=jsonschema.RefResolver(base_uri=sch["$id"], referrer=sch, store=store))
    out = []
    for e in sorted(validator.iter_errors(card), key=lambda e: [str(p) for p in e.absolute_path]):
        where = "/".join(str(p) for p in e.absolute_path) or "the card"
        out.append("%s: %s" % (where, e.message if len(e.message) < 240 else e.message[:240] + " ..."))
    return out


def problems(card):
    """Every reason the stage would not write this card."""
    out = schema_problems(card)
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
    return out


def make(rid, draft, seat, now=None, prior=None, prior_revision=0, note=None):
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
    found = problems(card)
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
    card = make(rid, draft, seat, now, prior, rev, note)
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
