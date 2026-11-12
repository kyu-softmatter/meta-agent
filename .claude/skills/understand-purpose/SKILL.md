---
name: understand-purpose
description: Turn what the person wants an agent for into a written goal that every later step reads, with no numbers in it. Use when the person describes an agent they want, a question they want answered or a task to automate, before any tool is analysed for that request, and whenever the purpose changes.
---

# Understand the person's purpose

A loose purpose gives every later step a different question. Write one goal, have the person confirm it, and everything after reads that card.

## Do this

1. **Keep the person's paragraph verbatim** at the top of the intake, in the language they used, with an English gloss.
2. **Restate it** as what the agent is for and what scientific task it serves. Where the wording is loose, say which reading you took. Ask only when two readings would lead to different agents.
3. **Fill the goal's fields** (`contracts/schemas/agent_goal.schema.json`): the purpose, the science task, the tool and its kind, the methods, whether it executes, what it must not do, what knowledge and which parameters it needs, where it will live, and the priorities to concede by when axes conflict.
4. **Make no numbers.** A target, a tolerance or a threshold is the person's and is asked for, or stays undecided.
5. **Ask once, only what only a person can answer.** Policy, permissions and publication scope are never inferred. Permission to analyse a binary or a runtime is the person's to give.
6. **Run the intake:**
   ```
   python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat>
   ```
   It writes the `agent_goal` first and carries the reference to the lab's profile.

## Keep the purpose in view afterwards

Every later choice is judged against this card. Giving up a requirement of the purpose is the person's decision, never a step's.

## Never

Invent a requirement the person did not state. Put a number in the goal. Confirm a policy field yourself.

Reference: `plan.md 5.1` (intake).
