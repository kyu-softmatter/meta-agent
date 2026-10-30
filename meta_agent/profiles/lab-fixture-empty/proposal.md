# Onboarding proposal: lab-fixture-empty

What Step zero read, what it inferred, what it could not, and what it asks. Inferred values are recommendations with evidence; only a person's answer makes a value `confirmed`.

## Inputs read

- folder: `D:/codes/github/meta-agent/meta_agent/tests/fixtures/labs/empty`

## Inferred (recommendations)

- nothing could be inferred: no material was given

## Asked (unknown, or policy)

- `existing_code` (materials, unknown): Are there repositories, documents, manuals or existing agent cards to analyse? PDFs or links for preferred simulation engines or experimental platforms are welcome at any time: one line in inbox/materials/LINKS.md is enough.
- `collaboration.first_agent` (lab, unknown): Is this the lab's first agent?
- `collaboration.mode` (collaboration, policy): Should the new agent be configured to collaborate with existing agents (a bridge plan), work alone, or decide later?
- `conventions.research_kind` (research kind, unknown): What kind of research will the agents support: simulation, experiment, analysis (several are fine)?
- `conventions.methods` (methods, unknown): If simulation: which methods - DFT, MD, BD/CG, mesoscale, CFD, FEM, other (several are fine)?
- `preferred_engines` (tool preferences, unknown): Which simulation engines does the lab prefer or already use?
- `preferred_instruments` (tool preferences, unknown): Which instruments will the agents operate or read?
- `software_env.language` (tool preferences, unknown): Which programming languages are in use?
- `software_env.os` (tool preferences, unknown): Which operating systems run the agents?
- `software_env.package_manager` (tool preferences, unknown): Which package or environment manager is in use (pixi, uv, conda, pip, other)?
- `hardware.gpu` (tool preferences, unknown): Are GPUs available for simulation or analysis?
- `hardware.hpc` (tool preferences, unknown): Is there an HPC cluster or a scheduler (SLURM, PBS, other)?
- `existing_data` (existing assets, unknown): Which data sets or run records exist and may be read?
- `validated_workflows` (existing assets, unknown): Which workflows are already validated and in use?
- `operational_constraints.licenses` (existing assets, unknown): Which licences constrain the code in use or the code to be written?
- `conventions.unit_system` (existing assets, unknown): Which unit conventions does the lab use (SI, kelvin only, others)?
- `gui_preference` (GUI, unknown): Do you want a GUI: none, a parameter form, a visual editor, or reuse of the lab's GUI?
- `policy.working_mode` (operating policy, policy): How does the lab want to work with the Meta-Agent: card by card with review, or in batches?
- `policy.approval_mode` (operating policy, policy): Which actions need a person's approval before they run?
- `policy.publication_scope` (operating policy, policy): Who may see the agents and their results: this lab, collaborators, or the public?
- `policy.execution_permission` (operating policy, policy): May a built agent run anything on its own, and if so what: mock, sandbox, an engine, an instrument?
- `policy.external_transfer_of_private_code` (operating policy, policy): May private code leave the lab's computers, for example to an analysis service?

## Skipped, with the reason

- `collaboration.existing_agents` (condition): deferred until the first-agent answer; carried as held
- `collaboration.bridge` (condition): deferred until the first-agent answer; carried as held
- `operational_constraints.execution_permission` (condition): filled from the answer to policy.execution_permission

## Held until answered

- `existing_code`
- `collaboration.first_agent`
- `collaboration.mode`
- `collaboration.existing_agents`
- `collaboration.bridge`
- `conventions.research_kind`
- `conventions.methods`
- `preferred_engines`
- `preferred_instruments`
- `software_env.language`
- `software_env.os`
- `software_env.package_manager`
- `hardware.gpu`
- `hardware.hpc`
- `existing_data`
- `validated_workflows`
- `operational_constraints.licenses`
- `conventions.unit_system`
- `gui_preference`
- `policy.working_mode`
- `policy.approval_mode`
- `policy.publication_scope`
- `policy.execution_permission`
- `policy.external_transfer_of_private_code`
- `operational_constraints.execution_permission`

## What happens next

The person answers the asked questions in a small JSON file (`answered_by: human`, a date, and `answers` by field) and the Meta-Agent runs Step three, which writes a new revision of the record and of the profile with those answers `confirmed`. Nothing is built from this profile while a policy field is open.
