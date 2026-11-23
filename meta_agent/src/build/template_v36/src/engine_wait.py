"""Wait on a process an adapter starts, telling an engine paused from outside from one that hung (v30).

An adapter that starts an engine and waits for it imports this module (src/ is on the path whenever src/run_tool.py
calls an adapter) and waits through it, not through subprocess.run(..., timeout=...):

    import engine_wait
    result = engine_wait.run(argv, cwd=work, budget_s=limit, progress=[log_path], stall_s=quiet,
                             stop_markers=["the words the engine prints when a signal stops it"])
    stop = engine_wait.stop_error("<tool>", result, resumes_from=checkpoint_path)
    if stop is not None:
        return stop              # a stop the agent may call again for, resuming from the checkpoint where there is one

A wall-clock timeout counts the time an engine is paused (SIGSTOP from a person, a scheduler or a job control stop)
as if it were running, so a paused engine is killed as if it had hung and loses what it ran since its last
checkpoint. Here:

- budget_s counts running time only. The process group is looked at every poll_s seconds; while any process of it is
  stopped, the time is counted as paused and not against the budget.
- stall_s, where given, is how long the engine may run (not paused) while none of the progress files changes, before
  the call takes it for hung.
- The call gives up on either and stops the engine with TERM first, so that an engine which checkpoints on TERM does
  so; only after grace_s more seconds is it killed.
- A run that ended on TERM, INT or HUP, sent by whoever, or whose output shows one of stop_markers, was stopped and
  did not fail: stop_error() turns it into an error contract with retryable true, and says whether a call made again
  resumes from the checkpoint the adapter names (evidence.resumable) or starts over. A call that gave up comes back
  as category timeout, a stop from outside as cancelled.

Each call keeps its own outputs (v35; failure line dft-24 of the builder's tree, where a rerun of a tool wrote over an
example's earlier outputs and log and left no record of the run it replaced):

    work = engine_wait.new_run_folder("scan")      # runs/scan/<UTC stamp>/, made new, never one that exists
    result = engine_wait.run(argv, cwd=work, stdout_path=os.path.join(work, "engine.out"), ...)

- new_run_folder(kind) makes runs/<kind>/<UTC stamp>/ inside this bundle and never takes a folder that exists, so an
  earlier call's folder is never written into; the stamp is the time the call began, in UTC.
- run() opens the logs it is given for stdout and stderr only where no file of that name exists, and raises
  FileExistsError naming it otherwise: it never writes over a log.

A call may run its engine on a number of processes (v35; dft-23, where a tool had no input for one and the reference's
conditions could not be reached):

    bad = engine_wait.processes_error("<tool>", payload.get("n_processes"), launcher=LAUNCHER)
    if bad is not None:
        return bad
    result = engine_wait.run(argv, n_processes=payload.get("n_processes"), launcher=LAUNCHER, ...)

- launcher is the adapter's: the argv of the program that starts the engine on several processes, one of its items
  "{n}" where the count goes (an MPI launcher's ["<path>/mpirun", "-np", "{n}"], say). With n_processes None the engine
  starts directly and the launcher is not used. The count is the call's input, a person's or a task's; this module
  chooses none and sets no ceiling: the gate reads the lab's permission level, which names no count.
- processes_error() returns an invalid_input error for a count that is not a positive integer, and an unavailable one
  where a count is asked for and the launcher is not there; run() refuses either with ValueError.

What the engine finished, failed or printed is the adapter's to read: this module judges no result and computes no
quantity. The numbers it takes are the adapter's arguments; the defaults are only how often it looks and how long it
waits after TERM. Standard library only.
"""
import datetime
import os
import signal
import subprocess
import tempfile
import time

STOP_SIGNALS = ("SIGTERM", "SIGINT", "SIGHUP")
TAIL = 4000          # characters of stdout and stderr kept in an error's evidence
HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
COUNT = "{n}"        # the launcher's item the count replaces


def new_run_folder(kind):
    """Make runs/<kind>/<UTC stamp>/ in this bundle, a folder no call made before, and return its path. A stamp taken
    twice within one microsecond gets a suffix; a folder that exists is never taken."""
    if not kind or os.sep in kind or (os.altsep and os.altsep in kind) or kind in (".", ".."):
        raise ValueError("a run folder's kind is one folder name, not %r" % (kind,))
    base = os.path.join(BUNDLE, "runs", kind)
    os.makedirs(base, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    for n in range(1000):
        path = os.path.join(base, stamp if n == 0 else "%s-%d" % (stamp, n))
        try:
            os.mkdir(path)          # refuses a folder that exists
            return path
        except FileExistsError:
            continue
    raise FileExistsError("no new run folder could be made under %s" % base)


def _count_ok(n):
    return isinstance(n, int) and not isinstance(n, bool) and n >= 1


def _launcher_ok(launcher):
    return (isinstance(launcher, (list, tuple)) and launcher and all(isinstance(a, str) for a in launcher)
            and COUNT in launcher)


def processes_error(tool, n_processes, launcher=None):
    """None where the call may run on n_processes (None: the engine starts directly), else an error contract: a count
    that is not a positive integer is invalid_input; a count asked for where the adapter names no launcher, or where
    the launcher's program is not there, is unavailable."""
    if n_processes is None:
        return None
    import run_tool   # here, not at the top: run_tool loads the adapter that imports this module
    if not _count_ok(n_processes):
        e = run_tool.error_template(tool, "invalid_input")
        e.update(code="%s-PROCESSES" % tool.upper(), category="invalid_input", retryable=False,
                 message="the number of processes is %r, not a positive integer" % (n_processes,),
                 remediation={"action": "name a positive count of processes, or none to start the engine directly"},
                 evidence={"n_processes": n_processes})
        return e
    program = launcher[0] if _launcher_ok(launcher) else None
    if program is None or not (os.path.isfile(program) or (not os.path.dirname(program) and _on_path(program))):
        e = run_tool.error_template(tool, "unavailable")
        e.update(code="%s-LAUNCHER" % tool.upper(), category="unavailable", retryable=False,
                 message="%d processes were asked for and %s" % (
                     n_processes, "this tool names no launcher" if program is None else "its launcher %s is not there" % program),
                 remediation={"action": "call with no count of processes, to start the engine directly, or remake the "
                                        "environment that holds the launcher"},
                 evidence={"n_processes": n_processes, "launcher": list(launcher) if launcher else None})
        return e
    return None


def _on_path(program):
    import shutil
    return shutil.which(program) is not None


def launched(argv, n_processes=None, launcher=None):
    """The argv that is started: argv itself where n_processes is None, else the launcher with the count in place of
    its "{n}", then argv. ValueError for a count that is not a positive integer or a launcher with no "{n}"."""
    if n_processes is None:
        return list(argv)
    if not _count_ok(n_processes):
        raise ValueError("the number of processes is %r, not a positive integer" % (n_processes,))
    if not _launcher_ok(launcher):
        raise ValueError("a count of processes needs a launcher, a list of strings with %r where the count goes" % COUNT)
    return [str(n_processes) if a == COUNT else a for a in launcher] + list(argv)


def _group_states(pgid):
    """The state letters of the processes of a process group, or None where they cannot be read."""
    if os.name != "posix":
        return None
    try:
        out = subprocess.run(["ps", "-A", "-o", "pgid=,stat="], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    states = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == str(pgid):
            states.append(parts[1])
    return states


def paused(pgid):
    """Whether any process of the group is stopped (state T): paused from outside, not hung."""
    states = _group_states(pgid)
    return bool(states) and any(s.startswith("T") for s in states)


def _signature(paths):
    sig = []
    for p in paths or ():
        try:
            st = os.stat(p)
            sig.append((p, st.st_size, st.st_mtime_ns))
        except OSError:
            sig.append((p, None, None))
    return tuple(sig)


def _signal(proc, sig):
    try:
        if os.name == "posix":
            os.killpg(proc.pid, sig)
        elif sig == getattr(signal, "SIGKILL", None):
            proc.kill()
        else:
            proc.terminate()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _signal_name(returncode):
    if returncode is None or returncode >= 0:
        return None
    try:
        return signal.Signals(-returncode).name
    except ValueError:
        return "signal %d" % -returncode


def _read(f):
    if f is None:
        return None
    f.seek(0)
    return f.read().decode("utf-8", "replace")


def _tail(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 65536))
            return f.read().decode("utf-8", "replace")
    except OSError:
        return ""


def run(argv, cwd=None, env=None, budget_s=None, stall_s=None, progress=(), stop_markers=(), poll_s=2.0, grace_s=120.0,
        stdout_path=None, stderr_path=None, n_processes=None, launcher=None):
    """Start argv in a process group of its own and wait for it; on n_processes through the launcher, where a count is
    given (see launched()). Returns a record:

    argv (what was started, the launcher included), n_processes, returncode, ended (exited | signal | stopped_by_call |
    killed_by_call), signal (its name, or None), gave_up (None, budget or stalled), running_s, paused_s, stop_marker
    (the first of stop_markers the output shows, or None), and stdout and stderr (the text, where no path was given for
    it; else None, and the path is in stdout_path or stderr_path). A log path that exists is never opened: it raises
    FileExistsError, since a log is never written over."""
    argv = launched(argv, n_processes, launcher)
    if stdout_path and stderr_path and os.path.abspath(stdout_path) == os.path.abspath(stderr_path):
        raise ValueError("stdout and stderr are given one log, %s; each needs its own" % stdout_path)
    outs = {}
    try:
        for name, path in (("stdout", stdout_path), ("stderr", stderr_path)):
            outs[name] = open(path, "xb") if path else tempfile.TemporaryFile()   # "x": never over a log that exists
    except FileExistsError:
        for f in outs.values():
            f.close()
        raise
    started = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=outs["stdout"], stderr=outs["stderr"],
                            start_new_session=(os.name == "posix"))
    running_s = paused_s = 0.0
    last = started
    seen, quiet_since = _signature(progress), 0.0
    gave_up = None
    try:
        while proc.poll() is None:
            time.sleep(poll_s)
            now = time.monotonic()
            step, last = now - last, now
            if proc.poll() is not None:
                running_s += step
                break
            if paused(proc.pid):
                paused_s += step
                continue
            running_s += step
            sig = _signature(progress)
            if sig != seen:
                seen, quiet_since = sig, running_s
            if budget_s is not None and running_s > budget_s:
                gave_up = "budget"
            elif stall_s is not None and progress and running_s - quiet_since > stall_s:
                gave_up = "stalled"
            if gave_up:
                break
        ended = None
        if gave_up:
            _signal(proc, signal.SIGTERM)
            _signal(proc, getattr(signal, "SIGCONT", signal.SIGTERM))   # a group stopped meanwhile takes the TERM too
            try:
                proc.wait(timeout=grace_s)
                ended = "stopped_by_call"
            except subprocess.TimeoutExpired:
                _signal(proc, getattr(signal, "SIGKILL", signal.SIGTERM))
                proc.wait()
                ended = "killed_by_call"
        returncode = proc.returncode
        if ended is None:
            ended = "exited" if returncode >= 0 else "signal"
        text = {n: (None if p else _read(outs[n])) for n, p in (("stdout", stdout_path), ("stderr", stderr_path))}
    finally:
        for f in outs.values():
            f.close()
    shown = (text["stdout"] or "") + (text["stderr"] or "")
    shown += "".join(_tail(p) for p in (stdout_path, stderr_path) if p)
    shown += "".join(_tail(p) for p in progress or ())
    marker = next((m for m in stop_markers or () if m and m in shown), None)
    return {"argv": list(argv), "n_processes": n_processes, "returncode": returncode, "ended": ended, "signal": _signal_name(returncode),
            "gave_up": gave_up, "running_s": round(running_s, 3), "paused_s": round(paused_s, 3),
            "budget_s": budget_s, "stall_s": stall_s, "stop_marker": marker,
            "stdout": text["stdout"], "stderr": text["stderr"], "stdout_path": stdout_path, "stderr_path": stderr_path}


def stopped(result):
    """Whether the run was stopped rather than failed: the call gave up and stopped it, or a stop signal or one of the
    adapter's stop markers ended it."""
    return bool(result.get("gave_up") or result.get("signal") in STOP_SIGNALS or result.get("stop_marker")
                or result.get("ended") in ("stopped_by_call", "killed_by_call"))


def stop_error(tool, result, resumes_from=None):
    """The error contract of a stopped run, or None where the run was not stopped. A stop is retryable: calling again
    resumes from resumes_from where that file exists, and starts over where it does not; the evidence says which."""
    if not stopped(result):
        return None
    import run_tool   # here, not at the top: run_tool loads the adapter that imports this module
    category = "timeout" if result.get("gave_up") else "cancelled"
    e = run_tool.error_template(tool, category)
    resumable = bool(resumes_from) and os.path.exists(resumes_from)
    if result.get("gave_up"):
        why = ("the call gave up on the engine after %s s of running time (%s; %s s while it was paused were not counted) "
               "and stopped it with TERM; it %s" % (
                   result.get("running_s"),
                   "its budget of %s s" % result.get("budget_s") if result["gave_up"] == "budget"
                   else "no progress file changed for %s s of running time" % result.get("stall_s"),
                   result.get("paused_s"),
                   "exited after the TERM" if result.get("ended") == "stopped_by_call" else "was killed when it did not exit after the TERM"))
    else:
        why = "the engine was stopped from outside (%s) after %s s of running time and %s s paused" % (
            result.get("signal") or "its output shows %r" % result.get("stop_marker"), result.get("running_s"), result.get("paused_s"))
    e["code"] = "%s-%s" % (tool.upper(), "GAVE-UP" if result.get("gave_up") else "STOPPED")
    e["category"] = category
    e["message"] = why + "; it did not fail, and a call made again %s" % (
        "resumes from its checkpoint" if resumable else "starts over, since no checkpoint was found")
    e["retryable"] = True
    e["remediation"] = {"action": "call the tool again with the same input" + (
        ": it resumes from %s" % resumes_from if resumable else ""),
        "note": "a stop is not a fault of the engine or of the input; the run's results so far are the engine's to report"}
    evidence = {k: result.get(k) for k in ("argv", "n_processes", "returncode", "ended", "signal", "gave_up", "running_s", "paused_s",
                                           "budget_s", "stall_s", "stop_marker", "stdout_path", "stderr_path")}
    for k in ("stdout", "stderr"):
        if result.get(k):
            evidence[k + "_tail"] = result[k][-TAIL:]
    evidence.update(resumable=resumable, resumes_from=resumes_from)
    e["evidence"] = evidence
    return e
