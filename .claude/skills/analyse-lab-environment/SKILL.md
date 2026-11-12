---
name: analyse-lab-environment
description: Read how a laboratory's materials, data, code and software are laid out and what its software can do, before asking anything, and write what was found as inferred with evidence or unknown. Use when a new laboratory, repository or folder is given, when the person asks to onboard a lab or to understand its environment or its software, and when new material about an engine or a program arrives.
---

# Analyse the lab environment and its software

Analyse first, ask later. What you can read you do not ask; what you infer is a recommendation; only the person confirms.

## The environment

1. **Discover.** Read the repositories, folders, documents and existing agent cards the person gave:
   ```
   python -m meta_agent.src.onboarding --lab-id <lab_id> --out meta_agent/profiles/<lab_id> --repo <path> --seat <seat>
   ```
   It writes the `discovery_report`: every field is `inferred` with its evidence, or `unknown`.
2. **Ask only what is `unknown` and the policy fields.** One or a few questions at a time, the most important first. Questions, answers and what was skipped, each with its reason, go to the `onboarding_record`.
3. **Propose** the `lab_profile`. `inferred` becomes `confirmed` by the person only.
4. **Check sufficiency** at each step. If design can go on despite a gap, the unsettled setting goes to `held` and work continues.

Policy fields are never skipped and never inferred: working mode, approval mode, publication scope, execution permission, collaboration mode, and whether private code may leave. A repository in Python does not make a Python-only lab, and a public repository does not make its data publishable.

## The software to be made into an agent

- **Source, documents, configuration, existing scripts:** read them with ordinary tools.
- **Binaries and runtime behaviour:** only through REA, and only when the `tool_profile` carries an `analysis_permission` that names a person, a scope, a basis and a date. Without it the gap is `inaccessible` and the design uses documented interfaces only. Runtime capture happens only in a replica with no instrument attached.
- **Every claim is one of four:** `observed`, `derived`, `inferred` or `unknown`, with its `basis`, its evidence and its limitations. An `unknown` says what would resolve it. Unsupported is never concluded from partial evidence.
- **Six points for software that drives something:** connection, operation, parameters, bandwidth, what is streamed live, and how often it is refreshed.

## Writes

`meta_agent/profiles/<lab_id>/` (the report, the record, the proposed profile) and the request's `tool_profile`.

## Never

Infer a policy. Grant a permission because the material seemed sufficient. Write an inference as an observation. Use a credential or a stored login.

Reference: `plan.md 5.0`, `plan.md 5.1` (tool understanding), `plan.md 5.6`.
