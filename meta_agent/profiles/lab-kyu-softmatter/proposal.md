# Onboarding proposal: lab-kyu-softmatter

What Step zero read, what it inferred, what it could not, and what it asks. Inferred values are recommendations with evidence; only a person's answer makes a value `confirmed`.

## Inputs read

- repo: `https://github.com/kyu-softmatter/soft-matter-agents@53746af`
- repo: `https://github.com/kyu-softmatter/HOOMD_GUI@785727e`

## Inferred (recommendations)

- `existing_code` = `https://github.com/kyu-softmatter/soft-matter-agents, https://github.com/kyu-softmatter/HOOMD_GUI` - from .claude/end-of-turn-commit-check.py, python/hoomd_gui_core/__init__.py
- `collaboration.first_agent` = `False` - from contracts/seats.json
- `collaboration.existing_agents` = `microscope_agent, simulation_agent, librarian_agent` - from contracts/seats.json
- `collaboration.bridge` = `True` - from bridge/
- `conventions.research_kind` = `simulation, experiment` - from microscope_agent/, pixi.toml, pyproject.toml
- `conventions.methods` = `md, bd_cg` - from console/src/sma_console/agents/mock_sim.py, librarian_agent/src/export_snapshot.py, pixi.toml, pyproject.toml, simulation_agent/src/abp_backend.py
- `preferred_engines` = `hoomd_blue` - from console/src/sma_console/agents/simulation.py, console/tests/agents/test_agents_simulation.py, pixi.toml, pyproject.toml, python/hoomd_gui_runner/__main__.py
- `preferred_instruments` = `sma_microscope` - from microscope_agent/
- `software_env.language` = `python, typescript, javascript` - from console/web/vite.config.ts, pyproject.toml, web/scripts/analysis.js
- `software_env.os` = `macos, linux, windows` - from pixi.toml, pyproject.toml
- `software_env.package_manager` = `pixi, uv` - from pixi.toml, pyproject.toml, uv.lock
- `hardware.gpu` = `True` - from microscope_agent/autofocus/scripts/bench_latency.py, microscope_agent/autofocus/src/dino_autofocus/backbone.py, microscope_agent/autofocus/tests/synth/test_gpu.py, scripts/check_environment.py
- `existing_data` = `soft-matter-agents:microscope_agent/` - from microscope_agent/autofocus/models/heads/head_k100x_dinov2_vits14_L1.npz
- `validated_workflows` = `HOOMD_GUI:tests/` - from tests/
- `operational_constraints.licenses` = `MIT (soft-matter-agents)` - from LICENSE
- `conventions.unit_system` = `SI, kelvin only` - from contracts/units.json
- `gui_preference` = `parameter_form` - from pixi.toml, pyproject.toml - a recommendation from the research kind and methods, not a reading of a preference; a visual editor or reuse of the lab's own GUI are the alternatives

## Asked (unknown, or policy)

- `collaboration.mode` (collaboration, policy): Should the new agent be configured to collaborate with existing agents (a bridge plan), work alone, or decide later?
- `hardware.hpc` (tool preferences, unknown): Is there an HPC cluster or a scheduler (SLURM, PBS, other)?
- `policy.working_mode` (operating policy, policy): How does the lab want to work with the Meta-Agent: card by card with review, or in batches?
- `policy.approval_mode` (operating policy, policy): Which actions need a person's approval before they run?
- `policy.publication_scope` (operating policy, policy): Who may see the agents and their results: this lab, collaborators, or the public?
- `policy.execution_permission` (operating policy, policy): May a built agent run anything on its own, and if so what: mock, sandbox, an engine, an instrument?
- `policy.external_transfer_of_private_code` (operating policy, policy): May private code leave the lab's computers, for example to an analysis service?

## Skipped, with the reason

- `existing_code` (inferred): inferred from .claude/end-of-turn-commit-check.py, python/hoomd_gui_core/__init__.py; shown as a recommendation in Step 2
- `collaboration.first_agent` (inferred): inferred from contracts/seats.json; shown as a recommendation in Step 2
- `collaboration.existing_agents` (inferred): inferred from contracts/seats.json; shown as a recommendation in Step 2
- `collaboration.bridge` (inferred): inferred from bridge/; shown as a recommendation in Step 2
- `conventions.research_kind` (inferred): inferred from microscope_agent/, pixi.toml, pyproject.toml; shown as a recommendation in Step 2
- `conventions.methods` (inferred): inferred from console/src/sma_console/agents/mock_sim.py, librarian_agent/src/export_snapshot.py, pixi.toml, pyproject.toml, simulation_agent/src/abp_backend.py; shown as a recommendation in Step 2
- `preferred_engines` (inferred): inferred from console/src/sma_console/agents/simulation.py, console/tests/agents/test_agents_simulation.py, pixi.toml, pyproject.toml, python/hoomd_gui_runner/__main__.py; shown as a recommendation in Step 2
- `preferred_instruments` (inferred): inferred from microscope_agent/; shown as a recommendation in Step 2
- `software_env.language` (inferred): inferred from console/web/vite.config.ts, pyproject.toml, web/scripts/analysis.js; shown as a recommendation in Step 2
- `software_env.os` (inferred): inferred from pixi.toml, pyproject.toml; shown as a recommendation in Step 2
- `software_env.package_manager` (inferred): inferred from pixi.toml, pyproject.toml, uv.lock; shown as a recommendation in Step 2
- `hardware.gpu` (inferred): inferred from microscope_agent/autofocus/scripts/bench_latency.py, microscope_agent/autofocus/src/dino_autofocus/backbone.py, microscope_agent/autofocus/tests/synth/test_gpu.py, scripts/check_environment.py; shown as a recommendation in Step 2
- `existing_data` (inferred): inferred from microscope_agent/autofocus/models/heads/head_k100x_dinov2_vits14_L1.npz; shown as a recommendation in Step 2
- `validated_workflows` (inferred): inferred from tests/; shown as a recommendation in Step 2
- `operational_constraints.licenses` (inferred): inferred from LICENSE; shown as a recommendation in Step 2
- `conventions.unit_system` (inferred): inferred from contracts/units.json; shown as a recommendation in Step 2
- `gui_preference` (inferred): inferred from pixi.toml, pyproject.toml; shown as a recommendation in Step 2
- `operational_constraints.execution_permission` (condition): filled from the answer to policy.execution_permission

## Held until answered

- `collaboration.mode`
- `hardware.hpc`
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
