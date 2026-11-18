# 024 — The Cantera control test, with the person's answers

**Status:** done on 2026-11-17, last commit of the work `77d0b05`, marked by `design-macbook-20261117-1` on the ask of `meta-macbook-20261117-4` (`../inbox/seats/20261117-meta-macbook-20261117-4-10.json`): both runs read by both roles and removed, their collections kept. Opened by `design-macbook-20261117-1` on 2026-11-17 on the ask of `meta-macbook-20261117-4` (`../inbox/seats/20261117-meta-macbook-20261117-4-7.json`) and the person's words recorded in `../../docs/ideas/20261117.md` ("The Cantera test's answers, and a control test with them"). It follows `020`, which is done. Nobody holds it.

**Seat:** one `meta-…` seat, holding this task alone; `meta-macbook-20261117-4` ran `020` and asked for it. A record in the design role's paths goes to that role as a note.

**Goal:** a fresh clone session given `../eval/briefs/clone-cantera.txt`, the request with the person's answers, is set beside a bare clone made from the same head, and both beside the bare test of `020` (run `chemical-kinetics/20261117-1`). What the answers changed, and what the system did by itself, can then be told apart, as the HOOMD-blue control test did for that engine.

**Inputs:** `../eval/plans/engines-of-other-kinds.md`; `020-the-meta-agent-on-cantera.md` and the collections of its runs in the chemical-kinetics log folder; `../../.claude/skills/test-outside-the-repository/SKILL.md`.

**Done when (read off the runs):** a pair of runs in the chemical-kinetics folders, made from one committed head (the person, 2026-11-17: "Both at same head (Recommended)"), one with `../eval/briefs/clone-cantera.txt` and one with `../eval/briefs/clone-cantera-bare.txt`, each with one unattended session on `claude-opus-5-5` at `high`, were collected and removed, their collections kept. They are runs `chemical-kinetics/20261117-12` and `-13`, at `a4fcc35`. What it showed is in failure lines, cases, notes or new versions, each naming the run and the collection. This card compares the two and says what was watched and what was not.

**Must not:** change the brief from what the person confirmed; decide a tolerance beyond the person's; push.

## What the pair showed (read by `meta-macbook-20261117-4`, 2026-11-17)

Runs `chemical-kinetics/20261117-12`, given `../eval/briefs/clone-cantera.txt`, and `-13`, given `../eval/briefs/clone-cantera-bare.txt`. Both were made at `a4fcc35`, before either session started, and each had one unattended session on claude-opus-5-5 at high effort, in that order. Collections: `collect-1` of each, in the chemical-kinetics log folder.

| | `-12`, with answers | `-13`, bare |
|---|---|---|
| how far | material to a validated build, `cantera-adiabatic/0001`; it stops at the hand-over | the same |
| scientific | `pass`: sci-1 and sci-2 judged against the person's tolerance in K | `undecided`: no tolerance applied |
| asked the person | 0 times, with 2 left open in the report (landing place, the page's registration) | 0 times, with 4 left open (tolerance, landing place and registration, a bundle test, notes) |
| the person's 1 K in the record | used as the brief's answer | read in `docs/ideas/20261117.md`, not applied, and asked whether it holds (`ctrl-pair-1`) |
| sources a seat found | three, each a card (the API page, the licence, the conda-forge record) | two, each a card (the data files `gri30.yaml`, `graphite.yaml`) |
| library skills | none made, none run | none made, none run |
| calls, calls in error | 123, 5 | 100, 3 |
| clone's gate | `VERDICT PASS … head=4fa14dd … failed=0 pending=3` | `VERDICT PASS … head=d3f02cb … failed=0 pending=3` |

- **What the answers changed:** the scientific verdict, and with it the overall verdict and the build's status. The answered clone also wrote the person's words into its intake. Neither clone stopped for a question, and they built the same three tools.
- **What the system changed since the bare test at `cea2070` (`020`):** both pairs show the agreement in K (`chem-1`), the engine's registry id (`chem-5`) and seat-found sources carded (`chem-2`, `chem-3`). That last change may come from the records the clones read as much as from the skills (`ctrl-pair-7`).
- **Faults:** `ctrl-pair-1` to `-7`. Those in the design role's paths are asked in note `20261117-meta-macbook-20261117-4-9`.
- **Not watched:** a session of either bundle standing alone; the 48 sweep points between the two ends; whether the order of the two sessions mattered.
- **Left outside the runs:** the test sessions' scratch folders under `/tmp` (`ctrl-pair-2`). Their removal is the person's step, since the sessions' permission mode refused it.

## Removed, and what landed (`meta-macbook-20261117-4`, 2026-11-17)

The design role read both collections (reply `20261117-design-macbook-20261117-1-16`). Runs `-12` and `-13` were removed with `testfolder.py wipe --sessions`, each with its one session transcript; their collections stay in the chemical-kinetics log folder.

- **Landed by the design role:** `ctrl-pair-2` (`9927906`), `ctrl-pair-3` (`44a1476`), `ctrl-pair-6` (`efb21ae`).
- **Open:**
  - `ctrl-pair-1`, put to the person;
  - `ctrl-pair-4`;
  - `ctrl-pair-5`, which stays with `chem-3`.
- **Waiting for the person's word:** the sixteen scratch folders left under `/tmp` before `9927906`.
