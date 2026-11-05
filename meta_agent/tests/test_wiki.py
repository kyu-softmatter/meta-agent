"""The wiki view and the card ontology (tasks/003), rendered in a scratch copy of the records.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom

from meta_agent.src.wiki import render as wiki

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
LINK = re.compile(r"\[\[([^\]]+)\]\]")


def scratch_tree():
    """A repository-like tree: the records under meta_agent/ and the schemas, nothing else."""
    tmp = tempfile.mkdtemp(prefix="ma-wiki-")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for part in ("requests", "profiles", "builds", "templates"):
        src = os.path.join(META, part)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(tmp, "meta_agent", part), ignore=ignore)
    shutil.copytree(os.path.join(REPO, "contracts", "schemas"), os.path.join(tmp, "contracts", "schemas"))
    return tmp


def snapshot(folder):
    out = {}
    for f in sorted(os.listdir(folder)):
        p = os.path.join(folder, f)
        if os.path.isfile(p):
            with open(p, "rb") as h:
                out[f] = h.read()
    return out


class WikiView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = scratch_tree()
        cls.out = os.path.join(cls.tmp, "meta_agent", "wiki")
        cls.result = wiki.render(cls.tmp)
        cls.pages = {f[:-3] for f in os.listdir(cls.out) if f.endswith(".md")}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def read(self, name):
        with open(os.path.join(self.out, name + ".md"), encoding="utf-8") as f:
            return f.read()

    def test_one_page_per_card_revision_and_artifact(self):
        n_cards = len(wiki.scan(self.tmp))
        self.assertEqual(self.result["cards"], n_cards)
        self.assertEqual(self.result["pages"], len(self.pages))
        self.assertEqual(len(self.pages), n_cards + self.result["artifacts"] + 1)
        self.assertIn("index", self.pages)
        self.assertIn("goal-echo-001@r1", self.pages)
        self.assertIn("goal-echo-001@r2", self.pages)

    def test_every_link_names_a_page(self):
        for name in self.pages:
            for target in LINK.findall(self.read(name)):
                self.assertIn(target, self.pages, "%s links to %s" % (name, target))

    def test_revisions_and_artifacts_are_linked(self):
        self.assertIn("- supersedes: [[goal-echo-001@r1]]", self.read("goal-echo-001@r2"))
        build = self.read("build-echo-0001@r1")
        self.assertIn("[[template-agent@21f0dd569975]]", build)
        self.assertIn("[[bundle-echo-0001]]", build)
        self.assertIn("- record: `meta_agent/builds/echo/0001/bundle`", self.read("bundle-echo-0001"))

    def test_a_second_run_writes_identical_bytes_and_drops_stale_pages(self):
        before = snapshot(self.out)
        with open(os.path.join(self.out, "stale@r9.md"), "w", encoding="utf-8") as f:
            f.write("# stale@r9\n")
        os.makedirs(os.path.join(self.out, ".obsidian"), exist_ok=True)
        wiki.render(self.tmp)
        self.assertEqual(snapshot(self.out), before)
        self.assertTrue(os.path.isdir(os.path.join(self.out, ".obsidian")))

    def test_check_18_accepts_the_view(self):
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--checks", "18"], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertIn("0 failed, 0 pending", p.stdout, p.stdout + p.stderr)
        self.assertRegex(p.stdout, r"\b%d wiki page\(s\)" % len(self.pages))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_check_18_refuses_an_edited_page(self):
        tmp = scratch_tree()
        try:
            wiki.render(tmp)
            page = os.path.join(tmp, "meta_agent", "wiki", "vr-echo-0001@r1.md")
            with open(page, "a", encoding="utf-8") as f:
                f.write("\nThe agreement was 0.5.\n")
            p = subprocess.run([sys.executable, VALIDATE, tmp, "--checks", "18"], capture_output=True, text=True,
                               env=dict(os.environ, PYTHONUTF8="1"))
            self.assertNotEqual(p.returncode, 0, p.stdout)
            self.assertIn("number 0.5 is in no field of the record this page renders", p.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_ontology_parses_and_names_the_card_types(self):
        doc = xml.dom.minidom.parse(os.path.join(self.out, "ontology.owl"))
        labels = {e.firstChild.data for e in doc.getElementsByTagName("rdfs:label") if e.firstChild}
        self.assertIn("agent_goal", labels)
        self.assertIn("kb_entry", labels)
        self.assertIn("supersedes", labels)
        self.assertEqual(len(doc.getElementsByTagName("owl:ObjectProperty")), self.result["properties"])
        self.assertEqual(len(doc.getElementsByTagName("owl:Class")), self.result["classes"])


if __name__ == "__main__":
    unittest.main()
