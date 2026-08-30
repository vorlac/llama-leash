#!/bin/sh
# A green smoke test over what the seed already carries, so the visible suite
# starts non-vacuous and the arm's own first red test is its own doing.
out=$(./snake --version 2>/dev/null) || { echo "--version exited non-zero"; exit 1; }
[ "$out" = "tui-snake/1" ] || { echo "--version printed '$out', wanted tui-snake/1"; exit 1; }
