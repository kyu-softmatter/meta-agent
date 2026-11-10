# meta-agent — design record

Version 0.3.2 (English record), 2026-10-29. Status: **approved by the person on 2026-10-29; M0 in progress.**
Subtitle: Meta-Agents for Scientific Agent Development and Self-Improvement.

This file is the design record from M0 on. The Korean plan it was written from, `docs/origin/PLAN.ko.md`, is frozen at v0.3.2 and is not edited (open question 2, settled by the person's approval of the plan that recommended it). Where a detail here is more specific than the origin, it is because M0 had to decide it; each such place says so.

---

## Decisions so far (the person's)

| Date | Decision |
|---|---|
| 2026-10-29 | One agent only. Modeled on soft-matter-agents (SMA). A bridge connects it to other agents later if needed. Plan in Korean first; code, cards and repository memos in English. |
| 2026-10-29 | The proposal's AWS deployment, operation and budget parts are not used. |
| 2026-10-29 | The materials inbox is designed so that the person can drop a link later with one line; nothing is asked for now. No materials exist yet. |
| 2026-10-29 | **First testbed: the lab's rheometer (B) and a rheology simulation engine (C), as a pair.** Done when a cross-validation card exists (same fluid, same model, same units). The order inside the pair (engine agent → rheometer agent → cross-validation) stays a recommendation. |
| 2026-10-29 | Repository `kyu-softmatter/meta-agent`, private, MIT; local folder `D:\codes\github\meta-agent`; first push = plan only; plan revisions as separate commits. |
| 2026-10-29 | Plan v0.3.2 approved; M0 (§15) started. |
| 2026-11-09 | **What the system automates, as the README says it**: working out how a lab's materials and data are laid out, searching the related literature, keeping the workflow, convening the meeting in which a plan is settled, building skills; the list is open (`docs/ideas/20261109.md`). The README states beside each what runs and what is only designed. |
| 2026-11-09 | **The repository is public** (`docs/ideas/20261109.md`), replacing "private" of 2026-10-29; MIT stands. What is pushed is published; no licensed text is copied into it (§5.0). |
| 2026-11-09 | **Goal: this system is an agent-native environment**, both the repository as the place seat sessions work in and the bundles built here as agents (`docs/ideas/20261109.md`). The person decides (safety values, thresholds, release of `held`, hand-over, roles and machine tags); sessions do the rest. Decisions only first, unattended runs later. A session may register its own seat, claim a task, and the gate runs in CI. The design, meta and harness seats run at the same time on one computer (§9, §14-29). |
| 2026-11-09 | **Design change: parameter bounds come from skills written as source code**, each computing a maximum or a minimum of one parameter, and the model takes the skills a request needs (`docs/ideas/20261109.md`, §5.3, §14-30). Code computes, the model chooses; this revises the helper registry and the rule-chosen mode of §14-26. |
| 2026-11-09 | **The skill library has kinds, and subagents use it**: hardware connection, hardware boot sequence, hardware control, hardware situation awareness, hardware calibration, data analysis and more, beside the parameter bounds; the Meta-Agent makes the skills as source code and the built agent's subagents take the ones they need (`docs/ideas/20261109.md`, §14-31). The Meta-Agent still never operates (MP1). |
| 2026-11-09 | **Every key quantity is obtained by a skill, the limits are considered together, and what is wanted is the rough ranges of the key physical quantities; the model reasons over them and sets the engine parameters** (`docs/ideas/20261109.md`, §5.3, §14-32). A model's own number still enters nothing: the model chooses and code computes. The rough-range pass is a card of its own. This revises §14-30(i). |
| 2026-11-09 | **A built agent settles its ranges among subagents that each hold a position**, a science subagent that does not forget the purpose and a safety subagent among them, with a compromise subagent that finds a range all accept, proposes it and obtains their agreement. It works inside the built agent; simple negotiations are skipped; whether an agreed range is adopted as it stands is for the built agent's user to decide and to change later. At most five rounds, and beyond that the person is told; giving up a requirement of the science subagent is the person's decision under any setting; experiment and simulation are different bundles; where the user has set adoption as agreed, a run on the instrument starts without a person being asked, and whether that is blocked where the bundle's gate has no limit check is also the user's to specify (`docs/ideas/20261109.md`, §14-33). |
| 2026-11-09 | **The plan card goes to an operating subagent, which runs the experiment within the range with the skills; then, with the data, to an analysing subagent; then a report goes to the user** (`docs/ideas/20261109.md`, §14-34). The names and fields of the cards are left to the seat. The Meta-Agent builds this and never runs it (MP1). |
| 2026-11-09 | **The aim is general scientific problems, and a validation speaks of resolution, accuracy and precision, and of the range of validity, convergence and stability, physical consistency and selectivity**; the structure of S6 is under the person's review (`docs/ideas/20261109.md`, §14-35). |
| 2026-11-09 | **While scanning the instrument the agent finds its maximum operable range by itself** (`docs/ideas/20261109.md`, §14-36). Read as the built agent at its destination, by read-only queries of what the instrument reports; the Meta-Agent still reaches no instrument (MP1). Where the person has set no safety value for a quantity, the scanned range stands in for it at the gate (answered the same day); no safety value is written, a model's number still reaches nothing, and the person may mark a safety row as one no range may stand in for (MP4 as narrowed, §14-36(f)). |

---

## 0. Position, language, references

- Language: the planning conversation is Korean. Everything that lives in the repository — code, schemas, cards, `CLAUDE.md`, `README.md`, `tasks/`, `failures.jsonl`, `docs/ideas/` — is English. Quotations of the person's words are kept verbatim in Korean with an English gloss (SMA practice).
- Nothing was built before approval. M0 builds the contracts first (§15).

**References.** Cited by these short names.

| Name | Source | What is taken |
|---|---|---|
| **SMA** | https://github.com/kyu-softmatter/soft-matter-agents (MIT, the person's own) | Cards, gates, seats, task queue, failure log, meta-harness rules (its §8.3). Principles P0–P16 are cited, not copied. |
| **Proposal** | "Meta-Agents for Closed-Loop Simulation and Experimentation" (research proposal draft). **Its AWS deployment, operation and budget parts (§2.5, §4) are not used.** | Role definitions, two loops, two improvement paths, the Designer's outputs, two validities, testbeds, evaluation design. |
| **REA** | https://github.com/morluto/rea (Reverse Engineer Anything, MIT) | Discipline for software and repository analysis: observed / derived / inferred / unknown, evidence provenance, registered unknowns, error contract, fail-closed integration, read-only by default. Called as a tool (MCP), never vendored. |
| **harness2** | https://github.com/google-research/harness2 (Apache-2.0; "not an officially supported Google product") | The eight harness components, Propose–Probe–Compose, two levels of recursion, the edit contract, the cost order, the experience format, the budget ledger, baseline first. Used as a reference for structure, not as an engine (§14-8). |
| **Conversation 1** | ChatGPT shared conversation, https://chatgpt.com/share/6ae3747c-b860-83e8-85c2-1e9b1121c126 | Functional partition and vocabulary, evaluation metrics, parameter and protein source candidates. |
| **Conversation 2** | Second shared conversation, https://chatgpt.com/share/6ae37853-e874-83e8-a21f-ac4f252c5e94 | Protein databases, scale / method / engine separation, Lab Profile, GUI, setup wizard with adaptive questions, the three-state vocabulary. |
| **HOOMD_GUI** | https://github.com/kyu-softmatter/HOOMD_GUI (the person's; README of 2026-10-29 calls it an "idea sketch / concept document"; no license file yet) | Reference case for a particle-simulation GUI: visual modelling, transparent code generation, separated scientific core, reproducibility first, validation before execution. |

**Marking unverified facts.** Database, library and engine facts that came from the conversations (existence, access path, coverage, license) were **not verified by the plan**. They are marked "to verify"; verification is the first job of M2/M3 and its result lives in `knowledge/sources/` records or in registry entries' `verified` field. What is unverified is never written as verified (SMA P1; numbers are read off a run).

**Materials inbox.** Manuals, papers, spec sheets and repository links for preferred engines or instruments can be dropped **at any time**: one line in `meta_agent/inbox/materials/LINKS.md`, or one file in `meta_agent/inbox/materials/drop/`. Classification, source record and registry updates are the Meta-Agent's; the person only confirms (§5.0). The four tools the plan knows about, none with materials yet:

| Tool | Kind | Known from | Waiting for |
|---|---|---|---|
| HOOMD-blue | engine (MD, BD) | SMA simulation agent, HOOMD_GUI | the lab's version, scripts, conventions |
| The microscope (SMA's microscope agent) | instrument | SMA | control software documentation, the place of the safety rules |
| The lab's rheometer (TA Instruments per the proposal; model and control software to verify) | instrument, **first testbed** | proposal, the person's decision of 2026-10-29 | control software / API / scripting documentation, data export format, basis of the analysis permission. **Needed first.** |
| A rheology simulation engine (candidate RheoTool / OpenFOAM; the person chooses, §14-20) | engine (CFD, viscoelastic), **first testbed** | proposal, the person's decision of 2026-10-29 | which engine, version, tutorial cases, lab setup. **Needed first.** |

---

## 1. Purpose

### 1.1 Three roles, one sentence

- **Meta-Agent**: the agent responsible for configuring, operating and improving other agents. The only agent in this repository. It touches no instrument and runs no simulation itself.
- **Agent Designer**: a role inside the Meta-Agent. It **designs, generates and validates** a Scientific Agent for a new tool (instrument, simulation engine, analysis software). Outputs: capability specification, callable tools, steering instructions, validation tasks, deployment configuration, and optionally a GUI specification.
- **Scientific Agent**: the agent that plans and runs the research task itself (SMA's microscope and simulation agents are examples). It is what the Meta-Agent **builds**, not part of it.

**One sentence.** The Meta-Agent first reads the lab's environment (Onboarding), builds scientific agents (Agent Designer), and makes them better from the knowledge and experience they gather in research (Self-Improvement). What it builds is a bundle (a directory); what it changes is a proposal card; what it remembers is a case.

### 1.2 Two loops

| Loop | Cycle | Actor | Goal |
|---|---|---|---|
| **Scientific Research Loop** | research goal → experiment / simulation plan → run → analysis → next condition | Scientific Agent | better scientific results |
| **System Improvement Loop** | agent run → success / failure evaluation → cause classification → knowledge or structural improvement → re-validation | Meta-Agent | better agent performance and reliability |

The loops are linked by run results and evaluations but have different purposes and are **evaluated separately**. The Meta-Agent never drives the first loop; it only reads its results.

### 1.3 Two improvement paths

| Path | What changes | What does not |
|---|---|---|
| **Knowledge-based** | knowledge entries and cases are added or updated and the next decision cites them | the agent's structure (instructions, tools, validation flow) |
| **Structural** | the meta-harness proposes changes to role split, tool choice, instructions, skills, context management, validation workflow, error handling | the content of the knowledge |

Their effects are compared under **four conditions** (none / structure only / knowledge only / both; §11).

### 1.4 Functions

| # | Function | Identifier | Outputs |
|---|---|---|---|
| **F0a** | **Onboarding & Setup Wizard**: discovery → adaptive questions → configuration proposal → approval | `onboarding` | `discovery_report`, `lab_profile`, `onboarding_record`, draft `agent_goal` |
| **F0** | **Agent Designer**: tool understanding → specification → build → two validities → hand-over | `designer` | `tool_profile`, `agent_spec`, `build`, `validation_report`, optional `gui_spec`, the bundle |
| F1 | Scan, distil and store papers, technical documents and run records (Knowledge Engine) | `knowledge` | `knowledge_brief`, source records, distillation notes, entries |
| F2 | Parameter analysis for simulation and hardware operation (Parameter Intelligence) | `parameters` | `parameter_sheet`, `protein` entries |
| F3 | Structural improvement through the meta-harness | `harness` | `incidents.jsonl`, `harness_proposal`, `ledger.jsonl`, `retro/`, `library/` |
| F4 | Storing and re-using failure / success metadata (Experience Memory) | `cases` | `case` entries, `case_refs` / `case_gaps` in cards |
| F5 | Card-based | `contracts/` | every hand-over is a card on disk (JSON record + MD for people) |

### 1.5 Success criteria (measurable)

1. A built bundle passes the interface gate and the scientific gate **without the Meta-Agent** and handles one mock question end to end (SMA P11).
2. An instruction change happens only as proposal → proof (fixture + replay) → landing by the owning seat; in replay a refusal is still a refusal and a gap is still named (SMA §8.3 rule 7).
3. A new request carries related cases as `case_refs`, or `case_gaps` naming **where it looked**.
4. Every number is a (value, unit, source, grade) tuple; model-made values (E6) enter no card and no store.
5. Every `tool_profile` claim is observed / derived / inferred / unknown, and an unknown says what would resolve it.
6. The four-condition comparison is **runnable** with the same task set, runner and seed, and the baseline is judged first.
7. Time to the first scientifically valid run, and the number of interventions, are read **off the record**.
8. Every wizard question targets a field that is `unknown` at that moment or a policy field. What the materials already answered is not asked again; policy, permissions and publication scope do not go to a build before a person confirms them (checks 15, 16). Material intake follows the same discipline: the person writes one line (the location); the Meta-Agent fills classification and source record; the person confirms (check 17).
9. All of the above are counted from runs, never from documents.

### 1.6 Failure signs

The Meta-Agent writes into a built agent's directory. A model-authored safety value appears in `envelope/`. A bundle that passed only the interface gate is handed over as "done". A proposal lands without a fixture; "helped" is written on adoption alone. An inference is written as an observation in a `tool_profile`; a binary is analysed without a permission record. The wizard asks for language and engine after reading the repository; or marks publication scope `confirmed` because the repository is public. An agent is built for an engine the lab does not use. A GUI file holds a threshold only the GUI knows; a passing GUI check is taken as permission to run. The case store grows and no card cites it. Two knowledge stores hold different values for one quantity. The system drifts toward a general workflow engine (SMA P10).

---

## 2. From the references: taken, changed, not taken

### 2.1 SMA

**Taken as is (by citation)**: principles P0–P16, the card hand-over convention D3, deterministic gate + rejected fixtures + "check and fixture in the same commit" + "watch the fixture fail first", the seat registry and boundary check, the `tasks/` queue, `failures.jsonl`, `docs/ideas/`, the meta-harness loop and rules 1–7 (§8.3), the flat output tree, five-field instructions / ten-line reports, the three disk conditions before cleanup.

**Changed**

| SMA | meta-agent | Why |
|---|---|---|
| four agents + bridge + console | **one agent** (`meta_agent/`) | the person's decision; a bridge connects later if needed |
| `questions/<qid>/` | `requests/<rid>/` | the input is "build / revise an agent", not a measurement question |
| condition design in 7 / 6 axes | six specification axes A1–A6 (§5.1) | the design object is an agent's boundary, interface, knowledge, parameters, safety, validation |
| execution tier S6 | none, Tier 0 | holds neither instrument nor engine |
| the librarian is the only knowledge owner | standalone: its own `knowledge/` is the record; connected: the librarian is the authority and entries here are candidates | keeps P14 and D5 together |
| `contracts/harness/` | `meta_agent/harness/` | the harness is this agent's main job |

**Not taken**: instrument-specific code and safety values, the console, the microscope's real-time judgement modules.

**What SMA is to the product** (the person, 2026-11-08, `docs/ideas/20261108.md`): one example of the shape the agents built through this repository should take: cards as hand-overs, seats, a deterministic gate with rejected fixtures, `failures.jsonl`, an envelope whose safety values only the person writes and whose readers run in a fixed order before any instrument action, a bridge that carries cards unchanged. The Designer's template and the B checks are measured against that shape; `docs/reference/sma_read_20261108.md` describes it as read on that day. "One of": other shapes may come, and the person names them.

### 2.2 Proposal

**Taken**: the three roles, two loops, two paths, the Designer's five outputs, the separation of the two validities, testbeds A / B / C and cross-validation, the four evaluation conditions and metrics, "time to the first scientifically valid closed-loop run", reproducible validation tasks and shareable success / failure examples in a public repository.

**Not taken**: AWS deployment / operation / budget (§2.5, §4), web service and dissemination targets, permanent central coordination of many agents (the bridge's job).

### 2.3 REA

**Taken as discipline**: claims are **observed / derived / inferred / unknown** with evidence provenance; unknowns are registered with **what would resolve them** (permission, environment); "absent" is never concluded from partial evidence; read-only by default with explicit write permission; configuration changes are additive and idempotent and shown as a plan first; the error contract (category, retryable, remediation); **fail-closed** integration when scope, permission, side effects or validation are unresolved; REA's own boundary: "repositories with source are for ordinary tools; binaries, packages and runtime behaviour are for REA".

**Taken as a tool**: investigation of interfaces, parameters and call paths of instrument control software and engine binaries **whose use and analysis permission a person confirmed**. Connected over MCP, runs locally.

**Not taken**: REA's analysis engines in this repository; runtime capture on the instrument computer.

**How REA reaches a computer** (the person, 2026-11-05, `docs/ideas/20261105.md`): `tools.lock.json` pins Node.js and `rea-agents`; `bootstrap.py` installs them for the user from their own sources, checked against the lock, and `.mcp.json` calls REA as an MCP server through it. Nothing of REA is vendored, and its install scripts are not run.

**Tools fetched when a request needs them** (the person, 2026-11-06, `docs/ideas/20261106.md`): when a request needs an external tool this computer lacks (Ghidra and a JDK for native code, ILSpy for managed code, TShark and capinfos or sigrok-cli for a capture file), the Meta-Agent installs it itself through `bootstrap.py` instead of asking the person to run a command. The tool is pinned in `tools.lock.json` (version, the project's own source, a checksum from that project's own release, license), lands in the tools home, is called out of process and never vendored, and its location is passed in the environment of the call that uses it (for REA's Ghidra provider, `GHIDRA_INSTALL_DIR` and the JDK given to `bootstrap.py run rea`); no PATH, registry or agent configuration changes. A tool not yet pinned is pinned by the Meta-Agent itself without asking (the person, 2026-11-06); the pin's commit, judged by the gate, is the record. The fetch is named in the report of the request that needed it (tool, version, source, size). **Stays the person's step**: a tool that is not open source or whose download asks for terms to be accepted; anything that needs administrator rights or installs a driver or service (Npcap, USBPcap, com0com), a PATH change, a new WSL distribution, anything on the instrument computer (P0). Frida's native module is fetched only under an `analysis_permission` that covers runtime analysis of that software. Open: §14-23.

### 2.4 harness2

**Taken as design**: harness = everything around the model. Eight editable components and their cost (always-on prose is the most expensive). The edit contract "omission is inheritance"; invalid proposals are discarded whole. Contrastive evidence from Propose–Probe–Compose. Two levels of recursion with a per-domain library. The experience format `cue / lesson / evidence / confidence` and the precedence of `confounded`. The budget ledger. Baseline first. Judge and report under one configuration. Restrict the runner's network so it cannot reach the evaluation material.

**Changed**: adoption is not left to a model judge. Our probe is mock replay + deterministic validation; compose is a model-written **draft**; adoption is gate + owning seat + (for loosening) a person (SMA §8.3 rule 4, MP5).

**Pinned, not carried** (2026-11-05): `tools.lock.json` names the harness2 commit and `bootstrap.py install harness2` sets it up on Linux or inside a WSL distribution, outside this repository. **Not taken (now)**: installing harness2 as an engine. If ever, only under SMA §8.3's trial design of 2026-10-19 (clone outside the working folder, mock only, a computer without instruments; §14-8).

### 2.5 Conversations 1 and 2

**From 1**: the functional partition and vocabulary (Agent Designer / Knowledge Engine / Parameter Intelligence / Experience Memory / Meta-Harness), four metric groups, roadmap phases, parameter and protein source candidates with tiered search, the distinction measured / computed / literature / estimated, observed phenomenon / suspected cause / confirmed cause, predicted structure ≠ experimental structure, existence / structure confirmation ≠ function / property confirmation.

**From 2**: the setup wizard (discover → adaptive questions → propose → approve) and "analyse first, ask later"; the three states; the information-sufficiency check and "sufficiency never grants permission"; scale / method / engine separation and the many-to-many relation; the Lab Profile; respecting the lab's existing tools; the GUI's common frame vs domain editors; GUI derived from the capability spec; GUI input validation never replaces engine validation; protein search paths and soft-matter conditions; multiscale coupling is the bridge's job.

**Not taken**: unverified factual statements (§0), framework / database / GUI stack choices, the goal of a fully auto-generated GUI from day one.

### 2.6 HOOMD_GUI

**Taken as principles**: visual modelling, transparent code generation, **separated scientific core** (physics model and validation logic outside the GUI, reusable by CLI, Python and agents), reproducibility first, validation before execution, versioned JSON project documents, a loopback-only Local Runner as the safe default.

**Fact check (README of 2026-10-29)**: implementation is a Pixi environment + a 2D particle editor (box, boundaries, particles, properties, browser-side checks, JSON import / export) + Local Runner. Code generation and HOOMD execution are **not implemented**. Moving authoritative validation into a Python package (`hoomd_gui_core`) is the roadmap. First platform macOS ARM64. **No license yet.** The README's About and body disagree on whether the GUI is implemented. Recorded in `docs/reference/hoomd_gui.md`.

**Not taken**: code. Reuse is decided after a license exists (§14-16).

---

## 3. Meta-principles MP1–MP13

SMA P0–P16 bind as they stand. These are added for this repository.

| # | Principle | Why | If broken |
|---|---|---|---|
| **MP1** | **The Meta-Agent builds and proposes. It does not operate.** No instrument or engine tools, no network path to an instrument (Tier 0). It never drives the Scientific Research Loop. | P0. A building seat that reaches an instrument makes two safety boundaries. | a build-time mistake reaches hardware |
| **MP2** | **A built agent stands alone.** The bundle passes both gates and handles a mock question without the Meta-Agent. | P11 | the Meta-Agent becomes a single point of failure |
| **MP3** | **The template is the record of structure.** Bundles come from a versioned template + spec; the difference is a diff in the `build` card. | tracking evolution needs "from what to what" in files | nobody knows why one agent differs |
| **MP4** | **Safety values are never generated.** The `envelope/safety.json` template is `null`; the gate rejects a safety value whose author is not human. **Narrowed 2026-11-09** (the person, §14-36(f)): in a built agent, where the person has set no safety value for a quantity, the operable range the device itself reports stands in for it at the gate; a safety value is still written by a person only, no model's number is ever a limit, and the person may mark a safety row as one no range may stand in for. | P0, SMA §8.3 rule 2 | a model-written limit reaches an instrument |
| **MP5** | **A proposal lands nothing.** The model drafts; fixtures and replay (code), the owning seat, and a person when needed decide. Adoption alone never means "helped". | SMA §8.3 rules 1 and 4; harness2's experience rule | a system that fixes its own safety |
| **MP6** | **Cases are re-ranked, never deleted.** They carry a falsification condition and counts; a superseded case stays with `superseded_by`. | P16 | only the first configurations that worked are repeated |
| **MP7** | **Distilled knowledge is a candidate until its source grades it.** Model output (E6) stays labelled in notes and never becomes an entry. Measured, correlation, computed, predicted, literature and estimated values are told apart by `value_kind`. | SMA §5.3, Conversation 1 | a plausible number becomes authority |
| **MP8** | **A feature enters when a request requires it.** Vector stores, engines, UIs and adapters must pass "does the request in front of us need this". | P10 | a general engine again |
| **MP9** | **A claim is one of four: observed / derived / inferred / unknown.** The same discipline for tool understanding and for case causes (observed / suspected / confirmed). "Absent" is never concluded from partial evidence. | REA; SMA's "no impossibility from silence" | an inference becomes a spec and reaches an instrument |
| **MP10** | **Fail-closed integration.** A capability with any unresolved scope, permission, side-effect or validation question stays out of the bundle as `held`. A person opens it. | REA's integration rule; SMA bridge's `undeclared → held` | an unpermitted analysis or a side-effecting call slips in |
| **MP11** | **Discovery recommends; a person confirms.** Settings inferred from code and documents (`inferred`) are recommendations with evidence. Operating policy, execution permission, publication scope and collaboration mode are never inferred. A sufficiency judgement grants no permission. | Conversation 2. Python code does not make a Python-only lab; a public repository does not make agents and data publishable. | an inference becomes policy and private code leaves |
| **MP12** | **Respect the lab's existing tools.** No engine or language is imposed. The registry is a list, not a ranking; recommendations come from the Lab Profile and the method, with evidence. | Conversation 2. The same Brownian dynamics is done with HOOMD-blue, LAMMPS or in-house code. | an agent for an engine nobody uses |
| **MP13** | **The GUI is not a source of scientific judgement.** It is a human interface to a validated model and runner. GUI input validation does not replace the scientific core's or the engine's; the GUI is derived from the capability specification; no threshold lives only in the GUI. | HOOMD_GUI's separated core; Conversation 2 | a wrong condition runs because a GUI check passed |

---

## 4. System overview

```
 person ──(materials: GitHub, documents, PDFs, links, existing cards; any time via inbox/materials/)──▶ S0 Onboarding (setup wizard)
            │  Step 0 discovery → discovery_report (inferred, with evidence)
            │  Step 1 adaptive questions (unknown and policy only) → onboarding_record
            │  Step 2 configuration proposal → lab_profile + draft agent_goal + validation plan outline
            │  Step 3 approval (person) ──▶ S1 Intake ──▶ agent_goal
                                                           │
       S2 Tool Understanding ◀─────────────────────────────┤  manuals, API docs, scripts, source (ordinary tools)
            │  tool_profile: observed/derived/inferred/unknown + evidence + limitations + permission record
            │                                               │  binaries, packages, runtime (REA, when permission is confirmed)
       S3 Recall / Scan ◀───────────────────────────────────┤  cases → case_refs/gaps · knowledge → knowledge_brief
                                                           ▼
       S4 Specify ──▶ agent_spec (A1–A6) ◀── parameter_sheet (F2) · lab_profile · method registry
                                                           ▼
       S5 Build ──▶ build card + builds/<agent>/<build_id>/ (bundle = harness surface + tools + validation tasks + optional GUI)
                                                           ▼
       S6 Validate ──▶ validation_report: ① interface gate  ② scientific gate   (both must pass)
                                                           ▼
       S7 Hand over ──▶ the person moves the bundle to its destination (the Meta-Agent writes nothing outside)
                                                           ▼
   ┌── System Improvement Loop ──────────────────────────────────────────────────────────────────────┐
   │  observe (read-only) → incidents → classify → knowledge-based (entries, cases) | structural (proposal) │
   │  → proof (fixture + replay + contrast) → gate → owning seat lands → measure → lesson into library       │
   └───────────────────────────────────────────────────────────────────────────────────────────────┘

   a new engine, instrument, code or material arrives ──▶ only S0 Step 0 re-runs for that item → v<N>_lab_profile
```

- S0 runs in full once per lab; afterwards only discovery re-runs when new material arrives.
- S1–S6 finish flat inside one request folder `requests/<rid>/`. When an improvement requires redesign, the same `rid` gets a new revision `v<N>_` and S4 onward re-run.
- The System Improvement Loop runs independently of requests (daily retro or the person's instruction).
- Every arrow is a card.

---

## 5. Specifications

### 5.0 F0a Onboarding and the adaptive setup wizard

**What.** The Meta-Agent's first entry point. Unlike an ordinary wizard it **analyses the lab's materials and environment first and does not ask what it already knows** (Conversation 2). It is also the Designer's first stage, Research Environment Discovery & Agent Onboarding.

**Four steps.**

| Step | Does | Produces |
|---|---|---|
| Step 0 Environment Discovery | reads the repositories, documents, manuals, PDFs, links, existing agent cards (SMA's `contracts/`, seats, `failures.jsonl`) and lab settings the person gave. Source with ordinary tools; binaries with REA only under permission (same discipline as §5.1 S2) | `discovery_report`: per field `{value, state: inferred, evidence[]}` or `unknown` |
| Step 1 Adaptive Questionnaire | asks only fields that are `unknown` at that moment and the **policy fields**. Order and count depend on earlier answers and discovered material. One or a few most important questions at a time | `onboarding_record`: questions, answers, skipped questions and their reasons |
| Step 2 Configuration Proposal | research environment summary, engine / instrument recommendations from the registry (with evidence), agent design outline, GUI options, validation plan outline, `held[]` | draft `lab_profile`, draft `agent_goal` |
| Step 3 Approval & Generation | only what the person confirms becomes `confirmed`. S1 onward run on the approved configuration | `lab_profile` (confirmed), `agent_goal` |

**Three states** (per setting):

| State | Meaning | Condition |
|---|---|---|
| `confirmed` | a person checked it or stated it explicitly | `confirmed_by: human`, `date` |
| `inferred` | inferred from code or documents | `evidence[]` required (`source_ref` + `locus`); presented as a recommendation only |
| `unknown` | no evidence, or not decided | asked, or carried as `held` |

`inferred → confirmed` is done by a person only. **Policy fields** (working mode, approval mode, publication scope, execution permission, collaboration mode, external transfer of private code) must be `confirmed` before a build; otherwise `held` (MP10, MP11). This vocabulary is the same discipline as `tool_profile` claim kinds (MP9): `inferred` is an inference, `confirmed` is a person's observation.

**Question bank** (no fixed order; skipped on condition):

| Group | Question | Skip / infer condition |
|---|---|---|
| 0 materials | Are there repositories, documents, manuals or existing agent cards to analyse? **PDFs or links for preferred simulation engines or experimental platforms?** (none needed now; one line in `inbox/materials/LINKS.md` at any time; a link given in conversation is copied there by the Meta-Agent) | always asked; connected material is reused |
| 1 lab | Is this the lab's first agent? | existing agent cards or repositories → recommended `inferred: no` |
| 2 collaboration | Configure to collaborate with existing agents? (→ bridge plan) | skipped or deferred for a first agent; important when existing agents are found |
| 3 research kind | simulation / experiment / analysis, **multiple** | recommended when inferable |
| 4 methods | if simulation: DFT · MD · BD/CG · mesoscale · CFD · FEM · other, **multiple** | inferable from code and input files |
| 5 tool preferences | preferred engines, languages, operating environment (OS, HPC, GPU, package manager) | inferable from repositories; "the repository's dev environment = today's run environment" is not shown, so recommendation only |
| 6 existing assets | code, models, data, validated workflows in use; links | repository and document analysis |
| 7 GUI | none / parameter form / domain visual editor / reuse the lab's GUI | recommended from research kind and methods |
| 8 operating policy | working mode, approval mode, publication scope, execution permission | **never skipped, never inferred** |

**Sufficiency check.** At each step: is what we have enough to design? If yes, continue; if not, ask the most important one or few questions. If it is possible to continue despite gaps, record the deferred settings in `held[]` and produce an initial configuration. Permissions — external transfer of private code, repository modification, real instrument control — are **never granted by a sufficiency judgement** (MP11).

**Applied to this lab** (illustrative; Step 0 produces the real values): SMA exists, so "first agent" is `inferred: no`; engine `HOOMD-blue` and language `Python` are `inferred`; one instrument (the microscope) and the bridge are `inferred`. Publication scope, approval mode, further methods and preferred engine / platform materials are `unknown` and are asked (§14-18, 19).

**Materials inbox.** One principle: **the person gives the location, the Meta-Agent fills the rest, the person confirms.** Same discipline as the wizard (analyse first, ask later; MP11).

*What the person does* (one of two, any time):

| Way | Does | Example |
|---|---|---|
| link | one row in the table of `meta_agent/inbox/materials/LINKS.md`; only the URL column is required | below |
| file | put a PDF, document or archive into `meta_agent/inbox/materials/drop/`; no renaming needed | `drop/TA_DHR_API_guide.pdf` |

```
LINKS.md (English, one table; url required, card filled by the Meta-Agent)

| url | name (optional) | role (optional) | note (optional) | card (filled by Meta-Agent) |
|---|---|---|---|---|
| https://hoomd-blue.readthedocs.io/ | HOOMD-blue | engine | lab uses v4 | |
```

*Five entry paths*, all ending in the same `material` card: (a) a row in `LINKS.md`, (b) a file in `drop/`, (c) an answer to wizard question 0 (the Meta-Agent copies the link into `LINKS.md`), (d) from M2 the command `add-material <url|path> [--about <name>]`, (e) in M9 (optional) the GUI's Project tab "Add material". Material arriving through the bridge comes as an `observation` in `inbox/<thread>/` and, once the person approves, is moved to (a) or (b); another agent never drops material directly.

*What the Meta-Agent does* (intake; the `meta-…` seat; read-only access):

1. On a new row or file it creates `inbox/materials/<YYYYMMDD>-<slug>/`, moves the file in, writes `MATERIAL.json`, and writes the card id into the `LINKS.md` row.
2. `kind`, `about` (name, role, methods) and `license_note` are **filled as `inferred` with evidence**. What it cannot fill stays `unknown` and goes on the question list (one or a few questions per material).
3. A URL is fetched and `retrieved_at` and `content_hash` recorded. Behind credentials or a login wall it is not fetched and the card is `held` (reason `permission_required`). A raw copy goes to `knowledge/sources/raw/` only when `may_quote: true` or the license allows; otherwise only the hash and locus are kept.
4. The person is shown the filled values and the questions once. On confirmation the state becomes `registered`.

*Afterwards* (F1, S0, S2): F1 turns `registered` material into a source record and a distillation note in `knowledge/sources/` and sets `distilled`. Material about a new engine or instrument re-runs S0 Step 0 **for that item only**, writes the difference into the `discovery_report` and **proposes** `v<N>_lab_profile` and registry updates (a person confirms). Material about a tool's behaviour makes S2 propose a `tool_profile` revision. A running request using that tool only gets a `superseded` notice, never an automatic swap. Material not accepted (duplicate, out of scope, license forbids) is `declined` with a reason. Design and build never wait for material: the tool's `tool_profile` simply keeps its `unknown` claims and their `requires`.

`MATERIAL.json` fields (the schema is the record):

```
id
kind:            manual | paper | spec_sheet | api_doc | repo | dataset | link | unknown
about:           {name, role: engine | instrument | platform | analysis_software | unknown, methods[]}
                 each field {value, state: confirmed | inferred | unknown, evidence[]}
location:        {url} or {path}                        (exactly one; the only field the person writes)
source_snapshot: {retrieved_at, content_hash, archived: path | null}   (required for a url)
added_by, added_at, entry_path: links_md | drop | wizard | cli | gui
license_note:    {value, state, evidence[]}             (confirmed by a person only)
may_quote:       true | false | unknown                 (written by a person only)
state:           queued | registered | distilled | declined | held
state_reason, questions[]
```

**Where the outputs live.** `meta_agent/profiles/<lab_id>/{discovery_report, onboarding_record, v<N>_lab_profile}.json`. When a request starts, `requests/<rid>/agent_goal.json` carries `lab_profile_ref`.

### 5.1 F0 Agent Designer

**S1 Intake → `agent_goal`.** The model refines S0's draft together with one paragraph from the person. The model **makes no numbers**. Fields: `purpose`, `science_task`, `tool` (name, kind `instrument | engine | analysis_software | none`, where its material is), `methods[]` (registry ids), `executes`, `must_not[]`, `knowledge_needs[]`, `parameter_scope[]`, `destination`, `priorities[]`, `lab_profile_ref`, `gui_choice`, `analysis_permission`. The person is asked once, only what only a person can answer.

**S2 Tool Understanding → `tool_profile`.** What the tool can do and what limits it, **with evidence**.

| Material | Method | Note |
|---|---|---|
| manuals, vendor specs, papers, `inbox/materials/` | read → source record → distillation note (F1's discipline) | a spec is `vendor_spec`, not this instrument's measurement |
| API / SDK docs, configuration files, existing scripts, source repositories | ordinary repository tools (read, search, static analysis). **Not REA** | REA's own boundary: source → ordinary tools |
| binaries, packages, runtime behaviour | **REA** (MCP); its evidence, limitations and unknowns are carried verbatim | **permission is confirmed first** |
| run records (if any) | format analysis of `runs/`, logs, result files | |

- **Permission.** Binary and runtime analysis only within use and analysis permission a person confirmed. A binary-derived claim without `tool_profile.analysis_permission = {granted_by: human, scope, basis (license clause or a docs/ideas commit), date}` is refused by the gate (check 11). Without permission the gap is recorded as `inaccessible` and the design uses **documented interfaces only**. Runtime capture only in a replica environment with no instrument attached, never on the instrument computer (P0).
- **Claim format.** Each item of `claims[]`: `{claim, kind: observed | derived | inferred | unknown, basis: documentation | source | binary | runtime | run_record, evidence: [{source_ref | rea_evidence_id, locus}], limitations, requires (for unknown: which permission, environment or measurement would resolve it)}`. (`basis` is M0's addition so that check 11 can tell a binary- or runtime-derived claim from a documentary one.) An inference is never written as an observation (MP9). "Unsupported" is never concluded from partial evidence.
- **Capability identification** (Conversation 1 §3.2): offered functions, actually executable commands, I/O formats, required parameters and units, valid ranges, hardware and numerical constraints, observable or computable quantities, unverified functions and gaps. Each is a `claims[]` item.
- **Six points REA answers for software** (the person, 2026-11-05, `docs/ideas/20261105.md`). For the software to be made into an agent, S2 reads its binary and runtime with REA, and the `tool_profile` answers six points, each a `claims[]` item whose `capability` names it: `connection` (transport and protocol to the instrument or engine), `operation` (command sequence and states), `parameter` (settable parameters, units, valid ranges), `bandwidth` (bytes per second and message sizes on that link), `realtime` (quantities streamed live during a run), `update_rate` (how often they are refreshed). Static reading (`basis: binary`) gives what the code can do: imported transport libraries, managed members and P/Invoke boundaries, string literals, constants such as timer intervals and baud rates; such a point stays `inferred` until a runtime observation (`basis: runtime`) confirms it. Runtime points come from Frida hooks in a replica environment or from a capture file REA is given; REA never captures traffic, and the Meta-Agent never reaches the instrument (P0). Without `analysis_permission` all six are `gaps` with `permission_required`. A point that only a run on the real link can answer (bandwidth and refresh period against the instrument) stays `unknown` with `requires` naming the capture; how that capture is obtained is §14-22.
- **Relation to the registry.** The registry (§5.6) is a curated list of "which tools exist and which methods they support"; the `tool_profile` is the evidence-based profile of **this tool in this request**. A difference becomes a registry update proposal.
- **Output**: `tool_profile.json` + `.md`, and the parameter candidate list for F2.

**S3 Recall / Scan.** Deterministic matching in `cases` by `science_task`, `tool`, `methods` and parameter names → `case_refs` / `case_gaps`. A `knowledge_brief` from `knowledge`. Attached to `v2_agent_goal.json`.

**S4 Specify → `agent_spec`, six axes.** Each axis is a `spec_a<N>.json` and may be written in parallel.

| Axis | Content | Source of numbers |
|---|---|---|
| A1 Boundary | directories, write / read / forbidden paths, seat name, tier | none |
| A2 Interface | cards read and written, inbox / outbox, **the list of callable tools with each tool's I/O and error contract** (S5), optional GUI-controlled fields | `tool_profile` |
| A3 Knowledge | entries copied into the envelope (`kb_version` pin), remaining gaps | `knowledge_brief` |
| A4 Parameters | the `parameter_sheet` rows this agent handles | `parameter_sheet` |
| A5 Safety | safety rows with **empty values**, the place of the deterministic rule (which code reads which value and stops), human-only actions | a person (`null`) |
| A6 Validation | **interface validation tasks** (call, response, error, configuration transfer) and **scientific validation tasks** (with reference results), completion and refusal conditions | refs from A3 / A4; a reference result has an entry or a source |

`synthesis.json` records conflicts between axes; the direction of concession comes from `agent_goal.priorities` and the Lab Profile's conventions. **Fail-closed** (MP10): a capability with unresolved scope, permission, side effect or validation goes into `held[]` and not into the bundle.

**S5 Build → `build` card + bundle.** Where the Designer's outputs go:

| Output | Place in the bundle |
|---|---|
| capability specification | `CAPABILITIES.json` (only `observed` and `derived` from the `tool_profile`; `inferred` → `unverified[]`, `unknown` → `gaps[]`) |
| scientific model & parameters | `envelope/snapshot.json` entries and `parameters.json` (sheet rows; safety rows `null`) |
| callable tools (tool adapter) | `tools/<name>/` (adapter code + `tool.json` contract + error contract); GPL and similar sources are called, never included (§14-10) |
| steering instructions & skills | `CLAUDE.md` (role, procedure, what it does not do), `skills/<name>/SKILL.md` |
| validation tasks | `validation/interface/*.json`, `validation/scientific/*.json` (+ source of the reference result), `replay/` (regression suite) |
| deployment configuration | `.claude/settings.json` (deny derived from A1, Bash / PowerShell twins, PostToolUse validation hook), `envelope/` (safety `null`, snapshot), `tasks/001-start.md`, `failures.jsonl` |
| optional GUI specification & components | `gui/gui_spec.json` + a composition of common components + tool-specific components only when needed (§5.7) |

**How the built agent calls its tools.** Today through Bash: `python src/run_tool.py <tool> < input.json` runs the gate, checks the input against `tool.json`, calls the adapter, checks the output and returns the output or an error contract. Recommended, not settled (§14-24, written at the person's word of 2026-11-06): the bundle also serves its tools as one MCP server, `src/mcp_server.py`, whose tool list is read from `tools/*/tool.json` and whose every call runs the same function as `run_tool.py`.

**Harness surface** (harness2's eight components mapped to bundle files). A proposal may edit only this surface. The GUI is not a surface but **an interface the surface exposes**; a proposal changes the GUI through `gui_spec`.

| Component | Bundle path | Context cost |
|---|---|---|
| system prompt | role and procedure in `CLAUDE.md` | always on |
| guardrails | "what it does not do" in `CLAUDE.md` + deny in `.claude/settings.json` | always on / tool loop |
| memory | `envelope/snapshot.json`, `case_refs` | always on (snapshot) |
| tool guidance | descriptions in `tools/*/tool.json`, the tool section of `CLAUDE.md` | always on |
| skills | `skills/<name>/SKILL.md` (+ `scripts/`) | on call |
| subagents | `.claude/agents/<name>.md` | own context |
| scripts | deterministic helpers in `src/` | on call |
| plugins / hooks | hooks in `.claude/settings.json` | inside the tool loop, cannot be skipped |

Edit contract: **omission is inheritance** (a proposal states only what changes). A proposal that fails validation (B checks) is discarded **whole**. Three discard rules: a skill needs a trigger sentence in `CLAUDE.md`; a named script must exist; a command deny must name both shells. Cost order: **skill > script > subagent > hook > always-on prose**. Adding always-on prose is paid for by removing something else (SMA's prose budget).

**Subagents of a built agent** (the person, 2026-11-09; §14-31, §14-33, §14-34; the names are the design seat's, and nothing is built). Two drawings, both in `.claude/agents/`. By what each argues for, none of them touching a device: the advocates `objective`, `budget` and the tool's own, `measurement` for an instrument or `numerics` for an engine (experiment and simulation are different bundles), each holding hard limits its own skills compute and soft preferences; a guard, `safety`, which reads the person's safety values, refuses, and neither concedes nor makes a value (MP4); and `mediator`, which proposes a range all accept and collects their answers. By side effect: `operator`, which alone may write to a device and runs the agreed plan within its intervals, and `analyst`, which touches no device. The flow is `run_plan` → `operator` → `run_record` and the data → `analyst` → `analysis` → `report` → the user. The Meta-Agent builds this and judges it on a mock; it never runs it (MP1).

`build` card: `spec_ref`, `lab_profile_ref`, `template_version`, `diff_from_template`, `bundle_sha256`, `held[]`, `gate_verdict`, `lineage`, `landed_at` (a person).

**S6 Validate → `validation_report`.** Two gates; both must pass.

| Gate | What | Where | Verdict |
|---|---|---|---|
| **Interface validity** | correctness of tool calls and responses, I/O consistency, error handling and recovery (error contract), transfer of settings and commands, and with a GUI the transfer GUI field → tool parameter | mock backend or sandbox (software tools in an isolated environment outside the working folder; hardware mock only) | per task `pass | fail | not_run`, deterministic |
| **Scientific validity** | quantity and unit consistency, validity of parameters and conditions, model assumptions, **agreement with reference results** (analytic solutions, literature values, reference data), reproducibility of interpretation | the `validation/scientific/` tasks in the same environment | a reference result is a number with an entry or a source; the agreement criterion (tolerance) is **a person's threshold**, otherwise UNDECIDED |

`not_run` is not a pass. A task that needs hardware stays `not_run: requires bench` and the bundle is handed over as "valid in mock" only. Browser-side GUI checks replace neither gate (MP13).

**Under review** (the person, 2026-11-09; §14-35). The aim is general scientific problems, and a validation speaks of seven things: resolution, accuracy, precision, the range of validity, convergence and stability, physical consistency, selectivity. What S6 judges today and a shape for it are in §14-35; nothing above is changed until the person answers.

**S7 Hand over.** The Meta-Agent writes nowhere outside `meta_agent/builds/`. The person moves the bundle to its destination and records `landed_at`. For an execution engine (instrument operation code) the Designer's job ends at the bundle's **skeleton** (the place of the deterministic gate, safety values `null`); the real operation code is written by the destination's owning seat with the person (MP1). A software tool's adapter (e.g. RheoTool) is built by the Designer and validated in the sandbox.

### 5.2 F1 Knowledge Engine (`meta_agent/knowledge/`)

Three layers (sources / distillation notes / entries), plus:

- **Input scope**: papers, technical documents, API docs, manuals, run records, the `registered` queue of `inbox/materials/`. S2's `tool_profile` and S0's `discovery_report` are inputs too.
- **`value_kind`** on every number: `measured | correlation | computed | predicted | literature | estimated | model_generated`. The grade is **derived** from (source kind, `value_kind`); the table is `contracts/grades.json` (§6.3). Rules for database values and predicted structures are §14-12.
- **Conflicts**: a value differing from an existing entry is recorded as `conflict` and both stay (SMA librarian's `kb_conflicts`). Insufficient grounds → `gap(unqualified_source)`.
- **Literature assessment**: candidate → critique → refinement **inside the distillation note**. Only refined claims become entries; the critique stays in the note.
- **Shared source adapters**: §5.3's adapters write source records into `knowledge/sources/`. Knowledge and parameters share one source layer.
- **Connected mode**: the librarian is the authority; entries here are `kb_candidate`.
- **Wiki view** (the person, 2026-11-04, `docs/ideas/20261104.md`; `meta_agent/tasks/003`): Karpathy's LLM-wiki pattern is adopted as a *view*, not a store. `meta_agent/wiki/` is rendered from the cards on demand, kept out of git and never edited by a model or by hand; one page per card revision, linked by the references the cards hold. The ontology of the card types and their references is exported as RDF/XML for Microsoft Ontology Playground, used at its hosted address or from a clone outside this repository. A rheology domain ontology is a later, separate decision of the person. `wiki/graph.html` (task 004) maps the same nodes and references in 3D with a 2D switch, written without a library and opened from disk. Check 18 refuses a page or a map that adds a number or a relation.
- **Working index** (the person, 2026-11-07, `docs/ideas/20261107.md`; `meta_agent/tasks/005`): auto-ontology-mcp's knowledge store is the Meta-Agent's working index for materials, beside the wiki view, not instead of it. At intake the model reads a material the person dropped and saves its passages, concepts and source through the server's MCP tools; S3 recall searches the store with FTS5 and hands hits to the `knowledge_brief` as candidates, each `inferred`. The cards stay the record: a value in the store is a model's reading and enters nothing (E6) until F1 writes it as an entry. The store is out of git, like `wiki/`; the server's SQL half is unused (MP8); search is lexical, so §13 and §14-7 stand. Pin, installer and the store's place are §14-25.

### 5.3 F2 Parameter Intelligence (`parameter_sheet`)

**Three stages** (Conversation 1 §5): **Discovery** (identify parameters together with the model, instrument, environment, assumptions, units and valid range they were used in, from papers, manuals, run records and databases) → **Reasoning** (correlations and constraints between parameters, scaling, dimensionless numbers, numerical stability conditions, instrument specifications; deterministic helpers) → **Recommendation** (value or range + grounds + uncertainty; without grounds, **propose the additional measurement or calibration** instead of a value).

**Bound skills** (the person, 2026-11-09; §14-30). The Reasoning stage is done with skills written as source code: each computes a maximum or a minimum of one parameter from one physical, numerical or instrument reason, and the model takes the ones a request needs. The model chooses and binds inputs to rows; code runs the skill, writes the bound as a `computed` row and intersects the bounds into the feasible interval. A skill has the bundle's skill layout (§5.1 S5), so the ones a specification used travel into the bundle.

**Rough ranges, and the model's choice** (the person, 2026-11-09; §14-32). Limits are tied to one another, so they are considered together and not one parameter at a time: the scales of the system → the requirements that follow from them and from the request → the tool's discrete configurations, listed in full by code → the configurations that meet the requirements, and the rough range each key quantity takes across them. Every quantity on the way is given by a skill (an estimate of a scale, what a configuration delivers, a bound). The model reasons over these and sets the engine parameters by choosing (which skills apply, which quantity is fixed first, which rule or candidate is taken) and saying why; code computes every value, so a model's own number still enters nothing. The pass is a card of its own, `range_sheet`. In a built agent the choice is made among its subagents (§14-33).

**Tiered search** (default order, not a trust ranking): 1 verified experimental data (measurement databases, public datasets, in-house measurements) → 2 curated models and open-source parameters (correlation libraries, potential and force-field repositories) → 3 literature (body and supplements) → 4 evidence check and comparison (units, conditions, uncertainty, valid range, source agreement) → 5 a `parameter_sheet` row, or a `gap`.

**Source adapter candidates** (`meta_agent/src/sources/`), all **to verify** (existence, access path, coverage and update time, license and terms, the `value_kind` of returned values):

| Area | Candidates | Expected role |
|---|---|---|
| fluid and thermodynamic properties | NIST ThermoML (REST serves metadata, numbers come from archive files; archive coverage date to verify), NIST Chemistry WebBook, `chemicals` / `thermo` (Python), CoolProp | viscosity, density, interfacial tension, thermal properties; correlation results marked `correlation` |
| species identification | PubChem | CAS, identifiers, molecular data |
| simulation parameters | NIST Interatomic Potentials Repository, OpenFF Toolkit, each engine's official models | potential and force-field parameters with source and version |
| special and rheology data | Zenodo, individual NIST datasets (photo-rheology, thermoset rheology), paper supplements | non-Newtonian response is not fixed by the material name: η = η(T, c, γ̇, M_w, history, …); conditions go on the row |
| helper libraries | `thermoml-io` (unofficial, new) | ThermoML archive search and parsing |

First comparison trial (M3): the same substance under the same conditions through two or more adapters side by side; the row must keep which value is measured and which a correlation.

**Protein area** (adapters when a request asks, MP8; the card format is fixed now). A `protein` entry: identifiers (UniProt / PDB / design id), origin (`natural | de_novo | engineered`), composition (sequence, length, molecular weight), structure (secondary, coordinates, assembly), properties (pI, stability, aggregation propensity), function (target, affinity, activity), validation state (`experimental | computational | unverified`), evidence (DOI, dataset version, conditions). `parameter_sheet` rows link through `protein_ref`. **Composition is separated from condition-dependent measurements** (oligomeric state, binding sites, crosslinking, properties at concentration / temperature / solution conditions); the latter are condition-tagged `parameter_sheet` rows. Three rules: **a predicted structure and an experimental one are different `value_kind`s** (`predicted` vs `measured`); **confirmation of existence / structure and of function / properties are recorded separately**; **design tools (RFdiffusion, ProteinMPNN, …) are not databases**, and protein design is out of scope until a request asks. Search path (Conversation 2): query → natural proteins via UniProt and InterPro, designed via PDA and Proteinbase, 3D structures via RCSB PDB and ModelArchive, experimental properties via ProtaBank and papers → **cross-validation** (sequence identity, structure provenance, conditions) → `protein` entry + rows. Sources (to verify): UniProt, InterPro, Protein Design Archive, Proteinbase, RCSB PDB, ModelArchive, AlphaFold DB, ProtaBank.

**Hardware**: as in v0.1, `vendor_spec` is not this instrument's measurement and `bench_confirmed: false` is the default.

### 5.4 F4 Experience Memory (`meta_agent/cases/`)

**Collected** (Conversation 1 §6.1): research goal, tool and system state at run time, knowledge and parameters used (refs), plan vs actual conditions, result, failures and exceptions, the researcher's interventions, attempted fixes and their outcome. Sources are the read-only paths of `observed.json` (§5.5) or `observation` cards.

**One case, one file**, with the v0.1 fields plus:

```
cue:          the shape of the situation the lesson applies to (a pattern, not this task's facts)
lesson:       an operation written so that it can be applied and checked, naming the component
evidence:     the runs, commits and cards it rests on, and their contrast
confidence:   high | medium | low, and why
cause_status: observed | suspected | confirmed     (confirmed needs run or commit evidence)
```

Too general is useless ("be thorough"); too specific never fires again (harness2). `cue` is written between.

**Recall**: deterministic — intersection with the input card's `signature` (task, tool, methods, observables, parameters, cause class, condition tags); same input, same output; sorted by grade → count → id. Text similarity is §14-7.

**Promotion**: a case with `cause_status: confirmed` and `count.supports ≥ N` (N is a person's; UNDECIDED before) becomes (a) a `kb_candidate` or (b) a `harness_proposal` of kind `reshape` (a skill). Scope and limits of the original case travel with it.

**Seeds**: SMA's `failures.jsonl` and `incidents.jsonl` are prior entries and get a verdict (`transfer | downgrade | drop`) and the source commit. The person's permission comes first (§14-6).

### 5.5 F3 Meta-Harness (`meta_agent/harness/`)

SMA §8.3's loop (observe → classify → propose → prove → gate → land → measure → retire) and rules 1–7 are adopted. **Scope (settled 2026-11-08, §14-28):** of the loop, only the steps code fills are built: observe (`observe.py` drafts incidents from the record), prove (`prove.py` runs the proof and writes its fields), gate, land by the owning seat, measure (the ledger and the computed `confounded` precedence) and a `retro/` written by code from the period's record. Classification stays the model's draft with `path: undecided` until evaluation; no retro, proof or classification is typed by hand, and the rest of this section is built only when a run shows the need. Added:

**Observed**: this repository (`failures.jsonl`, verdicts, refusals, `--no-verify`), built agents (read-only paths in `envelope/observed.json` with the commit hash read; `degraded` when unreachable), incidents between sessions (`incidents.jsonl`), onboarding records (unnecessary questions, wrong inferences).

**Where the two paths live**: knowledge-based improvement changes entries and cases and ends in F1 / F4 cards. Only structural improvement becomes a `harness_proposal`. One incident may spawn both; which it was is decided by evaluation (§11).

**Two levels of recursion** (harness2 under our rules):

| Level | What | Our way |
|---|---|---|
| build level | within one request, probe k candidate bundles with **the same validation tasks** and compose from the contrast of runs | k is a person's budget (default 1). Probe = mock replay + the two deterministic gates. Compose = a model-written draft. Adoption = gate + owning seat. **The baseline (unedited bundle) is judged first; if it fails, "no verdict"** |
| harness level | adopted harnesses and lessons accumulate in a per-domain library that the next build in the same domain reads first | `harness/library/<domain>/<build_id>/{diff, EXPERIENCE.md}`. Domain = the registry's method or tool kind (`rheometer`, `cfd_solver`, `md_engine`, `microscope`, …). Separated by run configuration (model, runner, k, seed) |

**Proposal card additions**: `edit_rows[]` = `{component, change, observed (which run diverged where), verdict: helped | hurt | no_observed_effect | confounded}`. If a candidate changed several components at once or there was one rollout, `confounded` **takes precedence**. A lesson resting only on `confounded` does not enter the library (`NO_ENTRY`).

**Proof**: tightening needs (a) a fixture reproducing the incident (failing before, passing after) and (b) history replay (no new FAIL). Instruction and skill changes need (c) unchanged verdicts in `replay/` and `validation/`. Every change leaves **contrastive evidence** (same task, runs before and after the edit) as `edit_rows`.

**Budget ledger**: each `ledger.jsonl` line carries rollouts, improvement sessions, tokens (in, out), wall-clock time, cost (as the provider states it, otherwise computed from public prices and marked "computed"). Only like configurations are compared.

**Revert**: revisions are append-only, so a "revert" is a new revision that re-adopts an earlier one; a recorded regression is marked `reverted_by` in the ledger.

**Core (propose only, never land)**: MP1, MP4, MP10, MP11, grade derivation and E6 exclusion, the person's seating, the gate's existence, SMA §8.3 rules 1–5, a built agent's `envelope/` and `approvals/`, the Lab Profile's policy fields, changes to safety policy and execution permission (managed apart from ordinary improvement).

**External engine**: harness2 as an engine is §14-8; if used, only under SMA §8.3's 2026-10-19 trial design, on a computer without instruments, outside the working folder, output = proposals.

### 5.6 Simulation Method Registry and Lab Profile

**Three layers.** Simulation is not a ladder DFT → MD → BD → CFD. Scales overlap, one physical model is implemented by several programs, and one engine supports several methods (Conversation 2).

```
Physical scale  ──▶  Modelling method  ──▶  Simulation engine      (method ↔ engine is many-to-many)
electronic / atomistic / coarse-grained / mesoscale / continuum
```

**Registry** (`contracts/registry/{methods,engines,instruments}.json`): a list, not a ranking (MP12). Each item: `{id, name, scale[], methods[] (engines), interface: python_api | input_file_cli | gui | sdk, language, license (may say "to verify"), material_refs[], verified: {by, date, evidence}}`. M0 seeds the files with the representative examples below, all without `verified`; license and version are entered after M2's verification.

| Method | Representative tools (to verify) | What matters in settings / GUI |
|---|---|---|
| electronic structure / DFT | Quantum ESPRESSO, CP2K, VASP | atomic structure, electronic state, basis, k-points |
| molecular dynamics | GROMACS, LAMMPS, OpenMM | atoms and molecules, force field, topology |
| Brownian / coarse-grained dynamics | HOOMD-blue, LAMMPS, in-house code | particles, potentials, diffusion, friction, boundary conditions |
| mesoscale / multiphase | LAMMPS, OpenFOAM, dedicated LBM / DPD codes | phase composition, particle–fluid interaction, interfaces |
| CFD | OpenFOAM (+ RheoTool), SU2 | geometry, mesh, boundary conditions, solver |
| structural / FEM | FEniCSx, deal.II, Abaqus, COMSOL | mesh, constitutive model, loads, constraints |
| (instruments) | microscope, rheometer, … | control interface, measurement conditions, calibration, the place of safety limits |

HOOMD-blue does MD and BD, CP2K does DFT and MD, FEniCSx goes beyond structural analysis to general PDEs: method and engine are many-to-many.

**Lab Profile** (`meta_agent/profiles/<lab_id>/v<N>_lab_profile.json`). **Environment and constraint information for agent generation**, not central management of labs. Every field has the three states (§5.0) and evidence.

| Group | Fields | Example |
|---|---|---|
| tools | `preferred_engines[]`, `preferred_instruments[]` (registry ids) | HOOMD-blue; the microscope |
| hardware | `hardware` | CPU, GPU, HPC cluster, isolation of the instrument computer |
| software environment | `software_env` | Python, C++, MPI, conda / pixi, OS |
| existing assets | `existing_code[]`, `existing_data[]`, `validated_workflows[]` | repository links, input files |
| scientific conventions | `conventions` | unit system, force field, validation criteria, naming |
| GUI preference | `gui_preference` | none / parameter_form / visual_editor / reuse_existing |
| operating constraints | `operational_constraints` | licenses, permissions, supported OS, network |
| collaboration | `collaboration` | first_agent, existing_agents[], bridge, mode |
| **policy** | `policy` | working mode, approval mode, publication scope, execution permission, external transfer of private code — **`confirmed` required** |

`agent_spec` A1, A2, A5 and `synthesis` read the Lab Profile. The recommended engine is `lab_profile.preferred_engines` when present; only without it does the registry propose candidates by method, with evidence.

### 5.7 GUI (optional)

**Principle**: MP13. Three things from HOOMD_GUI: visual modelling, transparent code generation, separated scientific core.

**Structure** (Conversation 2): one GUI for all simulations is too much; one per program cannot be maintained. So three layers.

| Layer | Content | Shared |
|---|---|---|
| common frame | Project (with "Add material", §5.0 path (e)) · Parameters · Validation · Execution · Results, card I/O | **shared** (workflow and card interface) |
| domain editors | particle editor (MD, BD) / mesh editor (CFD, FEM) / structure editor (DFT, molecules) / instrument panel | per domain; physical models are not forced into one universal schema |
| per-tool scientific core and adapter | validation, code generation, run interface, result processing | per tool; outside the GUI, shared with CLI and agents |

**Options** (wizard question 7): none / basic parameter form / domain visual editor / reuse the lab's GUI. A GUI is not required.

**Derivation**: `gui_spec` is derived from `CAPABILITIES.json` and `tools/*/tool.json`. Every GUI input maps to a tool parameter or a capability item (check B10); no numeric threshold lives in GUI files (values come from `envelope/` and the scientific core). GUI validation **calls** the scientific core's validator and has no rules of its own. A new engine reuses the common components; only special functions are defined separately.

**Start**: full automatic GUI generation is too large. Start from **a composition of validated common components**; new components only for special visualisation. Reference case HOOMD_GUI (particle based). The common elements for DFT / CFD / FEM are judged after surveying those tools. Architecture and stack are not decided now (§14-16).

---

## 6. Cards

### 6.1 Types

| Card | Written by | What |
|---|---|---|
| `material` | the person (location) + the intake seat (metadata, `inferred`) | one manual, paper or link; source snapshot; state |
| `discovery_report` | the onboarding seat | Step 0's findings: per field `inferred` + evidence, or `unknown` |
| `onboarding_record` | the onboarding seat (+ the person's answers) | what was asked, the answers, what was skipped and why |
| `lab_profile` | the onboarding seat (+ the person's `confirmed`) | §5.6's table, every field with state and evidence |
| `agent_goal` | the person → the executing seat | why and what the agent is for; no numbers |
| `tool_profile` | the executing seat | the tool's capabilities and limits; per claim kind, evidence, limitations; permission record |
| `knowledge_brief` + `kb_entry` | the executing seat | entries and gaps that entered a request / one claim per file |
| `parameter_sheet` (+ `protein`) | the executing seat | §5.3's table |
| `agent_spec` (+ `spec_axis` a1..a6, `synthesis`) | the executing seat | six axes and the synthesis, `held[]` |
| `gui_spec` (optional) | the executing seat | screens and input fields, each mapped to a capability or tool parameter |
| `build` | the executing seat (+ the person's `landed_at`) | bundle, gate verdict, lineage |
| `validation_report` | the executing seat | per-task verdicts in the interface and scientific sections |
| `case` | the executing / harness seat | §5.4 |
| `harness_incident`, `harness_proposal`, `harness_ledger_entry`, `harness_retro`, `harness_experience` | the harness seat | one incident / one structural change with proof and `edit_rows[]` / one ledger line / one retro / one library lesson |
| `refusal` | anyone | why it cannot be done, with the counterexample |
| `kb_candidate` | the executing seat | an entry candidate handed to the librarian |
| `observation` | the person or the bridge (inbox) | a run, failure or success report from a built agent |
| `tool_contract`, `error_contract` | the Designer (in bundles) | a callable tool's I/O contract / the structured error it returns |

The rough-range pass has a card of its own, `range_sheet` (§14-32), and a built agent's run has four more: `run_plan`, `run_record`, `analysis`, `report` (§14-34). They are the bundle's contracts, as `tool_contract` is; their names and fields are the design seat's by the person's word, and none is written yet.

### 6.2 Common fields (compatible with SMA `common.schema.json`)

`card`, `schema_version`, `id`, `rid` (SMA's `qid`; `thread` when connected), `revision`, `author`, `created_at`, `numbers[]` (4-tuple + `value_kind`), `assumptions[]`, `kb_refs[]` / `kb_gaps[]`, `case_refs[]` / `case_gaps[]`, `degraded[]`, `status`.

### 6.3 Numbers and claims

- A number is `{name, value, unit, source, grade, value_kind}`. The grade is derived, never self-reported. E6 enters no card.
- The derivation table is `contracts/grades.json`, keyed by the source kind (the part of `source` before the colon) and `value_kind`. M0's initial table, revisable under §14-12:

| Source kind | `value_kind` | Grade |
|---|---|---|
| `measured:<run_id>` (a run of this system) | measured | E1 |
| `calibration:<id>` (an expiry is mandatory) | measured | E2 |
| `literature:<source_id>` | measured, literature | E2 |
| `database:<db_id>` | measured | E2 |
| `database:<db_id>`, `literature:<source_id>` | correlation, computed | E4 |
| `spec:<device_id>` (vendor specification) | measured, literature | E3 |
| `prior_run:<repo@sha>` | measured, computed | E3 (a run over there is not a run over here) |
| `operator_read:<id>` | measured | E3 |
| `computed:<expression_id>` | computed | E4 |
| `correlation:<id>` | correlation | E4 |
| `predicted:<model_id>` | predicted | E5 |
| `assumed:<rationale_id>`, `operator_recall:<id>` | estimated | E5 |
| any | model_generated | E6 — forbidden |

- Claims are `observed | derived | inferred | unknown` (MP9). Settings are `confirmed | inferred | unknown` (§5.0).
- Every number in an MD file must exist in a JSON card of the same folder. Significant figures follow the worst input (P15).

### 6.4 Error contract (what a generated callable tool returns)

`{code, category, message, retryable, remediation: {action}, evidence?}`. `category` starts from REA's vocabulary — `invalid_input | unsupported_target | integrity_mismatch | truncated | cancelled | timeout | resource_constraint | unavailable | execution_failure` — plus `refused_by_safety` (a deterministic gate's refusal) and `permission_required`. Check B7 verifies it with fixture calls.

### 6.5 State machines

`draft → validated → (approved) → done | refused | held | superseded`. `held` is MP10's state and a person releases it. Records are append-only; a change is a new revision `v<N>_`. `material` has its own: `queued → registered → distilled | declined | held` (`registered` is the person's confirmation; `held` when access permission or license blocks; §5.0).

---

## 7. Repository layout

```
meta-agent/
  plan.md                     this record (English)
  CLAUDE.md / README.md / LICENSE / pyproject.toml / .claude/settings.json / .gitattributes / .gitignore

  contracts/                  ★ the only shared code
    schemas/                  material, discovery_report, onboarding_record, lab_profile, agent_goal, tool_profile,
                              knowledge_brief, kb_entry, kb_candidate, parameter_sheet, protein, agent_spec, spec_axis,
                              synthesis, gui_spec, build, validation_report, case,
                              harness_{incident, proposal, ledger_entry, retro, experience}, refusal, observation,
                              tool_contract, error_contract, common
    registry/                 methods.json, engines.json, instruments.json  (lists, not rankings; verified field)
    units.json                unit registry (SMA format: multiplicative, dimension vectors; kelvin only)
    grades.json               grade derivation table (§6.3)
    case_classes.json         cause class vocabulary
    claim_kinds.json          claim kinds, cause states, setting states, value kinds, policy fields, error categories
    records.json              append-only roots and the revision rule read by check 7
    seats.json                committer identity → boundary
    validate.py               deterministic validator (§8); --bundle for the bundle gate (later)
    examples/ + examples/rejected/
    hooks/                    pre-commit
    tools/seat_commit.py      (§14-9, later)

  meta_agent/                 ★ the one agent; movable together with contracts/
    CLAUDE.md / README.md / .claude/settings.json   (Tier 0; no writing outside builds/; two-shell twins)
    tasks/ · failures.jsonl · envelope/observed.json
    inbox/<thread>/           observations from the bridge or the person
    inbox/materials/README.md            "A link on one line is enough" (how to drop material, what happens next)
    inbox/materials/LINKS.md             the person's links, one row each (any time)
    inbox/materials/drop/                the person's files (any time; moved into a dated folder on intake)
    inbox/materials/<YYYYMMDD>-<slug>/   intaken material + MATERIAL.json (made by the Meta-Agent)
    profiles/<lab_id>/        discovery_report, onboarding_record, v<N>_lab_profile
    requests/<rid>/           agent_goal, tool_profile, knowledge_brief, parameter_sheet, spec_a1..a6, synthesis,
                              agent_spec, gui_spec, build, validation_report, refusal, failures.jsonl  (flat, v<N>_ revisions)
    knowledge/{sources, distilled, entries, index.json}   sources/raw/ holds copies only when may_quote: true
    cases/<case_id>.json + index.json
    harness/{incidents.jsonl, proposals/, ledger.jsonl, retro/, library/<domain>/<build_id>/}
    templates/agent@<hash>/   bundle template (harness surface + tools/ + validation/ + envelope/ skeleton + gui/ common components)
    builds/<agent>/<build_id>/  bundle + build card + validation_report
    eval/                     the four-condition task sets, configurations, results (§11)
    src/                      onboarding/, materials/, intake/, tooling/, knowledge/, sources/, parameters/,
                              spec/, build/, gui/, validate/, cases/, harness/   (one-way dependencies, no sibling imports)
    tests/

  docs/ideas/<YYYYMMDD>.md · docs/origin/PLAN.ko.md · docs/reference/<name>.md
```

---

## 8. Validation layer (`contracts/validate.py`)

Numbers are fixed and never reused after retirement. M0 implements 1, 2, 3, 6, 7, 11, 15, 16, 17; M1 added B1–B9 (`--bundle PATH`, and every bundle a `build` card outside `contracts/examples/` points at; a template is not a bundle and is not judged by them). Task 003 added 18 (2026-11-04). Task 009 added 20, 21 and the seat table and self-registration parts of 6 (2026-11-09); task 006's design part added 5 and 8 the same day, and task 010's added 22, B11 and the `self_calibration` part of 11; task 007's design part added 4 and 19 and, in check 2, the grade of a computed row that names its inputs; 19 and 22 are reserved by tasks 007 and 010.

| # | Check | Kind |
|---|---|---|
| 1 | every JSON with a `card` field passes its own schema (`contracts/schemas/<card>.schema.json`; the file name is not trusted; an unknown card fails) | schema |
| 2 | numbers are the 4-tuple + `value_kind`; the unit is registered; the grade equals the derived grade (`grades.json`); no E6 and no `model_generated` | numbers |
| 3 | every number in an MD file exists in a card of the same folder | numbers |
| 4 | safety values are `null` or `author: human`: a `safety_relevant` row of a `parameter_sheet` has no value but a person's and no recommended point or candidate; bounds may be attached to it as information (a bundle's `envelope/safety.json` is B3) | safety |
| 5 | `kb_refs` / `case_refs` resolve in the store's index (`cases/index.json`, `knowledge/index.json`: the nearest store at or above the card; id, and revision or hash when the reference gives one); an index is what the store's cards give (generated by `contracts/tools/cases.py`, never by hand); `*_gaps.searched` is non-empty | references |
| 6 | commit paths lie inside the committer seat's boundary (`seats.json`; unknown committer → reported, not failed; commits at or before `enforced_from` are reported only); every seat is what its name says, on a listed machine tag, and owns exactly its role's row (`roles`, from `tasks/009`); a commit that adds only the committer's own entry is judged by the standing rule of §9 against the table before the commit (name, listed machine tag, the role's row unchanged, `seated_by: self`, nothing else in the commit), for commits after `self_registration_from` | boundary |
| 7 | append-only under the roots of `records.json`; a revision is a new file `v<N>_<name>` whose `revision` is N and whose predecessor exists; a JSONL file only grows | history |
| 8 | `case` has `falsification`, `count`, `cue`, `cause_status`; `confirmed` has run / commit evidence; `cause_class` is registered and the signature's is the card's; a condition tag is `name`, `name:value` or `name:lo..hi` with lo ≤ hi; a case from a prior repository (`source_repo_commit`) is graded E3 or worse (§14-27(c)) | cases |
| 9 | `harness_proposal.kind` is one of four; loosen / retire / core need the person's words + a `docs/ideas/` commit; tighten needs a fixture | harness |
| 10 | a `ledger` line points at an existing proposal and commit; cost fields exist | harness |
| 11 | `tool_profile.claims[].kind` is one of four; evidence refs exist (`source_ref` or `rea_evidence_id`, with `locus`); `observed` / `derived` / `inferred` have evidence; `unknown` has `requires`; a claim with `basis` binary or runtime, or REA evidence, FAILS without `analysis_permission {granted_by: human, scope, basis, date}`; a `self_calibration[]` item's claim obeys the same rules, and mode `self` or `assisted` does not rest on an `unknown` claim (§14-31(l)) | tool understanding |
| 12 | `validation_report` has both sections, per-task `pass|fail|not_run`; scientific reference results have an entry or a source; without a tolerance UNDECIDED; `not_run` is not a pass | validation |
| 13 | `edit_rows[].verdict` is one of four; an `experience` resting only on `confounded` is refused from the library (`NO_ENTRY`) | harness |
| 14 | `held[]` items are not in the bundle; releasing `held` needs the person's words + a commit | fail-closed |
| 15 | every Lab Profile field has `state`; `inferred` has non-empty `evidence[]`; `confirmed` has `confirmed_by: human`; policy fields (`policy.*`, `collaboration.mode`, `operational_constraints.execution_permission`) FAIL when a `build` or `agent_goal` references the profile and they are not `confirmed`; an `inferred → confirmed` transition between revisions whose confirmer is not human FAILS | onboarding |
| 16 | each `onboarding_record.questions[]` item targets a field that is `unknown` in the referenced `discovery_report` or a policy field; a question on a `confirmed` field FAILS; a question on an `inferred` field is reported as unnecessary; each `skipped[]` item has a reason | onboarding |
| 17 | `material`: `location` has exactly one of `url` / `path`; `about.*` and `license_note` follow the three states and `inferred` has evidence; `added_by: human` and the metadata author is a seat; a `url` material that is `distilled` FAILS without `source_snapshot.retrieved_at` and `content_hash`; `archived` set while `may_quote` is not `true` FAILS; `held` and `declined` need `state_reason` | material intake |
| 18 | in every folder named `wiki/`: each page but `index.md` names one record (`- record: <path>`, a card or an artifact directory) and is titled and named `<id>@r<revision>`; every `[[link]]` names a page of that wiki and, between two records, a relation one of them holds (an id, a path or a file name, or two revisions of one id); every number left outside code spans and links is a number of the rendered card; a `graph.html` there loads nothing from another host, and its `wiki-graph` data names only pages of that wiki, with their records' `card` and `status`, and only edges one of the two pages links | view |
| 19 | every bound and every `computed` row of a `parameter_sheet` is recomputed by running the skill its `basis` names on the rows it names, in the manifest's units, within its stated uncertainty; its grade is `max(E4, worst input)`; the interval is the highest floor and the lowest ceiling and names the skills they came from; an empty interval carries no point; a value lies inside its interval; every applicable bound skill of the library at or above the sheet is in `skills_considered` as used or as not applied with a reason (§14-30; `tasks/007`) | parameters |
| 20 | the task queue: every task file has a row in `meta_agent/tasks/index.json` and their status agrees; a done row names its commit; a claim (`claims/<task>-<seat>.json`) names an open task whose dependencies are done and an active seat of one of the task's roles, one seat per role, and is committed by that seat (§14-29; `tasks/009`) | queue |
| 21 | notes between seats: one file per note, added by its `from` seat; a reply names the note it answers; a note with no reply is PENDING for its `to_role` (§14-29; `tasks/009`) | queue |
| 22 | skills: the folder and manifest are complete, a landed version is unchanged, the source reaches no device but through the tools it names and holds no limit, every worked case passes, a `write_device` skill is `held` (§14-31; `tasks/010`) | skills |
| B1 | required bundle files (§5.1 S5) | build |
| B2 | every `Bash(...)` deny / ask has a `PowerShell(...)` twin and vice versa | build |
| B3 | all values of `envelope/safety.json` are `null` | build |
| B4 | `snapshot.json` entry hashes match `knowledge/`; `kb_version` pinned | build |
| B5 | `replay/` and `validation/{interface,scientific}/` each have at least one task with an expected verdict | build |
| B6 | every number in the bundle's `CLAUDE.md` exists in `snapshot.json` | build |
| B7 | every `tools/<name>/tool.json` passes `tool_contract`, and fixture calls honour the error contract | build |
| B8 | every skill has a trigger sentence in `CLAUDE.md`; named scripts exist; no `inferred` claim in `CAPABILITIES.json` | build |
| B9 | safety-relevant tool call paths have the place of a deterministic gate (A5); a tool that only reads an instrument (`reads_instrument`) is not one | build |
| B10 | with `gui/`: every `gui_spec` input maps to a `tools/*/tool.json` parameter or a `CAPABILITIES.json` item; no numeric threshold in `gui/`; the GUI validation hook calls the scientific core's validator | build |
| B11 | skills and subagents of a bundle: every skill a subagent or `CLAUDE.md` names is in `skills/`; a subagent's `side_effects` cover the skills it names; one subagent alone lists `write_device`; a skill's `calls_tools` exist under `tools/`, those of a `write_device` skill ask for the gate, and a `read_device` skill calls no tool that changes anything (§14-31; `tasks/010`) | build |

Rules (from SMA): check and fixture in the same commit; a new fixture is watched failing first; `--expect-fail` must reject both totals in full; UNDECIDED and PENDING are not passes; every number is read off a run and the verdict line names the judged tree.

**How M0 runs checks 6 and 7.** Both read git: `--staged` judges the index against the committer identity git will use (the pre-commit hook's mode), `--commit-range A..B` judges each non-merge commit. Their logic is also exercised without git through `scenario.json` fixtures under `examples/rejected/` (a committer email with its changed paths; a list of status-and-path changes), so that `--expect-fail` covers them deterministically.

---

## 9. Permission model

**Seats**: `design-…` (root files, `contracts/`, `docs/`, `meta_agent/CLAUDE.md`, `meta_agent/.claude/`, and in M0 the `meta_agent/` skeleton it creates), `meta-…` (the rest of `meta_agent/`; onboarding too), from M5 `harness-…` (`meta_agent/harness/`). The person assigns a seat per session, or, under the person's standing rule of 2026-11-09 (`docs/ideas/20261109.md`), a session registers its own: a name of the pattern, a machine tag the person has already given, one of the three roles as the person or the session's task names it, the role's paths copied unchanged, in its own commit before any other work, marked `seated_by: self`. Names are `<role>-<machine>-<YYYYMMDD>-<n>`; the Office computer's tag is `office` and the MacBook Air's is `macbook` (`machines` in `seats.json`). The committer is `seat:<name>` <`<name>@seat.invalid`>, the author stays the person.

**Human-only**: safety values, seating outside the standing rule above (a new role, a new machine tag, a wider path), bundle hand-over (`landed_at`), permission to loosen / retire / change the core, thresholds (tolerance, k, N), verdicts on prior entries, **confirmation of analysis permission** (`analysis_permission`), release of `held`, validation tasks on hardware, **answers to policy questions and the `inferred → confirmed` transition**, publication scope, dropping material (giving the location) and confirming intaken metadata, quotation permission (`may_quote`) and license judgements.

**In a built agent** (the person, 2026-11-09; §14-33(i), §14-34(d)). Whether an agreed range is adopted as it stands, and with it whether a run on hardware starts without a person being asked, is a policy setting its user writes and may change; it is never inferred and a bundle ships it unset. Whether such a run is blocked where the bundle's gate has no limit check is a second setting of the same kind. Neither reaches safety values, the release of `held`, or what the gate refuses. Where the person has set no safety value for a quantity, the operable range the agent scanned from the device stands in for it at the gate (§14-36(f)), unless the person has marked that row as one no range may stand in for; a safety value itself is still written by a person only.

**One working copy, no worktrees** (SMA's decision). Commits name their paths; work lands on `main`. Several seats may work in it at the same time (the person, 2026-11-09): the committer is then set for the one commit, not in the repository's configuration, and a commit takes only the paths it names (§14-29, `meta_agent/tasks/009`).

**Isolation**: adapter validation for software tools in an isolated environment outside the working folder (a container or a separate WSL directory), network limited to the hosts needed. Mock only on an instrument computer. A GUI Local Runner, if any, is loopback only (HOOMD_GUI's default). URL access from the materials inbox is read-only and uses no stored credentials or login sessions (`held` if needed).

---

## 10. Testbeds, reference case, bridge

| Testbed | Target | Purpose | Notes |
|---|---|---|---|
| **A** existing agents | SMA's microscope agent and HOOMD simulation agent | comparing the two improvement paths (§11). The Designer proposes **revisions** only. The first real input of onboarding Step 0 (the SMA repository) | not a first build target. Observation through read-only paths or the bridge; changes land through SMA's owning seats |
| **B** rheometer — **first testbed** | the lab's rheometer (TA Instruments per the proposal; model and software §14-21) | generating an agent for a new instrument interface: control interface, measurement conditions, calibration, units, operating limits, validation procedure | analysis permission for the control software is confirmed by a person in S2. Safety values are the person's. The execution engine is the owning seat's with the person |
| **C** rheology engine — **first testbed** | a rheology simulation engine; candidate RheoTool (C++, OpenFOAM based, GPL-3.0); another engine goes through the same procedure after registry entry (§14-20) | does the same procedure work for a non-Python, configuration-file, command-line, result-parsing interface; computes with B's fluid, model and units | with source, ordinary tools. Scientific validation starts from **flows with analytic solutions** (Newtonian planar Couette flow, steady shear viscosity of a viscoelastic model) |
| cross-validation | **rheometer ↔ rheology engine (model, units) — the first testbed's completion condition**; microscope / HOOMD ↔ rheometer (micro dynamics ↔ macro rheology) | comparison across tools | the comparison itself is the bridge's job; the Meta-Agent makes both agents' cards share quantity, unit and condition fields |
| multiscale coupling (long term) | linking simulations at different scales | explicit interfaces and conversion conditions (units, scales, boundary data) | **the Meta-Agent never integrates engines.** A bridge or coupling tool does; the Meta-Agent writes the conversion conditions as cards |

**Reference case**: HOOMD_GUI is registered in `docs/reference/hoomd_gui.md` as the particle-simulation GUI reference (with the fact check of §2.6). Code reuse after its license exists.

**First testbed (decision, 2026-10-29, the person)**: **the lab's rheometer (B) and a rheology simulation engine (C), as a pair.** The goal is not two agents but the cross-validation card that puts measurement and computation side by side with the same fluid, model and units. Both agents' `parameter_sheet` and `validation_report` therefore use the same quantity names and the same unit registry from the start (checks 2, 3).

**Order inside the pair (recommendation)**: **C → B → cross-validation.** C has no hardware and so no P0 exposure, tests generalisation on a non-Python interface, and has analytic solutions for scientific validation. B reuses C's results (interface contract, validation task format). In both cases S0 runs first and this lab's `lab_profile` comes into being. M0–M5 proceed before the engine (§14-20) and the rheometer specification (§14-21) are settled; the moment their materials enter the inbox, S0 runs for those items.

**Bridge readiness**: `meta_agent/` + `contracts/` is a movable unit; common fields are compatible; `inbox/<thread>/` is reserved; when connected, the librarian is the knowledge authority; what happens when there are two `contracts/` is §14-3. If the wizard's collaboration question is "yes", a bridge plan goes into `agent_spec.A2`.

---

## 11. Evaluation

**Principles**: the two loops are measured separately. The baseline is judged first. Judgement and reporting use the same task set, runner, model, k and seed. A failed evaluation is "ungraded", not zero. Sample sizes and pass criteria are chosen by a person **after baselines are collected** (proposal §2.4).

**Four conditions**: C0 no improvement / C1 structure only / C2 knowledge only / C3 both. Configurations and results in `eval/<set>/<condition>/`. Turning knowledge off = building the bundle with `degraded: [knowledge, cases]`; turning structure off = the template's bundle as is.

| Group | Metrics | Read from |
|---|---|---|
| agent development | working time; the researcher's manual configuration and intervention counts; **the wizard's question count and unnecessary-question count**; fields the person wrote per material (target 1: the location); the range of validated capabilities; adaptation to new interfaces (C vs existing); **time to the first scientifically valid run** | `onboarding_record` in `profiles/`, `added_by` and `entry_path` in `inbox/materials/*/MATERIAL.json`, timestamps in `requests/<rid>/`, intervention records in `docs/ideas/`, `validation_report` |
| scientific performance | quantity and unit correctness, validity of parameter recommendations, reproducibility, agreement with reference results, failure detection and recovery | `validation_report`, `case` |
| self-improvement | differences between the four conditions, recurrence rate of incident classes, revert count | `incidents.jsonl`, `ledger.jsonl`, `eval/` |
| operating efficiency | the person's time, error recovery rate, latency, tokens and cost, regression rate after improvements | `ledger.jsonl`, run logs |

Manual vs Designer-assisted configuration is compared on **paired tasks** (same tool, same goal).

---

## 12. Milestones

Names are chunks of work, not an order. Only M0 blocks everything else.

| M | Chunk | Done when (read off a run) |
|---|---|---|
| **M0** | contracts: all schemas, `validate.py` checks 1·2·3·6·7·11·15·16·17, examples + rejected fixtures, `seats.json`, registry seeds, `inbox/materials/` (README, LINKS.md, drop/), hooks, `CLAUDE.md`, `plan.md` | `0 failed`; `--expect-fail` rejects both totals in full; seat committer from the first commit |
| **M1** | onboarding + Designer skeleton: Step 0 (read the materials folder and repositories) → Step 1 (ask `unknown` only) → Step 2 → Step 3 → `agent_goal` → `tool_profile` (documents only) → `agent_spec` → template v1 → **echo bundle** → interface gate B1–B9 → `validation_report` | on a material-rich fixture lab only **policy questions** appear; on an empty lab the full set appears (both read from `onboarding_record`); the echo bundle passes both gates (the scientific gate with one trivial task) and handles one `replay/` without the Meta-Agent |
| **M2** | Knowledge Engine: sources / distillation / entries, `value_kind`, conflicts, index, `knowledge_brief`, `inbox/materials/` intake (metadata inference, URL snapshot, the person's confirmation) and queue, `add-material`; **verification of the source adapter candidates and the registry's representative entries** (existence, access, coverage, license) and one first adapter | at least one entry with a derived grade and one gap with `searched`; verification results exist in `knowledge/sources/` and as `verified` in `registry/*.json` |
| **M3** | Parameter Intelligence: three stages, tiered search, bound skills (§14-30), the rough-range pass and the model's choice (§14-32), a comparison trial across two or more sources (correlation skills, §14-26(e), or adapters), the `protein` card format (composition / condition separation) | a sheet with empty safety rows passes check 4; a filled one is a rejected fixture; every row of the comparison keeps its `value_kind` |
| **M4** | Experience Memory: schema (`cue`…), vocabulary, `recall.py`, injection, promotion rule, SMA seed transfer (if permitted) | a new `agent_goal` carries `case_refs` or `case_gaps`; same input, same output |
| **M5** | Meta-Harness: incidents / proposals / ledger / retro / library, `edit_rows`, `observed.json`, replay, ratchet, **the four-condition evaluation harness (mock)** | one tightening lands with fixture + replay; one loosening is refused without the person's words (fixture); the four conditions run on the echo task set |
| **M6** | **Testbed C**: the rheology engine agent (candidate RheoTool; §14-20) — this lab's S0, source-analysis `tool_profile`, adapter (configuration file, command, result parsing), sandbox interface validation, analytic scientific validation, hand-over | `validation_report` both sections `pass` (no hardware tasks); the owning seat lands it at the destination and records `landed_at` |
| **M7** | **Testbed B**: the rheometer agent — permission confirmation, `tool_profile` within the permitted scope, adapter and execution-engine **skeleton**, safety values `null`, mock validation | both sections `pass` in mock, bench tasks `not_run: requires bench`; safety values filled by the person at the destination |
| **M8** | bridge and cross-validation: **completion of the first testbed** (the rheometer ↔ rheology engine cross-validation card, same fluid, model, units), inbox round-trip mock, card compatibility, testbed A's observation path and four-condition comparison | `r1_ask_*` is read and `degraded` propagates; A's four-condition results exist in `eval/` |
| **M9** (optional) | GUI: common frame + a parameter form derived from `CAPABILITIES.json` for the first agent with a `gui_preference`; domain editors after | B10 passes; a value entered in the GUI goes through the same scientific-core validator and gets the same verdict as the CLI (confirmed by replay) |

---

## 13. Non-goals

Instrument operation; running simulations (mock and sandbox validation excepted); a console UI; a web service. Permanent central coordination of many Scientific Agents (the bridge's job); central management of labs (the Lab Profile is a generation input). Integrating engines of different scales inside the Meta-Agent. Full automatic GUI generation from day one; forcing engines or languages. Widening execution permission without a person; retraining model weights. Auto-merge, auto-landing; a general agent framework. Vector stores, embeddings, crawlers (condition §14-7); embedding REA or harness2 as engines; embedding protein design tools. Deployment structures tied to an external cloud service.

---

## 14. Open questions (the person's decisions)

1. **Repository location and git init.** Settled 2026-10-29: `D:\codes\github\meta-agent`, GitHub `kyu-softmatter/meta-agent`, private, MIT. **Public since 2026-11-09** on the person's word ("Yes, make public", `docs/ideas/20261109.md`); MIT stands.
2. **Language of the record.** Settled with the approval: English `plan.md` is the record; the Korean plan is frozen at `docs/origin/PLAN.ko.md`.
3. **The relation of `contracts/`.** Recommendation: copy SMA's `common.schema.json` and `units.json` pinned to a commit hash and record the provenance. When connected, which side is the record? (M0 wrote its own `common.schema.json` and `units.json` in SMA's shape rather than copying, because SMA's carry microscope-specific vocabulary; the question of the record when connected stays open.)
4. **First real agent.** ~~Recommendation C RheoTool → B rheometer.~~ **Decided 2026-10-29: the first testbed is the lab's rheometer (B) and a rheology simulation engine (C) as a pair; done = their cross-validation.** The order inside the pair stays a recommendation (§10). Remaining: §14-20, 21.
5. **Runtime.** Do built agents run as Claude Code sessions, or also as SDK processes? Recommendation: emit skills in a **portable layout** (`skills/<name>/SKILL.md` + plugin manifest) like REA, and vary only the per-runtime installation. The tools would then reach both runtimes the same way, through one MCP server per bundle (§14-24).
6. **Seed transfer.** Settled 2026-11-08 (`docs/ideas/20261108.md`, "Take all six", to the fifth item of the list shown that day): permitted. SMA's `failures.jsonl` (119 lines over four agents at `d68ee7d2`, branch `closed-loop-validation`, 2026-11-05) and `incidents.jsonl` (119 lines, from history at `7bc5a0f9~1`) become seed cases, each with a verdict `transfer | downgrade | drop`, the source commit and a grade capped at E3 (§14-27(c)); done in `meta_agent/tasks/006`. The question as asked: permission to move SMA's `failures.jsonl` and `incidents.jsonl` into cases.
7. **When to introduce text similarity or vector search.** Recommendation: after deterministic matching produced `case_gaps` and the person found the relevant case by hand N times.
8. **harness2.** Reference only (recommendation, now), or trial as an engine (after M5, under SMA's trial design, on a computer without instruments).
9. **Commit tool.** When to bring in SMA's `seat_commit.py`.
10. **Licenses.** This repository MIT. Third parties (verified 2026-10-29 against each repository): harness2 Apache-2.0 (reference only; its `third_party/` keeps upstream licenses), REA MIT (called as a tool; its MIT does not cover the Hopper / IDA engines, Ghidra is Apache-2.0, its Windows addon statically links the MinGW-w64 runtime under GPL-3 with the GCC runtime exception; its DISCLAIMER leaves reverse engineering to the analysed software's license), RheoTool GPL-3.0 and OpenFOAM GPL-3 (**called out of process, never bundled**; OpenFOAM is a registered trademark), HOOMD-blue BSD-3-Clause, HOOMD_GUI **no license yet** (reference only until one exists). Not legal advice; the institution's IP policy may apply.
11. **External database access policy.** Allowed hosts, where API keys live, local archive (cache) location, each database's terms.
12. **Grade derivation for database values and predicted structures.** Which grade per `value_kind` (measurement database / correlation / predicted structure / design record). M0's initial table is §6.3. Settled in part 2026-11-08 (`docs/ideas/20261108.md`, "Take all six"): a `computed` number's grade is `max(E4, the worst grade among its inputs)`, as SMA derives it, instead of the flat E4 of §6.3; `contracts/grades.json` gains the rule as a new row with the old row kept under `retired_on`, check 2 compares against the inputs named in the row's `basis`, and a rejected fixture lands with it (`meta_agent/tasks/007`). The `database` and `predicted` rows stay open.
13. **Timing of the protein area.** Card format in M3; adapters when a request asks (recommendation).
14. **Procedure for confirming analysis permission.** Who (a person), with what (license clause, vendor consent), where (`docs/ideas/` commit → `analysis_permission.basis`).
15. **Threshold list (UNDECIDED).** Scientific tolerance, build-level k, promotion count N, four-condition sample size. All chosen by a person after baselines.
16. **GUI scope and stack.** Whether to do M9; whether HOOMD_GUI's `web/` + `python/` structure is the starting point of the common frame (after its license); whether to start with a parameter form only (recommendation).
17. **Lab Profile scope.** This lab only (recommendation, now) or several labs; if several, how `lab_id` is assigned and what profiles share.
18. **Materials for preferred simulation engines and experimental platforms (a slot, not a question).** PDFs or links for manuals, API documentation, papers and specifications are **not needed now**; drop them whenever they exist: one row in `meta_agent/inbox/materials/LINKS.md` or one file in `drop/` (§5.0). Targets are the four tools of §0 and any other engine (LAMMPS, GROMACS, OpenMM, OpenFOAM, FEniCSx, …) or instrument the lab uses or plans to use. Intake → confirmation → distillation → discovery re-run for that item; design and build never wait. **As of 2026-10-29: none; to be dropped later.** The rheometer's and the rheology engine's materials (§14-20, 21) are used first.
19. **This lab's onboarding answers.** What the wizard will ask that no material can infer: main research kinds and methods (multiple), preferred languages and environments, publication scope of agents and results, approval mode (which actions need a person), collaboration mode with the existing SMA agents (bridge). Answer now or when M1's wizard asks.
20. **Choice of the rheology simulation engine.** Candidates: the proposal's RheoTool / OpenFOAM (continuum, viscoelastic CFD); for particle- or coarse-grained suspension rheology, HOOMD-blue (BD), already in SMA. Which, or both, is the person's. Once chosen it is registered and its materials are the inbox's first item. With two engines C splits in two and the person orders them.
21. **The rheometer's specification.** Model, control software and its API / scripting interface, data export format, basis of the analysis permission (§14-14). The proposal says only "TA Instruments" (to verify). This answer is the minimum for B's `tool_profile` to start; safety values (torque, temperature, gap limits) are written by a person even then.
22. **What S2's six REA points need before the first real target** (§5.1 S2; the person's words of 2026-11-05). (a) Units for bandwidth: `B/s`, `bit/s`, `B` and an information dimension in `contracts/units.json` (none is registered). (b) Grades: `contracts/grades.json` has no row for a value read from a binary (a constant in the code is neither a vendor spec nor a measurement) or for a value measured from a capture file; until rows exist such a value cannot enter a card. (c) The capture of the real link: the Meta-Agent never reaches the instrument, so either the person captures on the instrument computer and drops the file, or the vendor's offline or simulator mode is captured in the replica; which, per instrument, is the person's. (d) Tools, entering `tools.lock.json` only when a request needs them (MP8) and then fetched by the Meta-Agent itself (§2.3, §14-23): Frida's native module (REA's install scripts are not run now), TShark and capinfos for capture files, sigrok-cli for logic or serial recordings (Linux); Ghidra (Apache-2.0) for native, non-managed code, without which REA's disassembly and decompilation tools (call graph, pseudo-code, value tracing) do not run: REA 6.8.0 on this computer reports the Ghidra provider `not_configured` and asks for a Ghidra 12.1.x directory, REA's Windows guide (repository main) needs a 64-bit JDK 21 or newer and admits 27 read-only Ghidra operations, and the newest Ghidra release (12.2, 2026-10-22) is outside what REA names, so the pin follows REA; a .NET decompiler for managed code, ILSpy (MIT, command line `ilspycmd`, latest release v11.2), whose C# output REA imports as analyst inference (`import_managed_reconstruction`), never as an observation. REA's own managed metadata reading (provider `rea-dotnet-static`, 3 operations available here) runs without either. Recommendation: settle (a) and (b) together with (c) when §14-21 names the rheometer's control software; whether that software needs Ghidra or ILSpy follows from whether it is native or managed, which `inspect_managed_artifact` answers without either.
23. **Fetching tools by itself** (§2.3; the person's words of 2026-11-06). (a) Settled 2026-11-06 (`docs/ideas/20261106.md`, "묻지 않기"): the first pin of a tool not yet in `tools.lock.json` needs no yes; the Meta-Agent pins and fetches it, and the pin's commit is the record. (b) A project permission rule in `.claude/settings.json` that lets `python bootstrap.py install` run without a prompt: a persistent configuration, so the person's; recommended for that one command only, since it installs nothing that is not pinned. (c) A check on `tools.lock.json` (each entry names a version, its own source, a checksum or commit, and a license) with its rejected fixture, landing with the first new pin; since no person looks at a pin before it is used, this check is the only guard between a pin and its use. (d) Installers in `bootstrap.py` for Ghidra (12.1.x, §14-22(d)), a 64-bit JDK 21 or newer and ILSpy, built when the first real target needs them (MP8).
24. **A bundle's tools as an MCP server** (§5.1 S5, §14-5; written at the person's word of 2026-11-06, `docs/ideas/20261106.md`; a recommendation, nothing is built). Recommendation: each bundle serves its tools as one MCP server, `src/mcp_server.py`, started by the bundle's own `.mcp.json`. Its tool list is read from `tools/*/tool.json` (the `inputs` and `outputs` schemas are already JSON Schema), and every call runs the function `run_tool.py` runs (gate, input check, adapter, output check, error contract), so the server and the command line that `replay/` and `validation/` use are one code path. Reasons: the same server serves a Claude Code session and an SDK process (§14-5); permission is stated per tool (`mcp__<agent>__<tool>`) rather than for one Bash command that reaches every tool; the gate runs inside the server process, before the adapter. Which tools a landed agent may call without a prompt is a permission, so the person's at landing; the bundle ships with no allow rule. Recommended: the server uses only the standard library, so the bundle gains no dependency. Interface validation (S6) then also checks that the server's tool list equals `tools/*/tool.json`. **Not MCP**: the validation gates (`replay/`, the two gates, B1–B9), which hooks, pre-commit and the command line run whether the model calls them or not; `envelope/safety.json`, for which no tool exists; `snapshot.json`, read as a file (MP8); card writing, which is Python in `src/`; the instrument execution engine, which is reached only behind the gate and is a mock in the bundle (P0, S7). REA and the literature index stay the Meta-Agent's MCP servers and enter a built agent only when its request needs them. **What MCP does not close**, read off a run on 2026-11-06 in `meta_agent/builds/echo/0001/bundle`: `python src/run_tool.py echo` and a direct `python -c` import of `tools/echo/adapter.py` both returned the echo output (message `hi`, length 2). Echo needs no gate (`safety_gate.required: false`), so nothing was bypassed, but the direct path reaches any adapter without `gate.py`; the bundle's deny rules cover Edit and Write of `envelope/safety.json`, `CLAUDE.md` and `.claude/**` only, and no rule covers `python -c` or an edit of `src/` or `tools/`. Recommendation: an adapter whose tool needs a gate calls `gate.check_before` at its own entry, so the runner, the server and a direct import all pass it; a B check with its rejected fixture tests that; deny gains Edit and Write rules for `src/**` and `tools/**`. A deny pattern on `python -c` is not the guard, since a command can be written around a pattern. For an instrument, the last guard stays the execution engine's own gate at the destination (S7).

25. **auto-ontology-mcp as the working index** (§5.2; the person's words of 2026-11-07, `docs/ideas/20261107.md`; done in `meta_agent/tasks/005`). Settled: coexistence with the wiki view, the store as a candidate layer only, the SQL half unused, lexical search only. Open, with recommendations: (a) the pin, under §14-23: `tools.lock.json` names the repository, the commit (`286ebc4` on 2026-11-07; the project has no release and `uvx` from `main` is unpinned), the license (Apache-2.0) and the runner (`uvx`); `bootstrap.py` installs it with `uv tool install` into the tools home and starts it for `.mcp.json`, `uv` itself staying the person's step as for harness2; the check on `tools.lock.json` (§14-23(c)) lands with this first new pin. (b) Where the store lives: recommended `meta_agent/knowledge/.index/`, gitignored, like `wiki/`. (c) What may be stored: passages only under the material's `may_quote`; otherwise concepts and one-line summaries; the 2026-11-05 note on licensed material stands. (d) How recall reads it: directly as SQLite with the standard library, through one module that knows the pinned schema and fails on a missing table, so recall is deterministic and makes no MCP call; the schema is the project's own (0.5.0 in its README) and may change under its four commits. (e) Whether a store's concept graph should ever be exported into the wiki view or the ontology: not now; it would put model-inferred relations into a view check 18 guards.

26. **M3: how a parameter value is recommended** (§5.3; a design pass on 2026-11-08 with SMA as reference, `docs/ideas/20261108.md`, `docs/reference/sma_read_20261108.md`). Settled 2026-11-08 ("Take all six"): (a) to (e) below as recommended, with the grade rule of §14-12; done in `meta_agent/tasks/007`, after `006`. **Revised 2026-11-09** (the person, `docs/ideas/20261109.md`, §14-30): the helper registry of (b) and the expression language of (c) give way to bound skills written as source code, and which constraints apply is chosen by the model, not by a rule; the recompute check, the grade rule, (d), (e) and the `neighbourhood` and `tradeoff` modes stand, working inside the interval the skills give. SMA searches for no value: its S4 intersects the intervals its axis cards state and takes the operating point from a hand-written table, and the principle "S4 makes no new numbers" is kept here. What this repository adds is a **recommendation mode** per row, chosen by a deterministic rule, never by the model: `lookup` (a source gives the value under matching conditions; the row keeps its derived grade), `scale` (the source's conditions differ and a registered helper or correlation bridges them; a computed row whose `basis` names the helper and the input rows), `interval` (one objective and several constraints from the reasoning stage, such as instrument limits, a stability condition or a dimensionless-number bound; the output is the feasible interval, each bound citing the row it came from, and one point by a stated rule such as the log-midpoint), `neighbourhood` (an anchor from literature or a prior run and a request for a value near it; a log-scale scan of ± a factor around the anchor, filtered by the constraints, giving candidates and a `gap` whose `requires` names the measurement or calibration that would pin the value), `tradeoff` (two or more objectives, read from `agent_goal.priorities` or from constraints that collide, pull one parameter two ways; the output is the Pareto set on a grid with its knee, and the weight is the person's, so the row is UNDECIDED and `chosen_by: human` until they choose), and `gap`. The person's two cases of 2026-11-08 are `tradeoff` and `neighbourhood`. A safety-relevant row gets a value from no mode (check 4); at most a ceiling interval derived from a vendor specification is attached as information. Open, with recommendations: (a) a `recommendation {mode, basis, candidates, frontier, chosen_by}` object on the row and an `objectives[]` list on the sheet, a schema change for the design seat; (b) the helpers as a registry, `contracts/registry/helpers.json`, each with an id, an expression in a small safe language, inputs with units, an output unit, a validity range and a source, the first set for testbeds B and C being Re, Wi, De, Pe, Ca, Bingham and Courant numbers, the rheometer geometry factors (stress from torque, rate from angular velocity), minimum torque → minimum stress → minimum measurable viscosity at a rate, the inertia limit and the gap-to-particle ratio; (c) a check that **recomputes** every `computed` row from its `basis` through the registry and fails on a mismatch, as SMA's check 17 does, which needs the validator to evaluate the expression language (recommended: yes, since it is the only way a computed value is read off a run rather than off a card); (d) uncertainty by first-order propagation through the helper and significant figures by the worst input (P15); (e) the first source adapter offline and pure Python (`chemicals`, MIT, recommended over CoolProp's C++ binding for MP8), water and glycerol-water viscosity against temperature and mass fraction, with NIST WebBook second, so that the comparison trial of §5.3 has two adapters. **Found 2026-11-09, read off PyPI while `tasks/007` was done, and put to the person**: `chemicals` 1.5.2 is MIT and pure Python itself, but it requires `fluids`, `scipy`, `numpy` and `pandas` and its wheel is 22 MB, so the reason it was recommended over CoolProp (MP8) holds only where those are already installed; and the documentation pages the meta seat read name no function for a glycerol-water mixture, so the adapter can give water alone. It is not pinned and the adapter runs `degraded`. Recommended instead, now that a correlation is a skill (§14-30(j)): the correlations the first testbed needs written as `value` skills with their cited source and a worked case from it, which adds no dependency; an external package only where a skill cannot reasonably hold the relation. **Settled 2026-11-09 ("Yes, use skills", `docs/ideas/20261109.md`)**: `chemicals` is not pinned; the correlations the first testbed needs are value skills, each with the source it is read from (never recalled) and a worked case the source states; a row such a skill gives is `value_kind: correlation` with source `correlation:<id>@v<n>` (check 19); the comparison trial of §5.3 is two skills for one quantity from two sources; where a source cannot be read the skill is not written and the paper is asked of the person through the materials inbox. Related: §14-12 on the grade of a computed value, where SMA's rule `max(E4, worst input)` is recommended over this repository's flat E4. **Touched later on 2026-11-09** (§14-32(j)): whether a `tradeoff` row waits for a person is now the adoption setting's question (§14-33(i)).

27. **M4: recall before writing** (§5.4; same pass). Settled 2026-11-08 ("Take all six"): (a) to (e) below as recommended, and §14-6 answered the same day; done in `meta_agent/tasks/006`, first of the three. SMA writes `failures.jsonl` in every agent and nothing reads it when a task starts; its lessons folder was designed and never built. So the first thing M4 builds is recall, and it is called, not offered: S3 calls it and the result enters `v2_agent_goal` as `case_refs` or `case_gaps`; A4 and A5 call it again. Recommendations: (a) recall is deterministic, an intersection of the input card's `signature` with each case's, weighted by field, in two levels, an exact signature match first and a match on `cause_class` and `executes` alone second, the brief saying which level matched, sorted grade → `count.supports` → id, a miss recorded as a `gap` naming the signature searched; (b) `condition_tags` may carry a range (`shear_rate:1e-2..1e3`) and match by interval overlap, so that an experience near a range of conditions is found; (c) cases are written from incidents (§14-28), from `validation_report` failures, from the person's interventions in `docs/ideas/`, and from SMA's `failures.jsonl` once §14-6 is answered, each seed with a verdict `transfer | downgrade | drop`, the source commit and a grade capped at E3 as SMA caps prior-repository numbers; the model drafts `what_happened`, `cue` and `lesson`, `cause_status` is `observed` by default and `confirmed` only with run or commit evidence (check 8); (d) promotion eligibility is computed and emits a draft `kb_candidate` or a draft `reshape` proposal, N staying the person's (§14-15); (e) a lesson enters a bundle only as a `replay/` or `validation/` task, never as prose, which is what "written so that it can be applied and checked" means in code. In connected mode a `kb_candidate` is handed to SMA in its `findings/` shape (`for_store: true`), since SMA has no `kb_candidate`. Checks 5 and 8 land here with their fixtures.

28. **M5: only what code can fill** (§5.5; same pass). Settled 2026-11-08 ("Take all six"): (a) the cut, with (b) to (d) as recommended and the order M4 → M3 → M5; §5.5 carries the scope line; done in `meta_agent/tasks/008`, last of the three. The person removed SMA's meta-harness on 2026-11-04. What died there was the hand work: proof fields typed and never verified (one proposal landed with every proof field null), a daily retro written by a harness seat, a regression suite never built. Recommendation (a): cut §5.5 to the steps code fills, and build the rest only when a run shows the need. `observe.py` extracts `harness_incident` drafts deterministically from `failures.jsonl`, the validator's verdict lines, refusals, `--no-verify` in the commit log, the read-only paths of `envelope/observed.json` (with the commit hash read, `degraded` when unreachable) and `onboarding_record`'s unnecessary questions; classification is the model's draft against `case_classes.json`, `path` `undecided` until evaluation; a proposal is a card and a diff under `harness/proposals/<id>/`, its `touches_core` computed from a `contracts/core.json` list, `loosen` refused without `persons_words` (check 9, with its fixture); **`prove.py` runs the proof and writes the fields**: the validator of the parent commit is taken with `git show <sha>:contracts/validate.py` into a temporary directory (no worktree) and run on the fixture before and after, and the affected bundles' `replay/` runs before and after for `new_fail`, so a proof field typed by hand is what the check refuses; the owning seat lands; the ledger entry carries configuration and cost, and the `confounded` precedence of §5.5 is computed (more than one component changed, or fewer than two rollouts, makes every verdict `confounded` and the experience `NO_ENTRY`, check 13); a revert is a new revision that re-adopts an earlier one, `reverted_by` on the ledger. No daily retro by hand: `retro/` is written by code from the period's incidents, proposals and ledger. (b) The four-condition evaluation (§11) runs on the echo task set in mock, C1 and C2 built with `degraded: [knowledge, cases]` and the template as is, baseline first, a failed evaluation ungraded; `k` stays 1 until the person sets a budget. (c) A threshold the person must choose (tolerance, §14-15) is shown as a curve read off replay, tolerance against refusal rate, in the same way §14-26's `tradeoff` mode shows a frontier; the harness never picks the point. (d) SMA's rule that a check deletion is declared (`Removes-check:` trailer, refused by the hook otherwise) is recommended for this repository's hook. Checks 9, 10, 13 and 14 land here with their fixtures. Order across the three milestones, recommended: M4 recall → M3 modes and registry → M5, since recall unblocks S3 and gives observe something to write into, and the helper registry can be built on fixtures before §14-20 and §14-21 name the engine and the rheometer.

29. **An agent-native environment** (the person's goal of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/009`, before `006`–`008`). Settled the same day as well: additional sessions may be opened for the building without asking each time, each its own seat with one task. Settled: the scope is the repository as the place seat sessions work in and the bundles as agents; the person only decides and sessions do the rest, unattended runs later; a session registers its own seat under the rule of §9, claims a task by a commit, and the gate runs in GitHub Actions; the three seats run at the same time on one computer. Open, with recommendations: (a) the seat mechanism: `python bootstrap.py seat <role>` derives the next free name from `contracts/seats.json` and the machine tag from the clone's own configuration and prints the entry; `seats.json` gains a `roles` table so that "the role's paths copied unchanged" is checkable, and check 6 lets a commit that adds only the committer's own entry pass and refuses a self-registered seat with a path, role or machine tag outside the rule (rejected fixtures); (b) a commit tool for a shared working copy, `contracts/tools/seat_commit.py --seat <name> -m <message> <paths…>`, as SMA has: it sets the committer for that commit, commits only the named paths, never amends, forces or skips the hook, and reads the commit back; `git add -A` and the repository-wide `committer.name` are what two seats in one folder cannot share; (c) the task queue as data: `meta_agent/tasks/index.json` (id, file, status, role, depends_on) kept by the design seat and checked against the task files, and a claim as one append-only file per task and seat under `meta_agent/tasks/claims/`, in every role's paths, so that two sessions never edit one file and a second claim of a task fails a check; (d) notes between seats, one append-only file per note in a folder every role may write, a reply being a new file that names the note it answers, unanswered notes reported as PENDING; this is not the bridge of M8, which carries cards between built agents; (e) CI: one workflow that runs `validate.py`, `--expect-fail` and the tests on every push with the full history, since check 6 reads commits (`.github/workflows/gate.yml`, written; its first run needs a push; the two actions are named by version tag, not yet pinned to a commit as `tools.lock.json` pins tools); (f) whether the edit hook, which judges the whole tree, lets one seat's unfinished card stop another seat: **read off runs on 2026-11-09 (`docs/ideas/20261109.md`), it does, and so does the pre-commit hook, which refuses another seat's commit while an unfinished card lies in the working copy**; **settled 2026-11-09 ("Yes, change it") for the commit gate**: the pre-commit hook exports the index of the commit and the validator that runs is the exported one, with that tree's own contracts, so nothing another seat has unfinished in the working copy stops or bends a commit; every check still runs and CI judges every pushed tree in full; open, the person's: the edit hook of `.claude/settings.json`, recommended to judge the files the seat changed; (g) whether a seat pushes on its own, the person's, and weightier since the repository became public the same day, a push being a publication; (h) for the product: what the template must gain so that a bundle is agent-native, where §14-5 (a portable skill layout) and §14-24 (one MCP server per bundle) hold the recommendations and SMA is the shape (§2.1), undecided.

30. **Parameter bounds from skills written as source code** (§5.3; the person's design change of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/007`). Settled: each skill computes a maximum or a minimum of one parameter; there are many, of various kinds; the model takes and uses the ones a request needs; this replaces §14-26's helper registry and its rule-chosen constraints. Open, with recommendations: (a) the layout, the bundle's own (§5.1 S5): `meta_agent/skills/bounds/<id>@v<N>/` with `SKILL.md` (what the model reads to choose: what it bounds, when it applies, what it needs), `skill.json` (the manifest code reads: `parameter`, `side: min | max`, `kind: instrument_limit | numerical_stability | physical_regime | resolution | budget`, `applies_to`, `inputs` with units, `output_unit`, `validity`, `source`), `scripts/bound.py` (one pure function) and `cases.json` (worked cases from the cited source); a version is a new folder, never an edit; (b) the model never types the bound: a runner executes the skill on the rows the model bound to its inputs and writes a `computed` row whose `basis` names the skill, its version and the input rows, graded `max(E4, worst input)` (§14-12); (c) the interval is the highest floor and the lowest ceiling, each citing its row, and an empty interval names the two skills that collide and is a `tradeoff` or a `gap`, never a silent choice; (d) the recompute check re-runs the skill named in `basis` and fails on a mismatch; to make running it safe a skill may import `math` only and do no input or output, which a check reads off its source; (e) a skill lands only with a worked case that passes, as a check lands with its fixture; a skill the model drafts during a request is a draft until a seat lands it; (f) a constant that is a judgement (a Courant limit, a multiple of a particle diameter, a fraction of a relaxation time) is an input row with its own source and grade, never a literal in the skill, so that thresholds stay the person's (§14-15); (g) omission is visible: every skill whose `applies_to` matches the request's parameter and tool is on the sheet as used or as not applied with a reason, and a silent omission fails; (h) a safety-relevant row gets a value from no skill (check 4), at most a ceiling as information; (i) **revised later the same day (§14-32)**: the person has the model reason over the skills' values and set the engine parameters, so the choice inside the interval is the model's too; the value is still code's, computed from the rule or candidate the model names (`interval`, `neighbourhood`, `tradeoff` of §14-26 are such rules); this item first read the morning's words as giving the model the choice of skills and not of the point; (j) a value at other conditions (§14-26's `scale`) is a skill of the same layout with `side: value`; (k) for the product, the bundle carries the skills its specification used and its tools may serve them (§14-24), so that the built agent recomputes its own bounds when conditions change; (l) where a Claude Code session finds the catalogue: a command that lists skills by parameter, with `.claude/skills/` left as it is. **Extended later on 2026-11-09** (§14-32): bounds are one of three kinds of skill a rough-range pass uses, and (i) is revised.

31. **A skill library with kinds, used by subagents** (§5.1 S5; the person's words of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/010`, on which `007` builds). Settled: skills as source code come in kinds, six named and the list open: hardware connection, hardware boot sequence, hardware control, hardware situation awareness, hardware calibration (the last two added the same day), data analysis, beside the bounds of §14-30; whether a device can calibrate itself is checked, and a calibration that needs outside help is designed with the person; the Meta-Agent makes them as it builds; subagents use them. Open, with recommendations: (a) one layout for every kind, `meta_agent/skills/<kind>/<id>@v<N>/{SKILL.md, skill.json, scripts/, cases.json}`, which is the bundle's `skills/<name>/` (§5.1), a version being a new folder; §14-30(a)'s path is this one with kind `bound`; (b) the manifest states `kind`, `side_effect: none | read_device | write_device`, `applies_to` (methods, instruments, engines of `contracts/registry/`), inputs and outputs with units, `source`, and for device skills the tools of the bundle it calls; (c) a device is reached only through the bundle's gated tool path (`src/run_tool.py`), never from a skill's own code, so a skill holds no limit value and the gate's order is the only order; a check reads this off the source (no socket, serial, subprocess or vendor import outside `tools/<name>/adapter`); (d) a `write_device` skill is `held` until a person releases it, once per skill (the manifest's `release`, with the person's words), which presupposes the analysis permission (§14-14); a released skill still runs only behind the gate and the person's safety values, and whether each run then waits for a person is the built agent's adoption policy (§14-33(i), §14-34(d); revised 2026-11-09 by the person's later word); in this repository it runs against a mock only (MP1), bench tasks `not_run: requires bench`; (e) what a skill returns: connection, `observed` identity claims; situation awareness, `measured` readings with the run id and the time; analysis and bounds, `computed` numbers with `basis`, recomputed by the check of §14-30(d); (f) every skill lands with worked cases, on a mock transcript for device skills and on fixture data for analysis; (g) subagents are the bundle's `.claude/agents/<name>.md` (already a part of the harness surface, §5.1), not seats: they write no record and the agent's seat commits; a definition names the skills and the side effects it may use, and a bundle check (B11) fails a subagent that names a skill the bundle lacks or a `write_device` skill without the gate; (h) how subagents are drawn: by side effect (a reader, the one that may write, one that touches no device) rather than one per kind, the Designer proposing and the person seeing it in the specification; (i) the library is read at S3 beside cases and knowledge, so that a second agent for the same instrument starts from the skills of the first, and at S5 the skills a specification names are copied into the bundle unchanged; (j) which instrument comes first is §14-21, so the first hardware skills are written against the fixture rheometer profile; (k) a boot sequence is an ordered list of steps, each `{actor: device | person, precondition, action, verify}`: a precondition and a verification are readings taken through a situation-awareness skill, a `person` step (air supply, a transport lock, a mounted geometry) waits for the person's word and is recorded as `operator_read`, never assumed; a failed verification stops the sequence where it is and returns the state, with no retry and no skipping; the kind is `write_device`, so (d) applies, and the boot has succeeded only when situation awareness returns `ready`; (l) calibration: the `tool_profile` carries, per quantity, a claim `self_calibration: observed | derived | inferred | unknown` with its evidence (S2), and the skill's first step reads it: `self` runs the device's own routine as gated tool calls (`write_device`, so (d) applies) and returns a `calibration:<id>` number with its mandatory expiry (§6.3, E2); `assisted` makes no tool call and opens a design with the person, whose result is a `calibration_design` card (quantity, reference and its traceability, who does which step, what is read and recorded as `operator_read`, the interval, the acceptance limit as the person's threshold), `draft` until the person confirms; `unknown` is a gap naming what would settle it; a reading on a quantity whose calibration is absent or expired says so on its row. **Extended later on 2026-11-09** (§14-32 to §14-34): the vocabulary of kinds in (a) gains `scale` and `capability`; beside (h)'s drawing by side effect there is a second drawing of subagents, by what each argues for (advocates, a guard, a mediator); `reader` is recommended folded into `operator`.

32. **Rough ranges of the key physical quantities, and the model reasoning to the engine parameters** (§5.3; the person's words of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/011`, on `007`). Settled: resolution has kinds (for a microscope, temporal and spatial), each opening onto several quantities (the imaging rate wanted, the rate the camera can give, the system's characteristic timescale, its fastest feature's timescale, the length of the recording); it is resource management, a maximum and a minimum fixed and a compromise found inside; each such quantity is obtained by a skill; the limits are considered together; what is wanted is the rough ranges of the key physical quantities; the model reasons over the values the skills give and sets the engine parameters, which revises §14-30(i); the rough-range pass is a card of its own (answered later the same day). Open, with recommendations: (a) the model still types no number (E6): it chooses which skills apply, which quantity is fixed first and which rule or candidate is taken inside an interval, and writes its reason; code computes the value from that choice, so a row carries the computed value, its `basis` and `choice {by: model, rule | candidate, reason}`, and the recompute check of §14-30(d) covers it; (b) a pass of four steps in front of the precise sheet: **scales** of the system (its extent, its smallest feature, its fastest and slowest timescales, its signal), each a range from an estimating skill; **requirements**, which follow from the scales and the request; **configurations**, the discrete choices the tool really has, listed in full by code, what each delivers computed by a skill; **intersection**, the configurations that meet the requirements and the range each key quantity takes across them; (c) the vocabulary of skill kinds (§14-31(a)) gains `scale` (an estimate, `side: value`, which §14-30(j) had in one line) and `capability` (what one configuration delivers) beside `bound`; (d) the configuration axes are `tool_profile` claims that list their discrete options with evidence (S2), so an axis that is only `inferred` is listed as such and an unknown one is a gap; (e) limits are tied: a skill may take another quantity's row as an input, the sheet is then a dependency graph, the runner recomputes what lies downstream when a row is set, and the order in which rows are set is the model's choice and is recorded; (f) code lists and filters and does not optimise: no solver enters (`007`'s rule stands), the grid being the configurations themselves; (g) a rough range is two rows, a minimum and a maximum, whose grade follows the worst input, so the grade rule already says how rough it is and no new `value_kind` is needed; (h) the card of its own is named `range_sheet` (the name is the seat's): a built agent remakes it whenever conditions change, while `parameter_sheet` stays the specification's; one schema, in `contracts/schemas/` and copied into the template, so that the Meta-Agent's and a bundle's are the same card; (i) the four steps are the same for every tool: any system has an extent over a resolution in space and in time, a budget their product must fit (a camera's pixels per second and its photons; a simulation's cells times steps; a rheometer's torque range, with the geometry as the configuration) and discrete choices, so the skills differ per tool and the pass and the card do not; the first worked fixture is the person's own case, a microscope written by hand from the words of 2026-11-09 (a camera, objectives, binning, a region of interest), the fixture rheometer after it; (j) §14-26 kept a `tradeoff` row `UNDECIDED` and `chosen_by: human`: with these words and §14-33 the proposal is the mediator's and whether it waits for a person is the adoption setting's (§14-33(i)); a safety-relevant row is outside all of it (check 4).

33. **Subagents that each hold a position, a safety subagent among them, and one that finds a range all accept** (§5.1 S5; the person's words of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/012`, on `010` and `011`). Settled: the ranges are settled among subagents that each hold to their own position (resource management, experiment, simulation, the list open); a compromise subagent finds a range that suits all, proposes it and obtains the agreement of all; a safety subagent sits among them; a science subagent that does not forget the purpose is needed; the names are left to the seat; the negotiation works inside the built agent; simple negotiations are skipped; whether an agreed range is adopted as it stands is decided by the user of the built agent, who may change it later; answered later the same day: at most five rounds, and beyond that the matter is reported to the person; giving up a requirement of the science subagent is the person's decision under any setting; experiment and simulation are in different bundles; under adoption as agreed a run on hardware starts without asking (the answer to the question of (i), put again); whether such a run is blocked where the bundle's gate lacks its limit check is for the user to specify. Open, with recommendations: (a) names and kinds: the advocates `budget` (instrument time, storage, computing time, what the sample can spend), `measurement` (what the instrument can really deliver and the quality of the measurement), `numerics` (numerical stability, convergence, comparability with the experiment) and `objective` (what must be resolved for the question to be answered); a guard, `safety`; and `mediator`; three kinds so that a kind tells its powers: an advocate has hard limits and soft preferences, a guard hard limits only, the mediator none; (b) a position is `{hard[], soft[], concession_order[]}`: each hard limit a `computed` row from the subagent's own skills (§14-32), conceded by nobody but the person; each soft preference a direction over a quantity, with a reason; an opinion with no row behind it is a model's number; (c) the intersection is code's (§14-32(b)); the mediator works after it, proposing one configuration where it is wide and, where it is empty, naming the two limits that collide and the soft preference that would give way; (d) agreement on a hard limit is a check, the subagent's skills run again on the proposal; agreement on a soft preference is the subagent's judgement with its reason; nothing a check can decide rests on a model agreeing with itself; (e) the bound on the rounds is the person's number, five; with no agreement inside them nothing is forced: the report to the person names the limits that collide and what each subagent last answered; (f) `safety`, so that MP4 holds: it reads `envelope/safety.json` and nothing else; it makes no value and fills no `null`; a missing value is answered with the scanned operable range standing in where `operating_range` has an `observed` item for it (§14-36(f)), the answer saying so, and otherwise "not set", which makes the configurations that need it `held` and not negotiated; its agreement is the function `src/gate.py` already is, so safety is judged by one piece of code, only earlier; the mediator may not ask it to concede, and its refusal removes a configuration rather than counting as a disagreement; it may propose a safety row's place (name, unit, reason) with the value `null`, as A5 does; (g) a quantity that is both a resource and a hazard is marked per row by the person: the loss of data from a damaged sample may be negotiated, harm to a person or to the instrument may not; (h) the skip: each advocate's soft preferences are declared in its definition as directions; code compares the surviving configurations along them, and where one is ahead of every other on every direction it is taken and no subagent is called; otherwise the negotiation opens; `safety`'s check is code and runs either way; the skip and its reason are written; (i) adoption: a policy field of the bundle with two values, `confirm` (a recommendation until the user confirms) and `adopt` (adopted as agreed); never inferred (MP11) and asked at set-up; shipped unset and written by the user at the destination, as a safety value is; unset behaves as `confirm`; a change is a new revision by the user; every `run_plan` states the value it was made under; it was first read as covering parameters only; put again in plainer words, the question whether `adopt` also covers the start of a run on hardware was answered by the person: it does, and the run starts without asking (`docs/ideas/20261109.md`); what `adopt` does not cover, each of which still stops and reaches a person: safety values, which stay the person's and `null` in a bundle (MP4); the release of a `write_device` skill from `held`, once per skill and a person's (§14-31(d)); the gate, which runs before every call and refuses as before; a requirement of `objective` given up; the sixth round; a departure from the plan's intervals; whether a bundle whose gate lacks the limit check and the interval check of §14-34(c), as today's template gate does, may start a writing run under `adopt` is for the user to specify (answered the same day, where the seat had recommended a fixed block): a second field of the policy, `adopt_without_gate_checks: block | allow`, written by the user at the destination and changeable as the first is; recommended and not answered: it is never inferred, a bundle ships it unset, and unset behaves as `block`, that is as `confirm` for that step (MP10); under `allow` the `run_record` states that the run started with no limit check; the operable range the agent scans (§14-36) is what gives that check something to compare against where no safety value has been set, standing in for it (§14-36(f)); (j) `objective` holds what must be resolved, from the request and `agent_goal.science_task`, when the plan is made, and when an `analysis` exists it judges whether the question was answered and proposes the next condition; giving up one of its requirements is the person's under either adoption value (settled, above), so the agent stops and asks; (k) subagents still write no record (§14-31(g)): the positions, the proposal and the answers are parts of the `run_plan` the agent's seat writes (§14-34); (l) a bundle check, B12, reads the kinds: an advocate, a guard and the mediator name no `read_device` or `write_device` skill, a guard declares no preference, the mediator no limit; (m) the Meta-Agent builds the definitions and the skills and judges one negotiation on a mock in S6; M3 then builds what sets values rather than recommending them, the specification's sheet listing rows, skills and judgement constants; (n) experiment and simulation being different bundles (settled, above), each bundle has its own table: an instrument's has `objective`, `budget` and `measurement`, an engine's `objective`, `budget` and `numerics`, each with `safety` and `mediator`; `measurement` and `numerics` therefore never sit at one table, and what one bundle needs of the other (the same fluid, model and units; conditions both can reach) arrives as a card over the bridge (M8) and is held by `objective` as a requirement; a negotiation between the two bundles themselves is the bridge's and is not designed here; (o) the first trial runs one fixture request with the negotiation and with the plain intersection and reads the difference off the two runs; no difference means the structure only costs.

34. **From the plan card to the report: what a built agent does with an agreed range** (§5.1 S5, §6.1; the person's words of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/013`, on `012`). Settled: what the negotiation produces is a card for carrying the experiment out; it goes to an operating subagent, which uses the skills and runs the experiment within the range; then, with the data, to an analysing subagent, which analyses with the data-analysis skills; then a report is written and reported to the user. Open, with recommendations: (a) four cards, whose names and fields the person left to the seat (the same day), the bundle's own contracts, written into the template as `tool_contract` is: `run_plan` (the configuration chosen, each parameter's interval and its basis, the positions and the answers, the order of skills, the stop conditions, the adoption value it was made under), `run_record` (the tool calls made and their verdicts, the device's readings, every departure from the plan, the hashes of the data), `analysis` (the numbers the analysis skills computed, with their basis, and the quality planned beside the quality obtained), `report` (the answer to the question, what is unknown, the next condition proposed); (b) the plan carries intervals and not points, and marks which parameters `operator` may adjust; `operator` adjusts inside them on what the `hardware_state` skills read; where it would have to leave an interval it stops and the matter returns to `mediator`; (c) the bundle's gate gains what it compares against, in SMA's order (`docs/reference/sma_read_20261108.md` 7): safety values present or, where one is unset, the scanned operable range standing in (§14-36(f)), the plan authorised (under `confirm` a signature on its hash, under `adopt` the standing policy a person set), the run lock, each call inside the plan's intervals and inside the operable range the agent scanned (§14-36); the template carries the plan check and the interval check, and the limits stay the destination's (S7); (d) the start of a run follows the adoption setting (§14-33(i), answered the same day): under `confirm` a plan with a `write_device` step needs the user's signature on its hash, SMA's form; under `adopt` no signature is asked, the gate takes the policy `{adoption: adopt, set_by: human}` as the authorisation, and the `run_record` states that the run started under it and under which revision of the policy; a run with no device follows the same setting; (e) the subagents are `operator`, which uses every hardware kind (§14-31(h)'s `reader` folded into it), and `analyst`; (f) an `analysis` number is `computed` with a `basis` naming the skill, its version and the data's hash; the quality obtained is stated per dimension (§14-35); (g) the `report` is an MD beside its JSON, every number in a card (check 3's rule, inside the bundle); (h) what returns to the Meta-Agent is an `observation` (§6.1) carrying the plan's reasons and the analysis: a reason the analysis contradicts is a case whose falsification is met (F4), which is how the reasons a parameter was set for become experience; (i) the Meta-Agent builds this and runs it on a mock only (MP1); the Scientific Research Loop stays the built agent's (§1.2).

35. **What a validation speaks of; S6 under review** (§5.1 S6, §8 check 12; the person's words of 2026-11-09, `docs/ideas/20261109.md`; no task is opened until the person has answered). Settled: the aim is general scientific problems; a validation speaks of resolution, accuracy and precision and, taken later the same day as the seat had recommended them, of the range of validity, convergence and stability, physical consistency and selectivity; the person is thinking the structure of S6 over. Open, with recommendations: (a) the seven as a vocabulary file: `resolution`; `accuracy`; `precision`; `range` (the conditions over which the others hold, the detection limit at the bottom and saturation at the top); `convergence` (does the answer stay when the resolution or the time changes; for an instrument, drift); `consistency` (units, conservation, known limits: judged with no reference data); `selectivity` (the intended quantity, or an artefact); still recommendations and not answered: accuracy fixed to mean the bias against a reference, precision told apart as `repeatability` and `reproducibility`, and the two together carried as an uncertainty on the number (§14-26(d)) rather than as one more item; (b) every scientific task names the dimension it judges, and a dimension a bundle does not judge is written as not assessed with a reason, as §14-30(g) does for skills; (c) `resolution` and `range` need no reference: the bound skills are run again on the parameters that were set (§14-32); (d) what S6 judges today, read off the tree at `214fb70` (`docs/ideas/20261109.md`): one tool call per task; no skill and no model in any task, while §1.5-1 asks for a mock question handled end to end; a tool behind the safety gate can only show its refusal; the reference is a function inside the bundle's runner; the echo report is `undecided` and `draft` for want of a tolerance; one `environment` per report; (e) a shape: S6 runs the flow of §14-34 on a mock from its first card to its last and judges at each hand-over, a task naming its target (`tool | skill | agent`), its question (interface, scientific, or behaviour: a refusal stays a refusal, a failed verification stops, a person's step is waited for) and its environment (no device, mock, bench); whether behaviour is a third gate beside the two is the person's; (f) `undecided` as a per-task verdict, which the report writes today as `not_run` with a reason; (g) a mock-only set of safety values, so that a writing skill's normal path can be shown, touches MP4 and is the person's; (h) whether a task that must match exactly needs a tolerance from the person; (i) references taken from knowledge entries and literature, not only from functions in the runner.

36. **The operable range of an instrument, found by the agent as it scans** (§5.1 S2 and S5; the person's words of 2026-11-09, `docs/ideas/20261109.md`; done in `meta_agent/tasks/014`, on `010`). Settled: while scanning the instrument the agent finds its maximum operable range by itself; the range so found stands in for a safety value the person has not set (answered the same day, where the seat had read no); the person may mark a safety row as one no range may stand in for. Open, with recommendations: (a) who scans: the built agent at its destination, where the instrument is; the Meta-Agent reaches no instrument (MP1) and at build time has the documents' values only (`spec:`, S2); (b) what a scan is: read-only queries (`read_device`), through the gated tool path, of what the device and its control software report about themselves (identity, firmware, travel, speed, torque and temperature ranges, sensor size, frame rates, the modes of each axis); it is not finding a limit by driving the instrument until it stops, which would be `write_device` and is not designed; (c) what it writes: a card of the bundle, `operating_range`, each item `{quantity, min, max, unit, claim: observed, evidence {tool, query, response, read_at}}`; a quantity the device does not report is `unknown` with `requires` (the vendor's specification, or the person) and is never filled in; a bundle ships none; (d) a skill kind `hardware_range` (`read_device`) beside `hardware_connection`, on `010`'s layout, with a worked case on a mock transcript; (e) what uses it: the configuration axes and `capability` skills of §14-32 take their options and ceilings from it, so a `range_sheet` rests on what this instrument reports and not only on a specification; `measurement` holds them as hard limits (§14-33); the gate's limit check refuses a call outside it (§14-34(c)); a difference between the scan and the specification the bundle was built from returns as an `observation`; (f) standing in (settled, above), read narrowly, since it narrows MP4: nothing writes `envelope/safety.json` but a person, and a bundle still ships it `null` (check 4, B3); at the gate, for a quantity whose safety value is unset, an `observed` item of `operating_range` is the limit in its place, and the `run_record` names every limit that was a stand-in; an item that is `unknown` stands in for nothing, so the gate refuses as before until the person sets the value; where the person has set a value the tighter of the two holds; what stands in is the device's own report read by code, never a model's figure (E6) and never a specification read from a document; a quantity the device cannot know (a clearance that depends on what is mounted, what a sample or a person can bear) can be marked by the person on its safety row as one no range may stand in for (settled, above): the row is then `{value: null, stand_in: never, set_by: human, date}` until the person gives it a value, and for it the gate refuses as it did before the narrowing; recommended and not answered: a row with no mark allows the stand-in; a bundle ships no mark, since a mark is a person's; `safety` may propose a mark with its reason, as it proposes a row's place (§14-33(f)), and the person makes it or does not; (g) the source of such a number: recommended `spec:<device_id>` with the query as evidence, the device's own statement about itself, and no new source kind (MP8; §14-12); (h) a new scan when the firmware, a geometry or an objective changes, as a new revision, the old one kept.

---

## 15. First work after approval (M0 checklist)

| # | Item | Status |
|---|---|---|
| 1 | repository location, `git init`, `.gitattributes` (LF), `.gitignore`, `LICENSE` | done 2026-10-29 |
| 2 | `plan.md` (English record); the Korean plan to `docs/origin/` | this file |
| 3 | `contracts/seats.json` with `design-…` and `meta-…`; the person assigns the two sessions | M0 |
| 4 | all of `contracts/schemas/` (§7), `units.json`, `case_classes.json`, `claim_kinds.json`, `tool_contract` and `error_contract` schemas, `registry/{methods,engines,instruments}.json` seeded without `verified` ("to verify") | M0 |
| 5 | `contracts/validate.py`: checks 1·2·3·6·7·11·15·16·17 + `--expect-fail` + verdict line | M0 |
| 6 | `contracts/examples/` (including `material`, `lab_profile`, `onboarding_record`, `tool_profile`, `validation_report`) and `rejected/` fixtures (at least one per check; 15 and 16: "a profile whose policy field is inferred" and "a record asking an already confirmed field"; 17: "a material with both url and path" and "a material with an archived copy and no may_quote"); the commit message says the fixtures were watched failing | M0 |
| 7 | `contracts/hooks/pre-commit`, `.claude/settings.json` (root and `meta_agent/`, two-shell twins, PostToolUse validation hook) | M0 |
| 8 | root `CLAUDE.md` (short), `README.md`, `meta_agent/CLAUDE.md`, `meta_agent/README.md`, `meta_agent/inbox/materials/{README.md, LINKS.md, drop/.gitkeep}`, `meta_agent/tasks/001-onboard-this-lab-on-fixtures.md`, `tasks/002-echo-agent-on-mock.md` | M0 |
| 9 | `docs/ideas/20261029.md` with the person's words verbatim; `docs/reference/hoomd_gui.md` with §2.6's fact check | M0 |
| 10 | first run: `python contracts/validate.py` → `0 failed`; `--expect-fail` rejects both totals; the numbers are read off the run and reported | M0 |

---

## Appendix A. Glossary (Korean → identifier)

| Korean | Identifier | Where |
|---|---|---|
| 메타 에이전트 / 에이전트 디자이너 / 과학 에이전트 | Meta-Agent / Agent Designer / Scientific Agent | §1.1 |
| 온보딩, 설치 마법사 | onboarding, Agent Setup Wizard | §5.0 |
| 발견 보고 / 온보딩 기록 / 연구실 프로필 | `discovery_report` / `onboarding_record` / `lab_profile` | §5.0, §5.6 |
| 설정 상태 | `confirmed` / `inferred` / `unknown` | MP11 |
| 자료 (투입구) | `material`, `inbox/materials/` | §5.0 |
| 방법 레지스트리 | `contracts/registry/{methods,engines,instruments}.json` | §5.6 |
| 연구 루프 / 개선 루프 | Scientific Research Loop / System Improvement Loop | §1.2 |
| 지식 기반 개선 / 구조 개선 | knowledge-based / structural improvement | §1.3 |
| 도구 프로필 | `tool_profile` | claims + evidence + limitations + permission |
| 주장의 종류 | observed / derived / inferred / unknown | MP9 |
| 원인 상태 | observed / suspected / confirmed | §5.4 |
| 값의 종류 | `value_kind`: measured / correlation / computed / predicted / literature / estimated / model_generated | MP7 |
| 인터페이스 검증 / 과학 검증 | interface validity / scientific validity | §5.1 S6 |
| 하네스 표면 | harness surface (8 components) | §5.1 S5 |
| GUI 명세 | `gui_spec` | §5.7, MP13 |
| 보류 | `held` | MP10 |
| 에러 계약 | error contract | §6.4 |
| 편집 행 | `edit_rows`: helped / hurt / no_observed_effect / confounded | §5.5 |
| 교훈 | `cue / lesson / evidence / confidence` | §5.4 |
| 라이브러리 | `harness/library/<domain>/` | harness-level recursion |
| 네 조건 | C0 / C1 / C2 / C3 | §11 |
| 자원관리 / 실험쟁이 / 시뮬쟁이 / 과학쟁이 서브에이전트 | advocates `budget` / `measurement` / `numerics` / `objective` | §14-33 |
| 안전쟁이 / 타협 서브에이전트 | guard `safety` / `mediator` | §14-33 |
| 운영쟁이 / 분석쟁이 | `operator` / `analyst` | §14-34 |
| 대략적 범위 | `range_sheet` | §14-32 |
| 실험 진행 카드 / 보고서 | `run_plan` / `report` | §14-34 |
| 카드, 요청, 명세, 번들, 증류, 항목, 공백, 사례, 사건, 제안, 장부, 회고, 래칫, 좌석, 봉투, 거부, 축소 모드, 등급 | card, request (`rid`), spec, bundle, distillation, entry, gap, case, incident, proposal, ledger, retro, ratchet, seat, envelope, refusal, degraded, grade | as in SMA |

## Appendix B. Card sketches

The origin's sketches (a `lab_profile` with three states, a `material` after intake, three `tool_profile` claims, a `case`'s experience fields, a `harness_proposal`'s edit rows) are superseded by the schemas and by `contracts/examples/`, which the validator judges. Read those.

## Appendix C. Key sentences of the references (summaries, not quotations)

- **Proposal**: the Meta-Agent is responsible for configuring, operating and improving other agents; the Agent Designer Agent designs, generates and validates agents for new tools. Outputs: capability specifications, callable tools, steering instructions, validation tasks, deployment configurations. Interface behaviour and scientific validity are checked separately. Self-improvement is evaluated under four conditions; the research loop and the system improvement loop are distinct. Testbeds: a TA Instruments rheometer and RheoTool.
- **REA**: observed, derived, inferred and unknown are distinguished and evidence provenance is kept. Results include evidence and limitations. It does not write into repositories that have source. Integration is fail-closed. The error contract is category, retryable, remediation.
- **harness2**: a harness is the system around the model and harnessing is its optimisation. Eight components, Propose–Probe–Compose, two levels of recursion, omission is inheritance, invalid proposals are discarded, always-on prose is the most expensive, lessons are cue / lesson / evidence / confidence, adoption alone never means "helped", the baseline is judged first, the runner's network must be restricted.
- **Conversation 1**: the partition Agent Designer / Knowledge Engine / Parameter Intelligence / Experience Memory / Meta-Harness, four metric groups, roadmap phases 0–5, parameter and protein database candidates, tiered search, measured vs computed vs literature vs estimated.
- **Conversation 2**: the setup wizard analyses first and asks later. Settings are confirmed / inferred / unknown; inference is a recommendation; policy and permission are never inferred. Simulation separates scale, method and engine, many-to-many. Respect the lab's tools (Lab Profile). The GUI splits into common frame + domain editors + per-tool scientific core, derived from the capability spec; GUI validation does not replace engine validation. Proteins are found via natural / designed / structure / experimental-property paths and cross-validated. Multiscale coupling is the bridge's or a coupling tool's.
- **HOOMD_GUI**: visual modelling, transparent code generation, separated scientific core, reproducibility first, validation before execution, versioned JSON project documents, a loopback-only Local Runner. As of 2026-10-29 a concept document plus a 2D editor skeleton; code generation and execution not implemented; license undecided.
