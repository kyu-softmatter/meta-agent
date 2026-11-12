---
name: begin-session
description: Start a working session in this repository. Runs the gate, takes a seat and registers it in its own commit, reads what other seats asked of the role, and claims a task. Use at the start of every session before any other write, when the person names a role or a task, when a brief says to take a task, and in a fork before it does anything else.
---

# Begin a session

Every command runs from the repository root. Nothing else is written before step three is committed.

1. **Run the gate.** `python contracts/validate.py`. The last line must say `VERDICT PASS`. If it does not, say what failed and stop: a session does not start work on a tree that fails.
2. **Know your role.** The person names it, or the task you were given does. Never choose a role, a machine tag or a wider path yourself. If none is named, ask the person once.
3. **Take a seat, in its own commit.**
   ```
   python bootstrap.py seat <role> --write
   python contracts/tools/seat_commit.py --seat <name> -m "contracts/seats: <name> seats itself" contracts/seats.json
   ```
   The first command prints your seat's name. A fork does this as well: it inherits a conversation in which another session names its seat, and it never commits as that seat.
4. **Read what binds you.** `CLAUDE.md`, and `meta_agent/CLAUDE.md` when your role is `meta`. On your first session here also read `plan.md 3, 6, 8, 9`.
5. **Read what was asked of your role.** `python contracts/tools/notes.py list --role <role>`. An ask that waits is answered before new work, or you say why not.
6. **Take a task and claim it, in its own commit.** Unless the person or your brief names one:
   ```
   python contracts/tools/tasks.py next --role <role>
   python contracts/tools/tasks.py claim <id> --seat <name>
   ```
   Commit the claim file alone with `seat_commit.py`. Where a task has a design part, that part lands first; `next` does not offer the task to another role before it has.
7. **If you are a fork,** write down what you inherited that your work rests on, before you rely on it: the person's words go to `docs/ideas/<YYYYMMDD>.md` through the design role, anything else to the task card. What is only in a conversation is not in the record.

## Commit as your seat, always

`python contracts/tools/seat_commit.py --seat <name> -m <message> <paths…>` commits only the paths you name, as your seat, with the person as author. Never `git add -A`. Never set `committer.name` in the repository's configuration while another seat shares the folder.

## A clone that is not set up

If `git config core.hooksPath` does not print `contracts/hooks`, set the clone up once:

```
git config core.hooksPath contracts/hooks
export PYTHONUTF8=1          (on Windows: set PYTHONUTF8=1)
python contracts/validate.py
python bootstrap.py check
python bootstrap.py install node rea --yes
```

`git config meta-agent.machine` must print the tag the person gave this computer. If it prints nothing, ask the person for the tag; a session does not invent one.

## When you are done

Use the `end-session` skill.
