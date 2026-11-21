# 030 — The Meta-Agent tested on QM/MM in one coupling tool

**Status:** open. Opened by `design-macbook-20261120-1` at the ask of `meta-macbook-20261120-2` (notes `../inbox/seats/20261120-meta-macbook-20261120-2-1.json` and `-2-2.json`), on the person's words of 2026-11-20 (`../../docs/ideas/20261120.md`, "A second reading tested beside it: QM/MM" and "The QM/MM clone's questions, answered"). The meta seat `meta-macbook-20261120-2` holds it once it claims it; it ran the test on the person's word before this card existed, and this card records that work.

**Seat:** one `meta-…` seat holding this task alone. The design part, this card, has landed. A record that falls in the design role's paths goes to that role as a note.

**Goal:** a fresh blind clone session is given the person's request "DFT와 MD를 함께 고려하는 시스템을 만들어보고싶어." with the reading the person chose for this test ("너는 2번으로 테스트를 해보자.": QM/MM, a small region computed with DFT and the rest with MM, in one coupling tool, the agent being for that tool). What it does is collected and read, and what it shows enters the repository as failure lines, cases, notes or new versions. The category (`multiscale`) and the level (opus-5-5, high) were taken by the seat from the person's answers for task `029`; they are not the person's words for this test.

**Inputs:**
- `../eval/briefs/clone-dft-md-qmmm.txt` (the request with the reading) and `../eval/briefs/v2_clone-dft-md-qmmm.txt` (with the person's answers to the clone's Q2 to Q5);
- `../../docs/ideas/20261120.md`; `../../.claude/skills/test-outside-the-repository/SKILL.md`.

**The person's grant for this test:** the data source of the clone's Q5, `raw.githubusercontent.com`, read-only and anonymous, is the person's grant for this test's clone ("너 제안대로 해", 2026-11-20). Whether it holds for any other agent of this lab is not settled (task `023` is where data hosts are designed).

**Done when (read off a run):** each run was made from the committed head with one unattended session in its clone, collected and removed, its collection still in the log folder under `multiscale/`; what it showed is in failure lines, cases, notes or new versions, each naming the run and the collection; this card says how far each clone went, what it asked and what it inferred, and what was watched and what was not.

**Must not:** put any answer in a brief that the person did not give; change a build or decide a threshold from the test; fix a fault in anything but a general mechanism shown on fixtures of two unrelated kinds; push.

## What the record holds when this card is opened (2026-11-20)

- Run `multiscale/20261120-4`, brief `clone-dft-md-qmmm.txt`, collection `collect-1`, the clone's request `req-qmmm-001`: its questions Q2 to Q5, answered by the person (above). No failure line of this run is in `../failures.jsonl` yet.
- A new run with `v2_clone-dft-md-qmmm.txt` (`4ed4dcc`) was to be made by the holding seat.

The holding seat writes below how far each clone went, as `017` does.
