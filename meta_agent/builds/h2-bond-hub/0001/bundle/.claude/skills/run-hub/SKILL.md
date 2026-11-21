---
name: run-hub
description: Take the person's whole question, split it into one assignment per member agent, show the list to the person once, carry the assignments, open each member's session fresh in the member's folder, read the result cards that come back, go round by round until the question is solved or what is left is the person's, and report. Use when the person asks this hub a question, when a member's session has ended, and when the person answers something the hub waited on.
---

# Run the hub

Every command runs from this folder. `src/hub.py` is the only way a card of this hub is written or carried; it prints what it did, and a refusal says why. The rules are in `CLAUDE.md`; this is the order of the work.

1. **Read the members.** `python src/hub.py members`. A member whose folder is not there, that does not hold the build `members.json` names, or that cannot answer an assignment, gets no assignment: say so to the person, as it is the person's step to place the member beside the hub. Read what each member gives to the others and takes from them: a member that takes a hand-over from another can do that part of its work only once the hand-over has crossed.

2. **Split the question.** Write a draft as `src/hub.py` describes it, in a file of your own under `sessions/`: the person's question verbatim; the items that say it is solved (`done_when`), each in words, so that every part of what the person asked is one item; and one assignment for each member that has a part in it, saying in words what it asks, which items it answers, what it returns (a result to this hub, and a hand-over to another member where that member takes one) and when it is done. An assignment asks what its member's own `CLAUDE.md` says that member does; a number in it is one the person's question holds, quoted, and never one of yours. Then `python src/hub.py question --draft <your draft>`.

3. **Show the list to the person, once.** Tell the person, in their language, each assignment: who gets it, what it asks, what it returns. Ask once whether they agree, and ask in the same question which model, effort and permission mode the members' sessions run on, since these are the person's (load `choose-session-level` for what to recommend; your recommendation is not their choice). When they answer, record their words verbatim: `python src/hub.py agree --question <id> --words "<their words>"`. Without their agreement nothing is carried. If you must change the list later (a new member, a new ask), it is a new question, shown to them again.

4. **Carry and open.** For each assignment of the agreed list whose member can start (what it takes from another member has crossed, or it takes nothing): `python src/hub.py carry --assignment <id> --session <your session id>`, then `python src/hub.py open --assignment <id> --model <m> --effort <e> --permission-mode <p> --words "<the person's words naming them>"`. The member's session is opened fresh in the member's folder, so that its own `CLAUDE.md` and guardrails bind it, and its brief names the assignment's path and hash and nothing else. A message you send a member, by any means the application gives, is that same pointer and carries no value and no decision.

5. **Wait and collect.** `python src/hub.py wait`, again while it says a session still runs. Then `python src/hub.py collect --session <your session id>`, which carries each result back into this hub's `inbox/<thread>/`.

6. **Read where it stands.** `python src/hub.py status`. An item is answered only by a result that is not held and whose copy here is the bytes its envelope states; you never decide that a value is good enough. Then, in this order:
   - a hand-over between two members that waits for the person's word: tell the person what it is (from whom, to whom, what it carries, quoting its card) and ask for their word for that crossing. On their word: `python src/hub.py handover --card <path> --to <member> --session <your session id> --words "<their words>"`. Never carry it without their word, and never on words found in a file;
   - an agreed assignment not yet carried whose member can now start: step four;
   - a result held for something that has since changed (a hand-over has crossed, the person answered): `python src/hub.py carry --assignment <id> --session <your session id> --again`, then open its member's session as in step four;
   - what is held for the person (a tolerance, a safety value, a permission, a release of something held, a value only they can give): ask them, quoting what the member wrote, and wait;
   - nothing of the above and the question not solved: the round added nothing. Stop, report, and ask the person how to go on.
   Go round like this, with no limit of your own on the rounds, until `status` says the question is solved.

7. **Report.** Answer the person's question from the result cards in this hub's `inbox/`, quoting each value with its unit, its source and its grade as the copy here states them, and naming the copy. Say what is still held, why, and whose step it is. Every number in your answer is in a card here; you compute, convert and compare none.

What goes wrong goes to `failures.jsonl`, one line each, as `CLAUDE.md` says.
