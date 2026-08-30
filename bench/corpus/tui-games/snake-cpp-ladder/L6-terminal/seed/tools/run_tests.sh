#!/bin/sh
# The visible suite: build, then run every executable directly under tests/.
#
# Unopinionated about what a test IS — a shell script, a compiled binary, a
# python file with a shebang. What it will not do is pass when it ran nothing: a
# glob matching no files and exiting 0 reports a green suite over an empty set,
# which cannot be told from a suite that was never wired up.
set -u
cd "$(dirname "$0")/.." || exit 2
root=$(pwd)

if [ ! -x ./build.sh ]; then
    [ -f ./build.sh ] && echo "FAIL: ./build.sh is not executable (chmod +x build.sh)" >&2 \
                      || echo "FAIL: no ./build.sh at the root (SPEC.md section 2)" >&2
    exit 1
fi
echo "== build =="
./build.sh || { echo "FAIL: ./build.sh exited non-zero" >&2; exit 1; }
[ -x ./snake ] || { echo "FAIL: ./build.sh left no executable ./snake (requirement 2)" >&2; exit 1; }

echo "== tests =="
count=0; failed=0
if [ -d tests ]; then
    for t in tests/*; do
        [ -f "$t" ] && [ -x "$t" ] || continue
        count=$((count + 1))
        printf '%s ... ' "$t"
        if (cd "$root" && "./$t"); then echo ok; else echo FAIL; failed=$((failed + 1)); fi
    done
fi
[ "$count" -gt 0 ] || { echo "FAIL: no executable tests under tests/ — a suite that runs nothing is not green" >&2; exit 1; }
echo "== $count test(s), $failed failure(s) =="
[ "$failed" -eq 0 ] || exit 1
exit 0
