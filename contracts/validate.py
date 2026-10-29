#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/validate.py -- the deterministic validator (plan.md 8).

Usage
  python contracts/validate.py [TREE] [--checks 1,2,...] [--strict] [--quiet]
  python contracts/validate.py --staged                 # pre-commit: adds checks 6 and 7 on the index
  python contracts/validate.py --commit-range A..B      # checks 6 and 7 over commits
  python contracts/validate.py --expect-fail            # every fixture under contracts/examples/rejected/ must be refused

M0 implements checks 1, 2, 3, 6, 7, 11, 15, 16 and 17. Check numbers are fixed and never reused.
Every number printed here is read off this run. The verdict line names the judged tree.
UNDECIDED and PENDING are not passes: --strict counts PENDING as failure.

Requires jsonschema (Anaconda ships it). Without it the script re-executes itself through
`uv run --offline --no-project --with jsonschema` when uv is present, and otherwise refuses to judge.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCHEMAS = os.path.join(HERE, "schemas")
REJECTED = os.path.join(HERE, "examples", "rejected")
IMPLEMENTED = [1, 2, 3, 6, 7, 11, 15, 16, 17]
SKIP_DIRS = {".git", ".agent", ".venv", ".pixi", "node_modules", "__pycache__"}

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environment dependent
    if os.environ.get("META_AGENT_VALIDATE_REEXEC") != "1":
        import shutil
        uv = shutil.which("uv")
        if uv:
            env = dict(os.environ, META_AGENT_VALIDATE_REEXEC="1", PYTHONUTF8="1")
            cmd = [uv, "run", "--offline", "--no-project", "--python", "3.12", "--with", "jsonschema",
                   "python", os.path.abspath(__file__)] + sys.argv[1:]
            sys.exit(subprocess.call(cmd, env=env))
    sys.stderr.write("validate.py: jsonschema is not importable and uv is not available; refusing to judge\n")
    sys.exit(2)


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def rel(path, tree):
    try:
        return os.path.relpath(path, tree).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


class Report:
    def __init__(self, quiet=False):
        self.fails = []     # (check, path, message)
        self.pendings = []  # (check, path, message)
        self.quiet = quiet
        self.ran = set()

    def fail(self, check, path, message):
        self.fails.append((check, path, message))
        if not self.quiet:
            print("FAIL    check %-2d %s: %s" % (check, path, message))

    def pending(self, check, path, message):
        self.pendings.append((check, path, message))
        if not self.quiet:
            print("PENDING check %-2d %s: %s" % (check, path, message))

    def failed_checks(self):
        return sorted({c for c, _, _ in self.fails})


class Contracts:
    """Everything the checks read from contracts/."""

    def __init__(self):
        self.schemas = {}
        for name in sorted(os.listdir(SCHEMAS)):
            if name.endswith(".schema.json"):
                s = load_json(os.path.join(SCHEMAS, name))
                self.schemas[name[:-len(".schema.json")]] = s
        self.store = {s["$id"]: s for s in self.schemas.values()}
        self.units = load_json(os.path.join(HERE, "units.json"))["units"]
        self.grades = load_json(os.path.join(HERE, "grades.json"))
        self.kinds = load_json(os.path.join(HERE, "claim_kinds.json"))
        self.records = load_json(os.path.join(HERE, "records.json"))
        self.seats = load_json(os.path.join(HERE, "seats.json"))
        self._validators = {}
        self.grade_table = {}
        for rule in self.grades["rules"]:
            for vk in rule["value_kinds"]:
                self.grade_table[(rule["source_kind"], vk)] = rule["grade"]

    def validator(self, name):
        if name not in self._validators:
            schema = self.schemas[name]
            try:
                from referencing import Registry, Resource  # jsonschema >= 4.18
                from referencing.jsonschema import DRAFT202012
                registry = Registry().with_resources(
                    [(uri, Resource.from_contents(s, default_specification=DRAFT202012))
                     for uri, s in self.store.items()])
                v = Draft202012Validator(schema, registry=registry)
            except ImportError:
                resolver = jsonschema.RefResolver(base_uri=schema["$id"], referrer=schema, store=self.store)
                v = Draft202012Validator(schema, resolver=resolver)
            self._validators[name] = v
        return self._validators[name]

    def derive_grade(self, source, value_kind):
        if not isinstance(source, str) or ":" not in source:
            return None, "source is not <kind>:<locator>"
        kind = source.split(":", 1)[0]
        known = {r["source_kind"] for r in self.grades["rules"]}
        if kind not in known:
            return None, "unregistered source kind %r" % kind
        g = self.grade_table.get((kind, value_kind))
        if g is None:
            return None, "no grade rule for (%s, %s)" % (kind, value_kind)
        return g, None


# ----------------------------------------------------------------------------
# tree scan
# ----------------------------------------------------------------------------
def scan(tree, report, include_rejected=False):
    """Return [(path, card_dict)] for every JSON with a card/artifact key, and the md files per folder."""
    cards = []
    md_by_dir = {}
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if not include_rejected and os.path.abspath(root).startswith(os.path.abspath(REJECTED)):
            dirs[:] = []
            continue
        if os.path.abspath(root) == os.path.abspath(SCHEMAS):
            continue
        for name in sorted(files):
            path = os.path.join(root, name)
            if name.endswith(".json"):
                try:
                    data = load_json(path)
                except (ValueError, UnicodeDecodeError) as e:
                    r = rel(path, tree)
                    if r.startswith("contracts/examples/") or r.startswith("meta_agent/") or tree != REPO:
                        report.fail(1, r, "malformed JSON: %s" % e)
                    continue
                if isinstance(data, dict) and (isinstance(data.get("card"), str) or isinstance(data.get("artifact"), str)):
                    cards.append((path, data))
            elif name.endswith(".md"):
                md_by_dir.setdefault(root, []).append(path)
    return cards, md_by_dir


def card_name(data):
    return data.get("card") if isinstance(data.get("card"), str) else data.get("artifact")


# ----------------------------------------------------------------------------
# check 1: schema by the card field
# ----------------------------------------------------------------------------
def check1(cards, c, report, tree):
    for path, data in cards:
        r = rel(path, tree)
        name = card_name(data)
        if name not in c.schemas:
            report.fail(1, r, "unknown card %r: no contracts/schemas/%s.schema.json" % (name, name))
            continue
        errors = sorted(c.validator(name).iter_errors(data), key=lambda e: list(e.absolute_path))
        for e in errors[:5]:
            loc = "$" + "".join("[%r]" % p if isinstance(p, int) else "." + str(p) for p in e.absolute_path)
            report.fail(1, r, "%s: %s" % (loc, e.message[:200]))
        if len(errors) > 5:
            report.fail(1, r, "... %d more schema errors" % (len(errors) - 5))


# ----------------------------------------------------------------------------
# check 2: numbers
# ----------------------------------------------------------------------------
def number_entries(data):
    """Yield (locus, entry) for numbers[] and parameter_sheet rows with a value."""
    for i, n in enumerate(data.get("numbers") or []):
        yield "numbers[%d]" % i, n
    if data.get("card") == "parameter_sheet":
        for i, row in enumerate(data.get("rows") or []):
            if isinstance(row, dict) and row.get("value") is not None:
                yield "rows[%d]" % i, row


def check2(cards, c, report, tree):
    forbidden_g = set(c.grades.get("forbidden_grades", []))
    forbidden_vk = set(c.grades.get("forbidden_value_kinds", []))
    for path, data in cards:
        r = rel(path, tree)
        for locus, n in number_entries(data):
            if not isinstance(n, dict):
                report.fail(2, r, "%s: not an object" % locus)
                continue
            missing = [k for k in ("name", "value", "unit", "source", "grade", "value_kind") if k not in n]
            if missing:
                report.fail(2, r, "%s: missing %s" % (locus, ", ".join(missing)))
                continue
            label = "%s (%s)" % (locus, n.get("name"))
            if not isinstance(n["value"], (int, float)) or isinstance(n["value"], bool):
                report.fail(2, r, "%s: value is not a number" % label)
            if n["unit"] not in c.units:
                report.fail(2, r, "%s: unit %r is not in contracts/units.json" % (label, n["unit"]))
            if n["value_kind"] in forbidden_vk:
                report.fail(2, r, "%s: value_kind %r enters no card" % (label, n["value_kind"]))
                continue
            if n["grade"] in forbidden_g:
                report.fail(2, r, "%s: grade %s enters no card" % (label, n["grade"]))
                continue
            derived, why = c.derive_grade(n["source"], n["value_kind"])
            if derived is None:
                report.fail(2, r, "%s: %s" % (label, why))
            elif derived != n["grade"]:
                report.fail(2, r, "%s: grade %s stated, %s derived from (%s, %s)" % (
                    label, n["grade"], derived, str(n["source"]).split(":", 1)[0], n["value_kind"]))
            if isinstance(n["source"], str) and n["source"].startswith("calibration:") and not n.get("expires"):
                report.fail(2, r, "%s: a calibration number needs expires" % label)


# ----------------------------------------------------------------------------
# check 3: every number in an md file exists in a card of the same folder
# ----------------------------------------------------------------------------
NUM_RE = re.compile(r"(?<![\w./:+-])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w/:%-])")
STRIP_RES = [
    re.compile(r"https?://\S+"),
    re.compile(r"^\s{0,3}#+\s+[\d.]+\s", re.M),                 # numbered headings
    re.compile(r"^\s*\d+\.\s", re.M),                           # ordered list markers
    re.compile(r"\b(?:check|checks|step|steps|group|question|rule|rules|section|rev|revision|item|k|N)\s*=?\s*\d+(?:\.\d+)*", re.I),
    re.compile(r"[§#]\s*\d+(?:\.\d+)*"),
    re.compile(r"\bv\d+(?:\.\d+)*"),
]


def json_numbers(obj, out):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            json_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            json_numbers(v, out)


def check3(cards, md_by_dir, report, tree):
    by_dir = {}
    for path, data in cards:
        by_dir.setdefault(os.path.dirname(path), []).append(data)
    for d, mds in sorted(md_by_dir.items()):
        if d not in by_dir:
            continue
        available = set()
        for data in by_dir[d]:
            json_numbers(data, available)
        for md in mds:
            text = open(md, "r", encoding="utf-8").read()
            for s in STRIP_RES:
                text = s.sub(" ", text)
            for m in NUM_RE.finditer(text):
                tok = m.group(0)
                try:
                    val = float(tok)
                except ValueError:
                    continue
                if val not in available:
                    report.fail(3, rel(md, tree), "number %s is in no card of this folder" % tok)


# ----------------------------------------------------------------------------
# check 6: commit paths inside the committer seat's boundary
# ----------------------------------------------------------------------------
def path_in(entry, path):
    if entry == "*":
        return "/" not in path
    if entry.endswith("/"):
        return path.startswith(entry)
    return path == entry


def seat_for(c, email):
    for s in c.seats["seats"]:
        if s.get("committer_email") == email:
            return s
    return None


def check6_changes(c, report, email, changes, label, report_only=False):
    seat = seat_for(c, email)
    if seat is None:
        mode = c.seats.get("unknown_committer", "report")
        msg = "committer %s is not a registered seat" % email
        if mode == "refuse" and not report_only:
            report.fail(6, label, msg)
        else:
            report.pending(6, label, msg)
        return
    for status, path in changes:
        inside = any(path_in(p, path) for p in seat.get("paths", [])) and \
            not any(path_in(x, path) for x in seat.get("excludes", []))
        if not inside:
            msg = "%s %s is outside seat %s" % (status, path, seat["seat"])
            if report_only:
                report.pending(6, label, msg + " (at or before enforced_from, reported only)")
            else:
                report.fail(6, label, msg)


# ----------------------------------------------------------------------------
# check 7: append-only records, revisions v<N>_
# ----------------------------------------------------------------------------
def rev_match(c, basename):
    m = re.match(c.records["revision_prefix_regex"], basename)
    return (int(m.group(1)), m.group(2)) if m else (None, None)


def check7_static(cards, c, report, tree):
    for path, data in cards:
        r = rel(path, tree)
        base = os.path.basename(path)
        n, rest = rev_match(c, base)
        revision = data.get("revision")
        if n is None:
            if isinstance(revision, int) and revision > 1:
                report.fail(7, r, "revision %d in a file without the v%d_ prefix" % (revision, revision))
            continue
        if revision != n:
            report.fail(7, r, "file says v%d_ and the card says revision %r" % (n, revision))
        if n < 2:
            report.fail(7, r, "v1_ is not a revision name; the first file carries no prefix")
            continue
        prev = ("v%d_%s" % (n - 1, rest)) if n > 2 else rest
        if not os.path.exists(os.path.join(os.path.dirname(path), prev)):
            report.fail(7, r, "predecessor %s is missing from the same folder" % prev)


def is_record_path(c, path):
    rec = c.records
    base = os.path.basename(path)
    if base in rec.get("mutable_names_within_roots", []):
        return False
    if any(path.startswith(d) for d in rec.get("mutable_dirs_within_roots", [])):
        return False
    return any(path.startswith(root) for root in rec["append_only_roots"])


def is_jsonl_log(c, path):
    if path in c.records.get("append_only_jsonl", []):
        return True
    return path.endswith("failures.jsonl") and path.startswith("meta_agent/requests/")


def check7_changes(c, report, changes, label, old_new):
    """changes: [(status, path)]; old_new(path) -> (old_text or None, new_text or None)."""
    for status, path in changes:
        if is_jsonl_log(c, path) and status.startswith("M"):
            old, new = old_new(path)
            if old is not None and new is not None and not new.startswith(old):
                report.fail(7, label, "%s is a log and the committed content is not a prefix of the new content" % path)
            continue
        if not is_record_path(c, path):
            continue
        if status.startswith("D"):
            report.fail(7, label, "D %s deletes a record" % path)
        elif status.startswith("M") or status.startswith("R") or status.startswith("T"):
            report.fail(7, label, "%s %s modifies a record; write v<N>_%s instead" % (status, path, os.path.basename(path)))


# ----------------------------------------------------------------------------
# git plumbing for --staged and --commit-range
# ----------------------------------------------------------------------------
def git(*args, check=True):
    p = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
    return p.stdout


def parse_name_status(text):
    changes = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        changes.append((status, path))
    return changes


def committer_email():
    ident = git("var", "GIT_COMMITTER_IDENT").strip()
    m = re.search(r"<([^>]*)>", ident)
    return m.group(1) if m else ident


def run_staged(c, report):
    email = committer_email()
    changes = parse_name_status(git("diff", "--cached", "--name-status", "-M"))
    label = "index (committer %s)" % email
    check6_changes(c, report, email, changes, label)

    def old_new(path):
        old = git("show", "HEAD:" + path, check=False)
        new = git("show", ":" + path, check=False)
        return old, new
    check7_changes(c, report, changes, label, old_new)
    return len(changes)


def run_commit_range(c, report, spec):
    out = git("log", "--format=%H%x00%ce", "--no-merges", spec)
    n = 0
    epoch = c.seats.get("enforced_from")
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, email = line.split("\x00")
        changes = parse_name_status(git("show", "--name-status", "--format=", "-M", sha))
        report_only = False
        if epoch:
            p = subprocess.run(["git", "merge-base", "--is-ancestor", sha, epoch], cwd=REPO, capture_output=True)
            report_only = (p.returncode == 0)
        label = "commit %s (committer %s)" % (sha[:7], email)
        check6_changes(c, report, email, changes, label, report_only=report_only)

        def old_new(path, sha=sha):
            return git("show", "%s^:%s" % (sha, path), check=False), git("show", "%s:%s" % (sha, path), check=False)
        check7_changes(c, report, changes, label, old_new)
        n += 1
    return n


# ----------------------------------------------------------------------------
# check 11: tool_profile claims
# ----------------------------------------------------------------------------
def permission_ok(p):
    return isinstance(p, dict) and p.get("granted_by") == "human" and all(
        isinstance(p.get(k), str) and p.get(k) for k in ("scope", "basis", "date"))


def check11(cards, c, report, tree):
    kinds = set(c.kinds["claim_kinds"])
    bases = set(c.kinds["claim_bases"])
    need_perm = set(c.kinds["claim_bases_needing_analysis_permission"])
    for path, data in cards:
        if data.get("card") != "tool_profile":
            continue
        r = rel(path, tree)
        perm = data.get("analysis_permission")
        for i, cl in enumerate(data.get("claims") or []):
            label = "claims[%d]" % i
            if not isinstance(cl, dict):
                report.fail(11, r, "%s: not an object" % label)
                continue
            kind = cl.get("kind")
            if kind not in kinds:
                report.fail(11, r, "%s: kind %r is not observed|derived|inferred|unknown" % (label, kind))
                continue
            basis = cl.get("basis")
            if basis not in bases:
                report.fail(11, r, "%s: basis %r is not one of %s" % (label, basis, sorted(bases)))
            ev = cl.get("evidence")
            ev = ev if isinstance(ev, list) else []
            bad = [j for j, e in enumerate(ev) if not (isinstance(e, dict) and e.get("locus") and (e.get("source_ref") or e.get("rea_evidence_id")))]
            if bad:
                report.fail(11, r, "%s: evidence %s lacks source_ref/rea_evidence_id or locus" % (label, bad))
            if kind in ("observed", "derived", "inferred") and not ev:
                report.fail(11, r, "%s: %s claim with no evidence" % (label, kind))
            if kind == "unknown" and not (isinstance(cl.get("requires"), str) and cl.get("requires").strip()):
                report.fail(11, r, "%s: unknown claim without requires" % label)
            from_binary = basis in need_perm or any(isinstance(e, dict) and e.get("rea_evidence_id") for e in ev)
            if from_binary and not permission_ok(perm):
                report.fail(11, r, "%s: %s-derived claim without analysis_permission {granted_by: human, scope, basis, date}" % (label, basis))


# ----------------------------------------------------------------------------
# check 15: lab_profile states
# ----------------------------------------------------------------------------
COMMON_KEYS = {"card", "schema_version", "id", "rid", "thread", "revision", "supersedes", "superseded_by", "author",
               "created_at", "numbers", "assumptions", "kb_refs", "kb_gaps", "case_refs", "case_gaps", "degraded",
               "status", "note", "lab_id", "held"}


def stated_leaves(obj, prefix=""):
    """Yield (dotted_path, leaf) for every three-state leaf under a profile field."""
    if isinstance(obj, dict):
        if "state" in obj and "value" in obj:
            yield prefix, obj
            return
        for k, v in obj.items():
            yield from stated_leaves(v, prefix + "." + k if prefix else k)


def profile_leaves(data):
    for k, v in data.items():
        if k in COMMON_KEYS:
            continue
        yield from stated_leaves(v, k)


def check_states(report, check, r, leaves, states):
    for fpath, leaf in leaves:
        st = leaf.get("state")
        if st not in states:
            report.fail(check, r, "%s: state %r is not confirmed|inferred|unknown" % (fpath, st))
            continue
        if st == "inferred" and not (isinstance(leaf.get("evidence"), list) and leaf["evidence"]):
            report.fail(check, r, "%s: inferred without evidence" % fpath)
        if st == "confirmed":
            if leaf.get("confirmed_by") != "human":
                report.fail(check, r, "%s: confirmed_by %r is not human" % (fpath, leaf.get("confirmed_by")))
            if not leaf.get("date"):
                report.fail(check, r, "%s: confirmed without a date" % fpath)


def check15(cards, c, report, tree):
    states = set(c.kinds["setting_states"])
    policy = c.kinds["policy_fields"]
    profiles = [(p, d) for p, d in cards if d.get("card") == "lab_profile"]
    referenced = {}
    for p, d in cards:
        if d.get("card") in ("agent_goal", "build") and isinstance(d.get("lab_profile_ref"), str):
            referenced.setdefault(d["lab_profile_ref"], []).append(rel(p, tree))
    # the latest revision per (folder, id) is the one a reference means
    latest = {}
    for p, d in profiles:
        key = (os.path.dirname(p), d.get("id"))
        if key not in latest or (d.get("revision") or 0) > (latest[key][1].get("revision") or 0):
            latest[key] = (p, d)
    for p, d in profiles:
        r = rel(p, tree)
        leaves = list(profile_leaves(d))
        check_states(report, 15, r, leaves, states)
        is_latest = latest.get((os.path.dirname(p), d.get("id")), (None,))[0] == p
        if is_latest and d.get("id") in referenced:
            by = {fp: leaf for fp, leaf in leaves}
            for f in policy:
                leaf = by.get(f)
                if leaf is None:
                    report.fail(15, r, "%s: policy field missing while referenced by %s" % (f, referenced[d["id"]]))
                elif leaf.get("state") != "confirmed":
                    report.fail(15, r, "%s: policy field is %s while referenced by %s" % (f, leaf.get("state"), referenced[d["id"]]))
        # transitions from the predecessor revision
        n, rest = rev_match(c, os.path.basename(p))
        if n:
            prev_name = ("v%d_%s" % (n - 1, rest)) if n > 2 else rest
            prev_path = os.path.join(os.path.dirname(p), prev_name)
            if os.path.exists(prev_path):
                try:
                    prev = load_json(prev_path)
                except ValueError:
                    prev = {}
                prev_by = dict(profile_leaves(prev)) if isinstance(prev, dict) else {}
                for fp, leaf in leaves:
                    before = prev_by.get(fp)
                    if before and before.get("state") == "inferred" and leaf.get("state") == "confirmed":
                        if leaf.get("confirmed_by") != "human":
                            report.fail(15, r, "%s: inferred -> confirmed by %r, not a person" % (fp, leaf.get("confirmed_by")))
                        if d.get("author") == before.get("confirmed_by"):
                            pass


# ----------------------------------------------------------------------------
# check 16: onboarding questions target unknown or policy fields
# ----------------------------------------------------------------------------
def check16(cards, c, report, tree):
    policy = set(c.kinds["policy_fields"])
    reports = {}
    for p, d in cards:
        if d.get("card") == "discovery_report":
            reports.setdefault(d.get("id"), []).append((p, d))
    for p, d in cards:
        if d.get("card") != "onboarding_record":
            continue
        r = rel(p, tree)
        ref_id = d.get("discovery_ref")
        cands = reports.get(ref_id, [])
        same = [x for x in cands if os.path.dirname(x[0]) == os.path.dirname(p)]
        disc = (same or cands or [(None, None)])[0][1]
        if disc is None:
            report.fail(16, r, "discovery_report %r not found; the questions cannot be judged" % ref_id)
            fields = None
        else:
            fields = disc.get("fields") or {}
        for i, q in enumerate(d.get("questions") or []):
            if not isinstance(q, dict):
                continue
            f = q.get("field")
            label = "questions[%d] (%s)" % (i, f)
            if q.get("state_at_ask") == "confirmed":
                report.fail(16, r, "%s: asked a field recorded as confirmed" % label)
            if fields is None or f in policy:
                continue
            st = (fields.get(f) or {}).get("state", "unknown") if isinstance(fields.get(f), dict) else "unknown"
            if st == "confirmed":
                report.fail(16, r, "%s: the discovery report already has it confirmed" % label)
            elif st == "inferred":
                report.pending(16, r, "%s: unnecessary question, the discovery report inferred it" % label)
        for i, s in enumerate(d.get("skipped") or []):
            if not isinstance(s, dict):
                continue
            if not (isinstance(s.get("reason"), str) and s.get("reason").strip()):
                report.fail(16, r, "skipped[%d] (%s): no reason" % (i, s.get("field")))


# ----------------------------------------------------------------------------
# check 17: material intake
# ----------------------------------------------------------------------------
SEAT_RE = re.compile(r"^[a-z]+-[a-z]+-[0-9]{8}-[0-9]+$")


def check17(cards, c, report, tree):
    states = set(c.kinds["setting_states"])
    roles = set(c.kinds["material_roles"])
    for p, d in cards:
        if d.get("card") != "material":
            continue
        r = rel(p, tree)
        loc = d.get("location") if isinstance(d.get("location"), dict) else {}
        has = [k for k in ("url", "path") if loc.get(k)]
        if len(has) != 1:
            report.fail(17, r, "location has %s; exactly one of url or path" % (has or "neither"))
        about = d.get("about") if isinstance(d.get("about"), dict) else {}
        leaves = [("about." + k, v) for k, v in about.items() if isinstance(v, dict)]
        if isinstance(d.get("license_note"), dict):
            leaves.append(("license_note", d["license_note"]))
        check_states(report, 17, r, leaves, states)
        role = about.get("role") if isinstance(about.get("role"), dict) else None
        if role and role.get("state") in ("confirmed", "inferred") and role.get("value") not in roles:
            report.fail(17, r, "about.role value %r is not one of %s" % (role.get("value"), sorted(roles)))
        if d.get("added_by") != "human":
            report.fail(17, r, "added_by %r is not human: only a person drops material" % d.get("added_by"))
        if not (isinstance(d.get("author"), str) and SEAT_RE.match(d["author"])):
            report.fail(17, r, "author %r is not the intake seat" % d.get("author"))
        snap = d.get("source_snapshot") if isinstance(d.get("source_snapshot"), dict) else {}
        if "url" in has:
            if d.get("state") == "distilled" and not (snap.get("retrieved_at") and snap.get("content_hash")):
                report.fail(17, r, "a distilled url material without source_snapshot.retrieved_at and content_hash")
            elif d.get("state") == "registered" and not (snap.get("retrieved_at") and snap.get("content_hash")):
                report.pending(17, r, "a registered url material without a snapshot")
        if snap.get("archived") and d.get("may_quote") is not True:
            report.fail(17, r, "archived copy %r while may_quote is %r" % (snap.get("archived"), d.get("may_quote")))
        if d.get("state") in ("held", "declined") and not (isinstance(d.get("state_reason"), str) and d["state_reason"].strip()):
            report.fail(17, r, "state %s without state_reason" % d.get("state"))


# ----------------------------------------------------------------------------
# drivers
# ----------------------------------------------------------------------------
def run_static(tree, c, report, checks, include_rejected=False):
    cards, md_by_dir = scan(tree, report, include_rejected=include_rejected)
    if 1 in checks:
        check1(cards, c, report, tree)
    if 2 in checks:
        check2(cards, c, report, tree)
    if 3 in checks:
        check3(cards, md_by_dir, report, tree)
    if 7 in checks:
        check7_static(cards, c, report, tree)
    if 11 in checks:
        check11(cards, c, report, tree)
    if 15 in checks:
        check15(cards, c, report, tree)
    if 16 in checks:
        check16(cards, c, report, tree)
    if 17 in checks:
        check17(cards, c, report, tree)
    report.ran.update(checks)
    card_dirs = {os.path.dirname(p) for p, _ in cards}
    return len(cards), sum(len(v) for d, v in md_by_dir.items() if d in card_dirs)


def run_scenario(path, c, report, checks):
    sc = load_json(path)
    label = rel(path, REPO)
    changes = [(ch["status"], ch["path"]) for ch in sc.get("changes", [])]
    if sc.get("check") == 6 and 6 in checks:
        check6_changes(c, report, sc.get("committer_email"), changes, label, report_only=sc.get("report_only", False))
    if sc.get("check") == 7 and 7 in checks:
        old = sc.get("old", {})
        new = sc.get("new", {})
        check7_changes(c, report, changes, label, lambda p: (old.get(p), new.get(p)))


def head_sha():
    try:
        return git("rev-parse", "--short", "HEAD").strip()
    except Exception:
        return "none"


def expect_fail(c, checks, strict, quiet):
    fixtures = sorted(d for d in os.listdir(REJECTED) if os.path.isdir(os.path.join(REJECTED, d)))
    total = len(fixtures)
    rejected = 0
    exp_total = 0
    exp_rejected = 0
    for name in fixtures:
        d = os.path.join(REJECTED, name)
        expect_path = os.path.join(d, "EXPECT")
        if not os.path.exists(expect_path):
            print("ACCEPTED %-55s no EXPECT file" % name)
            continue
        expected = sorted({int(m) for m in re.findall(r"check\s+(\d+)", open(expect_path, encoding="utf-8").read())})
        sub = Report(quiet=True)
        run_static(d, c, sub, checks, include_rejected=True)
        scenario = os.path.join(d, "scenario.json")
        if os.path.exists(scenario):
            run_scenario(scenario, c, sub, checks)
        got = sub.failed_checks()
        hit = [e for e in expected if e in got]
        exp_total += len(expected)
        exp_rejected += len(hit)
        ok = len(hit) == len(expected) and expected
        if ok:
            rejected += 1
        line = "%s %-55s expected %s got FAIL %s" % ("rejected" if ok else "ACCEPTED", name, expected, got)
        if not quiet or not ok:
            print(line)
            if not ok and not quiet:
                for ch, p, m in sub.fails:
                    print("    FAIL check %d %s: %s" % (ch, p, m))
    verdict = "PASS" if (rejected == total and exp_rejected == exp_total and total > 0) else "FAIL"
    print("expect-fail: %d of %d fixtures rejected; %d of %d expected checks rejected; checks run %s" % (
        rejected, total, exp_rejected, exp_total, sorted(checks)))
    print("VERDICT %s mode=expect-fail tree=%s head=%s fixtures=%d rejected=%d expected_checks=%d rejected_checks=%d" % (
        verdict, REJECTED.replace(os.sep, "/"), head_sha(), total, rejected, exp_total, exp_rejected))
    return 0 if verdict == "PASS" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree", nargs="?", default=REPO, help="the tree to judge (default: the repository)")
    ap.add_argument("--checks", default=None, help="comma-separated subset of the implemented checks")
    ap.add_argument("--staged", action="store_true", help="also judge the index: checks 6 and 7")
    ap.add_argument("--commit-range", default=None, help="also judge commits A..B: checks 6 and 7")
    ap.add_argument("--expect-fail", action="store_true", help="every fixture in contracts/examples/rejected/ must be refused")
    ap.add_argument("--strict", action="store_true", help="PENDING counts as failure")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    checks = set(IMPLEMENTED)
    if args.checks:
        checks = {int(x) for x in args.checks.split(",") if x.strip()}
        unknown = checks - set(IMPLEMENTED)
        if unknown:
            ap.error("checks %s are not implemented in M0 (implemented: %s)" % (sorted(unknown), IMPLEMENTED))
    c = Contracts()

    if args.expect_fail:
        return expect_fail(c, checks, args.strict, args.quiet)

    tree = os.path.abspath(args.tree)
    report = Report(quiet=args.quiet)
    n_cards, n_md = run_static(tree, c, report, checks)
    n_changes = n_commits = None
    if args.staged and (6 in checks or 7 in checks):
        n_changes = run_staged(c, report)
    if args.commit_range and (6 in checks or 7 in checks):
        n_commits = run_commit_range(c, report, args.commit_range)

    failed = len(report.fails)
    pending = len(report.pendings)
    verdict = "PASS" if failed == 0 and (pending == 0 or not args.strict) else "FAIL"
    extra = ""
    if n_changes is not None:
        extra += " staged_changes=%d" % n_changes
    if n_commits is not None:
        extra += " commits=%d" % n_commits
    print("%d cards, %d md files judged; %d failed, %d pending; checks run %s" % (
        n_cards, n_md, failed, pending, sorted(checks)))
    print("VERDICT %s tree=%s head=%s cards=%d md=%d failed=%d pending=%d failed_checks=%s%s" % (
        verdict, tree.replace(os.sep, "/"), head_sha(), n_cards, n_md, failed, pending, report.failed_checks(), extra))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
