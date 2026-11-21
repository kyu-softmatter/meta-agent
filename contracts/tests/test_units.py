# -*- coding: utf-8 -*-
"""Tests of contracts/tools/units.py: a factor between two registered units (tasks/031, dftmd-1).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds on purpose (the person, 2026-11-11): a DFT force constant handed to an MD engine's
own units, and a measured viscosity handed to a rheology engine.
"""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import units as U  # noqa: E402


class Registry(unittest.TestCase):
    def setUp(self):
        self.units = U.load()

    def test_every_derived_unit_is_what_its_parts_give(self):
        self.assertEqual(U.check(self.units), [])

    def test_a_derived_unit_stated_wrongly_is_found(self):
        units = dict(self.units)
        units["Ry/bohr^2"] = dict(units["Ry/bohr^2"], si_factor=units["Ry/bohr^2"]["si_factor"] * 1.001)
        self.assertEqual(len(U.check(units)), 1)

    def test_a_factor_is_the_ratio_of_si_factors(self):
        f, why = U.factor(self.units, "Pa.s", "mPa.s")
        self.assertIsNone(why)
        self.assertTrue(U.factor_matches(f, self.units["Pa.s"]["si_factor"] / self.units["mPa.s"]["si_factor"]))
        f, why = U.factor(self.units, "Ry/bohr^2", "eV/Angstrom^2")
        self.assertIsNone(why)
        self.assertTrue(U.factor_matches(f, self.units["Ry/bohr^2"]["si_factor"] / self.units["eV/Angstrom^2"]["si_factor"]))

    def test_no_factor_between_dimensions(self):
        for a, b in (("Pa.s", "m^2/s"), ("bohr", "eV")):
            f, why = U.factor(self.units, a, b)
            self.assertIsNone(f)
            self.assertIn("dimension", why)

    def test_an_engine_unit_needs_a_scale_of_its_dimension(self):
        f, why = U.factor(self.units, "bohr", "engine_length")
        self.assertIsNone(f)
        f, why = U.factor(self.units, "bohr", "engine_length", stands_for="eV")
        self.assertIsNone(f)
        f, why = U.factor(self.units, "bohr", "engine_length", stands_for="Angstrom")
        self.assertIsNone(why)
        self.assertTrue(U.factor_matches(f, self.units["bohr"]["si_factor"] / self.units["Angstrom"]["si_factor"]))

    def test_a_particle_mass_is_not_a_molar_mass(self):
        f, why = U.factor(self.units, "Da", "kg")
        self.assertIsNone(why)
        self.assertTrue(U.factor_matches(f, self.units["Da"]["si_factor"]))
        f, why = U.factor(self.units, "Da", "g/mol")
        self.assertIsNone(f)
        self.assertIn("dimension", why)

    def test_an_engine_mass_stands_for_a_mass(self):
        f, why = U.factor(self.units, "Da", "engine_mass", stands_for="g/mol")
        self.assertIsNone(f)
        f, why = U.factor(self.units, "g", "engine_mass", stands_for="Da")
        self.assertIsNone(why)
        self.assertTrue(U.factor_matches(f, self.units["g"]["si_factor"] / self.units["Da"]["si_factor"]))

    def test_a_value_in_an_engine_unit_goes_nowhere(self):
        f, why = U.factor(self.units, "engine_length", "nm")
        self.assertIsNone(f)
        self.assertIn("outside its engine", why)


if __name__ == "__main__":
    unittest.main()
