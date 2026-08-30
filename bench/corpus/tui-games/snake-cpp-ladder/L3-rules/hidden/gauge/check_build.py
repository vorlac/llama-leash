"""The build contract — SPEC.md section 2.

Three of the four fixed points in the whole specification are here, because
everything else the gauge does needs a binary to talk to. A tree that does not
build is not scored on its rules: it fails once, at the top, with the build's
own output attached, so the reader is not left guessing which of forty
requirements went wrong.
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snakegauge  # noqa: E402


class BuildContract(unittest.TestCase):
    def test_build_script_exists_and_is_executable(self):
        """[snake-tui-r1] ./build.sh is present at the root and executable."""
        script = os.path.join(snakegauge.root(), "build.sh")
        self.assertTrue(os.path.isfile(script),
                        "SPEC.md requirement 1: no ./build.sh at the root of the work tree")
        self.assertTrue(os.access(script, os.X_OK),
                        "SPEC.md requirement 1: ./build.sh is present but not executable")

    def test_build_succeeds_and_leaves_the_binary(self):
        """[snake-tui-r2] ./build.sh exits 0 and leaves an executable ./snake."""
        ok, detail = snakegauge.build()
        self.assertTrue(ok, detail)
        self.assertTrue(os.access(snakegauge.binary(), os.X_OK))

    def test_build_is_repeatable(self):
        """[snake-tui-r4] a second ./build.sh on the same tree also succeeds.

        A build that only works once is a build that will not work for the next
        reader, and it usually means a generated file is being written into a
        source directory.
        """
        snakegauge.require_build(self)
        try:
            proc = subprocess.run(["./build.sh"], cwd=snakegauge.root(),
                                  capture_output=True, text=True,
                                  timeout=snakegauge.BUILD_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            self.fail("the second ./build.sh did not finish in %ds"
                      % snakegauge.BUILD_TIMEOUT_S)
        self.assertEqual(
            proc.returncode, 0,
            "SPEC.md requirement 4: a second build exited %d\n--- stderr ---\n%s"
            % (proc.returncode, proc.stderr[-4000:]),
        )
        self.assertTrue(os.access(snakegauge.binary(), os.X_OK),
                        "the second build removed ./snake and did not put it back")


if __name__ == "__main__":
    unittest.main()
