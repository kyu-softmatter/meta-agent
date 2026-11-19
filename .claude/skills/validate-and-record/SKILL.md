---
name: validate-and-record
description: Validate a built agent on its interface and its science, record what failed and why as cases, and recall earlier cases before a card is written. Use after a bundle is built, when a run, a build or a check fails, when a cause is found, and at the start of a request to see whether the same situation was met before.
---

# Validate, and record what was learned

## Validate a bundle

1. **Both sections.** Interface tasks (a call, a response, an error, a configuration passed on) and scientific tasks (against a reference result that has an entry or a source).
2. **Run the gate on the bundle:** `python contracts/validate.py --bundle <bundle folder>`.
3. **Each task is** `pass`, `fail`, `not_run` or `undecided`. A task that was not run is not a pass. A scientific task without a tolerance is undecided. A tolerance is the person's, or one a library skill derives under the person's standing rule (the reference's stated uncertainty, else the span [lowest, highest] of the values or stated error ranges in suitable materials (published studies of the same or a similar system on any topic, and the maker's manuals), each read through `research-materials` as a material card, with `classify-knowledge` writing how its system and quantity compare with the task's, and carried by the task as entries under `measure.materials`, else the larger of half a unit in its last printed digit and the run's own numerical error, from two resolutions, where the estimate enters three times over, or from a series' standard error), recorded with the rule and the skill; the person's own overrides it.
4. **The bundle stands alone.** Its replay item is handled by a fresh session in the bundle's folder, with the Meta-Agent absent.
5. Write the `validation_report`. Every number in it is read off a run.

## Recall before writing

Search for earlier cases before a goal, a parameter axis or a safety axis is written:

```
python -m meta_agent.src.cases.recall --signature <file>
```

It is deterministic: the same signature against the same store gives the same result. A hit goes on the card as a reference; a miss is a gap that names where you looked.

## Record

- **A failure** is one line in `meta_agent/failures.jsonl`, append only. A bundle session's line that says what it needed (an uncertainty, a criterion, a judgement) is a candidate skill of the next build: the task card names it, and `build-library-skill` says which kind it is.
- **A case** (`contracts/schemas/case.schema.json`) carries its cue, its condition tags, what would falsify it, and its counts. Its cause is `observed`, `suspected` or `confirmed`; `confirmed` needs a run or a commit as evidence.
- **Index the store** after adding a case: `python contracts/tools/cases.py index meta_agent/cases`.
- **A case is re-ranked, never deleted.** A superseded one stays and names what replaced it.
- **Promotion is computed and lands nothing:** `python -m meta_agent.src.cases.promote`. The number of supporting cases it needs is the person's; without it the answer is undecided.

## Never

Call a task passed that was not run. Choose a tolerance by judgement, or derive one where the rule yields nothing. Delete or rewrite a case. Say a change helped because it was adopted: one run, or several changes at once, shows nothing.

Reference: `plan.md 5.1` (validate), `plan.md 5.4`, `plan.md 11`.
