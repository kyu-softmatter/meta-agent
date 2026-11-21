# 031 — The bridge: two built agents hand cards to each other unchanged

**Status:** open. Opened by `design-macbook-20261120-1` on the person's words of 2026-11-20 (`../../docs/ideas/20261120.md`): "둘로하고 각각 소통을 할 수 있게" (two agents, each able to communicate with the other) and, asked how a hand-over should travel, "Design a bridge now". It answers the failure lines `dftmd-2` and `dftmd-9` in `../failures.jsonl`, and `dftmd-1` where a received value is converted.

**Seat:** the design part (the cards, the units, the check, the fixtures, the plan) is the design role's and lands first. The meta part, building two bundles that use it, is a `meta-…` seat's once `design_part` is `landed` in `index.json`. A record that falls in the design role's paths goes to that role as a note.

**Goal:** two built agents hand values to each other through cards that no one changes on the way: one bundle writes a hand-over card in its own folder, a bridge carries it, byte for byte, into the other bundle's `inbox/<thread>/` (reserved by plan.md 10), and the receiving bundle uses it only as its build declared and only after its unit converts through the registry; everything else it holds. The first case is a Quantum ESPRESSO bundle that fits the H2 bond's force constant and rest length and a HOOMD-blue bundle that uses them.

**What stays as it is:** the Meta-Agent never integrates engines (plan.md 10). The bridge authors nothing, judges no science, runs no engine, and changes no card; it is not an agent. A bundle stands alone (MP2): without the bridge it runs, and a value that has not arrived is an input nothing in the bundle gives.

**Inputs:** plan.md 3 (MP2, MP10, MP11), 6, 8, 10 and M8; §14-33(n), which already says that what one bundle needs of the other "arrives as a card over the bridge (M8) and is held by `objective` as a requirement"; `../../docs/reference/sma_read_20261108.md` 6, SMA's bridge (an envelope that carries a card "without changing a character", `author: bridge`, empty `numbers[]`, delivery into `<agent>/inbox/<thread>/`, `undeclared` becomes a hold); `../failures.jsonl` `dftmd-1` to `dftmd-9`.

**Done when (read off a run):** the design part below has landed, each new check with its rejected fixture in the same commit, watched failing first; `python contracts/validate.py` passes and `--expect-fail` rejects both totals in full; the accepted fixtures stand for two unrelated kinds, DFT→MD and the second kind the person names, one of them not rheology; every choice between designs, policy or permission in it was put to the person and the answer is in `../../docs/ideas/20261120.md`; `index.json` says `design_part: landed`.

**Must not:** build either bundle; run either engine; let the bridge change, merge, convert or author a card; let a receiving bundle use a value its build did not declare; infer a policy, a permission or an engine's unit scale; push.

## Design (proposed by `design-macbook-20261120-1`, 2026-11-20; the choices marked "put to the person" wait for their word)

### Three cards

1. **`handover`**, written by the producing bundle in its own `outbox/`: the values it hands over (each a number of plan.md 6.3, its grade derived, never E6), each with the `conditions` it holds under (for a DFT fit: functional, pseudopotential, cut-offs, the points fitted), `from` and `to` (the two agents, by build), `thread`, `produced_by` (the library skill and the run record it was read off), and `degraded` as SMA carries it. A value handed over is in a registered unit that has an `si_factor`: an engine's own unit (`engine_length`, …) means nothing outside its engine.
2. **`bridge_envelope`**, written by the bridge alone (`author: bridge`) beside the copy of the card in the receiver's `inbox/<thread>/`: `thread`, `round`, `from`, `to`, the payload's file name and `sha256`, `trigger`, who released it, `degraded` copied from the payload, and `numbers: []`. Its presence is the turn, as in SMA.
3. **`handover_receipt`**, written by the receiving bundle in its own `received/`: which hand-over (id and the envelope's hash), which value, the row it fills, the conversion (from unit, to unit, the factor), and its state, `used` or `held` with a reason. `used` needs the row to be one the receiving build declared as taking a hand-over (`declared_in`); anything undeclared is `held` (MP10).

### Units and the conversion (dftmd-1)

A received value is converted only through `contracts/units.json`: the factor is `si_factor(from) / si_factor(to)` when the two units have the same dimension, and nothing else. Into an engine's own unit, the receiving bundle needs the scale of that unit (for HOOMD-blue: which registered unit `engine_length`, `engine_energy` and `engine_mass` stand for) declared as a setting, `confirmed` by the person (MP11: only a person confirms); an inferred scale is a recommendation and the value is `held`. The units the first case needs are added with their sources: `Angstrom`, `bohr`, `1/cm`, `Ry/bohr`, `Ry/bohr^2`, `eV/Angstrom`, `eV/Angstrom^2`, a factor that is not exact read from CODATA 2022 and cited in its note, and a composite one recomputed from its parts by a test. The gate reads the registry through `contracts/tools/units.py`; in a bundle the conversion is a library skill that reads the registry the bundle carries (the meta part).

### Check 25 (hand-overs and the bridge)

Proposed: an envelope stands in a folder `inbox/<thread>/` named by its `thread`, its payload beside it with the hash it states (unchanged); the payload is a `handover` whose `thread`, `from`, `to` and `degraded` are the envelope's; every value handed over has conditions and a unit with an `si_factor`; a receipt's factor is the registry's, between units of one dimension; a `used` receipt names its declaration and, into an engine's unit, a scale confirmed by the person; a `used` receipt names an envelope that is there. Each part lands with a rejected fixture under `contracts/examples/rejected/check25_…`.

### Put to the person

- where the bridge runs and who starts it;
- when a card crosses (SMA: a result crosses only on the person's word);
- whether a receiving bundle uses a declared value without asking, or holds every received value until the person opens it;
- the second kind of fixture, not DFT→MD.
