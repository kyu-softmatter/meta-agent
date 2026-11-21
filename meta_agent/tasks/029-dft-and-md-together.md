# 029 — The Meta-Agent tested on DFT and MD together (DFT→MD)

**Status:** open. Opened by `design-macbook-20261120-1` at the ask of `meta-macbook-20261120-1` (note `../inbox/seats/20261120-meta-macbook-20261120-1-1.json`), on the person's words of 2026-11-20 (`../../docs/ideas/20261120.md`, "DFT and MD together" and "The DFT→MD clone's four questions, answered"). The meta seat `meta-macbook-20261120-1` holds it once it claims it; it ran the test on the person's word before this card existed, and this card records that work.

**Seat:** one `meta-…` seat holding this task alone. The design part, this card, has landed. A record that falls in the design role's paths (a check, a schema, a session skill, `testfolder.py`, `docs/ideas/`) goes to that role as a note.

**Goal:** a fresh blind clone session is given the person's request "DFT와 MD를 함께 고려하는 시스템을 만들어보고싶어." with the reading the person chose, "DFT→MD 파라미터 전달". What it does is collected and read, and what it shows enters the repository as failure lines, cases, notes or new versions.

**Inputs:**
- `../eval/briefs/clone-dft-md.txt` (the request with the reading) and `../eval/briefs/clone-dft-md-answers.txt` (with the person's answers to the clone's four questions as well);
- `../../docs/ideas/20261120.md`; `../../.claude/skills/test-outside-the-repository/SKILL.md`.

**Done when (read off a run):** each run was made from the committed head with one unattended session in its clone, collected and removed, its collection still in the log folder under `multiscale/`; what it showed is in failure lines, cases, notes or new versions, each naming the run and the collection; this card says how far each clone went, what it asked and what it inferred, and what was watched and what was not.

**Must not:** put any answer in a brief that the person did not give; change a build or decide a threshold from the test; fix a fault in anything but a general mechanism shown on fixtures of two unrelated kinds; push.

## What the record holds when this card is opened (2026-11-20)

- Run `multiscale/20261120-3`, brief `clone-dft-md.txt`, collection `collect-1`, session `8bd0ac8c`: failure lines `dftmd-1` to `dftmd-6` in `../failures.jsonl` (`4399f51`).
- Run `multiscale/20261120-5`, brief `clone-dft-md-answers.txt`, collection `collect-1`, session `4176f759`: failure lines `dftmd-7` to `dftmd-9` (`b10d3f3`).
- Both clones stopped before any build on the same two gaps: units with no conversion through the registry (`dftmd-1`) and no card for a hand-over between two built agents (`dftmd-2`). How a hand-over travels (`dftmd-9`) was put to the person, who chose "Design a bridge now"; that design is task `031`, and a third round of this test waits for it.

Both runs still stand when this card is opened. The holding seat writes below how far each clone went, as `017` does.
