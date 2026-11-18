# K-Dense-AI/scientific-agent-skills, read on 2026-11-18 for how this system makes skills

Read by `design-macbook-20261117-3` on the person's word (`../ideas/20261118.md`, "How the skills of that collection are made"). The collection was read from a shallow clone of `https://github.com/K-Dense-AI/scientific-agent-skills` at its commit `ec59a29` (2026-11-16, MIT), made in this seat's scratch folder and not kept. Nothing of it was run. The counts below are read off one pass of a script over that clone's `skills/` folder. They describe that commit only. Every recommendation here is a proposal and lands nothing.

## 1. What the collection is

- The collection holds 177 skills, one folder each, under the open Agent Skills specification. The repository root is also an Agent Plugins package.
- **Scope rule:** each skill covers one package, database, platform or research workflow. General coding skills, infrastructure with a science example attached, orchestrators that route to other skills, and a second provider for a service already covered are declined.
- **Layout:** `SKILL.md` is required. `references/` holds long documentation loaded only when needed, `scripts/` holds executable helpers, and `assets/` holds templates and example inputs. Tests never live inside a skill; they sit in a repository suite under `tests/<skill>/`.
- **Front matter:** a closed set of fields. `description` says what the skill does and when to use it, with the words that should trigger it. `compatibility` names the environment (Python version, packages, network). `metadata.version` is bumped with every change, and most skills carry `last-reviewed` as well.
- **Counts at that commit:**
  - `SKILL.md` lengths: median 277 lines, none above 500, which their CI warns at.
  - With `references/`: 176. With `scripts/`: 121, every one of which has a test folder. With `assets/`: 43.
  - A version pin or a "tested on" statement in the text: 121.
  - A validation or check section: 115. A "when to use" section: 89. A "do not use / use instead" passage: 75.
- **Collection-level tooling:** a validator for the specification; a test of the manifest; tests that console output uses ASCII status markers (so diagnostics work on old Windows consoles) and that no personal path leaks; and a security scan of every skill by a model, cached per skill.
- **A meta-skill, `autoskill`:** reads a user's screen history (through a local recorder), clusters repeated research workflows, matches them against existing skills, and stages either a new skill draft or a composition recipe. A person reviews and promotes each one.

## 2. What their best skills do, read closely

Three skills were read in full: `cantera`, `uncertainty-and-units` and `molecular-dynamics`. The first is the clearest model.

**`cantera`** (homogeneous ignition delay):
- **Narrow, with stated limits.** One reactor class. It says it is not a flame solver. A successful run establishes numerical execution, not the mechanism's validity for the case.
- **The calculation is code.** A tested helper script runs it, and the skill's text tells the agent how to call the script and how to read its report. The agent is not asked to rewrite the calculation.
- **An exact output definition.** The delay is the time of the largest temperature rise rate on a uniform grid. It is reported only when the rise is large enough and the maximum lies away from both ends of the grid. Otherwise it is null, with a status that says why. Nothing is extrapolated.
- **A refinement contract.** Every request runs four fresh reactors: the baseline, half the output spacing, tighter solver tolerances, and twice the horizon. The result is "numerically resolved" only when all four agree within a tolerance the input names and every conservation check passes.
- **Conservation checks.** Mass, element and energy drift, each with a stated diagnostic tolerance, kept apart from model uncertainty.
- **Provenance in every output.** The inputs, the package versions, hashes of the configuration and of the mechanism, and a snapshot of the loaded mechanism, so the run can be replayed.
- **Tested versions and dated sources.** It says which package release it was run against. Its example values are marked as regression values, not experimental validation.
- **Its tests** cover both reactor kinds, conservation, agreement with an independent equilibrium, a case that does not ignite, a maximum at the grid's end, refinement, replay and invalid inputs.

**`uncertainty-and-units`:**
- A numbered, non-negotiable workflow: attach units at input; write the measurement model first; give each input its estimate, uncertainty, distribution and degrees of freedom; check correlations; check the linearization; say what the "±" means.
- A section of the failures the skill exists to prevent. Each failure runs without error and gives a plausible number.
- A table for choosing between linear propagation and Monte Carlo.
- Bundled command-line tools, a plausibility check against known scales, and a dated source list (the GUM documents, CODATA, the packages' releases).

**`molecular-dynamics` and `qutip`** are closer to usage guides: a workflow with code for each stage, a validation section, and references. They hold more example values and fewer tested helpers.

## 3. Set beside this system's skills

**Already alike, or held more strictly here:**
- Narrow scope, units on every input and output, a source per relation, worked cases, a `validity` field and a "what it does not say" line.
- The undecided state: a diagnostic that is handed no tolerance answers `undecided` (for example `diffusive_regime_from_msd@v1`).
- A skill is run through the runner, and its result is never typed.
- No number comes from a model.
- A threshold is an input, the person's or the standing rule's. In theirs, the diagnostic tolerances of the conservation checks are written into the skill's text with no source.

**What theirs carry that ours do not yet** (recommended, in the order of what they would change):
1. **A refinement skill, general across engines.** Run the engine's call again with its numerical controls changed one at a time (output spacing, solver tolerance, horizon or mesh), and report each output's change and a resolved / not resolved / undecided state against a tolerance it is handed. It would be the mechanism the standing tolerance rule names ("the run's own numerical error", 2026-11-18). CFD-T's refinement run and the GROMACS stage lengths are two kinds it would meet.
2. **Conservation and consistency diagnostics per family of engine.** Mass, energy and charge drift; a sum of fractions; a sign. Each would take its tolerance as an input or derive it by rule, and never hold it in text.
3. **An exact output definition, with null and a reason when unresolved.** A skill whose output is an event or a maximum would say how it is located, when it is not reported, and that it is never extrapolated (`series_maximum@v1` is the case to look at first).
4. **The versions a skill was run against, and the date each source was checked.** A field for each in the manifest, for skills that call an engine or a package, so that a later engine release is a known gap, not a silent one.
5. **The failures a skill prevents.** The manifest would name the failure lines and cases of `meta_agent/failures.jsonl` that the skill answers, so that a reader sees why it exists and a test can show the failure gone.
6. **Provenance in a skill's run record.** The runner already records each run. It would add the input hashes and the package versions, so that a skill's result can be replayed as a bundle's replay items are.
7. **"Not for, use instead".** Beside "what it does not say", the skill that covers the neighbouring case, by its id.
8. **Hygiene for the Windows computer of tomorrow** (the person, 2026-11-18): ASCII status markers in what the tools print, and a test that no personal path enters a committed file.
9. **A miner of the collections, as `autoskill` mines screen history.** Read the `calls.jsonl` of collected test sessions for calculations typed inline (a `python -c` that computes a quantity, a number written into a report), match them against the library, and draft a library skill or a note for review. It would answer the question task `016` left: what should have been a skill. A person or the owning seat promotes each draft; a draft lands nothing.

**Not to take:**
- Thresholds written into a skill's text.
- Example values with no source.
- Installs that name no version (some of their usage guides).
- Examples marked "illustrative" that were never run. Here every worked case is run by the gate.
- A model-run security scan as the gate. Here the gate is deterministic.

## 4. Where each would land, if the person takes it

| Item | Paths | Role |
|---|---|---|
| 1, 2, 3 | library skills under `meta_agent/skills/`, with worked cases from a cited source, on fixtures of two unrelated kinds | meta |
| 4, 5, 7 | the library skill manifest's schema, check 22, `build-library-skill` | design first, then meta for the existing skills |
| 6 | the skill runner of the template | meta (a template version) |
| 8 | `contracts/tests/`, the tools' output | design |
| 9 | a reader of collections beside `testfolder.py collect` | design (the tool), meta (the drafts) |

What this reading does not show: whether their skills work as they say (none was run here), and how often an agent using them makes the failures they name.
