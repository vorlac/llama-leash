"""Shared state for the snake-tui-cpp gauge: build the tree once, run the binary.

The three check modules are loaded into ONE process by run.py, so a module-level
cache here means `./build.sh` runs once no matter how many checks need it. That
matters for more than speed: a build run three times would report three
different failures for one broken build, and the reader would have to work out
they were the same one.
"""

import json
import os
import subprocess
import sys

# A build may configure CMake and compile from cold. Generous, because the cost
# of a ceiling that is too low is a PASSING implementation scored as a failure,
# which is the one error this gauge must not make.
BUILD_TIMEOUT_S = 600
# One headless replay is a few thousand ticks of integer work at most. A second
# would do; twenty is the same asymmetry as above.
RUN_TIMEOUT_S = 20

_build = None


def root():
    """The work tree. run.py runs from it, and gauge/ is materialized inside."""
    return os.getcwd()


def build():
    """Run ./build.sh once and remember what happened.

    Returns (ok, detail). Never raises: a build that fails is a result the
    checks report, not an error that takes the whole gauge down.
    """
    global _build
    if _build is not None:
        return _build
    script = os.path.join(root(), "build.sh")
    if not os.path.isfile(script):
        _build = (False, "no ./build.sh at the root of the work tree")
        return _build
    if not os.access(script, os.X_OK):
        _build = (False, "./build.sh is not executable")
        return _build
    try:
        proc = subprocess.run(
            ["./build.sh"], cwd=root(), capture_output=True, text=True,
            timeout=BUILD_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        _build = (False, "./build.sh did not finish in %ds" % BUILD_TIMEOUT_S)
        return _build
    except OSError as exc:
        _build = (False, "./build.sh could not be executed: %s" % exc)
        return _build
    if proc.returncode != 0:
        _build = (False, "./build.sh exited %d\n--- stdout ---\n%s\n--- stderr ---\n%s"
                  % (proc.returncode, proc.stdout[-4000:], proc.stderr[-4000:]))
        return _build
    binary = os.path.join(root(), "snake")
    if not os.path.isfile(binary) or not os.access(binary, os.X_OK):
        _build = (False, "./build.sh exited 0 but left no executable ./snake")
        return _build
    _build = (True, "")
    return _build


def binary():
    return os.path.join(root(), "snake")


def headless(seed, script_text, timeout=RUN_TIMEOUT_S):
    """One headless replay. Returns (returncode, stdout, stderr)."""
    import tempfile
    fd, path = tempfile.mkstemp(prefix="gauge-script-", suffix=".txt")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(script_text)
        proc = subprocess.run(
            [binary(), "--headless", "--seed", str(seed), "--script", path],
            cwd=root(), capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return None, "", "timed out after %ds" % timeout
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def vectors():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "vectors.json")) as handle:
        return json.load(handle)


def require_build(case):
    ok, detail = build()
    if not ok:
        case.fail("the tree does not build, so nothing below can be judged: " + detail)
