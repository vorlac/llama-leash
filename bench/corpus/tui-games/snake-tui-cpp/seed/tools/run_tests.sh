#!/bin/sh
# The visible suite: build the program, then run every test the tree carries.
#
# It is deliberately unopinionated about what a test IS. Anything executable
# directly under tests/ is run from the root of the work tree and must exit 0 —
# a shell script, a compiled binary, a python file with a shebang. What the
# suite will not do is pass when it ran nothing: a glob that matches no files
# and exits 0 reports a green suite over an empty set, which is the one result
# that cannot be distinguished from a suite that is not wired up.
#
# On a fresh checkout this fails at the first step, because there is no
# build.sh yet. That is the honest state of a workspace with no program in it.

set -u
cd "$(dirname "$0")/.." || exit 2
root=$(pwd)

if [ ! -x ./build.sh ]; then
    if [ -f ./build.sh ]; then
        echo "FAIL: ./build.sh exists but is not executable (chmod +x build.sh)" >&2
    else
        echo "FAIL: no ./build.sh at the root of the work tree (SPEC.md section 2)" >&2
    fi
    exit 1
fi

echo "== build =="
if ! ./build.sh; then
    echo "FAIL: ./build.sh exited non-zero" >&2
    exit 1
fi
if [ ! -x ./snake ]; then
    echo "FAIL: ./build.sh succeeded but left no executable ./snake (SPEC.md requirement 2)" >&2
    exit 1
fi

echo "== tests =="
count=0
failed=0
if [ -d tests ]; then
    for t in tests/*; do
        [ -f "$t" ] || continue
        [ -x "$t" ] || continue
        count=$((count + 1))
        printf '%s ... ' "$t"
        if (cd "$root" && "./$t"); then
            echo ok
        else
            echo FAIL
            failed=$((failed + 1))
        fi
    done
fi

if [ "$count" -eq 0 ]; then
    echo "FAIL: no executable tests under tests/ — a suite that runs nothing is not green" >&2
    exit 1
fi

echo "== $count test(s), $failed failure(s) =="
[ "$failed" -eq 0 ] || exit 1
exit 0
