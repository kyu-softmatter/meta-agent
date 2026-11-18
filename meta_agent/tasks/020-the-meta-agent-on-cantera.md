# 020 — The Meta-Agent tested on Cantera

**Status:** open. Opened by `design-macbook-20261117-1` on the person's words (`../../docs/ideas/20261117.md`, "Tests on engines of other kinds": "GROMACS + top 4", "다른 세션들에서 각각 작성할거야. 실험계획을 남겨서 그들이 참고할 수 있게 하자."). Nobody holds it. It starts when the person opens a session for it and says so ("지금 말고 내가 말하면 실행").

**Seat:** one `meta-…` seat, seated by itself under the standing rule, holding this task alone (the person, 2026-11-17: "Stay meta, add role (Recommended)", `../../docs/ideas/20261117.md`). The design part, this card and the shared plan, has landed. A record that falls in the design role's paths (a check, a schema, a session skill, `testfolder.py`, `docs/ideas/`) goes to that role as a note.

**Goal:** a fresh clone session is given the person's request on Cantera (chemical equilibrium and an adiabatic flame temperature). What it does is collected, read against the questions of the shared plan, and set beside the HOOMD-blue tests and the other engines of this plan.

**Inputs:**
- `../eval/plans/engines-of-other-kinds.md`: why this engine, its link, the recommended brief, how a task runs, what a collection is read for, and what to watch for in Cantera.
- `../../docs/ideas/20261117.md`; `../../.claude/skills/test-outside-the-repository/SKILL.md`; `../eval/briefs/clone-rheotool-bare.txt` and `../eval/briefs/clone-hoomd-blue-bare.txt` as the form of a brief without answers.

**Done when (read off a run):** the brief `../eval/briefs/clone-cantera-bare.txt` is committed in the words the person confirmed; one run was made from the committed head with one unattended session in its clone, collected and removed, the collection still in the log folder; what it showed is in failure lines, cases, notes or new versions, each naming the run and the collection; this card says how far the clone went, what it asked and what it inferred, and what was watched and what was not.

**Must not:** write a brief or make a run before the person's word; put any answer in the brief that the person did not give for this engine; change a build or decide a threshold from the test; fix a fault in anything but a general mechanism shown on fixtures of two unrelated kinds; push.

## What run `chemical-kinetics/20261117-1` showed (read by `meta-macbook-20261117-4`, 2026-11-17)

Made at `cea2070` under the chemical-kinetics folders of the test and log folders, a clone with no bundle copies. One unattended session (`3f39b7b8`) ran on claude-opus-5-5 at high effort in the permission mode `auto`, with `../eval/briefs/clone-cantera-bare.txt`. Collection `collect-1` stays in the log folder. The run stands until the design role has read the collection.

- **How far:** all the way from material to validation, and no stop for a person's question. It seated itself (`-5`), carded the given page (`mat-20261117-010`, queued), read the tool from the documentation, recalled one level-2 case (`case-engine-adapter-environment-first-001`), wrote request `req-cantera-adiabatic-001` (intake revisions 1 and 2, a parameter sheet of the example's settings each citing the page, three tool contracts) and built `cantera-adiabatic/0001`. Interface pass, replay as expected, scientific `undecided` with no tolerance, nothing held. 5 commits, the clone's gate `VERDICT PASS … head=c55e835 … failed=0 pending=3`.
- **Asked or inferred:** it asked the person 0 times. It took the lab's confirmed execution permission and package source from `lab-kyu-softmatter` (as far as an engine on this computer; pixi from conda-forge) and decided nothing that is the person's. It left four questions in its report: the tolerance, where the bundle lands, what else it should run, and the page's registration and quotation.
- **Sources:** 0 web searches, 0 web fetches, 6 shell fetches. It read three sources it was not given and carded none of them (`chem-2`).
- **Environment:** it found for itself that Cantera is on conda-forge for this platform, citing the package record, and installed it with pixi in a temporary folder outside the repository for the adapters' trial. The repository's own gates gave scientific `not_run` with no environment.
- **Library skills:** none made, none run. Its `bounds_binding.json` says no skill of the library applies. The flame temperature is read from the engine and not computed again.
- **Generality:** one fault lies in a general mechanism of the meta role (`chem-1`, the agreement's unit). `chem-4` is in the designer. `chem-2`, `chem-5` and `chem-6` reach the design role (note `20261117-meta-macbook-20261117-4-2`). None was fixed from this test.
- **Watched for Cantera:** the mechanism file is not treated as a material with a source (`chem-3`). There is no over-building of a value the engine reports.
- **Not watched:** a session of the bundle alone; a control run with answers; whether the clone read the notes folder of earlier runs (it was run from the command line, which gives none); the trial's printed values, which are evidence for the adapters and enter no card.

## What run `chemical-kinetics/20261117-2` showed: the bundle standing alone (read by `meta-macbook-20261117-4`, 2026-11-17)

Made with `testfolder.py make --no-clone --source` from the clone of run `20261117-1`. The copy of `cantera-adiabatic/0001` has a digest equal to the build's. One unattended session (`39e49172`) ran on claude-opus-5-5 at high effort, from the collection, with `../eval/briefs/cantera-adiabatic.txt` (`9fccb19`). The request in that brief is this seat's wording; the person asked for the test. Collection `collect-1` stays in the log folder.

- **Start task:** done as written. The gate self-check and replay passed. `validate_tasks` said scientific `not_run` before the install; the bundle's own `install_cantera` made its environment with pixi; then scientific `undecided`. It asked the person 0 times, ran no library skill and loaded `run-skill` and `classify-knowledge` at the points they name.
- **The person's request:** it answered with one call of `adiabatic_flame_point` at the example's settings from `envelope/parameters.json`, and said that is what it did. It kept "room temperature" and "atmospheric" as questions instead of choosing a reading, and named the lower edge of the gas phase's thermodynamic data, read from the tool's output, as something the person should know before choosing.
- **Faults:** `bundle-cantera-1` to `-4`, and `chem-3-correction`, which narrows `chem-3`.
- **Not watched:** a request outside the example's settings; a run whose input falls outside the thermodynamic data's range. The session's own statement of its effort ("low") disagrees with the collection, which records high; the collection is the record.
