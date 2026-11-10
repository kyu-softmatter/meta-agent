# claims/

One file per task and seat, written by the seat that takes the task and never edited: `<task id>-<seat>.json` holds the task, the seat and the time. A seat that gives a task up writes `<task id>-<seat>-released.json` beside it, saying why. Write them with `python contracts/tools/tasks.py claim <id> --seat <name>` and commit each alone. One seat holds a task's role at a time; check 20 fails a second claim, a claim before the task's dependencies are done, and a claim committed by another seat.
