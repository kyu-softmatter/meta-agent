# 017 — The Meta-Agent tested on GROMACS

**Status:** open. Opened by `design-macbook-20261117-1` on the person's words (`../../docs/ideas/20261117.md`, "Tests on engines of other kinds": "GROMACS + top 4", "다른 세션들에서 각각 작성할거야. 실험계획을 남겨서 그들이 참고할 수 있게 하자."). Nobody holds it. It starts when the person opens a session for it and says so ("지금 말고 내가 말하면 실행").

**Seat:** one `design-…` seat, seated by itself under the standing rule, holding this task alone. Records that fall in another role's paths go to that role as notes.

**Goal:** a fresh clone session is given the person's request on GROMACS (molecular dynamics of a protein in water). What it does is collected, read against the questions of the shared plan, and set beside the HOOMD-blue tests and the other engines of this plan.

**Inputs:**
- `../eval/plans/engines-of-other-kinds.md`: why this engine, its link, the recommended brief, how a task runs, what a collection is read for, and what to watch for in GROMACS.
- `../../docs/ideas/20261117.md`; `../../.claude/skills/test-outside-the-repository/SKILL.md`; `../eval/briefs/clone-rheotool-bare.txt` and `../eval/briefs/clone-hoomd-blue-bare.txt` as the form of a brief without answers.

**Done when (read off a run):** the brief `../eval/briefs/clone-gromacs-bare.txt` is committed in the words the person confirmed; one run was made from the committed head with one unattended session in its clone, collected and removed, the collection still in the log folder; what it showed is in failure lines, cases, notes or new versions, each naming the run and the collection; this card says how far the clone went, what it asked and what it inferred, and what was watched and what was not.

**Must not:** write a brief or make a run before the person's word; put any answer in the brief that the person did not give for this engine; change a build or decide a threshold from the test; fix a fault in anything but a general mechanism shown on fixtures of two unrelated kinds; push.
