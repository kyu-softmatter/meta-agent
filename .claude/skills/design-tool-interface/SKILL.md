---
name: design-tool-interface
description: Design how a built agent calls its instrument or engine, as one contract per callable tool for its inputs, outputs, side effects and errors. Use when a tool profile is written and the agent's callable tools are to be specified, when an adapter is added or changed, and when a tool's side effects or its place behind the safety gate must be decided.
---

# Design the tool interface

An agent reaches its tool only through contracts. Each callable tool has one, and every call goes through the bundle's runner, which asks the gate, checks the input, calls the adapter, checks the output and returns the output or a structured error.

## Do this

1. **Start from the claims.** Only `observed` and `derived` claims of the `tool_profile` become capabilities. An `inferred` one is listed as unverified and an `unknown` one as a gap.
2. **One contract per tool** (`contracts/schemas/tool_contract.schema.json`): its name and description, each input with its unit and range, each output with its unit, and its side effects.
3. **Say the side effect truthfully.** A tool that only reads an instrument says so. A tool that changes anything asks for the gate, and its contract names the script where the deterministic rule runs.
4. **Errors are structured** (`contracts/schemas/error_contract.schema.json`): a code, a category, a message, whether a retry may help, and what to do. A refusal by the safety rule and a missing permission each have their own category.
5. **Give fixture calls** for each tool: one that succeeds and one for each error it can return. The gate runs them.
6. **Units are registered** in `contracts/units.json`. A number in a contract carries its source.
7. **What is unresolved goes to `held`:** a scope, a permission, a side effect or a validation that is not settled keeps the tool out of the bundle.

## Never

Bundle source under a licence that forbids it: call it instead. Let a skill or a session reach the device around the runner. Put a limit in an adapter: limits are read from the envelope by the gate.

Reference: `plan.md 5.1` (interface axis and build), `plan.md 6.4`.
