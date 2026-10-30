"""S0 Step 0: environment discovery (plan.md 5.0).

Reads the repositories and folders the person named with ordinary tools
(file listing, text search) and writes a `discovery_report`: every field
of the lab profile either `inferred` with evidence or `unknown`. Nothing
here infers a policy field, and nothing here executes what it reads.
"""
import json
import os
import re
import subprocess

from . import cards
from .bank import FIELDS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONTRACTS = os.path.join(ROOT, "contracts")

SKIP_DIRS = {".git", ".pixi", ".venv", "venv", "node_modules", "__pycache__", ".agent",
             ".mypy_cache", ".ruff_cache", ".pytest_cache", ".tox", ".eggs", "dist", "build"}
TEXT_EXT = {".py", ".toml", ".yml", ".yaml", ".md", ".json", ".txt", ".sh", ".slurm", ".sbatch",
            ".cfg", ".ini", ".js", ".ts", ".cpp", ".hpp", ".c", ".h", ".f90", ".f", ".jl", ".R"}
CODE_EXT = {".py", ".js", ".ts", ".cpp", ".hpp", ".c", ".h", ".f90", ".f", ".jl", ".R", ".sh"}
CONFIG_NAMES = {"pyproject.toml", "pixi.toml", "environment.yml", "environment.yaml",
                "requirements.txt", "package.json", "Dockerfile", "Makefile", "CMakeLists.txt"}
DATA_EXT = {".csv", ".h5", ".hdf5", ".gsd", ".npz", ".npy", ".parquet", ".tsv"}
DATA_DIRS = {"data", "datasets", "runs", "results", "measurements"}
WORKFLOW_DIRS = {"replay", "validation", "tests", "workflows"}
MAX_READ = 512 * 1024

# registry id -> pattern in code and configuration files (not in prose)
ENGINE_ALIASES = {
    "hoomd_blue": r"\bhoomd\b",
    "lammps": r"\blammps\b",
    "gromacs": r"\bgromacs\b|\bgmx\b",
    "openmm": r"\bopenmm\b",
    "openfoam": r"\bopenfoam\b|\bsimpleFoam\b|\bpimpleFoam\b|\bfoamRun\b|\bblockMesh\b",
    "rheotool": r"\brheoTool\b|\brheoFoam\b",
    "fenicsx": r"\bdolfinx\b|\bfenics\b",
    "quantum_espresso": r"\bpw\.x\b|quantum.?espresso",
    "cp2k": r"\bcp2k\b",
    "vasp": r"\bvasp\b",
}
INSTRUMENT_KEYWORDS = {"microscope": "sma_microscope", "rheometer": "lab_rheometer"}
GPU_RE = re.compile(r"device\.GPU\(|--gres=gpu|nvidia-smi|torch\.cuda|\bcupy\b|cuda:\d", re.I)
HPC_RE = re.compile(r"#SBATCH|\bsbatch\b|#PBS\b|\bqsub\b")
PLATFORMS_RE = re.compile(r"platforms\s*=\s*\[([^\]]*)\]")
RUNS_ON_RE = re.compile(r"runs-on:\s*([\w.-]+)")
OS_TOKENS = [("osx", "macos"), ("macos", "macos"), ("win", "windows"), ("linux", "linux"), ("ubuntu", "linux")]
LICENSE_RE = [
    (re.compile(r"\bMIT License\b", re.I), "MIT"),
    (re.compile(r"Apache License", re.I), "Apache-2.0"),
    (re.compile(r"GNU GENERAL PUBLIC LICENSE", re.I), "GPL"),
    (re.compile(r"GNU LESSER GENERAL PUBLIC", re.I), "LGPL"),
    (re.compile(r"BSD", re.I), "BSD"),
]


def load_registry(name):
    try:
        return cards.load_json(os.path.join(CONTRACTS, "registry", name + ".json"))
    except (OSError, ValueError):
        return {}


class Source(object):
    """One input: a repository or a folder, read-only."""

    def __init__(self, path, name=None, url=None, commit=None, kind="folder"):
        self.path = os.path.abspath(path)
        self.name = name or os.path.basename(self.path.rstrip("/\\"))
        self.url = url
        self.kind = kind
        self.commit = commit or (git_commit(self.path) if kind == "repo" else None)
        self.files = []
        self._text = {}
        self._walk()

    @property
    def ref(self):
        if self.kind == "repo" and self.commit:
            return "repo_%s@%s" % (self.name, self.commit)
        return "%s_%s" % (self.kind, self.name)

    def _walk(self):
        for dirpath, dirnames, filenames in os.walk(self.path):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, self.path).replace(os.sep, "/")
                self.files.append(rel)
                if len(self.files) > 20000:
                    return

    def text(self, rel):
        if rel not in self._text:
            full = os.path.join(self.path, rel)
            try:
                if os.path.getsize(full) > MAX_READ:
                    self._text[rel] = ""
                else:
                    with open(full, "r", encoding="utf-8", errors="replace") as f:
                        self._text[rel] = f.read()
            except OSError:
                self._text[rel] = ""
        return self._text[rel]

    def has(self, rel):
        return rel in self.files

    def ev(self, locus, note=None):
        e = {"source_ref": self.ref, "locus": locus}
        if note:
            e["note"] = note
        return e

    def code_and_config(self):
        for rel in self.files:
            base = os.path.basename(rel)
            ext = os.path.splitext(rel)[1]
            if base in CONFIG_NAMES or ext in (CODE_EXT | {".toml", ".yml", ".yaml", ".cfg", ".ini", ".slurm", ".sbatch", ".txt"}):
                yield rel


def git_commit(path):
    try:
        p = subprocess.run(["git", "-C", path, "rev-parse", "--short=7", "HEAD"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None


class Found(object):
    """Accumulates inferred values and their evidence per field."""

    def __init__(self):
        self.values = {}
        self.evidence = {}
        self.notes = {}

    def add(self, field, value, evidence, note=None):
        if isinstance(value, list):
            cur = self.values.setdefault(field, [])
            for v in value:
                if v not in cur:
                    cur.append(v)
        else:
            self.values.setdefault(field, value)
        evs = self.evidence.setdefault(field, [])
        for e in evidence:
            if e not in evs and len(evs) < 6:
                evs.append(e)
        if note and field not in self.notes:
            self.notes[field] = note

    def stated(self, field):
        if field in self.values:
            leaf = {"value": self.values[field], "state": "inferred", "evidence": self.evidence[field]}
            if field in self.notes:
                leaf["note"] = self.notes[field]
            return leaf
        return {"value": None, "state": "unknown"}


def scan_source(src, found, materials_seen, engines_registry, instruments_registry):
    files = set(src.files)
    engine_methods = {e["id"]: e.get("methods", []) for e in engines_registry.get("engines", [])}
    instrument_ids = {i["id"] for i in instruments_registry.get("instruments", [])}

    # existing code
    code_files = [f for f in src.files if os.path.splitext(f)[1] in CODE_EXT]
    if code_files:
        found.add("existing_code", [src.url or src.path.replace(os.sep, "/")], [src.ev(code_files[0])])

    # language
    if "pyproject.toml" in files or "setup.py" in files or "requirements.txt" in files:
        locus = "pyproject.toml" if "pyproject.toml" in files else ("setup.py" if "setup.py" in files else "requirements.txt")
        found.add("software_env.language", ["python"], [src.ev(locus)])
    elif any(f.endswith(".py") for f in src.files):
        found.add("software_env.language", ["python"], [src.ev(next(f for f in src.files if f.endswith(".py")))])
    if "package.json" in files:
        found.add("software_env.language", ["javascript"], [src.ev("package.json")])
    elif any(f.endswith(".js") for f in src.files):
        found.add("software_env.language", ["javascript"], [src.ev(next(f for f in src.files if f.endswith(".js")))])
    for ext, lang in ((".ts", "typescript"), (".cpp", "c++"), (".f90", "fortran"), (".jl", "julia")):
        hit = next((f for f in src.files if f.endswith(ext)), None)
        if hit:
            found.add("software_env.language", [lang], [src.ev(hit)])

    # package manager
    if "pixi.toml" in files:
        found.add("software_env.package_manager", ["pixi"], [src.ev("pixi.toml")])
    elif "pyproject.toml" in files and "[tool.pixi" in src.text("pyproject.toml"):
        found.add("software_env.package_manager", ["pixi"], [src.ev("pyproject.toml")])
    elif "pixi.lock" in files:
        found.add("software_env.package_manager", ["pixi"], [src.ev("pixi.lock")])
    if "uv.lock" in files:
        found.add("software_env.package_manager", ["uv"], [src.ev("uv.lock")])
    if "environment.yml" in files or "environment.yaml" in files:
        found.add("software_env.package_manager", ["conda"], [src.ev("environment.yml" if "environment.yml" in files else "environment.yaml")])
    if "requirements.txt" in files:
        found.add("software_env.package_manager", ["pip"], [src.ev("requirements.txt")])
    if "package.json" in files:
        found.add("software_env.package_manager", ["npm"], [src.ev("package.json")])

    # operating systems: declared platforms and CI runners
    for cfg in ("pixi.toml", "pyproject.toml"):
        if cfg in files:
            for m in PLATFORMS_RE.finditer(src.text(cfg)):
                oses = []
                for tok in re.findall(r"[\w-]+", m.group(1)):
                    for key, name in OS_TOKENS:
                        if tok.lower().startswith(key) and name not in oses:
                            oses.append(name)
                if oses:
                    found.add("software_env.os", oses, [src.ev(cfg)])
    for wf in [f for f in src.files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]:
        oses = []
        for m in RUNS_ON_RE.finditer(src.text(wf)):
            for key, name in OS_TOKENS:
                if m.group(1).lower().startswith(key) and name not in oses:
                    oses.append(name)
        if oses:
            found.add("software_env.os", oses, [src.ev(wf)])

    # licence
    for lic in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
        if lic in files:
            head = src.text(lic)[:2000]
            label = "unrecognised licence text"
            for rx, name in LICENSE_RE:
                if rx.search(head):
                    label = name
                    break
            found.add("operational_constraints.licenses", ["%s (%s)" % (label, src.name)], [src.ev(lic)])
            break

    # existing agents, bridge
    agents = []
    if "contracts/seats.json" in files:
        try:
            seats = json.loads(src.text("contracts/seats.json"))
            for s in seats.get("seats", []):
                for o in s.get("owns", []) or []:
                    if o.endswith("_agent") and o not in agents:
                        agents.append(o)
        except ValueError:
            pass
        if agents:
            found.add("collaboration.existing_agents", agents, [src.ev("contracts/seats.json")])
    agent_dirs = sorted({f.split("/")[0] for f in src.files if "/" in f and f.split("/")[0].endswith("_agent")
                         and (f.split("/")[0] + "/CLAUDE.md") in files})
    for d in agent_dirs:
        if d not in agents:
            agents.append(d)
            found.add("collaboration.existing_agents", [d], [src.ev(d + "/CLAUDE.md")])
    if agents:
        found.add("collaboration.first_agent", False,
                  [src.ev("contracts/seats.json")] if "contracts/seats.json" in files else [src.ev(agent_dirs[0] + "/CLAUDE.md")])
    if any(f.startswith("bridge/") for f in src.files):
        found.add("collaboration.bridge", True, [src.ev("bridge/")])

    # engines, methods, GPU, HPC from code and configuration
    engine_hits = {}
    gpu_hits, hpc_hits, brownian_hits = [], [], []
    for rel in src.code_and_config():
        text = src.text(rel)
        if not text:
            continue
        for eid, pat in ENGINE_ALIASES.items():
            if re.search(pat, text):
                engine_hits.setdefault(eid, [])
                if len(engine_hits[eid]) < 3:
                    engine_hits[eid].append(rel)
        if GPU_RE.search(text) and len(gpu_hits) < 3:
            gpu_hits.append(rel)
        if HPC_RE.search(text) and len(hpc_hits) < 3:
            hpc_hits.append(rel)
        if re.search(r"\bBrownian\b", text) and len(brownian_hits) < 3:
            brownian_hits.append(rel)
    for eid, loci in sorted(engine_hits.items()):
        found.add("preferred_engines", [eid], [src.ev(l) for l in loci])
        if engine_methods.get(eid):
            found.add("conventions.methods", list(engine_methods[eid]), [src.ev(l) for l in loci[:1]])
    if brownian_hits:
        found.add("conventions.methods", ["bd_cg"], [src.ev(l) for l in brownian_hits])
    if engine_hits:
        found.add("conventions.research_kind", ["simulation"], [src.ev(loci[0]) for loci in list(engine_hits.values())[:2]])
        found.add("gui_preference", "parameter_form", [src.ev(loci[0]) for loci in list(engine_hits.values())[:1]],
                  note="a recommendation from the research kind and methods, not a reading of a preference; "
                       "a visual editor or reuse of the lab's own GUI are the alternatives")
    if gpu_hits:
        found.add("hardware.gpu", True, [src.ev(l) for l in gpu_hits])
    if hpc_hits:
        text = src.text(hpc_hits[0])
        found.add("hardware.hpc", "slurm" if "SBATCH" in text or "sbatch" in text else "pbs", [src.ev(l) for l in hpc_hits])
        found.add("software_env.os", ["linux"], [src.ev(hpc_hits[0], "a batch scheduler implies a Linux cluster")])

    # instruments from directory and agent names
    inst = []
    for name in agents + [f.split("/")[0] for f in src.files if "/" in f]:
        low = name.lower()
        for kw, rid in INSTRUMENT_KEYWORDS.items():
            if kw in low:
                value = rid if rid in instrument_ids else kw
                if value not in inst:
                    inst.append(value)
                    locus = name if name in agents or (name + "/") in {f.split("/")[0] + "/" for f in src.files} else name
                    found.add("preferred_instruments", [value], [src.ev(locus + "/" if not locus.endswith("/") else locus)])
    if inst:
        found.add("conventions.research_kind", ["experiment"], found.evidence.get("preferred_instruments", [])[:2])

    # data and workflows
    top_dirs = sorted({f.split("/")[0] for f in src.files if "/" in f})
    for d in top_dirs:
        if d in DATA_DIRS:
            found.add("existing_data", ["%s:%s/" % (src.name, d)], [src.ev(d + "/")])
        if d in WORKFLOW_DIRS:
            found.add("validated_workflows", ["%s:%s/" % (src.name, d)], [src.ev(d + "/")])
    data_file = next((f for f in src.files if os.path.splitext(f)[1] in DATA_EXT and f.split("/")[0] not in DATA_DIRS), None)
    if data_file:
        d = data_file.split("/")[0] if "/" in data_file else "."
        found.add("existing_data", ["%s:%s/" % (src.name, d)], [src.ev(data_file)])

    # unit conventions
    if "contracts/units.json" in files:
        text = src.text("contracts/units.json")
        found.add("conventions.unit_system", "SI, kelvin only" if "kelvin" in text.lower() else "SI (unit registry)",
                  [src.ev("contracts/units.json")])

    # the materials inbox of the lab, if it has one
    links = next((f for f in src.files if f.endswith("inbox/materials/LINKS.md")), None)
    if links:
        for row in src.text(links).splitlines():
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if not cells or not cells[0].startswith("http"):
                continue
            url = cells[0]
            if url not in materials_seen:
                materials_seen.append(url)
            name = cells[1] if len(cells) > 1 else ""
            role = cells[2].lower() if len(cells) > 2 else ""
            eid = next((k for k, pat in ENGINE_ALIASES.items() if re.search(pat, name or url, re.I)), None)
            if role == "engine" and eid:
                found.add("preferred_engines", [eid], [src.ev(links, url)])
            elif role == "instrument":
                found.add("preferred_instruments", [name.lower().replace(" ", "_") or url], [src.ev(links, url)])
    for f in src.files:
        if f.endswith("/MATERIAL.json") and "inbox/materials/" in f:
            try:
                mid = json.loads(src.text(f)).get("id")
            except ValueError:
                mid = None
            if mid and mid not in materials_seen:
                materials_seen.append(mid)


def discover(lab_id, sources, seat, now=None, note=None):
    """Run Step 0 over `sources` (a list of Source) and return the discovery_report card."""
    created = cards.now_iso(now)
    found = Found()
    materials_seen = []
    engines_registry = load_registry("engines")
    instruments_registry = load_registry("instruments")
    for src in sources:
        scan_source(src, found, materials_seen, engines_registry, instruments_registry)
    fields = {}
    for f in FIELDS:
        if f.startswith("policy.") or f in ("collaboration.mode", "operational_constraints.execution_permission"):
            fields[f] = {"value": None, "state": "unknown"}   # never inferred (plan.md 5.0, MP11)
        else:
            fields[f] = found.stated(f)
    card = cards.skeleton("discovery_report", "dr-" + lab_id, seat, created)
    card["lab_id"] = lab_id
    card["inputs"] = []
    for src in sources:
        item = {"kind": src.kind, "ref": src.url or src.path.replace(os.sep, "/")}
        if src.commit:
            item["commit"] = src.commit
        item["note"] = "%d files listed; code and configuration read, nothing executed" % len(src.files)
        card["inputs"].append(item)
    for url in materials_seen:
        card["inputs"].append({"kind": "material", "ref": url})
    card["fields"] = fields
    card["materials_seen"] = materials_seen
    card["scope"] = "full"
    n_inf = sum(1 for v in fields.values() if v["state"] == "inferred")
    card["note"] = note or ("Step zero over %d input(s): %d field(s) inferred with evidence, %d unknown."
                            % (len(sources), n_inf, len(fields) - n_inf))
    return card
