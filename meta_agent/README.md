# meta_agent/

The one agent of this repository: onboarding, Agent Designer, knowledge engine, parameter intelligence, experience memory and meta-harness, all writing cards that `../contracts/validate.py` judges. `CLAUDE.md` here is what a session seated as this agent follows.

**Nothing runs yet (M0).** This folder holds the skeleton the plan names (`../plan.md` 7):

| Path | What | When it fills |
|---|---|---|
| `tasks/` | the task queue; `001` onboards the fixture lab, `002` builds the echo agent on mock | M1 |
| `failures.jsonl` | one failure per line, append only | from the first run |
| `envelope/observed.json` | read-only paths of built agents the harness may observe | M5 |
| `inbox/materials/` | where the person drops links and files; `README.md` there explains | any time; intake code in M2 |
| `inbox/<thread>/` | observations from the person or the bridge | M8 |
| `profiles/<lab_id>/` | discovery report, onboarding record, lab profile revisions | M1 |
| `requests/<rid>/` | one request, flat: goal, tool profile, brief, sheet, axes, synthesis, spec, build, validation report | M1 |
| `knowledge/`, `cases/`, `harness/`, `templates/`, `builds/`, `eval/`, `src/`, `tests/` | as the plan's layout | M2–M5 |

The accepted example set under `../contracts/examples/` is laid out the way this folder will be, so the shape can be read before the code exists.
