"""S0 Steps 1 to 3: the adaptive questionnaire, the configuration proposal,
and the record of the person's answers (plan.md 5.0).

Step 1 asks only what the discovery report left `unknown`, plus the policy
fields, which are asked whatever the report says. Step 2 proposes a
`lab_profile` from the report. Step 3 writes `confirmed` only for the
fields a person answered, with `confirmed_by: human` and the date.
"""
import os

from . import cards
from .bank import BANK, DERIVED, FIELDS, GROUP_NAMES, by_field
from .discover import CONTRACTS

PROFILE_GROUPS = {
    "hardware": ["gpu", "hpc"],
    "software_env": ["language", "os", "package_manager"],
    "conventions": ["unit_system", "research_kind", "methods"],
    "operational_constraints": ["licenses", "execution_permission"],
    "collaboration": ["first_agent", "existing_agents", "bridge", "mode"],
    "policy": ["working_mode", "approval_mode", "publication_scope", "execution_permission",
               "external_transfer_of_private_code"],
}
PROFILE_TOP = ["preferred_engines", "preferred_instruments", "existing_code", "existing_data",
               "validated_workflows", "gui_preference"]


def policy_fields():
    kinds = cards.load_json(os.path.join(CONTRACTS, "claim_kinds.json"))
    return list(kinds["policy_fields"])


def _state(fields, f):
    leaf = fields.get(f) or {}
    return leaf.get("state", "unknown"), leaf.get("value")


def condition_blocks(cond, fields):
    """Return (blocked, reason) for a bank condition given the discovery fields."""
    if cond is None:
        return False, None
    if cond == "needs_existing_agents":
        st, val = _state(fields, "collaboration.first_agent")
        if st == "unknown":
            return True, "deferred until the first-agent answer; carried as held"
        if val is True:
            return True, "a first agent has no existing agents to collaborate with"
        return False, None
    if cond == "simulation_possible":
        st, val = _state(fields, "conventions.research_kind")
        if st != "unknown" and isinstance(val, list) and "simulation" not in val:
            return True, "the research kind excludes simulation"
        return False, None
    raise ValueError("unknown condition %r" % cond)


def _loci(leaf):
    return ", ".join(sorted({e.get("locus", "?") for e in leaf.get("evidence", [])}))


def ask(disc, seat, now=None):
    """Step 1: build the onboarding_record with the questions to put to the person."""
    created = cards.now_iso(now)
    policy = set(policy_fields())
    fields = disc["fields"]
    questions, skipped, held = [], [], []
    for field, group, text, cond in BANK:
        st, _ = _state(fields, field)
        if field in policy:
            questions.append({"field": field, "group": group, "question": text,
                              "state_at_ask": "policy", "answer": None, "answered_by": None, "asked_at": created})
            continue
        blocked, reason = condition_blocks(cond, fields)
        if blocked:
            skipped.append({"field": field, "reason": reason, "basis": "condition"})
            if st == "unknown":
                held.append(field)
            continue
        if st == "confirmed":
            skipped.append({"field": field, "reason": "already confirmed by a person", "basis": "answered_earlier"})
        elif st == "inferred":
            skipped.append({"field": field,
                            "reason": "inferred from %s; shown as a recommendation in Step 2" % _loci(fields[field]),
                            "basis": "inferred"})
        else:
            questions.append({"field": field, "group": group, "question": text,
                              "state_at_ask": "unknown", "answer": None, "answered_by": None, "asked_at": created})
    for derived, source in DERIVED.items():
        skipped.append({"field": derived, "reason": "filled from the answer to %s" % source, "basis": "condition"})
    card = cards.skeleton("onboarding_record", "ob-" + disc["lab_id"], seat, created)
    card["lab_id"] = disc["lab_id"]
    card["discovery_ref"] = disc["id"]
    card["questions"] = questions
    card["skipped"] = skipped
    card["held"] = held
    n_pol = sum(1 for q in questions if q["state_at_ask"] == "policy")
    card["note"] = ("Step one: %d question(s), %d of them policy, %d unknown; %d skipped; %d held. "
                    "Answers are empty until a person writes them." % (len(questions), n_pol, len(questions) - n_pol, len(skipped), len(held)))
    return card


def set_leaf(profile, dotted, leaf):
    parts = dotted.split(".")
    node = profile
    for p in parts[:-1]:
        node = node.setdefault(p, {})
    node[parts[-1]] = leaf


def get_leaf(profile, dotted):
    node = profile
    for p in dotted.split("."):
        if not isinstance(node, dict) or p not in node:
            return None
        node = node[p]
    return node


def propose(disc, record, seat, now=None):
    """Step 2: the draft lab_profile, every leaf copied from the discovery report."""
    created = cards.now_iso(now)
    fields = disc["fields"]
    card = cards.skeleton("lab_profile", disc["lab_id"], seat, created)
    card["lab_id"] = disc["lab_id"]
    for f in PROFILE_TOP:
        card[f] = dict(fields.get(f) or {"value": None, "state": "unknown"})
    for g, leaves in PROFILE_GROUPS.items():
        card[g] = {}
        for l in leaves:
            card[g][l] = dict(fields.get(g + "." + l) or {"value": None, "state": "unknown"})
    card["held"] = [f for f in FIELDS if (fields.get(f) or {}).get("state", "unknown") == "unknown"]
    card["note"] = ("Step two proposal: inferred values are recommendations with evidence; "
                    "unknown values are held until a person answers. Nothing here is confirmed.")
    return card


def apply_answers(record, profile, answers, answered_by, date, seat, now=None):
    """Step 3: new revisions of the record and the profile carrying the person's answers.

    `answers` maps field -> value. Only those fields become confirmed. Anything the
    person did not answer keeps its state. Returns (record_v2, profile_v2).
    """
    if answered_by != "human":
        raise ValueError("answers must come from a person (answered_by: human), got %r" % answered_by)
    created = cards.now_iso(now)
    rec = dict(record)
    rec["revision"] = record["revision"] + 1
    rec["supersedes"] = record["id"]
    rec["author"] = seat
    rec["created_at"] = created
    rec["questions"] = []
    answered = set()
    for q in record["questions"]:
        q2 = dict(q)
        if q["field"] in answers:
            q2["answer"] = answers[q["field"]]
            q2["answered_by"] = answered_by
            answered.add(q["field"])
        rec["questions"].append(q2)
    prof = _deepcopy(profile)
    prof["revision"] = profile["revision"] + 1
    prof["supersedes"] = profile["id"]
    prof["author"] = seat
    prof["created_at"] = created
    for field, value in answers.items():
        if field not in FIELDS:
            continue
        set_leaf(prof, field, {"value": value, "state": "confirmed", "confirmed_by": answered_by, "date": date})
        for derived, source in DERIVED.items():
            if source == field:
                set_leaf(prof, derived, {"value": value, "state": "confirmed", "confirmed_by": answered_by, "date": date})
    prof["held"] = [f for f in FIELDS if (get_leaf(prof, f) or {}).get("state", "unknown") == "unknown"]
    rec["held"] = [f for f in record["held"] if (get_leaf(prof, f) or {}).get("state") == "unknown"]
    open_q = [q["field"] for q in rec["questions"] if q["answered_by"] is None]
    policy = policy_fields()
    all_policy = all((get_leaf(prof, f) or {}).get("state") == "confirmed" for f in policy)
    rec["status"] = "done" if not open_q else "draft"
    prof["status"] = "validated" if all_policy else "draft"
    rec["note"] = "Step three: %d answer(s) recorded from %s on %s; %d question(s) still open." % (
        len(answered), answered_by, date, len(open_q))
    prof["note"] = ("Step three: %d field(s) confirmed by %s on %s. %s" % (
        len(answers), answered_by, date,
        "All policy fields are confirmed; a build may reference this revision."
        if all_policy else "Policy fields are still open; no build may reference this profile (check 15)."))
    return rec, prof


def _deepcopy(obj):
    import json
    return json.loads(json.dumps(obj))


def proposal_markdown(disc, record, profile, engines_registry=None):
    """A human-readable Step 2 proposal. It carries no bare numbers so that
    check 3 can judge the folder: counts are written in words or omitted."""
    bank = by_field()
    fields = disc["fields"]
    lines = ["# Onboarding proposal: %s" % disc["lab_id"], ""]
    lines.append("What Step zero read, what it inferred, what it could not, and what it asks. "
                 "Inferred values are recommendations with evidence; only a person's answer makes a value `confirmed`.")
    lines.append("")
    lines.append("## Inputs read")
    lines.append("")
    for i in disc["inputs"]:
        tag = i["kind"]
        c = ("@" + i["commit"]) if i.get("commit") else ""
        lines.append("- %s: `%s%s`" % (tag, i["ref"], c))
    lines.append("")
    lines.append("## Inferred (recommendations)")
    lines.append("")
    any_inf = False
    for f in FIELDS:
        leaf = fields.get(f) or {}
        if leaf.get("state") == "inferred":
            any_inf = True
            lines.append("- `%s` = `%s` - from %s%s" % (f, _plain(leaf.get("value")), _loci(leaf),
                                                       (" - " + leaf["note"]) if leaf.get("note") else ""))
    if not any_inf:
        lines.append("- nothing could be inferred: no material was given")
    lines.append("")
    lines.append("## Asked (unknown, or policy)")
    lines.append("")
    for q in record["questions"]:
        g = q.get("group")
        lines.append("- `%s` (%s, %s): %s" % (q["field"], GROUP_NAMES.get(g, "?"), q["state_at_ask"], q["question"]))
    lines.append("")
    if record["skipped"]:
        lines.append("## Skipped, with the reason")
        lines.append("")
        for s in record["skipped"]:
            lines.append("- `%s` (%s): %s" % (s["field"], s["basis"], s["reason"]))
        lines.append("")
    if profile.get("held"):
        lines.append("## Held until answered")
        lines.append("")
        for h in profile["held"]:
            lines.append("- `%s`" % h)
        lines.append("")
    eng = (fields.get("preferred_engines") or {}).get("value") or []
    if eng and engines_registry:
        lines.append("## Registry entries that match the engines found")
        lines.append("")
        for e in engines_registry.get("engines", []):
            if e["id"] in eng:
                lines.append("- `%s` %s: methods %s; interface %s; licence %s; verified: %s" % (
                    e["id"], e.get("name", ""), ", ".join(e.get("methods", [])), e.get("interface", "?"),
                    e.get("license", "?"), "no" if e.get("verified") is None else "yes"))
        lines.append("")
    lines.append("## What happens next")
    lines.append("")
    lines.append("The person answers the asked questions in a small JSON file (`answered_by: human`, a date, "
                 "and `answers` by field) and the Meta-Agent runs Step three, which writes a new revision of the "
                 "record and of the profile with those answers `confirmed`. Nothing is built from this profile "
                 "while a policy field is open.")
    lines.append("")
    return "\n".join(lines)


def _plain(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)
