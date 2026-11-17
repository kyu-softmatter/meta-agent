---
name: build-library-skill
description: Turn one relation or one procedure into a library skill, as source code with a manifest and worked cases from its source. Use when a quantity must be computed (a bound, an estimate, a value, an analysis of data) and no library skill gives it, when a calculation is found in a script or a card writer, and when a procedure over a device is to be made repeatable.
---

# Build a library skill

Every calculation of a quantity is a library skill, the approximate ones as much as the exact ones. A library skill is not a session skill: it is source code that the runner runs, and no session loads it when it starts.

## The folder

`meta_agent/skills/<kind>/<id>@v<n>/` holds four things:

- `SKILL.md`: what a model reads to choose it. Front matter `name` and `description`; then what it gives, what it needs, when it applies, and what it never does.
- `skill.json`: the manifest code reads (`contracts/schemas/skill.schema.json`).
- `scripts`, a folder: the source. The manifest's `entry` names one function.
- `cases.json`: worked cases with their inputs and the expected output.

The kinds, and the side effect each may declare, are in `contracts/skill_kinds.json`.

## Do this

1. **Read the source.** The relation comes from a paper, a manual or a standard that was read, and the manifest cites it. A relation you remember is not a source.
2. **One relation, one skill.** A window is two skills, a maximum and a minimum. An approximate and an exact relation for one quantity are two skills.
3. **Write a pure function.** No file, no network, no device, and only the imports the gate allows. A device is reached only through the tools the manifest names.
4. **Hold no judgement in the code.** A margin, a multiple, a tolerance or a limit is an input with its own source.
5. **Say where it holds.** For an estimate, the manifest's `validity` says what is neglected and over what conditions; an estimate gives a range.
6. **Give worked cases from the cited source,** values that the source itself states. At least one must run. Where the source gives the relation and states no value of it, a case is worked by hand: its arithmetic is written out in the case's `worked`, short enough to check by eye, and the manifest's note says no value of the source stands behind it. A row that is the value of a source's expression is then `computed` by that skill, not a literature value. A skill of kind `bound` gives one output, the bound or the value of its parameter, and carries two cases that run with inputs that differ: a second quantity is a second skill, and one case cannot tell a relation from a constant.
7. **Check it, index, then run the library's tests:**
   ```
   python contracts/tools/skills.py check <skill folder>
   python contracts/tools/skills.py run-cases <skill folder>
   python -m meta_agent.src.skills index
   python -m unittest discover -s meta_agent/tests -t .
   ```
   The check says what the gate will say of the skill alone. The tests say what the code that uses the library needs of it; a new skill is not landed while one of them fails.
8. **A change is the next version.** A landed folder is never edited; write the next version's folder beside it.

## Who lands it

A model may draft a skill in the middle of a request. A seat lands it, with its worked case, before any value it gives is used. A skill that changes a device's state is `held` until the person releases it.

## Never

Land a skill without a running case. Put a limit or a safety value in a skill. Edit a landed version. Write one session skill per library skill.

Reference: `plan.md 14-30`, `plan.md 14-31`, `plan.md 14-32`.
