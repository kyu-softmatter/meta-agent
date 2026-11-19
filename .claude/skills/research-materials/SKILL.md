---
name: research-materials
description: Take in the materials the person gives (a link, a manual, a paper, a repository) and search what is written about a tool, a method or a quantity, as sources that are read and never recalled. Use when a row appears in the materials inbox or a file is dropped, when the person gives a link in conversation, when a request needs a formula, a value or a published measurement, and before any number is taken from literature.
---

# Research the materials

The person gives a location, or you find one. You fill the rest and the person confirms. Access is read-only and anonymous.

Load `classify-knowledge` before the first value, statement or data file of this part enters a card, a sheet or a skill's inputs, if it is not loaded in this session yet: it binds at every stage (`meta_agent/CLAUDE.md`), and a value that entered before it was loaded has been placed from memory of it.

## Intake of one material

1. A new row in `meta_agent/inbox/materials/LINKS.md`, or a new file in `meta_agent/inbox/materials/drop/`. A link given in conversation is copied into `LINKS.md` first.
2. Make `meta_agent/inbox/materials/<YYYYMMDD>-<slug>/`, move the file in, and write `MATERIAL.json` (`contracts/schemas/material.schema.json`): `added_by: human`, `author` your seat, exactly one of `url` or `path`.
3. Fill `kind`, `about` and `license_note` as `inferred`, each with its evidence. What you cannot fill stays `unknown`. `about.role` takes only a value listed under `material_roles` in `contracts/claim_kinds.json`; a material that fits none of them is `unknown`, and a sentence there is refused by the gate.
4. Fetch a URL and record `retrieved_at` and `content_hash`. Behind a login or a credential it is not fetched: the card is `held` with `permission_required`.
5. Keep a raw copy only when `may_quote` is `true`. Otherwise keep the hash and the place in the source.
6. Write the card's id back into the row. Show the person what you filled and ask one or a few questions. `registered` is their word, never yours.

## Finding what was not given

- **Search when a request or a skill needs a source it was not given:** the relation a library skill implements, a value a row needs, a published measurement to compare a result with, the reference page of a tool's class. Search by the quantity, the method or the tool alone; a query carries no lab data and no private code (`meta_agent/CLAUDE.md`).
- **Prefer the source closest to the claim:** the original paper or a textbook that derives it, then a review, then the tool's own documentation, then a curated database. An encyclopedia page or a forum answer is a way to find those, never the source a skill or a row cites.
- **A relation needs no citation only where it is a definition,** and then the definition is named with where it is defined.
- **Every source you read and use is a material card** you write (`added_by` and `author` your seat, `entry_path: search`), `queued`, with what it was found for and how it was found. Design and build do not wait for the person to register it. Registering it and quoting from it stay the person's word: when the person registers it, the card's `state_reason` says where that word is recorded.
- **Look for something published to compare with** before a request ends at theory alone: a measurement, a figure or a table of a paper that ran the same system, as a scientific task's reference.
- **Where that reference states no uncertainty, look for what others allow,** before the tolerance falls to the last printed digit and the run's own error: other values of the quantity, or error ranges stated for it, in published studies of the same or a similar system on any topic and in the maker's manuals. This holds for any quantity of any engine or instrument. Each value or range is handed to the scientific task as an entry under `measure.materials`, a map from the stated field to a list of entries. An entry names its `material`, says in `compares` how that material's system, quantity and engine compare with the task's (`classify-knowledge`), and gives either `value` or `low` and `high`. Where the source states an uncertainty beside a value, the entry gives it too, and `compares` says what kind of uncertainty it is; the value then enters the span widened by it. A search that finds nothing is written as a gap with where you looked.

## Searching the literature

- Read the source itself: the paper, the manual, the database page. A formula or a value you remember is a model's number, which is `E6` and enters nothing.
- For each claim keep the source, the place in it, the conditions it holds under (model, instrument, units, valid range) and its `value_kind`: `measured`, `correlation`, `computed`, `predicted`, `literature` or `estimated`. The grade is derived from `contracts/grades.json`, never stated.
- Assess in a note: candidate, then critique, then refinement. Only a refined claim becomes an entry; the critique stays in the note.
- A value that differs from one already held is a conflict and both stay. Grounds that are too thin are a gap, not a value.
- What is missing is written as missing, with where you looked. Never fill it.
- A relation that gives a quantity is handed on as a library skill with a worked case from this source: use `build-library-skill`.

## What exists today

- The material card, its schema and check, and the inbox folders.
- `meta_agent/src/knowledge/brief.py` writes the `knowledge_brief` of a request, with its gaps.
- Not built: the knowledge store's folders for sources, notes and entries, and the command that adds a material. Until they are, a source's reading lives in the request's intake and in the manifest of the skill that cites it.

## Never

Use a stored login or a credential. Copy licensed text into the repository. Mark a material `registered` or confirm a license yourself. Let design or a build wait for material.

Reference: `plan.md 5.0` (materials inbox), `plan.md 5.2`.
