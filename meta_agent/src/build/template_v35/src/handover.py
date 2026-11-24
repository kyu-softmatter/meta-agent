"""Hand values to another agent, and take the values another agent handed here (v32; v33 carries each value's definition;
v34 names in it the tool field each of the skill's inputs came from).

    python src/handover.py write --record <skill record> --runs <tool result> [<tool result> ...] [--thread <thread>]
    python src/handover.py receive [--thread <thread>]
    python src/handover.py values
    python src/handover.py board

What this agent gives and takes is in envelope/handovers.json, written by the build: `agent` names this agent and its
build; `gives` lists each hand-over it may write, to which agent, over which thread, read off which library skill's
record and from which tool results; `takes` lists the rows of envelope/parameters.json that take a value handed
over, each with the value's name, the thread and the agent it comes from; `engine_scales` says, for each of this
agent's engine's own units, which registered unit a person confirmed it stands for. envelope/units.json is the
registry the build carried.

write   makes one hand-over card in outbox/ from a record that src/run_skill.py wrote with --record. The record must
        be of the skill the entry names, have run, and have taken as its inputs exactly the fields of the tool results
        named with --runs, in their order (or of the one result named, where the entry reads its inputs off one
        result); the results must state the same conditions. Each value handed over is the
        skill's output as the record holds it, in the unit the build declared, with the grade the build derived and
        the conditions the results state, and with its definition, the meaning the skill's manifest gives that output,
        under conditions.definition, so that the receiver need not have the skill to know what the value is a value of.
        The card is written with status draft, as every card a bundle writes is. Nothing is computed here and no card
        is written over.
receive reads each envelope in inbox/<thread>/ that has no receipt yet, checks that its payload is the bytes the
        envelope states, and writes one receipt per value in received/: `used` where envelope/handovers.json declares
        the value's row and its unit converts, through the library skill named under unit_skill in TEMPLATE.json and
        the registry carried here, into the row's unit (into an engine's own unit only through a scale a person
        confirmed); `held` with its reason otherwise. A payload whose bytes are not the envelope's is refused and
        nothing is written for it.
values  prints, for each row that takes a hand-over, the value of its latest used receipt, read off the record of
        the conversion, with the definition the hand-over carried: what a tool's input that names the row is given.
board   prints what is in outbox/, inbox/ and received/, and for each envelope who ran the bridge.

Wherever an envelope is shown, its ran_by is shown with it, as the envelope says it: the person ran the bridge, or a
session ran it on the person's words, quoted (v33; the bridge records it since tasks/032). The person's word is behind
both; which one carried a card is said, never assumed.

inbox/ is written by the bridge alone, which a person starts; a session never writes there. outbox/ and received/
are written by this script alone. The exit status is 0 when everything asked was done, 1 when the command was not
understood, 3 when something was refused (and it says what), and 4 when a value was held.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

DECL = "envelope/handovers.json"
UNITS = "envelope/units.json"
PARAMS = "envelope/parameters.json"


class Refused(Exception):
    pass


def path(rel):
    return os.path.join(BUNDLE, *rel.split("/"))


def load(rel):
    with open(path(rel), "r", encoding="utf-8") as f:
        return json.load(f)


def write_new(rel, data):
    p = path(rel)
    if os.path.exists(p):
        raise Refused("%s exists; a card is never written over" % rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel_of(p):
    return os.path.relpath(os.path.abspath(p), BUNDLE).replace(os.sep, "/")


def skeleton(card, ident, author):
    return {"card": card, "schema_version": "0.1", "id": ident, "revision": 1, "author": author, "created_at": now(),
            "numbers": [], "assumptions": [], "kb_refs": [], "kb_gaps": [], "case_refs": [], "case_gaps": [],
            "degraded": [], "status": "draft"}


# ---------------------------------------------------------------------------------------------------- write

def write(record_file, run_files, thread=None):
    decl = load(DECL)
    me = decl.get("agent") or {}
    gives = [g for g in decl.get("gives") or [] if thread in (None, g.get("thread"))]
    if not gives:
        raise Refused("this agent's build declares no hand-over%s to write" % (" over %s" % thread if thread else ""))
    if len(gives) > 1:
        raise Refused("this agent gives over several threads (%s); name one with --thread"
                      % ", ".join(g["thread"] for g in gives))
    g = gives[0]
    with open(record_file, "r", encoding="utf-8") as f:
        record = json.load(f)
    if record.get("record") != "skill_run" or record.get("ref") != g["skill"]:
        raise Refused("the record is not a run of %s, the skill this hand-over is read off" % g["skill"])
    if record.get("verdict") != "ran":
        raise Refused("the record's skill did not run (verdict %s): %s" % (record.get("verdict"), record.get("why")))
    outputs = record.get("outputs") or {}
    accept = g.get("accept_states")
    if accept and outputs.get("state") not in accept:
        raise Refused("the skill's state is %r, and this hand-over is written only on %s; why: %s"
                      % (outputs.get("state"), accept, outputs.get("why")))
    if not run_files:
        raise Refused("name the tool results the record's inputs were taken from, with --runs")
    runs = []
    for rf in run_files:
        with open(rf, "r", encoding="utf-8") as f:
            runs.append(json.load(f))
    one = g.get("record_inputs_from") == "one_result"
    if one and len(runs) != 1:
        raise Refused("the skill's inputs are read off one tool result, and %d were named" % len(runs))
    for inp, field in sorted((g.get("record_inputs") or {}).items()):
        from_runs = runs[0].get(field) if one else [r.get(field) for r in runs]
        if record.get("inputs", {}).get(inp) != from_runs:
            raise Refused("the record's input %s is not the field %s of the results named, in their order: the values "
                          "would rest on runs other than these" % (inp, field))
    cfield = g.get("conditions_field")
    conditions = dict(g.get("conditions") or {})
    if cfield:
        stated = [r.get(cfield) for r in runs]
        if any(not isinstance(s, dict) or not s for s in stated):
            raise Refused("a result names no %s: the conditions it held under are not stated" % cfield)
        if any(s != stated[0] for s in stated[1:]):
            raise Refused("the results state different %s: values fitted over runs under different conditions are "
                          "not handed over" % cfield)
        conditions.update(stated[0])
    conditions["runs"] = [rel_of(rf) for rf in run_files]
    rec_rel = rel_of(record_file)
    meanings = output_meanings(g["skill"])
    numbers = []
    for n in g["numbers"]:
        value = outputs.get(n["output"])
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise Refused("the skill gave no number as %s (%r)" % (n["output"], value))
        if not meanings.get(n["output"]):
            raise Refused("the manifest of %s gives no meaning for its output %s: the value's definition cannot travel "
                          "with it" % (g["skill"], n["output"]))
        numbers.append({"name": n["name"], "value": value, "unit": n["unit"],
                        "source": "computed:skill %s, %s" % (g["skill"], rec_rel), "grade": n["grade"],
                        "value_kind": n["value_kind"], "uncertainty": None,
                        "conditions": dict(conditions, definition="%s, the output %s of %s: %s%s" % (
                            n["name"], n["output"], g["skill"], meanings[n["output"]], inputs_named(g)))})
    seq = len(glob.glob(path("outbox/handover-%s-*.json" % g["thread"]))) + 1
    ident = "ho-%s-%03d" % (g["thread"], seq)
    card = skeleton("handover", ident, me.get("agent"))
    card.update({"thread": g["thread"], "from": {"agent": me.get("agent"), "build": me.get("build")},
                 "to": dict(g["to"]), "numbers": numbers, "produced_by": {"skill": g["skill"], "record": rec_rel},
                 "what": g["what"]})
    rel = "outbox/handover-%s-%03d.json" % (g["thread"], seq)
    write_new(rel, card)
    return rel, card


def output_meanings(ref):
    """{output name: meaning} from the manifest of a skill this bundle carries."""
    p = path("skills/%s/skill.json" % ref)
    if not os.path.isfile(p):
        raise Refused("this bundle does not carry %s, the skill its hand-over is read off" % ref)
    with open(p, "r", encoding="utf-8") as f:
        return {o.get("name"): o.get("meaning") for o in json.load(f).get("outputs") or []}


def carried_by(env):
    """Who ran the bridge for this envelope, in words, as the envelope says it (ran_by, tasks/032); an envelope of before
    that field says nothing of it, and this says so rather than guess."""
    r = env.get("ran_by") if isinstance(env.get("ran_by"), dict) else None
    if r is None:
        return "the envelope does not say who ran the bridge"
    if r.get("by") == "person":
        return "the person ran the bridge"
    if r.get("by") == "session":
        return "a session (%s) ran the bridge on the person's words: %s" % (r.get("session"), r.get("words"))
    return "the envelope's ran_by is not one this script reads: %s" % json.dumps(r, ensure_ascii=False)


def inputs_named(g):
    """What the skill's inputs were, in the words of the tool that made them (v34, dftmd-16): a generic skill names its
    input only as a position or an energy, and the tool's contract says which coordinate it varied."""
    fields = g.get("record_fields") or {}
    return "".join("; its input %s was the field %s of the result of %s: %s" % (
        inp, f.get("field"), f.get("tool"), f.get("description")) for inp, f in sorted(fields.items()) if isinstance(f, dict))


def definition_of(n):
    d = (n.get("conditions") or {}).get("definition")
    return d if isinstance(d, str) and d else None


# ---------------------------------------------------------------------------------------------------- receive

def registry_entry(units, name):
    u = units.get(name)
    if not isinstance(u, dict):
        return None
    return {"name": name, "si_factor": u.get("si_factor"), "dim": u.get("dim") or {}}


def unit_skill():
    with open(path("TEMPLATE.json"), "r", encoding="utf-8") as f:
        return json.load(f)["unit_skill"]


def convert(ref, inputs, record_rel):
    import run_skill
    record = run_skill.run(ref, inputs)
    p = path(record_rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return record


def receive_one(env_rel, decl, units, rows, ref):
    env = load(env_rel)
    thread, rnd = env.get("thread"), env.get("round")
    pl = env.get("payload") or {}
    here = os.path.dirname(env_rel)
    p_rel = here + "/" + pl.get("file", "")
    if not os.path.isfile(path(p_rel)):
        raise Refused("%s names a payload %s that is not beside it" % (env_rel, pl.get("file")))
    if sha256_file(path(p_rel)) != pl.get("sha256"):
        raise Refused("%s is not the bytes %s states: it changed after the producer wrote it, and nothing of it is "
                      "used" % (p_rel, env_rel))
    payload = load(p_rel)
    if payload.get("card") != "handover" or payload.get("id") != pl.get("id"):
        raise Refused("%s is not the hand-over %s names" % (p_rel, env_rel))
    me = (decl.get("agent") or {}).get("agent")
    scales = {s.get("unit"): s for s in decl.get("engine_scales") or [] if isinstance(s, dict)}
    out = []
    origin = (payload.get("from") or {}).get("agent")
    for n in payload.get("numbers") or []:
        matching = [t for t in decl.get("takes") or [] if t.get("name") == n.get("name") and t.get("thread") == thread
                    and t.get("from_agent") == origin]
        for take in matching or [None]:
            out.append(receipt_for(n, take, env_rel, env, pl, payload, thread, rnd, me, units, rows, scales, ref))
    return out


def receipt_for(n, take, env_rel, env, pl, payload, thread, rnd, me, units, rows, scales, ref):
    """One receipt: the value n for the row take declares, or held as undeclared where no row does."""
    row = take["row"] if take else n["name"]
    to_unit = n["unit"]
    if take:
        r = rows.get(row)
        to_unit = r.get("unit") if isinstance(r, dict) and r.get("unit") else n["unit"]
    conv = {"from_unit": n["unit"], "to_unit": to_unit, "factor": None, "by": ref}
    ident = "rc-%s-r%s-%s" % (thread, rnd, re.sub(r"[^A-Za-z0-9._-]", "-", row))
    receipt = skeleton("handover_receipt", ident, me)
    receipt.update({"envelope": env_rel, "payload_sha256": pl["sha256"], "handover": payload["id"], "name": n["name"],
                    "row": row, "declared_in": DECL if take else None, "conversion": conv})
    fu, tu = registry_entry(units, n["unit"]), registry_entry(units, to_unit)
    stands = None
    held = None
    if not take:
        held = "undeclared"
    elif fu is None or tu is None:
        held = "unit_not_convertible"
    elif tu["si_factor"] is None:
        s = scales.get(to_unit)
        if s:
            conv["engine_scale"] = {k: s[k] for k in ("unit", "stands_for", "state", "confirmed_by", "evidence") if k in s}
        if not s or s.get("state") != "confirmed" or s.get("confirmed_by") != "human":
            held = "engine_scale_not_confirmed"
        else:
            stands = registry_entry(units, s.get("stands_for"))
            if stands is None:
                held = "unit_not_convertible"
    record_rel = record_of(thread, rnd, ident)
    if held in (None, "undeclared") and fu is not None and tu is not None:
        record = convert(ref, {"value": n["value"], "from_unit": fu, "to_unit": tu, "stands_for": stands}, record_rel)
        outs = record.get("outputs") or {}
        if record.get("verdict") == "ran" and outs.get("state") == "converted":
            conv["factor"] = outs["factor"]
            if held is None:
                receipt["note"] = "the converted value, in %s, is the output converted of %s; %s; %s" % (
                    to_unit, record_rel, "the hand-over defines it as: " + definition_of(n) if definition_of(n)
                    else "the hand-over carries no definition of it", carried_by(env))
        elif held is None:
            held = "unit_not_convertible"
            receipt["note"] = "%s: %s" % (record_rel, outs.get("why") or record.get("why"))
    receipt["state"] = "held" if held else "used"
    if held:
        receipt["reason"] = held
    rel = "received/%s-r%s-%s.json" % (thread, rnd, row)
    write_new(rel, receipt)
    return rel, receipt


def record_of(thread, rnd, ident):
    return "runs/handover/%s/r%s_%s.record.json" % (thread, rnd, ident)


def receive(thread=None):
    decl = load(DECL)
    units = load(UNITS)["units"]
    rows = {r.get("name"): r for r in load(PARAMS).get("rows") or [] if isinstance(r, dict)}
    ref = unit_skill()
    done = []
    pattern = path("inbox/%s/r*_envelope.json" % (thread or "*"))
    for env_path in sorted(glob.glob(pattern), key=lambda p: (os.path.dirname(p), int(re.findall(r"r(\d+)_", os.path.basename(p))[0]))):
        env_rel = rel_of(env_path)
        env = load(env_rel)
        mark = "received/%s-r%s-" % (env.get("thread"), env.get("round"))
        if glob.glob(path(mark + "*.json")):
            continue
        done.extend(receive_one(env_rel, decl, units, rows, ref))
    return done


# ---------------------------------------------------------------------------------------------------- values, board

def values():
    decl = load(DECL)
    out = {}
    for t in decl.get("takes") or []:
        latest = None
        for rp in glob.glob(path("received/%s-r*-%s.json" % (t["thread"], t["row"]))):
            rc = load(rel_of(rp))
            if rc.get("state") == "used" and rc.get("row") == t["row"] and rc.get("name") == t["name"]:
                rnd = int(re.findall(r"/r(\d+)_envelope", rc["envelope"])[0])
                if latest is None or rnd > latest[0]:
                    latest = (rnd, rc, rel_of(rp))
        if latest is None:
            out[t["row"]] = {"value": None, "why": "no used receipt for %s over %s" % (t["name"], t["thread"])}
            continue
        rnd, rc, rc_rel = latest
        record_rel = record_of(t["thread"], rnd, rc["id"])
        rec = load(record_rel)
        env = load(rc["envelope"])
        payload = load(os.path.dirname(rc["envelope"]) + "/" + env["payload"]["file"])
        handed = next((n for n in payload.get("numbers") or [] if n.get("name") == t["name"]), {})
        out[t["row"]] = {"value": rec["outputs"]["converted"], "unit": rc["conversion"]["to_unit"],
                         "definition": definition_of(handed) or "the hand-over carries no definition of it",
                         "carried": carried_by(env),
                         "source": "computed:skill %s, %s" % (rc["conversion"]["by"], record_rel),
                         "value_kind": "computed", "receipt": rc_rel,
                         "grade": "not derived here: the builder derives it"}
    return out


def board():
    out = {"outbox": sorted(rel_of(p) for p in glob.glob(path("outbox/*.json"))),
           "inbox": sorted(rel_of(p) for p in glob.glob(path("inbox/*/*.json"))),
           "carried": [{"envelope": rel_of(p), "carried": carried_by(load(rel_of(p)))}
                       for p in sorted(glob.glob(path("inbox/*/r*_envelope.json")))],
           "received": []}
    for rp in sorted(glob.glob(path("received/*.json"))):
        rc = load(rel_of(rp))
        out["received"].append({"file": rel_of(rp), "name": rc.get("name"), "row": rc.get("row"), "state": rc.get("state"),
                                "reason": rc.get("reason")})
    return out


def main(argv):
    if not argv or argv[0] not in ("write", "receive", "values", "board"):
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    thread = None
    if "--thread" in rest:
        i = rest.index("--thread")
        thread = rest[i + 1] if i + 1 < len(rest) else None
        rest = rest[:i] + rest[i + 2:]
    try:
        if cmd == "write":
            if "--record" not in rest or "--runs" not in rest:
                print(__doc__)
                return 1
            i = rest.index("--record")
            record = rest[i + 1]
            runs = rest[rest.index("--runs") + 1:]
            runs = [r for r in runs if r != "--record" and r != record]
            rel, card = write(record, runs, thread)
            print(json.dumps({"written": rel, "card": card}, indent=2, ensure_ascii=False))
            return 0
        if cmd == "receive":
            done = receive(thread)
            print(json.dumps({"written": [{"file": r, "name": c["name"], "row": c["row"], "state": c["state"],
                                           "reason": c.get("reason"), "carried": carried_by(load(c["envelope"]))}
                                          for r, c in done]}, indent=2, ensure_ascii=False))
            return 4 if any(c["state"] == "held" for _, c in done) else 0
        if cmd == "values":
            print(json.dumps(values(), indent=2, ensure_ascii=False))
            return 0
        print(json.dumps(board(), indent=2, ensure_ascii=False))
        return 0
    except Refused as e:
        print(json.dumps({"refused": str(e)}, indent=2, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
