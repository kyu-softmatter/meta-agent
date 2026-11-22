"""The hub's one script (hub template v2; v1 with hub-1, hub-2 and hub-3 of meta_agent/failures.jsonl): it writes the hub's cards from the session's words, carries them through the
bridge, opens a member's session and reads what came back. It reads no value to judge it and computes none.

    python src/hub.py members
    python src/hub.py question --draft <draft.json>
    python src/hub.py agree --question <question id> --words "<the person's words, verbatim>"
    python src/hub.py words --question <question id> --words "<the person's later words, verbatim>"
    python src/hub.py round --assignment <list item id> [--quote <question revision> <index> "<a part of the words>"]...
    python src/hub.py carry --assignment <assignment id> --session <this session's id> [--again]
    python src/hub.py brief --assignment <assignment id>
    python src/hub.py open --assignment <assignment id> --model <model> --effort <effort> --permission-mode <mode>
                           --words "<the person's words naming them, verbatim>"
    python src/hub.py wait [--slice <seconds>]
    python src/hub.py collect --session <this session's id>
    python src/hub.py handover --card <member folder>/outbox/<hand-over card> --to <member> --session <this session's id>
                               --words "<the person's words for this crossing, verbatim>"
    python src/hub.py status

members   what members.json lists, and for each member whether its folder is there, holds the build members.json names
          and can answer an assignment, what it gives to and takes from the others (its envelope/handovers.json), and
          each of its parameter rows (envelope/parameters.json): whether it holds a value, who chose it and on what basis,
          and whether it takes a hand-over (v2, hub-2), so that a split knows which settings stand already.
question  writes the person's question as a hub_question card in question/ and one assignment card per entry of the
          draft in assignments/, after checking that each goes to a member, answers items of the question, and that
          every item is answered by some assignment. The draft is JSON: {"question": the person's words verbatim,
          "done_when": [{"id", "what"}], "assignments": [{"to": member, "asks", "answers_items": [ids],
          "returns": [{"card": "result" | "handover", "to": hub or member}], "done_when", "round" (1 when absent)}]}.
          The question has no agreement yet: nothing is carried until `agree`. It prints the list to show the person.
agree     writes the question's next revision, v<N>_<file>, with the person's words agreeing to its list, verbatim.
words     writes the question's next revision with the person's words given after the agreement appended to its
          person_words, verbatim, numbers included; the question, its items, its list and the agreement stay as they are
          (v2, hub-3; the person, 2026-11-21, 'Append to the question (Recommended)', 'Next round quotes them
          (Recommended)').
round     writes the next round of an assignment of the agreed list: a card to the same member, answering the same items,
          asking and returning the same, naming the list item it carries on (list_item) and quoting, character for
          character, parts of the person's later words in the question's revisions (quotes); the person need not agree
          again, since the list is unchanged. It is written only after the member answered the last round carried.
          The card is then carried like any assignment (v2, hub-3).
carry     carries one assignment into its member's inbox/<thread>/ through the bridge on the hub's trigger, only where
          the person agreed to the list that holds it, and only once every hand-over the member takes from another
          member of this hub (its envelope/handovers.json takes) has crossed into its inbox (v2, hub-1); --again carries the same assignment once more, as the next round
          of its thread, after the member answered the last one. It prints the pointer a message to the member carries.
brief     prints the brief of a member's session: the path of the assignment in its inbox and its hash, and nothing else.
open      starts the member's session, fresh, in the member's folder, with the brief on its standard input, on the
          model, effort and permission mode given, which are the person's (each must be given, and the person's words
          naming them are kept with the record). It returns at once; the session runs on by itself.
wait      waits until every session `open` started has ended, or until the slice has passed, and says which are running.
collect   carries each result a member wrote to this hub, answering an assignment of this hub, into inbox/<thread>/,
          on the hub's trigger; a result already carried is not carried again.
handover  carries a hand-over card from one member to another on the person's word for that crossing: the bridge's
          trigger human, released by the person, run by this session with the person's words, verbatim.
status    reads the cards: for each question, whether the person agreed, what was carried, opened and answered; for each
          item of the question, the results that answer it and are not held; what is held, why and what it needs; the
          hand-overs between members that wait for the person's word; and whether the question is solved.

The exit status is 0 when what was asked was done, 1 when the command was not understood, 3 when something was refused
(and it says what), and 5 from `wait` while a session still runs. Standard library only.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.dirname(HERE)
sys.path.insert(0, HERE)

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,80}$")
ENV_RE = re.compile(r"^r([0-9]+)_envelope\.json$")
ASKS_NOTHING = ("bypassPermissions",)
DEFAULT_SLICE = 480


class Refused(Exception):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def try_load(p):
    try:
        return load(p)
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def write_new(p, data):
    if os.path.exists(p):
        raise Refused("%s exists; a card is never written over" % os.path.relpath(p, HUB))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def rel(p, base=HUB):
    return os.path.relpath(os.path.abspath(p), base).replace(os.sep, "/")


def skeleton(card, ident, author):
    return {"card": card, "schema_version": "0.1", "id": ident, "revision": 1, "author": author, "created_at": now(),
            "numbers": [], "assumptions": [], "kb_refs": [], "kb_gaps": [], "case_refs": [], "case_gaps": [],
            "degraded": [], "status": "draft"}


# ---------------------------------------------------------------------------------------------------- the members

def members():
    m = try_load(os.path.join(HUB, "members.json"))
    if not isinstance(m, dict) or m.get("card") != "hub_members":
        raise Refused("members.json is not a hub_members card")
    return m


def me():
    h = members()["hub"]
    return {"agent": h["agent"], "build": h["build"]}


def member(name):
    for m in members()["members"]:
        if m["agent"] == name:
            return dict(m, path=os.path.normpath(os.path.join(HUB, m["folder"])))
    raise Refused("%s is not a member of this hub; its members are %s" % (
        name, ", ".join(x["agent"] for x in members()["members"])))


def member_of_folder(folder):
    real = os.path.realpath(folder)
    for m in members()["members"]:
        if os.path.realpath(os.path.join(HUB, m["folder"])) == real:
            return dict(m, path=os.path.normpath(os.path.join(HUB, m["folder"])))
    raise Refused("%s is the folder of no member of this hub" % folder)


def declared_agent(path):
    for relp in ("envelope/results.json", "envelope/handovers.json"):
        d = try_load(os.path.join(path, *relp.split("/")))
        if isinstance(d, dict) and isinstance(d.get("agent"), dict):
            return d["agent"]
    return None


def members_report():
    out = []
    for m in members()["members"]:
        path = os.path.normpath(os.path.join(HUB, m["folder"]))
        e = {"agent": m["agent"], "build": m["build"], "folder": m["folder"], "there": os.path.isdir(path)}
        if e["there"]:
            agent = declared_agent(path)
            t = try_load(os.path.join(path, "TEMPLATE.json")) or {}
            e["holds_this_build"] = bool(agent) and agent.get("agent") == m["agent"] and agent.get("build") == m["build"]
            e["holds"] = agent
            e["answers_assignments"] = bool(t.get("results_file")) and os.path.isfile(os.path.join(path, "src", "handover.py"))
            h = try_load(os.path.join(path, "envelope", "handovers.json")) or {}
            e["gives"] = [{"thread": g.get("thread"), "to": (g.get("to") or {}).get("agent"), "what": g.get("what")}
                          for g in h.get("gives") or []]
            e["takes"] = [{"thread": t2.get("thread"), "from": t2.get("from_agent"), "name": t2.get("name")}
                          for t2 in h.get("takes") or []]
            prm = try_load(os.path.join(path, "envelope", "parameters.json")) or {}
            e["rows"] = [{"name": r.get("name"), "unit": r.get("unit"), "holds_a_value": r.get("value") is not None,
                          "chosen_by": r.get("chosen_by"), "basis": r.get("basis"),
                          "takes_handover": isinstance(r.get("takes_handover"), dict),
                          "note": r.get("note")}
                         for r in prm.get("rows") or [] if isinstance(r, dict)]
        out.append(e)
    return out


# ---------------------------------------------------------------------------------------------------- the question

def questions():
    """{question id: (path, card)} at its latest revision."""
    out = {}
    for p in sorted(glob.glob(os.path.join(HUB, "question", "*.json"))):
        q = try_load(p)
        if isinstance(q, dict) and q.get("card") == "hub_question":
            have = out.get(q.get("id"))
            if have is None or q.get("revision", 1) > have[1].get("revision", 1):
                out[q["id"]] = (p, q)
    return out


def assignment_cards():
    out = {}
    for p in sorted(glob.glob(os.path.join(HUB, "assignments", "*.json"))):
        a = try_load(p)
        if isinstance(a, dict) and a.get("card") == "assignment":
            out[a["id"]] = (p, a)
    return out


def question(draft_path):
    hub = me()
    d = load(draft_path)
    words = d.get("question")
    if not isinstance(words, str) or not words.strip():
        raise Refused("the draft has no question: the person's words, verbatim")
    items = d.get("done_when") or []
    ids = []
    for it in items:
        if not isinstance(it, dict) or not ID_RE.match(str(it.get("id"))) or not str(it.get("what") or "").strip():
            raise Refused("each item of done_when has an id and says in words what must be answered")
        ids.append(it["id"])
    if not ids or len(set(ids)) != len(ids):
        raise Refused("done_when holds at least one item, each id once")
    names = {m["agent"]: m for m in members()["members"]}
    drafts = d.get("assignments") or []
    if not drafts:
        raise Refused("the draft has no assignment")
    seq = len(questions()) + 1
    qid = "q-%s-%03d" % (hub["agent"], seq)
    cards, covered = [], set()
    for a in drafts:
        to = a.get("to")
        if to not in names:
            raise Refused("an assignment goes to %r, which is not a member of this hub" % to)
        if not str(a.get("asks") or "").strip() or not str(a.get("done_when") or "").strip():
            raise Refused("the assignment to %s says in words what it asks and when it is done" % to)
        answers = a.get("answers_items") or []
        if set(answers) - set(ids):
            raise Refused("the assignment to %s answers %s, which are not items of the question" % (
                to, sorted(set(answers) - set(ids))))
        covered |= set(answers)
        returns = []
        for r in a.get("returns") or []:
            target = r.get("to")
            if r.get("card") == "result":
                if target not in (None, hub["agent"]):
                    raise Refused("a result goes to the hub, not to %r" % target)
                returns.append({"card": "result", "to": dict(hub)})
            elif r.get("card") == "handover":
                if target not in names or target == to:
                    raise Refused("a hand-over from %s goes to another member, not to %r" % (to, target))
                returns.append({"card": "handover", "to": {"agent": target, "build": names[target]["build"]}})
            else:
                raise Refused("an assignment returns a result or a hand-over, not %r" % r.get("card"))
        if not any(r["card"] == "result" for r in returns):
            raise Refused("the assignment to %s returns no result to the hub" % to)
        rnd = a.get("round", 1)
        if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
            raise Refused("an assignment's round is a whole number from one")
        aid = "as-%03d-%s-r%d" % (seq, to, rnd)
        card = skeleton("assignment", aid, hub["agent"])
        card.update({"thread": "thr-%s-%s" % (hub["agent"], to), "round": rnd, "question": qid, "from": dict(hub),
                     "to": {"agent": to, "build": names[to]["build"]}, "asks": a["asks"], "answers_items": answers,
                     "returns": returns, "done_when": a["done_when"]})
        cards.append(card)
    missing = [i for i in ids if i not in covered]
    if missing:
        raise Refused("no assignment answers the items %s of the question" % missing)
    if len({c["id"] for c in cards}) != len(cards):
        raise Refused("two assignments go to one member in one round; say it as one assignment")
    for c in cards:
        if not ID_RE.match(c["id"]) or not ID_RE.match(c["thread"]):
            raise Refused("%s cannot be an id or a thread" % c["id"])
    q = skeleton("hub_question", qid, hub["agent"])
    q.update({"question": words, "done_when": items, "assignments": [c["id"] for c in cards]})
    write_new(os.path.join(HUB, "question", qid + ".json"), q)
    for c in cards:
        write_new(os.path.join(HUB, "assignments", c["id"] + ".json"), c)
    return q, cards


def agree(qid, words):
    qs = questions()
    if qid not in qs:
        raise Refused("%s is no question of this hub" % qid)
    path, q = qs[qid]
    if isinstance(q.get("agreed"), dict):
        raise Refused("the person agreed to %s already: %s" % (qid, q["agreed"].get("words")))
    if not isinstance(words, str) or not words.strip():
        raise Refused("give the person's words agreeing to the list, verbatim")
    n = q.get("revision", 1) + 1
    new = dict(q, revision=n, created_at=now(), agreed={"words": words, "at": now()})
    base = re.sub(r"^v[0-9]+_", "", os.path.basename(path))
    out = os.path.join(HUB, "question", "v%d_%s" % (n, base))
    write_new(out, new)
    return out, new


def words(qid, said):
    """The person's words after the agreement, appended verbatim in the question's next revision (v2, hub-3)."""
    qs = questions()
    if qid not in qs:
        raise Refused("%s is no question of this hub" % qid)
    path, q = qs[qid]
    if not isinstance(q.get("agreed"), dict):
        raise Refused("the person has not agreed to the list of %s; their words go into the question before it, and the "
                      "list is shown to them again" % qid)
    if not isinstance(said, str) or not said.strip():
        raise Refused("give the person's words, verbatim")
    n = q.get("revision", 1) + 1
    new = dict(q, revision=n, created_at=now(), person_words=list(q.get("person_words") or []) + [{"at": now(), "words": said}])
    base = re.sub(r"^v[0-9]+_", "", os.path.basename(path))
    out = os.path.join(HUB, "question", "v%d_%s" % (n, base))
    write_new(out, new)
    return out, new


def question_revisions(qid):
    """{revision: card} of every revision of a question this hub holds."""
    out = {}
    for p in sorted(glob.glob(os.path.join(HUB, "question", "*.json"))):
        q = try_load(p)
        if isinstance(q, dict) and q.get("card") == "hub_question" and q.get("id") == qid:
            out[q.get("revision", 1)] = q
    return out


def rounds_of(item):
    """[(path, card)] of the list item and every later round that carries it on, in round order."""
    return sorted([(p, a) for p, a in assignment_cards().values() if (a.get("list_item") or a.get("id")) == item],
                  key=lambda x: x[1].get("round", 1))


def next_round(item, quotes):
    cards = assignment_cards()
    if item not in cards or cards[item][1].get("list_item"):
        raise Refused("%s is no assignment of the agreed list of this hub; name the list item itself" % item)
    first = cards[item][1]
    revs = question_revisions(first["question"])
    if not any(item in (q.get("assignments") or []) and isinstance(q.get("agreed"), dict) for q in revs.values()):
        raise Refused("the person has not agreed to the list that holds %s" % item)
    chain = rounds_of(item)
    last = chain[-1][1]
    m = member(first["to"]["agent"])
    done = carries_of(last["id"])
    if not done:
        raise Refused("%s, the last round of %s, has not been carried yet" % (last["id"], item))
    env = rel(done[-1][0], m["path"])
    if not any((r.get("answers") or {}).get("envelope") == env for _, r in results_of(m["path"], me())):
        raise Refused("the member has not answered %s yet; a next round is written only after it answered" % env)
    out_quotes = []
    for rev, idx, text in quotes:
        try:
            rev, idx = int(rev), int(idx)
        except ValueError:
            raise Refused("a quote names a question revision and an index as whole numbers")
        said = ((revs.get(rev) or {}).get("person_words") or [])
        if not (0 <= idx < len(said)) or not isinstance(text, str) or not text or text not in said[idx].get("words", ""):
            raise Refused("%r does not stand in the person's words %d of revision %d of %s" % (text, idx, rev, first["question"]))
        out_quotes.append({"question_revision": rev, "index": idx, "quote": text})
    rnd = last.get("round", 1) + 1
    aid = re.sub(r"-r[0-9]+$", "", item) + "-r%d" % rnd
    card = skeleton("assignment", aid, me()["agent"])
    for k in ("thread", "question", "from", "to", "asks", "answers_items", "returns", "done_when"):
        card[k] = first[k]
    card.update({"round": rnd, "list_item": item})
    if out_quotes:
        card["quotes"] = out_quotes
    p = os.path.join(HUB, "assignments", aid + ".json")
    write_new(p, card)
    return p, card


def waits_for_handover(m):
    """What the member takes from another member of this hub and has not received yet (v2, hub-1)."""
    names = {x["agent"] for x in members()["members"]}
    h = try_load(os.path.join(m["path"], "envelope", "handovers.json")) or {}
    out = []
    for t in h.get("takes") or []:
        if t.get("from_agent") not in names or t.get("from_agent") == m["agent"]:
            continue
        crossed = [p for p, e in envelopes(m["path"], t.get("thread")) if (e.get("payload") or {}).get("card") == "handover"]
        if not crossed:
            out.append("%s over %s from %s" % (t.get("name"), t.get("thread"), t.get("from_agent")))
    return out


# ---------------------------------------------------------------------------------------------------- carrying

def envelopes(folder, thread=None):
    """[(path, envelope)] under folder/inbox/, in round order."""
    out = []
    for p in glob.glob(os.path.join(folder, "inbox", thread or "*", "r*_envelope.json")):
        e = try_load(p)
        if isinstance(e, dict):
            out.append((p, e))
    return sorted(out, key=lambda x: (os.path.dirname(x[0]), int(ENV_RE.match(os.path.basename(x[0])).group(1))))


def carries_of(aid):
    """[(envelope path, envelope)] that carried the assignment into its member, in round order."""
    cards = assignment_cards()
    if aid not in cards:
        raise Refused("%s is no assignment of this hub" % aid)
    a = cards[aid][1]
    m = member(a["to"]["agent"])
    return [(p, e) for p, e in envelopes(m["path"], a["thread"])
            if (e.get("payload") or {}).get("card") == "assignment" and (e.get("payload") or {}).get("id") == aid]


def results_of(member_path, hub):
    out = []
    for p in sorted(glob.glob(os.path.join(member_path, "outbox", "result-*.json"))):
        r = try_load(p)
        if isinstance(r, dict) and r.get("card") == "result" and r.get("to") == hub:
            out.append((p, r))
    return out


def carry(aid, session, again=False):
    import bridge
    cards = assignment_cards()
    if aid not in cards:
        raise Refused("%s is no assignment of this hub" % aid)
    path, a = cards[aid]
    m = member(a["to"]["agent"])
    waiting = sorted(set(waits_for_handover(m)))
    if waiting:
        raise Refused("%s takes %s, which has not crossed into its inbox: its assignment is carried once the person has "
                      "let the hand-over cross" % (m["agent"], "; ".join(waiting)))
    done = carries_of(aid)
    if done and not again:
        raise Refused("%s was carried already (%s); --again carries it once more as the next round of its thread" % (
            aid, rel(done[-1][0])))
    if again:
        if not done:
            raise Refused("%s has not been carried yet; carry it without --again" % aid)
        last = rel(done[-1][0], m["path"])
        if not any((r.get("answers") or {}).get("envelope") == last for _, r in results_of(m["path"], me())):
            raise Refused("the member has not answered %s yet; it is carried again only after it answered" % last)
    try:
        env, payload = bridge.carry(path, m["path"], "hub", {"by": "hub", "session": session}, trigger="hub")
    except bridge.Refused as e:
        raise Refused("the bridge refused: %s" % e)
    return pointer(m, env, payload)


def pointer(m, env, payload):
    e = load(env)
    return {"member": m["agent"], "folder": m["folder"], "thread": e["thread"], "round": e["round"],
            "card": rel(payload, m["path"]), "sha256": e["payload"]["sha256"], "envelope": rel(env, m["path"])}


def brief(aid):
    done = carries_of(aid)
    if not done:
        raise Refused("%s has not been carried; carry it first" % aid)
    a = assignment_cards()[aid][1]
    m = member(a["to"]["agent"])
    env_path, e = done[-1]
    p = pointer(m, env_path, os.path.join(os.path.dirname(env_path), e["payload"]["file"]))
    return ("Your assignment from %s is %s (%s), carried with %s.\n" % (me()["agent"], p["card"], p["sha256"], p["envelope"]),
            p)


def collect(session):
    import bridge
    hub = me()
    carried = {(e.get("payload") or {}).get("id") for _, e in envelopes(HUB)}
    mine = {aid: a for aid, (_, a) in assignment_cards().items()}
    out = []
    for m in members()["members"]:
        path = os.path.normpath(os.path.join(HUB, m["folder"]))
        for p, r in results_of(path, hub):
            if r.get("id") in carried:
                continue
            aid = (r.get("answers") or {}).get("assignment")
            if aid not in mine or (mine[aid].get("to") or {}).get("agent") != m["agent"]:
                out.append({"result": rel(p), "refused": "it answers %r, which is no assignment of this hub to %s" % (
                    aid, m["agent"])})
                continue
            try:
                env, payload = bridge.carry(p, HUB, "hub", {"by": "hub", "session": session}, trigger="hub")
            except bridge.Refused as e:
                out.append({"result": rel(p), "refused": str(e)})
                continue
            out.append({"result": rel(p), "carried": rel(payload), "envelope": rel(env), "state": r.get("state")})
    return out


def handover(card, to, session, words):
    import bridge
    card = os.path.abspath(card)
    if os.path.basename(os.path.dirname(card)) != "outbox":
        raise Refused("%s is not a card in a member's outbox/" % card)
    src = member_of_folder(os.path.dirname(os.path.dirname(card)))
    dst = member(to)
    h = try_load(card)
    if not isinstance(h, dict) or h.get("card") != "handover":
        raise Refused("%s is not a hand-over card" % rel(card))
    if (h.get("from") or {}).get("agent") != src["agent"]:
        raise Refused("the hand-over says it is from %r, and it stands in %s's outbox" % ((h.get("from") or {}).get("agent"),
                                                                                         src["agent"]))
    if h.get("to") != {"agent": dst["agent"], "build": dst["build"]}:
        raise Refused("the hand-over goes to %s, and the member %s is build %s" % (json.dumps(h.get("to")), dst["agent"],
                                                                                    dst["build"]))
    if not isinstance(words, str) or not words.strip():
        raise Refused("a hand-over crosses only on the person's word: give their words for this crossing, verbatim")
    try:
        env, payload = bridge.carry(card, dst["path"], "human", {"by": "session", "session": session, "words": words},
                                    trigger="human")
    except bridge.Refused as e:
        raise Refused("the bridge refused: %s" % e)
    return {"carried": rel(payload), "envelope": rel(env), "from": src["agent"], "to": dst["agent"]}


# ---------------------------------------------------------------------------------------------------- sessions

def sessions_dir():
    return os.path.join(HUB, "sessions")


def session_records():
    out = []
    for p in sorted(glob.glob(os.path.join(sessions_dir(), "*.session.json"))):
        s = try_load(p)
        if isinstance(s, dict):
            ended = try_load(p[:-len(".session.json")] + ".ended.json")
            out.append((p, s, ended))
    return out


def open_session(aid, model, effort, mode, words):
    for k, v in (("model", model), ("effort", effort), ("permission mode", mode), ("person's words", words)):
        if not isinstance(v, str) or not v.strip():
            raise Refused("the %s of a member's session is the person's: give it, with --words quoting them" % k)
    if mode in ASKS_NOTHING:
        raise Refused("the permission mode %s asks nothing; a member's session is never opened in it" % mode)
    text, p = brief(aid)
    env_rel = p["envelope"]
    for _, s, _ in session_records():
        if s.get("member") == p["member"] and s.get("envelope") == env_rel:
            raise Refused("a session was opened for %s already (%s)" % (env_rel, s.get("name")))
    exe = shutil.which("claude")
    if not exe:
        raise Refused("no command-line claude on this computer's PATH: putting it there is the person's step")
    m = member(p["member"])
    os.makedirs(sessions_dir(), exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(sessions_dir(), "%s-%d.session.json" % (p["member"], n))):
        n += 1
    name = "%s-%d" % (p["member"], n)
    base = os.path.join(sessions_dir(), name)
    with open(base + ".brief.txt", "x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    cmd = [exe, "-p", "--output-format", "json", "--permission-mode", mode, "--model", model, "--effort", effort]
    # fresh: the variables this session's application gave it (CLAUDE...) are not passed on, so the member's session
    # is the member folder's own and not a part of this one
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    with open(base + ".brief.txt", "rb") as fin, open(base + ".out.json", "wb") as fout, open(base + ".err.txt", "wb") as ferr:
        proc = subprocess.Popen(cmd, cwd=m["path"], stdin=fin, stdout=fout, stderr=ferr, start_new_session=True, env=env)
    record = {"name": name, "member": p["member"], "folder": p["folder"], "assignment": aid, "envelope": env_rel,
              "assignment_copy": p["card"], "sha256": p["sha256"], "pid": proc.pid, "command": ["claude"] + cmd[1:],
              "model": model, "effort": effort, "permission_mode": mode, "words": words, "started_at": now(),
              "brief": rel(base + ".brief.txt"), "out": rel(base + ".out.json")}
    write_new(base + ".session.json", record)
    return record


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:
        done, _ = os.waitpid(pid, os.WNOHANG)    # a child of this process that ended is reaped here
        return done == 0
    except ChildProcessError:
        return True


def ended_record(path, s):
    out = try_load(os.path.join(HUB, *s["out"].split("/")))
    said = out.get("result") if isinstance(out, dict) else None
    e = {"name": s["name"], "ended_seen_at": now(), "session_id": out.get("session_id") if isinstance(out, dict) else None,
         "is_error": out.get("is_error") if isinstance(out, dict) else None,
         "said_first_line": (said.strip().splitlines()[0] if isinstance(said, str) and said.strip() else None)}
    write_new(path[:-len(".session.json")] + ".ended.json", e)
    return e


def wait(slice_s=DEFAULT_SLICE):
    deadline = time.time() + slice_s
    while True:
        running, out = [], []
        for p, s, ended in session_records():
            if ended is None and not alive(s["pid"]):
                ended = ended_record(p, s)
            if ended is None:
                running.append(s["name"])
            out.append({"name": s["name"], "member": s["member"], "envelope": s["envelope"],
                        "state": "running" if ended is None else "ended", "ended": ended})
        if not running or time.time() >= deadline:
            return out, running
        time.sleep(5)


# ---------------------------------------------------------------------------------------------------- status

def status():
    hub = me()
    inbox = {}
    for p, e in envelopes(HUB):
        pl = e.get("payload") or {}
        if pl.get("card") == "result":
            r = try_load(os.path.join(os.path.dirname(p), pl.get("file", "")))
            same = os.path.isfile(os.path.join(os.path.dirname(p), pl.get("file", ""))) and \
                sha256_file(os.path.join(os.path.dirname(p), pl.get("file", ""))) == pl.get("sha256")
            if isinstance(r, dict):
                inbox[r["id"]] = {"copy": rel(os.path.join(os.path.dirname(p), pl["file"])), "envelope": rel(p),
                                  "unchanged": same, "card": r}
    cards = assignment_cards()
    sessions = session_records()
    out = {"hub": hub, "questions": [], "handovers": []}
    for qid, (qpath, q) in sorted(questions().items()):
        entry = {"id": qid, "card": rel(qpath), "question": q.get("question"),
                 "agreed": q.get("agreed"), "person_words": q.get("person_words") or [], "assignments": [], "items": [],
                 "held": []}
        for aid in q.get("assignments") or []:
            if aid not in cards:
                entry["assignments"].append({"id": aid, "missing": True})
                continue
            a = cards[aid][1]
            m = member(a["to"]["agent"])
            ids = [c["id"] for _, c in rounds_of(aid)]
            carried = [rel(p, m["path"]) for x in ids for p, _ in carries_of(x)]
            written = [rel(p, m["path"]) for p, r in results_of(m["path"], hub) if (r.get("answers") or {}).get("assignment") in ids]
            back = [dict(v, id=k) for k, v in inbox.items() if (v["card"].get("answers") or {}).get("assignment") in ids]
            opened = [{"name": s["name"], "envelope": s["envelope"], "state": "ended" if ended else "running"}
                      for _, s, ended in sessions if s.get("assignment") in ids]
            entry["assignments"].append({
                "id": aid, "rounds": ids, "waits_for_handover": waits_for_handover(m),
                "to": a["to"]["agent"], "asks": a.get("asks"), "answers_items": a.get("answers_items"),
                "returns": a.get("returns"), "carried": carried, "sessions": opened, "results_written": written,
                "results_here": [{"id": b["id"], "copy": b["copy"], "state": b["card"].get("state"),
                                  "unchanged": b["unchanged"], "answers_envelope": (b["card"].get("answers") or {}).get("envelope")}
                                 for b in back]})
            for b in back:
                for h in b["card"].get("held") or []:
                    entry["held"].append(dict(h, by=a["to"]["agent"], result=b["copy"]))
        for it in q.get("done_when") or []:
            by = []
            for a_entry in entry["assignments"]:
                if it["id"] not in (a_entry.get("answers_items") or []):
                    continue
                for b in a_entry.get("results_here") or []:
                    if b["state"] == "answered" and b["unchanged"]:
                        by.append(b["copy"])
            entry["items"].append({"id": it["id"], "what": it["what"], "answered_by": by})
        entry["solved"] = bool(entry["items"]) and all(i["answered_by"] for i in entry["items"])
        out["questions"].append(entry)
    for m in members()["members"]:
        path = os.path.normpath(os.path.join(HUB, m["folder"]))
        for p in sorted(glob.glob(os.path.join(path, "outbox", "handover-*.json"))):
            h = try_load(p)
            if not isinstance(h, dict) or h.get("card") != "handover":
                continue
            to = (h.get("to") or {}).get("agent")
            arrived = []
            try:
                dst = member(to)
                arrived = [rel(ep, dst["path"]) for ep, e in envelopes(dst["path"], h.get("thread"))
                           if (e.get("payload") or {}).get("id") == h.get("id")]
            except Refused:
                pass
            out["handovers"].append({"card": rel(p), "from": m["agent"], "to": to, "thread": h.get("thread"),
                                     "crossed": arrived, "waits_for": None if arrived else "the person's word for this crossing"})
    return out


# ---------------------------------------------------------------------------------------------------- main

def opt(rest, flag, required=True):
    if flag in rest:
        i = rest.index(flag)
        if i + 1 < len(rest):
            return rest[i + 1]
    if required:
        raise Refused("give %s" % flag)
    return None


def main(argv):
    cmds = ("members", "question", "agree", "words", "round", "carry", "brief", "open", "wait", "collect", "handover",
            "status")
    if not argv or argv[0] not in cmds:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "members":
            print(json.dumps({"hub": me(), "members": members_report()}, indent=2, ensure_ascii=False))
        elif cmd == "question":
            q, cards = question(opt(rest, "--draft"))
            print(json.dumps({"written": "question/%s.json" % q["id"], "question": q["question"],
                              "done_when": q["done_when"], "agreed": None,
                              "list": [{"id": c["id"], "to": c["to"]["agent"], "asks": c["asks"],
                                        "answers_items": c["answers_items"], "returns": c["returns"],
                                        "done_when": c["done_when"]} for c in cards]}, indent=2, ensure_ascii=False))
        elif cmd == "agree":
            p, q = agree(opt(rest, "--question"), opt(rest, "--words"))
            print(json.dumps({"written": rel(p), "agreed": q["agreed"]}, indent=2, ensure_ascii=False))
        elif cmd == "words":
            p, q = words(opt(rest, "--question"), opt(rest, "--words"))
            print(json.dumps({"written": rel(p), "person_words": q["person_words"]}, indent=2, ensure_ascii=False))
        elif cmd == "round":
            quotes, i = [], 0
            while i < len(rest):
                if rest[i] == "--quote":
                    if i + 3 >= len(rest) + 0 and len(rest[i + 1:i + 4]) < 3:
                        raise Refused("--quote takes a question revision, an index and the words quoted")
                    quotes.append(tuple(rest[i + 1:i + 4]))
                    i += 4
                else:
                    i += 1
            p, card = next_round(opt(rest, "--assignment"), quotes)
            print(json.dumps({"written": rel(p), "card": card}, indent=2, ensure_ascii=False))
        elif cmd == "carry":
            print(json.dumps(carry(opt(rest, "--assignment"), opt(rest, "--session"), "--again" in rest), indent=2,
                             ensure_ascii=False))
        elif cmd == "brief":
            text, _ = brief(opt(rest, "--assignment"))
            print(text, end="")
        elif cmd == "open":
            print(json.dumps(open_session(opt(rest, "--assignment"), opt(rest, "--model"), opt(rest, "--effort"),
                                          opt(rest, "--permission-mode"), opt(rest, "--words")), indent=2, ensure_ascii=False))
        elif cmd == "wait":
            s = opt(rest, "--slice", required=False)
            out, running = wait(float(s) if s else DEFAULT_SLICE)
            print(json.dumps({"sessions": out, "running": running}, indent=2, ensure_ascii=False))
            return 5 if running else 0
        elif cmd == "collect":
            print(json.dumps({"collected": collect(opt(rest, "--session"))}, indent=2, ensure_ascii=False))
        elif cmd == "handover":
            print(json.dumps(handover(opt(rest, "--card"), opt(rest, "--to"), opt(rest, "--session"), opt(rest, "--words")),
                             indent=2, ensure_ascii=False))
        else:
            print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    except Refused as e:
        print(json.dumps({"refused": str(e)}, indent=2, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
