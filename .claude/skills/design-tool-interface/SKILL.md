---
name: design-tool-interface
description: Design how a built agent calls its instrument or engine, as one contract per callable tool for its inputs, outputs, side effects and errors. Use when a tool profile is written and the agent's callable tools are to be specified, when an adapter is added or changed, and when a tool's side effects or its place behind the safety gate must be decided.
---

# Design the tool interface

An agent reaches its tool only through contracts. Each callable tool has one, and every call goes through the bundle's runner, which asks the gate, checks the input, calls the adapter, checks the output and returns the output or a structured error.

Load `classify-knowledge` before the first value, statement or data file of this part enters a card, a sheet or a skill's inputs, if it is not loaded in this session yet: it binds at every stage (`meta_agent/CLAUDE.md`), and a value that entered before it was loaded has been placed from memory of it.

## Do this

1. **Start from the claims.** Only `observed` and `derived` claims of the `tool_profile` become capabilities. An `inferred` one is listed as unverified and an `unknown` one as a gap.
2. **One contract per tool** (`contracts/schemas/tool_contract.schema.json`): its name and description, each input with its unit and range, each output with its unit, and its side effects.
3. **Say the side effect truthfully.** A tool that only reads an instrument says so. A tool that changes anything asks for the gate, and its contract names the script where the deterministic rule runs. Say what opens its gate (`opens_by`): a tool that changes an instrument opens only by safety values a person wrote; one that starts an engine or writes the agent's own files may open by the lab's confirmed execution permission; one that reaches the network may open by it only to install the agent's packages, from a source its contract names (`installs_from`) and the lab's permission lists.
4. **Every setting a tool takes has a row.** A value the source states for a call (a run's settings, an analysis's settings) is a row of the request's parameter sheet citing where it was read, and the bundle's tasks, its replay items and a person's run all take it from that row. A value that stands only in a validation item is one a session cannot use. An input a row gives names that row under `row` in the contract's input schema, and an input that takes a swept parameter names a row per point under `rows`; the bundle's gate looks for each named row in the bundle's parameter file. An input with a closed set of values lists them in its contract.
5. **Errors are structured** (`contracts/schemas/error_contract.schema.json`): a code, a category, a message, whether a retry may help, and what to do. A refusal by the safety rule and a missing permission each have their own category.
6. **Give fixture calls** for each tool: one that succeeds and one for each error it can return. The gate runs them.
7. **Units are registered** in `contracts/units.json`. A number in a contract carries its source.
8. **What is unresolved goes to `held`:** a scope, a permission, a side effect or a validation that is not settled keeps the tool out of the bundle, and the intake's `held` names it with its reason, so that the bundle says what it lacks.

## Never

Bundle source under a licence that forbids it: call it instead. Let a skill or a session reach the device around the runner. Put a limit in an adapter: limits are read from the envelope by the gate.

Reference: `plan.md 5.1` (interface axis and build), `plan.md 6.4`.
