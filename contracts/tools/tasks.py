#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/tasks.py -- the task queue as data (plan.md 14-29, meta_agent/tasks/009).

  python contracts/tools/tasks.py list                      every task: status, roles, who holds it
  python contracts/tools/tasks.py next --role ROLE          the lowest open task of this role that nobody holds
                                                            and whose dependencies are done
  python contracts/tools/tasks.py claim ID --seat NAME      write the claim file and print the commit line
  python contracts/tools/tasks.py release ID --seat NAME --why TEXT

meta_agent/tasks/index.json is the design seat's: one row per task file. Where a task has a design part and
another, the other roles wait until the row says design_part: landed. A claim is one file per task and
seat under meta_agent/tasks/claims/, written by the seat that takes the task and never edited, so two
sessions never write the same file; a second claim of a task's role by another seat fails check 20. A
release is a second file beside the claim. The same functions are read by contracts/validate.py (check 20).
Standard library only.
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
TASKS_REL = "meta_agent/tasks"
CLAIMS_REL = TASKS_REL + "/claims"
TASK_FILE_RE = re.compile(r"^([0-9]{3})-[a-z0-9-]+\.md$")
CLAIM_RE = re.compile(r"^([0-9]{3})-([a-z]+-[a-z]+-[0-9]{8}-[1-9][0-9]*)(-released)?\.json$")
CLAIM_PATH_RE = re.compile(r"^" + re.escape(CLAIMS_REL) + r"/([0-9]{3})-([a-z]+-[a-z]+-[0-9]{8}-[1-9][0-9]*)(-released)?\.json$")
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s+([a-z]+)", re.M)
STATUSES = ("open", "done")
DESIGN_PARTS = ("open", "landed")


def waits_for_design(row, role):
    """A task with a design part and another: the other roles wait until the design part has landed."""
    return role != "design" and "design" in row.get("roles", []) and row.get("design_part") != "landed"
NOT_CLAIMS = (".gitkeep", "README.md")


def read(tree):
    """What is on disk: the index (or None), the task files' status words, the claim files."""
    tdir = os.path.join(tree, *TASKS_REL.split("/"))
    out = {"index": None, "index_error": None, "files": {}, "claims": [], "stray": []}
    if not os.path.isdir(tdir):
        return out
    ipath = os.path.join(tdir, "index.json")
    if os.path.exists(ipath):
        try:
            with open(ipath, "r", encoding="utf-8") as f:
                out["index"] = json.load(f)
        except ValueError as e:
            out["index_error"] = str(e)
    for name in sorted(os.listdir(tdir)):
        m = TASK_FILE_RE.match(name)
        if m:
            with open(os.path.join(tdir, name), "r", encoding="utf-8") as f:
                s = STATUS_RE.search(f.read())
            out["files"][m.group(1)] = (name, s.group(1) if s else None)
    cdir = os.path.join(tdir, "claims")
    if os.path.isdir(cdir):
        for name in sorted(os.listdir(cdir)):
            if name in NOT_CLAIMS:
                continue
            m = CLAIM_RE.match(name)
            if not m:
                out["stray"].append(name)
                continue
            try:
                with open(os.path.join(cdir, name), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except ValueError:
                data = None
            out["claims"].append({"name": name, "task": m.group(1), "seat": m.group(2),
                                  "released": bool(m.group(3)), "data": data})
    return out


def rows(state):
    idx = state["index"] or {}
    return {r.get("id"): r for r in idx.get("tasks", []) if isinstance(r, dict)}


def holders(state):
    """{task id: {seat: claim}} for the claims that have no release beside them."""
    released = {(c["task"], c["seat"]) for c in state["claims"] if c["released"]}
    out = {}
    for c in state["claims"]:
        if not c["released"] and (c["task"], c["seat"]) not in released:
            out.setdefault(c["task"], {})[c["seat"]] = c
    return out


def problems(tree, seats, commit_exists=None):
    """[(relative path, message)] for everything check 20 refuses."""
    state = read(tree)
    out = []
    ipath = TASKS_REL + "/index.json"
    if state["index_error"]:
        return [(ipath, "malformed JSON: %s" % state["index_error"])]
    if state["index"] is None:
        if state["files"]:
            out.append((ipath, "the task files have no index.json"))
        return out
    by_id = {}
    for r in state["index"].get("tasks", []):
        rid = r.get("id") if isinstance(r, dict) else None
        if not isinstance(rid, str) or rid in by_id:
            out.append((ipath, "row id %r is missing or issued twice" % (rid,)))
            continue
        by_id[rid] = r
        missing = [k for k in ("file", "status", "roles", "depends_on", "opened") if k not in r]
        if missing:
            out.append((ipath, "%s: no %s" % (rid, ", ".join(missing))))
            continue
        if r["status"] not in STATUSES:
            out.append((ipath, "%s: status %r is not one of %s" % (rid, r["status"], ", ".join(STATUSES))))
        for role in r["roles"]:
            if role not in seats.get("roles", {}):
                out.append((ipath, "%s: role %r is not in contracts/seats.json" % (rid, role)))
        if not r["roles"]:
            out.append((ipath, "%s: no role" % rid))
        if "design" in r["roles"] and len(r["roles"]) > 1 and r.get("design_part") not in DESIGN_PARTS:
            out.append((ipath, "%s: a task with a design part and another says design_part: %s" % (rid, " | ".join(DESIGN_PARTS))))
        f = state["files"].get(rid)
        if f is None or f[0] != r["file"]:
            out.append((ipath, "%s: file %r is not a task file here" % (rid, r["file"])))
        elif f[1] != r["status"]:
            out.append((TASKS_REL + "/" + f[0], "the Status line says %r and index.json says %r" % (f[1], r["status"])))
        if r["status"] == "done":
            sha = r.get("done_commit")
            if not isinstance(sha, str) or not sha:
                out.append((ipath, "%s: done without done_commit" % rid))
            elif commit_exists is not None and not commit_exists(sha):
                out.append((ipath, "%s: done_commit %s is not a commit here" % (rid, sha)))
    for rid, r in by_id.items():
        for dep in r.get("depends_on", []):
            if dep not in by_id:
                out.append((ipath, "%s: depends on %r, which has no row" % (rid, dep)))
    for tid, (name, _) in sorted(state["files"].items()):
        if tid not in by_id:
            out.append((TASKS_REL + "/" + name, "no row in index.json"))
    for name in state["stray"]:
        out.append((CLAIMS_REL + "/" + name, "not a claim file: <task id>-<seat>.json or <task id>-<seat>-released.json"))
    claimed = {(c["task"], c["seat"]) for c in state["claims"] if not c["released"]}
    for c in state["claims"]:
        path = CLAIMS_REL + "/" + c["name"]
        d = c["data"]
        when = "released_at" if c["released"] else "claimed_at"
        if not isinstance(d, dict) or d.get("task") != c["task"] or d.get("seat") != c["seat"] or not d.get(when):
            out.append((path, "the file does not say {task: %s, seat: %s, %s}" % (c["task"], c["seat"], when)))
        if c["released"]:
            if (c["task"], c["seat"]) not in claimed:
                out.append((path, "a release without its claim"))
            elif not (isinstance(d, dict) and d.get("why")):
                out.append((path, "a release says why"))
            continue
        row = by_id.get(c["task"])
        if row is None:
            out.append((path, "task %s has no row" % c["task"]))
            continue
        seat = seat_rules.seat_by_name(seats, c["seat"])
        if seat is None or seat.get("status") != "active":
            out.append((path, "%s is not an active seat in contracts/seats.json" % c["seat"]))
            continue
        if seat.get("role") not in row.get("roles", []):
            out.append((path, "task %s is for %s; %s is a %s seat" % (c["task"], " and ".join(row.get("roles", [])), c["seat"], seat.get("role"))))
        elif row.get("status") == "open" and waits_for_design(row, seat.get("role")):
            out.append((path, "task %s is claimed for the %s role before its design part has landed" % (c["task"], seat.get("role"))))
    for tid, seats_holding in sorted(holders(state).items()):
        row = by_id.get(tid)
        if row is None:
            continue
        by_role = {}
        for sname in sorted(seats_holding):
            seat = seat_rules.seat_by_name(seats, sname)
            if seat is not None:
                by_role.setdefault(seat.get("role"), []).append(sname)
        for role, names in sorted(by_role.items()):
            if len(names) > 1:
                for sname in names:
                    out.append((CLAIMS_REL + "/" + seats_holding[sname]["name"],
                                "task %s is claimed for the %s role by %s; one seat holds a task's role" % (tid, role, " and ".join(names))))
        if row.get("status") == "open":
            undone = [d for d in row.get("depends_on", []) if by_id.get(d, {}).get("status") != "done"]
            if undone:
                for sname in sorted(seats_holding):
                    out.append((CLAIMS_REL + "/" + seats_holding[sname]["name"],
                                "task %s is claimed before %s is done" % (tid, ", ".join(undone))))
    return out


def claim_committer_problem(path, status, email):
    """An added claim or release is committed by the seat its name carries."""
    m = CLAIM_PATH_RE.match(path)
    if m and status[:1] == "A" and email != seat_rules.email_of(m.group(2)):
        return "%s is committed by %s, not by %s" % (path, email, m.group(2))
    return None


def next_task(tree, seats, role):
    state = read(tree)
    by_id = rows(state)
    held = holders(state)
    for tid in sorted(by_id):
        r = by_id[tid]
        if r.get("status") != "open" or role not in r.get("roles", []):
            continue
        if any(by_id.get(d, {}).get("status") != "done" for d in r.get("depends_on", [])):
            continue
        if waits_for_design(r, role):
            continue
        if any((seat_rules.seat_by_name(seats, s) or {}).get("role") == role for s in held.get(tid, {})):
            continue
        return tid
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("next")
    p.add_argument("--role", required=True)
    for name in ("claim", "release"):
        p = sub.add_parser(name)
        p.add_argument("id")
        p.add_argument("--seat", required=True)
        if name == "release":
            p.add_argument("--why", required=True)
    args = ap.parse_args(argv)
    seats = seat_rules.load()
    state = read(REPO)
    by_id = rows(state)
    held = holders(state)
    if args.cmd == "list":
        for tid in sorted(by_id):
            r = by_id[tid]
            who = ", ".join(sorted(held.get(tid, {}))) or "-"
            part = "design part %-6s" % r["design_part"] if r.get("design_part") else " " * 18
            print("%s  %-4s  %-12s  %s  after %-8s  held by %s  %s" % (tid, r.get("status"), "+".join(r.get("roles", [])), part,
                  ",".join(r.get("depends_on", [])) or "-", who, r.get("file")))
        return 0
    if args.cmd == "next":
        tid = next_task(REPO, seats, args.role)
        if tid is None:
            print("no open, unclaimed task for the %s role whose dependencies are done" % args.role)
            waiting = [t for t in sorted(by_id) if by_id[t].get("status") == "open" and args.role in by_id[t].get("roles", [])
                       and waits_for_design(by_id[t], args.role)]
            if waiting:
                print("waiting for their design part to land: %s" % ", ".join(waiting))
            return 1
        print("%s  %s" % (tid, by_id[tid]["file"]))
        print("claim it in its own commit before you start: python contracts/tools/tasks.py claim %s --seat <your seat>" % tid)
        return 0
    seat = seat_rules.seat_by_name(seats, args.seat)
    if seat is None:
        raise SystemExit("tasks: %s is not a seat in contracts/seats.json" % args.seat)
    if args.id not in by_id:
        raise SystemExit("tasks: no task %s in index.json" % args.id)
    cdir = os.path.join(REPO, *CLAIMS_REL.split("/"))
    os.makedirs(cdir, exist_ok=True)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if args.cmd == "claim":
        rel = "%s/%s-%s.json" % (CLAIMS_REL, args.id, args.seat)
        data = {"task": args.id, "seat": args.seat, "claimed_at": now}
    else:
        rel = "%s/%s-%s-released.json" % (CLAIMS_REL, args.id, args.seat)
        data = {"task": args.id, "seat": args.seat, "released_at": now, "why": args.why}
    path = os.path.join(REPO, *rel.split("/"))
    if os.path.exists(path):
        raise SystemExit("tasks: %s exists; a claim is never rewritten" % rel)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    bad = [m for p, m in problems(REPO, seats) if p == rel]
    if bad:
        os.remove(path)
        raise SystemExit("tasks: refused, nothing written: " + "; ".join(bad))
    print("written   %s" % rel)
    print('commit it alone: python contracts/tools/seat_commit.py --seat %s -m "tasks: %s %s %s" %s'
          % (args.seat, args.seat, "claims" if args.cmd == "claim" else "releases", args.id, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
