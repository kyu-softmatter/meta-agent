# meta_agent/

The one agent of this repository: onboarding, Agent Designer, knowledge engine, parameter intelligence, experience memory and meta-harness, all writing cards that `../contracts/validate.py` judges. `CLAUDE.md` here is what a session seated as this agent follows.

**M1: onboarding and the Designer run.** `python -m meta_agent.src.onboarding` reads a lab (S0) and `python -m meta_agent.src.designer` takes a request through S1–S6; both are read off their cards, and `tests/` runs them on fixtures (`PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .` from the repository root). The layout the plan names (`../plan.md` 7):

| Path | What | When it fills |
|---|---|---|
| `tasks/` | the task queue; `001` onboarded the fixture labs and this lab, `002` built the echo agent on mock (M1, done); `003` renders a wiki view and an ontology from the cards (done); `004` adds a 3D map of the cards to the view (done); `005` adopts auto-ontology-mcp as M2's working index for materials and recall (open); `006` recall and the SMA seeds (M4), `007` parameter bound skills as source code that the model picks, the feasible interval and the first adapter (M3; rewritten 2026-11-09), `008` the meta-harness cut to what code fills (M5), opened 2026-11-08 in that order (open); `009` the agent-native environment (a seat command, a commit tool for a shared working copy, the task index and claims, notes between seats, CI), done 2026-11-09 (the first CI run passed at `2b7dd69`); `010` the skill library (one layout and manifest for every kind: bound, hardware connection, boot sequence, situation awareness, control, calibration, data analysis) and the bundle's subagents that use it, opened 2026-11-09, after `009` and before `007` (open); `011` the rough ranges of the key quantities on a card of their own and the model's choice among skills, rules and candidates, `012` a built agent's subagents that hold positions, its safety guard and its mediator, `013` a built agent's run on a mock from the plan card to the report, opened 2026-11-09 on the person's words of that day, in that order after `007` (open); `014` the operable range of an instrument, read by a built agent as it scans, after `010` (open) | M1 (done), 003 (done), 004 (done), 006 (done, 2026-11-09: recall and 238 draft seeds), 009 (done), 005, 007, 008 and 010–014 (open) |
| `failures.jsonl` | one failure per line, append only | from the first run |
| `envelope/observed.json` | read-only paths of built agents the harness may observe | M5 |
| `inbox/materials/` | where the person drops links and files; `README.md` there explains | any time; intake code in M2 |
| `inbox/<thread>/` | observations from the person or the bridge | M8 |
| `profiles/<lab_id>/` | discovery report, onboarding record, lab profile revisions | M1 (two fixture labs, this lab waiting for answers) |
| `requests/<rid>/` | one request, flat: intake, goal, tool profile, brief, axes, synthesis, spec | M1 (`req-echo-001`) |
| `templates/agent@<hash>/`, `builds/<agent>/<build_id>/` | the versioned bundle template and each build: bundle, build card, validation report, diff from the template | M1 (`echo/0001`) |
| `wiki/` | a view rendered from the cards by `python -m meta_agent.src.wiki`: one page per card revision, an index, `ontology.owl` for Ontology Playground, `graph.html` a 3D map with a 2D switch; not in git, never edited (check 18) | on demand (`tasks/003`) |
| `knowledge/`, `cases/`, `harness/`, `eval/` | as the plan's layout | M2–M5 |

The accepted example set under `../contracts/examples/` is laid out the way this folder will be, so the shape can be read before the code exists.
