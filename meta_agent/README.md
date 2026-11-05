# meta_agent/

The one agent of this repository: onboarding, Agent Designer, knowledge engine, parameter intelligence, experience memory and meta-harness, all writing cards that `../contracts/validate.py` judges. `CLAUDE.md` here is what a session seated as this agent follows.

**M1: onboarding and the Designer run.** `python -m meta_agent.src.onboarding` reads a lab (S0) and `python -m meta_agent.src.designer` takes a request through S1–S6; both are read off their cards, and `tests/` runs them on fixtures (`PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .` from the repository root). The layout the plan names (`../plan.md` 7):

| Path | What | When it fills |
|---|---|---|
| `tasks/` | the task queue; `001` onboarded the fixture labs and this lab, `002` built the echo agent on mock (M1, done); `003` proposes a derived wiki view and an ontology of the cards (waiting for the person) | M1 (done), 003 proposed |
| `failures.jsonl` | one failure per line, append only | from the first run |
| `envelope/observed.json` | read-only paths of built agents the harness may observe | M5 |
| `inbox/materials/` | where the person drops links and files; `README.md` there explains | any time; intake code in M2 |
| `inbox/<thread>/` | observations from the person or the bridge | M8 |
| `profiles/<lab_id>/` | discovery report, onboarding record, lab profile revisions | M1 (two fixture labs, this lab waiting for answers) |
| `requests/<rid>/` | one request, flat: intake, goal, tool profile, brief, axes, synthesis, spec | M1 (`req-echo-001`) |
| `templates/agent@<hash>/`, `builds/<agent>/<build_id>/` | the versioned bundle template and each build: bundle, build card, validation report, diff from the template | M1 (`echo/0001`) |
| `knowledge/`, `cases/`, `harness/`, `eval/` | as the plan's layout | M2–M5 |

The accepted example set under `../contracts/examples/` is laid out the way this folder will be, so the shape can be read before the code exists.
