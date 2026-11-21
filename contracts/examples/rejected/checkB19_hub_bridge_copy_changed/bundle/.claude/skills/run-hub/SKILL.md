---
name: run-hub
description: Take the person's question, split it into assignments for the members, carry them, open each member's session, read the results and report. Use for every question put to this hub.
---

# Run the hub

1. Write the question with `src/hub.py question`, and the list of assignments, one per member in `members.json`.
2. Show the person the list once and record their words of agreement with `src/hub.py agree`.
3. Carry each assignment with `src/hub.py carry`, which runs `src/bridge.py` on the hub's trigger.
4. Open each member's session fresh in the member's folder, its brief naming only the assignment's path.
5. Read each result's state with `src/hub.py results`; quote values from the result cards, never compute one.
6. Go on round by round until every item of the question is answered by a result that is not held; wait where what is left is the person's; report.
