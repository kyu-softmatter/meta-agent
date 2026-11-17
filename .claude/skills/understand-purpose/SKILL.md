---
name: understand-purpose
description: Turn what the person wants an agent for into a written goal that every later step reads, with no numbers in it. Use when the person describes an agent they want, a question they want answered or a task to automate, before any tool is analysed for that request, and whenever the purpose changes.
---

# Understand the person's purpose

A loose purpose gives every later step a different question. Write one goal, have the person confirm it, and everything after reads that card.

## Do this

1. **Start the request's intake card** (`contracts/schemas/intake.schema.json`). Write a draft, a file of your own with what you know and no stage in it, and let the stage write the card from it; never write `meta_agent/requests/<rid>/intake.json` by hand or by a script of your own:
   ```
   python -m meta_agent.src.intake write --rid <rid> --draft <file> --seat <seat>
   ```
   Keep the person's words verbatim in the draft, in the language they used, with an English gloss and what they came with (a link, a file). A later draft holds only what changes and gives the next revision. The card is at the stage `reading` until it carries a tool contract.
2. **Restate it** as what the agent is for and what scientific task it serves. Where the wording is loose, say which reading you took. Ask only when two readings would lead to different agents.
3. **Fill the goal's fields** (`contracts/schemas/agent_goal.schema.json`): the purpose, the science task, the tool and its kind, the methods, whether it executes, what it must not do, what knowledge and which parameters it needs, where it will live, and the priorities to concede by when axes conflict.
4. **Make no numbers.** A target, a tolerance or a threshold is the person's and is asked for, or stays undecided.
5. **Ask once, only what only a person can answer.** Policy, permissions and publication scope are never inferred. Permission to analyse a binary or a runtime is the person's to give. Each question goes into the intake with what it is needed before, so that a request that waits is a card the gate reads and the next session finds: `python -m meta_agent.src.intake waiting --rid <rid>` lists what waits, and the person's answer is written into the card with `python -m meta_agent.src.intake answer --rid <rid> --n <n> --verbatim "…" --date <day> --seat <seat>`, the words unchanged.
6. **Do not wait where nothing needs the answer.** Carry on with every part that no open question stands before: the tool's reading, the scales, the recall. Under a working mode of batches the request is carried through and stops only at what only a person decides.
7. **When the contracts and the tasks are written** (`design-tool-interface`, and the validation tasks), the next revision of the intake is at the stage `specified` and carries them. **Run the Designer on that one:**
   ```
   python -m meta_agent.src.designer --intake meta_agent/requests/<rid>/intake.json --seat <seat>
   ```
   It writes the `agent_goal` first and carries the reference to the lab's profile. A goal on a lab whose policy fields are not confirmed is refused by the gate: the policy questions of that lab's proposal are then the first thing asked.

## Keep the purpose in view afterwards

Every later choice is judged against this card. Giving up a requirement of the purpose is the person's decision, never a step's.

## Never

Invent a requirement the person did not state. Put a number in the goal. Confirm a policy field yourself.

Reference: `plan.md 5.1` (intake).
