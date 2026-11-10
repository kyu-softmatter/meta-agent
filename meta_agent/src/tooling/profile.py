"""S2 Tool Understanding from documentation (plan.md 5.1).

The seat reads the tool's documentation and writes down claims; this module
holds them to the discipline: every claim has a kind, a basis and evidence,
an unknown says what would resolve it, and a claim whose basis is a binary
or the runtime is turned into a gap unless a person confirmed analysis
permission. It also derives CAPABILITIES.json for the bundle: only
observed and derived claims become capabilities.
"""
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


def capabilities(profile, agent_name):
    """CAPABILITIES.json: observed and derived claims only; inferred to unverified, unknown to gaps."""
    cap = {"schema_version": "0.1", "agent": agent_name, "tool": profile["tool"]["name"],
           "source": profile["tool"].get("source"), "observed": [], "derived": [], "unverified": [], "gaps": []}
    for c in profile["claims"]:
        item = {"claim": c["claim"], "capability": c.get("capability"),
                "evidence": [e.get("locus") for e in c.get("evidence", [])]}
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
