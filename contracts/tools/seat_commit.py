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
    exception is a session adding its own entry under the standing rule, which is its own commit, and
    commits HEAD's table with that one entry added, so that other seats' entries, written into the
    working file at the same time and not yet committed, neither block it nor come along;
  - a leading byte order mark of the message is dropped (office-12);
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


def git(root, *args, env=None, check=True, input=None):
    # bytes in and out, decoded here: a text-mode pipe would write "\n" as "\r\n" on Windows
    p = subprocess.run(["git"] + list(args), cwd=root, env=env, capture_output=True,
                       input=None if input is None else input.encode("utf-8"))
    p.stdout, p.stderr = (p.stdout or b"").decode("utf-8", "replace"), (p.stderr or b"").decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit("seat_commit: git %s failed: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
    return p


def _real(path):
    """path with its links and Windows' short 8.3 names resolved, as far as it exists: a deleted file being
    committed does not exist, so its folder is resolved and its name kept."""
    path = os.path.abspath(path)
    head, tail = path, []
    while not os.path.exists(head):
        head, t = os.path.split(head)
        if not t:
            break
        tail.insert(0, t)
    return os.path.join(os.path.realpath(head), *tail)


def repo_rel(path, root):
    """path relative to the repository's top level, in git's spelling, or None when it lies outside. The
    two are compared resolved: git prints the long form of a folder that the temporary folder may name by
    its 8.3 short form (C:\\Users\\KYUHWA~1, office-4), and a path on another drive has no relative path."""
    try:
        r = os.path.relpath(_real(path), _real(root)).replace(os.sep, "/")
    except ValueError:                          # another drive
        return None
    if r == ".." or r.startswith("../"):
        return None
    return r


def read_message(args):
    """The commit message as text, without a leading byte order mark: Windows PowerShell 5.1's Out-File
    -Encoding utf8 writes one, and git keeps it as the first character of the subject (office-12, 182ae68)."""
    if args.message is not None:
        text = args.message
    elif args.file == "-":
        text = sys.stdin.buffer.read().decode("utf-8", "replace")
    else:
        with open(args.file, "rb") as f:
            text = f.read().decode("utf-8", "replace")
    return text[1:] if text.startswith("﻿") else text


def head_mode(root):
    """The mode HEAD records for contracts/seats.json: a copy made on WSL's /mnt drives holds it as 100755, and
    a mode written here would differ from the file's own (run of 5a97f1e in WSL Ubuntu-20.04)."""
    line = git(root, "ls-tree", "HEAD", "--", seat_rules.SEATS_REL).stdout.split()
    return line[0] if line and line[0] in ("100644", "100755") else "100644"


def commit_registration(root, text, message, env):
    """Commit contracts/seats.json as `text` (HEAD's table and the seat's own entry) through an index of its
    own, so that neither what other seats have written into the working file nor what they have staged
    comes along; the pre-commit hook judges that index as it judges any commit's."""
    blob = git(root, "hash-object", "-w", "--stdin", input=text).stdout.strip()
    mode = head_mode(root)
    index = os.path.join(root, git(root, "rev-parse", "--git-path", "seat-commit-%d.index" % os.getpid()).stdout.strip())
    env = dict(env, GIT_INDEX_FILE=os.path.abspath(index))
    try:
        git(root, "read-tree", "HEAD", env=env)
        git(root, "update-index", "--add", "--cacheinfo", "%s,%s,%s" % (mode, blob, seat_rules.SEATS_REL), env=env)
        return git(root, "commit", "-F", "-", env=env, check=False, input=message)
    finally:
        if os.path.exists(index):
            os.remove(index)


def settle_order(root):
    """When the working file holds what HEAD holds and differs only in the order of its entries (seats that
    seated at once committed in another order than they wrote), it is written as HEAD's text; otherwise it is
    left as it is, since what differs is another seat's uncommitted entry."""
    path = os.path.join(root, seat_rules.SEATS_REL)
    head_text = git(root, "show", "HEAD:" + seat_rules.SEATS_REL).stdout
    with open(path, "r", encoding="utf-8") as f:
        working = seat_rules._json(f.read())
    head = seat_rules._json(head_text)
    if not isinstance(working, dict) or not isinstance(head, dict):
        return

    def key(table):
        return dict(table, seats=sorted(table.get("seats", []), key=lambda s: str(s.get("seat"))))
    if working != head and key(working) == key(head):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(head_text)


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
        r = repo_rel(p, root)
        if r is None:
            return refuse("%s is outside the repository" % p)
        if r not in paths:
            paths.append(r)

    message = read_message(args)
    head = git(root, "show", "HEAD:" + seat_rules.SEATS_REL, check=False)
    if head.returncode != 0:
        return refuse("HEAD has no %s" % seat_rules.SEATS_REL)
    import json
    table = json.loads(head.stdout)
    seat = seat_rules.seat_by_name(table, name)
    registration = None
    if seat is None:
        if paths != [seat_rules.SEATS_REL]:
            return refuse("%s is not a seat at HEAD. Register it first, in its own commit: python bootstrap.py seat "
                          "<role> --write, then this tool with %s as the only path" % (name, seat_rules.SEATS_REL))
        with open(os.path.join(root, seat_rules.SEATS_REL), "r", encoding="utf-8") as f:
            working = seat_rules._json(f.read())
        # HEAD's table and this seat's own entry, and nothing else of the working file: seats that seated
        # themselves at the same time each find the others' entries there, uncommitted (2026-11-23,
        # meta-office-20261123-1, -2 and -3), and each commits its own
        mine = [s for s in (working or {}).get("seats", []) if isinstance(s, dict) and s.get("committer_email") == email
                and seat_rules.seat_by_name(table, s.get("seat")) is None]
        if len(mine) != 1:
            return refuse("the working copy's %s does not add exactly one entry for %s" % (seat_rules.SEATS_REL, email))
        registration = seat_rules.dump(dict(table, seats=list(table.get("seats", [])) + mine))
        candidate, problems = seat_rules.self_registration(head.stdout, registration, email,
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
    if registration is None:
        git(root, "add", "--", *paths, env=env)
        p = git(root, "commit", "--only", "-F", "-", "--", *paths, env=env, check=False, input=message)
    else:
        p = commit_registration(root, registration, message, env)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    after = git(root, "rev-parse", "HEAD").stdout.strip()
    if p.returncode != 0 or after == before:
        return refuse("no commit was made (the hook's verdict is above); the named paths stay staged")
    if registration is not None:                # the index agrees with the commit; the others' entries stay unstaged
        blob = git(root, "rev-parse", "HEAD:" + seat_rules.SEATS_REL).stdout.strip()
        git(root, "update-index", "--cacheinfo", "%s,%s,%s" % (head_mode(root), blob, seat_rules.SEATS_REL))
        settle_order(root)

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
