# 023 — Data hosts a built agent may fetch from

**Status:** open. Opened by `design-macbook-20261117-2` on the person's words (`../../docs/ideas/20261117.md`, "Design work from the Quantum ESPRESSO test": "여기서 진행", "Every agent of this lab"), from `dft-7` in `../failures.jsonl` (task `018`, run `dft/20261117-3`). The design part landed on 2026-11-17 by `design-macbook-20261117-2` (claim `claims/023-design-macbook-20261117-2.json`), see below; the meta part is open.

**Goal:** a person can allow a built agent to read data from named hosts, read-only and anonymously, as a value the gate reads and no sentence; and a bundle's tool that does so opens by the lab's execution permission only where every host it names is allowed. Today the template's gate and check B9 open a network tool only as an install from a listed package source, so the hosts the person allowed for the Quantum ESPRESSO agent (gitlab.com for the examples, pseudopotentials.quantum-espresso.org for the pseudopotentials) reach no bundle.

**Design part (design role):**
- `contracts/schemas/lab_profile.schema.json` and `contracts/schemas/execution_permission.schema.json`: `data_sources`, a list of `{host, access}` beside `package_sources`, `access` being `read_only_anonymous` alone; a host is a bare lower-case host name, matched by equality, with no scheme, path or wildcard.
- `contracts/schemas/tool_contract.schema.json`: `fetches_from`, the list of `{host, access}` a tool reads data from.
- Check B9: a tool that reaches the network and opens by the execution permission names `installs_from`, `fetches_from` or both, and each names only what the bundle's permission lists (a pair under `package_sources`, every host under `data_sources` with the same access); a tool naming neither is refused as before. Rejected fixtures of two unrelated kinds, and the contract tests of B9 extended.

**Meta part (meta role), after the design part:**
- The lab profile `lab-kyu-softmatter`: its next revision carries the two hosts under `policy.execution_permission.data_sources`, on the person's words, and nothing wider.
- The Designer copies `data_sources` from the profile into a bundle's permission as it copies `package_sources`.
- A template version whose `src/gate.py` opens a tool with `fetches_from` by the same rule as B9, shown on fixtures of two unrelated kinds.

**Open, not designed here:** a bundle carrying a material's files verbatim (the person allowed it for the examples on 2026-11-17). The clone's proposal, read from run `dft/20261117-3`: the intake names files of a material whose card says `may_quote: true`, the Designer copies them into the bundle beside the licence notice, and a bundle check refuses a carried file that does not come unchanged from such a material. It is a design part of its own, after this one.

**Done when:** the design part has landed with its fixtures watched failing and the gate passing in both modes; the meta part has landed a profile revision, the Designer's copy and a template version; and a fresh clone given `../eval/briefs/clone-quantum-espresso.txt` builds an agent whose fetch tools open, read from a run.

**Must not:** add a host the person did not name; let `data_sources` open an install or `package_sources` open a fetch; open a network tool by anything but the lab's confirmed permission; change a build.

**What the design part landed (`356c09a`):** `data_sources` in the two permission schemas and `fetches_from` in the tool contract schema, as above; check B9 judging an install and a fetch each against its own list; two rejected fixtures, an engine's example inputs and pseudopotentials from a host not listed and a weather station's archive where only a package source is listed; the contract test of B9 extended with both kinds, allowed and refused. Watched: before the change the allowed fetch was refused and both fixtures failed checks 1 and B7 as well; with the host comparison taken out of a scratch copy of the validator, both fixtures were accepted and the test failed. plan.md 8 (B9) says the same. The meta part is asked of the meta role by note.
