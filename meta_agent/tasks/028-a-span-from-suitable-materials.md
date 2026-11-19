# 028 — A tolerance from the span of suitable materials

**Status:** open. Opened by `design-macbook-20261117-1` on 2026-11-19 from the person's standing rule for tolerances, branch 3, as amended (`../../docs/ideas/20261118.md`, "Tolerances from the span of comparable published values"; `../../docs/ideas/20261119.md`, "What the literature-span skill is for, and what it may draw on"). Nobody holds it. It takes over what the design role asked of the meta role in `../inbox/seats/20261118-design-macbook-20261117-1-16.json`, which no meta seat took up.

**What the person said it is for:** a skill that can check the cases a person passed by judgement, by working out an error range from suitable materials. Those cases are CFD round four's maximal drag and its two peak times (run `cfd/20261118-7`) and the GROMACS water count (run `molecular-dynamics/20261118-1`). For the water count, the person said a paper on a similar solvation will do: the solute need not be a protein, the solvent need not be water, and the engine need not be GROMACS.

**Seat:** the design part has landed: the rule in the root `CLAUDE.md`, `plan.md` item 15, `validate-and-record`, and the interval form of `validation_report` (`interval {low, high}`, `chosen_by: rule`, `from: literature_span`). The skill, the error-range skill's next version and the template are a meta seat's.

**Goal:** a library skill, run through the runner, takes the values or stated error ranges of a quantity from material cards and gives the interval [lowest, highest]. Each card says its source, and `classify-knowledge` has written how the source's system, quantity and engine compare with the task's. With fewer than two values, or one stated range, the skill says what it has and yields nothing where the rule yields nothing. `validate_tasks` takes the branches in the rule's order. The Designer looks for such materials first, through `research-materials`.

**Done when:**
- the skill passes check 22 with worked cases on two unrelated kinds, one of them not rheology (the CFD drag coefficient and the GROMACS water count are two such kinds);
- the template that carries it says which branch each tolerance came from;
- a test shows a built bundle deriving a span from cards it was not handed;
- `python contracts/validate.py` prints `VERDICT PASS`.

**Must not:** recall a value from memory; take a value from a source without a material card; choose which materials are suitable on the model's word alone, without writing how each compares; widen the interval by any statistic or multiplier; overturn a pass the person gave by judgement.
