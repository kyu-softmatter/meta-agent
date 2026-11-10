"""Parameter Intelligence (plan.md 5.3): the bounds pass of M3 (tasks/007).

What a sheet's bounds and computed rows must be is contracts/tools/sheets.py, the file checks 4 and 19
read; this package loads that file and writes sheets it has nothing to say about.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(os.path.dirname(HERE))      # meta_agent/
REPO = os.path.dirname(META)
RULES_PATH = os.path.join(REPO, "contracts", "tools", "sheets.py")
GRADES_PATH = os.path.join(REPO, "contracts", "grades.json")


def _load_rules():
    spec = importlib.util.spec_from_file_location("contracts_tools_sheets", RULES_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rules = _load_rules()
