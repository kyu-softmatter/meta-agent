# 015 — The agent and the agents it builds work from skills

**Status:** open; the design part landed on 2026-11-12 but for the wiring of B15 (see "What the design part landed" below), by `design-macbook-20261112-1` (claim `claims/015-design-macbook-20261112-1.json`). Opened by `design-macbook-20261112-1` on the person's words (`../../docs/ideas/20261112.md`: "결국 이 에이전트도 스킬을 기반으로 움직이고, 만들어지는 생성물 에이전트도 스킬을 기반으로 움직이도록 하자"), recorded in plan.md 14-37. Nothing exists yet. Order: after `010` (the skill layout and the runner, done). It does not wait for `011`–`014`, and they use what it gives where it exists.

**Seat:** the session skills under `.claude/skills/`, the two `CLAUDE.md` files brought down to the rules, check 24, bundle check B15 and their fixtures are the design seat's and land first. The bundle's one session skill, the generated page per library skill, the template that carries them and the tests are a `meta-…` seat's.

**Goal:** a session of this repository, and a session of a bundle built here, learns what to do from a skill it loads when it needs it, and reads whole only the rules that bind it always. Every calculation of a quantity is a library skill reached through the runner. A session opens other sessions fresh or as a fork by one procedure, and they report to each other in one form.

**What is settled (the person, 2026-11-12):** working from skills is efficient, and sessions are divided into fresh or fork so that they communicate efficiently (a finding); the deterministic Python calculations for approximate estimates and for parameter calculation are each made a skill; this agent works from skills, and the agents it builds work from skills. Standing: every hand-over is a card on disk; a session is its own seat, registered before any other work (plan.md 9); the person alone decides what plan.md 9 keeps human-only; a model's number is E6 and enters nothing; the Meta-Agent builds and never operates (MP1).

**Two words kept apart (plan.md 14-37(a)):** a *library skill* is source code with a manifest and worked cases under `meta_agent/skills/` or a bundle's `skills/` (check 22). A *session skill* is a procedure in `.claude/skills/<name>/SKILL.md` that a session loads when its description matches. This task writes session skills and changes no library skill.

**Inputs:**
- `../../plan.md` 3 (MP1, MP2, MP5, MP8), 5.1 S5, 8 (checks 21, 22, B8, B11), 9, 14-29, 14-30, 14-31, 14-32, 14-37; `../../docs/ideas/20261112.md`, `../../docs/ideas/20261109.md` ("Sessions may be opened for the building").
- soft-matter-agents, branch `calculator-runner` at `38f4de2`: its plan.md 4.5.2.2 and `contracts/tools/skills.py`, for one session skill per agent in front of a dispatcher, and pages rendered from the table.
- `../../CLAUDE.md`, `../CLAUDE.md`, `../../contracts/tools/{seats.py,seat_commit.py,tasks.py,notes.py,skills.py}`, `../src/skills/{runner.py,catalogue.py}`, `../src/build/template_v2/`.

**Method (recommended, not settled):**
- Design seat, the session skills of this repository, under the root `.claude/skills/`, since every command is run from the root. Few: one per procedure a session begins on its own cue, never one per item.
  - `begin-session`: the gate, the seat and its commit, the notes for the role, the next task and its claim. It replaces the block of commands in the root `CLAUDE.md`.
  - `open-sessions`: the hub's procedure. Which sessions and why; fresh or fork for each (plan.md 14-37(c)); the brief of a fresh session, whose first line names the task card; that a fork registers its own seat and writes down what it inherited (14-37(d)); the report form (14-37(f)); reading a report against the commit before telling the person (14-37(g)).
  - `end-session`: sorting what went wrong into `failures.jsonl`, a `case`, the skill or the `CLAUDE.md` line it corrects, or a note to the role that owns the path (14-37(h)); the gate; the report.
  - `run-pipeline`: one session skill for the Meta-Agent's S0–S7, with one page per stage beside it that is reference and not a trigger. It replaces the stage list in `../CLAUDE.md`.
  - Each `SKILL.md` names the commands it runs and the files it writes, and holds no rule that is not also in a `CLAUDE.md`, no number, no limit and no threshold.
- Design seat, the two `CLAUDE.md` files: the rules, what the agent never has and never does, where things are, and one line per session skill saying when it is used. A rule stays where every session reads it; only procedure moves.
- Design seat, check 24, session skills: every folder under a `.claude/skills/` has a `SKILL.md` whose front matter has `name` and `description`, the name being the folder's; every command and path it names exists; the `CLAUDE.md` beside or above it names it; it carries no number outside code spans. Rejected fixtures, one per assertion, watched failing first.
- Meta seat, the bundle: the template gains one session skill that sends the bundle's session to its runner and says what a session may and may not change (it may ask for a further library skill with a reason; it types no value); code renders one reference page per library skill from its manifest; the bundle's `CLAUDE.md` keeps its rules and names the one session skill. A new template version, the difference recorded in the `build` card (MP3).
- Design seat, B15: a bundle has exactly one session skill that names its runner; every library skill of the bundle has its page and the page agrees with the manifest; a page is not a trigger. Rejected fixtures, one per assertion.
- Every calculation a skill (plan.md 14-32, added 2026-11-12): no relation that gives a quantity is computed outside a library skill. Read on 2026-11-12, a search of `../src/` found arithmetic in `parameters/bounds.py` only, the propagation and rounding of uncertainty. The meta seat reads the tree again when it starts and reports what it finds; whether that machinery becomes a skill is not answered.

**Waits for the person, and is left as it is until answered (plan.md 14-37):**
- whether a message between sessions is allowed beside notes, and what it may carry. Until then `open-sessions` uses notes, and a message, where one is sent, only points at a committed path;
- the default model and effort per role. Until then the hub chooses and tells the person;
- B8, which asks for a trigger sentence per skill in a bundle's `CLAUDE.md`, and who may leave an applicable skill out. Until then B8 stands and the trigger sentences stay beside the one session skill;
- which of the four session skills above are taken; the person may strike any.

**Done when (read off a run):**
- `python contracts/validate.py --expect-fail` rejects every fixture under `check24_*` and `checkB15_*`; `python contracts/validate.py` prints `0 failed`.
- `wc -l CLAUDE.md meta_agent/CLAUDE.md` is lower than on 2026-11-12, and a reading of the diff shows every rule of that day still in one of the two files.
- A fresh session given only its task card's path seats itself, claims the task and reports in the form of 14-37(f); watched once, the seat and the commits named in the report.
- The `echo` agent rebuilt from the new template passes its B checks, and a fresh session in the bundle handles its replay item through the one session skill, the Meta-Agent absent (MP2).
- `PYTHONUTF8=1 python -m unittest discover -s contracts/tests` and `-s meta_agent/tests -t .` are OK.

**Must not:** leave a rule in a session skill only; write one session skill per library skill or per calculation; put a number, a limit or a threshold in a session skill; let a fork commit as the seat whose conversation it inherited; let a message carry a decision or a number that is not in a committed file; change B8 or check 19 before the person has answered; edit a landed library skill (a change is the next version); open a path to an instrument (MP1); copy text from the private repository.

**What the design part landed (2026-11-12, `design-macbook-20261112-1`):**
- The person named the Meta-Agent's work as skills while this part was being done (`../../docs/ideas/20261112.md`, "The Meta-Agent's work, named as skills"), so `run-pipeline` above was not written. In its place there are eleven: `research-materials`, `analyse-physical-system`, `analyse-lab-environment`, `analyse-hardware`, `understand-purpose`, `design-tool-interface`, `design-gui`, `estimate-parameter-ranges`, `build-library-skill`, `specify-and-build`, `validate-and-record`. With `begin-session`, `open-sessions` and `end-session` there are fourteen, under `../../.claude/skills/`.
- `../../CLAUDE.md` and `../CLAUDE.md`: the setup and the new-session blocks and the stage procedure moved into the skills; the rules stayed, and two were added to the root file (working from skills; fresh and fork). Read off `wc`: the root file 52 lines to 42 and 6150 bytes to 7046, this folder's 40 lines to 39 and 5660 bytes to 5140. In bytes the two together grew, so the first "done when" line holds for lines only.
- Check 24, `../../contracts/tools/session_skills.py` (`check`, `list`), its tests, and seven rejected fixtures `check24_*`, each watched going unrejected before the check was wired.
- **Not landed: the wiring of B15.** The rule is `bundle_problems` in `session_skills.py`, with tests for each assertion; it applies to a bundle whose `TEMPLATE.json` says version v3 or later, so that the builds that exist are not judged by it. Wiring it into the gate made `../tests/test_skills.py` fail, which lists the bundle checks by hand (`B_CHECKS`), and that file is the meta role's. The design seat asked the meta role by a note and took the wiring and its five fixtures back out (`checkB15_no_session_skill`, `checkB15_two_session_skills`, `checkB15_session_skill_names_no_runner`, `checkB15_library_skill_as_a_session_skill`, `checkB15_session_skill_not_named`, each a bundle with a `TEMPLATE.json` of version v3). When the test reads the list from the validator, the design seat wires B15 with those fixtures in one commit.
- A fault of the validator met on the way and fixed: `--expect-fail` raised an error while printing a fixture that was not rejected and had a bundle check among its failures.

**What is left for a `meta-…` seat:**
- `../tests/test_skills.py`: take the list of bundle checks from the validator, so that a new bundle check does not fail it (the note asks this; B12 to B14 will meet the same line).
- The bundle part of the method above: a template version v3 that carries one session skill naming the runner, the bundle's `CLAUDE.md` naming it, the `echo` agent rebuilt from it, and the fresh session of "done when", which is the meta seat's own session when it takes this task from its card alone.
- Whoever makes template v3 first, for this task or another, makes it with the session skill: from v3 on B15 asks for it.

**Report:** ten lines or fewer — the session skills written, the line counts of the two `CLAUDE.md` files before and after, the fixture counts of 24 and B15, what the fresh session did, the template version and the bundle's verdict, the verdict line, the test counts.
