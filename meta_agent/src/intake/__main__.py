"""python -m meta_agent.src.intake write | answer | waiting | check  (see card.py's docstring)."""
import argparse
import os
import sys

from .. import cards
from . import card as card_mod


def rel(path, root):
    return os.path.relpath(path, os.path.dirname(root)).replace(os.sep, "/")


def say_waiting(intake):
    left = card_mod.waiting(intake)
    for q in left:
        print("  question %s, needed before %s: %s" % (q.get("n"), q.get("needed_before"), q.get("question")))
    return left


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m meta_agent.src.intake", description=card_mod.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=card_mod.META, help="the meta_agent/ tree to write under (tests use a copy)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    wr = sub.add_parser("write", help="the card a draft gives: the first, or the next revision")
    wr.add_argument("--rid", required=True)
    wr.add_argument("--draft", required=True, help="one JSON object: what a session knows of the request")
    wr.add_argument("--seat", required=True)
    wr.add_argument("--note", help="what changed from the revision before, and on whose word")
    wr.add_argument("--now")
    an = sub.add_parser("answer", help="the person's words to one question, as the next revision")
    an.add_argument("--rid", required=True)
    an.add_argument("--n", required=True, type=int)
    an.add_argument("--verbatim", required=True, help="what the person said, unchanged, in the language they used")
    an.add_argument("--date", required=True)
    an.add_argument("--gloss")
    an.add_argument("--recorded-in", help="the docs/ideas file that carries the words")
    an.add_argument("--seat", required=True)
    an.add_argument("--now")
    wt = sub.add_parser("waiting", help="the questions that have no answer yet; writes nothing")
    wt.add_argument("--rid", required=True)
    ck = sub.add_parser("check", help="every reason the stage would not write this intake; writes nothing")
    ck.add_argument("file")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    if args.cmd == "check":
        intake = cards.load_json(args.file)
        if not card_mod.is_card(intake):
            print("not a card: this intake is of before the card (contracts/schemas/intake.schema.json) and is read as it is")
            return 0
        found = card_mod.problems(intake, os.path.dirname(os.path.abspath(args.file)))
        for line in found:
            print(line)
        print("stage %s, revision %s; %s" % (intake.get("stage"), intake.get("revision"), "%d problem(s)" % len(found) if found else "nothing to say"))
        return 1 if found else 0

    req_dir = os.path.join(root, "requests", args.rid)
    if args.cmd == "waiting":
        rev, path = card_mod.latest(req_dir)
        if path is None:
            print("no intake in %s" % rel(req_dir, root))
            return 1
        intake = cards.load_json(path)
        print("%s  stage %s, revision %d" % (rel(path, root), intake.get("stage", "(of before the card)"), rev))
        left = say_waiting(intake)
        print("%d question(s) wait for the person" % len(left) if left else "no question waits for the person")
        return 0

    try:
        if args.cmd == "write":
            path, card = card_mod.write(req_dir, args.rid, cards.load_json(args.draft), args.seat, args.now, args.note)
        else:
            path, card = card_mod.answer(req_dir, args.rid, args.n, args.verbatim, args.date, args.seat, args.gloss,
                                         args.recorded_in, args.now)
    except card_mod.Refused as e:
        print("refused  %s" % e)
        return 1
    if path is None:
        print("nothing written: the draft changes nothing of revision %s" % card.get("revision", 1))
        return 0
    print("wrote  %s" % rel(path, root))
    print("stage  %s, revision %d" % (card["stage"], card["revision"]))
    left = say_waiting(card)
    if card["stage"] == "specified":
        print("next   python -m meta_agent.src.designer --intake %s --seat %s" % (rel(path, root), args.seat))
    else:
        print("next   %s" % ("the person's answers, then the contracts and the tasks" if left else
                             "the contracts and the tasks; the card is specified when it carries them"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
