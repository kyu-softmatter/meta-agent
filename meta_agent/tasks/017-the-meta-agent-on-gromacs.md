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

## What the design role answered, and run `20261117-16` removed

The design role read `molecular-dynamics/20261117-16` `collect-1` and replied (note `20261117-design-macbook-20261117-1-18`, `c4ef5b5`): gmx-1, the GROMACS units are in `contracts/units.json` (`9954f02`); gmx-5, the rehearsal copy is a git clone (`efb21ae`); gmx-9, a session's TMPDIR is inside the run (`9927906`); gmx-2 stays open under `tasks/023`. Then, by a message from that seat, the person decided that a test clone is blind (`250a7cc`, `docs/ideas/20261117.md`): `testfolder.py make` leaves out `meta_agent/eval/`, `docs/ideas/` and the cards, rows and claims of the tasks that run tests, unless `--not-blind` is given on the person's word. This answers gmx-6 for later runs; run `20261117-16` itself was not blind.

Run `20261117-16` was removed with `wipe --sessions` (a second collection, `collect-2`, taken first; one transcript removed). Build `gromacs-lysozyme/0001` was in that clone only; its files remain in `collect-1/items/repo/changes.patch` and as the copy in run `20261117-19`. Run `20261117-19` stands until the design role has read its collection (gmx-14 is in that role's paths).

Still open for this task: the person's answers to the clone's five questions, and a second round from a blind clone once they are given.

## Run `20261117-19` removed

The design role read `molecular-dynamics/20261117-19` `collect-1` (note `20261117-design-macbook-20261117-1-21`, `36e0105`): the run may be wiped; gmx-14 is cfd-12 on a second kind and is put to the person; gmx-10 to gmx-13 are the meta role's, gmx-12 waiting on the template version asked in `20261117-design-macbook-20261117-1-14`. The run was removed with `wipe --sessions` (`collect-2` taken first; one transcript removed). No run of this task stands; both runs' collections stay in the log folder under `molecular-dynamics/`. Build `gromacs-lysozyme/0001` now exists only as `collect-1/items/repo/changes.patch` of run `20261117-16`.

Still open: the person's answers to the clone's five questions; a second round from a blind clone once they are given; gmx-3, gmx-4, gmx-7, gmx-8 and gmx-10 to gmx-13 in the meta role's paths.

## The person answers the clone's five questions (2026-11-18)

In the cleanup session (`local_2567d051`), shown the five questions of the clone of run `20261117-16`, the person said "모두 그렇다" ("all of them, yes"); that session relayed it here and recorded nothing. Asked then by this seat directly, with the buttons this seat wrote:

- "Does it mean: the agent may fetch from files.rcsb.org (PDB 1AKI), mackerell.umaryland.edu (CHARMM36) and www.mdtutorials.com (the tutorial's .mdp files); the force field is CHARMM36 with TIP3P water; GROMACS 2025.2; and the tutorial may be registered and quoted?" — "Yes, all of that";
- what kind of source the tutorial's values are, it being one author's page and not the maker's documentation — "prior_run (E3)";
- how the second round compares with the tutorial — "Counts exact, averages: diff only" (set-up counts of atoms, water molecules, ions and the box match exactly; for averages the difference is reported with no verdict);
- how far the second round runs GROMACS on this computer — "Tutorial's own lengths" (minimisation, NVT, NPT and production as the tutorial's `.mdp` files give them).

Not settled by these words: whether the three hosts hold for every agent of this lab or for the GROMACS agent alone (asked next).

## The person's follow-up in the cleanup session (2026-11-18)

On the three parts with no value (the kind of source, the tolerances and the criterion for "settled", the run length), the person said in the cleanup session "모두 세션 판단대로" ("all as the session judges"); that session relayed it here. The values had already been put to the person by this seat directly, each named, and chosen by the person's own buttons (above): the tutorial's values are `prior_run` (E3); set-up counts (atoms, water molecules, ions, box) are compared exactly, and for averages the value, the tutorial's and their difference are reported with no verdict, so no tolerance and no criterion for "settled" is chosen and that judgement stays the person's; the runs go to the tutorial's own lengths as its `.mdp` files give them. No value was chosen by a seat. The round-two brief `../eval/briefs/clone-gromacs.txt` carries those answers and no other.

## Round two, run `molecular-dynamics/20261117-23`, read from `collect-1`

A blind clone made at `5cb850e` (lab profile v6 in it; `meta_agent/eval/`, `docs/ideas/` and the test tasks left out), brief `../eval/briefs/clone-gromacs.txt`, one unattended session (`f0d5e2f6`, `claude-opus-5-5` at `high`). It ended by itself. Clone head `3ba16bc`, 5 commits, nothing uncommitted, the clone's gate `VERDICT PASS ... head=3ba16bc ... failed=0 pending=1`. The collection says 150 calls, 4 in error, 0 questions put to the person in the session, 10 shell fetches, 1 material card added and `registered` (the person's word in the brief).

**How far it went:** through to a build: `gromacs-lysozyme/0001` (clone), seven tools: install (GROMACS 2025.2, pixi, conda-forge), a fetch of 1AKI, the CHARMM36 archive and the tutorial's five `.mdp` files from the three hosts of profile v6, the set-up (pdb2gmx, editconf, solvate, genion), the four stages with the tutorial's files unchanged (each call stops at a `max_hours` the caller gives and continues from its checkpoint), and three readers (energy averages, RMSD, radius of gyration). Both gates pass on the tree and on the bundle alone. The scientific tasks are `not_run` at build, because the inputs are fetched by the built agent, not by the builder. The rehearsal was a git clone (efb21ae). Its scratch was under the run's TMPDIR (9927906).

**Asked or inferred:** the person's answers were taken from the brief and not asked again. The set-up counts carry tolerance 0 `chosen_by: human` with the person's words quoted. The averages carry no tolerance and are reported as value, reference and difference. The tutorial's values have the source `prior_run:mat-20261118-001@…`. The protein's net charge was also given an exact tolerance, which the person did not name (gmx-19). Two questions for the person: the atom count and the box, which the tutorial does not state; and whether hydrogen bonds and secondary structure are reported (the tutorial gives them only as rough words and a plot). It also asked the design role which value kind a setting taken from a prior run carries (it wrote the box distance as `measured`, with a note).

**Environment and trial:** it tried each tool once through the bundle's runner under TMPDIR: the install, the fetch, the set-up, minimisation, a full NVT and NPT (the NPT over four calls from its checkpoint, about an hour of engine time) and a short part of production, then the readers. The trial's printed values entered no card (the patch has none of them). Its report to the person gives one of them, a water count that differs by one from the tutorial's, as a likely failure of the exact rule at the real run; that is a model's reading of a trial and decides nothing. Whether a trial may run whole equilibration stages to prove the checkpoint continuation is not settled by any rule this seat found; it is watched here, not called a fault.

**Generality:** gmx-18 is gmx-10 again; gmx-20 is cfd-15 again. Like this seat (gmx-15), the clone found test_designer.DataSources failing at its head after profile v6 and fixed it in its own clone; the fix in this repository is `8fc3dfa`.

**Watched:** the said text, the failure lines and tolerances in the patch, the collection's counts. **Not watched:** the transcript line by line; the built bundle standing alone in a session of its own; a real run of the workflow (production would take on the order of a day of engine time on this computer, by the clone's reading of mdrun's log). Failure lines gmx-16 to gmx-20 are in `../failures.jsonl`. The run stands until the design role has read the collection.

## Round two's bundle standing alone, run `molecular-dynamics/20261118-1`, read from `collect-1`

The person asked for it ("Yes, test bundle", 2026-11-18). `gromacs-lysozyme/0001` copied with `make --no-clone --source` from the clone of run `20261117-23`, its digest equal to its build card's. Brief `../eval/briefs/v2_gromacs-lysozyme.txt` (this seat's wording of the request; set-up only, so the session ends in minutes). One unattended session (`bb50707f`), `claude-opus-5-5` at `high` by the session record. 15 calls, 1 in error (the session's own shell quoting); skills `run-skill` and `classify-knowledge`; `measurement_error@v1` run twice through the bundle's runner; no web search or fetch by the session itself.

What it did: task 001's commands printed `gate: self-check ok`, `replay: 2 item(s), 2 as expected, 0 not; OK` and, before the inputs, `gates: interface pass, scientific not_run; overall not_run`. It installed GROMACS through the bundle's tool (`2025.2-conda_forge`, mixed precision, no GPU). On the request it fetched the inputs through `fetch_inputs` (the gate opened the fetch by the hosts of profile v6; the session says the 7 files match the builder's copy) and prepared the system. Read off the bundle's own validation, against the person's tolerance of 0: `fail sci-1 outside the tolerance: waters (measured 12589, stated 12588), waters_after_solvate (measured 12597, stated 12596)` and `pass sci-2 … agreement 0.0` (chloride 8, net charge 8 e); final line `gates: interface pass, scientific fail; overall fail`. It compared nothing for the atom count and the box, for want of a tutorial value, gave the cause of the extra water as unknown, and put the one-water difference to the person as the person's call.

Faults it showed: gmx-21 to gmx-23 in `../failures.jsonl`. Not watched: the stages after the set-up, which wait for the person's answer and for the person's word on a run of about a day of engine time. Runs `20261117-23` and `20261118-1` stand until the design role has read their collections.

## The person answers what the bundle of round two left (2026-11-18)

Asked by this seat, with the buttons this seat wrote:

- on the water count, one more than the tutorial's after solvate and after genion, against the exact rule: "Keep exact; record fail" (the tolerance stays 0; run `20261118-1` is recorded as a fail of sci-1, and the agent goes on);
- on the atom count and the box, which the tutorial does not state: "Find a reference" (the Meta-Agent looks for a published value to compare with, and it is then put to the person);
- on hydrogen bonds and secondary structure: "Yes, report, no verdict" (added in a later build, reported beside the tutorial's rough words with no verdict);
- on a full run of the tutorial, of the order of a day of engine time on this computer: "Yes, run it in the background".

What these settle: the exact rule holds and sci-1 of run `20261118-1` is a fail on the record; a later build (round three) searches for a reference for the atom count and the box and reports hydrogen bonds and secondary structure with no verdict; the bundle of round two runs the whole tutorial in an unattended session. Not settled: the `max_hours` of each stage call (asked next).

## What the design role answered on round two, and run `20261117-23` removed

Notes `8a10345` and `fbe282b`, from `design-macbook-20261117-1`: gmx-16 landed in `analyse-lab-environment` (`426dd87`); gmx-17 landed in checks 3 and B6 (`0e97474`); gmx-20 stays, the failure lines being kept on the person's "Keep failure lines"; a setting taken from a prior run has the source `prior_run:<run>`, with the value kind it had in that run, graded E3; isolated test sessions (`be69e2d`) answer gmx-14. The person's answers of 2026-11-18 are in `../../docs/ideas/20261118.md` (`0c78685`), and the earlier ones ("모두 그렇다", the hosts' scope, "모두 세션 판단대로") in `../../docs/ideas/20261117.md`, as answered by `design-macbook-20261117-3`.

Run `20261117-23` was removed with `wipe --sessions` (`collect-2` taken first; one transcript removed). Its build stays only as `collect-1/items/repo/changes.patch` and as the copy in run `20261118-1`, where the full run of the tutorial is under way.

## The standing rule for tolerances (2026-11-18), as it touches this task

The person set a standing rule (`../../docs/ideas/20261118.md`, "Tolerances by a standing rule", `c2499f2`): a scientific task's tolerance is the reference's stated uncertainty, else half a unit in the last digit it prints, derived by a library skill (`chosen_by: rule`); a tolerance the person gave overrides it. For this task: the exact comparison of the set-up counts stands (the person's, and after the fail "Keep exact; record fail"); the averages stay value, reference and difference with no verdict, which is also the person's own word ("Counts exact, averages: diff only"). Whether the rule should replace either of those in round three is the person's and is not asked by this seat on its own. The mechanism (a library skill, the template's `validate_tasks.py`, the Designer) is asked of the meta role in `76ba4c5`, with no task; it is general work and not this task's.

Asked by this seat "Should the standing tolerance rule replace the GROMACS exact counts in round three?", the person answered with the button this seat wrote (2026-11-18):

> No, keep exact

So in round three and after, the set-up counts of the GROMACS agent keep tolerance 0, chosen by the person, and the standing rule does not replace it. The averages stay value, reference and difference with no verdict (the person's "Counts exact, averages: diff only"); this answer was asked of the counts alone.

## Clean-up on the person's word (2026-11-18)

Asked through the cleanup session (`design-macbook-20261117-3`, `2949b75`) to remove what this test built once its part is finished. Run `20261118-1` stands: its unattended session is running the full tutorial (`gmx mdrun` was working when this was written), and the design role has not read that run's second session. It is removed with `wipe --sessions` once the session ends and both roles have read it. Runs `20261117-16`, `20261117-19` and `20261117-23` were removed earlier. Outside any run, the only scratch folder this seat left (a rehearsal copy of the lab profile in its own scratch folder) is removed. Builds and records in the repository stay.

## The full run, stopped on the person's word (2026-11-18)

The person said, relayed by the cleanup session (`design-macbook-20261117-3`): "그로맥스 현재 튜토리얼 진행분 까지만 진행하고 정지" ("run GROMACS only as far as the tutorial has progressed now, and stop"). At 12:46 local time this seat froze the unattended session (`16513229`) so it could start no further call, sent `mdrun` a TERM signal (its log: "Received the TERM signal, stopping within 200 steps", then "Writing checkpoint, step 112480"), and then ended the session. The session's record therefore says FAILED TO RUN; it was stopped, it did not fail. Collected as `collect-2` of run `20261118-1`.

How far the tutorial got, read from the session's own text and the engine's log: minimisation converged (the engine reported 490 steps); NVT ran all 50000 steps in one call; NPT ran all 250000 steps over five one-hour calls, each continuing from its checkpoint; production stopped at step 112480 of 5000000 (about 225 ps of 10 ns), with a checkpoint from which it could continue. The session had begun reading the finished stages (`read_stage`, `read_energy_averages`, kept in the bundle's `runs/session-2`) but had not reported them; no average is reported here. The engine's speed fell from call to call while other test sessions ran beside it (the session read a load average of about 70), which is how NPT took five calls.

Watched: the session's text, the engine's log, the stop. Not watched: the averages and structural readings, which the session had not reported; production past 225 ps. Run `20261118-1` stands, stopped, until the design role has read `collect-2`.

## Production resumed on the person's word (2026-11-19)

The person said, in the status-report session (`local_2f39e32b`, no seat), relayed here: "그로맥스 계속 진행" ("continue GROMACS"). Production of run `20261118-1` is resumed from its checkpoint (`md_0_10.cpt`, step 112480 of 5000000) by a fresh unattended session in the bundle's folder, brief `../eval/briefs/gromacs-lysozyme-resume.txt`, on `claude-opus-5-5` at `high`, one-hour calls (the person's "1 hour per call"). Its earlier stages are not run again.

## The water count: the person asks for what others allow (2026-11-19)

In the status-report session (`local_2f39e32b`, no seat), about the table of round two's standalone result (run `20261118-1`: water after solvate 12597 against 12596, after genion 12589 against 12588; chloride and charge equal), the person said, relayed here: "하나정도 차이는 맞다고 봐야할ㄷ스" (read by that session as a typo for "봐야할듯": "a difference of about one should be regarded as correct, I think"). This differs from the person's earlier "No, keep exact". Asked by this seat directly how to record it (water counts only ±1, every count ±1, or keep exact), the person answered in their own words:

> 시스템마다 다를텐데, 논문을 찾아보고 보통 다른 사람들은 어느정도로 오차를 허용하는지 확인

("It will differ from system to system; look up papers and check how much error other people usually allow.")

What the words settle: this seat searches the published sources for how far a set-up count (the water molecules a solvation adds, and the counts after ions) is allowed to differ between runs, versions or machines, writes each source it uses as a `queued` material card, and puts what it found to the person as a recommendation. Not settled: the tolerance itself, which stays the person's; until the person chooses, the exact rule of "No, keep exact" stands and sci-1 of run `20261118-1` stays a fail.

What this seat found (2026-11-19), from sources read and written as `queued` files under `../inbox/materials/20261119-*`:

- No paper or manual this seat found states a tolerance for the number of water molecules a solvation adds. The reproducibility literature it searched (a reporting checklist for MD, a cross-engine reproducibility study) speaks of replicates and of observables, not of set-up counts. This is a search that found nothing, not a finding that nothing exists.
- The maker (gmx solvate help, GROMACS 2025.2): the count follows from the van der Waals radii database, `-scale`, `-radius` and the solvent's coordinate file, so it changes with any of them.
- The maker ("Managing long simulations"): precision, the number of cores, the processor and the compiler change a run's output; an individual trajectory is not reproducible, while its observables converge and are.
- The tutorial's author (its solvation page): minor variations in computer architecture and compilers may give very slight differences in the number of water molecules added in that step. No number is given.
- The standing rule of 2026-11-18 would give half a unit of the tutorial's last printed digit (the count is printed as a whole number), which a difference of one water still fails; the person's own tolerance overrides the rule in any case.

So the recommendation put to the person is a choice among forms, not a value from a source.

Asked the form, the person answered: "논문도 너가 찾아봐야지" ("you should look up papers too"). This seat searched again for papers (system preparation across tools and machines, cross-platform reproducibility of GROMACS, acceptance criteria for a set-up's water count) and read the article form of the tutorial, Lemkul's LiveCoMS paper for GROMACS-2025 (`../inbox/materials/20261119-lemkul-livecoms-gromacs-tutorials/`). No paper found states a tolerance on the number of water molecules a solvation adds. A study of membrane simulations says only that the number of water molecules or ions can be hard to control exactly when a system is assembled by hand, and that there is no strict standard for the volume of the aqueous phase. The LiveCoMS article says the chloride ions' placement differs in every system and states no tolerance on a count. The forms are put to the person again.

Asked the form again, the person answered: "비슷한 시스템들을 찾아봐야지 솔베이션 문제인것 같은데 다른 솔베이션 논문들" ("you should look at similar systems; it seems to be a solvation problem; other papers on solvation"). This seat searches papers on solvating a protein in a box of water (how tools place water, how many molecules they add, how far those numbers differ between tools, settings or machines), for systems like this one.
