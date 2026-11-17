"""S2 Tool Understanding from documentation (plan.md 5.1).

The seat reads the tool's documentation and writes down claims; this module
holds them to the discipline: every claim has a kind, a basis and evidence,
an unknown says what would resolve it, and a claim whose basis is a binary
or the runtime is turned into a gap unless a person confirmed analysis
permission. It also derives CAPABILITIES.json for the bundle: only
observed and derived claims become capabilities.
"""
import re

from .. import cards

KINDS = ("observed", "derived", "inferred", "unknown")
NEEDS_PERMISSION = ("binary", "runtime")


def make_profile(intake, seat, now=None):
    created = cards.now_iso(now)
    rid = intake["rid"]
    tool = intake["tool"]
    card = cards.skeleton("tool_profile", "tp-" + rid.replace("req-", ""), seat, created, rid=rid)
    doc = tool.get("documentation")
    source_ref = "doc_" + tool["name"]
    card["tool"] = {"name": tool["name"], "kind": tool["kind"], "registry_id": tool.get("registry_id")}
    if doc:
        card["tool"]["source"] = doc
    for k in ("language", "version", "license"):
        if tool.get(k):
            card["tool"][k] = tool[k]
    permission = intake.get("analysis_permission")
    card["analysis_permission"] = permission
    claims, gaps = [], []
    for r in intake.get("tool_reading", []):
        kind = r["kind"]
        if kind not in KINDS:
            raise ValueError("claim kind %r is not one of %s" % (kind, KINDS))
        basis = r.get("basis", "documentation")
        if basis in NEEDS_PERMISSION and not permission:
            gaps.append({"what": r["claim"], "reason": "permission_required",
                         "requires": "analysis_permission confirmed by a person (granted_by, scope, basis, date)"})
            continue
        claim = {"claim": r["claim"], "kind": kind, "basis": basis,
                 "evidence": [{"source_ref": source_ref, "locus": l} for l in r.get("loci", [])]}
        if kind != "unknown" and not claim["evidence"]:
            raise ValueError("claim %r is %s but has no evidence" % (r["claim"], kind))
        if kind == "unknown":
            if not r.get("requires"):
                raise ValueError("unknown claim %r must say what would resolve it" % r["claim"])
            claim["requires"] = r["requires"]
            gaps.append({"what": r["claim"], "reason": r.get("gap_reason", "no_material"), "requires": r["requires"]})
        if r.get("limitations"):
            claim["limitations"] = r["limitations"]
        if r.get("capability"):
            claim["capability"] = r["capability"]
        claims.append(claim)
    card["claims"] = claims
    contracts = [t["contract"] for t in intake.get("tools") or []] or [intake.get("tool_contract") or {}]
    card["parameter_candidates"] = sorted({k for c in contracts for k in ((c.get("inputs") or {}).get("properties") or {})})
    card["gaps"] = gaps
    card["material_refs"] = list(tool.get("material_refs", []))
    return card


def names_in(text, names):
    """The names that stand in a text as words of their own (not inside another word or a hyphenated one)."""
    return sorted(n for n in set(names) if re.search(r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % re.escape(n), text or ""))


def capabilities(profile, agent_name, tools_here=None, held=None, held_items=None):
    """CAPABILITIES.json: observed and derived claims only; inferred to unverified, unknown to gaps.

    A bundle stands alone (MP2), so what the builder hands in decides what the file may name. `tools_here`
    are the names of the tools the bundle carries and `held` the skills the specification holds,
    [{skill, calls_tools}]. When `tools_here` is given, `source` is the name of the document the builder
    read and not its path in the builder's tree; `held` lists each held skill with the tools it would call;
    and a claim whose words name one of those tools, the bundle not carrying it, says so under `not_here`.
    `held_items` are the other items the specification holds (a request's own held[], a tool held for want
    of a safety row or a permission), each a string or {item, reason}; `held` lists them too, so that the
    file never says nothing is held while the specification holds something (test run 20261116-6).
    Without `tools_here` the file is written as before template v6 wrote it."""
    source = profile["tool"].get("source")
    held = list(held or [])
    absent = sorted({t for h in held for t in h.get("calls_tools") or []} - set(tools_here or []))
    if tools_here is not None and source:
        source = "the documentation of %s (%s), as the builder read it; the document is not in this directory" % (
            profile["tool"]["name"], str(source).replace("\\", "/").split("/")[-1])
    cap = {"schema_version": "0.1", "agent": agent_name, "tool": profile["tool"]["name"],
           "source": source, "observed": [], "derived": [], "unverified": [], "gaps": []}
    if tools_here is not None:
        cap["held"] = [{"skill": h["skill"], "calls_tools": sorted(h.get("calls_tools") or []),
                        "reason": "held by the builder until a person releases it; neither the skill nor the tools it "
                                  "would call are in this directory"} for h in held]
        for h in held_items or []:
            item = h if isinstance(h, dict) else {"item": h}
            cap["held"].append({"item": item["item"], "reason": item.get("reason") or
                                "held by the builder until a person releases it; it is not in this directory"})
    for c in profile["claims"]:
        item = {"claim": c["claim"], "capability": c.get("capability"),
                "evidence": [e.get("locus") for e in c.get("evidence", [])]}
        gone = names_in(c["claim"], absent) if tools_here is not None else []
        if gone:
            item["not_here"] = gone
        if c["kind"] in ("observed", "derived"):
            item["kind"] = c["kind"]
            cap[c["kind"]].append(item)
        elif c["kind"] == "inferred":
            item["limitations"] = c.get("limitations")
            cap["unverified"].append(item)
        else:
            cap["gaps"].append({"what": c["claim"], "requires": c.get("requires")})
    for g in profile.get("gaps", []):
        if not any(x["what"] == g["what"] for x in cap["gaps"]):
            cap["gaps"].append({"what": g["what"], "requires": g.get("requires"), "reason": g.get("reason")})
    return cap
