#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/testfolder.py -- tests in a folder of their own, which may be removed at any time
(plan.md 14-39, meta_agent/tasks/016; the person, 2026-11-16, docs/ideas/20261116.md).

  python contracts/tools/testfolder.py where                  the test folder and the log folder of this clone
  python contracts/tools/testfolder.py make [--bundle BUILD ...] [--no-clone] [--no-bundles] [--source REPO]
                                                              a new run: a clean clone of this repository and a
                                                              copy of each bundle (default: every agent's newest build);
                                                              --source takes them from another repository's committed
                                                              head instead, such as the clone of an earlier run
  python contracts/tools/testfolder.py status                 every run: what it holds, what was collected, removed or not
  python contracts/tools/testfolder.py session RUN ITEM --brief FILE [--model M] [--effort E]
                                                              run one unattended session in an item of a run
  python contracts/tools/testfolder.py collect [RUN] [--no-gate]
                                                              what the sessions of a run did and what they changed
  python contracts/tools/testfolder.py wipe (RUN | --all) [--no-collect] [--sessions]
                                                              collect, then remove the run's folder

The Meta-Agent and the bundles it builds are tested outside this repository, so that a session in a bundle
is given the bundle's own instructions and nothing of this repository's (MP2), and so that a test changes
no record here. Two folders, both outside the repository and neither inside the other:

  the test folder   holds runs. A run is made from the committed head and may be removed at any time.
  the log folder    holds what was collected from each run, and stays. It is never committed: a session's
                    transcript is the person's, and publication scope is never inferred (MP11).

Where they are is this computer's, read from the clone's git configuration as the machine tag is:
`git config meta-agent.testfolder <path>` and `git config meta-agent.testlogs <path>`; --root and --logs
say otherwise for one call.

A run is `<test folder>/<YYYYMMDD>-<n>/`, and a name is never used twice, even after its folder is gone: the
application keeps a session's history and memory by the path the session was opened in, so a path used
again would hand a later test what an earlier one left. The log folder gets the run's entry the moment it
is made, which is what keeps the name taken. In a run:

  TESTFOLDER.json           the mark of a folder this tool made; wipe removes no folder without it
  origin.git/               a bare copy of this repository at its head, with no remote of its own
  repo/                     a clone of that copy, set up as begin-session asks of a clone. Its origin is the
                            copy beside it: it never moves while the test runs, and a push ends inside the run
  bundles/<agent>-<build>/  the bundle alone, as committed, its digest equal to its build card's

`session` runs one session with nobody present, as a person at a terminal would start it: the command-line
`claude -p` in the item's folder, the brief on its standard input, in the permission mode `auto` (the
person, 2026-11-16) and never in one that asks nothing. The variables an application gives its own sessions
are not passed on, so the session is given what the folder gives and the user's own settings, and nothing of
the session that started it. What it was asked and what the command printed are kept in the log folder
(`<run>/sessions/<item>-<n>.json`); its transcript is taken by `collect` like any other.

`collect` writes `<log folder>/<run>/collect-<n>/`, a new folder each time. For every session whose
transcript says it was opened inside the run: the transcript as the application wrote it, one line per tool
call beside it (`<session>.calls.jsonl`, a call that ended in an error with the error's text), what the
session itself wrote to its reader in order (`<session>.said.md`, its report last), and in `collection.json`
what was read off it: the model, the first
and last time, what it was asked, the skills it loaded, the files it wrote and which of them lie outside the
folder it was opened in. For a bundle: the files added, changed and removed against the hashes of `make`,
and the files themselves. For the clone: the commits made, the difference from the head it was cloned at,
the untracked files, and the gate's verdict line. What a collection cannot show is written into it: a
session removed from the application before the collection has no transcript left, and a file a shell
command wrote outside the folder is seen only as the command's text.

`wipe` collects, then removes the run's folder. It removes nothing of this repository or of the log folder.
With `--sessions` it also removes, from the application's own folder, the transcripts it has just collected
of the sessions opened in the run (the person, 2026-11-16: the folder and the sessions are removed); a
session the application lists is removed there first, and this is for the ones run from the command line.
Standard library only, Python 3.9 or later.
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDS_REL = "meta_agent/builds"
MARK = "TESTFOLDER.json"
VERSION = "0.1"
RUN_RE = re.compile(r"^([0-9]{8})-([1-9][0-9]*)$")
COLLECT_RE = re.compile(r"^collect-([1-9][0-9]*)$")
KEY_ROOT, KEY_LOGS = "meta-agent.testfolder", "meta-agent.testlogs"
ABOVE = ("CLAUDE.md", ".claude", ".git")          # what must not stand above a run (MP2)
HASH_SKIP = (".git", "__pycache__")               # as the build card's digest skips them
WRITERS = ("Write", "Edit", "NotebookEdit")       # the application's tools that write a file by its path
PERMISSION_MODES = ("auto", "acceptEdits", "dontAsk", "manual", "plan")   # never one that asks nothing
NOT_PASSED_ON = ("CLAUDE", "ANTHROPIC", "USE_STAGING_OAUTH", "USE_LOCAL_OAUTH")   # an application's own, by prefix
NOT_SEEN = [
    "a session removed from the application before this collection: its transcript is gone with it",
    "a file a shell command wrote outside the folder the session was opened in: only the command's text is here",
    "what a session was shown by the application and did not write into its transcript",
]


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------- small things
def git(cwd, *args, check=True, raw=False):
    """Run git with no GIT_* variable of a caller (a hook's index is not this call's)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(["git"] + list(args), cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise Refused("git %s: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout if raw else p.stdout.decode("utf-8", "replace")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def real(path):
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


def inside(path, parent):
    """Is path the parent or under it, links resolved."""
    p, q = real(path), real(parent)
    return p == q or p.startswith(q.rstrip(os.sep) + os.sep)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    if os.path.islink(path) and not os.path.exists(path):
        # a link whose target is not there (a package cache makes them): its own text is what it is
        h.update(b"symlink\0" + os.readlink(path).encode("utf-8", "surrogateescape"))
        return h.hexdigest()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(root):
    """{relative posix path: sha256} of every file under root, as the build card's digest reads a tree."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in HASH_SKIP)
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            try:
                out[os.path.relpath(full, root).replace(os.sep, "/")] = sha256_file(full)
            except FileNotFoundError:   # removed between the listing and the reading
                continue
    return out


def tree_digest(hashes):
    """The digest a build card carries as bundle_sha256 (meta_agent/src/cards.py, sha256_tree)."""
    h = hashlib.sha256()
    for rel in sorted(hashes):
        h.update(rel.encode("utf-8") + b"\0")
        h.update(bytes.fromhex(hashes[rel]) + b"\0")
    return "sha256:" + h.hexdigest()


# ---------------------------------------------------------------------------- the two folders
def folders(args, repo=REPO):
    def one(given, key, what):
        value = given or git(repo, "config", "--get", key, check=False).strip()
        if not value:
            raise Refused("where the %s is has not been said on this computer. The person names it: "
                          "git config %s <path>" % (what, key))
        return os.path.abspath(os.path.expanduser(value))
    root, logs = one(args.root, KEY_ROOT, "test folder"), one(args.logs, KEY_LOGS, "log folder")
    for name, path in (("test folder", root), ("log folder", logs)):
        if inside(path, repo) or inside(repo, path):
            raise Refused("the %s (%s) and the repository (%s) must lie apart" % (name, path, repo))
    if inside(root, logs) or inside(logs, root):
        raise Refused("the test folder (%s) and the log folder (%s) must lie apart: one is removed, the other "
                      "stays" % (root, logs))
    return root, logs


def stands_above(folder, home=None):
    """Instruction files, session skills and repositories at or above a folder. The home folder's own
    `.claude` is the application's and stands above every session on this computer; it is not counted."""
    home = real(home or os.path.expanduser("~"))
    found, d = [], real(folder)
    while True:
        for n in ABOVE:
            p = os.path.join(d, n)
            if os.path.lexists(p) and not (n == ".claude" and d == home):
                found.append(p)
        parent = os.path.dirname(d)
        if parent == d:
            return found
        d = parent


def run_names(root, logs):
    names = set()
    for d in (root, logs):
        if os.path.isdir(d):
            names.update(n for n in os.listdir(d) if RUN_RE.match(n) and os.path.isdir(os.path.join(d, n)))
    return sorted(names, key=lambda n: (RUN_RE.match(n).group(1), int(RUN_RE.match(n).group(2))))


def next_run(root, logs, today):
    used = [int(RUN_RE.match(n).group(2)) for n in run_names(root, logs) if RUN_RE.match(n).group(1) == today]
    return "%s-%d" % (today, max(used) + 1 if used else 1)


def marked(root, run):
    """The run's folder, if it is one this tool made."""
    path = os.path.join(root, run)
    mark = os.path.join(path, MARK)
    if not RUN_RE.match(run) or not os.path.isfile(mark):
        return None
    try:
        data = read_json(mark)
    except ValueError:
        return None
    return path if data.get("run") == run and data.get("testfolder") else None


# ---------------------------------------------------------------------------- make
def newest_builds(repo):
    out = []
    for agent in git(repo, "ls-tree", "-d", "--name-only", "HEAD", BUILDS_REL + "/").split():
        builds = git(repo, "ls-tree", "-d", "--name-only", "HEAD", agent + "/").split()
        if builds:
            out.append(sorted(builds)[-1])
    return out


def build_rel(repo, given):
    rel = os.path.relpath(os.path.abspath(given), repo).replace(os.sep, "/").rstrip("/")
    if rel.endswith("/bundle"):
        rel = rel[:-len("/bundle")]
    if rel.startswith("../"):
        raise Refused("%s is outside the repository" % given)
    return rel


def export_tree(repo, rel, dest):
    """The tree at HEAD:<rel> as committed, written to dest. Nothing uncommitted and nothing ignored comes along."""
    data = git(repo, "archive", "--format=tar", "HEAD:" + rel, raw=True)
    os.makedirs(dest)
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        for m in tf.getmembers():
            if m.name.startswith("/") or ".." in m.name.split("/") or not (m.isfile() or m.isdir()):
                raise Refused("%s holds %s, which is not a plain file under it" % (rel, m.name))
        try:
            tf.extractall(dest, filter="data")
        except TypeError:                       # Python before the extraction filters
            tf.extractall(dest)


def make_bundle(repo, rel, run_path):
    card_text = git(repo, "show", "HEAD:%s/build.json" % rel, check=False)
    if not card_text:
        raise Refused("%s has no build.json at HEAD; a test takes a build as committed" % rel)
    card = json.loads(card_text)
    parts = rel.split("/")
    name = "%s-%s" % (parts[-2], parts[-1])
    item_rel = "bundles/" + name
    dest = os.path.join(run_path, "bundles", name)
    export_tree(repo, card.get("bundle_path") or rel + "/bundle", dest)
    hashes = tree_hashes(dest)
    digest = tree_digest(hashes)
    if digest != card.get("bundle_sha256"):
        raise Refused("%s: the copy's digest is %s and the build card says %s" % (rel, digest, card.get("bundle_sha256")))
    return {"name": name, "kind": "bundle", "path": item_rel, "build": rel, "build_id": card.get("id"),
            "template_version": card.get("template_version"), "bundle_sha256": digest, "files": hashes}


def make_clone(repo, run_path):
    origin, dest = os.path.join(run_path, "origin.git"), os.path.join(run_path, "repo")
    git(repo, "clone", "--quiet", "--bare", "--no-hardlinks", repo, origin)
    git(origin, "remote", "remove", "origin")        # nothing in a run points at the working copy
    git(run_path, "clone", "--quiet", "--no-hardlinks", origin, dest)
    setup = {"remote.origin.url": "origin.git, a bare copy inside the run"}
    if os.path.isdir(os.path.join(dest, "contracts", "hooks")):
        git(dest, "config", "core.hooksPath", "contracts/hooks")
        setup["core.hooksPath"] = "contracts/hooks"
    tag = git(repo, "config", "--get", "meta-agent.machine", check=False).strip()
    if tag:                                     # this computer's tag, already given by the person
        git(dest, "config", "meta-agent.machine", tag)
        setup["meta-agent.machine"] = tag
    return {"name": "repo", "kind": "clone", "path": "repo", "head": git(dest, "rev-parse", "HEAD").strip(),
            "branch": git(dest, "rev-parse", "--abbrev-ref", "HEAD").strip(), "setup": setup}


def make(args, repo=REPO):
    root, logs = folders(args, repo)
    if args.source:
        source = os.path.abspath(os.path.expanduser(args.source))
        if not os.path.isdir(os.path.join(source, ".git")) and git(source, "rev-parse", "--is-bare-repository", check=False).strip() != "true":
            raise Refused("%s is not a git repository" % source)
        if inside(source, root) and marked(root, os.path.relpath(source, root).split(os.sep)[0]) is None:
            raise Refused("%s lies in the test folder but in no run this tool made" % source)
        repo = source                                   # what is copied comes from there; the folders stay this clone's
    above = stands_above(root)
    if above:
        raise Refused("a run under %s would not stand alone; above it: %s" % (root, ", ".join(above)))
    builds = [build_rel(repo, b) for b in args.bundle] if args.bundle else ([] if args.no_bundles else newest_builds(repo))
    if args.no_clone and not builds:
        raise Refused("nothing to make: no clone and no bundle")
    run = next_run(root, logs, datetime.date.today().strftime("%Y%m%d"))
    run_path = os.path.join(root, run)
    os.makedirs(run_path)
    try:
        items = [] if args.no_clone else [make_clone(repo, run_path)]
        items += [make_bundle(repo, rel, run_path) for rel in builds]
        made = {"testfolder": VERSION, "run": run, "made_at": now(), "folder": run_path,
                "source": {"repository": repo, "head": git(repo, "rev-parse", "HEAD").strip(),
                           "uncommitted": [l[3:] for l in git(repo, "status", "--porcelain").splitlines() if l.strip()]},
                "user_level": [p for p in (os.path.join(os.path.expanduser("~"), ".claude", n) for n in ("CLAUDE.md", "skills"))
                               if os.path.exists(p)],
                "items": items}
        write_json(os.path.join(run_path, MARK), {"testfolder": VERSION, "run": run, "made_at": made["made_at"],
                                                  "logs": os.path.join(logs, run)})
        write_json(os.path.join(logs, run, "made.json"), made)
    except BaseException:
        shutil.rmtree(run_path, ignore_errors=True)
        raise
    print("run     %s" % run)
    print("folder  %s" % run_path)
    print("logs    %s" % os.path.join(logs, run))
    for it in items:
        if it["kind"] == "clone":
            print("clone   %s  at %s on %s; its origin is a copy inside the run" % (it["path"], it["head"][:7], it["branch"]))
        else:
            print("bundle  %s  %d file(s), digest equal to %s's" % (it["path"], len(it["files"]), it["build_id"]))
    if made["source"]["uncommitted"]:
        print("note    %d uncommitted path(s) of the working copy are not in the run; a run is the committed head"
              % len(made["source"]["uncommitted"]))
    if made["user_level"]:
        print("note    every session on this computer is also given: %s" % ", ".join(made["user_level"]))
    print("open a session in:")
    for it in items:
        print("  %s" % os.path.join(run_path, *it["path"].split("/")))
    return 0


# ---------------------------------------------------------------------------- collect: sessions
def transcripts_dir(given=None):
    if given:
        return os.path.abspath(os.path.expanduser(given))
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(base, "projects")


def first_cwd(path):
    """The folder a session was opened in: the first `cwd` its transcript carries."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"cwd"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if isinstance(o, dict) and isinstance(o.get("cwd"), str):
                    return o["cwd"]
    except OSError:
        pass
    return None


def find_sessions(projects, run_path):
    """[(project folder, transcript file, cwd)] of every session opened at or under run_path."""
    out = []
    if not os.path.isdir(projects):
        return out
    for d in sorted(os.listdir(projects)):
        pdir = os.path.join(projects, d)
        if not os.path.isdir(pdir):
            continue
        for n in sorted(os.listdir(pdir)):
            if n.endswith(".jsonl"):
                cwd = first_cwd(os.path.join(pdir, n))
                if cwd and inside(cwd, run_path):
                    out.append((pdir, n, cwd))
    return out


def _short(tool, given):
    """What a call was, short enough for one line: the command, the file, the skill."""
    given = given if isinstance(given, dict) else {}
    out = {}
    for k in ("command", "file_path", "notebook_path", "skill", "args", "subagent_type", "description", "url", "query", "pattern", "path"):
        if isinstance(given.get(k), (str, int, float, bool)):
            out[k] = given[k]
    if not out:
        out["keys"] = sorted(given)
    return out


def read_transcript(path):
    """What one transcript says: (summary, calls, said). Every value is read off the file; none is judged."""
    s = {"cwd": None, "models": [], "efforts": [], "first": None, "last": None, "asked": [], "lines": 0, "unread_lines": 0}
    calls, results, usage, said = [], {}, {}, []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            s["lines"] += 1
            try:
                o = json.loads(line)
            except ValueError:
                s["unread_lines"] += 1
                continue
            if not isinstance(o, dict):
                continue
            if s["cwd"] is None and isinstance(o.get("cwd"), str):
                s["cwd"] = o["cwd"]
            ts = o.get("timestamp")
            if isinstance(ts, str):
                s["first"] = ts if s["first"] is None or ts < s["first"] else s["first"]
                s["last"] = ts if s["last"] is None or ts > s["last"] else s["last"]
            m = o.get("message") if isinstance(o.get("message"), dict) else None
            if m is None:
                continue
            content = m.get("content")
            if o.get("type") == "assistant":
                if isinstance(m.get("model"), str) and m["model"] not in s["models"]:
                    s["models"].append(m["model"])
                if isinstance(o.get("effort"), str) and o["effort"] not in s["efforts"]:
                    s["efforts"].append(o["effort"])
                if isinstance(m.get("usage"), dict):
                    usage[m.get("id") or o.get("uuid")] = m["usage"]     # the last usage of a message stands
                for b in content if isinstance(content, list) else []:
                    if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str) \
                            and b["text"].strip() and not o.get("isSidechain"):
                        said.append((ts, b["text"]))
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        call = {"n": len(calls) + 1, "at": ts, "tool": b.get("name"), "id": b.get("id")}
                        call.update(_short(b.get("name"), b.get("input")))
                        if o.get("isSidechain"):
                            call["sidechain"] = True
                        calls.append(call)
            elif o.get("type") == "user":
                blocks = content if isinstance(content, list) else []
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        results[b.get("tool_use_id")] = _result_text(b.get("content")) if b.get("is_error") else None
                if o.get("isMeta") or o.get("isSidechain") or any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                    continue
                text = content if isinstance(content, str) else "\n".join(
                    b["text"] for b in blocks if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
                if text.strip():
                    s["asked"].append(text)
    for c in calls:
        c["answered"] = c["id"] in results
        c["error"] = results.get(c["id"]) is not None
        if c["error"]:
            c["error_text"] = results[c["id"]]
    cwd = s["cwd"]
    by_tool = {}
    for c in calls:
        by_tool[c["tool"]] = by_tool.get(c["tool"], 0) + 1
    written = []
    for c in calls:
        p = c.get("file_path") or c.get("notebook_path")
        if c["tool"] in WRITERS and isinstance(p, str) and p not in written:
            written.append(p)
    tokens = {}
    for u in usage.values():
        for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            if isinstance(u.get(k), int):
                tokens[k] = tokens.get(k, 0) + u[k]
    s.update({
        "calls": len(calls), "calls_by_tool": by_tool, "calls_in_error": sum(1 for c in calls if c["error"]),
        "skills_loaded": [c.get("skill") for c in calls if c["tool"] == "Skill" and c.get("skill")],
        "library_skills_run": library_skills_run(calls),
        "asked_the_person": by_tool.get("AskUserQuestion", 0),
        "files_written": written,
        "written_outside": [p for p in written if cwd and not inside(p if os.path.isabs(p) else os.path.join(cwd, p), cwd)],
        "tokens": tokens, "tokens_read_as": "the last usage of each message id in the transcript, summed",
    })
    return s, calls, said


SKILL_RUN_RE = re.compile(r"run_skill\.py\s+([a-z][a-z0-9_]*@v[1-9][0-9]*)")


def library_skills_run(calls):
    """{skill id: times} a session ran through a bundle's skill runner, read from its shell commands: what a
    built agent uses of its library (the person, 2026-11-17)."""
    out = {}
    for c in calls:
        for sid in SKILL_RUN_RE.findall(c.get("command") or ""):
            out[sid] = out.get(sid, 0) + 1
    return out


def _result_text(content):
    """The text of a tool's result, whichever of the application's two shapes it has."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return "" if content is None else json.dumps(content, ensure_ascii=False)


def collect_sessions(projects, run_path, items, dest):
    out = []
    by_path = sorted(((os.path.join(run_path, *it["path"].split("/")), it["name"]) for it in items), key=lambda t: -len(t[0]))
    for pdir, name, cwd in find_sessions(projects, run_path):
        item = next((n for p, n in by_path if inside(cwd, p)), "_run")
        sid = name[:-len(".jsonl")]
        sdir = os.path.join(dest, "sessions", item)
        os.makedirs(sdir, exist_ok=True)
        shutil.copy2(os.path.join(pdir, name), os.path.join(sdir, name))
        if os.path.isdir(os.path.join(pdir, sid)):      # subagents' transcripts and saved tool results
            shutil.copytree(os.path.join(pdir, sid), os.path.join(sdir, sid), dirs_exist_ok=True)
        memory = os.path.join(pdir, "memory")
        kept = sorted(os.listdir(memory)) if os.path.isdir(memory) else []
        if kept:                                        # what the application keeps for this path between sessions
            shutil.copytree(memory, os.path.join(sdir, "memory"), dirs_exist_ok=True)
        summary, calls, said = read_transcript(os.path.join(pdir, name))
        with open(os.path.join(sdir, sid + ".calls.jsonl"), "w", encoding="utf-8") as f:
            for c in calls:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        with open(os.path.join(sdir, sid + ".said.md"), "w", encoding="utf-8") as f:
            for at, text in said:
                f.write("<!-- %s -->\n\n%s\n\n" % (at, text.strip()))
        summary.update({"session": sid, "item": item, "transcript": "sessions/%s/%s" % (item, name),
                        "calls_file": "sessions/%s/%s.calls.jsonl" % (item, sid),
                        "said_file": "sessions/%s/%s.said.md" % (item, sid), "said": len(said), "memory_files": kept})
        out.append(summary)
    return out


# ---------------------------------------------------------------------------- collect: what changed
ENV_MARKERS = ("conda-meta", "pyvenv.cfg", "CACHEDIR.TAG")   # a package environment (conda, pixi, a venv) or a tagged cache


def _not_kept(src_root, rel, seen):
    """The folder of rel that is a package environment or a cache, or None. Such a folder is listed and
    counted in a collection, not copied: it is what an install made, not what a session did (run 20261117-2)."""
    parts = rel.split("/")[:-1]
    for i in range(1, len(parts) + 1):
        d = "/".join(parts[:i])
        if d not in seen:
            full = os.path.join(src_root, *parts[:i])
            ignore = os.path.join(full, ".gitignore")
            star = False
            if os.path.isfile(ignore):
                with open(ignore, "r", encoding="utf-8", errors="replace") as f:
                    star = f.read().strip() == "*"
            seen[d] = ("cache" in parts[i - 1].lower() or star
                       or any(os.path.exists(os.path.join(full, m)) for m in ENV_MARKERS))
        if seen[d]:
            return d
    return None


def _copy_into(src_root, rels, dest_root):
    """Copy rels; return {folder: number of files} of what was left as an environment or a cache."""
    seen, left = {}, {}
    for rel in rels:
        d = _not_kept(src_root, rel, seen)
        if d is not None:
            left[d] = left.get(d, 0) + 1
            continue
        src = os.path.join(src_root, *rel.split("/"))
        if os.path.isfile(src):
            dst = os.path.join(dest_root, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return left


def bundle_changes(item, path, dest):
    made, cur = item["files"], tree_hashes(path)
    added = sorted(set(cur) - set(made))
    removed = sorted(set(made) - set(cur))
    changed = sorted(r for r in cur if r in made and cur[r] != made[r])
    left = _copy_into(path, added + changed, os.path.join(dest, "files"))
    return {"name": item["name"], "kind": "bundle", "added": added, "changed": changed, "removed": removed,
            "not_copied": left, "needed": needed_lines(path) if "failures.jsonl" in added + changed else [],
            "digest_made": item["bundle_sha256"], "digest_now": tree_digest(cur)}


def needed_lines(bundle):
    """What a bundle session wrote it needed, line by line of its failures.jsonl: where a missing skill shows
    (the person, 2026-11-17). A line names it under `needed`, at its top or in its `detail`."""
    out = []
    try:
        with open(os.path.join(bundle, "failures.jsonl"), "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        detail = d.get("detail") if isinstance(d.get("detail"), dict) else {}
        need = d.get("needed", detail.get("needed"))
        if isinstance(need, (str, list)) and need:
            out.append(need if isinstance(need, str) else "; ".join(str(x) for x in need))
    return out


def clone_changes(item, path, dest, gate=True):
    head = item["head"]
    commits = [dict(zip(("commit", "committer", "subject"), l.split("\t", 2)))
               for l in git(path, "log", "--reverse", "--format=%H%x09%cn%x09%s", head + "..HEAD").splitlines() if l.strip()]
    status = [l for l in git(path, "status", "--porcelain").splitlines() if l.strip()]
    patch = git(path, "diff", "--binary", head, raw=True)
    os.makedirs(dest, exist_ok=True)
    if patch:
        with open(os.path.join(dest, "changes.patch"), "wb") as f:
            f.write(patch)
    untracked = [l for l in git(path, "ls-files", "--others", "--exclude-standard").splitlines() if l.strip()]
    left = _copy_into(path, untracked, os.path.join(dest, "files"))
    out = {"name": item["name"], "kind": "clone", "head_made": head, "head_now": git(path, "rev-parse", "HEAD").strip(),
           "commits": commits, "uncommitted": status, "untracked": untracked, "not_copied": left,
           "patch": "changes.patch" if patch else None,
           "verdict": None}
    if gate and os.path.isfile(os.path.join(path, "contracts", "validate.py")):
        env = dict({k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, os.path.join("contracts", "validate.py")], cwd=path, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = [l for l in p.stdout.decode("utf-8", "replace").splitlines() if l.strip()]
        out["verdict"] = lines[-1] if lines else None
        out["verdict_exit"] = p.returncode
    return out


def collect_run(root, logs, run, projects, gate=True):
    made_path = os.path.join(logs, run, "made.json")
    if not os.path.isfile(made_path):
        raise Refused("%s has no entry in the log folder (%s)" % (run, made_path))
    made = read_json(made_path)
    run_path = os.path.join(root, run)
    standing = marked(root, run) is not None
    done = [int(COLLECT_RE.match(n).group(1)) for n in os.listdir(os.path.join(logs, run)) if COLLECT_RE.match(n)]
    name = "collect-%d" % (max(done) + 1 if done else 1)
    dest = os.path.join(logs, run, name)
    os.makedirs(dest)
    sessions = collect_sessions(projects, run_path, made["items"], dest)
    items = []
    for it in made["items"]:
        path = os.path.join(run_path, *it["path"].split("/"))
        idest = os.path.join(dest, "items", it["name"])
        if not standing or not os.path.isdir(path):
            items.append({"name": it["name"], "kind": it["kind"], "gone": True})
        elif it["kind"] == "bundle":
            items.append(bundle_changes(it, path, idest))
        else:
            items.append(clone_changes(it, path, idest, gate))
    write_json(os.path.join(dest, "collection.json"),
               {"testfolder": VERSION, "run": run, "collection": name, "collected_at": now(), "run_standing": standing,
                "transcripts_from": projects, "sessions": sessions, "items": items, "not_seen": NOT_SEEN})
    return dest, sessions, items


def report_collection(run, dest, sessions, items):
    print("run         %s" % run)
    print("collection  %s" % dest)
    per = {}
    for s in sessions:
        per[s["item"]] = per.get(s["item"], 0) + 1
    print("sessions    %d%s" % (len(sessions), "  (%s)" % ", ".join("%s: %d" % kv for kv in sorted(per.items())) if per else ""))
    for s in sessions:
        print("  %s  %s  %s at %s  %d call(s), %d in error; skills %s; %d file(s) by a writing tool, %d outside its "
              "folder (what a shell command wrote is under the item)"
              % (s["item"], s["session"][:8], "/".join(s["models"]) or "-", "/".join(s["efforts"]) or "?", s["calls"],
                 s["calls_in_error"], ", ".join(s["skills_loaded"]) or "none", len(s["files_written"]), len(s["written_outside"])))
        ran = s.get("library_skills_run") or {}
        print("  %s  %s  library skills run: %s; asked the person %d time(s)"
              % (s["item"], s["session"][:8], ", ".join("%s x%d" % kv for kv in sorted(ran.items())) or "none",
                 s.get("asked_the_person", 0)))
    for it in items:
        if it.get("gone"):
            print("%-11s %s  its folder is gone; transcripts only" % (it["name"], it["kind"]))
        elif it["kind"] == "bundle":
            print("%-11s bundle  %d added, %d changed, %d removed" % (it["name"], len(it["added"]), len(it["changed"]), len(it["removed"])))
            for need in it.get("needed") or []:
                print("%-11s         needed: %s" % ("", need[:160]))
            for d, n in sorted(it.get("not_copied", {}).items()):
                print("%-11s         %s: %d file(s) of an environment or a cache, listed and not copied" % ("", d, n))
        else:
            print("%-11s clone   %d commit(s), %d uncommitted path(s); %s"
                  % (it["name"], len(it["commits"]), len(it["uncommitted"]), it["verdict"] or "the gate was not run"))


def collect(args, repo=REPO):
    root, logs = folders(args, repo)
    run = args.run
    if not run:
        standing = [n for n in run_names(root, logs) if marked(root, n)]
        if len(standing) != 1:
            raise Refused("name the run: %s" % (", ".join(standing) or "none stands in %s" % root))
        run = standing[0]
    dest, sessions, items = collect_run(root, logs, run, transcripts_dir(args.transcripts), not args.no_gate)
    report_collection(run, dest, sessions, items)
    return 0


# ---------------------------------------------------------------------------- session: one unattended session
def session(args, repo=REPO):
    root, logs = folders(args, repo)
    run_path = marked(root, args.run)
    if run_path is None:
        raise Refused("%s is not a run that stands in %s" % (args.run, root))
    made = read_json(os.path.join(logs, args.run, "made.json"))
    item = next((it for it in made["items"] if it["name"] == args.item), None)
    if item is None:
        raise Refused("%s has no item %s; it has %s" % (args.run, args.item, ", ".join(it["name"] for it in made["items"])))
    if args.permission_mode not in PERMISSION_MODES:
        raise Refused("the permission mode is one of %s" % ", ".join(PERMISSION_MODES))
    exe = args.claude or os.environ.get("TESTFOLDER_CLAUDE") or shutil.which("claude")
    if not exe:
        raise Refused("no command-line claude on this computer's PATH; --claude names one")
    with open(args.brief, "r", encoding="utf-8") as f:
        brief = f.read()
    cmd = [exe, "-p", "--output-format", "json", "--permission-mode", args.permission_mode]
    cmd += (["--model", args.model] if args.model else []) + (["--effort", args.effort] if args.effort else [])
    env = {k: v for k, v in os.environ.items() if not k.startswith(NOT_PASSED_ON) and not k.startswith("GIT_")}
    cwd = os.path.join(run_path, *item["path"].split("/"))
    started = now()
    p = subprocess.run(cmd, cwd=cwd, env=env, input=brief.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.stdout.decode("utf-8", "replace")
    try:
        result = json.loads(out)
    except ValueError:
        result = None
    sdir = os.path.join(logs, args.run, "sessions")
    os.makedirs(sdir, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(sdir, "%s-%d.json" % (args.item, n))):
        n += 1
    record = {"testfolder": VERSION, "run": args.run, "item": args.item, "started_at": started, "ended_at": now(),
              "command": [os.path.basename(exe)] + cmd[1:], "cwd": cwd, "model": args.model, "effort": args.effort,
              "permission_mode": args.permission_mode, "brief_file": os.path.abspath(args.brief), "brief": brief,
              "exit": p.returncode, "result": result if result is not None else out[-4000:],
              "stderr": p.stderr.decode("utf-8", "replace")[-4000:]}
    path = os.path.join(sdir, "%s-%d.json" % (args.item, n))
    write_json(path, record)
    failed = p.returncode != 0 or result is None or bool(result.get("is_error"))
    said = (result.get("result") if isinstance(result, dict) else out) or ""
    print("session  %s in %s  %s" % ((result or {}).get("session_id", "?"), args.item, "FAILED TO RUN" if failed else "ended"))
    print("record   %s" % path)
    print("said     %s" % (said.strip().splitlines()[0][:200] if said.strip() else "(nothing)"))
    return 1 if failed else 0


# ---------------------------------------------------------------------------- wipe, status, where
def remove_transcripts(projects, run_path, collection):
    """Remove from the application's folder the transcripts of the run's sessions, each only when its copy is
    in the collection; a project folder left holding nothing goes too."""
    gone = []
    copied = set()
    for dirpath, _, filenames in os.walk(os.path.join(collection, "sessions")):
        copied.update(fn for fn in filenames if fn.endswith(".jsonl") and not fn.endswith(".calls.jsonl"))
    for pdir, name, _ in find_sessions(projects, run_path):
        if name not in copied:
            continue
        os.remove(os.path.join(pdir, name))
        shutil.rmtree(os.path.join(pdir, name[:-len(".jsonl")]), ignore_errors=True)
        gone.append(name[:-len(".jsonl")])
        left = [n for n in os.listdir(pdir) if not (n == "memory" and not os.listdir(os.path.join(pdir, n)))]
        if not left:
            shutil.rmtree(pdir, ignore_errors=True)
    return gone


def wipe(args, repo=REPO):
    root, logs = folders(args, repo)
    if bool(args.run) == bool(args.all):
        raise Refused("name one run, or --all")
    runs = [n for n in run_names(root, logs) if marked(root, n)] if args.all else [args.run]
    if not runs:
        print("no run stands in %s" % root)
        return 0
    for run in runs:
        path = marked(root, run)
        if path is None:
            raise Refused("%s is not a run this tool made (no %s in it); nothing is removed" % (os.path.join(root, run), MARK))
        if not inside(path, root) or inside(path, repo) or inside(path, logs):
            raise Refused("%s does not lie in the test folder alone; nothing is removed" % path)
        collection, gone = None, []
        if args.sessions and args.no_collect:
            raise Refused("a session's transcript is removed only after it has been collected; drop --no-collect")
        projects = transcripts_dir(args.transcripts)
        if not args.no_collect:
            dest, sessions, items = collect_run(root, logs, run, projects, not args.no_gate)
            report_collection(run, dest, sessions, items)
            collection = os.path.basename(dest)
        if args.sessions:
            gone = remove_transcripts(projects, path, os.path.join(logs, run, collection))
        shutil.rmtree(path)
        if os.path.lexists(path):
            raise Refused("%s could not be removed whole" % path)
        write_json(os.path.join(logs, run, "wiped.json"),
                   {"run": run, "wiped_at": now(), "collected_first": collection, "sessions_removed": gone})
        print("removed     %s%s" % (path, "" if collection else "  (not collected first)"))
        if args.sessions:
            print("removed     %d session transcript(s) from %s" % (len(gone), projects))
    return 0


def status(args, repo=REPO):
    root, logs = folders(args, repo)
    names = run_names(root, logs)
    if not names:
        print("no run yet; make one: python contracts/tools/testfolder.py make")
        return 0
    for run in names:
        ldir = os.path.join(logs, run)
        made = read_json(os.path.join(ldir, "made.json")) if os.path.isfile(os.path.join(ldir, "made.json")) else None
        cols = sorted((n for n in os.listdir(ldir) if COLLECT_RE.match(n)), key=lambda n: int(COLLECT_RE.match(n).group(1))) \
            if os.path.isdir(ldir) else []
        where = "stands" if marked(root, run) else ("removed" if os.path.isfile(os.path.join(ldir, "wiped.json")) else
                                                    ("not this tool's" if os.path.isdir(os.path.join(root, run)) else "gone"))
        held = ", ".join(it["name"] for it in made["items"]) if made else "no entry in the log folder"
        last = ""
        if cols:
            c = read_json(os.path.join(ldir, cols[-1], "collection.json"))
            last = "; %s at %s: %d session(s)" % (cols[-1], c["collected_at"], len(c["sessions"]))
        print("%-12s %-8s made %s at %s; %s; %d collection(s)%s"
              % (run, where, made["made_at"] if made else "?", made["source"]["head"][:7] if made else "?", held, len(cols), last))
    return 0


def where(args, repo=REPO):
    for what, key, given in (("test folder", KEY_ROOT, args.root), ("log folder", KEY_LOGS, args.logs)):
        value = given or git(repo, "config", "--get", key, check=False).strip()
        print("%-12s %s" % (what, os.path.abspath(os.path.expanduser(value)) if value else
                            "not said on this computer; the person names it: git config %s <path>" % key))
    print("%-12s %s" % ("transcripts", transcripts_dir(getattr(args, "transcripts", None))))
    folders(args, repo)
    return 0


def main(argv=None, repo=REPO):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="the test folder, for this call")
    ap.add_argument("--logs", help="the log folder, for this call")
    ap.add_argument("--transcripts", help="where the application keeps its sessions' transcripts, for this call")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where")
    m = sub.add_parser("make")
    m.add_argument("--bundle", action="append", default=[], metavar="BUILD", help="a build folder, e.g. meta_agent/builds/echo/0004")
    m.add_argument("--no-clone", action="store_true")
    m.add_argument("--no-bundles", action="store_true")
    m.add_argument("--source", help="the repository whose committed head the run is made from (default: this one)")
    sub.add_parser("status")
    r = sub.add_parser("session")
    r.add_argument("run")
    r.add_argument("item")
    r.add_argument("--brief", required=True, help="a file holding what the session is asked")
    r.add_argument("--model")
    r.add_argument("--effort")
    r.add_argument("--permission-mode", default="auto")
    r.add_argument("--claude", help="the command-line claude to run, when it is not the one on PATH")
    c = sub.add_parser("collect")
    c.add_argument("run", nargs="?")
    c.add_argument("--no-gate", action="store_true", help="do not run the clone's gate")
    w = sub.add_parser("wipe")
    w.add_argument("run", nargs="?")
    w.add_argument("--all", action="store_true")
    w.add_argument("--no-collect", action="store_true")
    w.add_argument("--no-gate", action="store_true")
    w.add_argument("--sessions", action="store_true", help="also remove the collected transcripts from the application's folder")
    args = ap.parse_args(argv)
    try:
        return {"where": where, "make": make, "status": status, "session": session, "collect": collect, "wipe": wipe}[args.cmd](args, repo)
    except Refused as e:
        sys.stderr.write("testfolder: refused: %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
