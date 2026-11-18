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


if __name__ == "__main__":
    unittest.main()
