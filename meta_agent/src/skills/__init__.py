"""The skill library's catalogue and runner (plan.md 14-30, 14-31; tasks/010).

What a skill is, how its source is read and how its worked cases run is contracts/tools/skills.py, the
file check 22 reads; this package loads that file and adds no second reader of manifests and no second
case runner. `catalogue` builds skills/index.json from the manifests and answers what a model reads to
choose; `runner` runs one skill with a tool runner it is given and writes what it ran.

    python -m meta_agent.src.skills list [--kind K] [--parameter P] [--instrument I]
    python -m meta_agent.src.skills run <id@vN> --inputs FILE [--transcript FILE] [--record FILE]
    python -m meta_agent.src.skills index [--check]
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(os.path.dirname(HERE))      # meta_agent/
REPO = os.path.dirname(META)
LIBRARY = os.path.join(META, "skills")
RULES_PATH = os.path.join(REPO, "contracts", "tools", "skills.py")


def _load_rules():
    spec = importlib.util.spec_from_file_location("contracts_tools_skills", RULES_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rules = _load_rules()
