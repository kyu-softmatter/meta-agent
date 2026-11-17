"""Run S0 on a lab.

    python -m meta_agent.src.onboarding --lab-id <id> --out <folder>
        [--repo PATH[=URL][@COMMIT]]... [--folder PATH]...
        [--answers answers.json] [--seat <seat>] [--now <iso>]

Writes discovery_report.json, onboarding_record.json, lab_profile.json and
proposal.md into --out. With --answers it also writes v2_onboarding_record.json
and v2_lab_profile.json carrying the person's answers. Prints the question
counts read off the record, then the questions.

    python -m meta_agent.src.onboarding --lab-id <id> --out <folder> --answers answers.json --seat <seat>

With --answers and nothing to read (no --repo, no --folder), on a folder that already
holds a lab's record and profile, it runs Step three alone: the answers are applied to
the latest revision of each, the next revision of each is written, and no card the
folder holds is written again. This is how a lab that was onboarded earlier gets the
person's answers when they come.
"""
import argparse
import os
import re
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


def latest(out, name):
    """(revision, path) of the highest revision of a card in a profile folder: v<N>_<name>, or <name> for the first."""
    found = []
    for fn in os.listdir(out) if os.path.isdir(out) else []:
        m = re.match(r"^(?:v([0-9]+)_)?%s$" % re.escape(name), fn)
        if m:
            found.append((int(m.group(1) or 1), os.path.join(out, fn)))
    return max(found) if found else (0, None)


def answers_only(lab_id, out, answers_path, seat, now=None):
    """Step three alone, on the cards a profile folder holds. Returns the two paths written."""
    (rev_r, rec_path), (rev_p, prof_path) = latest(out, "onboarding_record.json"), latest(out, "lab_profile.json")
    record, profile = cards.load_json(rec_path), cards.load_json(prof_path)
    if profile.get("lab_id") != lab_id or record.get("lab_id") != lab_id:
        raise ValueError("%s holds the cards of %r, not of %r" % (out, profile.get("lab_id"), lab_id))
    a = cards.load_json(answers_path)
    asked = {q["field"] for q in record["questions"]}
    unasked = sorted(f for f in a["answers"] if f not in asked)
    if unasked:
        raise ValueError("an answer to a question the record did not ask: %s" % ", ".join(unasked))
    rec2, prof2 = wizard.apply_answers(record, profile, a["answers"], a.get("answered_by"), a["date"], seat, now)
    paths = [os.path.join(out, "v%d_onboarding_record.json" % (rev_r + 1)), os.path.join(out, "v%d_lab_profile.json" % (rev_p + 1))]
    for p in paths:
        if os.path.exists(p):
            raise FileExistsError(p)
    cards.write_json(paths[0], rec2)
    cards.write_json(paths[1], prof2)
    print("answers applied: %d confirmed; record %s, profile %s; still open: %s" % (
        len(a["answers"]), rec2["status"], prof2["status"],
        [q["field"] for q in rec2["questions"] if q["answered_by"] is None] or "none"))
    for p in paths:
        print("wrote  %s" % p)
    return paths


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

    if args.answers and not args.repo and not args.folder and latest(args.out, "onboarding_record.json")[1] \
            and latest(args.out, "lab_profile.json")[1]:
        answers_only(args.lab_id, args.out, args.answers, args.seat, args.now)
        return 0

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
