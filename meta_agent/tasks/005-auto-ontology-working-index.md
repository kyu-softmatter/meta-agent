# 005 — auto-ontology-mcp as M2's working index

**Status:** open, 2026-11-07. Opened by the design seat on the person's words ("고고" to the coexistence recommendation, `../../docs/ideas/20261107.md`). Nothing is installed or written yet; `meta_agent/knowledge/` does not exist.

**Seat:** a `meta-…` seat the person seats for this task, for `src/` and `tests/`. The pin in `../../tools.lock.json`, the installer in `../../bootstrap.py`, the entry in `../../.mcp.json` and the check on `tools.lock.json` (plan.md 14-23(c)) are the design seat's and land first, in their own commit, so that the meta seat's run starts from a computer `bootstrap.py check` calls complete.

**Goal:** give the Meta-Agent a working index for the materials the person drops, and make S3 recall read it. The model reads a material at intake and saves its passages, concepts and source into auto-ontology-mcp's knowledge store through MCP; S3 recall searches the store with FTS5 and hands candidates to the `knowledge_brief`. The cards stay the record; the store is a candidate layer, out of git, like `wiki/`. This replaces the word-match recall of `src/knowledge/brief.py` and is the first piece of M2 (plan.md 5.2, 12).

**What is settled (the person, 2026-11-07):** coexistence with the wiki view, which is not touched; the store as a candidate layer only; the SQL half of the server unused (MP8); lexical search only, so plan.md 13 and 14-7 stand.

**Inputs:**
- `../../plan.md` 5.0 (materials inbox), 5.1 S3, 5.2, 6.3 (numbers and claims), 13, 14-7, 14-23, 14-25.
- `../../docs/ideas/20261105.md` (licensed material stays the person's download; `may_quote`), `../../docs/ideas/20261107.md`.
- The server: https://github.com/gogoymh/auto-ontology-mcp at commit `286ebc4bc7736e6435a2ac44d6bb77ad5ba63080` (read 2026-11-07; Apache-2.0; no release). Its README names the tools: `save_passages`, `save_concept`, `define_entity`, `add_records`, `search_text`, `get_source`, `list_terms`, `recent_changes`, `export_wiki`, `export_ontology`, `import_ontology`, and the prompt `remember`.
- `src/knowledge/brief.py` and `src/intake/`; `../../contracts/schemas/knowledge_brief.schema.json`; `inbox/materials/README.md`.
- A fixture material under `tests/fixtures/`: a short text you write (an engine's documentation page, a few paragraphs with two named quantities), never a copyrighted PDF.

**Method (recommended, not settled):**
- Design seat: `tools.lock.json` gains `auto_ontology_mcp` with `source`, `commit`, `license`, `python: 3.12`, `runner: uvx`; `bootstrap.py install auto-ontology --yes` runs `uv tool install git+<source>@<commit>` into the tools home (reuse `find_uv`; `uv` itself stays the person's step, as for harness2) and `bootstrap.py check` reports it; `bootstrap.py run auto-ontology mcp` starts it with its data directory under `meta_agent/knowledge/.index/` (gitignored); `.mcp.json` gains the server through that command. The check on `tools.lock.json` (14-23(c)) lands here with its rejected fixture, since this is the first new pin.
- Meta seat, intake: when a material in `drop/` or `LINKS.md` is read, the model saves the source (`get_source` must return the path or URL the person gave, with the date), then passages and concepts; the `MATERIAL.json` queue card records the store's source id. What is saved is bounded by the material's `may_quote`; without it, concepts and the model's own one-line summaries only, no passages.
- Meta seat, recall: `src/knowledge/brief.py` reads the store **directly as SQLite** with the standard library (one module, `src/knowledge/index_store.py`, that knows the pinned schema and fails with a named error if a table is missing), runs FTS5 queries built from the goal's `knowledge_needs[]` and `parameter_scope[]`, and writes each hit into the brief as a candidate: `{kind: inferred, source_ref: <store source id>, locus: <passage id>, text: <the hit>}`. No MCP call at recall time, so the same input gives the same output. A need with no hit is a `gap` that names the query. Nothing from the store is written as a number.
- Tests: the fixture material is saved through the store's own Python API or a prepared `knowledge.sqlite` committed under `tests/fixtures/` (small, generated once, its generating script beside it); recall finds the two named quantities as candidates and records a gap for a third need; a card written from the brief passes `validate.py`; the schema check fails on a store with a renamed table.

**Done when (read off a run):**
- `python bootstrap.py check` prints `ok` for auto-ontology-mcp at the pinned commit; `python contracts/validate.py --expect-fail` rejects the new `tools.lock.json` fixture.
- `python -m meta_agent.src.designer` on a fixture request writes a `knowledge_brief` whose candidates came from the store (the card names the store's source id and passage id) and whose gaps name what was searched; the card passes `validate.py` with `0 failed`.
- The brief carries no number from the store; every candidate is `inferred`.
- A second run on the same store and goal writes an identical brief.
- `meta_agent/knowledge/.index/` is ignored by git and `git status` is clean after a run.
- `PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .` is OK.

**Must not:** write an entry, a number or a grade from the store; put a passage of a material without `may_quote` into the store; commit the store; add an embedding model, a vector index or a crawler (plan.md 13); use the server's SQL tools; touch `src/wiki/` or `tasks/003`–`004`; write outside `meta_agent/` (meta seat) or inside `meta_agent/src/` (design seat).

**Report:** ten lines or fewer — the pin and the check's id, the number of passages and concepts the fixture produced, the candidates and gaps in the brief, the verdict line, the test count.
