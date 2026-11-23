"""A bundle's digest is one its commit reproduces (failure line office-2).

On Windows a session wrote three library skills with CRLF line endings; the build copied them into the bundle byte for
byte and took bundle_sha256 over that working tree, while git stored the same files with LF under the repository's
`* text=auto eol=lf`. So the commit could not reproduce its own build card, and testfolder.py make refused it. From
here the build writes every file git takes for text with LF before it takes the digest (cards.lf_tree), and leaves a
file git takes for binary as it was, so the bundle on disk, its digest and the commit agree on every computer.

Two unrelated kinds, neither rheology, as the v38 test composes them: a plane-wave DFT engine and an optical
spectrometer, each built once from LF inputs and once from the same inputs with CRLF in a copied library skill, in a
file of the template and in the tool's adapter. Watched failing before the build called cards.lf_tree.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.tests import test_template_v38 as v38

SKILL = "series_maximum@v3"
TEMPLATE_FILE = "src/replay.py"
BINARY = "src/blob.bin"
BINARY_BYTES = b"a\r\nb\x00c\rd\r\n"
ADAPTER = "def run(payload):\n    return {'done': True}\n"


def crlf(folder):
    """Every text file under folder written with CRLF, as an editor on Windows writes it."""
    for rel in cards.tree_files(folder):
        path = os.path.join(folder, rel)
        with open(path, "rb") as f:
            data = f.read()
        if cards.git_text(data):
            with open(path, "wb") as f:
                f.write(data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def build(tmp, kind, windows):
    """The bundle of one kind and its digest; with windows, CRLF in a skill, a template file and the adapter."""
    k = v38.KINDS[kind]
    template = os.path.join(tmp, "template")
    shutil.copytree(template_mod.SOURCE, template, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    with open(os.path.join(template, *BINARY.split("/")), "wb") as f:
        f.write(BINARY_BYTES)
    row = catalogue_mod.take([SKILL])[0]
    folder = os.path.join(tmp, "library", SKILL)
    shutil.copytree(row["folder"], folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    adapter = ADAPTER
    if windows:
        crlf(folder)
        crlf(os.path.join(template, "src"))
        with open(os.path.join(template, *BINARY.split("/")), "wb") as f:
            f.write(BINARY_BYTES)
        adapter = ADAPTER.replace("\n", "\r\n")
    path = os.path.join(tmp, k["agent"], "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": k["agent"], "template": "agent@test", "rid": "req-%s-001" % k["agent"], "purpose": "p",
            "science_task": k["science_task"], "tools_section": bundle_mod.tools_section([v38.contract(k)]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    replay = [{"id": "rp-001", "name": "the mock answers", "call": {"tool": k["call"], "input": {}},
               "expected": {"output": {"done": True}}, "expected_verdict": "pass"}]
    sha = bundle_mod.compose(template, path, fill, [{"name": k["call"], "contract": v38.contract(k),
                                                     "adapter_source": adapter, "errors": []}],
                             {"tool": k["tool"], "held": k["held"], "observed": []},
                             {"safety": {}, "parameters": {"rows": []}}, [], [], replay,
                             skills=[dict(row, folder=folder)], simulation=False, tool_kind=k["tool_kind"])
    return path, sha


class TheBundleIsWrittenAsItIsCommitted(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-line-endings-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_crlf_inputs_give_the_bundle_and_the_digest_of_lf_inputs(self):
        for kind in v38.KINDS:
            lf_path, lf_sha = build(os.path.join(self.tmp, kind, "lf"), kind, windows=False)
            path, sha = build(os.path.join(self.tmp, kind, "crlf"), kind, windows=True)
            self.assertEqual(sha, lf_sha, kind)
            self.assertEqual(sha, cards.sha256_tree(path), kind)
            for rel in cards.tree_files(path):
                with open(os.path.join(path, rel), "rb") as f:
                    data = f.read()
                if rel != BINARY:
                    self.assertNotIn(b"\r\n", data, (kind, rel))
            for rel in ("skills/%s/scripts/analysis.py" % SKILL, TEMPLATE_FILE, "tools/%s/adapter.py" % v38.KINDS[kind]["call"]):
                self.assertTrue(os.path.isfile(os.path.join(path, *rel.split("/"))), (kind, rel))

    def test_a_file_git_takes_for_binary_is_left_as_it_was(self):
        for kind in v38.KINDS:
            path, _ = build(os.path.join(self.tmp, kind, "bin"), kind, windows=True)
            with open(os.path.join(path, *BINARY.split("/")), "rb") as f:
                self.assertEqual(f.read(), BINARY_BYTES, kind)


class GitsTestForText(unittest.TestCase):
    def test_text_with_crlf_is_text(self):
        self.assertTrue(cards.git_text(b"one\r\ntwo\r\n\tthree\n"))
        self.assertTrue(cards.git_text(b""))

    def test_a_nul_or_a_lone_cr_is_binary(self):
        self.assertFalse(cards.git_text(b"one\r\ntwo\x00"))
        self.assertFalse(cards.git_text(b"one\rtwo\r\n"))

    def test_many_bytes_that_do_not_print_are_binary(self):
        self.assertFalse(cards.git_text(bytes(range(1, 8)) * 4 + b"ab\r\n"))
        self.assertTrue(cards.git_text("é and ü\r\n".encode("utf-8")))

    def test_lf_tree_rewrites_text_and_names_what_it_rewrote(self):
        tmp = tempfile.mkdtemp(prefix="ma-lf-tree-")
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel, data in (("a.txt", b"x\r\ny\r\n"), ("b/c.py", b"z\n"), ("d.bin", b"\x00\r\n")):
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            with open(os.path.join(tmp, rel), "wb") as f:
                f.write(data)
        self.assertEqual(cards.lf_tree(tmp), ["a.txt"])
        with open(os.path.join(tmp, "a.txt"), "rb") as f:
            self.assertEqual(f.read(), b"x\ny\n")
        with open(os.path.join(tmp, "d.bin"), "rb") as f:
            self.assertEqual(f.read(), b"\x00\r\n")


if __name__ == "__main__":
    unittest.main()
