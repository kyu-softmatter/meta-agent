# Onboarding proposal: lab-fixture-rich

What Step zero read, what it inferred, what it could not, and what it asks. Inferred values are recommendations with evidence; only a person's answer makes a value `confirmed`.

## Inputs read

- folder: `D:/codes/github/meta-agent/meta_agent/tests/fixtures/labs/rich`
- material: `https://hoomd-blue.readthedocs.io/`

## Inferred (recommendations)

- `existing_code` = `D:/codes/github/meta-agent/meta_agent/tests/fixtures/labs/rich` - from scripts/run_hoomd.py
- `collaboration.first_agent` = `False` - from contracts/seats.json
- `collaboration.existing_agents` = `microscope_agent, simulation_agent` - from contracts/seats.json
- `collaboration.bridge` = `True` - from bridge/
- `conventions.research_kind` = `simulation, experiment` - from microscope_agent/, pixi.toml
- `conventions.methods` = `md, bd_cg` - from pixi.toml, scripts/run_hoomd.py
- `preferred_engines` = `hoomd_blue` - from inbox/materials/LINKS.md, pixi.toml, scripts/run_hoomd.py
- `preferred_instruments` = `sma_microscope` - from microscope_agent/
- `software_env.language` = `python` - from pyproject.toml
- `software_env.os` = `windows, macos, linux` - from pixi.toml, scripts/submit.slurm
- `software_env.package_manager` = `pixi` - from pixi.toml
- `hardware.gpu` = `True` - from scripts/run_hoomd.py, scripts/submit.slurm
- `hardware.hpc` = `slurm` - from scripts/submit.slurm
- `existing_data` = `rich:data/` - from data/
- `validated_workflows` = `rich:replay/` - from replay/
- `operational_constraints.licenses` = `MIT (rich)` - from LICENSE
- `conventions.unit_system` = `SI, kelvin only` - from contracts/units.json
- `gui_preference` = `parameter_form` - from pixi.toml - a recommendation from the research kind and methods, not a reading of a preference; a visual editor or reuse of the lab's own GUI are the alternatives

## Asked (unknown, or policy)

- `collaboration.mode` (collaboration, policy): Should the new agent be configured to collaborate with existing agents (a bridge plan), work alone, or decide later?
- `policy.working_mode` (operating policy, policy): How does the lab want to work with the Meta-Agent: card by card with review, or in batches?
- `policy.approval_mode` (operating policy, policy): Which actions need a person's approval before they run?
- `policy.publication_scope` (operating policy, policy): Who may see the agents and their results: this lab, collaborators, or the public?
- `policy.execution_permission` (operating policy, policy): May a built agent run anything on its own, and if so what: mock, sandbox, an engine, an instrument?
- `policy.external_transfer_of_private_code` (operating policy, policy): May private code leave the lab's computers, for example to an analysis service?

## Skipped, with the reason

- `existing_code` (inferred): inferred from scripts/run_hoomd.py; shown as a recommendation in Step 2
- `collaboration.first_agent` (inferred): inferred from contracts/seats.json; shown as a recommendation in Step 2
- `collaboration.existing_agents` (inferred): inferred from contracts/seats.json; shown as a recommendation in Step 2
- `collaboration.bridge` (inferred): inferred from bridge/; shown as a recommendation in Step 2
- `conventions.research_kind` (inferred): inferred from microscope_agent/, pixi.toml; shown as a recommendation in Step 2
- `conventions.methods` (inferred): inferred from pixi.toml, scripts/run_hoomd.py; shown as a recommendation in Step 2
- `preferred_engines` (inferred): inferred from inbox/materials/LINKS.md, pixi.toml, scripts/run_hoomd.py; shown as a recommendation in Step 2
- `preferred_instruments` (inferred): inferred from microscope_agent/; shown as a recommendation in Step 2
- `software_env.language` (inferred): inferred from pyproject.toml; shown as a recommendation in Step 2
- `software_env.os` (inferred): inferred from pixi.toml, scripts/submit.slurm; shown as a recommendation in Step 2
- `software_env.package_manager` (inferred): inferred from pixi.toml; shown as a recommendation in Step 2
- `hardware.gpu` (inferred): inferred from scripts/run_hoomd.py, scripts/submit.slurm; shown as a recommendation in Step 2
- `hardware.hpc` (inferred): inferred from scripts/submit.slurm; shown as a recommendation in Step 2
- `existing_data` (inferred): inferred from data/; shown as a recommendation in Step 2
- `validated_workflows` (inferred): inferred from replay/; shown as a recommendation in Step 2
- `operational_constraints.licenses` (inferred): inferred from LICENSE; shown as a recommendation in Step 2
- `conventions.unit_system` (inferred): inferred from contracts/units.json; shown as a recommendation in Step 2
- `gui_preference` (inferred): inferred from pixi.toml; shown as a recommendation in Step 2
- `operational_constraints.execution_permission` (condition): filled from the answer to policy.execution_permission

## Held until answered

- `collaboration.mode`
- `policy.working_mode`
- `policy.approval_mode`
- `policy.publication_scope`
- `policy.execution_permission`
- `policy.external_transfer_of_private_code`
- `operational_constraints.execution_permission`

## Registry entries that match the engines found

- `hoomd_blue` HOOMD-blue: methods md, bd_cg; interface python_api; licence BSD-3-Clause (LICENSE read on GitHub 2026-10-29; entry unverified); verified: no

## What happens next

The person answers the asked questions in a small JSON file (`answered_by: human`, a date, and `answers` by field) and the Meta-Agent runs Step three, which writes a new revision of the record and of the profile with those answers `confirmed`. Nothing is built from this profile while a policy field is open.
