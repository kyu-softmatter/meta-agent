#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bootstrap.py -- set up, on one computer, the external tools this repository calls (tools.lock.json).

  python bootstrap.py check                      read-only: what is here, what is missing, the command for each gap
  python bootstrap.py install node [--yes]       the pinned Node.js from nodejs.org, checked against the lock's SHA-256
  python bootstrap.py install rea [--yes]        the pinned rea-agents into that Node, install scripts not run
  python bootstrap.py install harness2 [--yes]   Linux or WSL only: the pinned harness2 commit with a Python 3.12 venv
  python bootstrap.py run rea [ARGS ...]         REA with the pinned Node; .mcp.json calls `run rea mcp`
  python bootstrap.py selftest                   offline checks of this script
  python bootstrap.py seat [ROLE] [--machine TAG] [--task ID] [--write]
                                                 the next free seat name for this computer and its entry for
                                                 contracts/seats.json (plan.md 9); with no ROLE, the table's
                                                 default role (meta, the person 2026-11-18); --write adds the
                                                 entry under a lock in the git dir (seat.lock); a name found in
                                                 tracked files or in git history's committers is skipped;
                                                 META_AGENT_SEAT_LOCK_WAIT sets how long the lock is awaited
  python bootstrap.py machine TAG DESCRIPTION [--write]
                                                 the tag the person of this copy gives this computer: added to
                                                 the machines of contracts/seats.json and to this clone's git
                                                 configuration (meta-agent.machine), before its first seat

Nothing is vendored: each tool comes from its own source at the version the lock names, and lands for the
current user under the tools home (tools.lock.json), outside the repository. Without --yes an install prints
its plan and changes nothing. This script never edits PATH, a shell profile, the registry or an agent's
configuration, never enables a Windows feature, never installs WSL and never asks for a password; those
steps stay with the person. Standard library only, Python 3.9 or later.
"""
import contextlib
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK_PATH = os.path.join(HERE, "tools.lock.json")
IS_WINDOWS = sys.platform == "win32"


def load_lock(path=LOCK_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------- where things go
def platform_key(system=None, machine=None):
    system = system or sys.platform
    machine = (machine or platform.machine()).lower()
    os_key = "win" if system == "win32" else "darwin" if system == "darwin" else "linux" if system.startswith("linux") else None
    arch = {"amd64": "x64", "x86_64": "x64", "x64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine)
    if not os_key or not arch:
        raise SystemExit("unsupported platform %s/%s" % (system, machine))
    return "%s-%s" % (os_key, arch)


def tools_home(lock):
    if os.environ.get(lock["tools_home"]["override"]):
        return os.environ[lock["tools_home"]["override"]]
    if IS_WINDOWS:
        return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local"), "Programs")
    return os.path.expanduser("~/.local/opt")


def node_dir(lock, key=None):
    return os.path.join(tools_home(lock), "node-%s-%s" % (lock["node"]["version"], key or platform_key()))


def node_exe(ndir):
    return os.path.join(ndir, "node.exe") if IS_WINDOWS else os.path.join(ndir, "bin", "node")


def node_modules(ndir):
    return os.path.join(ndir, "node_modules") if IS_WINDOWS else os.path.join(ndir, "lib", "node_modules")


def node_env(ndir):
    env = dict(os.environ)
    bindir = ndir if IS_WINDOWS else os.path.join(ndir, "bin")
    env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
    return env


def rea_script(ndir):
    return os.path.join(node_modules(ndir), "rea-agents", "scripts", "rea.mjs")


def rea_version(ndir):
    p = os.path.join(node_modules(ndir), "rea-agents", "package.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("version")
    except (OSError, ValueError):
        return None


def harness2_dir(lock):
    return os.path.join(tools_home(lock), "harness2-%s" % lock["harness2"]["commit"][:7])


# ---------------------------------------------------------------------------- checked downloads
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def python_has_https():
    try:
        import ssl  # noqa: F401
    except ImportError:
        return False
    return "https" in getattr(urllib.request, "__all__", []) or hasattr(urllib.request, "HTTPSHandler")


def download(url, dest):
    """urllib when this Python has working TLS, else the curl that Windows 10+, macOS and Linux ship.
    The checksum in the lock is what makes either one trustworthy."""
    if python_has_https():
        req = urllib.request.Request(url, headers={"User-Agent": "meta-agent-bootstrap/0.1"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        print("  downloaded with Python")
        return
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        raise SystemExit("this Python has no TLS and no curl was found; download %s by hand into %s" % (url, dest))
    run([curl, "-sSfL", "--retry", "2", "-o", dest, url])
    print("  downloaded with curl (this Python has no TLS)")


def safe_members(names, root):
    """Refuse an archive with an absolute path or one that climbs out of root."""
    root = os.path.abspath(root)
    for n in names:
        if n.startswith(("/", "\\")) or ":" in n.split("/")[0] or ".." in n.replace("\\", "/").split("/"):
            raise SystemExit("refused: archive entry %r leaves the destination" % n)
        if not os.path.abspath(os.path.join(root, n)).startswith(root):
            raise SystemExit("refused: archive entry %r leaves the destination" % n)


def extract(archive, dest):
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            safe_members(z.namelist(), dest)
            z.extractall(dest)
    else:
        with tarfile.open(archive) as t:
            members = t.getmembers()
            safe_members([m.name for m in members], dest)
            for m in members:
                if m.issym() or m.islnk():
                    if os.path.isabs(m.linkname):
                        raise SystemExit("refused: archive link %r points to an absolute path" % m.name)
                    base = os.path.dirname(m.name) if m.issym() else ""
                    target = os.path.normpath(os.path.join(base, m.linkname)).replace("\\", "/")
                    safe_members([target], dest)
            if hasattr(tarfile, "data_filter"):
                t.extractall(dest, filter="data")
            else:
                t.extractall(dest)


def run(cmd, env=None, cwd=None):
    print("  $ " + " ".join(cmd))
    p = subprocess.run(cmd, env=env, cwd=cwd)
    if p.returncode != 0:
        raise SystemExit("failed (exit %d): %s" % (p.returncode, " ".join(cmd)))


def capture(cmd, env=None, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    out = p.stdout
    if out[:2] in (b"\xff\xfe", b"\xfe\xff") or (len(out) > 1 and out[1:2] == b"\x00"):
        text = out.decode("utf-16-le", errors="replace")
    else:
        text = out.decode("utf-8", errors="replace")
    return p.returncode, text.replace("\x00", "").strip()


# ---------------------------------------------------------------------------- install
def install_node(lock, yes):
    key = platform_key()
    spec = lock["node"]["archives"].get(key)
    if not spec:
        raise SystemExit("the lock has no Node archive for %s" % key)
    ndir = node_dir(lock, key)
    url = lock["node"]["base_url"] + spec["file"]
    print("node %s for %s" % (lock["node"]["version"], key))
    print("  from   %s" % url)
    print("  sha256 %s" % spec["sha256"])
    print("  into   %s" % ndir)
    if os.path.exists(node_exe(ndir)):
        print("  already installed: %s" % capture([node_exe(ndir), "-v"])[1])
        return ndir
    if not yes:
        print("  plan only; add --yes to download, check and extract")
        return None
    tmp = tempfile.mkdtemp(prefix="meta-agent-node-")
    try:
        archive = os.path.join(tmp, spec["file"])
        download(url, archive)
        got = sha256_file(archive)
        if got != spec["sha256"]:
            raise SystemExit("refused: sha256 %s does not match the lock" % got)
        print("  sha256 matches the lock")
        os.makedirs(tools_home(lock), exist_ok=True)
        extract(archive, tools_home(lock))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    code, version = capture([node_exe(ndir), "-v"])
    if version != lock["node"]["version"]:
        raise SystemExit("node -v printed %r, not %s" % (version, lock["node"]["version"]))
    print("  installed: node %s" % version)
    return ndir


def npm_cli(ndir):
    return os.path.join(node_modules(ndir), "npm", "bin", "npm-cli.js")


def install_rea(lock, yes):
    ndir = node_dir(lock)
    want = lock["rea"]["version"]
    print("rea %s@%s into %s" % (lock["rea"]["package"], want, ndir))
    if not os.path.exists(node_exe(ndir)):
        raise SystemExit("Node %s is not installed: run python bootstrap.py install node --yes" % lock["node"]["version"])
    have = rea_version(ndir)
    if have == want:
        print("  already installed: rea %s" % have)
        return
    if not yes:
        print("  plan only; add --yes to run npm install -g %s@%s (install scripts are not run)" % (lock["rea"]["package"], want))
        return
    run([node_exe(ndir), npm_cli(ndir), "install", "-g", "--prefix", ndir, "--no-fund", "--no-audit",
         "--ignore-scripts", "--registry", lock["rea"]["registry"], "%s@%s" % (lock["rea"]["package"], want)],
        env=node_env(ndir))
    code, out = capture([node_exe(ndir), rea_script(ndir), "--version"], env=node_env(ndir))
    if out.strip().splitlines()[-1:] != [want]:
        raise SystemExit("rea --version printed %r, not %s" % (out, want))
    print("  installed: rea %s" % want)


def find_uv():
    found = shutil.which("uv")
    if found:
        return found
    local = os.path.expanduser("~/.local/bin/uv")
    return local if os.path.exists(local) else None


def install_harness2(lock, yes):
    spec = lock["harness2"]
    hdir = harness2_dir(lock)
    print("harness2 %s into %s" % (spec["commit"][:12], hdir if not IS_WINDOWS else "a WSL distribution"))
    if not sys.platform.startswith("linux"):
        repo = HERE.replace("\\", "/")
        wsl_path = "/mnt/%s%s" % (repo[0].lower(), repo[2:]) if len(repo) > 2 and repo[1] == ":" else repo
        print("  harness2 runs on Linux only. Inside a WSL distribution, run:")
        print("    wsl -d <distribution> -- python3 %s/bootstrap.py install harness2 --yes" % wsl_path)
        return
    uv = find_uv()
    if os.path.exists(os.path.join(hdir, ".venv")):
        print("  already installed")
        return
    if not uv:
        raise SystemExit("uv is not installed here; install it (https://docs.astral.sh/uv/) and run this again")
    if not yes:
        print("  plan only; add --yes to clone %s at %s and build a Python %s venv with %s" % (
            spec["repository"], spec["commit"][:12], spec["python"], uv))
        return
    if not os.path.exists(hdir):
        run(["git", "clone", "--quiet", spec["repository"], hdir])
    run(["git", "-C", hdir, "checkout", "--quiet", spec["commit"]])
    run([uv, "venv", "--python", spec["python"], os.path.join(hdir, ".venv")], cwd=hdir)
    target = "." + ("[%s]" % ",".join(spec["extras"]) if spec["extras"] else "")
    run([uv, "pip", "install", "--python", os.path.join(hdir, ".venv", "bin", "python"), "-e", target], cwd=hdir)
    print("  installed; the local demo needs no model account: %s/.venv/bin/harness2-demo --output runs/demo --k 1" % hdir)


# ---------------------------------------------------------------------------- check
def check(lock):
    rows = []
    key = platform_key()
    rows.append(("platform", "ok", "%s, Python %s" % (key, platform.python_version())))
    code, hooks = capture(["git", "-C", HERE, "config", "core.hooksPath"])
    rows.append(("git hooks", "ok" if hooks == "contracts/hooks" else "missing",
                 hooks or "git config core.hooksPath contracts/hooks"))
    ndir = node_dir(lock, key)
    if os.path.exists(node_exe(ndir)):
        rows.append(("node", "ok", "%s at %s" % (capture([node_exe(ndir), "-v"])[1], ndir)))
    else:
        rows.append(("node", "missing", "python bootstrap.py install node --yes"))
    have = rea_version(ndir) if os.path.exists(node_exe(ndir)) else None
    if have == lock["rea"]["version"]:
        rows.append(("rea", "ok", "%s (install scripts not run)" % have))
    else:
        rows.append(("rea", "missing" if not have else "other version %s" % have, "python bootstrap.py install rea --yes"))
    try:
        mcp = load_lock(os.path.join(HERE, ".mcp.json")).get("mcpServers", {})
        rows.append(("mcp: rea", "ok" if "rea" in mcp else "missing", ".mcp.json at the repository root"))
    except (OSError, ValueError):
        rows.append(("mcp: rea", "missing", ".mcp.json at the repository root"))
    if IS_WINDOWS:
        code, status = capture(["wsl.exe", "--status"])
        code2, names = capture(["wsl.exe", "-l", "-q"])
        distros = [n.strip() for n in names.splitlines() if n.strip()] if code2 == 0 else []
        if code == 0 and distros:
            rows.append(("wsl", "ok", "distributions: " + ", ".join(distros)))
        else:
            rows.append(("wsl", "missing", "the person installs it: wsl --install (administrator, then a restart)"))
        rows.append(("harness2", "inside WSL", "wsl -d <distribution> -- python3 <repo>/bootstrap.py check"))
    elif sys.platform.startswith("linux"):
        hdir = harness2_dir(lock)
        ok = os.path.exists(os.path.join(hdir, ".venv"))
        rows.append(("harness2", "ok" if ok else "missing", hdir if ok else "python3 bootstrap.py install harness2 --yes"))
        rows.append(("uv", "ok" if find_uv() else "missing", find_uv() or "https://docs.astral.sh/uv/"))
    width = max(len(r[0]) for r in rows)
    for name, state, detail in rows:
        print("%-*s  %-12s %s" % (width, name, state, detail))
    missing = [r for r in rows if r[1] not in ("ok", "inside WSL")]
    print("check: %d item(s), %d to do" % (len(rows), len(missing)))
    return 0


# ---------------------------------------------------------------------------- run
def run_rea(lock, args):
    ndir = node_dir(lock)
    if not os.path.exists(rea_script(ndir)):
        sys.stderr.write("REA is not installed for this user: python bootstrap.py install node --yes, "
                         "then python bootstrap.py install rea --yes\n")
        return 2
    return subprocess.call([node_exe(ndir), rea_script(ndir)] + list(args), env=node_env(ndir))


# ---------------------------------------------------------------------------- selftest
def selftest(lock):
    n = 0
    assert platform_key("win32", "AMD64") == "win-x64"; n += 1
    assert platform_key("linux", "aarch64") == "linux-arm64"; n += 1
    assert platform_key("darwin", "arm64") == "darwin-arm64"; n += 1
    for key in ("win-x64", "linux-x64", "darwin-arm64"):
        spec = lock["node"]["archives"][key]
        assert spec["file"].startswith("node-%s-%s." % (lock["node"]["version"], key)) and len(spec["sha256"]) == 64; n += 1
    tmp = tempfile.mkdtemp(prefix="meta-agent-selftest-")
    try:
        p = os.path.join(tmp, "a.txt")
        with open(p, "wb") as f:
            f.write(b"meta-agent\n")
        assert sha256_file(p) == hashlib.sha256(b"meta-agent\n").hexdigest(); n += 1
        bad = os.path.join(tmp, "bad.zip")
        with zipfile.ZipFile(bad, "w") as z:
            z.writestr("../escape.txt", "x")
        try:
            extract(bad, os.path.join(tmp, "out"))
            raise AssertionError("an archive entry outside the destination was extracted")
        except SystemExit as e:
            assert "refused" in str(e); n += 1
        good = os.path.join(tmp, "good.zip")
        with zipfile.ZipFile(good, "w") as z:
            z.writestr("node-x/inside.txt", "x")
        extract(good, os.path.join(tmp, "out"))
        assert os.path.exists(os.path.join(tmp, "out", "node-x", "inside.txt")); n += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert lock["rea"]["version"] and lock["harness2"]["commit"] and len(lock["harness2"]["commit"]) == 40; n += 1
    print("selftest: %d checks OK" % n)
    return 0


SEAT_LOCK_WAIT = 10.0   # seconds a --write waits for another one's lock; META_AGENT_SEAT_LOCK_WAIT overrides it


def seat_names_elsewhere(root, role, machine, yyyymmdd):
    """Seat names of this role, machine and date used outside contracts/seats.json: in tracked files (a record
    naming a seat of a test clone) and in the committer lines of git history. Returns (names, None), or
    (set(), why) when git could not be asked, and then the table alone decides."""
    if not (re.match(r"^[a-z]+$", role or "") and re.match(r"^[a-z]+$", machine or "") and re.match(r"^[0-9]{8}$", yyyymmdd)):
        return set(), "the role, machine or date is not a plain seat-name part"
    stem = "%s-%s-%s-" % (role, machine, yyyymmdd)
    code, grep = capture(["git", "grep", "-h", "-o", "-w", "-I", "-E", stem + "[1-9][0-9]*"], cwd=root)
    if code not in (0, 1):
        return set(), "git grep did not run (%s)" % ("git not found" if code is None else "exit %d" % code)
    code, log = capture(["git", "log", "--all", "--format=%cn%n%ce"], cwd=root)
    if code != 0:
        return set(), "git log did not run (%s)" % ("git not found" if code is None else "exit %d" % code)
    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(stem) + r"[1-9][0-9]*(?![0-9])")
    return set(pattern.findall(grep + "\n" + log)), None


def seat_lock_path(root):
    """The lock file for the read-modify-write of contracts/seats.json: inside the git dir, so it is never a
    file of the working copy; outside git, in the temporary folder, keyed by this repository's path."""
    code, out = capture(["git", "rev-parse", "--git-path", "seat.lock"], cwd=root)
    if code == 0 and out:
        return os.path.normpath(os.path.join(root, out))
    key = hashlib.sha256(os.path.abspath(root).encode("utf-8")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), "meta-agent-seat-%s.lock" % key)


@contextlib.contextmanager
def seat_lock(path, wait):
    """Hold path, created exclusively (O_CREAT|O_EXCL works on macOS, Linux and Windows), for the block; wait
    up to `wait` seconds for another holder, then refuse. Only a lock this call created is removed."""
    deadline = time.monotonic() + wait
    busy = (FileExistsError, PermissionError) if IS_WINDOWS else (FileExistsError,)
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except busy:
            if time.monotonic() >= deadline:
                try:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        holder = f.read().strip() or "nothing recorded"
                except OSError:
                    holder = "unreadable"
                raise SystemExit("seat: another `bootstrap.py seat --write` holds the lock %s (waited %.1f s; it "
                                 "records: %s). Nothing was written. Run again when it is done; if no such command "
                                 "is running, the lock is stale: remove that file and run again." % (path, wait, holder))
            time.sleep(0.1)
    try:
        import datetime
        os.write(fd, ("pid %d, %s\n" % (os.getpid(), datetime.datetime.now().isoformat(timespec="seconds"))).encode("utf-8"))
        os.close(fd)
        yield
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def seat(rest):
    """Name the next seat of a role on this computer and print its entry (the standing rule of 2026-11-09).

    A name is never reissued: besides contracts/seats.json, names of the same role, machine and date in tracked
    files and in git history's committer lines are skipped. With --write the table is re-read and the name
    chosen under an exclusive lock, so two sessions seating at once take two names."""
    import datetime
    sys.path.insert(0, os.path.join(HERE, "contracts", "tools"))
    import seats as seat_rules
    args = {"--machine": None, "--task": None}
    write = "--write" in rest
    rest = [r for r in rest if r != "--write"]
    role = None
    i = 0
    while i < len(rest):
        if rest[i] in args and i + 1 < len(rest):
            args[rest[i]] = rest[i + 1]
            i += 2
        elif role is None and not rest[i].startswith("-"):
            role = rest[i]
            i += 1
        else:
            raise SystemExit("seat: unexpected argument %r" % rest[i])
    table = seat_rules.load()
    roles = sorted(table.get("roles", {}))
    by_default = role is None
    if by_default:
        role = table.get("default_role")
        if not role:
            raise SystemExit("seat: no role is named and contracts/seats.json names no default role; name one of %s"
                             % ", ".join(roles))
    if role not in roles:
        raise SystemExit("seat: role %r is not one of %s; a new role is the person's" % (role, ", ".join(roles)))
    machine = args["--machine"]
    if machine is None:
        machine = capture(["git", "config", "--get", "meta-agent.machine"], cwd=HERE)[1].strip() or None
    if machine is None:
        raise SystemExit("seat: this clone has no machine tag. If this computer has one (known: %s), record it once: "
                         "git config meta-agent.machine <tag>, or pass --machine. If it is a new computer, the person "
                         "gives it a tag: python bootstrap.py machine <tag> \"<which computer>\" --write"
                         % ", ".join(sorted(table.get("machines", {}))))
    if machine not in table.get("machines", {}):
        raise SystemExit("seat: machine tag %r is not in contracts/seats.json; the person gives a new computer "
                         "its tag before its first seat (known: %s)" % (machine, ", ".join(sorted(table.get("machines", {})))))
    today = datetime.date.today()
    yyyymmdd = today.strftime("%Y%m%d")
    seated = "%s, self-registered%s" % (today.isoformat(), " for tasks/%s" % args["--task"] if args["--task"] else "")

    def choose(table):
        elsewhere, why = seat_names_elsewhere(HERE, role, machine, yyyymmdd)
        name = seat_rules.next_name(table, role, machine, yyyymmdd, also_used=elsewhere)
        entry = seat_rules.entry_for(table, name, "self, under the person's standing rule of 2026-11-09 "
                                     "(docs/ideas/20261109.md)", seated)
        problems = seat_rules.entry_problems(table, entry)
        if problems:
            raise SystemExit("seat: " + "; ".join(problems))
        print("seat      %s" % name)
        print("committer seat:%s <%s>" % (name, entry["committer_email"]))
        print("entry     %s" % json.dumps(entry, ensure_ascii=False))
        if by_default:
            print("role      %s, the default role: none was named (the person, 2026-11-18; a role the person or "
                  "the task names holds over it)" % role)
        in_table = {s.get("seat") for s in table.get("seats", [])}
        skipped = sorted(elsewhere - in_table, key=lambda n: seat_rules.parse_name(n)[3])
        if skipped:
            print("skipped   %s (used outside contracts/seats.json: tracked files or git history)" % ", ".join(skipped))
        if why:
            print("note      %s; the name is checked against contracts/seats.json alone" % why)
        return name, entry

    if write:
        try:
            wait = float(os.environ.get("META_AGENT_SEAT_LOCK_WAIT", SEAT_LOCK_WAIT))
        except ValueError:
            raise SystemExit("seat: META_AGENT_SEAT_LOCK_WAIT is not a number of seconds")
        with seat_lock(seat_lock_path(HERE), wait):
            table = seat_rules.load()       # re-read: another session may have written its entry meanwhile
            name, entry = choose(table)
            table["seats"].append(entry)
            with open(seat_rules.SEATS_PATH, "w", encoding="utf-8") as f:
                f.write(seat_rules.dump(table))
        print("written   contracts/seats.json (this entry only). Register it in its own commit before any other work:")
    else:
        name, entry = choose(table)
        print("nothing written. With --write the entry is added; then register it in its own commit:")
    print('  python contracts/tools/seat_commit.py --seat %s -m "contracts/seats: %s seats itself" contracts/seats.json'
          % (name, name))
    return 0


def machine(rest):
    """Record the tag the person of this copy gives this computer (the person, 2026-11-18).

    A new computer's tag is the person's word; on a copy made for someone else, that someone is the person of the
    copy. The tag goes into the machines of contracts/seats.json, in a commit of its own before the computer's
    first seat (a self-registration is judged against the table before it, so the tag must already stand), and
    into this clone's git configuration. A session runs this only with the tag and the words the person gave."""
    sys.path.insert(0, os.path.join(HERE, "contracts", "tools"))
    import seats as seat_rules
    write = "--write" in rest
    rest = [r for r in rest if r != "--write"]
    if len(rest) != 2 or not rest[1].strip():
        raise SystemExit('machine: give the tag and which computer it is, in the person\'s words: '
                         'python bootstrap.py machine <tag> "<which computer>" [--write]')
    tag, description = rest[0], rest[1].strip()
    if not re.match(r"^[a-z]+$", tag):
        raise SystemExit("machine: a tag is lower-case letters only, as a seat name's part (%r is not)" % tag)
    table = seat_rules.load()
    machines = table.setdefault("machines", {})
    if tag in machines:
        raise SystemExit("machine: %r is already the tag of %s; a tag is never given twice" % (tag, machines[tag]))
    print("machine   %s: %s" % (tag, description))
    if not write:
        print("nothing written. With --write the tag is added to contracts/seats.json and to this clone's git "
              "configuration.")
        return 0
    machines[tag] = description
    with open(seat_rules.SEATS_PATH, "w", encoding="utf-8") as f:
        f.write(seat_rules.dump(table))
    code, _ = capture(["git", "config", "meta-agent.machine", tag], cwd=HERE)
    if code != 0:
        raise SystemExit("machine: contracts/seats.json is written, but git config meta-agent.machine %s failed; "
                         "run it by hand" % tag)
    print("written   contracts/seats.json (this tag only) and git config meta-agent.machine %s" % tag)
    print("Commit contracts/seats.json in its own commit, before this computer's first seat:")
    print('  git commit -m "contracts/seats: the person gives this computer the tag %s" contracts/seats.json' % tag)
    print("then seat:  python bootstrap.py seat --write")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["seat"]:
        return seat(argv[1:])
    if argv[:1] == ["machine"]:
        return machine(argv[1:])
    lock = load_lock()
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "check":
        return check(lock)
    if cmd == "selftest":
        return selftest(lock)
    if cmd == "run" and rest[:1] == ["rea"]:
        return run_rea(lock, rest[1:])
    if cmd == "install" and rest:
        yes = "--yes" in rest
        installers = {"node": install_node, "rea": install_rea, "harness2": install_harness2}
        tools = [r for r in rest if r != "--yes"]
        unknown = [t for t in tools if t not in installers]
        if unknown or not tools:
            raise SystemExit("unknown tool(s) %s; known: %s" % (", ".join(unknown) or "none", ", ".join(installers)))
        for tool in tools:
            installers[tool](lock, yes)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
