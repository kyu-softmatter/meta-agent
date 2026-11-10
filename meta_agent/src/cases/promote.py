"""Promotion eligibility, computed; it lands nothing (plan.md 5.4, 14-15, 14-27(d); tasks/006).

    python -m meta_agent.src.cases.promote [--store meta_agent/cases]
    python -m meta_agent.src.cases.promote --n N [--emit kb_candidate|reshape] [--out DIR] [--seat SEAT] [--now ISO]

A case may be promoted when its `cause_status` is `confirmed` and its `count.supports` is at or above
N. N is the person's (14-15): it has no default here and is never read from anywhere but the flag.

Without --n the command lists the confirmed cases with their counts, says UNDECIDED and writes
nothing. With --n it lists the eligible ones. With --emit it also drafts, for each eligible case,
  kb_candidate  a `kb_candidate` card whose claim is the case's lesson, or
  reshape       a `harness_proposal` of kind `reshape` (the lesson as a skill),
each `status: draft`, carrying the case's cue, condition tags and falsification as its scope and
limits, and naming the case it came from. The drafts are printed, or written under --out when a
folder is given. Nothing is landed, no case is changed and no store is written: what becomes of a
draft is the librarian's, the owning seat's and the person's.

A candidate's grade is never better than its case's: a case from a prior repository gives
`prior_run:` at E3, a case of this system with run evidence gives `measured:` at E1 when the case
itself is E1, and anything else gives `assumed:` at E5; the grade is looked up in
contracts/grades.json, not stated.
"""
import argparse
import json
import os
import sys

from . import META, REPO
from . import recall as recall_mod
from .. import cards

GRADE_ORDER = recall_mod.GRADE_ORDER


def confirmed_cases(store_dir):
    """[(index row, case)] of the recallable cases whose cause is confirmed, in id order."""
    return [(row, case) for row, case in recall_mod.load_store(store_dir) if case.get("cause_status") == "confirmed"]


def supports_of(case):
    return (case.get("count") or {}).get("supports", 0)


def eligible(store_dir, n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("N is a positive integer given by the person")
    return [(row, case) for row, case in confirmed_cases(store_dir) if supports_of(case) >= n]


def derived_grade(source_kind, value_kind):
    with open(os.path.join(REPO, "contracts", "grades.json"), "r", encoding="utf-8") as f:
        table = json.load(f)
    for rule in table["rules"]:
        if rule["source_kind"] == source_kind and value_kind in rule["value_kinds"] and not rule.get("retired_on"):
            return rule["grade"]
    raise ValueError("contracts/grades.json has no row for %s / %s" % (source_kind, value_kind))


def source_of(case):
    """(source, value_kind, grade) for a candidate, never better than the case's own grade."""
    case_rank = GRADE_ORDER.get(case.get("grade"), 9)
    choices = []
    if case.get("source_repo_commit"):
        ref = next((e["ref"] for e in case.get("evidence") or [] if e.get("kind") == "commit"), case["source_repo_commit"])
        choices.append(("prior_run:" + ref, "measured"))
    else:
        run = next((e["ref"] for e in case.get("evidence") or [] if e.get("kind") == "run"), None)
        if run:
            choices.append(("measured:" + run, "measured"))
    choices.append(("assumed:" + case["id"], "estimated"))
    for source, value_kind in choices:
        grade = derived_grade(source.split(":", 1)[0], value_kind)
        if GRADE_ORDER[grade] >= case_rank:
            return source, value_kind, grade
    source, value_kind = choices[-1]
    return source, value_kind, derived_grade("assumed", value_kind)


def suffix_of(case):
    return case["id"][len("case-"):] if case["id"].startswith("case-") else case["id"]


def scope_of(case):
    sig = case.get("signature") or {}
    return {"cue": case["cue"], "condition_tags": list(sig.get("condition_tags") or []), "falsification": case["falsification"]}


def why(case, n):
    return ("promotion eligibility computed by meta_agent/src/cases/promote.py from %s revision %s: cause_status confirmed, "
            "count.supports %d at or above the N of %d given on the command line; a draft that lands nothing" % (
                case["id"], case.get("revision"), supports_of(case), n))


def kb_candidate_of(case, n, seat, now):
    sig = case.get("signature") or {}
    source, value_kind, grade = source_of(case)
    card = cards.skeleton("kb_candidate", "kbc-" + suffix_of(case), seat, now)
    card.update({
        "subject": sig.get("science_task") or "cause class " + case["cause_class"],
        "claim": case["lesson"],
        "conditions": scope_of(case),
        "source": source,
        "grade": grade,
        "value_kind": value_kind,
        "validity": {"conditions": "until falsified: " + case["falsification"]},
        "relations": {"supports": [], "refutes": [], "supersedes": [], "conflict_with": []},
        "proposed_to": "own_store",
        "origin": {"case_ref": case["id"], "note": why(case, n)},
    })
    return card


def reshape_of(case, n, seat, now):
    card = cards.skeleton("harness_proposal", "HP-" + suffix_of(case), seat, now)
    card.update({
        "kind": "reshape",
        "class": case["cause_class"],
        "answers": [case["id"]],
        "changes": [{"path": "(a skill, to be named by the owning seat)", "owner": "(the owning seat)",
                     "change": "%s Applies when: %s. Falsified when: %s" % (case["lesson"], case["cue"], case["falsification"])}],
        "edit_rows": [],
        "proof": {"fixtures": [], "replay": {"range": None, "new_fail": None}},
        "persons_words": None,
        "touches_core": [],
        "needs_threshold": False,
        "cost": {"rollouts": 0, "sessions": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0, "usd_basis": "computed"},
        "note": why(case, n) + ". Condition tags of the case: %s." % (", ".join(scope_of(case)["condition_tags"]) or "none"),
    })
    return card


EMIT = {"kb_candidate": kb_candidate_of, "reshape": reshape_of}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", default=os.path.join(META, "cases"))
    ap.add_argument("--n", type=int, default=None, help="the person's N; there is no default")
    ap.add_argument("--emit", choices=sorted(EMIT))
    ap.add_argument("--out", help="a folder for the drafts; without it they are printed")
    ap.add_argument("--seat")
    ap.add_argument("--now", default=None)
    args = ap.parse_args(argv)
    confirmed = confirmed_cases(args.store)
    if args.n is None:
        if args.emit or args.out:
            ap.error("--emit and --out need --n: N is the person's and has no default")
        print("confirmed  %d case(s) with cause_status confirmed" % len(confirmed))
        for row, case in confirmed:
            print("  %s  supports %d  grade %s" % (case["id"], supports_of(case), case.get("grade")))
        print("UNDECIDED  N is the person's (plan.md 14-15); give it with --n. Nothing written.")
        return 0
    chosen = eligible(args.store, args.n)
    print("eligible   %d of %d confirmed case(s) with count.supports >= %d" % (len(chosen), len(confirmed), args.n))
    for row, case in chosen:
        print("  %s  supports %d  grade %s" % (case["id"], supports_of(case), case.get("grade")))
    if not args.emit:
        print("nothing written (no --emit)")
        return 0
    if not args.seat:
        ap.error("--emit needs --seat, the author of the drafts")
    now = cards.now_iso(args.now)
    for row, case in chosen:
        card = EMIT[args.emit](case, args.n, args.seat, now)
        if args.out:
            path = os.path.join(args.out, card["id"] + ".json")
            if os.path.exists(path):
                print("kept       %s (already there)" % path)
                continue
            cards.write_json(path, card)
            print("draft      %s" % path)
        else:
            print(json.dumps(card, indent=2, ensure_ascii=False))
    print("landed nothing: the drafts wait for the librarian, the owning seat or the person")
    return 0


if __name__ == "__main__":
    sys.exit(main())
