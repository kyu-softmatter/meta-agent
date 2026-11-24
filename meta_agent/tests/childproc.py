"""What a test needs to start a child process alike on Windows, macOS and Linux (failure line office-6).

Three things differ on Windows, and each made a template test fail there while it passed on the Mac and in WSL:

- a Python started with an environment that lacks SYSTEMROOT stops before it runs anything ("failed to get random
  numbers"), so a test that gives a child a bare environment keeps SYSTEMROOT, and PATHEXT, by which Windows finds a
  program on PATH;
- a program on PATH is found by its extension, so an installer's stand-in is a .cmd there and a shell script elsewhere;
- Claude Code runs a hook's command in Git for Windows' bash, not in cmd.exe, which is what subprocess's shell=True
  starts, so a test of a hook runs the command in that bash.
"""
import os
import shutil
import subprocess
import unittest

WINDOWS = os.name == "nt"
KEPT_ON_WINDOWS = ("SYSTEMROOT", "PATHEXT")


def bare_env(**values):
    """An environment holding only `values`, and on Windows what a child process needs there to start at all."""
    env = {}
    if WINDOWS:
        for name in KEPT_ON_WINDOWS:
            if os.environ.get(name):
                env[name] = os.environ[name]
    env.update(values)
    return env


def stand_in(folder, name):
    """A program named `name` in `folder` that exits 0, made so that this platform finds it on PATH; its path."""
    if WINDOWS:
        path, text = os.path.join(folder, name + ".cmd"), "@exit /b 0\r\n"
    else:
        path, text = os.path.join(folder, name), "#!/bin/sh\nexit 0\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.chmod(path, 0o755)
    return path


def git_bash():
    """Git for Windows' bash.exe, found as Claude Code finds it (CLAUDE_CODE_GIT_BASH_PATH, else beside git), or None."""
    named = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if named and os.path.isfile(named):
        return named
    git = shutil.which("git")
    if not git:
        return None
    folder = os.path.dirname(os.path.realpath(git))
    for _ in range(3):                      # Git\cmd\git.exe or Git\mingw64\bin\git.exe; bash is Git\bin\bash.exe
        folder = os.path.dirname(folder)
        bash = os.path.join(folder, "bin", "bash.exe")
        if os.path.isfile(bash):
            return bash
    return None


def run_hook(command, **kwargs):
    """Run a hook's command as Claude Code would on this platform: sh here, Git for Windows' bash on Windows."""
    if not WINDOWS:
        return subprocess.run(command, shell=True, **kwargs)
    bash = git_bash()
    if bash is None:
        raise unittest.SkipTest("no Git for Windows bash on this computer, in which Claude Code runs a hook's command")
    return subprocess.run([bash, "-c", command], **kwargs)
