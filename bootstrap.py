#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""bootstrap.py -- set up, on one computer, the external tools this repository calls (tools.lock.json).

  python bootstrap.py check                      read-only: what is here, what is missing, the command for each gap
  python bootstrap.py install node [--yes]       the pinned Node.js from nodejs.org, checked against the lock's SHA-256
  python bootstrap.py install rea [--yes]        the pinned rea-agents into that Node, install scripts not run
  python bootstrap.py install harness2 [--yes]   Linux or WSL only: the pinned harness2 commit with a Python 3.12 venv
  python bootstrap.py run rea [ARGS ...]         REA with the pinned Node; .mcp.json calls `run rea mcp`
  python bootstrap.py selftest                   offline checks of this script

Nothing is vendored: each tool comes from its own source at the version the lock names, and lands for the
current user under the tools home (tools.lock.json), outside the repository. Without --yes an install prints
its plan and changes nothing. This script never edits PATH, a shell profile, the registry or an agent's
configuration, never enables a Windows feature, never installs WSL and never asks for a password; those
steps stay with the person. Standard library only, Python 3.9 or later.
"""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
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


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
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
