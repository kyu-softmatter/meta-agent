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

### 2.2 Proposal

**Taken**: the three roles, two loops, two paths, the Designer's five outputs, the separation of the two validities, testbeds A / B / C and cross-validation, the four evaluation conditions and metrics, "time to the first scientifically valid closed-loop run", reproducible validation tasks and shareable success / failure examples in a public repository.

**Not taken**: AWS deployment / operation / budget (§2.5, §4), web service and dissemination targets, permanent central coordination of many agents (the bridge's job).

### 2.3 REA

**Taken as discipline**: claims are **observed / derived / inferred / unknown** with evidence provenance; unknowns are registered with **what would resolve them** (permission, environment); "absent" is never concluded from partial evidence; read-only by default with explicit write permission; configuration changes are additive and idempotent and shown as a plan first; the error contract (category, retryable, remediation); **fail-closed** integration when scope, permission, side effects or validation are unresolved; REA's own boundary: "repositories with source are for ordinary tools; binaries, packages and runtime behaviour are for REA".

**Taken as a tool**: investigation of interfaces, parameters and call paths of instrument control software and engine binaries **whose use and analysis permission a person confirmed**. Connected over MCP, runs locally.

**Not taken**: REA's analysis engines in this repository; runtime capture on the instrument computer.

### 2.4 harness2

**Taken as design**: harness = everything around the model. Eight editable components and their cost (always-on prose is the most expensive). The edit contract "omission is inheritance"; invalid proposals are discarded whole. Contrastive evidence from Propose–Probe–Compose. Two levels of recursion with a per-domain library. The experience format `cue / lesson / evidence / confidence` and the precedence of `confounded`. The budget ledger. Baseline first. Judge and report under one configuration. Restrict the runner's network so it cannot reach the evaluation material.

**Changed**: adoption is not left to a model judge. Our probe is mock replay + deterministic validation; compose is a model-written **draft**; adoption is gate + owning seat + (for loosening) a person (SMA §8.3 rule 4, MP5).

**Not taken (now)**: installing harness2 as an engine. If ever, only under SMA §8.3's trial design of 2026-10-19 (clone outside the working folder, mock only, a computer without instruments; §14-8).

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
| **MP4** | **Safety values are never generated.** The `envelope/safety.json` template is `null`; the gate rejects a safety value whose author is not human. | P0, SMA §8.3 rule 2 | a model-written limit reaches an instrument |
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

`build` card: `spec_ref`, `lab_profile_ref`, `template_version`, `diff_from_template`, `bundle_sha256`, `held[]`, `gate_verdict`, `lineage`, `landed_at` (a person).

**S6 Validate → `validation_report`.** Two gates; both must pass.

| Gate | What | Where | Verdict |
|---|---|---|---|
| **Interface validity** | correctness of tool calls and responses, I/O consistency, error handling and recovery (error contract), transfer of settings and commands, and with a GUI the transfer GUI field → tool parameter | mock backend or sandbox (software tools in an isolated environment outside the working folder; hardware mock only) | per task `pass | fail | not_run`, deterministic |
| **Scientific validity** | quantity and unit consistency, validity of parameters and conditions, model assumptions, **agreement with reference results** (analytic solutions, literature values, reference data), reproducibility of interpretation | the `validation/scientific/` tasks in the same environment | a reference result is a number with an entry or a source; the agreement criterion (tolerance) is **a person's threshold**, otherwise UNDECIDED |

`not_run` is not a pass. A task that needs hardware stays `not_run: requires bench` and the bundle is handed over as "valid in mock" only. Browser-side GUI checks replace neither gate (MP13).

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

### 5.3 F2 Parameter Intelligence (`parameter_sheet`)

**Three stages** (Conversation 1 §5): **Discovery** (identify parameters together with the model, instrument, environment, assumptions, units and valid range they were used in, from papers, manuals, run records and databases) → **Reasoning** (correlations and constraints between parameters, scaling, dimensionless numbers, numerical stability conditions, instrument specifications; deterministic helpers) → **Recommendation** (value or range + grounds + uncertainty; without grounds, **propose the additional measurement or calibration** instead of a value).

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

SMA §8.3's loop (observe → classify → propose → prove → gate → land → measure → retire) and rules 1–7 are adopted. Added:

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

Numbers are fixed and never reused after retirement. M0 implements 1, 2, 3, 6, 7, 11, 15, 16, 17; M1 added B1–B9 (`--bundle PATH`, and every bundle a `build` card outside `contracts/examples/` points at; a template is not a bundle and is not judged by them). Task 003 added 18 (2026-11-04).

| # | Check | Kind |
|---|---|---|
| 1 | every JSON with a `card` field passes its own schema (`contracts/schemas/<card>.schema.json`; the file name is not trusted; an unknown card fails) | schema |
| 2 | numbers are the 4-tuple + `value_kind`; the unit is registered; the grade equals the derived grade (`grades.json`); no E6 and no `model_generated` | numbers |
| 3 | every number in an MD file exists in a card of the same folder | numbers |
| 4 | safety values are `null` or `author: human` | safety |
| 5 | `kb_refs` / `case_refs` resolve in the pinned index; `*_gaps.searched` is non-empty | references |
| 6 | commit paths lie inside the committer seat's boundary (`seats.json`; unknown committer → reported, not failed; commits at or before `enforced_from` are reported only) | boundary |
| 7 | append-only under the roots of `records.json`; a revision is a new file `v<N>_<name>` whose `revision` is N and whose predecessor exists; a JSONL file only grows | history |
| 8 | `case` has `falsification`, `count`, `cue`, `cause_status`; `confirmed` has run / commit evidence; `cause_class` is registered | cases |
| 9 | `harness_proposal.kind` is one of four; loosen / retire / core need the person's words + a `docs/ideas/` commit; tighten needs a fixture | harness |
| 10 | a `ledger` line points at an existing proposal and commit; cost fields exist | harness |
| 11 | `tool_profile.claims[].kind` is one of four; evidence refs exist (`source_ref` or `rea_evidence_id`, with `locus`); `observed` / `derived` / `inferred` have evidence; `unknown` has `requires`; a claim with `basis` binary or runtime, or REA evidence, FAILS without `analysis_permission {granted_by: human, scope, basis, date}` | tool understanding |
| 12 | `validation_report` has both sections, per-task `pass|fail|not_run`; scientific reference results have an entry or a source; without a tolerance UNDECIDED; `not_run` is not a pass | validation |
| 13 | `edit_rows[].verdict` is one of four; an `experience` resting only on `confounded` is refused from the library (`NO_ENTRY`) | harness |
| 14 | `held[]` items are not in the bundle; releasing `held` needs the person's words + a commit | fail-closed |
| 15 | every Lab Profile field has `state`; `inferred` has non-empty `evidence[]`; `confirmed` has `confirmed_by: human`; policy fields (`policy.*`, `collaboration.mode`, `operational_constraints.execution_permission`) FAIL when a `build` or `agent_goal` references the profile and they are not `confirmed`; an `inferred → confirmed` transition between revisions whose confirmer is not human FAILS | onboarding |
| 16 | each `onboarding_record.questions[]` item targets a field that is `unknown` in the referenced `discovery_report` or a policy field; a question on a `confirmed` field FAILS; a question on an `inferred` field is reported as unnecessary; each `skipped[]` item has a reason | onboarding |
| 17 | `material`: `location` has exactly one of `url` / `path`; `about.*` and `license_note` follow the three states and `inferred` has evidence; `added_by: human` and the metadata author is a seat; a `url` material that is `distilled` FAILS without `source_snapshot.retrieved_at` and `content_hash`; `archived` set while `may_quote` is not `true` FAILS; `held` and `declined` need `state_reason` | material intake |
| 18 | in every folder named `wiki/`: each page but `index.md` names one record (`- record: <path>`, a card or an artifact directory) and is titled and named `<id>@r<revision>`; every `[[link]]` names a page of that wiki and, between two records, a relation one of them holds (an id, a path or a file name, or two revisions of one id); every number left outside code spans and links is a number of the rendered card; a `graph.html` there loads nothing from another host, and its `wiki-graph` data names only pages of that wiki, with their records' `card` and `status`, and only edges one of the two pages links | view |
| B1 | required bundle files (§5.1 S5) | build |
| B2 | every `Bash(...)` deny / ask has a `PowerShell(...)` twin and vice versa | build |
| B3 | all values of `envelope/safety.json` are `null` | build |
| B4 | `snapshot.json` entry hashes match `knowledge/`; `kb_version` pinned | build |
| B5 | `replay/` and `validation/{interface,scientific}/` each have at least one task with an expected verdict | build |
| B6 | every number in the bundle's `CLAUDE.md` exists in `snapshot.json` | build |
| B7 | every `tools/<name>/tool.json` passes `tool_contract`, and fixture calls honour the error contract | build |
| B8 | every skill has a trigger sentence in `CLAUDE.md`; named scripts exist; no `inferred` claim in `CAPABILITIES.json` | build |
| B9 | safety-relevant tool call paths have the place of a deterministic gate (A5) | build |
| B10 | with `gui/`: every `gui_spec` input maps to a `tools/*/tool.json` parameter or a `CAPABILITIES.json` item; no numeric threshold in `gui/`; the GUI validation hook calls the scientific core's validator | build |

Rules (from SMA): check and fixture in the same commit; a new fixture is watched failing first; `--expect-fail` must reject both totals in full; UNDECIDED and PENDING are not passes; every number is read off a run and the verdict line names the judged tree.

**How M0 runs checks 6 and 7.** Both read git: `--staged` judges the index against the committer identity git will use (the pre-commit hook's mode), `--commit-range A..B` judges each non-merge commit. Their logic is also exercised without git through `scenario.json` fixtures under `examples/rejected/` (a committer email with its changed paths; a list of status-and-path changes), so that `--expect-fail` covers them deterministically.

---

## 9. Permission model

**Seats**: `design-…` (root files, `contracts/`, `docs/`, `meta_agent/CLAUDE.md`, `meta_agent/.claude/`, and in M0 the `meta_agent/` skeleton it creates), `meta-…` (the rest of `meta_agent/`; onboarding too), from M5 `harness-…` (`meta_agent/harness/`). The person assigns a seat per session. Names are `<role>-<machine>-<YYYYMMDD>-<n>`; this computer's tag is `office`. The committer is `seat:<name>` <`<name>@seat.invalid`>, the author stays the person.

**Human-only**: safety values, seating, bundle hand-over (`landed_at`), permission to loosen / retire / change the core, thresholds (tolerance, k, N), verdicts on prior entries, **confirmation of analysis permission** (`analysis_permission`), release of `held`, validation tasks on hardware, **answers to policy questions and the `inferred → confirmed` transition**, publication scope, dropping material (giving the location) and confirming intaken metadata, quotation permission (`may_quote`) and license judgements.

**One working copy, no worktrees** (SMA's decision). Commits name their paths; work lands on `main`.

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
| **M3** | Parameter Intelligence: three stages, tiered search, helpers, a comparison trial across two or more adapters, the `protein` card format (composition / condition separation) | a sheet with empty safety rows passes check 4; a filled one is a rejected fixture; every row of the comparison keeps its `value_kind` |
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

1. **Repository location and git init.** Settled 2026-10-29: `D:\codes\github\meta-agent`, GitHub `kyu-softmatter/meta-agent`, private, MIT.
2. **Language of the record.** Settled with the approval: English `plan.md` is the record; the Korean plan is frozen at `docs/origin/PLAN.ko.md`.
3. **The relation of `contracts/`.** Recommendation: copy SMA's `common.schema.json` and `units.json` pinned to a commit hash and record the provenance. When connected, which side is the record? (M0 wrote its own `common.schema.json` and `units.json` in SMA's shape rather than copying, because SMA's carry microscope-specific vocabulary; the question of the record when connected stays open.)
4. **First real agent.** ~~Recommendation C RheoTool → B rheometer.~~ **Decided 2026-10-29: the first testbed is the lab's rheometer (B) and a rheology simulation engine (C) as a pair; done = their cross-validation.** The order inside the pair stays a recommendation (§10). Remaining: §14-20, 21.
5. **Runtime.** Do built agents run as Claude Code sessions, or also as SDK processes? Recommendation: emit skills in a **portable layout** (`skills/<name>/SKILL.md` + plugin manifest) like REA, and vary only the per-runtime installation.
6. **Seed transfer.** Permission to move SMA's `failures.jsonl` and `incidents.jsonl` into cases.
7. **When to introduce text similarity or vector search.** Recommendation: after deterministic matching produced `case_gaps` and the person found the relevant case by hand N times.
8. **harness2.** Reference only (recommendation, now), or trial as an engine (after M5, under SMA's trial design, on a computer without instruments).
9. **Commit tool.** When to bring in SMA's `seat_commit.py`.
10. **Licenses.** This repository MIT. Third parties (verified 2026-10-29 against each repository): harness2 Apache-2.0 (reference only; its `third_party/` keeps upstream licenses), REA MIT (called as a tool; its MIT does not cover the Hopper / IDA engines, Ghidra is Apache-2.0, its Windows addon statically links the MinGW-w64 runtime under GPL-3 with the GCC runtime exception; its DISCLAIMER leaves reverse engineering to the analysed software's license), RheoTool GPL-3.0 and OpenFOAM GPL-3 (**called out of process, never bundled**; OpenFOAM is a registered trademark), HOOMD-blue BSD-3-Clause, HOOMD_GUI **no license yet** (reference only until one exists). Not legal advice; the institution's IP policy may apply.
11. **External database access policy.** Allowed hosts, where API keys live, local archive (cache) location, each database's terms.
12. **Grade derivation for database values and predicted structures.** Which grade per `value_kind` (measurement database / correlation / predicted structure / design record). M0's initial table is §6.3.
13. **Timing of the protein area.** Card format in M3; adapters when a request asks (recommendation).
14. **Procedure for confirming analysis permission.** Who (a person), with what (license clause, vendor consent), where (`docs/ideas/` commit → `analysis_permission.basis`).
15. **Threshold list (UNDECIDED).** Scientific tolerance, build-level k, promotion count N, four-condition sample size. All chosen by a person after baselines.
16. **GUI scope and stack.** Whether to do M9; whether HOOMD_GUI's `web/` + `python/` structure is the starting point of the common frame (after its license); whether to start with a parameter form only (recommendation).
17. **Lab Profile scope.** This lab only (recommendation, now) or several labs; if several, how `lab_id` is assigned and what profiles share.
18. **Materials for preferred simulation engines and experimental platforms (a slot, not a question).** PDFs or links for manuals, API documentation, papers and specifications are **not needed now**; drop them whenever they exist: one row in `meta_agent/inbox/materials/LINKS.md` or one file in `drop/` (§5.0). Targets are the four tools of §0 and any other engine (LAMMPS, GROMACS, OpenMM, OpenFOAM, FEniCSx, …) or instrument the lab uses or plans to use. Intake → confirmation → distillation → discovery re-run for that item; design and build never wait. **As of 2026-10-29: none; to be dropped later.** The rheometer's and the rheology engine's materials (§14-20, 21) are used first.
19. **This lab's onboarding answers.** What the wizard will ask that no material can infer: main research kinds and methods (multiple), preferred languages and environments, publication scope of agents and results, approval mode (which actions need a person), collaboration mode with the existing SMA agents (bridge). Answer now or when M1's wizard asks.
20. **Choice of the rheology simulation engine.** Candidates: the proposal's RheoTool / OpenFOAM (continuum, viscoelastic CFD); for particle- or coarse-grained suspension rheology, HOOMD-blue (BD), already in SMA. Which, or both, is the person's. Once chosen it is registered and its materials are the inbox's first item. With two engines C splits in two and the person orders them.
21. **The rheometer's specification.** Model, control software and its API / scripting interface, data export format, basis of the analysis permission (§14-14). The proposal says only "TA Instruments" (to verify). This answer is the minimum for B's `tool_profile` to start; safety values (torque, temperature, gap limits) are written by a person even then.

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
