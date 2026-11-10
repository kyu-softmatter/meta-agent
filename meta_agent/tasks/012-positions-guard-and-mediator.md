# 012 — Subagents that hold positions, the safety guard and the mediator

**Status:** open, 2026-11-09. Opened by `design-macbook-20261109-1` on the person's words (`../../docs/ideas/20261109.md`: "서로 자신의 의견을 고집하는 와중에 타협 서브에이전트가 모두에게 적절한 범위를 찾아 제안하고 모두의 동의를 얻는", "안전쟁이도 추가", "목적을 잊지 않는 과학쟁이 필요", "지어진 에이전트 안에서 작동", "단순 협상은 건너뛰자", "협상 횟수는 최대 5회 그 이상이 되면 사람에게 보고"), recorded in plan.md 14-33. Nothing exists yet. Order: after `010` (subagent definitions in the template, B11) and `011` (`range_sheet`).

**Seat:** bundle check B12, the `run_plan` contract's `negotiation` part (with `013`'s design part), the `policy` file of the envelope and their fixtures are the design seat's and land first. The template's subagent definitions, `src/negotiate.py` and the tests are a `meta-…` seat's.

**Goal:** inside a built agent, a range is settled among subagents that each hold a position and a mediator that proposes one all accept. What code can decide, code decides: the intersection, whether the negotiation is skipped, agreement on a hard limit, the count of rounds. The Meta-Agent builds this and judges it on a mock.

**What is settled (the person, 2026-11-09):** subagents each holding a position, the list open; a compromise subagent that proposes and obtains the agreement of all; a safety subagent among them; a science subagent that does not forget the purpose; inside the built agent; simple negotiations skipped; whether an agreed range is adopted as it stands is the built agent's user's, changeable later; at most five rounds, then the person is told; giving up a requirement of the science subagent is the person's under any setting; experiment and simulation are different bundles; under adoption as agreed a run on hardware starts without asking (`013` builds what that needs). The names are the seat's by the person's word.

**Inputs:**
- `../../plan.md` 3 (MP1, MP4, MP10, MP11), 5.1 S5, 9, 14-31, 14-32, 14-33; `../../docs/ideas/20261109.md`.
- `010`: the template's `.claude/agents/`, B11; `011`: `range_sheet`; `../src/build/template_v1/src/gate.py`, `envelope/safety.json`.

**Method (recommended, not settled):**
- Design seat, kinds: a subagent definition states `kind: advocate | guard | mediator | worker` (the last being `010`'s `operator` and `analyst`). An instrument bundle has the advocates `objective`, `budget`, `measurement`; an engine bundle `objective`, `budget`, `numerics`; each has the guard `safety` and `mediator`. An advocate's definition declares its skills and its soft preferences as directions, `{quantity, prefers: higher | lower, reason}`.
- Design seat, B12: an advocate, a guard and the mediator name no `read_device` or `write_device` skill; a guard declares no preference and no order of concession; the mediator declares no limit; every direction names a quantity of the bundle's `range_sheet`; `envelope/policy.json` exists with `adoption: null`. Rejected fixtures, one per assertion.
- Design seat, the envelope: `envelope/policy.json`, `{adoption: null}` in a bundle; at a destination the user writes `{value: confirm | adopt, set_by: human, date}`; unset is read as `confirm`. A change is a new revision.
- Meta seat, `src/negotiate.py` in the template, code only: reads the `range_sheet` and the definitions; the **skip**: where one feasible configuration is ahead of every other on every declared direction it is taken, `negotiation.mode: skipped` with the reason, and no subagent is called; otherwise `mode: held`. In a held negotiation code keeps the count of rounds (at most five), runs every hard limit again on each proposal and writes `hard: pass | fail`; `safety`'s answer is `gate.py`'s function on the proposal, with a missing value answered `not_set` and the configuration `held`; a proposal that relaxes a requirement held by `objective` stops the negotiation and is reported to the person under either adoption value; after the fifth round without agreement the outcome is `reported_to_person`, naming the limits that collide and each subagent's last answer.
- Meta seat, what the model does, as files: each advocate writes its soft answer (`accept | object`, reason) and its order of concession; `mediator` writes each proposal (a configuration, what it relaxes, why). In tests these are fixture files, as `007`'s binding file is, so the same files give the same `run_plan`.
- Meta seat, the trial plan.md 14-33(o) asks for: one fixture request run with the negotiation and with the plain intersection, the two outcomes side by side in a file a card can cite.
- Tests: a request with one dominant configuration is skipped and calls no subagent; a request with two configurations ahead on different directions is held and agrees inside five rounds on the fixture answers; fixture answers that never agree end at five rounds with `reported_to_person`; a proposal that breaks a hard limit is answered `fail` whatever the subagent's file says; a missing safety value makes the configuration `held`; a proposal relaxing `objective` stops and is reported; an advocate that names a device skill fails B12.

**Done when (read off a run):**
- `python contracts/validate.py --expect-fail` rejects every fixture under `checkB12_*`; `python contracts/validate.py` prints `0 failed`.
- On the fixture bundle the four cases above (skipped, agreed, five rounds, `objective` relaxed) each write the outcome named; the trial's two outcomes are on file.
- `PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .` is OK.

**Must not:** let a subagent's word stand where a check can decide; let `safety` make, fill or concede a value; negotiate a configuration that needs an unset safety value; go past five rounds or force a compromise; relax a requirement of `objective` without the person; infer `adoption`; put `measurement` and `numerics` in one bundle; design the negotiation between two bundles (M8); give a subagent a seat or let it commit.

**Report:** ten lines or fewer — the subagents by kind in the fixture bundle, the fixture count of B12, the outcome of each of the four cases with its rounds, the trial's two outcomes, the verdict line, the test count.
