"""S1 Intake: the agent_goal from the person's paragraph (plan.md 5.1).

The model makes no numbers here: `numbers` stays empty and the card is
refused if any field would carry one. S3 attaches what recall found, or
where it looked, as a second revision.
"""
import re

from .. import cards

GOAL_FIELDS = ["purpose", "science_task", "tool", "methods", "executes", "must_not", "knowledge_needs",
               "parameter_scope", "destination", "priorities", "lab_profile_ref", "gui_choice",
               "analysis_permission", "requested_by"]
BARE_NUMBER = re.compile(r"(?<![\w./:+-])[-+]?\d+(?:\.\d+)?(?![\w/:%-])")


def make_goal(intake, seat, now=None):
    created = cards.now_iso(now)
    rid = intake["rid"]
    card = cards.skeleton("agent_goal", "goal-" + rid.replace("req-", ""), seat, created, rid=rid)
    tool = intake["tool"]
    card["purpose"] = intake["paragraph"].strip()
    card["science_task"] = intake["science_task"]
    card["tool"] = {"name": tool["name"], "kind": tool["kind"], "registry_id": tool.get("registry_id"),
                    "material_refs": list(tool.get("material_refs", []))}
    card["methods"] = list(intake.get("methods", []))
    card["executes"] = intake.get("executes", "none")
    card["must_not"] = list(intake.get("must_not", []))
    card["knowledge_needs"] = list(intake.get("knowledge_needs", []))
    card["parameter_scope"] = list(intake.get("parameter_scope", []))
    card["destination"] = intake["destination"]
    card["priorities"] = list(intake.get("priorities", []))
    card["lab_profile_ref"] = intake["lab_profile_ref"]
    card["gui_choice"] = intake.get("gui_choice", "undecided")
    card["analysis_permission"] = intake.get("analysis_permission")
    card["requested_by"] = intake.get("requested_by", "human")
    if intake.get("note"):
        card["note"] = intake["note"]
    for bad in numbers_in(card):
        raise ValueError("agent_goal must carry no number; found %r in %s" % bad[::-1])
    return card


def numbers_in(card):
    """Bare numbers in the goal's free-text fields: the model writes none (plan.md 5.1)."""
    out = []
    for f in ("purpose", "science_task", "destination"):
        for m in BARE_NUMBER.finditer(card.get(f) or ""):
            out.append((f, m.group(0)))
    for f in ("must_not", "knowledge_needs", "parameter_scope", "priorities"):
        for item in card.get(f) or []:
            for m in BARE_NUMBER.finditer(str(item)):
                out.append((f, m.group(0)))
    return out


def attach_recall(goal, kb_refs, kb_gaps, case_refs, case_gaps, seat, now=None, status="validated"):
    """S3's result on the goal: a second revision with refs, or gaps naming where it looked."""
    v2 = dict(goal)
    v2["revision"] = goal["revision"] + 1
    v2["supersedes"] = goal["id"]
    v2["author"] = seat
    v2["created_at"] = cards.now_iso(now)
    v2["kb_refs"] = list(kb_refs)
    v2["kb_gaps"] = list(kb_gaps)
    v2["case_refs"] = list(case_refs)
    v2["case_gaps"] = list(case_gaps)
    v2["status"] = status
    if goal.get("knowledge_needs") and not (kb_refs or kb_gaps):
        raise ValueError("S3 must leave kb_refs or kb_gaps on a goal with knowledge needs")
    if not (case_refs or case_gaps):
        raise ValueError("S3 must leave case_refs or case_gaps on the goal")
    return v2
