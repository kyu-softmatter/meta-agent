"""Whether S6's isolated copy of a bundle is gone, looked at and never assumed (failure line dft-8, tasks/018 and 020).

Test run dft/20261117-3 (collect-1): src/validate/gate.py removed the copy with shutil.rmtree(..., ignore_errors=True),
the copy stayed in the temporary folder, 5.4 GB each time, and the validation report said it was removed. The cause was
not shown. remove_copy() looks after the removal whether the copy is still there, tries once more, and otherwise says
what is left and the first errors it met, so that the next time shows the cause.
"""
import os
import shutil
import stat
import tempfile
import unittest

from meta_agent.src.validate import gate as gate_mod


class RemoveCopy(unittest.TestCase):

    def test_a_copy_that_goes_is_none(self):
        tmp = tempfile.mkdtemp(prefix="ma-s6-probe-")
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "bundle", "runs", "env"))
        with open(os.path.join(tmp, "bundle", "runs", "env", "f"), "w") as f:
            f.write("x")
        self.assertIsNone(gate_mod.remove_copy(tmp))
        self.assertFalse(os.path.exists(tmp))

    def test_a_copy_already_gone_is_none(self):
        tmp = tempfile.mkdtemp(prefix="ma-s6-probe-")
        os.rmdir(tmp)
        self.assertIsNone(gate_mod.remove_copy(tmp))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root removes a read-only directory's files")
    def test_a_copy_that_stays_is_said_with_its_errors(self):
        tmp = tempfile.mkdtemp(prefix="ma-s6-probe-")
        locked = os.path.join(tmp, "bundle", "runs", "env")
        os.makedirs(locked)
        with open(os.path.join(locked, "f"), "w") as f:
            f.write("x")
        os.chmod(locked, stat.S_IRUSR | stat.S_IXUSR)

        def unlock():
            os.chmod(locked, stat.S_IRWXU)
            shutil.rmtree(tmp, ignore_errors=True)
        self.addCleanup(unlock)
        said = gate_mod.remove_copy(tmp)
        self.assertTrue(os.path.exists(tmp))
        self.assertIsNotNone(said)
        self.assertIn("the isolated copy %s was not removed" % tmp, said)
        self.assertIn("PermissionError", said)


def deep(root, length):
    """A folder under root whose path is at least `length` characters, made by the form Windows reads it in."""
    p = root
    while len(p) < length:
        p = os.path.join(p, "pkgs-cache-" + "x" * 40)
    os.makedirs(gate_mod.long_path(p))
    return p


class RemoveCopyOnWindows(unittest.TestCase):
    """Failure lines office-7 and office-11: on Windows a pixi package cache in the copy has paths longer than Windows
    allows by default, and a clone's git objects are read-only files; shutil.rmtree met both. Two unrelated kinds: an
    engine's environment cache and a data repository's object store. Watched failing on Windows (LongPathsEnabled 0)
    before remove_copy went by the long form and made a read-only file writable."""

    def test_a_cache_with_a_path_past_the_default_limit_goes(self):
        tmp = tempfile.mkdtemp(prefix="ma-s6-probe-")
        self.addCleanup(shutil.rmtree, gate_mod.long_path(tmp), True)
        leaf = deep(os.path.join(tmp, "bundle", "runs", "env", ".pixi"), 300)
        with open(os.path.join(gate_mod.long_path(leaf), "info.json"), "w") as f:
            f.write("{}")
        self.assertIsNone(gate_mod.remove_copy(tmp))
        self.assertFalse(os.path.lexists(gate_mod.long_path(tmp)))

    def test_read_only_files_go(self):
        tmp = tempfile.mkdtemp(prefix="ma-s6-probe-")
        self.addCleanup(shutil.rmtree, gate_mod.long_path(tmp), True)
        objects = os.path.join(tmp, "bundle", "data", "origin.git", "objects", "36")
        os.makedirs(objects)
        obj = os.path.join(objects, "bc9057e43d7130c0c495895427e461bd2783be")
        with open(obj, "wb") as f:
            f.write(b"x\0")
        os.chmod(obj, stat.S_IREAD)
        self.assertIsNone(gate_mod.remove_copy(tmp))
        self.assertFalse(os.path.lexists(tmp))


if __name__ == "__main__":
    unittest.main()
