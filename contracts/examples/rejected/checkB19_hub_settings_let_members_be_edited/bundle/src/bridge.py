#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/bridge.py -- the bridge between two built agents (plan.md 10, M8; meta_agent/tasks/031).

  python contracts/tools/bridge.py carry --card PRODUCER/outbox/NAME.json --to RECEIVER --released-by human --ran-by person
  python contracts/tools/bridge.py carry --card ... --to ... --released-by human --ran-by session --session ID --words "..."
  python contracts/tools/bridge.py carry --trigger hub --card HUB/assignments/NAME.json --to MEMBER --released-by hub --ran-by hub --session ID
  python contracts/tools/bridge.py carry --trigger hub --card MEMBER/outbox/RESULT.json --to HUB --released-by hub --ran-by hub --session ID
  python contracts/tools/bridge.py board BUNDLE                      read only: what is in a bundle's outbox and inbox

The person starts it ("Small tool, I start it", 2026-11-20, docs/ideas/20261120.md), and a card crosses only
on the person's word ("Only on my word"): `carry` refuses unless --released-by is human, and the envelope says
trigger human. A session may run it on the person's word for that crossing ("Yes, on my word
(Recommended)", 2026-11-20; tasks/032, bridge-2), and the envelope says who ran it: --ran-by person, or
--ran-by session with the session's id and the person's words to it, verbatim; `carry` refuses without them.
It carries one hand-over card from the producing bundle's outbox/ into the receiving bundle's
inbox/<thread>/, byte for byte, as r<N>_<name>.json, and writes beside it r<N>_envelope.json: author bridge,
no numbers, the payload's hash, and the payload's degraded. Round N is one more than the thread's last.

On the hub's trigger (meta_agent/tasks/033; the person, 2026-11-20, "Assign freely, carry on my word
(Recommended)") the hub's session carries an assignment from the hub's assignments/ into one of its members,
listed in the hub's members.json and in a question whose list of assignments the person agreed to once ("Ask once
per question (Recommended)"), or a result from a member's outbox/ into its hub; a hand-over between two members
is refused on that trigger and still crosses only on the person's word.

It authors nothing, converts nothing, judges no science, runs no engine and never writes in the producing
bundle; what the receiving bundle does with a value is its own (a receipt in its received/, check 25). After a
carry the two folders are judged with `python contracts/validate.py <folder holding both> --checks 1,2,25`.
Standard library only.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

ENVELOPE_RE = re.compile(r"^r([0-9]+)_envelope\.json$")


class Refused(Exception):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def next_round(thread_dir):
    rounds = [int(m.group(1)) for m in (ENVELOPE_RE.match(n) for n in (os.listdir(thread_dir) if os.path.isdir(thread_dir) else [])) if m]
    return (max(rounds) if rounds else 0) + 1


def who_ran(ran_by, trigger="human"):
    """The envelope's ran_by, checked: {"by": "person"} or {"by": "session", "session": ID, "words": TEXT} on the
    person's word; {"by": "hub", "session": ID} on the hub's trigger."""
    if trigger == "hub":
        session = ran_by.get("session") if isinstance(ran_by, dict) else None
        if not isinstance(ran_by, dict) or ran_by.get("by") != "hub" or not (isinstance(session, str) and session.strip()) \
                or set(ran_by) != {"by", "session"}:
            raise Refused("on the hub's trigger the hub's session runs the bridge: --ran-by hub --session ID")
        return {"by": "hub", "session": session}
    if not isinstance(ran_by, dict) or ran_by.get("by") not in ("person", "session"):
        raise Refused("say who ran the bridge: --ran-by person, or --ran-by session --session ID --words TEXT")
    if ran_by["by"] == "person":
        if set(ran_by) != {"by"}:
            raise Refused("a carry the person ran names no session and quotes no words")
        return {"by": "person"}
    session, words = ran_by.get("session"), ran_by.get("words")
    if not (isinstance(session, str) and session.strip() and isinstance(words, str) and words.strip()):
        raise Refused("a session runs the bridge only on the person's word for this crossing: give --session "
                      "and the person's words, verbatim, with --words")
    if set(ran_by) != {"by", "session", "words"}:
        raise Refused("ran_by holds by, session and words only")
    return {"by": "session", "session": session, "words": words}


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _same_agent(a, b):
    return isinstance(a, dict) and isinstance(b, dict) and (a.get("agent"), a.get("build")) == (b.get("agent"), b.get("build"))


def _members(hub):
    data = _load(os.path.join(hub, "members.json"))
    return data if isinstance(data, dict) and data.get("card") == "hub_members" else None


def _agreed(hub, assignment):
    """Whether the assignment is in a question of the hub whose list the person agreed to."""
    qdir = os.path.join(hub, "question")
    for name in sorted(os.listdir(qdir)) if os.path.isdir(qdir) else []:
        q = _load(os.path.join(qdir, name))
        if isinstance(q, dict) and q.get("card") == "hub_question" and q.get("id") == assignment.get("question") \
                and assignment.get("id") in (q.get("assignments") or []) \
                and isinstance(q.get("agreed"), dict) and str(q["agreed"].get("words") or "").strip():
            return True
    return False


def _check_hub_route(card, producer, receiver, trigger):
    """An assignment goes from a hub to one of its members; a result from a member to its hub."""
    kind = card.get("card")
    if kind == "assignment":
        members = _members(producer)
        if members is None:
            raise Refused("an assignment is carried from a hub's assignments/, beside its members.json")
        if not _same_agent(card.get("from"), members.get("hub")):
            raise Refused("the assignment's from is not the hub of members.json")
        m = next((m for m in members.get("members") or [] if _same_agent(m, card.get("to"))), None)
        if m is None:
            raise Refused("the assignment's to is not a member of the hub")
        if os.path.realpath(os.path.join(producer, m.get("folder", ""))) != os.path.realpath(receiver):
            raise Refused("the receiving folder is not the member's folder in members.json")
        if trigger == "hub" and not _agreed(producer, card):
            raise Refused("the assignment is not in a question whose list of assignments the person agreed to")
    elif kind == "result" and trigger == "hub":
        members = _members(receiver)
        if members is None or not _same_agent(card.get("to"), members.get("hub")):
            raise Refused("on the hub's trigger a result is carried to its hub only")
        m = next((m for m in members.get("members") or [] if _same_agent(m, card.get("from"))), None)
        if m is None or os.path.realpath(os.path.join(receiver, m.get("folder", ""))) != os.path.realpath(producer):
            raise Refused("the result's from is not a member of the hub at the folder members.json names")


def carry(card_path, receiver, released_by, ran_by=None, now=None, trigger="human"):
    """Carry one card; returns (envelope path, payload path). Raises Refused."""
    if trigger not in ("human", "hub"):
        raise Refused("a card crosses on the person's word (--trigger human) or on the hub's run (--trigger hub)")
    if trigger == "human" and released_by != "human":
        raise Refused("a card crosses only on the person's word: --released-by human")
    if trigger == "hub" and released_by != "hub":
        raise Refused("on the hub's trigger the hub releases: --released-by hub")
    ran_by = who_ran(ran_by, trigger)
    card_path = os.path.abspath(card_path)
    receiver = os.path.abspath(receiver)
    outbox = os.path.dirname(card_path)
    producer = os.path.dirname(outbox)
    box = os.path.basename(outbox)
    if box not in ("outbox", "assignments") or not os.path.isfile(card_path):
        raise Refused("the card is not a file in a bundle's outbox/ or a hub's assignments/: %s" % card_path)
    if not os.path.isdir(receiver):
        raise Refused("the receiving bundle is not a folder: %s" % receiver)
    if os.path.realpath(receiver) == os.path.realpath(producer):
        raise Refused("the producing and the receiving bundle are one folder")
    with open(card_path, "rb") as f:
        raw = f.read()
    try:
        card = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise Refused("the card is not JSON: %s" % e)
    kind = card.get("card") if isinstance(card, dict) else None
    if kind not in ("handover", "assignment", "result"):
        raise Refused("the bridge carries handover, assignment and result cards only")
    if (kind == "assignment") != (box == "assignments"):
        raise Refused("an assignment is carried from a hub's assignments/, and a %s from an outbox/" % kind
                      if kind != "assignment" else "an assignment is carried from a hub's assignments/")
    if trigger == "hub" and kind == "handover":
        raise Refused("a hand-over between two agents crosses only on the person's word, not on the hub's trigger")
    for key in ("id", "thread", "from", "to"):
        if not card.get(key):
            raise Refused("the %s has no %s" % (kind, key))
    _check_hub_route(card, producer, receiver, trigger)
    thread = card["thread"]
    if not re.match(r"^[A-Za-z][A-Za-z0-9._-]{1,80}$", str(thread)):
        raise Refused("the thread %r cannot name a folder" % thread)
    thread_dir = os.path.join(receiver, "inbox", thread)
    os.makedirs(thread_dir, exist_ok=True)
    rnd = next_round(thread_dir)
    payload_name = "r%d_%s" % (rnd, os.path.basename(card_path))
    payload_path = os.path.join(thread_dir, payload_name)
    envelope_path = os.path.join(thread_dir, "r%d_envelope.json" % rnd)
    if os.path.exists(payload_path) or os.path.exists(envelope_path):
        raise Refused("round %d of thread %s is already there" % (rnd, thread))
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    shutil.copyfile(card_path, payload_path)
    if sha256_file(payload_path) != digest:
        os.remove(payload_path)
        raise Refused("the copy is not the card's bytes")
    when = (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = {
        "card": "bridge_envelope", "schema_version": "0.1",
        "id": "env-%s-r%d" % (thread, rnd), "revision": 1, "author": "bridge", "created_at": when,
        "numbers": [], "degraded": list(card.get("degraded") or []), "status": "draft",
        "thread": thread, "round": rnd, "from": card["from"], "to": card["to"],
        "payload": {"file": payload_name, "card": kind, "id": card["id"], "sha256": digest,
                    "origin": box + "/" + os.path.basename(card_path)},
        "trigger": trigger, "released_by": released_by, "released_at": when, "ran_by": ran_by,
    }
    with open(envelope_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n")
    return envelope_path, payload_path


def board(bundle):
    """Lines saying what a bundle's outbox holds and what arrived in its inbox, and whether each arrival is
    the bytes its envelope states and has a receipt. Reads only."""
    bundle = os.path.abspath(bundle)
    lines = []
    outbox = os.path.join(bundle, "outbox")
    for name in sorted(os.listdir(outbox)) if os.path.isdir(outbox) else []:
        if name.endswith(".json"):
            lines.append("outbox   %s" % name)
    receipts = {}
    received = os.path.join(bundle, "received")
    for name in sorted(os.listdir(received)) if os.path.isdir(received) else []:
        try:
            with open(os.path.join(received, name), "r", encoding="utf-8") as f:
                rc = json.load(f)
            receipts.setdefault(rc.get("envelope"), []).append("%s %s" % (rc.get("name"), rc.get("state")))
        except (ValueError, OSError, UnicodeDecodeError, AttributeError):
            continue
    inbox = os.path.join(bundle, "inbox")
    for thread in sorted(os.listdir(inbox)) if os.path.isdir(inbox) else []:
        tdir = os.path.join(inbox, thread)
        for name in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else []:
            if not ENVELOPE_RE.match(name):
                continue
            with open(os.path.join(tdir, name), "r", encoding="utf-8") as f:
                env = json.load(f)
            pl = env.get("payload") or {}
            ppath = os.path.join(tdir, pl.get("file", ""))
            same = os.path.isfile(ppath) and sha256_file(ppath) == pl.get("sha256")
            key = "inbox/%s/%s" % (thread, name)
            rb = env.get("ran_by") or {}
            ran = "ran by the person" if rb.get("by") == "person" else (
                "ran by session %s on the person's words" % rb.get("session") if rb.get("by") == "session" else (
                    "ran by the hub's session %s" % rb.get("session") if rb.get("by") == "hub" else "who ran it unsaid"))
            lines.append("inbox    %s  %s  from %s  %s  %s  receipts: %s" % (
                key, pl.get("id"), (env.get("from") or {}).get("agent"), ran,
                "unchanged" if same else "CHANGED OR MISSING", ", ".join(receipts.get(key, [])) or "none"))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="the bridge between two built agents; the person starts it")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("carry")
    c.add_argument("--card", required=True)
    c.add_argument("--to", required=True)
    c.add_argument("--released-by", required=True)
    c.add_argument("--trigger", default="human", choices=("human", "hub"),
                   help="human (default): the person's word, for any card; hub: the hub's run, for an assignment or a result")
    c.add_argument("--ran-by", required=True, choices=("person", "session", "hub"),
                   help="person when the person runs this command; session when a session runs it on the person's word; "
                        "hub when the hub's session runs it on the hub's trigger")
    c.add_argument("--session", help="with --ran-by session or hub: the session's id or name")
    c.add_argument("--words", help="with --ran-by session: the person's words to it for this crossing, verbatim")
    b = sub.add_parser("board")
    b.add_argument("bundle")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "carry":
            ran_by = {"by": a.ran_by}
            if a.ran_by in ("session", "hub") or a.session or a.words:
                ran_by.update({k: v for k, v in (("session", a.session), ("words", a.words)) if v is not None})
            env, payload = carry(a.card, a.to, a.released_by, ran_by, trigger=a.trigger)
            print("carried  %s" % payload)
            print("envelope %s" % env)
            return 0
        for line in board(a.bundle):
            print(line)
        return 0
    except Refused as e:
        print("refused  %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
