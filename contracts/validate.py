#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/validate.py -- the deterministic validator (plan.md 8).

Usage
  python contracts/validate.py [TREE] [--checks 1,2,...] [--strict] [--quiet]
  python contracts/validate.py --staged                 # pre-commit: judges the tree the commit would make (the
                                                        # index, exported and judged by its own contracts) and
                                                        # adds checks 6, 7, 20 and 21 on the index's paths
  python contracts/validate.py --commit-range A..B      # checks 6 and 7 over commits
  python contracts/validate.py --expect-fail            # every fixture under contracts/examples/rejected/ must be refused
  python contracts/validate.py --bundle PATH            # the B checks on one built bundle

M0 implements checks 1, 2, 3, 6, 7, 11, 15, 16 and 17; M1 adds B1-B9 on bundles (plan.md 8), run on
every bundle a build card points at; tasks/003 adds 18 on wiki pages (every folder named wiki/),
and tasks/004 its graph.html.
Check numbers are fixed and never reused.
Every number printed here is read off this run. The verdict line names the judged tree.
UNDECIDED and PENDING are not passes: --strict counts PENDING as failure.

Requires jsonschema (Anaconda ships it). Without it the script re-executes itself through
`uv run --offline --no-project --with jsonschema` when uv is present, and otherwise refuses to judge.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GATE_ENV = "META_AGENT_GATE_GIT_REPO"      # set by --staged for its own re-run from the exported index
GIT_REPO = os.environ.get(GATE_ENV) or REPO  # where git is asked; differs from REPO only in that re-run
EXPORTED = bool(os.environ.get(GATE_ENV))
SCHEMAS = os.path.join(HERE, "schemas")
REJECTED = os.path.join(HERE, "examples", "rejected")
IMPLEMENTED = [1, 2, 3, 4, 5, 6, 7, 8, 11, 15, 16, 17, 18, 19, 20, 21, 22, 24]
SKIP_DIRS = {".git", ".agent", ".venv", ".pixi", "node_modules", "__pycache__"}

def judge_the_commits_tree(argv):
    """--staged: export the index git has built for the commit and run the validator from that copy.

    The person's decision of 2026-11-09 (docs/ideas/20261109.md): at commit time the gate judges the tree the
    commit would make. The cards, the schemas, the seat table and this file itself are then the commit's own,
    so what another seat has lying unfinished in the working copy neither stops nor bends the judgement; git
    is still asked in the real repository. Every check runs; CI judges each pushed tree in full.
    """
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="meta-agent-gate-")
    try:
        p = subprocess.run(["git", "checkout-index", "--all", "--prefix=" + tmp.replace(os.sep, "/") + "/"],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
        script = os.path.join(tmp, "contracts", "validate.py")
        if p.returncode != 0 or not os.path.exists(script):
            sys.stderr.write("validate.py: the index could not be exported or holds no contracts/validate.py; "
                             "refusing to judge. %s\n" % p.stderr.strip())
            return 2
        with open(script, "r", encoding="utf-8") as f:
            knows = GATE_ENV in f.read()
        if not knows:   # the commit's validator predates this rule: judge as it did, from here
            return None
        env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        env[GATE_ENV] = REPO
        return subprocess.call([sys.executable, script] + list(argv), env=env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Before anything else of this copy is loaded: at commit time the judging is handed to the commit's own copy,
# so that a tool or a schema another seat is in the middle of editing here cannot break or bend it.
if __name__ == "__main__" and "--staged" in sys.argv[1:] and not EXPORTED \
        and "--expect-fail" not in sys.argv[1:] and "--bundle" not in sys.argv[1:]:
    _rc = judge_the_commits_tree(sys.argv[1:])
    if _rc is not None:
        sys.exit(_rc)

sys.path.insert(0, os.path.join(HERE, "tools"))
import seats as seat_rules  # noqa: E402  (contracts/tools/seats.py: names, role rows, the self-registration rule)
import tasks as task_rules  # noqa: E402  (contracts/tools/tasks.py: the task index and claims)
import notes as note_rules  # noqa: E402  (contracts/tools/notes.py: notes between seats)
import cases as case_rules  # noqa: E402  (contracts/tools/cases.py: condition tags, store indexes, references)
import skills as skill_rules  # noqa: E402  (contracts/tools/skills.py: what a skill is; its source read, its cases run)
import session_skills as session_skill_rules  # noqa: E402  (contracts/tools/session_skills.py: a procedure a session loads)
import sheets as sheet_rules  # noqa: E402  (contracts/tools/sheets.py: a sheet's bounds recomputed, its safety rows)

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
            print("FAIL    check %-3s %s: %s" % (check, path, message))

    def pending(self, check, path, message):
        self.pendings.append((check, path, message))
        if not self.quiet:
            print("PENDING check %-3s %s: %s" % (check, path, message))

    def failed_checks(self):
        return sorted({c for c, _, _ in self.fails}, key=check_key)


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
        self.skill_kinds = load_json(os.path.join(HERE, "skill_kinds.json"))
        classes = load_json(os.path.join(HERE, "case_classes.json")).get("classes", {})
        self.case_classes = set(classes) if isinstance(classes, dict) else {x.get("id") for x in classes if isinstance(x, dict)}
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
            if derived is not None and data.get("card") == "parameter_sheet" and isinstance(n.get("basis"), dict) \
                    and str(n["source"]).startswith(("computed:", "correlation:")):
                # a computed number is never better than its worst input (plan.md 14-12, grades.json with_basis)
                derived = sheet_rules.computed_grade(data, n["basis"]) or derived
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
# check 4: a safety-relevant row has no value but a person's
# check 19: a sheet's bounds and computed rows are what their skills give; nothing applicable is left out
# ----------------------------------------------------------------------------
def check4(cards, c, report, tree):
    for path, data in cards:
        if data.get("card") == "parameter_sheet":
            for msg in sheet_rules.check4(data):
                report.fail(4, rel(path, tree), msg)


def check19(cards, c, report, tree):
    for path, data in cards:
        if data.get("card") == "parameter_sheet":
            for msg in sheet_rules.check19(data, path, tree):
                report.fail(19, rel(path, tree), msg)


# ----------------------------------------------------------------------------
# check 5: references resolve in the store's index; a gap names where it looked
# ----------------------------------------------------------------------------
def check5(cards, c, report, tree):
    judged = {}

    def index_problem(store):
        if store not in judged:
            judged[store] = case_rules.index_problem(store)
        return judged[store]

    for path, data in cards:
        r = rel(path, tree)
        for key, spec in sorted(case_rules.STORES.items()):
            refs = data.get(key)
            if not (isinstance(refs, list) and refs):
                continue
            store = case_rules.store_for(path, tree, spec["dir"])
            if store is None:
                report.fail(5, r, "%s cites %d item(s) and no %s/ store is at or above the card" % (key, len(refs), spec["dir"]))
                continue
            problem = index_problem(store)
            if problem:
                report.fail(5, r, "%s cannot be resolved: %s: %s" % (key, rel(store, tree), problem))
                continue
            for ref in refs:
                problem = case_rules.ref_problem(ref if isinstance(ref, dict) else {}, store, spec)
                if problem:
                    report.fail(5, r, "%s: %s" % (key, problem))
        for key in case_rules.GAPS:
            for i, gap in enumerate(data.get(key) or []):
                searched = gap.get("searched") if isinstance(gap, dict) else None
                if not (isinstance(searched, list) and any(isinstance(x, str) and x.strip() for x in searched)):
                    report.fail(5, r, "%s[%d] names nowhere it searched" % (key, i))
    # an index that exists is what its cards give, cited or not
    for path, data in cards:
        for spec in case_rules.STORES.values():
            if card_name(data) != spec["card"]:
                continue
            store = case_rules.store_for(path, tree, spec["dir"])
            if store and store not in judged and os.path.isfile(os.path.join(store, "index.json")):
                problem = index_problem(store)
                if problem:
                    report.fail(5, rel(os.path.join(store, "index.json"), tree), problem)


# ----------------------------------------------------------------------------
# check 8: cases
# ----------------------------------------------------------------------------
CAPPED_GRADES = ("E3", "E4", "E5")


def check8(cards, c, report, tree):
    for path, data in cards:
        if card_name(data) != "case":
            continue
        r = rel(path, tree)
        for key in ("falsification", "cue", "lesson"):
            if not (isinstance(data.get(key), str) and data[key].strip()):
                report.fail(8, r, "%s is empty" % key)
        if not isinstance(data.get("count"), dict):
            report.fail(8, r, "no count")
        cls = data.get("cause_class")
        if cls not in c.case_classes:
            report.fail(8, r, "cause_class %r is not in contracts/case_classes.json" % (cls,))
        sig = data.get("signature") if isinstance(data.get("signature"), dict) else {}
        if "cause_class" in sig and sig["cause_class"] != cls:
            report.fail(8, r, "signature.cause_class %r is not the card's %r" % (sig["cause_class"], cls))
        if data.get("cause_status") == "confirmed":
            kinds = {e.get("kind") for e in data.get("evidence") or [] if isinstance(e, dict)}
            if not kinds & {"run", "commit"}:
                report.fail(8, r, "cause_status confirmed without run or commit evidence")
        for tag in sig.get("condition_tags") or []:
            parsed = case_rules.parse_tag(tag)
            if parsed is None:
                report.fail(8, r, "condition tag %r is not name, name:value or name:lo..hi" % (tag,))
            elif parsed[1] == "reversed":
                report.fail(8, r, "condition tag %r: the range runs from its lower to its upper end" % (tag,))
        if isinstance(data.get("source_repo_commit"), str) and data["source_repo_commit"].strip() \
                and data.get("grade") not in CAPPED_GRADES:
            report.fail(8, r, "a case from a prior repository (source_repo_commit) is graded E3 or worse; this one says %s" % data.get("grade"))


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


def check6_changes(c, report, email, changes, label, report_only=False, old_new=None, day=None):
    # A session adding its own entry to seats.json (the person's standing rule of 2026-11-09): judged by the
    # rule, against the table as it was before the commit, and only as a commit of its own.
    touched = [st for st, path in changes if path == seat_rules.SEATS_REL and st[:1] == "M"]
    if old_new is not None and touched:
        old, new = old_new(seat_rules.SEATS_REL)
        candidate, problems = seat_rules.self_registration(old, new, email, day)
        if candidate:
            if len(changes) > 1:
                problems = problems + ["a self-registration is its own commit, before any other work; this one "
                                       "also touches %s" % ", ".join(p for _, p in changes if p != seat_rules.SEATS_REL)]
            for msg in problems:
                if report_only:
                    report.pending(6, label, "self-registration: %s (at or before enforced_from, reported only)" % msg)
                else:
                    report.fail(6, label, "self-registration: " + msg)
            return
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


def check6_table(seats, report, label):
    """Every seat is what its name says and owns exactly its role's row."""
    for msg in seat_rules.table_problems(seats):
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
    p = subprocess.run(["git"] + list(args), cwd=GIT_REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


def run_staged(c, report, checks=None):
    email = committer_email()
    changes = parse_name_status(git("diff", "--cached", "--name-status", "-M"))
    label = "index (committer %s)" % email

    def old_new(path):
        old = git("show", "HEAD:" + path, check=False)
        new = git("show", ":" + path, check=False)
        return old, new
    check6_changes(c, report, email, changes, label, old_new=old_new, day=datetime.date.today().strftime("%Y%m%d"))
    check7_changes(c, report, changes, label, old_new)
    if checks is None or 20 in checks:
        check20_changes(c, report, email, changes, label)
    if checks is None or 21 in checks:
        check21_changes(c, report, email, changes, label)
    return len(changes)


def run_commit_range(c, report, spec, checks=None):
    out = git("log", "--format=%H%x00%ce%x00%cs", "--no-merges", spec)
    n = 0
    epoch = c.seats.get("enforced_from")
    rule_epoch = c.seats.get("self_registration_from")
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, email, day = line.split("\x00")
        changes = parse_name_status(git("show", "--name-status", "--format=", "-M", sha))
        report_only = False
        if epoch:
            p = subprocess.run(["git", "merge-base", "--is-ancestor", sha, epoch], cwd=GIT_REPO, capture_output=True)
            report_only = (p.returncode == 0)
        label = "commit %s (committer %s)" % (sha[:7], email)

        def old_new(path, sha=sha):
            return git("show", "%s^:%s" % (sha, path), check=False), git("show", "%s:%s" % (sha, path), check=False)
        before_rule = False
        if rule_epoch:
            p = subprocess.run(["git", "merge-base", "--is-ancestor", sha, rule_epoch], cwd=GIT_REPO, capture_output=True)
            before_rule = (p.returncode == 0)
        check6_changes(c, report, email, changes, label, report_only=report_only,
                       old_new=None if before_rule else old_new, day=day.replace("-", ""))
        check7_changes(c, report, changes, label, old_new)
        if checks is None or 20 in checks:
            check20_changes(c, report, email, changes, label)
        if checks is None or 21 in checks:
            check21_changes(c, report, email, changes, label)
        n += 1
    return n


# ----------------------------------------------------------------------------
# check 20: the task queue (meta_agent/tasks/index.json and claims/)
# ----------------------------------------------------------------------------
def check20(tree, c, report):
    exists = None
    if tree == REPO:
        def exists(sha):
            return subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"], cwd=GIT_REPO, capture_output=True).returncode == 0
    for path, msg in task_rules.problems(tree, c.seats, commit_exists=exists):
        report.fail(20, path, msg)


def check20_changes(c, report, email, changes, label):
    for status, path in changes:
        msg = task_rules.claim_committer_problem(path, status, email)
        if msg:
            report.fail(20, label, msg)


# ----------------------------------------------------------------------------
# check 21: notes between seats (meta_agent/inbox/seats/)
# ----------------------------------------------------------------------------
def check21(tree, c, report):
    fails, pending = note_rules.judge(tree, c.seats)
    for path, msg in fails:
        report.fail(21, path, msg)
    for path, msg in pending:
        report.pending(21, path, "an ask with no reply, " + msg)


def check21_changes(c, report, email, changes, label):
    for status, path in changes:
        msg = note_rules.note_committer_problem(path, status, email)
        if msg:
            report.fail(21, label, msg)


# ----------------------------------------------------------------------------
# check 22: skills (a folder <id>@v<n>/ under skills/: manifest, source read, worked cases run)
# ----------------------------------------------------------------------------
def check22(tree, c, report, include_rejected=False):
    for d in skill_rules.find_skill_dirs(tree, skip=[] if include_rejected else [REJECTED]):
        manifest = skill_rules.read_manifest(d)
        errors = []
        if manifest is not None:
            for e in sorted(c.validator("skill").iter_errors(manifest), key=lambda e: list(e.absolute_path))[:5]:
                loc = "$" + "".join("[%r]" % p if isinstance(p, int) else "." + str(p) for p in e.absolute_path)
                errors.append("%s: %s" % (loc, e.message[:200]))
        for msg in skill_rules.problems(d, c.skill_kinds, errors):
            report.fail(22, rel(d, tree), msg)


# ----------------------------------------------------------------------------
# check 24: session skills (a folder .claude/skills/<name>/ with a SKILL.md a session loads; tasks/015)
# ----------------------------------------------------------------------------
def check24(tree, c, report, include_rejected=False):
    for d, msg in session_skill_rules.judge(tree, skip=[] if include_rejected else [REJECTED]):
        report.fail(24, rel(d, tree), msg)


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
        labelled = [("claims[%d]" % i, cl) for i, cl in enumerate(data.get("claims") or [])]
        for i, sc in enumerate(data.get("self_calibration") or []):
            cl = sc.get("claim") if isinstance(sc, dict) else None
            labelled.append(("self_calibration[%d].claim" % i, cl))
            if isinstance(sc, dict) and isinstance(cl, dict) and sc.get("mode") in ("self", "assisted") and cl.get("kind") == "unknown":
                report.fail(11, r, "self_calibration[%d]: mode %s rests on an unknown claim; whether a device calibrates %s itself "
                            "is checked, not assumed (mode unknown until it is)" % (i, sc.get("mode"), sc.get("quantity")))
        for label, cl in labelled:
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
# ----------------------------------------------------------------------------
# B checks: one built bundle (plan.md 5.1 S5, 8). Run with --bundle PATH, on every
# bundle a build card points at, and on <fixture>/bundle/ under --expect-fail.
# ----------------------------------------------------------------------------
B_IMPLEMENTED = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B11"]
BUNDLE_FILES = ["CLAUDE.md", ".claude/settings.json", "CAPABILITIES.json", "envelope/safety.json",
                "envelope/snapshot.json", "envelope/parameters.json", "failures.jsonl",
                "src/gate.py", "src/run_tool.py", "src/replay.py", "src/validate_tasks.py"]
BUNDLE_DIRS = ["tools", "validation/interface", "validation/scientific", "replay", "tasks"]
SHELL_RE = re.compile(r"^(Bash|PowerShell)\((.*)\)$")
SCRIPT_RE = re.compile(r"\bsrc/[A-Za-z0-9_./-]+\.py\b")
VERDICTS = ("pass", "fail", "not_run", "undecided")


def check_key(ch):
    """Sort key over mixed check ids: numeric checks first, then B1, B2, ..."""
    if isinstance(ch, str):
        return (1, int(ch[1:]) if ch[1:].isdigit() else 0, ch)
    return (0, ch, "")


def parse_check(tok):
    tok = tok.strip()
    if tok.upper().startswith("B"):
        return "B" + tok[1:]
    return int(tok)


def bundle_json(bundle, relpath, report, check):
    """Load one JSON file of the bundle; a missing or malformed file is that check's failure (None)."""
    path = os.path.join(bundle, *relpath.split("/"))
    if not os.path.exists(path):
        return None
    try:
        return load_json(path)
    except (ValueError, UnicodeDecodeError) as e:
        report.fail(check, relpath, "malformed JSON: %s" % e)
        return None


def bundle_items(bundle, sub):
    """(relpath, item) for every JSON item under a validation or replay folder."""
    d = os.path.join(bundle, *sub.split("/"))
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            try:
                out.append((sub + "/" + fn, load_json(os.path.join(d, fn))))
            except (ValueError, UnicodeDecodeError):
                out.append((sub + "/" + fn, None))
    return out


def tool_dirs(bundle):
    d = os.path.join(bundle, "tools")
    if not os.path.isdir(d):
        return []
    return sorted(n for n in os.listdir(d) if os.path.isdir(os.path.join(d, n)))


def checkB1(bundle, label, report):
    for f in BUNDLE_FILES:
        if not os.path.isfile(os.path.join(bundle, *f.split("/"))):
            report.fail("B1", label, "required file %s is missing" % f)
    for d in BUNDLE_DIRS:
        if not os.path.isdir(os.path.join(bundle, *d.split("/"))):
            report.fail("B1", label, "required directory %s/ is missing" % d)
    tasks = os.path.join(bundle, "tasks")
    if os.path.isdir(tasks) and not any(n.endswith(".md") for n in os.listdir(tasks)):
        report.fail("B1", label, "tasks/ holds no task")
    claude = os.path.join(bundle, "CLAUDE.md")
    if os.path.isfile(claude) and "{{" in open(claude, encoding="utf-8").read():
        report.fail("B1", label, "CLAUDE.md still carries a template placeholder")


def checkB2(bundle, label, report):
    settings = bundle_json(bundle, ".claude/settings.json", report, "B2")
    if settings is None:
        return
    perms = settings.get("permissions") or {}
    for kind in ("deny", "ask"):
        rules = perms.get(kind) or []
        if not isinstance(rules, list):
            report.fail("B2", label, "permissions.%s is not a list" % kind)
            continue
        have = set(r for r in rules if isinstance(r, str))
        for r in sorted(have):
            m = SHELL_RE.match(r)
            if not m:
                continue
            shell, body = m.groups()
            twin = "%s(%s)" % ("PowerShell" if shell == "Bash" else "Bash", body)
            if twin not in have:
                report.fail("B2", label, "permissions.%s: %s has no %s twin" % (kind, r, twin))


def checkB3(bundle, label, report):
    safety = bundle_json(bundle, "envelope/safety.json", report, "B3")
    if safety is None:
        return
    if not isinstance(safety, dict):
        report.fail("B3", label, "envelope/safety.json is not an object")
        return
    for k, v in safety.items():
        if v is not None:
            report.fail("B3", label, "envelope/safety.json: %s is %r, not null" % (k, v))


def checkB4(bundle, label, report, knowledge_root):
    snap = bundle_json(bundle, "envelope/snapshot.json", report, "B4")
    if snap is None:
        return
    kb = snap.get("kb_version")
    if not (isinstance(kb, str) and kb.strip()):
        report.fail("B4", label, "envelope/snapshot.json: kb_version is not pinned")
    entries = snap.get("entries")
    if not isinstance(entries, list):
        report.fail("B4", label, "envelope/snapshot.json: entries is not a list")
        return
    for i, e in enumerate(entries):
        if not (isinstance(e, dict) and isinstance(e.get("id"), str)):
            report.fail("B4", label, "snapshot entries[%d] has no id" % i)
            continue
        h = e.get("hash")
        if not (isinstance(h, str) and re.match(r"^sha256:[0-9a-f]{64}$", h)):
            report.fail("B4", label, "snapshot entry %s has no sha256 hash" % e["id"])
            continue
        candidates = []
        if isinstance(e.get("path"), str):
            candidates.append(os.path.join(REPO, *e["path"].split("/")))
        if knowledge_root:
            candidates.append(os.path.join(knowledge_root, "entries", e["id"] + ".json"))
        found = [p for p in candidates if os.path.isfile(p)]
        if not found:
            report.fail("B4", label, "snapshot entry %s: no file under knowledge/entries/ (looked at %s)" % (
                e["id"], [c.replace(os.sep, "/") for c in candidates] or "nothing: no knowledge root"))
            continue
        actual = "sha256:" + sha256_of(found[0])
        if actual != h:
            report.fail("B4", label, "snapshot entry %s: hash %s does not match %s (%s)" % (
                e["id"], h[:19] + "...", rel(found[0], REPO), actual[:19] + "..."))


def sha256_of(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def checkB5(bundle, label, report):
    tools = set(tool_dirs(bundle))
    for sub in ("replay", "validation/interface", "validation/scientific"):
        if not os.path.isdir(os.path.join(bundle, *sub.split("/"))):
            continue  # B1 reports the missing directory
        items = bundle_items(bundle, sub)
        good = 0
        for relpath, item in items:
            if item is None:
                report.fail("B5", relpath, "malformed JSON")
                continue
            ev = item.get("expected_verdict")
            if ev not in VERDICTS:
                report.fail("B5", relpath, "expected_verdict %r is not one of %s" % (ev, "|".join(VERDICTS)))
                continue
            call = item.get("call") or {}
            if not isinstance(call, dict) or not isinstance(call.get("tool"), str):
                report.fail("B5", relpath, "item names no call.tool")
                continue
            if call["tool"] not in tools:
                report.fail("B5", relpath, "call.tool %r is not a tool of this bundle" % call["tool"])
                continue
            good += 1
        if good == 0:
            report.fail("B5", label, "%s/ has no task with an expected verdict" % sub)


def checkB6(bundle, label, report):
    claude = os.path.join(bundle, "CLAUDE.md")
    snap = bundle_json(bundle, "envelope/snapshot.json", report, "B6")
    if not os.path.isfile(claude) or snap is None:
        return
    available = set()
    json_numbers(snap, available)
    text = open(claude, encoding="utf-8").read()
    for s in STRIP_RES:
        text = s.sub(" ", text)
    for m in NUM_RE.finditer(text):
        try:
            val = float(m.group(0))
        except ValueError:
            continue
        if val not in available:
            report.fail("B6", label, "CLAUDE.md: number %s is not in envelope/snapshot.json" % m.group(0))


def run_fixture_call(bundle, tool, payload):
    """Call the bundle's runner the way the agent would, in a fresh isolated interpreter."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run([sys.executable, "-I", os.path.join("src", "run_tool.py"), tool], cwd=bundle, input=json.dumps(payload),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, "the runner did not finish: %s" % e
    try:
        return json.loads(p.stdout), None
    except ValueError:
        return None, "the runner printed no JSON (exit %s): %s" % (p.returncode, (p.stderr or p.stdout).strip()[-300:])


def checkB7(bundle, label, report, c):
    contracts = {}
    for name in tool_dirs(bundle):
        relpath = "tools/%s/tool.json" % name
        tc = bundle_json(bundle, relpath, report, "B7")
        if tc is None:
            report.fail("B7", relpath, "missing or malformed tool contract")
            continue
        errors = sorted(c.validator("tool_contract").iter_errors(tc), key=lambda e: list(e.absolute_path))
        for e in errors[:5]:
            loc = "$" + "".join("[%r]" % p if isinstance(p, int) else "." + str(p) for p in e.absolute_path)
            report.fail("B7", relpath, "%s: %s" % (loc, e.message[:200]))
        if tc.get("name") != name:
            report.fail("B7", relpath, "name %r differs from the folder tools/%s/" % (tc.get("name"), name))
        if not os.path.isfile(os.path.join(bundle, "tools", name, "adapter.py")):
            report.fail("B7", relpath, "tools/%s/adapter.py is missing" % name)
        contracts[name] = tc
        errs_dir = os.path.join(bundle, "tools", name, "errors")
        if os.path.isdir(errs_dir):
            for fn in sorted(os.listdir(errs_dir)):
                if not fn.endswith(".json"):
                    continue
                er = "tools/%s/errors/%s" % (name, fn)
                ec = bundle_json(bundle, er, report, "B7")
                if ec is None:
                    continue
                for e in sorted(c.validator("error_contract").iter_errors(ec), key=lambda e: list(e.absolute_path))[:3]:
                    report.fail("B7", er, "error contract: %s" % e.message[:200])
                if ec.get("category") not in (tc.get("errors") or []):
                    report.fail("B7", er, "category %r is not in the tool's errors %s" % (ec.get("category"), tc.get("errors")))
    # fixture calls: every item that expects an error must get a well-formed error contract of that category
    for sub in ("replay", "validation/interface"):
        for relpath, item in bundle_items(bundle, sub):
            if not isinstance(item, dict):
                continue
            want = (item.get("expected") or {}).get("error")
            call = item.get("call") or {}
            if not isinstance(want, dict) or call.get("tool") not in contracts:
                continue
            out, err = run_fixture_call(bundle, call["tool"], call.get("input"))
            if err:
                report.fail("B7", relpath, err)
                continue
            if not (isinstance(out, dict) and out.get("artifact") == "error_contract"):
                report.fail("B7", relpath, "expected an error contract, the runner returned %s" % type(out).__name__)
                continue
            schema_errors = list(c.validator("error_contract").iter_errors(out))
            for e in sorted(schema_errors, key=lambda e: list(e.absolute_path))[:3]:
                report.fail("B7", relpath, "the returned error does not honour the error contract: %s" % e.message[:200])
            if want.get("category") and out.get("category") != want["category"]:
                report.fail("B7", relpath, "expected category %s, the runner returned %s" % (want["category"], out.get("category")))
            if want.get("code") and out.get("code") != want["code"]:
                report.fail("B7", relpath, "expected code %s, the runner returned %s" % (want["code"], out.get("code")))
            if out.get("category") not in (contracts[call["tool"]].get("errors") or []):
                report.fail("B7", relpath, "returned category %r is not in the tool's errors" % out.get("category"))


def checkB8(bundle, label, report):
    claude_path = os.path.join(bundle, "CLAUDE.md")
    claude = open(claude_path, encoding="utf-8").read() if os.path.isfile(claude_path) else ""
    skills = os.path.join(bundle, "skills")
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            sdir = os.path.join(skills, name)
            if not os.path.isdir(sdir):
                continue
            skill_md = os.path.join(sdir, "SKILL.md")
            if not os.path.isfile(skill_md):
                report.fail("B8", "skills/%s" % name, "no SKILL.md")
                continue
            if "`%s`" % name not in claude:
                report.fail("B8", "skills/%s" % name, "no trigger sentence names `%s` in CLAUDE.md" % name)
            for script in sorted(set(SCRIPT_RE.findall(open(skill_md, encoding="utf-8").read()))):
                if not os.path.isfile(os.path.join(bundle, *script.split("/"))):
                    report.fail("B8", "skills/%s/SKILL.md" % name, "named script %s does not exist" % script)
    for script in sorted(set(SCRIPT_RE.findall(claude))):
        if not os.path.isfile(os.path.join(bundle, *script.split("/"))):
            report.fail("B8", "CLAUDE.md", "named script %s does not exist" % script)
    settings = bundle_json(bundle, ".claude/settings.json", report, "B8")
    if isinstance(settings, dict):
        for event, groups in (settings.get("hooks") or {}).items():
            for g in groups if isinstance(groups, list) else []:
                for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                    for script in sorted(set(SCRIPT_RE.findall(str(h.get("command", ""))))):
                        if not os.path.isfile(os.path.join(bundle, *script.split("/"))):
                            report.fail("B8", ".claude/settings.json", "hook %s names script %s, which does not exist" % (event, script))
    cap = bundle_json(bundle, "CAPABILITIES.json", report, "B8")
    if isinstance(cap, dict):
        if "inferred" in cap:
            report.fail("B8", "CAPABILITIES.json", "carries an inferred[] list; inferred claims go to unverified[]")
        for key in ("observed", "derived"):
            for i, item in enumerate(cap.get(key) or []):
                if isinstance(item, dict) and item.get("kind") not in (None, key):
                    report.fail("B8", "CAPABILITIES.json", "%s[%d] has kind %r" % (key, i, item.get("kind")))
        for key in ("observed", "derived", "unverified", "gaps"):
            for i, item in enumerate(cap.get(key) or []):
                if isinstance(item, dict) and item.get("kind") == "inferred":
                    report.fail("B8", "CAPABILITIES.json", "%s[%d] is an inferred claim" % (key, i))


def checkB9(bundle, label, report):
    runner = os.path.join(bundle, "src", "run_tool.py")
    runner_text = open(runner, encoding="utf-8").read() if os.path.isfile(runner) else ""
    for name in tool_dirs(bundle):
        relpath = "tools/%s/tool.json" % name
        tc = bundle_json(bundle, relpath, report, "B9")
        if not isinstance(tc, dict):
            continue
        gate = tc.get("safety_gate") if isinstance(tc.get("safety_gate"), dict) else {}
        relevant = tc.get("side_effects") not in (None, "none", "reads_instrument") or bool(gate.get("required"))
        if not relevant:
            continue
        if not gate.get("required"):
            report.fail("B9", relpath, "side effects %r without safety_gate.required true" % tc.get("side_effects"))
            continue
        place = gate.get("place")
        if not (isinstance(place, str) and place.strip()):
            report.fail("B9", relpath, "safety_gate.place does not name where the deterministic gate runs")
            continue
        scripts = SCRIPT_RE.findall(place)
        if not scripts:
            report.fail("B9", relpath, "safety_gate.place %r names no src/ script" % place)
        for script in scripts:
            if not os.path.isfile(os.path.join(bundle, *script.split("/"))):
                report.fail("B9", relpath, "safety_gate.place names %s, which does not exist" % script)
        if "check_before" not in runner_text:
            report.fail("B9", "src/run_tool.py", "the runner does not consult the gate (no check_before) while %s needs one" % name)


SKILL_TOKEN_RE = re.compile(r"`([a-z][a-z0-9_]*@v[1-9][0-9]*)`")


def checkB11(bundle, label, report):
    """Skills and subagents of a bundle: what is named exists, a subagent's side effects cover its skills,
    one subagent alone may change a device, and a skill reaches a device through tools the bundle has, the
    writing ones behind the gate."""
    skills = {}
    sdir = os.path.join(bundle, "skills")
    if os.path.isdir(sdir):
        for d in skill_rules.find_skill_dirs(sdir):
            m = skill_rules.read_manifest(d)
            if isinstance(m, dict):
                skills[os.path.basename(d)] = m
    tools = set(tool_dirs(bundle))
    for ref, m in sorted(skills.items()):
        for t in m.get("calls_tools") or []:
            if t not in tools:
                report.fail("B11", "skills/%s" % ref, "calls the tool %s and the bundle has no tools/%s/" % (t, t))
                continue
            tc = bundle_json(bundle, "tools/%s/tool.json" % t, report, "B11")
            effect = tc.get("side_effects") if isinstance(tc, dict) else None
            if m.get("side_effect") == "read_device" and effect not in (None, "none", "reads_instrument"):
                report.fail("B11", "skills/%s" % ref, "says it only reads the device and calls %s, a tool with side effects %s" % (t, effect))
            if m.get("side_effect") == "write_device":
                gate = tc.get("safety_gate") if isinstance(tc, dict) and isinstance(tc.get("safety_gate"), dict) else {}
                if not gate.get("required"):
                    report.fail("B11", "skills/%s" % ref, "changes the device through %s, whose contract asks for no gate" % t)
    writers = []
    adir = os.path.join(bundle, ".claude", "agents")
    texts = {"CLAUDE.md": open(os.path.join(bundle, "CLAUDE.md"), encoding="utf-8").read()
             if os.path.isfile(os.path.join(bundle, "CLAUDE.md")) else ""}
    for name in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        if not name.endswith(".md"):
            continue
        relpath = ".claude/agents/%s" % name
        text = open(os.path.join(adir, name), encoding="utf-8").read()
        texts[relpath] = text
        fm = skill_rules.front_matter(text)
        if fm.get("name") != name[:-3]:
            report.fail("B11", relpath, "front matter name %r is not the file's" % (fm.get("name"),))
        effects = skill_rules.front_list(text, "side_effects")
        unknown = [e for e in effects if e not in ("none", "read_device", "write_device")]
        if unknown:
            report.fail("B11", relpath, "side_effects %s are not none, read_device or write_device" % unknown)
        if "write_device" in effects:
            writers.append(name[:-3])
        for ref in skill_rules.front_list(text, "skills"):
            m = skills.get(ref)
            if m is None:
                report.fail("B11", relpath, "names the skill %s, which the bundle does not carry" % ref)
            elif m.get("side_effect") != "none" and m.get("side_effect") not in effects:
                report.fail("B11", relpath, "names %s, which is %s, and its side_effects are %s" % (ref, m.get("side_effect"), effects or "none"))
    if len(writers) > 1:
        report.fail("B11", ".claude/agents", "%s all list write_device; one subagent alone may change a device" % ", ".join(writers))
    for relpath, text in sorted(texts.items()):
        for ref in sorted(set(SKILL_TOKEN_RE.findall(text))):
            if ref not in skills:
                report.fail("B11", relpath, "names the skill `%s`, which the bundle does not carry" % ref)


def run_bundle_checks(bundle, c, report, checks, knowledge_root, label=None):
    bundle = os.path.abspath(bundle)
    label = label or rel(bundle, REPO)
    if not os.path.isdir(bundle):
        report.fail("B1", label, "bundle directory does not exist")
        report.ran.update(ch for ch in checks if isinstance(ch, str))
        return
    if "B1" in checks:
        checkB1(bundle, label, report)
    if "B2" in checks:
        checkB2(bundle, label, report)
    if "B3" in checks:
        checkB3(bundle, label, report)
    if "B4" in checks:
        checkB4(bundle, label, report, knowledge_root)
    if "B5" in checks:
        checkB5(bundle, label, report)
    if "B6" in checks:
        checkB6(bundle, label, report)
    if "B7" in checks:
        checkB7(bundle, label, report, c)
    if "B8" in checks:
        checkB8(bundle, label, report)
    if "B9" in checks:
        checkB9(bundle, label, report)
    if "B11" in checks:
        checkB11(bundle, label, report)
    report.ran.update(ch for ch in checks if isinstance(ch, str))


def knowledge_root_for(tree):
    for base in (tree, REPO):
        k = os.path.join(base, "meta_agent", "knowledge")
        if os.path.isdir(k):
            return k
    return None


def bundles_of(cards, tree):
    """The bundles the tree's build cards point at: (label, path) per build card outside
    contracts/examples/, resolved against the judged tree first and the repository second."""
    out = []
    for path, data in cards:
        if data.get("card") != "build" or not isinstance(data.get("bundle_path"), str):
            continue
        if rel(path, tree).startswith("contracts/examples/"):
            continue  # a shape example of the card, not a build; the B fixtures live under rejected/
        bp = data["bundle_path"]
        candidates = [os.path.join(tree, *bp.split("/")), os.path.join(REPO, *bp.split("/"))]
        found = next((p for p in candidates if os.path.isdir(p)), candidates[0])
        out.append((rel(path, tree) + " -> " + bp, found))
    return out


# ----------------------------------------------------------------------------
# check 18: a wiki page renders one record and adds nothing to it (tasks/003)
# ----------------------------------------------------------------------------
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
WIKI_RECORD_RE = re.compile(r"^- record: `([^`]+)`[ \t]*$", re.M)
WIKI_H1_RE = re.compile(r"^#[ \t]+(.+?)[ \t]*$", re.M)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")


def json_strings(obj, out):
    if isinstance(obj, str):
        out.add(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            json_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            json_strings(v, out)


def wiki_record(page_path, tree):
    """(text, record path relative to the tree, record, error) for one page; a directory record is an artifact."""
    text = open(page_path, encoding="utf-8").read()
    m = WIKI_RECORD_RE.search(text)
    if not m:
        return text, None, None, "names no record line (- record: `<path>`)"
    relp = m.group(1).strip()
    full = os.path.abspath(os.path.join(tree, relp))
    if not full.startswith(os.path.abspath(tree)):
        return text, relp, None, "record %s lies outside the judged tree" % relp
    if os.path.isdir(full):
        return text, relp, {"_artifact": relp}, None
    if not os.path.isfile(full):
        return text, relp, None, "record %s does not exist" % relp
    try:
        data = load_json(full)
    except (ValueError, UnicodeDecodeError):
        return text, relp, None, "record %s is not JSON" % relp
    if not (isinstance(data, dict) and isinstance(data.get("card"), str) and data.get("id")):
        return text, relp, None, "record %s is not a card" % relp
    return text, relp, data, None


def wiki_node(data):
    return "%s@r%d" % (data["id"], data.get("revision", 1))


def wiki_related(a_rel, a, b_rel, b):
    """True when one record names the other (its id, path or file name), or both are revisions of one id."""
    def names(rel_path, d):
        out = {rel_path, os.path.basename(rel_path.rstrip("/"))}
        if "_artifact" not in d:
            out.add(d["id"])
        return out

    def values(d):
        out = set()
        if "_artifact" not in d:
            json_strings(d, out)
        return out
    if "_artifact" not in a and "_artifact" not in b and a["id"] == b["id"]:
        return True
    return bool(names(b_rel, b) & values(a)) or bool(names(a_rel, a) & values(b))


WIKI_GRAPH_RE = re.compile(r'<script id="wiki-graph" type="application/json">(.*?)</script>', re.S)
EXTERNAL_RE = re.compile(r"""\b(?:src|href)\s*=\s*["']?\s*(?:[a-z][a-z0-9+.-]*:)?//""", re.I)


def check18_graph(path, pages, info, report, tree):
    """graph.html (tasks/004): nothing from another host; nodes are pages with their records' card and status;
    every edge is a link one of its two pages holds."""
    label = rel(path, tree)
    text = open(path, encoding="utf-8").read()
    if EXTERNAL_RE.search(text):
        report.fail(18, label, "loads a resource from another host")
    m = WIKI_GRAPH_RE.search(text)
    if not m:
        report.fail(18, label, "carries no wiki-graph data block")
        return
    try:
        data = json.loads(m.group(1))
        nodes, edges = list(data["nodes"]), list(data["edges"])
    except (ValueError, KeyError, TypeError):
        report.fail(18, label, "the wiki-graph data block is not {nodes, edges}")
        return
    for n in nodes:
        nid = n.get("id") if isinstance(n, dict) else None
        if nid not in pages or nid == "index":
            report.fail(18, label, "node %s has no page in this wiki" % nid)
            continue
        rec = info[nid][2]
        if rec is None:
            continue
        if "_artifact" in rec:
            if n.get("status") != "artifact":
                report.fail(18, label, "node %s is an artifact and says status %s" % (nid, n.get("status")))
        elif (n.get("card"), n.get("status")) != (rec.get("card"), rec.get("status")):
            report.fail(18, label, "node %s says %s/%s; its record says %s/%s" % (
                nid, n.get("card"), n.get("status"), rec.get("card"), rec.get("status")))
    for e in edges:
        if not (isinstance(e, list) and len(e) == 3):
            report.fail(18, label, "edge %s is not [source, relation, target]" % (e,))
            continue
        src, relation, tgt = e
        if src not in pages or tgt not in pages:
            report.fail(18, label, "edge %s %s %s names a node with no page" % (src, relation, tgt))
            continue
        if "[[%s]]" % tgt not in info[src][0] and "[[%s]]" % src not in info[tgt][0]:
            report.fail(18, label, "edge %s %s %s is on neither page" % (src, relation, tgt))


def check18(md_by_dir, report, tree):
    for d in sorted(md_by_dir):
        if os.path.basename(d) != "wiki":
            continue
        pages = {os.path.splitext(os.path.basename(p))[0]: p for p in md_by_dir[d]}
        report.wiki_pages = getattr(report, "wiki_pages", 0) + len(pages)
        info = {}
        for stem, p in sorted(pages.items()):
            label = rel(p, tree)
            if stem == "index":
                info[stem] = (open(p, encoding="utf-8").read(), None, None)
                continue
            text, relp, data, err = wiki_record(p, tree)
            if err:
                report.fail(18, label, err)
                info[stem] = (text, None, None)
                continue
            if "_artifact" not in data:
                want = wiki_node(data)
                h1 = WIKI_H1_RE.search(text)
                if not h1 or h1.group(1) != want:
                    report.fail(18, label, "the title is not %s, the record's id and revision" % want)
                if stem != want:
                    report.fail(18, label, "the file is not named %s.md" % want)
            info[stem] = (text, relp, data)
        for stem, (text, relp, data) in sorted(info.items()):
            label = rel(pages[stem], tree)
            for m in WIKI_LINK_RE.finditer(text):
                target = m.group(1).strip()
                if target not in pages:
                    report.fail(18, label, "[[%s]] names no page of this wiki" % target)
                    continue
                t_text, t_rel, t_data = info[target]
                if data is None or t_data is None:
                    continue
                if not wiki_related(relp, data, t_rel, t_data):
                    report.fail(18, label, "[[%s]] is a relation neither record holds" % target)
            body = WIKI_H1_RE.sub(" ", text, count=1)
            body = WIKI_RECORD_RE.sub(" ", body)
            body = CODE_SPAN_RE.sub(" ", body)
            body = WIKI_LINK_RE.sub(" ", body)
            for s in STRIP_RES:
                body = s.sub(" ", body)
            available = set()
            if data is not None and "_artifact" not in data:
                json_numbers(data, available)
            for n in NUM_RE.finditer(body):
                try:
                    val = float(n.group(0))
                except ValueError:
                    continue
                if val not in available:
                    report.fail(18, label, "number %s is in no field of the record this page renders" % n.group(0))
        graph = os.path.join(d, "graph.html")
        if os.path.isfile(graph):
            check18_graph(graph, pages, info, report, tree)


def run_static(tree, c, report, checks, include_rejected=False):
    cards, md_by_dir = scan(tree, report, include_rejected=include_rejected)
    if 1 in checks:
        check1(cards, c, report, tree)
    if 2 in checks:
        check2(cards, c, report, tree)
    if 3 in checks:
        check3(cards, md_by_dir, report, tree)
    if 4 in checks:
        check4(cards, c, report, tree)
    if 5 in checks:
        check5(cards, c, report, tree)
    if 19 in checks:
        check19(cards, c, report, tree)
    if 8 in checks:
        check8(cards, c, report, tree)
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
    if 18 in checks:
        check18(md_by_dir, report, tree)
    if 20 in checks:
        check20(tree, c, report)
    if 21 in checks:
        check21(tree, c, report)
    if 22 in checks:
        check22(tree, c, report, include_rejected)
    if 24 in checks:
        check24(tree, c, report, include_rejected)
    report.ran.update(ch for ch in checks if isinstance(ch, int))
    card_dirs = {os.path.dirname(p) for p, _ in cards}
    return len(cards), sum(len(v) for d, v in md_by_dir.items() if d in card_dirs), cards


def run_scenario(path, c, report, checks):
    sc = load_json(path)
    label = rel(path, REPO)
    changes = [(ch["status"], ch["path"]) for ch in sc.get("changes", [])]
    if sc.get("check") == 6 and 6 in checks and isinstance(sc.get("seats"), dict):
        check6_table(sc["seats"], report, label)
    if sc.get("check") == 6 and 6 in checks and (changes or "seats" not in sc):
        texts = None
        if "old" in sc or "new" in sc:
            def texts(p):
                return sc.get("old", {}).get(p), sc.get("new", {}).get(p)
        check6_changes(c, report, sc.get("committer_email"), changes, label, report_only=sc.get("report_only", False),
                       old_new=texts, day=sc.get("day"))
    if sc.get("check") == 20 and 20 in checks:
        check20_changes(c, report, sc.get("committer_email"), changes, label)
    if sc.get("check") == 21 and 21 in checks:
        check21_changes(c, report, sc.get("committer_email"), changes, label)
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
        expected = sorted({parse_check(m) for m in re.findall(r"check\s+(B?\d+)", open(expect_path, encoding="utf-8").read())}, key=check_key)
        sub = Report(quiet=True)
        run_static(d, c, sub, checks, include_rejected=True)
        fixture_bundle = os.path.join(d, "bundle")
        if os.path.isdir(fixture_bundle):
            kroot = os.path.join(d, "knowledge")
            run_bundle_checks(fixture_bundle, c, sub, checks, kroot if os.path.isdir(kroot) else None, label=name + "/bundle")
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
                    print("    FAIL check %s %s: %s" % (ch, p, m))
    verdict = "PASS" if (rejected == total and exp_rejected == exp_total and total > 0) else "FAIL"
    print("expect-fail: %d of %d fixtures rejected; %d of %d expected checks rejected; checks run %s" % (
        rejected, total, exp_rejected, exp_total, sorted(checks, key=check_key)))
    print("VERDICT %s mode=expect-fail tree=%s head=%s fixtures=%d rejected=%d expected_checks=%d rejected_checks=%d" % (
        verdict, REJECTED.replace(os.sep, "/"), head_sha(), total, rejected, exp_total, exp_rejected))
    return 0 if verdict == "PASS" else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree", nargs="?", default=REPO, help="the tree to judge (default: the repository)")
    ap.add_argument("--checks", default=None, help="comma-separated subset of the implemented checks")
    ap.add_argument("--staged", action="store_true", help="also judge the index: checks 6 and 7")
    ap.add_argument("--commit-range", default=None, help="also judge commits A..B: checks 6 and 7")
    ap.add_argument("--expect-fail", action="store_true", help="every fixture in contracts/examples/rejected/ must be refused")
    ap.add_argument("--bundle", default=None, help="judge one built bundle with the B checks only")
    ap.add_argument("--strict", action="store_true", help="PENDING counts as failure")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    checks = set(IMPLEMENTED) | set(B_IMPLEMENTED)
    if args.checks:
        checks = {parse_check(x) for x in args.checks.split(",") if x.strip()}
        unknown = checks - set(IMPLEMENTED) - set(B_IMPLEMENTED)
        if unknown:
            ap.error("checks %s are not implemented (implemented: %s and %s)" % (sorted(unknown, key=check_key), IMPLEMENTED, B_IMPLEMENTED))
    c = Contracts()

    if args.expect_fail:
        return expect_fail(c, checks, args.strict, args.quiet)

    tree = os.path.abspath(args.tree)
    report = Report(quiet=args.quiet)
    if args.bundle:
        b_checks = {ch for ch in checks if isinstance(ch, str)}
        bundle = os.path.abspath(args.bundle)
        run_bundle_checks(bundle, c, report, b_checks, knowledge_root_for(tree))
        failed, pending = len(report.fails), len(report.pendings)
        verdict = "PASS" if failed == 0 else "FAIL"
        print("1 bundle judged; %d failed, %d pending; checks run %s" % (failed, pending, sorted(b_checks, key=check_key)))
        print("VERDICT %s mode=bundle tree=%s head=%s bundles=1 failed=%d pending=%d failed_checks=%s" % (
            verdict, bundle.replace(os.sep, "/"), head_sha(), failed, pending, report.failed_checks()))
        return 0 if verdict == "PASS" else 1
    n_cards, n_md, cards = run_static(tree, c, report, checks)
    if 6 in checks and tree == REPO:
        check6_table(c.seats, report, "contracts/seats.json")
    bundles = bundles_of(cards, tree)
    for label, path in bundles:
        run_bundle_checks(path, c, report, checks, knowledge_root_for(tree), label=label)
    n_changes = n_commits = None
    if args.staged and (6 in checks or 7 in checks or 20 in checks or 21 in checks):
        n_changes = run_staged(c, report, checks)
    if args.commit_range and (6 in checks or 7 in checks or 20 in checks or 21 in checks):
        n_commits = run_commit_range(c, report, args.commit_range, checks)

    failed = len(report.fails)
    pending = len(report.pendings)
    verdict = "PASS" if failed == 0 and (pending == 0 or not args.strict) else "FAIL"
    extra = ""
    if n_changes is not None:
        extra += " staged_changes=%d" % n_changes
    if n_commits is not None:
        extra += " commits=%d" % n_commits
    print("%d cards, %d md files, %d wiki page(s), %d bundle(s) judged; %d failed, %d pending; checks run %s" % (
        n_cards, n_md, getattr(report, "wiki_pages", 0), len(bundles), failed, pending, sorted(checks, key=check_key)))
    shown = GIT_REPO.replace(os.sep, "/") + "@index" if EXPORTED and tree == REPO else tree.replace(os.sep, "/")
    print("VERDICT %s tree=%s head=%s cards=%d md=%d bundles=%d failed=%d pending=%d failed_checks=%s%s" % (
        verdict, shown, head_sha(), n_cards, n_md, len(bundles), failed, pending, report.failed_checks(), extra))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
