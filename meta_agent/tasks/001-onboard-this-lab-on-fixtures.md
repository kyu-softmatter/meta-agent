# 001 — Onboard this lab on fixtures

**Status:** done (M1), 2026-10-29, by `meta-office-20261029-1` in commit `1a0a0be`; read off the committed `onboarding_record` cards: the rich fixture lab was asked 6 questions (the policy fields only) and the empty lab 22 (the bank minus the deferred ones); this lab's own run (`profiles/lab-kyu-softmatter/`) stopped with 7 questions for the person. The validator printed `0 failed, 0 pending`. The research-kind and methods leaves were proposed under `conventions.*` because the lab_profile schema has no such leaves (a schema proposal for the design seat). **Opened:** 2026-10-29 by the design seat on the plan's instruction (plan.md 15-8).

**Seat:** the `meta-…` seat the person assigns.

**Goal:** make S0 real on two fixture labs and on this lab's own repositories, and read the result off `onboarding_record`, not off the code. Build `src/onboarding/` far enough that Step 0 reads a materials folder and repositories, Step 1 asks only what is `unknown` and the policy fields, Step 2 proposes a `lab_profile`, and Step 3 records only the person's confirmations as `confirmed`.

**Inputs:**
- `../../plan.md` 5.0 (the four steps, three states, question bank, sufficiency check, materials inbox), 5.6 (Lab Profile fields), 8 (checks 15, 16, 17).
- `../../contracts/examples/profiles/lab-fixture-01/` — the shape of the four cards.
- Two fixture labs you create under `tests/fixtures/`: one rich (a repository with `pyproject.toml`, input files, an existing agent card set, a `LINKS.md` row) and one empty.
- Read-only: https://github.com/kyu-softmatter/soft-matter-agents and https://github.com/kyu-softmatter/HOOMD_GUI as this lab's real input (plan.md 10, testbed A's first use).

**Done when (read off a run):**
- On the rich fixture lab the `onboarding_record` holds **policy questions only** (group 8 and `collaboration.mode`); on the empty lab it holds the full question bank. Both counts are printed by the run and quoted in the report.
- Every question targets a field that is `unknown` in the `discovery_report` or a policy field (check 16 passes; no `PENDING` unnecessary questions).
- `python ../../contracts/validate.py` prints `0 failed` with the new cards under `profiles/`.
- The real-lab run produces `profiles/<lab_id>/discovery_report.json` and the question list for the person, and stops there until the person answers (plan.md 14-19).

**Must not:** infer a policy field; write `confirmed` without the person's word; fetch anything with a credential; write outside `meta_agent/`; add a dependency the step does not need; touch `../../contracts/` (propose a schema change in the report instead).

**Report:** ten lines or fewer — what ran, the two question counts, the validator's verdict line, what is open.
