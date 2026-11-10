# -*- coding: utf-8 -*-
"""contracts/tools/seats.py -- what a seat is, in one place (plan.md 9, contracts/seats.json).

Read by contracts/validate.py (check 6), bootstrap.py (`seat`) and contracts/tools/seat_commit.py, so that
the three cannot disagree about a name, a role's paths or the standing rule for self-registration
(the person, 2026-11-09, docs/ideas/20261109.md). Standard library only; no git, no I/O beyond load().
"""
import datetime
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SEATS_PATH = os.path.join(os.path.dirname(HERE), "seats.json")
SEATS_REL = "contracts/seats.json"
NAME_RE = re.compile(r"^([a-z]+)-([a-z]+)-([0-9]{8})-([1-9][0-9]*)$")
ROLE_KEYS = ("paths", "excludes", "owns")


def load(path=SEATS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(seats):
    return json.dumps(seats, indent=2, ensure_ascii=False) + "\n"


def parse_name(name):
    """(role, machine, yyyymmdd, n) or None."""
    m = NAME_RE.match(name) if isinstance(name, str) else None
    if not m:
        return None
    try:
        datetime.datetime.strptime(m.group(3), "%Y%m%d")
    except ValueError:
        return None
    return m.group(1), m.group(2), m.group(3), int(m.group(4))


def email_of(name):
    return "%s@seat.invalid" % name


def seat_by_email(seats, email):
    for s in seats.get("seats", []):
        if s.get("committer_email") == email:
            return s
    return None


def seat_by_name(seats, name):
    for s in seats.get("seats", []):
        if s.get("seat") == name:
            return s
    return None


def path_in(entry, path):
    if entry == "*":
        return "/" not in path
    if entry.endswith("/"):
        return path.startswith(entry)
    return path == entry


def inside(seat, path):
    return any(path_in(p, path) for p in seat.get("paths", [])) and \
        not any(path_in(x, path) for x in seat.get("excludes", []))


def next_name(seats, role, machine, yyyymmdd):
    """The first name of this role, machine and date that was never issued."""
    used = set()
    for s in seats.get("seats", []):
        p = parse_name(s.get("seat"))
        if p and p[:3] == (role, machine, yyyymmdd):
            used.add(p[3])
    n = 1
    while n in used:
        n += 1
    return "%s-%s-%s-%d" % (role, machine, yyyymmdd, n)


def entry_for(seats, name, seated_by, seated=None):
    """The entry a seat of this name gets: the role's row, copied unchanged."""
    role, machine, _, _ = parse_name(name)
    row = seats["roles"][role]
    entry = {
        "seat": name,
        "committer_email": email_of(name),
        "role": role,
        "machine": machine,
        "seated_by": seated_by,
        "status": "active",
        "owns": list(row.get("owns", [])),
        "paths": list(row["paths"]),
        "excludes": list(row.get("excludes", [])),
    }
    if seated:
        entry["seated"] = seated
    return entry


def entry_problems(seats, entry):
    """What is wrong with one entry against the table's roles and machines (no problem: [])."""
    out = []
    name = entry.get("seat")
    p = parse_name(name)
    if not p:
        return ["seat name %r is not <role>-<machine>-<YYYYMMDD>-<n> with a real date" % (name,)]
    role, machine, _, _ = p
    if entry.get("committer_email") != email_of(name):
        out.append("%s: committer_email is not %s" % (name, email_of(name)))
    if entry.get("role") != role:
        out.append("%s: role %r is not the name's %r" % (name, entry.get("role"), role))
    if entry.get("machine") != machine:
        out.append("%s: machine %r is not the name's %r" % (name, entry.get("machine"), machine))
    roles = seats.get("roles", {})
    if role not in roles:
        out.append("%s: role %r is not in roles (a new role is the person's)" % (name, role))
    if machine not in seats.get("machines", {}):
        out.append("%s: machine tag %r is not in machines (the person gives a new computer its tag)" % (name, machine))
    if role in roles and entry.get("status") == "active":
        row = roles[role]
        for key in ROLE_KEYS:
            if list(entry.get(key, [])) != list(row.get(key, [])):
                out.append("%s: %s differ from the %s role's row" % (name, key, role))
    return out


def table_problems(seats):
    """What is wrong with the whole table."""
    out = []
    if not isinstance(seats.get("roles"), dict) or not seats.get("roles"):
        out.append("no roles table")
    if not isinstance(seats.get("machines"), dict) or not seats.get("machines"):
        out.append("no machines table")
    names, emails = set(), set()
    for entry in seats.get("seats", []):
        out.extend(entry_problems(seats, entry))
        if entry.get("seat") in names:
            out.append("%s: the name is issued twice" % entry.get("seat"))
        if entry.get("committer_email") in emails:
            out.append("%s: the committer_email is issued twice" % entry.get("seat"))
        names.add(entry.get("seat"))
        emails.add(entry.get("committer_email"))
    return out


def _json(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def self_registration(old_text, new_text, email, yyyymmdd=None):
    """Is this change to seats.json a session adding its own entry, and if so what is wrong with it?

    Returns (candidate, problems). candidate is True when the new table has exactly one seat name the old
    one lacks and that entry carries the committer's own email; the rule of 2026-11-09 then applies and
    problems lists every way the entry breaks it. Roles, machines and the rows are read from the OLD table,
    so a commit cannot widen a role and seat itself into it in one step.
    """
    old, new = _json(old_text), _json(new_text)
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False, []
    old_names = {s.get("seat") for s in old.get("seats", [])}
    added = [s for s in new.get("seats", []) if s.get("seat") not in old_names]
    if len(added) != 1 or added[0].get("committer_email") != email:
        return False, []
    entry = added[0]
    problems = []
    rest = dict(new)
    rest["seats"] = [s for s in new.get("seats", []) if s is not entry]
    if rest != old:
        problems.append("the commit changes more of %s than the committer's own entry" % SEATS_REL)
    problems.extend(entry_problems(old, entry))
    if entry.get("status") != "active":
        problems.append("%s: status is not active" % entry.get("seat"))
    if not str(entry.get("seated_by", "")).startswith("self"):
        problems.append("%s: seated_by does not start with 'self' (a seat the person gives is added by the design seat)" % entry.get("seat"))
    p = parse_name(entry.get("seat"))
    if p and yyyymmdd:
        try:
            a = datetime.datetime.strptime(p[2], "%Y%m%d")
            b = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
            if abs((a - b).days) > 1:
                problems.append("%s: the name's date is not the day of the commit (%s)" % (entry.get("seat"), yyyymmdd))
        except ValueError:
            pass
    return True, problems
