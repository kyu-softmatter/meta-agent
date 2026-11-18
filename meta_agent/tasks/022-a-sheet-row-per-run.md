# 022 — A parameter sheet that bounds every run, not one row of a name

**Status:** open. Opened by `design-macbook-20261117-1` on 2026-11-17 from failure `em-2` (run `electromagnetics/20261117-1`, collect-1, the Meep clone without answers; ask `../inbox/seats/20261117-meta-macbook-20261117-3-3.json`), under the person's word that this seat takes the design role's asks from the test sessions (`../../docs/ideas/20261117.md`). Nobody holds it.

**Seat:** the schema of the parameter sheet, `../../contracts/tools/sheets.py` and checks 4 and 19 are the design seat's, and land first. The Designer that writes sheets (`../src/designer.py`) and the template text are a meta seat's.

**Goal:** a request whose tutorial runs the engine several times, each with its own value of a parameter (four Meep runs, each with a resolution), gets a sheet on which every run's row is bounded by the skills that apply to it, and the gate can tell which run a row belongs to.

**What was seen:** the clone's `parameter_sheet.json` held rows of the same name more than once (`ring_source_frequency`, `resolution`, …), one set per run. Only the first `resolution` carried bounds; the later rows of the same name carried none. The gate passed the sheet.

**Inputs:** `../eval/plans/engines-of-other-kinds.md`; the collection named above, in the log folder; `../../.claude/skills/estimate-parameter-ranges/SKILL.md` step 5 (a swept parameter is a row per point); `../../contracts/tools/sheets.py`; plan.md 5.3, 14-30, 14-32.

**Method (recommended, not settled):** a row carries the run or the point it belongs to (a `run` or `point` key), a row's name is unique within one run, a bound skill that applies to a name applies to it in every run, and check 19 fails a run whose row of a bounded name has no bound. Fixtures of two unrelated kinds, one of them not rheology, before it counts.

**Done when:** the schema, `sheets.py` and check 19 say the above, each new rule landed with its rejected fixture watched failing first; `python contracts/validate.py` prints `VERDICT PASS`; the meta part has the Designer write a row per run.

**Must not:** change a sheet that is a record (a change is a new version); decide a threshold.
