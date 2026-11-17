"""A science task that names what held[] holds (tasks/016, run 20261117-7, the clone's failure line rheotool-2).

A science task written at an intake's first revision named quantities that a later revision held, and the bundle's
CLAUDE.md then named what the bundle does not compute. The intake stage refuses a card whose science task names an
item of its held[] not yet released; and since the goal keeps the science task of the revision it was made from, the
build's Role says which of what it names is held, and where its reason is.

Two unrelated kinds: an engine whose shear material functions are held, and a spectrometer whose peak fit is held;
the echo request is built end to end with a held item its science task names.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
import os
import shutil
import subprocess
import sys
import unittest

from meta_agent.src import cards
from meta_agent.src import designer
from meta_agent.src.intake import card as card_mod
from meta_agent.tests.test_designer import NOW, SEAT, VALIDATE, load_intake, scratch_root

KINDS = {
    "engine": ("the steady material functions (shear viscosity, first normal stress difference, extensional viscosity) of a "
               "constitutive model in homogeneous flow",
               [{"item": "shear material functions (shear viscosity, normal-stress differences)", "reason": "no source states them"},
                {"item": "install_environment", "reason": "no source named"}, "rheoFoam and the other solvers"],
               ["shear viscosity", "normal stress difference"],
               "material functions of a constitutive model in homogeneous flow"),
    "spectrometer": ("absorbance spectra of a sample and the Voigt fit of their peaks, with the baseline_correction applied",
                     [{"item": "peak deconvolution (Voigt fit)", "reason": "no line shape source read"},
                      {"item": "baseline_correction", "reason": "the person has not chosen one"}, "the other detectors"],
                     ["voigt fit", "baseline correction"],
                     "absorbance spectra of a sample"),
}


class TheMatch(unittest.TestCase):
    def test_a_science_task_that_names_a_held_item_is_found(self):
        for kind, (task, held, phrases, _) in KINDS.items():
            self.assertEqual([p for _, p in card_mod.held_named(task, held)], phrases, kind)

    def test_a_narrowed_science_task_names_nothing_held(self):
        for kind, (_, held, _, narrowed) in KINDS.items():
            self.assertEqual(card_mod.held_named(narrowed, held), [], kind)

    def test_a_released_item_is_not_held(self):
        for kind, (task, held, _, _) in KINDS.items():
            released = [dict(h, released_by="human", released_at="2026-11-17") if isinstance(h, dict) else h for h in held]
            self.assertEqual(card_mod.held_named(task, released), [], kind)

    def test_one_common_word_is_not_a_phrase(self):
        self.assertEqual(card_mod.held_named("the solvers of the model", ["solvers"]), [])
        self.assertEqual(card_mod.held_phrases("rheoFoam and the other solvers"), [["rheofoam"]])   # 'other' leads, 'solver' alone


class TheIntakeStage(unittest.TestCase):
    def test_the_stage_refuses_it_and_says_what_to_do(self):
        for kind, (task, held, phrases, narrowed) in KINDS.items():
            card = {"science_task": task, "held": held}
            words = " ".join(p for p in card_mod.problems(card) if p.startswith("science_task:"))
            for phrase in phrases:
                self.assertIn("it names %s, which held[] holds" % phrase, words, kind)
            self.assertIn("narrow it in this revision, or a person releases the item", words)
            card["science_task"] = narrowed
            self.assertEqual([p for p in card_mod.problems(card) if p.startswith("science_task:")], [], kind)


class TheRole(unittest.TestCase):
    def test_the_role_says_what_of_the_science_task_is_held(self):
        for kind, (task, held, _, narrowed) in KINDS.items():
            line = designer.science_task_line(task, held)
            self.assertTrue(line.startswith(task), kind)
            self.assertIn("this agent does not compute what the request holds", line)
            self.assertIn("in `CAPABILITIES.json`", line)
            self.assertEqual(designer.science_task_line(narrowed, held), narrowed, kind)

    def test_a_held_item_with_a_digit_is_not_named(self):
        line = designer.science_task_line("the shear viscosity of the fluid", ["shear viscosity (at 2 rates)"])
        self.assertIn("an item of the held list in `CAPABILITIES.json`", line)
        self.assertEqual([ch for ch in line if ch.isdigit()], [])

    def test_a_built_bundle_s_role_says_it_and_passes_the_gate(self):
        i = copy.deepcopy(load_intake())
        i["held"] = [{"item": "the character count", "reason": "the person has not asked for it yet"}]
        tmp, root = scratch_root()
        try:
            designer.run(i, SEAT, "0001", NOW, root)
            bundle = os.path.join(root, "builds", "echo", "0001", "bundle")
            text = cards.read_text(os.path.join(bundle, "CLAUDE.md"))
            self.assertIn("Science task: %s\n\nOf what this science task names, this agent does not compute what the request "
                          "holds: the character count." % i["science_task"], text)
            p = subprocess.run([sys.executable, VALIDATE, tmp, "--strict"], capture_output=True, text=True,
                               env=dict(os.environ, PYTHONUTF8="1"))
            self.assertIn("0 failed, 0 pending", p.stdout, p.stdout + p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
