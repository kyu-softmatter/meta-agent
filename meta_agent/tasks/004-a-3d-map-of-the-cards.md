# 004 — A 3D map of the cards

**Status:** done, 2026-11-04. Opened by the design seat on the person's words ("meta 시트로 004 진행", `../../docs/ideas/20261104.md`) after the person saw a 3D map of the cards drawn in the conversation without a library. The design seat extended check 18 to `graph.html` with three rejected fixtures `../../contracts/examples/rejected/check18_graph_*/` and an accepted example map (commit `6d8d91f`; expect-fail 54 of 57 before, 57 of 57 and 60 of 60 expected checks after). The meta seat added `src/wiki/graph_template.html` and the map to the renderer with three tests (commit `e5528a2`). Read off the runs: `python -m meta_agent.src.wiki` wrote `graph.html` with 27 nodes and 62 edges; the validator printed `0 failed` with the map judged; the suite ran 31 tests, OK. Opened from disk in a browser session: the map rotated in 3D, a click on a node and a search both listed its references in the side panel, and the 2D switch redrew it flat. Not checked: the dark colour scheme, and how the force layout scales past a few hundred nodes (it is quadratic; a WebGL library is the person's later decision).

**Seat:** `meta-office-20261029-1`, seated again in this session for this task. The extension of check 18 and its fixtures are the design seat's.

**Goal:** the wiki view of task 003 gains one more file, `wiki/graph.html`: a map of the same nodes and references that the pages hold, drawn in 3D with a 2D switch, that opens from disk with no network and no library. It is a view like the pages: regenerated, never edited, out of git.

**Inputs:**
- `../src/wiki/render.py` (the graph the pages are rendered from) and `tasks/003`.
- `../../plan.md` 3 (MP8: no dependency the request does not need), 5.2 (the wiki view).
- The map drawn in the conversation the same day: a 3D force layout, rotation by drag, zoom by wheel, perspective, a click that shows a card's references; colour by layer (lab, request, specification, build, artifact), a hollow mark for `draft`, a dashed line for `supersedes`.

**Data contract (what check 18 reads):** `graph.html` carries one block `<script id="wiki-graph" type="application/json">{"nodes": [{"id", "card", "status"}], "edges": [[source, relation, target]]}</script>`. Every node is a page of the same wiki and carries that page's record's `card` and `status` (`artifact` for an artifact); every edge is a link one of its two pages holds. The file loads nothing from outside (no `src` or `href` to another host).

**Done when (read off a run):**
- `python -m meta_agent.src.wiki` also writes `wiki/graph.html`; its data block holds exactly the renderer's nodes and edges, and a second run writes identical bytes.
- The map opens in a browser from disk, rotates, switches to 2D, and selecting a node lists its references (a browser session checks and says what it saw).
- Check 18 refuses a `graph.html` whose edge no page holds and one that loads an external script; each lands with a rejected fixture, watched accepted before the extension and rejected after.
- `python ../../contracts/validate.py` prints `0 failed`; the suite passes.

**Must not:** add a library, a CDN, a build step or a server; put a number, claim or relation in the map that no card holds; let the map edit anything; write outside `meta_agent/`.

**Report:** ten lines or fewer — what the renderer wrote, what the browser showed, the validator's verdict line, the fixtures.
