"""Template v18 (the design role's ask 20261117-design-macbook-20261117-1-14; failures.jsonl em-10, and cfd-5, cfd-16 of
tasks/019): text only, the bundle's classify-knowledge says what the builder's own says. spec is the maker's
documentation, a tutorial or example page of the maker included; a quantity defined up to a constant is compared only
once both share its zero; a value a source tabulates from its raw series is read against that series.

Shown on two unrelated kinds, the engine and the spectrometer of the v13 test: a bundle of each carries the text, and
check 24 has nothing to say of the session skill.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v17 as v17

V18 = template_mod.SOURCES["v18"]
REPO = v17.REPO
SAYS = ["`spec` (the maker's documentation: a vendor's specification, a manual, or a tutorial or example page",
        "is compared with another only after both are shown to share that zero",
        "is read against that series where the source publishes it"]
SKILL = os.path.join(".claude", "skills", "classify-knowledge", "SKILL.md")


class TheBundlesClassifyKnowledge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v18-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_bundle_of_each_kind_carries_the_builders_words(self):
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind, [v13.task(kind)], template=V18)
            text = cards.read_text(os.path.join(b, SKILL))
            for words in SAYS:
                self.assertIn(words, text, (kind, words))
            self.assertNotIn("`spec` (a vendor's specification)", text, kind)
            p = subprocess.run([sys.executable, os.path.join(REPO, "contracts", "tools", "session_skills.py"), "check",
                                os.path.dirname(os.path.join(b, SKILL))], capture_output=True, text=True, cwd=REPO)
            self.assertEqual(p.stdout.strip(), "nothing to say", (kind, p.stdout + p.stderr))

    def test_the_builders_own_skill_says_the_same(self):
        own = cards.read_text(os.path.join(REPO, SKILL))
        for words in SAYS:
            self.assertIn(words, own, words)


class TheVersion(unittest.TestCase):
    def test_v18_changes_one_text(self):
        v17_src = template_mod.SOURCES["v17"]
        self.assertIn("v18", template_mod.SOURCES)                  # v19 is the latest since the tolerance rule
        self.assertEqual(cards.tree_files(v17_src), cards.tree_files(V18))
        changed = sorted(r for r in cards.tree_files(v17_src)
                         if cards.sha256_file(os.path.join(v17_src, r)) != cards.sha256_file(os.path.join(V18, r)))
        self.assertEqual(changed, [".claude/skills/classify-knowledge/SKILL.md", "TEMPLATE.json"])
        self.assertEqual(cards.load_json(os.path.join(V18, "TEMPLATE.json"))["version"], "v18")


if __name__ == "__main__":
    unittest.main()
