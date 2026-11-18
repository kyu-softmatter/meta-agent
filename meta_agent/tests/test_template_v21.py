"""Template v21 (tasks/025; the person's amended tolerance rule of 2026-11-18, 'Yes, run's own error'): the common set
also carries discretization_error_from_two_resolutions@v1, and the run's error it gives is what
tolerance_from_reference@v2 weighs against half the reference's last printed digit.

Two unrelated kinds: a flow's drag coefficient and an FDTD run's transmission, each at two resolutions; and the
engine and spectrometer tools of the v13 test, each built as an engine's bundle, carry the skill.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v20 as v20

V21 = template_mod.SOURCES["v21"]
ERROR = "discretization_error_from_two_resolutions@v1"
RULE = "tolerance_from_reference@v2"
NOW = "2026-11-18T17:30:00Z"
KINDS = {"a fluid flow simulation": ({"fine": 2.95, "coarse": 2.92, "refinement_ratio": 2.0, "order": 2.0}, "2.9437637214"),
         "an electromagnetic fdtd simulation": ({"fine": 0.1472, "coarse": 0.15, "refinement_ratio": 1.5, "order": 2.0}, "0.147162555528154")}


class TheRunsOwnError(unittest.TestCase):
    def test_the_estimate_feeds_the_rule_and_outweighs_a_long_printed_reference(self):
        for system, (two, printed) in KINDS.items():
            e = runner_mod.run(ERROR, two, now=NOW)
            self.assertEqual((e["verdict"], e["outputs"]["estimated"]), ("ran", True), system)
            t = runner_mod.run(RULE, {"printed": printed, "stated_uncertainty": None,
                                      "run_numerical_error": e["outputs"]["error"]}, now=NOW)["outputs"]
            self.assertEqual((t["from"], t["tolerance"]), ("run_numerical_error", e["outputs"]["error"]), system)

    def test_a_simulation_bundle_of_each_kind_carries_it(self):
        tmp = tempfile.mkdtemp(prefix="ma-template-v21-")
        self.addCleanup(shutil.rmtree, tmp, True)
        orig = v20.V20
        v20.V20 = V21
        try:
            for kind in v13.KINDS:
                self.assertIn(ERROR, v20.carried(v20.compose(tmp, kind, [v13.task(kind)])), kind)
        finally:
            v20.V20 = orig


class TheVersion(unittest.TestCase):
    def test_v21_is_the_latest_and_changes_its_template_card_alone(self):
        v20_src = template_mod.SOURCES["v20"]
        self.assertEqual(template_mod.LATEST, "v21")
        changed = sorted(r for r in cards.tree_files(v20_src)
                         if cards.sha256_file(os.path.join(v20_src, r)) != cards.sha256_file(os.path.join(V21, r)))
        self.assertEqual(changed, ["TEMPLATE.json"])
        meta = cards.load_json(os.path.join(V21, "TEMPLATE.json"))
        self.assertEqual(meta["version"], "v21")
        self.assertIn(ERROR, meta["common_skills"])


if __name__ == "__main__":
    unittest.main()
