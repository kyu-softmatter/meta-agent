# 025 — A common library every simulation bundle carries, and an error-range skill

**Status:** open; the design part landed on 2026-11-18 by `design-macbook-20261117-1` (claim `claims/025-design-macbook-20261117-1.json`; see "What the design part landed"). The meta part is open. Opened by `design-macbook-20261117-1` on 2026-11-18 on the person's words, relayed by the status-report session and recorded in `../../docs/ideas/20261118.md` ("An error-range skill, and a common library every bundle carries"). Nobody holds it.

**Seat:** the design part is the record of what a bundle carries and how an adaptation is recorded: the build card's difference, a check if one is needed, and `specify-and-build`'s line on it. It lands first. The meta part is the skills themselves, the template that ships them, and the Designer that adapts them. It is one meta seat's, and it takes in the ask `../inbox/seats/20261118-design-macbook-20261117-1-5.json` (the tolerance skill and template v19), which `meta-macbook-20261117-2` holds.

**Goal:** every simulation bundle is built with a common set of library skills that this repository makes and tests in advance, the error-range skill among them, and a build adapts one to its engine as a next version that its build card shows.

**Inputs:** the failure lines of the tests of 2026-11-17 and 2026-11-18 (`../failures.jsonl`: the skills used or missed across HOOMD-blue, Cantera, Meep, FEniCSx, Quantum ESPRESSO and GROMACS); the skills already in `../skills/`; `../../contracts/skill_kinds.json`; the standing rule for tolerances (`../../docs/ideas/20261118.md`).

**Candidates (the status-report session's list, not chosen):** a difference from a reference; agreement of a pair within a tolerance; a mean consistent with a reference; the standard error of independent estimates; a series' maximum, settling and window; a power-law exponent along a sweep; a diffusive regime from a mean squared displacement; a value outside its data's validity range (missed three times in the Cantera tests); and the error-range skill.

**Method (recommended, not settled):** a skill's manifest says it is common (a field the design part adds, read by check 22). The template carries the common skills into every simulation bundle. An adaptation is `<name>@v<N+1>` inside the bundle, made by the builder and listed in the build card's difference from the template. A common skill counts only when it runs on fixtures of two unrelated kinds, one of them not rheology.

**Waits for the person:** how the error-range skill treats a reference printed with many digits (the person took none of the three floors offered).

**Done when:** the design part's field, line and any check are landed with a rejected fixture watched failing first. The meta part's common skills, error-range skill among them, run through the runner on two unrelated kinds. A bundle built after it carries them, and one adaptation shows in a build card. `python contracts/validate.py` prints `VERDICT PASS`.

**Must not:** edit a landed skill; decide a tolerance or a floor the person has not chosen; ship a skill that has not run on two unrelated kinds.

**What the design part landed (2026-11-18, `design-macbook-20261117-1`):**
- `../../contracts/schemas/skill.schema.json`: a skill's manifest may say `common: true`, or `adapted_from: <name>@v<N>` for a next version a build made for an engine.
- Check 22 (`../../contracts/tools/skills.py`, `common_problems`): a common skill names no engine, instrument or parameter under `applies_to`, and its worked cases each name their `system`, at least two unrelated kinds. A skill adapted from a common one is not common and names its engine. The rejected fixture `../../contracts/examples/rejected/check22_common_skill_shown_on_one_kind` was watched being accepted once the schema knew the field, then refused by the rule. Unit tests on two unrelated kinds are in `../../contracts/tests/test_skills.py`.
- `build-library-skill` and `specify-and-build` say how a common skill is made, how a simulation bundle carries every common skill, and how a build adapts one as a next version that the build card lists.
- Not landed, and left to the meta part: which skills are common, the template that ships them, and the Designer's adaptation. The CFD seat's `tolerance_from_reference@v1` (template v19, `d538fba`) is a candidate for the error-range skill, as it stands or as a next version with `common: true`. A bundle check that a simulation bundle carries every common skill waits until a template ships them, so that it can name the template version it applies from.

**What the meta part landed so far (2026-11-18, `meta-macbook-20261117-2`, claim `claims/025-meta-macbook-20261117-2.json`):**
- The common set, seven next versions with `common: true`, their cases each naming a system, at least two unrelated kinds each: `measurement_error@v2` (the agreement), `tolerance_from_reference@v2` (the error-range skill, the rule as amended: the stated uncertainty, else the larger of half the last printed digit and the run's own numerical error, saying when that error was not estimated), `series_maximum@v2`, `series_settled@v3`, `series_within_window@v3`, `standard_error_of_independent_estimates@v2`, `power_law_exponent_along_sweep@v3` (also the order of convergence along a refinement). Not taken: `diffusive_regime_from_msd` (particles alone); the validity-range candidate, which has no skill and no source read yet.
- Template v20 names the set in `TEMPLATE.json` (`common_skills`); its `src/validate_tasks.py` reads the agreement skill's name there. The builder (`../src/build/bundle.py`) puts the set into every bundle whose tool is an engine, keeps a version the specification names, and takes a build's adaptation from `requests/<rid>/adapted/<id>@v<N>/` in the common one's place, refusing one that names no engine, is not later, adapts from outside the set, is itself common, or adapts the agreement skill; the difference from the template lists each adaptation. The Designer passes the tool's kind and that folder.
- Shown in `../tests/test_template_v20.py` on two kinds; an instrument's bundle carries no common set.
- Open: a skill that estimates a run's numerical error from two resolutions; a build a session makes carrying the set, with an adaptation in its build card; the bundle check (the design role's) now that v20 ships the set.

