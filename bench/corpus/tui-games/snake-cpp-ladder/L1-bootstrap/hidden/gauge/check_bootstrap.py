"""Rung 1: a tree that builds, and a program that runs — SPEC.md sections 2 and 3.

Nothing about the rules is graded here. This rung asks only for the thing every
later rung needs and no later rung can supply for itself: a build that produces
`./snake`, and a program that starts and answers. What the tree looks like
underneath, and what builds it, is the arm's decision and is not checked — that
freedom is the point of grading the outside of the program and nothing else.
"""

import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snakegauge  # noqa: E402


class Bootstrap(unittest.TestCase):
    def test_build_script_exists_and_is_executable(self):
        """[L1-r1] ./build.sh is present at the root and executable."""
        script = os.path.join(snakegauge.root(), "build.sh")
        self.assertTrue(os.path.isfile(script),
                        "SPEC.md requirement 1: no ./build.sh at the root of the work tree")
        self.assertTrue(os.access(script, os.X_OK),
                        "SPEC.md requirement 1: ./build.sh is present but not executable")

    def test_build_succeeds_and_leaves_the_binary(self):
        """[L1-r2] ./build.sh exits 0 and leaves an executable ./snake."""
        ok, detail = snakegauge.build()
        self.assertTrue(ok, detail)
        self.assertTrue(os.access(snakegauge.binary(), os.X_OK))

    def test_build_is_repeatable(self):
        """[L1-r4] a second ./build.sh on the same tree also succeeds.

        A build that works once usually means a generated file is being written
        into a source directory, and it is the next reader who finds out.
        """
        snakegauge.require_build(self)
        try:
            proc = subprocess.run(["./build.sh"], cwd=snakegauge.root(),
                                  capture_output=True, text=True,
                                  timeout=snakegauge.BUILD_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            self.fail("the second ./build.sh did not finish in %ds" % snakegauge.BUILD_TIMEOUT_S)
        self.assertEqual(proc.returncode, 0,
                         "SPEC.md requirement 4: a second build exited %d\n--- stderr ---\n%s"
                         % (proc.returncode, proc.stderr[-3000:]))
        self.assertTrue(os.access(snakegauge.binary(), os.X_OK),
                        "the second build removed ./snake and did not put it back")

    def test_version_answers_the_schema(self):
        """[L1-r5] `./snake --version` prints the schema string and exits 0.

        The one behaviour this rung pins. It is in the specification because a
        build that produces an unrunnable binary is not a build, and `--version`
        is the smallest question that distinguishes the two.
        """
        snakegauge.require_build(self)
        proc = subprocess.run([snakegauge.binary(), "--version"], cwd=snakegauge.root(),
                              capture_output=True, text=True, timeout=snakegauge.RUN_TIMEOUT_S)
        self.assertEqual(proc.returncode, 0,
                         "--version exited %d; stderr: %s" % (proc.returncode, proc.stderr[-1500:]))
        self.assertEqual(proc.stdout.strip(), "tui-snake/1",
                         "SPEC.md: --version must print tui-snake/1, printed %r" % proc.stdout[:200])

    def test_the_binary_does_not_need_a_terminal_to_start(self):
        """[L1-r7] `--version` works with stdout on a pipe, not only on a tty."""
        snakegauge.require_build(self)
        proc = subprocess.run([snakegauge.binary(), "--version"], cwd=snakegauge.root(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              stdin=subprocess.DEVNULL, timeout=snakegauge.RUN_TIMEOUT_S)
        self.assertEqual(proc.returncode, 0)
        self.assertIn(b"tui-snake/1", proc.stdout)


if __name__ == "__main__":
    unittest.main()
