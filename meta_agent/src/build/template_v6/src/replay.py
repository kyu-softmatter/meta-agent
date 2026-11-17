"""Run the regression suite in replay/ against this bundle's tools.

    python src/replay.py [--json]

Each replay/<id>.json item names a call and what it expected: an output,
or an error of a category (and optionally a code). A refusal expected is a
refusal required. Prints one line per item and a summary; exit status is
zero only when every item's verdict equals its expected verdict.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import run_tool  # noqa: E402


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def judge(item):
    """Return (verdict, detail) for one call item: 'pass' when the call matched the expectation."""
    call = item["call"]
    try:
        out = run_tool.run_call(call["tool"], call["input"])
    except FileNotFoundError as exc:
        return "fail", str(exc)
    expected = item.get("expected") or {}
    is_error = isinstance(out, dict) and out.get("artifact") == "error_contract"
    if "error" in expected:
        want = expected["error"]
        if not is_error:
            return "fail", "expected an error of category %s, got an output" % want.get("category")
        if want.get("category") and out.get("category") != want["category"]:
            return "fail", "expected category %s, got %s" % (want["category"], out.get("category"))
        if want.get("code") and out.get("code") != want["code"]:
            return "fail", "expected code %s, got %s" % (want["code"], out.get("code"))
        return "pass", "error %s as expected" % out.get("code")
    if is_error:
        return "fail", "expected an output, got error %s (%s)" % (out.get("code"), out.get("category"))
    want = expected.get("output")
    if want is not None:
        for k, v in want.items():
            if out.get(k) != v:
                return "fail", "output.%s = %r, expected %r" % (k, out.get(k), v)
    return "pass", "output matched"


def run_dir(d):
    results = []
    if not os.path.isdir(d):
        return results
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        item = load(os.path.join(d, fn))
        verdict, detail = judge(item)
        results.append({"id": item.get("id", fn), "name": item.get("name", item.get("id", fn)), "verdict": verdict,
                        "expected_verdict": item.get("expected_verdict", "pass"), "detail": detail, "file": fn})
    return results


def main(argv):
    results = run_dir(os.path.join(BUNDLE, "replay"))
    ok = all(r["verdict"] == r["expected_verdict"] for r in results) and bool(results)
    if "--json" in argv:
        print(json.dumps({"items": results, "ok": ok}, indent=2))
    else:
        for r in results:
            print("%-6s %-12s expected %-6s %s" % (r["verdict"], r["id"], r["expected_verdict"], r["detail"]))
        print("replay: %d item(s), %d as expected, %d not; %s" % (
            len(results), sum(1 for r in results if r["verdict"] == r["expected_verdict"]),
            sum(1 for r in results if r["verdict"] != r["expected_verdict"]), "OK" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
