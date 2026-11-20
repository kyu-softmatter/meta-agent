# 026 — What an interface call shows in the builder's tree, where the engine's environment is not made

**Status:** open. Opened by `design-macbook-20261117-1` on 2026-11-18 from three failures on two unrelated kinds, under the person's word that this seat takes the design role's asks from the test sessions (`../../docs/ideas/20261117.md`). Nobody holds it.

**What was seen:**
- `ctrl-pair-4` (Cantera, run `chemical-kinetics/20261117-12`): B7 makes every interface call that expects an error in the builder's tree. An interface task that expected Cantera's own `execution_failure` passed in the Designer's isolated copy and failed under B7, where the call returned `unavailable`. The clone took the task out.
- `cfd-3` (FEniCSx, run `cfd/20261117-1`): an interface task that calls the bundle's install tool made the engine's environment inside the builder's tree and ran past the gate's time limit.
- `cfd-20` (FEniCSx, run `cfd/20261118-2`): a task expecting an error that its adapter raises after it checks the environment got the environment's error instead. The clone changed its contract so that the runner refuses the input first.
- `rheotool-33` (rheoTool, run `rheology/20261119-1`, added 2026-11-19 from the note `../inbox/seats/20261119-meta-macbook-20261118-1-2.json`): for a tool that starts an engine already on the computer and opens by the execution permission, an error item whose error shows only after the engine has run made B7 start the engine inside the clone's repository at every gate run, and so at every commit's hook, and left run folders under the build's bundle. The clone discarded that build before committing.

**Seat:** B7 and the rule for what the gate's fixture calls may do are the design seat's, and land first. The builder's S6 copy, the template's tasks and the Designer's choice of interface tasks are a meta seat's.

**Goal:** an interface task says what it shows, and the gate makes in the builder's tree only the calls that the tree can show. These are the runner's refusals before an adapter runs, and calls that need no engine environment. A call that needs the engine's environment, or that installs it, is shown in the isolated copy where that environment is made, and the tree's gate reads its verdict there rather than calling it again.

**Method (recommended, not settled):** a fixture call names what it needs (`needs: environment`, or the install's own mark `installs_from`). B7 makes in the tree only the calls that need nothing. It reads the verdict of the others from the S6 copy's record, where one exists, and otherwise reports them as `not_run`, never as a pass or a fail. Fixtures of two unrelated kinds.

**Done when:** the rule is in B7 and in `design-tool-interface`, each new rule landed with a rejected fixture watched being accepted first; the meta part has the Designer and the S6 copy mark and record such calls; `python contracts/validate.py` prints `VERDICT PASS`.

**Must not:** let B7 make the engine's environment in the builder's tree, or start an engine there; count a call that was not made as a pass.

**Waits for the person (2026-11-19):** whether this task is started. This seat asked on 2026-11-18 and the person has not answered. The fourth case above makes it heavier: until the rule lands, a gate run in a clone may start an engine that is already installed.
