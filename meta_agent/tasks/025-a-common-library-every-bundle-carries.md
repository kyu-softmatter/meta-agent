# 025 — A common library every simulation bundle carries, and an error-range skill

**Status:** open. Opened by `design-macbook-20261117-1` on 2026-11-18 on the person's words, relayed by the status-report session and recorded in `../../docs/ideas/20261118.md` ("An error-range skill, and a common library every bundle carries"). Nobody holds it.

**Seat:** the design part is the record of what a bundle carries and how an adaptation is recorded: the build card's difference, a check if one is needed, and `specify-and-build`'s line on it. It lands first. The meta part is the skills themselves, the template that ships them, and the Designer that adapts them. It is one meta seat's, and it takes in the ask `../inbox/seats/20261118-design-macbook-20261117-1-5.json` (the tolerance skill and template v19), which `meta-macbook-20261117-2` holds.

**Goal:** every simulation bundle is built with a common set of library skills that this repository makes and tests in advance, the error-range skill among them, and a build adapts one to its engine as a next version that its build card shows.

**Inputs:** the failure lines of the tests of 2026-11-17 and 2026-11-18 (`../failures.jsonl`: the skills used or missed across HOOMD-blue, Cantera, Meep, FEniCSx, Quantum ESPRESSO and GROMACS); the skills already in `../skills/`; `../../contracts/skill_kinds.json`; the standing rule for tolerances (`../../docs/ideas/20261118.md`).

**Candidates (the status-report session's list, not chosen):** a difference from a reference; agreement of a pair within a tolerance; a mean consistent with a reference; the standard error of independent estimates; a series' maximum, settling and window; a power-law exponent along a sweep; a diffusive regime from a mean squared displacement; a value outside its data's validity range (missed three times in the Cantera tests); and the error-range skill.

**Method (recommended, not settled):** a skill's manifest says it is common (a field the design part adds, read by check 22). The template carries the common skills into every simulation bundle. An adaptation is `<name>@v<N+1>` inside the bundle, made by the builder and listed in the build card's difference from the template. A common skill counts only when it runs on fixtures of two unrelated kinds, one of them not rheology.

**Waits for the person:** how the error-range skill treats a reference printed with many digits (the person took none of the three floors offered).

**Done when:** the design part's field, line and any check are landed with a rejected fixture watched failing first. The meta part's common skills, error-range skill among them, run through the runner on two unrelated kinds. A bundle built after it carries them, and one adaptation shows in a build card. `python contracts/validate.py` prints `VERDICT PASS`.

**Must not:** edit a landed skill; decide a tolerance or a floor the person has not chosen; ship a skill that has not run on two unrelated kinds.
