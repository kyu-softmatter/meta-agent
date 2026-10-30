"""Run S0 on a lab.

    python -m meta_agent.src.onboarding --lab-id <id> --out <folder>
        [--repo PATH[=URL][@COMMIT]]... [--folder PATH]...
        [--answers answers.json] [--seat <seat>] [--now <iso>]

Writes discovery_report.json, onboarding_record.json, lab_profile.json and
proposal.md into --out. With --answers it also writes v2_onboarding_record.json
and v2_lab_profile.json carrying the person's answers. Prints the question
counts read off the record, then the questions.
"""
import argparse
import os
import sys

from . import cards, discover, wizard


def parse_repo(spec):
    path, url, commit = spec, None, None
    if "=" in spec:
        path, rest = spec.split("=", 1)
        url = rest
        if "@" in rest:
            url, commit = rest.rsplit("@", 1)
    elif "@" in spec and not os.path.exists(spec):
        path, commit = spec.rsplit("@", 1)
    return path, url, commit


def main(argv=None):
    ap = argparse.ArgumentParser(prog="onboarding")
    ap.add_argument("--lab-id", required=True)
    ap.add_argument("--out", required=True, help="profiles/<lab_id>/ folder to write into")
    ap.add_argument("--repo", action="append", default=[], help="PATH[=URL][@COMMIT] of a repository to read")
    ap.add_argument("--folder", action="append", default=[], help="a plain folder to read")
    ap.add_argument("--answers", help="the person's answers: {answered_by, date, answers:{field: value}}")
    ap.add_argument("--seat", default=os.environ.get("META_AGENT_SEAT", "meta-office-20261029-1"))
    ap.add_argument("--now", help="ISO timestamp for reproducible runs")
    args = ap.parse_args(argv)

    sources = []
    for spec in args.repo:
        path, url, commit = parse_repo(spec)
        sources.append(discover.Source(path, url=url, commit=commit, kind="repo",
                                       name=os.path.basename(url.rstrip("/")) if url else None))
    for path in args.folder:
        sources.append(discover.Source(path, kind="folder"))

    disc = discover.discover(args.lab_id, sources, args.seat, args.now)
    record = wizard.ask(disc, args.seat, args.now)
    profile = wizard.propose(disc, record, args.seat, args.now)
    out = args.out
    cards.write_json(os.path.join(out, "discovery_report.json"), disc)
    cards.write_json(os.path.join(out, "onboarding_record.json"), record)
    cards.write_json(os.path.join(out, "lab_profile.json"), profile)
    cards.write_text(os.path.join(out, "proposal.md"),
                     wizard.proposal_markdown(disc, record, profile, discover.load_registry("engines")))

    n_pol = sum(1 for q in record["questions"] if q["state_at_ask"] == "policy")
    print("lab %s: %d input(s); %d field(s) inferred, %d unknown" % (
        args.lab_id, len(sources),
        sum(1 for v in disc["fields"].values() if v["state"] == "inferred"),
        sum(1 for v in disc["fields"].values() if v["state"] == "unknown")))
    print("questions asked: %d (policy %d, unknown %d); skipped %d; held %d" % (
        len(record["questions"]), n_pol, len(record["questions"]) - n_pol, len(record["skipped"]), len(record["held"])))
    for q in record["questions"]:
        print("  [%s] %s: %s" % (q["state_at_ask"], q["field"], q["question"]))

    if args.answers:
        a = cards.load_json(args.answers)
        rec2, prof2 = wizard.apply_answers(record, profile, a["answers"], a.get("answered_by"), a["date"], args.seat, args.now)
        cards.write_json(os.path.join(out, "v2_onboarding_record.json"), rec2)
        cards.write_json(os.path.join(out, "v2_lab_profile.json"), prof2)
        print("answers applied: %d confirmed; record %s, profile %s; still open: %s" % (
            len(a["answers"]), rec2["status"], prof2["status"],
            [q["field"] for q in rec2["questions"] if q["answered_by"] is None] or "none"))
    else:
        print("stopped after Step two: waiting for the person's answers (plan.md 14-19)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
