"""python -m meta_agent.src.skills list | run | index  (see the package's docstring)."""
import argparse
import json
import sys

from .. import cards
from . import LIBRARY, catalogue, runner

EXIT = {"ran": 0, "refused": 3, "failed": 4}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m meta_agent.src.skills", description=__doc__)
    ap.add_argument("--library", default=LIBRARY, help="the skills/ folder to read (default: meta_agent/skills)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list", help="the skills a model may take, read off the manifests")
    ls.add_argument("--kind")
    ls.add_argument("--parameter")
    ls.add_argument("--instrument")
    ls.add_argument("--json", action="store_true")
    rn = sub.add_parser("run", help="run one skill and say what it ran")
    rn.add_argument("ref", metavar="id@vN")
    rn.add_argument("--inputs", required=True, help="a JSON object, one key per input the manifest names")
    rn.add_argument("--transcript", help="recorded tool replies, the runner of a device skill here")
    rn.add_argument("--record", help="write the run's record to this file (never over an existing one)")
    rn.add_argument("--now", help="the record's ran_at, for a reproducible record")
    ix = sub.add_parser("index", help="write skills/index.json from the manifests")
    ix.add_argument("--check", action="store_true", help="write nothing; say whether the file on disk is current")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        rows = catalogue.select(catalogue.build_index(args.library)["skills"], args.kind, args.parameter, args.instrument)
        print(json.dumps(rows, indent=2, ensure_ascii=False) if args.json else catalogue.listing(rows))
        return 0
    if args.cmd == "index":
        if args.check:
            ok = catalogue.index_is_current(args.library)
            print("index.json is %s" % ("current" if ok else "not what the manifests give; run index"))
            return 0 if ok else 1
        path = catalogue.write_index(args.library)
        print("wrote  %s (%d skills)" % (catalogue.rel_repo(path), len(cards.load_json(path)["skills"])))
        return 0
    tools = runner.Transcript(cards.load_json(args.transcript)) if args.transcript else None
    record = runner.run(args.ref, cards.load_json(args.inputs), tools, args.library, args.now)
    if args.record:
        runner.write_record(args.record, record)
    print(json.dumps(record, indent=2, ensure_ascii=False))
    line = "%s %s: %d tool call(s)%s" % (args.ref, record["verdict"], len(record["tool_calls"]),
                                         ("; " + record["why"]) if record["why"] else "")
    print(line + ("; record at %s" % args.record if args.record else "; no record file asked for"), file=sys.stderr)
    return EXIT[record["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
