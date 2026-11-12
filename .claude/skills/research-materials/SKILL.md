---
name: research-materials
description: Take in the materials the person gives (a link, a manual, a paper, a repository) and search what is written about a tool, a method or a quantity, as sources that are read and never recalled. Use when a row appears in the materials inbox or a file is dropped, when the person gives a link in conversation, when a request needs a formula, a value or a published measurement, and before any number is taken from literature.
---

# Research the materials

The person gives the location. You fill the rest and the person confirms. Access is read-only and anonymous.

## Intake of one material

1. A new row in `meta_agent/inbox/materials/LINKS.md`, or a new file in `meta_agent/inbox/materials/drop/`. A link given in conversation is copied into `LINKS.md` first.
2. Make `meta_agent/inbox/materials/<YYYYMMDD>-<slug>/`, move the file in, and write `MATERIAL.json` (`contracts/schemas/material.schema.json`): `added_by: human`, `author` your seat, exactly one of `url` or `path`.
3. Fill `kind`, `about` and `license_note` as `inferred`, each with its evidence. What you cannot fill stays `unknown`.
4. Fetch a URL and record `retrieved_at` and `content_hash`. Behind a login or a credential it is not fetched: the card is `held` with `permission_required`.
5. Keep a raw copy only when `may_quote` is `true`. Otherwise keep the hash and the place in the source.
6. Write the card's id back into the row. Show the person what you filled and ask one or a few questions. `registered` is their word, never yours.

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
