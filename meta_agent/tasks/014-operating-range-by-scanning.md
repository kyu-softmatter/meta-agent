# 014 — The operable range of an instrument, read by the built agent as it scans

**Status:** open, 2026-11-09. Opened by `design-macbook-20261109-1` on the person's words (`../../docs/ideas/20261109.md`: "장비를 스캔하면서 최대동작 가능한 범위는 스스로 파악해"), recorded in plan.md 14-36. Nothing exists yet. Order: after `010` (the skill layout, the hardware kinds on a mock, the gated tool path); `011` and `013` use what it writes where it exists.

**Seat:** the `operating_range` contract, the kind `hardware_range` (unless `010`'s design part has already added it), bundle check B14 and their fixtures are the design seat's and land first. The skill, the mock transcript and the tests are a `meta-…` seat's.

**Goal:** a built agent, at the place where the instrument is, reads what the instrument reports about its own ranges and modes and writes them down with their evidence, so that the configurations, the hard limits of `measurement` and the gate's limit check rest on this instrument and not only on a specification. The Meta-Agent builds the skill and proves it on a mock; it reaches no instrument.

**What is settled (the person, 2026-11-09):** while scanning the instrument the agent finds its maximum operable range by itself. Standing: the Meta-Agent never operates (MP1); safety values are the person's and are never generated (MP4); a claim is observed, derived, inferred or unknown, and an unknown says what would resolve it (MP9).

**Inputs:**
- `../../plan.md` 3 (MP1, MP4, MP9, MP10), 5.1 S2 and S5, 6.3, 14-12, 14-31, 14-32, 14-34, 14-36; `../../docs/ideas/20261109.md`.
- `010`: `skill.schema.json`, the runner, `hardware_connection/find_and_identify@v1`, the mock transcript; `../src/build/template_v1/src/{gate.py,run_tool.py}`.

**Method (recommended, not settled):**
- Design seat, the card: `operating_range`, a contract of the bundle beside `tool_contract`. Fields beside the common ones: `device {id, model, firmware}`; `items[]`, each `{quantity, min, max, unit, claim: observed | unknown, evidence {tool, query, response, read_at}, requires}`; `axes[]`, each `{name, options[], evidence}` for the discrete modes the device lists; `scanned_at`; `supersedes`. A bundle ships none: it is written at the destination.
- Design seat, B14: a bundle carries the contract and no `operating_range` card; in a fixture card every `observed` item has evidence naming a tool of the bundle whose contract says `side_effects: read`, every `unknown` item has `requires` and no value, no item is authored by anything but the scan (no `assumed:`, no `model_generated`), and `envelope/safety.json` is unchanged by a scan. Rejected fixtures, one per assertion.
- Meta seat, the skill `hardware_range/read_operating_range@v1`, `side_effect: read_device`: after `find_and_identify`, it asks the device and its control software, through `run_tool.py`, what they report about themselves (travel, speed, torque, temperature, sensor size, frame rates, the modes of each axis) and returns the items. It sets nothing and moves nothing. A quantity the device does not report is returned `unknown` with `requires` naming the vendor's specification or the person. It never looks for a limit by driving the instrument until it stops.
- Meta seat, what uses it, each where the card exists: `011`'s configuration axes and `capability` skills take their options and ceilings from `axes[]` and `items[]`; `012`'s `measurement` holds them as hard limits; `013`'s gate refuses a call outside an `observed` item. A difference between an item and the `spec:` value the bundle was built with is written as an `observation` for the Meta-Agent.
- Tests: on the mock transcript the skill returns the fixture's ranges with the queries as evidence; a quantity the transcript does not answer comes back `unknown` with `requires`; the skill's source makes no call to a tool whose contract writes; a second scan after the transcript's firmware changes writes a new revision and keeps the old; the gate refuses a call outside an `observed` item and passes the same call when the item is `unknown` only if nothing else refuses it, the record saying the range was unknown.

**Done when (read off a run):**
- `python contracts/validate.py --expect-fail` rejects every fixture under `checkB14_*`; `python contracts/validate.py` prints `0 failed`.
- `python -m meta_agent.src.skills run hardware_range/read_operating_range@v1` on the mock writes an `operating_range` card whose every `observed` item names its query and response.
- `PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .` is OK.

**Must not:** run the skill against a real device or open a path to one from this repository (MP1); find a limit by moving, heating or loading the instrument; write, fill or tighten a safety value from a scan, or let a scanned range stand in for one; fill an item the device does not report; edit `tasks/010` or its skills (held by another seat); let a model write a number.

**Report:** ten lines or fewer — the items and axes the mock scan returned, the unknown ones and what each requires, the fixture count of B14, what the gate did with a call outside a scanned item, the verdict line, the test count.
