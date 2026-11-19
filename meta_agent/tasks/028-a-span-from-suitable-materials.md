# 028 — A tolerance from the span of suitable materials

**Status:** open. Opened by `design-macbook-20261117-1` on 2026-11-19 from the person's standing rule for tolerances, branch 3, as amended (`../../docs/ideas/20261118.md`, "Tolerances from the span of comparable published values"; `../../docs/ideas/20261119.md`, "What the literature-span skill is for, and what it may draw on"). Held by `meta-macbook-20261119-1` (claim `affd098`); its meta part landed on 2026-11-19 except the outside test (see "The meta part" below). It takes over what the design role asked of the meta role in `../inbox/seats/20261118-design-macbook-20261117-1-16.json`, which no meta seat took up.

**What the person said it is for:** a skill that can check the cases a person passed by judgement, by working out an error range from suitable materials. Those cases are CFD round four's maximal drag and its two peak times (run `cfd/20261118-7`) and the GROMACS water count (run `molecular-dynamics/20261118-1`). For the water count, the person said a paper on a similar solvation will do: the solute need not be a protein, the solvent need not be water, and the engine need not be GROMACS.

**Seat:** the design part has landed: the rule in the root `CLAUDE.md`, `plan.md` item 15, `validate-and-record`, and the interval form of `validation_report` (`interval {low, high}`, `chosen_by: rule`, `from: literature_span`). The skill, the error-range skill's next version and the template are a meta seat's.

**Goal:** a library skill, run through the runner, takes the values or stated error ranges of a quantity from material cards and gives the interval [lowest, highest]. Each card says its source, and `classify-knowledge` has written how the source's system, quantity and engine compare with the task's. With fewer than two values, or one stated range, the skill says what it has and yields nothing where the rule yields nothing. `validate_tasks` takes the branches in the rule's order. The Designer looks for such materials first, through `research-materials`.

**Done when:**
- the skill passes check 22 with worked cases on two unrelated kinds, one of them not rheology (the CFD drag coefficient and the GROMACS water count are two such kinds);
- the template that carries it says which branch each tolerance came from;
- a test shows a built bundle deriving a span from cards it was not handed;
- `python contracts/validate.py` prints `VERDICT PASS`.

**Must not:** shape the skill, the template or the search around the drag coefficient or solvation, which are worked cases only: the skill serves any quantity of any engine or instrument (the person, 2026-11-19, "반드시 항력계수, 솔베이션에만 해당하는게 아닌건 알지?"); recall a value from memory; take a value from a source without a material card; choose which materials are suitable on the model's word alone, without writing how each compares; widen the interval by any statistic or multiplier; overturn a pass the person gave by judgement.

## The meta part (2026-11-19, `meta-macbook-20261119-1`, `claude-fable-5-2` at `high`)

**Landed:**
- `d6bca5a`: four source records under `../inbox/materials/`, each saying what it gives and how its system, quantity and engine compare with the task's. They are `RETRIEVED.json` files in the `queued` state and not `MATERIAL.json` cards, because check 17 still fails a material a seat added.
- `081a3ae`: `../skills/data_analysis/literature_span@v1` and `../skills/data_analysis/tolerance_from_reference@v5`. Check 22 has nothing to say of either.
- `8d2d786`: `../src/build/template_v28`, the builder (`../src/build/bundle.py`) and `../tests/test_template_v28.py` on two unrelated kinds, a flow coefficient and a spectral peak.

**How it works:** a scientific task carries its materials under `measure.materials`, a map from the stated field to a list of entries. An entry names its material, says in `compares` how that material's system, quantity and engine compare with the task's, and gives either `value` or `low` and `high`. The span skill gives [lowest, highest] and which material gave each edge. The rule's skill takes the span after a stated uncertainty and before the printed digit and the run's error. The task is then judged by the interval, `chosen_by: rule`, `from: literature_span`, `derived_by` the span's skill. The builder derives it for a task that names no refinement; a bundle derives it when its check runs for a task that does, and makes no finer run. An entry that names no material or does not say how it compares is refused by the builder and gives no span in the skill.

**What the sources give:**
- *The maximal drag coefficient of the DFG 2D-3 case:* Schäfer and Turek 1996 state an interval (their Table 5, read in a copy that needs no login); V. John 2004 gives a reference value (his equation 8); the FeatFlow page gives its level-6 value. The span is the 1996 interval, and both values lie inside it. This is the skill's first worked case.
- *The time of that maximum:* two values, John's and the FeatFlow page's, each a multiple of its own time step. Their span is the second worked case.
- *The water count of the lysozyme solvation:* one value, the tutorial's own. Nothing was found that gives a second published value of this count for this set-up, or a range for how far a solvation's count may differ. Looked in: the tutorial's page and its article (LiveCoMS), the `gmx solvate` help, the Solv-eze preprint, and searches for comparisons of water counts between solvation tools, between computers and versions, and between independently prepared replicas. The tutorial says the count may differ very slightly between computers and gives no number. With one value and no stated range the skill gives nothing, which is its fourth worked case. The person's "차이만 보고, 판정 없음" stands.
- *A third kind,* the viscosity of liquid water at 25 °C from two reference works already in the inbox, shows the skill on a measured property.

**Not done:** the test of a built bundle deriving a span from cards it was not handed. It needs a run, and a run waits for the hub's word while GROMACS production holds the computer.

**Open, and whose:**
- *Settled on 2026-11-19 ("Widen by uncertainty"):* whether a value a source gives with an uncertainty enters as a range. See "A stated uncertainty widens the span" below.
- Which of a source's numbers is its value for the quantity (its own result, or every row of its refinement study) is the reader's to say in `compares`. The worked cases take a source's own result only. What makes a material suitable is the person's.
- Two values printed to their sources' time steps give a span that says nothing of either's resolution (the second worked case). Whether such a span should judge is the person's.
- *Landed by the design role (`9c510b2`):* the session skills name `measure.materials`.
- A span these cases show judges no build. The passes the person gave by judgement stay as they are.

## Material cards (2026-11-19)

Check 17 now takes a card a seat adds by its own search (`c84bd5e`). The four sources of the worked cases are `MATERIAL.json` cards beside their reading records (`0e90631`), and the LiveCoMS article is a fifth (`19ff527`). All are `queued`; registering and quoting stay the person's.

## A stated uncertainty widens the span (2026-11-19, `meta-macbook-20261119-1`)

The person answered "Widen by uncertainty" (`../../docs/ideas/20261119.md`, "A source's stated uncertainty widens the span"), and the design role asked for the next versions (`../inbox/seats/20261119-design-macbook-20261117-1-4.json`).

**Landed:**
- `1b5fe06`: `../skills/data_analysis/literature_span@v2`. An entry that gives one value may carry `uncertainty`, the uncertainty its material states for that value. It then enters as the range from the value less that uncertainty to the value plus it, with no multiplier, and counts as one stated range, so one such entry gives a span by itself. Every case of v1 gives the same. Check 22 has nothing to say.
- `0790309`: `../src/build/template_v29`, which names the v2 skill, and the builder, which refuses an uncertainty below zero, one beside a range, and any under a template earlier than v29. `../tests/test_template_v29.py` runs on two unrelated kinds.

**New worked cases, on two unrelated kinds read from materials:**
- V. John's reference value of the maximal drag coefficient with the bound his paper states for it. With the 1996 interval and the FeatFlow value the span is still the 1996 interval; alone, the value with its bound is a span by itself.
- The hydration free energy of ethanol in the LiveCoMS article of GROMACS tutorials: the article's own result with the error its analysis prints, and two values it quotes from other papers, one with an uncertainty. The quoted values were not followed to those papers, and each entry says so.

**Still open:** the outside test; which of a source's numbers is its value for the quantity; whether a span of two values known no finer than their sources' time steps should judge. An uncertainty a source states relative to the value, or in another unit, is not converted by the skill: the reader brings it to the quantity's unit through a skill first.
