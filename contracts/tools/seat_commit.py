#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/seat_commit.py -- commit as a seat in a working copy that other seats share.

  python contracts/tools/seat_commit.py --seat NAME -m MESSAGE PATH [PATH ...]
  python contracts/tools/seat_commit.py --seat NAME -F MESSAGE_FILE PATH [PATH ...]     (-F - reads stdin)

Several seats may work in the one working copy at the same time (plan.md 9, the person, 2026-11-09). The
repository's own committer.name can hold one seat only and `git add -A` takes everybody's files, so this
tool makes one commit that is one seat's:

  - the committer is set for this commit alone (GIT_COMMITTER_NAME, GIT_COMMITTER_EMAIL); the author stays
    whoever git says the person is;
  - only the paths named are committed (`git commit --only`), so what another seat has staged or left
    unstaged is neither committed nor lost;
  - the seat is read from HEAD's contracts/seats.json and every path must lie inside its boundary; the one
    exception is a session adding its own entry under the standing rule, which is its own commit;
  - the pre-commit hook runs as always; nothing is amended, forced or skipped, and nothing is pushed;
  - the commit is read back and printed: hash, committer, paths.

Exit 0 when the commit exists and is what was asked; 1 when it was refused, with the reason. Standard
library only.
"""
import argparse
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seats as seat_rules  # noqa: E402


def git(root, *args, env=None, check=True):
    p = subprocess.run(["git"] + list(args), cwd=root, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit("seat_commit: git %s failed: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
    return p


def refuse(msg):
    sys.stderr.write("seat_commit: refused: %s\n" % msg)
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seat", required=True, help="the seat's name, as in contracts/seats.json")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-m", "--message")
    g.add_argument("-F", "--file", help="read the commit message from this file")
    ap.add_argument("paths", nargs="+", help="the paths this commit takes, and nothing else")
    args = ap.parse_args(argv)

    root = git(os.getcwd(), "rev-parse", "--show-toplevel").stdout.strip()
    name = args.seat
    email = seat_rules.email_of(name)
    paths = []
    for p in args.paths:
        r = os.path.relpath(os.path.abspath(p), root).replace(os.sep, "/")
        if r.startswith("../") or r == "..":
            return refuse("%s is outside the repository" % p)
        if r not in paths:
            paths.append(r)

    head = git(root, "show", "HEAD:" + seat_rules.SEATS_REL, check=False)
    if head.returncode != 0:
        return refuse("HEAD has no %s" % seat_rules.SEATS_REL)
    import json
    table = json.loads(head.stdout)
    seat = seat_rules.seat_by_name(table, name)
    if seat is None:
        if paths != [seat_rules.SEATS_REL]:
            return refuse("%s is not a seat at HEAD. Register it first, in its own commit: python bootstrap.py seat "
                          "<role> --write, then this tool with %s as the only path" % (name, seat_rules.SEATS_REL))
        with open(os.path.join(root, seat_rules.SEATS_REL), "r", encoding="utf-8") as f:
            new_text = f.read()
        candidate, problems = seat_rules.self_registration(head.stdout, new_text, email,
                                                           datetime.date.today().strftime("%Y%m%d"))
        if not candidate:
            return refuse("the working copy's %s does not add exactly one entry for %s" % (seat_rules.SEATS_REL, email))
        if problems:
            return refuse("this self-registration breaks the standing rule: " + "; ".join(problems))
    else:
        if seat.get("status") != "active":
            return refuse("%s is not active" % name)
        outside = [p for p in paths if not seat_rules.inside(seat, p)]
        if outside:
            return refuse("outside %s's paths: %s" % (name, ", ".join(outside)))

    changed = git(root, "status", "--porcelain", "--", *paths).stdout.strip()
    if not changed:
        return refuse("nothing to commit under %s" % ", ".join(paths))

    env = dict(os.environ, GIT_COMMITTER_NAME="seat:%s" % name, GIT_COMMITTER_EMAIL=email, PYTHONUTF8="1")
    before = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "add", "--", *paths, env=env)
    msg = ["-m", args.message] if args.message is not None else \
        ["-F", args.file if args.file == "-" else os.path.abspath(args.file)]  # "-" reads the message from stdin
    p = git(root, "commit", "--only", *msg, "--", *paths, env=env, check=False)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    after = git(root, "rev-parse", "HEAD").stdout.strip()
    if p.returncode != 0 or after == before:
        return refuse("no commit was made (the hook's verdict is above); the named paths stay staged")

    got_email = git(root, "log", "-1", "--format=%ce").stdout.strip()
    got_name = git(root, "log", "-1", "--format=%cn").stdout.strip()
    got_paths = [l.split("\t")[-1] for l in git(root, "show", "--name-status", "--format=", "HEAD").stdout.splitlines() if l.strip()]
    extra = [g for g in got_paths if not any(g == q or g.startswith(q.rstrip("/") + "/") for q in paths)]
    print("commit    %s" % after[:7])
    print("committer %s <%s>" % (got_name, got_email))
    print("paths     %s" % ", ".join(got_paths))
    if got_email != email or extra:
        return refuse("the commit read back is not what was asked (committer %s, extra paths %s); it exists and is "
                      "not undone by this tool" % (got_email, extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
