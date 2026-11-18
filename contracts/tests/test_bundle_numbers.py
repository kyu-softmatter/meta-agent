# -*- coding: utf-8 -*-
"""Tests of bundle check B6: a number in a bundle's CLAUDE.md is in its snapshot, and a unit is not a number
(tasks/016: the Tools section of a bundle prints the unit a tool contract names).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts"))
import validate  # noqa: E402


class B6(unittest.TestCase):
    def judge(self, text, numbers=()):
        d = tempfile.mkdtemp(prefix="b6-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "envelope"))
        with open(os.path.join(d, "envelope", "snapshot.json"), "w", encoding="utf-8") as f:
            json.dump({"kb_version": "kb@x", "entries": [], "numbers": [{"value": n} for n in numbers]}, f)
        with open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write(text)
        report = validate.Report(quiet=True)
        validate.checkB6(d, "bundle", report)
        return [m for _, _, m in report.fails]

    def test_a_unit_a_contract_names_is_not_a_number(self):
        # two unrelated kinds of tool: an instrument's status and a simulation box
        self.assertEqual(self.judge("- output: `gap` (number, m), `temperature` (number, K), `density` (number, kg/m^3)\n"), [])
        self.assertEqual(self.judge("- output: `volume` (number, m^3), `area` (number, m^2), `g` (number, m/s^2), "
                                    "`rho` (number, g/cm^3), `fraction` (number, 1), `count` (integer, 1)\n"), [])

    def test_a_number_beside_a_unit_is_still_read(self):
        self.assertEqual(len(self.judge("The gap is 3 m^3 wide.\n")), 1)
        self.assertEqual(len(self.judge("- output: `fraction` (number, 1); it never exceeds 1\n")), 1)
        self.assertEqual(len(self.judge("A box of 2 m^2.\n", numbers=(3,))), 1)
        self.assertEqual(self.judge("A box of 2 m^2.\n", numbers=(2,)), [])


    def test_the_unit_one_is_passed_whatever_follows_it_in_the_brackets(self):
        self.assertEqual(self.judge("- input: `fraction` (number, 1, required; the volume fraction), `n` (integer, 1; a count)\n"), [])
        self.assertEqual(len(self.judge("- input: `fraction` (number, 12, required)\n")), 1)

    def test_a_version_after_the_word_version_and_markup_is_an_identifier(self):
        # two unrelated kinds: a molecular engine's version in a table (run molecular-dynamics/20261117-23, gmx-17) and an
        # instrument's firmware in a field
        for text in ("| version | 2025.2 |\n", "- version: 2025.2\n", "**Version** 4.1 of the firmware\n", "version `2025.2`\n"):
            self.assertEqual(self.judge(text), [], text)
        self.assertEqual(len(self.judge("| cutoff | 1.2 |\n")), 1)          # a number in a table is still read
        self.assertEqual(len(self.judge("version: 2025.2, with 4 ranks\n")), 1)

    def test_the_unit_one_stands_on_an_array_too(self):
        # two unrelated kinds: a sweep of equivalence ratios from a combustion engine (run chemical-kinetics/20261117-12,
        # ctrl-pair-3) and a list of strain amplitudes from an instrument
        self.assertEqual(self.judge("- output: `equivalence_ratios` (array, 1, required), `temperatures` (array, K)\n"), [])
        self.assertEqual(self.judge("- input: `strain_amplitudes` (array, 1; the amplitudes to visit)\n"), [])
        self.assertEqual(len(self.judge("- output: `ratios` (array, 12)\n")), 1)
        self.assertEqual(len(self.judge("- output: `ratios` (array, 1); at most 3 of them\n")), 1)

    def test_a_version_of_three_parts_is_an_identifier_and_a_number_beside_it_is_still_read(self):
        # two unrelated kinds of program: a simulation engine and an instrument's firmware (tasks/016, run 20261117-1)
        self.assertEqual(self.judge("Pinned: hoomd 7.2.2, gsd 5.0.1.\n"), [])
        self.assertEqual(self.judge("The controller runs firmware 2.14.0-rc1 (v3.4.1 of its manual).\n"), [])
        self.assertEqual(len(self.judge("Version 7.2. The volume fraction is 0.57.\n", numbers=(7.2,))), 1)
        self.assertEqual(len(self.judge("hoomd 7.2.2 on 4 cores\n")), 1)

    def test_a_version_of_two_parts_is_an_identifier_where_the_word_version_or_v_stands_before_it(self):
        # a package of an engine's environment and a controller's firmware (tasks/016, run 20261117-3)
        self.assertEqual(self.judge("packaging version 26.3, pillow v13.0\n"), [])
        self.assertEqual(self.judge("The firmware is at version 2.14 (versions 2.1 and before are refused).\n"), [])
        self.assertEqual(len(self.judge("packaging 26.3\n")), 1)      # beside a name alone it is read


class Check3(unittest.TestCase):
    """A page shows where a claim was read; a numeral of a locus is the card's."""

    def judge(self, card, text):
        d = tempfile.mkdtemp(prefix="c3-")
        self.addCleanup(shutil.rmtree, d, True)
        with open(os.path.join(d, "page.md"), "w", encoding="utf-8") as f:
            f.write(text)
        report = validate.Report(quiet=True)
        validate.check3([(os.path.join(d, "card.json"), card)], {d: [os.path.join(d, "page.md")]}, report, d)
        return [m for _, _, m in report.fails]

    def test_a_numeral_of_a_locus_may_stand_on_the_page_and_no_other_text_of_a_card(self):
        # two unrelated kinds of source: a notebook's cells and a manual's page
        card = {"claims": [{"claim": "the stage ends after 13000 moves", "loci": ["section 5, cells [4] to [8]"]},
                           {"claim": "the cone is truncated", "locus": "manual, page 212"}], "numbers": [{"value": 7.5}]}
        self.assertEqual(self.judge(card, "Read in section 5, cells [4] to [8], and on page 212; the value is 7.5.\n"), [])
        self.assertEqual(len(self.judge(card, "The stage ends after 13000 moves.\n")), 1)      # a claim's text gives the page no number


class B9Permission(unittest.TestCase):
    """What the lab's execution permission opens (the person, 2026-11-16): an engine, the agent's own files, and an
    install from a package source a person allowed; never an instrument."""

    def bundle(self, side, installs=None, sources=None, perm=True, fetches=None, hosts=None):
        d = tempfile.mkdtemp(prefix="b9-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "tools", "t"))
        os.makedirs(os.path.join(d, "src"))
        os.makedirs(os.path.join(d, "envelope"))
        with open(os.path.join(d, "src", "run_tool.py"), "w") as f:
            f.write("from gate import check_before\n")
        with open(os.path.join(d, "src", "gate.py"), "w") as f:
            f.write("def check_before(tool):\n    return None\n")
        tc = {"name": "t", "side_effects": side, "safety_gate": {"required": True, "place": "src/gate.py", "opens_by": "execution_permission"}}
        if installs:
            tc["installs_from"] = installs
        if fetches:
            tc["fetches_from"] = fetches
        with open(os.path.join(d, "tools", "t", "tool.json"), "w") as f:
            json.dump(tc, f)
        if perm:
            with open(os.path.join(d, "envelope", "execution_permission.json"), "w") as f:
                json.dump({"reaches": "engine", "package_sources": sources or [], "data_sources": hosts or []}, f)
        report = validate.Report(quiet=True)
        validate.checkB9(d, "bundle", report)
        return [m for _, _, m in report.fails]

    def test_an_install_from_an_allowed_source_opens_and_nothing_else_on_the_network(self):
        allowed = [{"installer": "pixi", "channel": "conda-forge"}]
        self.assertEqual(self.bundle("network", {"installer": "pixi", "channel": "conda-forge"}, allowed), [])
        self.assertEqual(self.bundle("runs_process"), [])
        self.assertEqual(len(self.bundle("network", None, allowed)), 1)
        self.assertEqual(len(self.bundle("network", {"installer": "pip", "channel": "pypi"}, allowed)), 1)
        self.assertEqual(len(self.bundle("controls_instrument", None, allowed)), 1)
        self.assertEqual(len(self.bundle("writes_files", perm=False)), 1)

    def test_a_fetch_opens_only_from_hosts_the_permission_lists_and_neither_list_opens_the_other(self):
        # The person, 2026-11-17 (tasks/023): data hosts a built agent may read from, for every agent of the lab.
        pkgs = [{"installer": "pixi", "channel": "conda-forge"}]
        hosts = [{"host": "gitlab.com", "access": "read_only_anonymous"},
                 {"host": "pseudopotentials.quantum-espresso.org", "access": "read_only_anonymous"}]
        examples = [{"host": "gitlab.com", "access": "read_only_anonymous"}]
        both = hosts
        self.assertEqual(self.bundle("network", fetches=examples, hosts=hosts), [])
        self.assertEqual(self.bundle("network", fetches=both, hosts=hosts), [])
        self.assertEqual(self.bundle("network", {"installer": "pixi", "channel": "conda-forge"}, pkgs, fetches=examples, hosts=hosts), [])
        # a second kind: a weather station's archive, allowed and not
        archive = [{"host": "archive.example-weather.org", "access": "read_only_anonymous"}]
        self.assertEqual(self.bundle("network", fetches=archive, hosts=archive), [])
        self.assertEqual(len(self.bundle("network", fetches=archive, hosts=hosts)), 1)
        self.assertEqual(len(self.bundle("network", fetches=examples + archive, hosts=hosts)), 1)
        self.assertEqual(len(self.bundle("network", fetches=[{"host": "www.gitlab.com", "access": "read_only_anonymous"}], hosts=hosts)), 1)
        self.assertEqual(len(self.bundle("network", fetches=[{"host": "gitlab.com", "access": "read_write"}], hosts=hosts)), 1)
        # a data host opens no install, and a package source opens no fetch
        self.assertEqual(len(self.bundle("network", {"installer": "pixi", "channel": "conda-forge"}, [], hosts=hosts)), 1)
        self.assertEqual(len(self.bundle("network", sources=pkgs, fetches=examples)), 1)
        self.assertEqual(len(self.bundle("network", fetches=[], hosts=hosts)), 1)


if __name__ == "__main__":
    unittest.main()


class Check5Materials(unittest.TestCase):
    """A material id is a reference: in the newest revision of a card it names a material card (tasks/016, run 20261117-3)."""

    def judge(self, files):
        d = tempfile.mkdtemp(prefix="c5-")
        self.addCleanup(shutil.rmtree, d, True)
        for rel_path, data in files.items():
            p = os.path.join(d, *rel_path.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f)
        report = validate.Report(quiet=True)
        cards, _ = validate.scan(d, report)
        validate.check5(cards, validate.Contracts(), report, d)
        return [m for _, _, m in report.fails]

    def test_two_kinds_of_card_resolve_and_a_wrong_id_fails_only_in_the_newest_revision(self):
        material = {"inbox/materials/one/MATERIAL.json": {"card": "material", "id": "mat-20261117-004"}}
        # a parameter sheet's row of a simulation engine, and a tool profile's claims of an instrument
        sheet = {"card": "parameter_sheet", "id": "s", "rows": [{"source": "literature:mat-20261117-004"}]}
        profile = {"card": "tool_profile", "id": "p", "material_refs": ["mat-20261117-004"]}
        self.assertEqual(self.judge(dict(material, **{"requests/r/sheet.json": sheet, "requests/r/tool_profile.json": profile})), [])
        wrong = {"card": "parameter_sheet", "id": "s", "rows": [{"source": "literature:mat-20261117-009"}]}
        fails = self.judge(dict(material, **{"requests/r/sheet.json": wrong}))
        self.assertEqual(len(fails), 1)
        self.assertIn("mat-20261117-009", fails[0])
        # the same wrong revision, once a later one stands beside it, is a record and is judged as it was written
        self.assertEqual(self.judge(dict(material, **{"requests/r/sheet.json": wrong, "requests/r/v2_sheet.json": sheet})), [])
