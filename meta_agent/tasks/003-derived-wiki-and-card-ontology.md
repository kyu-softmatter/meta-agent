# 003 — A derived wiki view and an ontology of the cards

**Status:** proposed, 2026-11-04, by the design seat on the person's words (`../../docs/ideas/20261104.md`). Waiting for the person's word on the four decisions below; nothing is built in the repository yet. A prototype ran the same day outside the repository on this tree at `7ffa87a`: it found 27 nodes (25 card revisions and 2 artifacts, the template and the bundle), 62 references among them, 13 node types and 14 relation names, wrote one Obsidian-style page per node, and wrote an RDF/XML ontology that parses as XML. It was not loaded into Ontology Playground.

**Seat:** a `meta-…` seat the person seats for this task (the M1 seat was seated for M1). The new check and its fixture are the design seat's.

**Goal:** make the relation network of the record visible without creating a second store. The cards stay the record; the wiki and the ontology are views rendered from them, the way `knowledge/index.json` is.

How the two pieces map onto the plan:

| LLM wiki | here |
|---|---|
| raw sources, never edited | `inbox/materials/`, `knowledge/sources/raw/` |
| wiki pages | distillation notes and entries (cards), rendered as pages |
| schema file | `CLAUDE.md`, `../../contracts/` |
| `index.md` | `knowledge/index.json` |
| `log.md` | `failures.jsonl`, the harness logs, git history |
| ingest | F1: material, source record, distillation, entries (plan.md 5.0, 5.2) |
| query | S3 recall and the `knowledge_brief` |
| lint | `../../contracts/validate.py`; contradictions are `relations.conflict_with`, orphans are "a case no card cites" (plan.md 1.4) |

Ontology Playground is the viewer and editor for the ontology half: the card types and their references now, and a lab domain ontology later if the person wants one.

**Decisions only the person makes:**

1. **Derived or authored.** Recommended: the wiki is rendered from cards and never edited by a model. An authored wiki, as in the gist, rewrites pages in place, which breaks the append-only records (check 7) and makes two stores that can disagree (plan.md 1.4).
2. **Which ontology.** (a) The card ontology, derivable today from the schemas and the references. (b) A rheology domain ontology (material, sample, instrument, method, measurement, model, parameter) that `kb_entry.subject` would use. (b) is a lab decision; the Meta-Agent may propose terms, each `inferred`, and only the person confirms them.
3. **Committed or local.** Recommended: render on demand into `meta_agent/wiki/` and keep it out of git, so the view can never drift from the cards in a commit. The alternative is to commit it as generated, like `index.json`.
4. **Ontology Playground's place.** Recommended: use it at its hosted address or from a clone outside this repository, loading the exported file. It is MIT, so bundling is allowed, but no request needs a JavaScript build here (MP8).

**Inputs:**
- `../../plan.md` 1.4, 3 (MP7, MP8), 5.2, 6, 8; `../../contracts/records.json`; the `relations` block of `../../contracts/schemas/kb_entry.schema.json` (`supports`, `refutes`, `supersedes`, `conflict_with`).
- Every card under `meta_agent/` outside bundles, templates, `src/` and `tests/`.

**Method (as prototyped):** a node is one revision of a card, `<id>@r<revision>`; a bare id points at its latest revision; a revision N > 1 gets a `supersedes` edge to N − 1. An edge is any string field whose value is another card's id, a `lab_id` that names a `lab_profile`, or a file name of a card in the same folder; `template_version` and `bundle_path` become artifact nodes. The ontology has one `owl:Class` per card type and one `owl:ObjectProperty` per relation with its domain and range.

**Done when (read off a run):**
- `python -m meta_agent.src.wiki` renders one page per node and an `index.md`, every `[[link]]` names a rendered page, and a second run on the same tree writes byte-identical files.
- The exported ontology loads in Ontology Playground and shows the card types and relations (the person or a browser session checks, and says which).
- A new check, numbered by the design seat, refuses a wiki page whose link or number is not in the card it renders; it lands with its rejected fixture, watched failing first.
- `python ../../contracts/validate.py` prints `0 failed`.

**Must not:** put a number, claim or relation in a page that no card holds; let a model edit a page; mark a domain term `confirmed`; add a dependency, a JavaScript build or a web service; write outside `meta_agent/`.

**Found by the prototype, for the person:** `tool_profile` and `knowledge_brief` of `req-echo-001` reference no other card; they are tied to the request by folder only. Whether such cards should name their goal is a schema question for the design seat.

**Report:** ten lines or fewer — pages and edges rendered, whether the ontology loaded, the new check's id and fixture, the validator's verdict line.
