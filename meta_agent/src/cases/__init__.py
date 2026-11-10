"""F4 Experience Memory (plan.md 5.4): recall before writing, the SMA seeds, promotion eligibility.

`rules` is contracts/tools/cases.py, loaded from its file: what a condition tag means, what a store's
index holds and how a reference resolves. Check 5 and check 8 read the same functions, so recall and
the gate cannot disagree about a range or an index. Nothing here writes a second reading of either.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(os.path.dirname(HERE))          # meta_agent/
REPO = os.path.dirname(META)
RULES_PATH = os.path.join(REPO, "contracts", "tools", "cases.py")


def _load_rules():
    spec = importlib.util.spec_from_file_location("contracts_tools_cases", RULES_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rules = _load_rules()
