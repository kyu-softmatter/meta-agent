"""Recall: a case is found before a card is written (plan.md 5.4, 14-27(a); tasks/006).

    python -m meta_agent.src.cases.recall --signature FILE.json [--store meta_agent/cases]

Deterministic and called, not offered: the same signature against the same store gives the same
result, byte for byte. No model call, no text similarity, no embedding (plan.md 13, 14-7): a scalar
field meets when the two values are equal after lower-casing and collapsing blanks, a list field when
an item is equal, a condition tag when `tags_meet` of contracts/tools/cases.py says so (equal, a
number inside a range, or two ranges that overlap, on one name).

Two levels.
  Level 1, the signature: a case is a hit when at least one identifying field meets (science_task,
    instrument, engine, methods, observables, parameter_names, condition_tags). `executes` and
    `cause_class` add weight to such a hit and never make one alone: `executes` has four values.
  Level 2, searched only when level 1 found nothing: `cause_class` and `executes` alone, both stated
    by the signature and both equal. The class `unknown` means "not classified yet" and meets nothing.
The result names the level that matched. A miss is a gap naming the store and the signature as
searched, at both levels.

Order of hits: grade (E1 first), then count.supports (more first), then the hit's weight (heavier
first), then id. Grade and count come first because that is the settled order (14-27(a)); the weight
orders what they leave tied, ahead of the id, which carries no meaning.

Not recalled: an older revision of an id, a case with `superseded_by` or with status `superseded`
or `refused`, and a case tagged `seed_verdict:drop` (a prior entry ruled not carried over; the card
stays in the store as the record of the ruling, MP6).
"""
import argparse
import json
import os
import sys

from . import rules

# The weight of one meeting in each field. Not a threshold and not the person's to set (14-15 keeps
# thresholds with the person; nothing here is compared with a cut-off): they only say which fields
# identify a situation more narrowly, and so which of two hits of equal grade and count comes first.
# A science task or a tool names the situation; a condition or an observable narrows it; a method or a
# parameter name is shared by many situations; the cause class and what the agent executes are the
# coarsest. A list field adds its weight once per item of the signature that meets.
WEIGHTS = {
    "science_task": 5,
    "instrument": 4,
    "engine": 4,
    "condition_tags": 3,
    "observables": 3,
    "methods": 2,
    "parameter_names": 2,
    "cause_class": 2,
    "executes": 1,
}
SCALARS = ("science_task", "executes", "instrument", "engine", "cause_class")
LISTS = ("methods", "observables", "parameter_names")
TAGS = "condition_tags"
FIELDS = ("science_task", "executes", "instrument", "engine", "methods", "observables", "parameter_names",
          "cause_class", TAGS)
IDENTIFYING = ("science_task", "instrument", "engine", "methods", "observables", "parameter_names", TAGS)
LEVEL_2 = ("cause_class", "executes")
NEVER_MEETS = {"cause_class": ("unknown",), "executes": ()}
NOT_RECALLED_STATUS = ("superseded", "refused")
NOT_RECALLED_TAGS = ("seed_verdict:drop",)
GRADE_ORDER = {"E1": 1, "E2": 2, "E3": 3, "E4": 4, "E5": 5, "E6": 6}


class RecallError(Exception):
    """The store cannot be read as a store: recall refuses rather than search a part of it."""


def norm(value):
    return " ".join(str(value).lower().split())


def normalize(signature):
    """The signature as searched: the nine fields, empty ones left out, lists deduplicated and sorted."""
    out = {}
    sig = signature if isinstance(signature, dict) else {}
    for f in FIELDS:
        v = sig.get(f)
        if f in SCALARS:
            if isinstance(v, str) and norm(v):
                out[f] = norm(v)
        elif f == TAGS:
            tags = sorted({t.strip() for t in (v or []) if isinstance(t, str) and t.strip()})
            if tags:
                out[f] = tags
        else:
            items = sorted({norm(x) for x in (v or []) if isinstance(x, str) and norm(x)})
            if items:
                out[f] = items
    return out


def signature_text(sig, fields=FIELDS):
    """One line, in the fixed field order, for a gap's `searched`."""
    parts = []
    for f in fields:
        if f in sig:
            v = sig[f]
            parts.append("%s=%s" % (f, ", ".join(v) if isinstance(v, list) else v))
    return "; ".join(parts) if parts else "(nothing stated)"


def meetings(query, case_sig):
    """{field: number of meetings} between a normalized signature and a normalized case signature."""
    met = {}
    for f in SCALARS:
        if f in query and f in case_sig and query[f] == case_sig[f] and query[f] not in NEVER_MEETS.get(f, ()):
            met[f] = 1
    for f in LISTS:
        n = len(set(query.get(f, ())) & set(case_sig.get(f, ())))
        if n:
            met[f] = n
    n = sum(1 for t in query.get(TAGS, ()) if any(rules.tags_meet(t, u) for u in case_sig.get(TAGS, ())))
    if n:
        met[TAGS] = n
    return met


def weight_of(met):
    return sum(WEIGHTS[f] * n for f, n in met.items())


def load_store(store_dir):
    """[(index row, case)] for the latest revision of every recallable case, in id order."""
    spec = rules.store_of(store_dir)
    if spec is None or spec["card"] != "case":
        raise RecallError("%s is not a cases/ folder" % store_dir)
    problem = rules.index_problem(store_dir)
    if problem:
        raise RecallError("%s: %s" % (store_dir, problem))
    base = os.path.dirname(os.path.abspath(store_dir))
    latest = {}
    for row in rules.read_index(store_dir)[spec["key"]]:
        rev = row.get("revision") if isinstance(row.get("revision"), int) else 0
        if row["id"] not in latest or rev > latest[row["id"]][0]:
            latest[row["id"]] = (rev, row)
    out = []
    for cid in sorted(latest):
        row = latest[cid][1]
        with open(os.path.join(base, row["path"]), "r", encoding="utf-8") as f:
            case = json.load(f)
        tags = (case.get("signature") or {}).get(TAGS) or []
        if case.get("superseded_by") or case.get("status") in NOT_RECALLED_STATUS \
                or any(t in NOT_RECALLED_TAGS for t in tags):
            continue
        out.append((row, case))
    return out


def one_line(text):
    return " ".join(str(text or "").split())


def hit_of(row, case, level, met, parent=""):
    return {
        "id": row["id"],
        "revision": row.get("revision"),
        "path": (parent + "/" if parent else "") + row["path"],
        "hash": row["hash"],
        "grade": case.get("grade"),
        "supports": (case.get("count") or {}).get("supports", 0),
        "level": level,
        "weight": weight_of(met),
        "matched": [f for f in FIELDS if f in met],
        "cue": one_line(case.get("cue")),
    }


def order(hits):
    return sorted(hits, key=lambda h: (GRADE_ORDER.get(h["grade"], 9), -h["supports"], -h["weight"], h["id"]))


def recall(signature, store_dir, label=None):
    """Search a cases/ store for a signature.

    Returns {store, cases_read, searched, level, hits}: `level` is 1, 2 or None (a miss), `hits` is
    ordered, `searched` is the normalized signature. `label` is how the store is named in the result
    (a repository-relative path); it defaults to the path given, and a hit's path is written under it.
    """
    label = (label or store_dir).replace(os.sep, "/").rstrip("/")
    parent = label.rsplit("/", 1)[0] if "/" in label else ""
    query = normalize(signature)
    result = {"store": label + "/index.json", "cases_read": 0, "searched": query, "level": None, "hits": []}
    if not os.path.isdir(store_dir) or not os.path.isfile(os.path.join(store_dir, "index.json")):
        result["store"] = label + " (absent)" if not os.path.isdir(store_dir) else label + " (no index.json)"
        return result
    store = load_store(store_dir)
    result["cases_read"] = len(store)
    scored = [(row, case, meetings(query, normalize(case.get("signature")))) for row, case in store]
    hits = [hit_of(row, case, 1, met, parent) for row, case, met in scored if any(f in met for f in IDENTIFYING)]
    if hits:
        result["level"], result["hits"] = 1, order(hits)
        return result
    if all(f in query for f in LEVEL_2):
        hits = [hit_of(row, case, 2, {f: met[f] for f in LEVEL_2}, parent)
                for row, case, met in scored if all(f in met for f in LEVEL_2)]
        if hits:
            result["level"], result["hits"] = 2, order(hits)
    return result


def searched_lines(result):
    """Where recall looked and with what, as the strings a gap's `searched` carries (check 5)."""
    query = result["searched"]
    lines = ["%s (%d case(s) read)" % (result["store"], result["cases_read"]),
             "level 1, the signature: " + signature_text(query)]
    if all(f in query for f in LEVEL_2):
        lines.append("level 2, cause_class and executes alone: " + signature_text(query, LEVEL_2))
    else:
        lines.append("level 2 not searched: the signature states no cause_class"
                     if "cause_class" not in query else "level 2 not searched: the signature states no executes")
    return lines


def refs_and_gaps(result, what=None):
    """(case_refs, case_gaps) for a card: references that resolve in the store's index, or one gap."""
    if result["hits"]:
        refs = []
        for h in result["hits"]:
            ref = {"id": h["id"], "version": str(h["revision"]), "hash": h["hash"], "path": h["path"],
                   "note": "level %d (weight %d: %s); cue: %s" % (h["level"], h["weight"], ", ".join(h["matched"]), h["cue"])}
            refs.append(ref)
        return refs, []
    absent = result["store"].endswith(")")
    reason = "no case shares an identifying field with the signature"
    if all(f in result["searched"] for f in LEVEL_2):
        reason += ", and none shares its cause class and what it executes"
    gap = {
        "what": what or "a prior case for this signature",
        "searched": searched_lines(result),
        "reason": "no cases store to search" if absent else reason,
        "requires": "a case written from this agent's first incidents, validation failures or the person's interventions",
    }
    return [], [gap]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--signature", required=True, help="a JSON file holding a signature, or a card with one")
    ap.add_argument("--store", default=os.path.join("meta_agent", "cases"))
    args = ap.parse_args(argv)
    with open(args.signature, "r", encoding="utf-8") as f:
        data = json.load(f)
    signature = data.get("signature") if isinstance(data.get("signature"), dict) else data
    try:
        result = recall(signature, args.store)
    except RecallError as e:
        sys.stderr.write("recall: %s\n" % e)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
