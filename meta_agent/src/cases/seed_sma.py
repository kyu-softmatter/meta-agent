"""Seed cases from soft-matter-agents' failure lines and incidents (plan.md 5.4, 14-6, 14-27(c); tasks/006).

    python -m meta_agent.src.cases.seed_sma <path-to-sma-checkout> --seat <seat>
           [--out meta_agent/cases] [--drafts meta_agent/src/cases/sma_drafts.json] [--now ISO] [--files]

Reads, and writes nothing there:
  <agent>/failures.jsonl of librarian_agent, simulation_agent, microscope_agent and bridge, as committed at
  d68ee7d2 (`git show d68ee7d2:<path>`), and contracts/harness/incidents.jsonl as it was before its
  removal (`git show 7bc5a0f9~1:<path>`). With --files the same paths are read from the folder as files
  and a file that is absent is skipped: that is for a fixture, and the commits are recorded as named.

Writes one draft case per line, <out>/sma/<source>-<n>.json with id case-sma-<source>-<n>, n the line's
number in its file, and then the store's index with contracts/tools/cases.py. A file that exists is
never rewritten (records are append-only): a second run changes nothing.

Every field but three is derived by the rules below, so the same lines give the same cases. The three
are `cue`, `lesson` and `falsification`: the model drafts them from the line, they are read from the
drafts file by case id, and they stay drafts until the person confirms. A line without a draft gets no
case, and the run says so and exits 1.

What a case carries
  status draft, cause_status observed, numbers [] (no number of a line is lifted), count 1 / 0 with
  last_seen the line's day (an incident with no day of its own takes the day it was recorded, and
  its note says so), confidence low, source_agent, source_repo_commit, and one evidence item of
  kind commit naming repository, commit, file and line. `what_happened` is copied: the line's `what`,
  or, where a failure line has none, its string fields in order as "key: value" (the seat's name left
  out). kind is `success` for a success line, `incident` for an incident, `failure` otherwise.

Signature (what recall can meet)
  executes        instrument for microscope_agent, engine for simulation_agent, none for the rest
  engine          hoomd, when a simulation_agent line names it
  observables     tracer_diffusivity, when the line carries that identifier
  science_task    empty: no line states one
  cause_class     an incident's class with - as _, when contracts/case_classes.json has that key;
                  otherwise unknown ("not classified yet"), which recall meets with nothing
  condition_tags  sma_agent:<source>, sma_kind:<kind> (failure lines), sma_class:<class> (incidents),
                  seed_verdict:<verdict>

Verdict (a draft ruling by rule, the first that applies; the person may rule otherwise in a revision)
  failure lines
    F1  kind success                                              -> drop
        a success line records no failure to recall
    F2  kind refusal with detail.what_is_left                     -> transfer
        a refusal that says what is left is a boundary that can hold here too
    F3  a microscope_agent line                                   -> downgrade
        it speaks of one bench; here it is a hint, not a finding
    F4  kind refusal                                              -> downgrade
        a refusal that does not say what is left
    F5  detail states a general form (shape_to_remember, the_general_form, how_to_apply,
        what_would_have_caught_it or class)                       -> transfer
        the line itself says what recurs
    F6  anything else                                             -> downgrade
        specific to its task there, with no general form stated
  incidents
    I1  every evidence item is prose_only                         -> downgrade
        it rests on a sentence of that repository's instructions, not on a commit, a file or a log
    I2  anything else                                             -> transfer
        a commit, a file or a log there shows it

Grade by verdict: transfer E3 (a run over there is not a run over here; check 8 caps a prior
repository's case at E3), downgrade E5, drop E5. A dropped seed stays in the store as the record of the
ruling and recall leaves it out (`seed_verdict:drop`). The verdict and its rule are on the case's note.
"""
import argparse
import json
import os
import re
import subprocess
import sys

from . import META, REPO, rules
from .. import cards

REPOSITORY = "soft-matter-agents"
FAILURES_COMMIT = "d68ee7d2"
INCIDENTS_COMMIT = "7bc5a0f9~1"
# (source name in ids and file names, the agent folder, commit, path in the repository, executes)
SOURCES = [
    ("librarian", "librarian_agent", FAILURES_COMMIT, "librarian_agent/failures.jsonl", "none"),
    ("simulation", "simulation_agent", FAILURES_COMMIT, "simulation_agent/failures.jsonl", "engine"),
    ("microscope", "microscope_agent", FAILURES_COMMIT, "microscope_agent/failures.jsonl", "instrument"),
    ("bridge", "bridge", FAILURES_COMMIT, "bridge/failures.jsonl", "none"),
    ("incident", "harness", INCIDENTS_COMMIT, "contracts/harness/incidents.jsonl", "none"),
]
GENERAL_FORM = ("shape_to_remember", "the_general_form", "how_to_apply", "what_would_have_caught_it", "class")
OBSERVABLE_IDS = ("tracer_diffusivity",)
RULES = {
    "F1": ("drop", "a success line records no failure to recall"),
    "F2": ("transfer", "a refusal that says what is left is a boundary that can hold here too"),
    "F3": ("downgrade", "a microscope_agent line speaks of one bench; here it is a hint, not a finding"),
    "F4": ("downgrade", "a refusal that does not say what is left"),
    "F5": ("transfer", "the line itself states a general form of what recurs"),
    "F6": ("downgrade", "specific to its task there, with no general form stated"),
    "I1": ("downgrade", "it rests on a sentence of that repository's instructions, not on a commit, a file or a log"),
    "I2": ("transfer", "a commit, a file or a log there shows it"),
}
GRADE = {"transfer": "E3", "downgrade": "E5", "drop": "E5"}
DEFAULT_DRAFTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sma_drafts.json")
DRAFTED = ("cue", "lesson", "falsification")
CLASS_VALUE = re.compile(r"^[A-Za-z0-9_.+-]+$")


def read_source(checkout, commit, path, files=False):
    """The text of one source file, or None when --files is given and the file is not there."""
    if files:
        full = os.path.join(checkout, path)
        if not os.path.isfile(full):
            return None
        with open(full, "r", encoding="utf-8") as f:
            return f.read()
    p = subprocess.run(["git", "-C", checkout, "show", "%s:%s" % (commit, path)], capture_output=True)
    if p.returncode != 0:
        raise SystemExit("seed_sma: cannot read %s:%s in %s: %s" % (commit, path, checkout, p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout.decode("utf-8")


def lines_of(text):
    """[(line number, object)] of a JSONL text; blank lines keep their number and give nothing."""
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        if raw.strip():
            out.append((n, json.loads(raw)))
    return out


def verdict_of(source, line):
    """(rule id, verdict) for one line, by the rules of the module's docstring."""
    if source == "incident":
        kinds = {e.get("kind") for e in line.get("evidence") or [] if isinstance(e, dict)}
        return ("I1", "downgrade") if kinds <= {"prose_only"} else ("I2", "transfer")
    detail = line.get("detail") if isinstance(line.get("detail"), dict) else {}
    kind = line.get("kind")
    if kind == "success":
        rule = "F1"
    elif kind == "refusal" and detail.get("what_is_left"):
        rule = "F2"
    elif source == "microscope":
        rule = "F3"
    elif kind == "refusal":
        rule = "F4"
    elif any(k in detail for k in GENERAL_FORM):
        rule = "F5"
    else:
        rule = "F6"
    return rule, RULES[rule][0]


def what_happened(source, line):
    if source == "incident":
        return str(line["what"]).strip()
    detail = line.get("detail") if isinstance(line.get("detail"), dict) else {}
    if isinstance(detail.get("what"), str) and detail["what"].strip():
        return detail["what"].strip()
    parts = ["%s: %s" % (k, v.strip()) for k, v in detail.items() if k != "seat" and isinstance(v, str) and v.strip()]
    return "; ".join(parts) or json.dumps(detail, ensure_ascii=False, sort_keys=True)


def day_of(source, line):
    """(day, undated): the line's own day; an incident with no `on` gives the day it was recorded."""
    if source != "incident":
        return str(line["at"])[:10], False
    if isinstance(line.get("on"), str) and line["on"].strip():
        return line["on"][:10], False
    return str(line["recorded_on"])[:10], True


def signature_of(source, executes, line, verdict, case_classes):
    text = json.dumps(line, ensure_ascii=False).lower()
    tags = ["sma_agent:" + source]
    cause = "unknown"
    if source == "incident":
        cls = str(line.get("class") or "")
        if CLASS_VALUE.match(cls):
            tags.append("sma_class:" + cls)
        if cls.replace("-", "_") in case_classes:
            cause = cls.replace("-", "_")
    else:
        tags.append("sma_kind:" + str(line.get("kind")))
    tags.append("seed_verdict:" + verdict)
    sig = {"science_task": "", "executes": executes}
    if source == "simulation" and "hoomd" in text:
        sig["engine"] = "hoomd"
    sig["observables"] = [o for o in OBSERVABLE_IDS if o in text]
    sig["parameter_names"] = []
    sig["cause_class"] = cause
    sig["condition_tags"] = tags
    return sig, cause


def case_of(source, agent, commit, path, executes, n, line, draft, seat, now, case_classes):
    rule, verdict = verdict_of(source, line)
    sig, cause = signature_of(source, executes, line, verdict, case_classes)
    cid = "case-sma-%s-%03d" % (source, n)
    where = "%s@%s %s:%d" % (REPOSITORY, commit, path, n)
    if source == "incident":
        where += " (%s)" % line.get("id")
        kind, said = "incident", "an incident of class %s" % line.get("class")
    else:
        kind = "success" if line.get("kind") == "success" else "failure"
        said = "a %s line" % line.get("kind")
    day, undated = day_of(source, line)
    card = cards.skeleton("case", cid, seat, now)
    card.update({
        "kind": kind,
        "signature": sig,
        "what_happened": what_happened(source, line),
        "cause_class": cause,
        "cause_status": "observed",
        "evidence": [{"kind": "commit", "ref": where}],
        "cue": draft["cue"],
        "lesson": draft["lesson"],
        "confidence": {"level": "low", "why": "one line of a prior repository, not rerun here; cue, lesson and falsification are the model's drafts"},
        "falsification": draft["falsification"],
        "count": {"supports": 1, "contradicts": 0, "last_seen": day},
        "source_agent": agent,
        "source_repo_commit": commit,
        "grade": GRADE[verdict],
        "superseded_by": None,
        "note": "Seed from %s, %s. Verdict %s by rule %s of meta_agent/src/cases/seed_sma.py: %s. what_happened is copied "
                "from the line; cue, lesson and falsification are the model's drafts and stay drafts until the person "
                "confirms; the verdict is a draft ruling and the person may rule otherwise in a revision.%s" % (
                    where, said, verdict, rule, RULES[rule][1],
                    " The incident carries no day of its own; last_seen is the day it was recorded." if undated else ""),
    })
    return verdict, card


def seed(checkout, out_dir, seat, drafts, now=None, files=False):
    """Write the cases that are not there yet. Returns a report dict; writes no index."""
    now = cards.now_iso(now)
    with open(os.path.join(REPO, "contracts", "case_classes.json"), "r", encoding="utf-8") as f:
        case_classes = json.load(f)["classes"]
    report = {"sources": [], "written": [], "kept": [], "no_draft": [], "verdicts": {"transfer": 0, "downgrade": 0, "drop": 0}}
    for source, agent, commit, path, executes in SOURCES:
        text = read_source(checkout, commit, path, files)
        if text is None:
            continue
        row = {"source": source, "path": path, "commit": commit, "lines": 0, "transfer": 0, "downgrade": 0, "drop": 0}
        for n, line in lines_of(text):
            row["lines"] += 1
            cid = "case-sma-%s-%03d" % (source, n)
            draft = drafts.get(cid)
            if not (isinstance(draft, dict) and all(isinstance(draft.get(k), str) and draft[k].strip() for k in DRAFTED)):
                report["no_draft"].append(cid)
                continue
            verdict, card = case_of(source, agent, commit, path, executes, n, line, draft, seat, now, case_classes)
            row[verdict] += 1
            report["verdicts"][verdict] += 1
            target = os.path.join(out_dir, "sma", "%s-%03d.json" % (source, n))
            if os.path.exists(target):
                report["kept"].append(cid)
            else:
                cards.write_json(target, card)
                report["written"].append(cid)
        report["sources"].append(row)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkout", help="the soft-matter-agents checkout; read only")
    ap.add_argument("--seat", required=True)
    ap.add_argument("--out", default=os.path.join(META, "cases"), help="the cases/ store to write under")
    ap.add_argument("--drafts", default=DEFAULT_DRAFTS, help="cue, lesson and falsification by case id")
    ap.add_argument("--now", default=None)
    ap.add_argument("--files", action="store_true", help="read the paths as files of the folder (a fixture), not through git")
    args = ap.parse_args(argv)
    out_dir = os.path.abspath(args.out)
    if os.path.basename(out_dir) != "cases":
        raise SystemExit("seed_sma: --out is a cases/ folder")
    checkout = os.path.abspath(args.checkout)
    if out_dir == checkout or out_dir.startswith(checkout + os.sep):
        raise SystemExit("seed_sma: nothing is written into the checkout it reads")
    with open(args.drafts, "r", encoding="utf-8") as f:
        drafts = json.load(f)
    report = seed(args.checkout, out_dir, args.seat, drafts, args.now, args.files)
    for row in report["sources"]:
        print("%-10s %s@%s  %3d line(s): transfer %d, downgrade %d, drop %d" % (
            row["source"], row["path"], row["commit"], row["lines"], row["transfer"], row["downgrade"], row["drop"]))
    print("verdicts   transfer %(transfer)d, downgrade %(downgrade)d, drop %(drop)d" % report["verdicts"])
    print("written    %d case(s); %d already there and left as they are" % (len(report["written"]), len(report["kept"])))
    if report["written"] or not os.path.isfile(os.path.join(out_dir, "index.json")):
        os.makedirs(out_dir, exist_ok=True)
        rules.main(["index", out_dir])
    if report["no_draft"]:
        print("no draft   %d line(s) have no cue, lesson and falsification in %s and got no case: %s" % (
            len(report["no_draft"]), args.drafts, ", ".join(report["no_draft"][:8]) + (" ..." if len(report["no_draft"]) > 8 else "")))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
