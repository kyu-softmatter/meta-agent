# 017 — The Meta-Agent tested on GROMACS

**Status:** open. Opened by `design-macbook-20261117-1` on the person's words (`../../docs/ideas/20261117.md`, "Tests on engines of other kinds": "GROMACS + top 4", "다른 세션들에서 각각 작성할거야. 실험계획을 남겨서 그들이 참고할 수 있게 하자."). Nobody holds it. It starts when the person opens a session for it and says so ("지금 말고 내가 말하면 실행").

**Seat:** one `meta-…` seat, seated by itself under the standing rule, holding this task alone (the person, 2026-11-17: "Yes, meta for both", `../../docs/ideas/20261117.md`). The design part, this card and the shared plan, has landed. A record that falls in the design role's paths (a check, a schema, a session skill, `testfolder.py`, `docs/ideas/`) goes to that role as a note.

**Goal:** a fresh clone session is given the person's request on GROMACS (molecular dynamics of a protein in water). What it does is collected, read against the questions of the shared plan, and set beside the HOOMD-blue tests and the other engines of this plan.

**Inputs:**
- `../eval/plans/engines-of-other-kinds.md`: why this engine, its link, the recommended brief, how a task runs, what a collection is read for, and what to watch for in GROMACS.
- `../../docs/ideas/20261117.md`; `../../.claude/skills/test-outside-the-repository/SKILL.md`; `../eval/briefs/clone-rheotool-bare.txt` and `../eval/briefs/clone-hoomd-blue-bare.txt` as the form of a brief without answers.

**Done when (read off a run):** the brief `../eval/briefs/clone-gromacs-bare.txt` is committed in the words the person confirmed; one run was made from the committed head with one unattended session in its clone, collected and removed, the collection still in the log folder; what it showed is in failure lines, cases, notes or new versions, each naming the run and the collection; this card says how far the clone went, what it asked and what it inferred, and what was watched and what was not.

**Must not:** write a brief or make a run before the person's word; put any answer in the brief that the person did not give for this engine; change a build or decide a threshold from the test; fix a fault in anything but a general mechanism shown on fixtures of two unrelated kinds; push.

## Begun (2026-11-17, `meta-macbook-20261117-8`)

The person opened this session with "그로맥스 시뮬레이션 생성 및 테스트 / 폴더가 없다면 폴더를 만들고 검증" ("create and test the GROMACS simulation; if the folder does not exist, make it and check"). Both category folders, `molecular-dynamics` under the test folder and under the log folder, already stood and were empty; none was made.

Asked by this seat, the person answered with the buttons this seat wrote:

- on the brief (role line `meta`, the link `http://www.mdtutorials.com/gmx/lysozyme/`, a third party's tutorial, "이것을 자동화 하고싶어", the lines on carrying through and reporting, no answers): "Yes, this bare brief (Recommended)";
- on timing, two other test sessions working at the time (`cfd/20261117-14`, `chemical-kinetics/20261117-12`): "Start now, in parallel (Recommended)";
- on level: "opus-5-5, high (Recommended)".

So the brief is `../eval/briefs/clone-gromacs-bare.txt`; the run is made now under the `molecular-dynamics` folders; the clone session runs on `claude-opus-5-5` at `high`. Not settled: the source and prefix of the third party's tutorial, whether GROMACS may be installed and run on this computer, and every tolerance; these are left to the clone to ask.

## Run `molecular-dynamics/20261117-16`, read from `collect-1`

One unattended session (`bc74eb79`, `claude-opus-5-5` at `high`, permission mode `auto`) in the clone made at `b065854`; it ended by itself. Clone head `0b3c5a7`, 11 commits, nothing uncommitted, the clone's gate `VERDICT PASS ... head=0b3c5a7 ... failed=0 pending=6`. The collection says 145 calls, 3 in error, 0 questions put to the person in the session, 0 web searches, 0 web fetches, 10 shell fetches, 1 material card added (queued), none found by a seat, no library skill run through a bundle's runner.

**How far it went:** materials (the tutorial, 11 pages and 5 `.mdp` files, read and hashed, not copied; three material cards: the tutorial queued, two pages of the GROMACS 2025.2 manual), intake in three revisions, the physical system, one library skill (`solute_box_distance_min_from_cutoff@v1`, from the manual's cut-off restriction), a parameter sheet written by the runner (box distance at least 1.2 nm), two tool contracts (`install_environment`, `prepare_system`), and build `gromacs-lysozyme/0001`: interface tasks pass, replay as expected, the three scientific tasks `not_run` because the structure and the force field are not in the bundle. It stopped after the set-up steps. Minimisation, the two equilibrations, production and analysis are not built: their settings need units the registry lacks (gmx-1) and the person's answers. The stop is partly a question to the person and partly a fault in the registry.

**Asked or inferred:** five questions put to the person in the intake: data hosts (RCSB, CHARMM36, the tutorial's files), force field and water model (recommends CHARMM36 and TIP3P), whether the tutorial may be registered and quoted and what kind of source it is, tolerances and criteria for "settled", run length and GROMACS version (recommends 2025.2). No policy or permission was decided by itself. The version it recommended was fixed in the build's install adapter while still a question (gmx-7).

**Sources:** it searched for the maker's documentation by itself (the GROMACS 2025.2 manual and online help) and wrote two pages as material cards with the `spec:` prefix, as the person decided on 2026-11-17 for the maker's documentation. The third party's tutorial stays queued, its kind put to the person. The scientific tasks name the tutorial's counts as their reference, with no tolerance (null) and `not_run`.

**Environment:** it found for itself that GROMACS installs with pixi from conda-forge on this computer, made the environment in the run folder, and read `gmx --version` (`2025.2-conda_forge`); a trial of `prepare_system` on a hand-written peptide went through pdb2gmx to genion. The fetch of PDB 1AKI was refused by the permission mode (gmx-2).

**Generality:** gmx-4 is cfd-2 again and gmx-5 is ctrl-pair-6 again, each now on a second kind. gmx-1 is a gap in a general vocabulary, not shaped by HOOMD-blue. gmx-6 makes the run not blind: the clone read this card and the plan in its eighth and ninth calls.

**Watched:** the said text, the calls, the patch of the clone, the collection's counts. **Not watched:** the transcript line by line; the built bundle in a session of its own (not run); whether the GROMACS trial's printed counts were right (a model's numbers, they enter no card). Failure lines gmx-1 to gmx-9 are in `../failures.jsonl`. The run stands until the design role has read the collection.

## The bundle standing alone, run `molecular-dynamics/20261117-19`, read from `collect-1`

The person asked for it ("Yes, test bundle", 2026-11-17). `gromacs-lysozyme/0001` was copied with `make --no-clone --source` from the clone of run `20261117-16`, its digest equal to its build card's. Brief `../eval/briefs/gromacs-lysozyme.txt`, in the form of `hoomd-hpmc.txt`; the request in it is this seat's wording. One unattended session (`80f6c074`), `claude-opus-5-5` at `high` by the session record (the session named its effort as low; gmx-14). 15 calls, 1 in error; skills `run-skill` and `classify-knowledge`; the library skill `solute_box_distance_min_from_cutoff@v1` run once through the bundle's runner; no web search or fetch.

What it did: task 001's three commands printed `gate: self-check ok`, `replay: 1 item(s), 1 as expected, 0 not; OK` and `gates: interface pass, scientific not_run; overall not_run`. It called `install_environment` as task 001 says, and the bundle made its own GROMACS environment (the tool reported `2025.2-conda_forge`). On the request it called `prepare_system`, which refused with `PREPARE-UNAVAILABLE-001 (unavailable)` because the structure is not there. It wrote two lines in the bundle's `failures.jsonl` naming what is missing (PDB 1AKI; the CHARMM36 force field, which the installed GROMACS does not ship; the box distance, whose row is null) and whose step each is (the person's). It gave no count and did not present the tutorial's reference counts as a result. The folder was enough to show what blocks the request, not to answer it.

Faults it showed: gmx-10 to gmx-14 in `../failures.jsonl` (the CAPABILITIES source line, a permission field that is not in the bundle, em-10 again, CLAUDE.md and task 001 not matching the build, cfd-12 again). Not watched: whether the bundle's counts would match the tutorial's once the structure and force field are given; that waits for the person's answers. Run `20261117-19` stands with run `20261117-16` until the design role has read their collections.
