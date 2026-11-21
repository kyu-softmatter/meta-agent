# 033 — A hub agent and a session per engine

**Status:** open, 2026-11-20; the design part landed the same day (section below), the meta part waits for a `meta-…` seat. Opened by `design-macbook-20261120-3` on the person's words of 2026-11-20 (`../../docs/ideas/20261120.md`, "Several engines or instruments: a hub session that assigns, and a session per engine"): "여러 시뮬레이션 엔진 또는 하드웨어를 운영하고자 하는 경우에는 전체 질문을 받고 업무를 배정하는 세션(연 세션)과 개별 엔진을 관리하는 세션을 추가로 열어서(fork 또는 fresh) 세션간 메세지로 세션간 소통을 할 수 있게 하자." (when several engines or pieces of hardware are to be operated, let the session opened take the whole question and assign the work, open further sessions each looking after one engine, as a fork or fresh, and let them talk by messages between sessions), and the four answers recorded there. Plan: §14-41.

**Seat:** the design part (the cards, the check, the fixtures, the plan, the hub template's drawing) is the design role's and lands first. The meta part, the hub template and the builder that makes a hub bundle beside its engine bundles, is a `meta-…` seat's once `design_part` is `landed` in `index.json`.

**Goal:** a person who wants several engines or instruments operated together speaks to one session, the hub's, which takes the whole question, splits it into one assignment per engine agent, has each engine agent run in a session of its own, gathers what they return and reports to the person; the sessions speak by messages that only point at cards, and every value stays in a card on disk with its source and grade.

**What stays as it is:** the Meta-Agent never integrates engines and never runs a built agent (MP1, plan.md 10). Each engine bundle stands alone (MP2): without the hub it runs as now, and an assignment is one more card in its `inbox/<thread>/`. A card of values crosses from one engine agent to another only on the person's word, through `contracts/tools/bridge.py carry` (task `031`, "Only on my word"; the person again on 2026-11-20, "Assign freely, carry on my word (Recommended)"). A message carries no value and no decision (plan.md 14-38(f); "Pointer to a card (Recommended)"). The Meta-Agent's own seat sessions keep their hub of plan.md 14-38(e); nothing here changes them.

**Inputs:** plan.md 3 (MP1, MP2, MP10, MP11), 6.1, 8 (check 25), 10, 14-38(c)–(g) and (j), 14-40; task `031` and its cards (`handover`, `bridge_envelope`, `handover_receipt`) and fixtures `../../contracts/examples/bridge/`; `../../.claude/skills/open-sessions/SKILL.md`, whose hub, brief and report form are the shape the hub agent's own session skill follows; the DFT→MD builds `qe-h2-bond` and `hoomd-h2-bond`, the first case.

**Done when (read off a run):** the design part has landed, each new check with its rejected fixture in the same commit, watched failing first; `python contracts/validate.py` passes and `--expect-fail` rejects both totals in full; the accepted fixtures stand for two unrelated kinds, one of them not rheology; every choice between designs, policy or permission in it was put to the person and the answer is in `../../docs/ideas/`; `index.json` says `design_part: landed`.

**Must not:** build a bundle; run an engine; let the hub carry a value card between engine agents without the person's word; let a message carry a value or a decision; let the hub compute, convert or judge a value; infer a round limit, a stopping rule, a model, an effort or a permission mode; push.

## Design (proposed by `design-macbook-20261120-3`, 2026-11-20; as landed, it is the section after this one)

### The hub bundle

A bundle built from a hub template beside the engine bundles of one request. It carries:

- `members.json`: the engine and instrument bundles it coordinates, each by name, build id, folder and the digest of its build card; the builder writes it and refuses a member whose digest is not its build card's.
- `question/`: the person's whole question as a card, as an engine bundle's request is now.
- `assignments/`: one `assignment` card per engine agent and round.
- `inbox/<thread>/`: what the bridge carries back to it, each beside its envelope.
- `CLAUDE.md` and one session skill, `run-hub`: take the question, split it, assign, open the engine sessions, read what they return against their cards, report; the same steps the repository's `open-sessions` skill gives its hub, said for built agents.
- no `tools/` that reach an instrument or an engine, no `write_device` or `read_device` skill, no library skill that computes a quantity: the hub reasons over cards and quotes them by path.

### Two cards

1. **`assignment`**, written by the hub in its own `assignments/`: `thread`, `round`, `to` (one member, by build), `asks` (what the engine agent is to find, in words and with no number the question does not hold as a card), `inputs[]` (paths and hashes of cards the engine agent may read, each of which reaches it only through the bridge), `returns` (the card kind the hub expects back: a `handover` to another member, or a `result` to the hub), `done_when`, and `numbers: []` unless every number is quoted from a card it names.
2. **`result`**, written by an engine agent in its own `outbox/` to the hub: the assignment it answers (id and the envelope's hash), what was run (the run records it was read off), the values (each a number of plan.md 6.3, its grade derived), and what is held and why. A value the hub reports to the person is quoted from the copy in its own `inbox/`, so check 3 finds it in the folder.

### The bridge, one more trigger

`bridge.py carry` gains `--trigger hub`, for the hub's run: it carries an `assignment` from the hub's `assignments/` into a member's `inbox/<thread>/`, and a `result` from a member's `outbox/` into the hub's `inbox/<thread>/`, and refuses any other card on that trigger. A `handover` from one member to another still needs `--released-by human` and the person's word for that crossing. The envelope's `trigger` gains `hub`, with `released_by: hub`; check 25 refuses an envelope whose trigger is `hub` and whose payload is not an assignment or a result, and an assignment carried to anything but a member of the hub that wrote it.

### Sessions and messages

- The hub's session is the one the person opens in the hub bundle's folder. It opens one session per member, **fresh in that member's folder by default**, so that the member's `CLAUDE.md`, guardrails and envelope bind it; its brief names the assignment's path in the member's `inbox/<thread>/` and nothing else. A **fork** inherits the hub's conversation and, as this app opens one, works in the hub's folder: it is for work that stands in the hub's folder, and an engine session is a fork only where the application can open it in the member's folder. Each session is its own: a member session writes only its own bundle.
- A message between them is a pointer, `{thread, card path, sha256}`, and the short report form of plan.md 14-38(f). The envelope's presence in `inbox/<thread>/` is the turn, as in SMA, so a session in a terminal or on another computer reads the same files and loses nothing but the nudge.
- The hub opens no session and carries nothing beyond what the person's question asked for; what it may do without asking each time is the open question below.

### Put to the person, and answered (2026-11-20)

The role of this seat, "Design seat (Recommended)"; the hub's form, "A hub bundle (Recommended)"; assigning and carrying, "Assign freely, carry on my word (Recommended)"; what a message carries, "Pointer to a card (Recommended)" (`../../docs/ideas/20261120.md`).

### Answered on 2026-11-20, three more (`../../docs/ideas/20261120.md`, "Task 033: three more answers")

- the second fixture kind: "Three engines, one hub". The seat's choice of the three, for fixture cards only: a photonic device heated by the light it absorbs, a mode solver (MPB) giving an effective index, an FDTD engine (Meep) giving the power absorbed, and a heat-conduction engine (FEniCS) giving the temperature rise, under one hub; it shares nothing with DFT→MD in science or in engines, and it is not rheology;
- opening the members' sessions: "Ask once per question (Recommended)": the hub shows the list of its assignments once for each question and opens the members' sessions within it without asking again;
- rounds: "until solve the problem": no limit on their number; the hub goes on by itself until the question's `done_when` is answered by result cards that are not held, and waits only where what is left is the person's (a hand-over crossing, a tolerance, a safety value, a permission, a release of `held`); a new assignment outside the agreed list is shown to the person again (the seat's reading, in the ideas file).

### Still the person's

- what the hub does when a round adds nothing (recommended: stop and report, which sets no number);
- the model, effort and permission mode of the hub's and each member's session (a cost and a permission; `choose-session-level` recommends).

## The design part, landed (2026-11-20, `design-macbook-20261120-3`)

- **Four cards:** `contracts/schemas/hub_members.schema.json` (the hub and two members at least, each by build, folder and build card hash; no numbers), `hub_question.schema.json` (the person's question verbatim, `done_when` items, the list of assignments, and `agreed`, the person's words agreeing to it, absent until given), `assignment.schema.json` (thread, round, question, from the hub, to a member, `asks` in words, `answers_items`, `returns`, `done_when`; `numbers` must be empty) and `result.schema.json` (from a member to its hub, `answers` naming the assignment and the envelope that carried it, `state` answered, held or partly held, a held state with at least one `held` entry saying what, why and what it needs, an answered one with none). plan.md 6.1 lists them. Two cards rather than the one `question/` folder of the proposal: the person's agreement once per question needed a card to stand in.
- **The bridge, the hub's trigger:** `bridge.py carry --trigger hub --released-by hub --ran-by hub --session ID` carries an assignment from a hub's `assignments/` into the member its `to` names, at the folder `members.json` gives, only when the assignment is in a `hub_question` with the person's agreement; and a result from a member's `outbox/` into its hub, only when `members.json` there lists the member at that folder. On that trigger it refuses a hand-over. The person's word (`--trigger human`, the default) carries any of the three cards, as before. The envelope schema takes `trigger` human or hub, `released_by` human or hub, `ran_by` `{by: hub, session}`, and a payload of any of the three cards, with `origin` in `assignments/` or `outbox/`.
- **Check 25** (plan.md 8): the trigger agrees with who released and who ran; on the hub's trigger no hand-over; an assignment stands in its hub's `assignments/`, from that hub, to a listed member, inside an agreed list, or in an `inbox/<thread>/` beside its envelope; a result stands in an `outbox/` or in its hub's `inbox/<thread>/`, answering an assignment of that hub on the same thread, made to the agent that returns it. Rejected fixtures: `check25_hub_carries_a_handover`, `check25_hub_trigger_released_by_the_person`, `check25_assignment_to_a_non_member`, `check25_assignment_not_in_an_agreed_list`, `check25_assignment_outside_assignments`, `check25_result_answers_no_assignment`, and `check01_assignment_with_a_number`, drawn from both kinds. Each check-25 fixture was watched accepted with the new parts of check 25 left out and rejected with them, for the reason it was written for; the check-1 fixture accepted with the assignment's `numbers` unbounded and rejected as landed.
- **Two kinds:** `contracts/examples/hub/dft-md/` (a hub over `qe-h2-bond` and `hoomd-h2-bond`) and `contracts/examples/hub/photonic-heating/` (a hub over a mode solver, an FDTD engine and a heat-conduction engine, the three the seat chose for the person's "Three engines, one hub"). Their copies and envelopes were made by running `bridge.py carry --trigger hub` on these folders. Tests: `contracts/tests/test_hub.py`, on both kinds.
- **Not changed:** the agent template, the builder, and the repository's own session skills. The hub template, its session skill (`run-hub`: take the question, split it, show the list once, carry the assignments, open each member's session fresh in the member's folder, read the results against their cards, go on until solved or until what is left is the person's, report) and the builder that writes `members.json` are the meta part.

- **B19, at the meta role's ask** (note `../inbox/seats/20261120-meta-macbook-20261120-4-1.json`): a bundle whose `TEMPLATE.json` says `template: hub` is judged by B19 and B2 in place of B1–B18, as plan.md 8 says; `bundles_of` now hands each build card to the bundle checks, so B19 compares `members.json`'s hub build with the build's own and `src/bridge.py` with the copy in the template folder the build card names. Six rejected fixtures `checkB19_hub_…`, three from each kind, each watched accepted with B19 left out and rejected with it; a hub bundle of each kind, made by the seat outside the repository, passed `--bundle`. Taken as the meta seat proposed, with two choices of this seat: a member's folder is `../<agent>-<NNNN>`, and the bridge copy is compared with the template's copy, so that a later change of `contracts/tools/bridge.py` does not fail a hub built before it.

## The meta part (for a `meta-…` seat, once the design part has landed)

**Goal:** a hub template and a builder that makes a hub bundle beside the engine bundles of one request, whose `members.json` names them by build and digest; the first case is a hub over `qe-h2-bond` and `hoomd-h2-bond`.

**Done when (read off a run):** the hub build passes its gate; `python contracts/validate.py <a folder holding the hub and its members> --checks 1,2,25` passes after an assignment and a result have crossed on the hub's trigger and a hand-over on the person's word; a test standing alone, as `../../.claude/skills/test-outside-the-repository/SKILL.md` says, in which the hub's session opens its member sessions and reports.

**Must not:** give the hub a tool that reaches an engine or an instrument; let it compute a value; carry a hand-over between members without the person's word; change `../../contracts/` (ask the design role by a note); push.
