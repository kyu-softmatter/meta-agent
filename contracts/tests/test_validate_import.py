# -*- coding: utf-8 -*-
"""contracts/validate.py imported by another program on a Python without jsonschema (office-5).

The gate run as a script may relaunch itself through uv; imported, it must not, since it would judge with the
importing program's arguments. Two unrelated importers: an intake command with its own flags, and a
Designer check given a bundle folder.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

IMPORTER = r"""
import importlib.util, os, sys
sys.modules["jsonschema"] = None            # this Python cannot import it
sys.argv = [sys.argv[0]] + sys.argv[1:]
spec = importlib.util.spec_from_file_location("gate_rules", os.path.join(%r, "contracts", "validate.py"))
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except ImportError as e:
    print("IMPORTER SAW ImportError:", e)
    sys.exit(7)
print("IMPORTER WENT ON")
"""


class ImportedWithoutJsonschema(unittest.TestCase):
    def importer(self, *argv):
        env = dict(os.environ, PYTHONUTF8="1")
        env.pop("META_AGENT_VALIDATE_REEXEC", None)
        return subprocess.run([sys.executable, "-c", IMPORTER % REPO] + list(argv), cwd=REPO, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)

    def test_the_importer_is_told_and_nothing_is_judged(self):
        for argv in (["intake", "--goal", "goal.json"], ["designer", "check", "builds/x/0001/bundle"]):
            p = self.importer(*argv)
            out = p.stdout.decode("utf-8", "replace")
            self.assertEqual(p.returncode, 7, out)
            self.assertIn("IMPORTER SAW ImportError: contracts/validate.py needs jsonschema", out)
            self.assertNotIn("VERDICT", out)


if __name__ == "__main__":
    unittest.main()
