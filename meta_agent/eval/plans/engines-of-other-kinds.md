# Experiment plan: the Meta-Agent on engines of other kinds

Written by `design-macbook-20261117-1` on 2026-11-17, from the person's words in `../../../docs/ideas/20261117.md` ("Tests on engines of other kinds"). This file is the plan that the sessions of tasks `017` to `021` share. Each session takes one engine, writes that engine's brief, runs the test and reads it. This plan decides nothing that belongs to the person. Where it recommends something, it says so.

## Why these tests

The clone has been tested on one engine, HOOMD-blue: a Python API, hard-particle Monte Carlo, soft matter. rheoTool comes next. A testbed tests and does not shape (2026-11-11), and a general mechanism counts only when it runs on fixtures of two unrelated kinds, one of them not rheology. These five engines differ from HOOMD-blue in physics, in how they are driven, and in what can be checked against a source. Each fault they show tells us whether a mechanism is general or was quietly shaped around HOOMD-blue.

| Task | Engine | Kind | How it is driven | Why it is a different test |
|---|---|---|---|---|
| `017` | GROMACS | molecular dynamics, biomolecular | a chain of command-line tools, each passing files to the next | a long pipeline (structure, solvation, ions, minimisation, two equilibrations, production), with many settings a person must confirm (force field, water model) |
| `018` | Quantum ESPRESSO | density functional theory, plane waves | an input file read by a compiled program | the first engine driven by an input file; convergence in cutoff and k-points is parameter-range estimation; pseudopotential files come from a source someone has to name |
| `019` | FEniCSx | computational fluid dynamics, finite elements | Python API | the tutorial is a published benchmark with reference values in the literature, so it tries finding a source and comparing against it; it is not OpenFOAM, which keeps it apart from rheoTool |
| `020` | Cantera | chemical kinetics and thermodynamics | Python API | runs in seconds and gives the same answer each time; the cheapest test of the whole chain from request to build |
| `021` | Meep | electromagnetics, finite-difference time-domain | Python API | resolution, the thickness of the absorbing layer and the Courant factor bound one another, so it tries the joint ranges of `estimate-parameter-ranges` |

## What was observed before the plan (2026-11-17, by the session this seat forked from)

Each engine had a build for `osx-arm64` listed on conda-forge (read from `https://api.anaconda.org/package/conda-forge/<name>` on 2026-11-17): `gromacs` 2026.3, `qe` 7.6, `fenics-dolfinx` 0.11.0, `cantera` 3.2.0, `pymeep` 1.35.1. Each tutorial page below answered with HTTP 200 on the same day. Neither the tutorials nor the licences were read in full. The licence each package declares on conda-forge is a claim to be read again, not a finding. These lines are observations for the sessions of these tasks. They are not material cards, and the clone is not told any of them.

Seen in the same reading, not part of these tasks: conda-forge lists `openfoam` for `linux-64` only. rheoTool is built on OpenFOAM, so its test on this computer may stop at installation. Nothing is done about that here. Whether the clone finds it out for itself is part of that test.

## The links

| Task | Link the brief would carry |
|---|---|
| `017` | `http://www.mdtutorials.com/gmx/lysozyme/` (one author's tutorial; registering it and quoting from it are the person's) |
| `018` | open: the official examples `https://gitlab.com/QEF/q-e/-/tree/develop/PW/examples` or the unofficial tutorial `https://pranabdas.github.io/espresso/`; the person chooses |
| `019` | `https://jsdokken.com/dolfinx-tutorial/chapter2/ns_code2.html` |
| `020` | `https://cantera.org/stable/examples/python/thermo/adiabatic.html` |
| `021` | `https://meep.readthedocs.io/en/latest/Python_Tutorials/Basics/` |

## The brief (recommended form, not confirmed)

The form the person confirmed for rheoTool (`../briefs/clone-rheotool-bare.txt`): the role line, the link, the person's sentence "이것을 자동화 하고싶어", and the lines on carrying the request through and reporting. It carries no answers. The person confirmed that sentence for rheoTool, not for these five. A session asks before it uses it. Proposed file names: `../briefs/clone-gromacs-bare.txt`, `clone-quantum-espresso-bare.txt`, `clone-fenicsx-bare.txt`, `clone-cantera-bare.txt`, `clone-meep-bare.txt`.

A brief without answers leaves every policy, permission, source and tolerance for the clone to ask about. Those questions, and what the clone infers without asking, are part of what the test reads.

## How each task runs

1. Begin with `begin-session`, in the role your task names, and claim your task, one engine per seat. `019` and `021` are a meta seat's (the person, 2026-11-17); the others are a design seat's until the person says otherwise.
2. Wait for the person's word before writing the brief or making a run ("지금 말고 내가 말하면 실행").
3. Write the brief, confirmed with the person, and commit it alone.
4. Make the run, open one unattended session in its clone, and collect, all as `test-outside-the-repository` says. Each category keeps its runs and collections in a folder of its own: pass `--root <test folder>/<category>` and `--logs <log folder>/<category>` to every call of `contracts/tools/testfolder.py`. The categories are `molecular-dynamics` (`017`), `dft` (`018`), `cfd` (`019`), `chemical-kinetics` (`020`) and `electromagnetics` (`021`). This is the reading `meta-macbook-20261117-3` took of the person's word "각 시스템(시뮬레이션 카테고리) 별로 폴더를 만들고 거기서 작업하도록 하자". It is an inference that the person has not confirmed, and the repository is still one working copy on `main`. Model and effort: `choose-session-level` recommends and the person's word holds. Recommended: the level of the HOOMD-blue control test without answers, so that the runs can be compared.
5. Read the collection against the questions below. Write what it shows as records in the path of the seat that owns each one, naming the run and the collection. Then remove the run as the session skill says.
6. Close with `end-session`. The task card says what was watched and what was not.

One computer runs one clone at a time. That is the default the design seat took for rheoTool, and the person has neither confirmed nor objected to it. Whether these runs wait behind rheoTool is the person's.

## What every collection is read for

The same questions for every engine, so that the five can be set beside HOOMD-blue and beside each other:

- **How far it went:** materials, intake, physical system, parameter sheet, tool contracts, build, validation. Where it stopped, and whether the stop was a person's question or a fault.
- **Asked or inferred:** each policy, permission, source and scientific setting it met, and whether it asked, inferred (and wrote the inference as one) or decided by itself. Deciding by itself something that is the person's is a fault, whatever the engine.
- **Sources:** whether it searched for sources it was not given (permitted 2026-11-17), what it wrote as queued material cards, and whether a number it compared against has a source.
- **Environment:** whether it found for itself how the engine installs on this computer and wrote that as a finding with evidence, without being told.
- **Library skills:** which it made, whether each computes a quantity that enters a card or a decision (2026-11-17), and whether a session of the built bundle runs them.
- **Generality:** for each fault, whether its cause lies in a general mechanism (a skill, a card, a check, a template, a runner) or in something HOOMD-blue shaped. A fix lands only in a general mechanism, and is shown on fixtures of two unrelated kinds.

What to watch for in each engine:

- **GROMACS:** molecular-dynamics trajectories are not reproduced bit for bit across machines or thread counts. Only set-up values (counts of atoms and molecules, box, steps) can be compared exactly. Averages need a tolerance, and the tolerance is the person's.
- **Quantum ESPRESSO:** whether the clone treats the cutoff and the k-point mesh as ranges to be estimated by library skills rather than numbers copied from an example; where the pseudopotentials come from.
- **FEniCSx:** whether the reference drag and lift values are found in their original source and compared with a tolerance the person gives, or copied from the tutorial page.
- **Cantera:** whether the reaction mechanism file is treated as a material with a source; whether the clone over-builds a calculation that the engine reports itself (a value the engine reports is read from it, 2026-11-17).
- **Meep:** whether the joint bounds of resolution, absorbing layer and time step come from library skills, with the reason for each choice stated.

## Waits for the person

- the word to begin;
- the text of each brief, and Quantum ESPRESSO's link;
- the order relative to the rheoTool test, and whether runs may overlap;
- the model and effort of each test session;
- every tolerance a comparison needs;
- whether the candidates that were not chosen are ever tested.
