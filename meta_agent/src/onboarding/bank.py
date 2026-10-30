"""The question bank of S0 Step 1 (plan.md 5.0).

One entry per lab_profile leaf the wizard may ask about. The bank has no
fixed order; what is asked is decided per lab by `wizard.ask` from the
discovery report: a field that is `unknown` is asked, a field that is
`inferred` is skipped and shown as a recommendation, and a policy field is
asked whatever the report says. Policy fields are read from
contracts/claim_kinds.json, not from this file.
"""

# (field, group, question, condition)
# condition is a name evaluated by `wizard.condition_blocks`; None = no condition.
BANK = [
    ("existing_code", 0,
     "Are there repositories, documents, manuals or existing agent cards to analyse? "
     "PDFs or links for preferred simulation engines or experimental platforms are welcome "
     "at any time: one line in inbox/materials/LINKS.md is enough.", None),
    ("collaboration.first_agent", 1,
     "Is this the lab's first agent?", None),
    ("collaboration.mode", 2,
     "Should the new agent be configured to collaborate with existing agents (a bridge plan), "
     "work alone, or decide later?", None),
    ("collaboration.existing_agents", 2,
     "Which agents already exist, and where do their cards live?", "needs_existing_agents"),
    ("collaboration.bridge", 2,
     "Is there a bridge or message board between the agents?", "needs_existing_agents"),
    ("conventions.research_kind", 3,
     "What kind of research will the agents support: simulation, experiment, analysis "
     "(several are fine)?", None),
    ("conventions.methods", 4,
     "If simulation: which methods - DFT, MD, BD/CG, mesoscale, CFD, FEM, other "
     "(several are fine)?", "simulation_possible"),
    ("preferred_engines", 5,
     "Which simulation engines does the lab prefer or already use?", None),
    ("preferred_instruments", 5,
     "Which instruments will the agents operate or read?", None),
    ("software_env.language", 5,
     "Which programming languages are in use?", None),
    ("software_env.os", 5,
     "Which operating systems run the agents?", None),
    ("software_env.package_manager", 5,
     "Which package or environment manager is in use (pixi, uv, conda, pip, other)?", None),
    ("hardware.gpu", 5,
     "Are GPUs available for simulation or analysis?", None),
    ("hardware.hpc", 5,
     "Is there an HPC cluster or a scheduler (SLURM, PBS, other)?", None),
    ("existing_data", 6,
     "Which data sets or run records exist and may be read?", None),
    ("validated_workflows", 6,
     "Which workflows are already validated and in use?", None),
    ("operational_constraints.licenses", 6,
     "Which licences constrain the code in use or the code to be written?", None),
    ("conventions.unit_system", 6,
     "Which unit conventions does the lab use (SI, kelvin only, others)?", None),
    ("gui_preference", 7,
     "Do you want a GUI: none, a parameter form, a visual editor, or reuse of the lab's GUI?", None),
    ("policy.working_mode", 8,
     "How does the lab want to work with the Meta-Agent: card by card with review, or in batches?", None),
    ("policy.approval_mode", 8,
     "Which actions need a person's approval before they run?", None),
    ("policy.publication_scope", 8,
     "Who may see the agents and their results: this lab, collaborators, or the public?", None),
    ("policy.execution_permission", 8,
     "May a built agent run anything on its own, and if so what: mock, sandbox, an engine, an instrument?", None),
    ("policy.external_transfer_of_private_code", 8,
     "May private code leave the lab's computers, for example to an analysis service?", None),
]

# A field filled from another field's answer: one question, two leaves.
DERIVED = {
    "operational_constraints.execution_permission": "policy.execution_permission",
}

# Every leaf a discovery report and a lab profile carry, asked or not.
FIELDS = [f for f, _, _, _ in BANK] + list(DERIVED)

GROUP_NAMES = {
    0: "materials", 1: "lab", 2: "collaboration", 3: "research kind", 4: "methods",
    5: "tool preferences", 6: "existing assets", 7: "GUI", 8: "operating policy",
}


def by_field():
    return {f: (g, q, cond) for f, g, q, cond in BANK}
