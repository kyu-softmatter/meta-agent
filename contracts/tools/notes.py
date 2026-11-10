#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/notes.py -- notes between seats (plan.md 14-29, meta_agent/tasks/009).

  python contracts/tools/notes.py list [--role ROLE]                  asks that wait, for one role or for all
  python contracts/tools/notes.py ask --seat NAME --to ROLE [--task ID] TEXT
  python contracts/tools/notes.py reply NOTE_ID --seat NAME TEXT       by a seat of the role that was asked
  python contracts/tools/notes.py withdraw NOTE_ID --seat NAME TEXT    by the seat that asked

A note is one file, meta_agent/inbox/seats/<YYYYMMDD>-<from seat>-<n>.json, written by its sender and never
edited (the inbox is an append-only root); every role may write the folder. A reply or a withdrawal is a new
file whose `answers` names the ask. An ask nobody answered is PENDING for its `to_role` (check 21), so a
seat that sits down sees what waits for its role. This is how a meta seat asks the design seat for a schema
or a check; it is not the bridge between built agents (M8). Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seats as seat_rules  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NOTES_REL = "meta_agent/inbox/seats"
NOTE_RE = re.compile(r"^([0-9]{8})-([a-z]+-[a-z]+-[0-9]{8}-[1-9][0-9]*)-([1-9][0-9]*)\.json$")
NOTE_PATH_RE = re.compile(r"^" + re.escape(NOTES_REL) + r"/([0-9]{8})-([a-z]+-[a-z]+-[0-9]{8}-[1-9][0-9]*)-([1-9][0-9]*)\.json$")
KINDS = ("ask", "reply", "withdrawn")
NOT_NOTES = (".gitkeep", "README.md")


def read(tree):
    ndir = os.path.join(tree, *NOTES_REL.split("/"))
    notes, stray = {}, []
    if os.path.isdir(ndir):
        for name in sorted(os.listdir(ndir)):
            if name in NOT_NOTES:
                continue
            m = NOTE_RE.match(name)
            if not m:
                stray.append(name)
                continue
            try:
                with open(os.path.join(ndir, name), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except ValueError:
                data = None
            notes[name[:-5]] = {"name": name, "seat": m.group(2), "data": data}
    return notes, stray


def role_of(seats, name):
    p = seat_rules.parse_name(name)
    return p[0] if p else None


def judge(tree, seats):
    """([(path, message)] to fail, [(path, message)] pending)."""
    notes, stray = read(tree)
    fails, pending = [], []
    for name in stray:
        fails.append((NOTES_REL + "/" + name, "not a note file: <YYYYMMDD>-<from seat>-<n>.json"))
    closed = set()
    for nid, n in sorted(notes.items()):
        path = NOTES_REL + "/" + n["name"]
        d = n["data"]
        if not isinstance(d, dict):
            fails.append((path, "malformed JSON"))
            continue
        if d.get("from") != n["seat"]:
            fails.append((path, "from %r is not the seat in the file's name" % (d.get("from"),)))
        if seat_rules.seat_by_name(seats, n["seat"]) is None:
            fails.append((path, "%s is not a seat in contracts/seats.json" % n["seat"]))
        if d.get("kind") not in KINDS:
            fails.append((path, "kind %r is not one of %s" % (d.get("kind"), ", ".join(KINDS))))
            continue
        if not isinstance(d.get("text"), str) or not d["text"].strip():
            fails.append((path, "a note says something: no text"))
        if d["kind"] == "ask":
            if d.get("to_role") not in seats.get("roles", {}):
                fails.append((path, "to_role %r is not a role in contracts/seats.json" % (d.get("to_role"),)))
            if d.get("answers") is not None:
                fails.append((path, "an ask answers nothing"))
            continue
        target = notes.get(d.get("answers"))
        td = target["data"] if target else None
        if not isinstance(td, dict) or td.get("kind") != "ask":
            fails.append((path, "answers %r is not an ask in this folder" % (d.get("answers"),)))
            continue
        if d["kind"] == "reply" and role_of(seats, n["seat"]) != td.get("to_role"):
            fails.append((path, "the ask was to the %s role; %s is a %s seat" % (td.get("to_role"), n["seat"], role_of(seats, n["seat"]))))
            continue
        if d["kind"] == "withdrawn" and n["seat"] != target["seat"]:
            fails.append((path, "only %s, which asked, withdraws %s" % (target["seat"], d.get("answers"))))
            continue
        closed.add(d.get("answers"))
    for nid, n in sorted(notes.items()):
        d = n["data"]
        if isinstance(d, dict) and d.get("kind") == "ask" and nid not in closed and d.get("to_role") in seats.get("roles", {}):
            text = " ".join(str(d.get("text", "")).split())
            pending.append((NOTES_REL + "/" + n["name"], "for the %s role, from %s%s: %s" % (
                d["to_role"], n["seat"], " on tasks/%s" % d["task"] if d.get("task") else "", text[:160])))
    return fails, pending


def note_committer_problem(path, status, email):
    m = NOTE_PATH_RE.match(path)
    if m and status[:1] == "A" and email != seat_rules.email_of(m.group(2)):
        return "%s is committed by %s, not by %s" % (path, email, m.group(2))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--role")
    p = sub.add_parser("ask")
    p.add_argument("--seat", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--task")
    p.add_argument("text")
    for name in ("reply", "withdraw"):
        p = sub.add_parser(name)
        p.add_argument("id")
        p.add_argument("--seat", required=True)
        p.add_argument("text")
    args = ap.parse_args(argv)
    seats = seat_rules.load()
    if args.cmd == "list":
        _, pending = judge(REPO, seats)
        shown = [(p, m) for p, m in pending if not args.role or m.startswith("for the %s role" % args.role)]
        for path, msg in shown:
            print("%s  %s" % (os.path.basename(path)[:-5], msg))
        if not shown:
            print("no ask waits%s" % (" for the %s role" % args.role if args.role else ""))
        return 0
    if seat_rules.seat_by_name(seats, args.seat) is None:
        raise SystemExit("notes: %s is not a seat in contracts/seats.json" % args.seat)
    ndir = os.path.join(REPO, *NOTES_REL.split("/"))
    os.makedirs(ndir, exist_ok=True)
    today = datetime.date.today().strftime("%Y%m%d")
    n = 1
    while os.path.exists(os.path.join(ndir, "%s-%s-%d.json" % (today, args.seat, n))):
        n += 1
    name = "%s-%s-%d.json" % (today, args.seat, n)
    data = {"from": args.seat, "kind": {"ask": "ask", "reply": "reply", "withdraw": "withdrawn"}[args.cmd],
            "to_role": getattr(args, "to", None), "task": getattr(args, "task", None),
            "answers": getattr(args, "id", None), "text": args.text,
            "written_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    if args.cmd != "ask":
        data.pop("to_role")
        data.pop("task")
    path = os.path.join(ndir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    rel = NOTES_REL + "/" + name
    bad = [m for p, m in judge(REPO, seats)[0] if p == rel]
    if bad:
        os.remove(path)
        raise SystemExit("notes: refused, nothing written: " + "; ".join(bad))
    print("written   %s" % rel)
    print('commit it alone: python contracts/tools/seat_commit.py --seat %s -m "notes: %s %s" %s'
          % (args.seat, args.seat, {"ask": "asks the %s role" % getattr(args, "to", ""), "reply": "replies to %s" % getattr(args, "id", ""),
                                    "withdraw": "withdraws %s" % getattr(args, "id", "")}[args.cmd], rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
