#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
CHECKER="$SKILL_DIR/check-css-classes.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

python3 "$CHECKER" >"$TMPDIR/clean.out" 2>"$TMPDIR/clean.err" || {
  cat "$TMPDIR/clean.out" "$TMPDIR/clean.err" >&2
  fail "clean CSS class check should pass"
}
grep -Fq "CSS-CLASSES OK" "$TMPDIR/clean.out" || {
  cat "$TMPDIR/clean.out" "$TMPDIR/clean.err" >&2
  fail "clean CSS class check did not print OK"
}
echo "PASS clean CSS class check"

FIXTURE="$TMPDIR/bogus-snippet.html"
cat >"$FIXTURE" <<'HTML'
<div class="frame zzz-not-a-class">
  <p class="feature-title">Bogus CSS class fixture</p>
</div>
HTML

if python3 "$CHECKER" --extra-html "$FIXTURE" >"$TMPDIR/bogus.out" 2>"$TMPDIR/bogus.err"; then
  cat "$TMPDIR/bogus.out" "$TMPDIR/bogus.err" >&2
  fail "CSS class check should fail on injected bogus class"
fi
grep -Fq "HALT: undefined CSS class(es)" "$TMPDIR/bogus.err" || {
  cat "$TMPDIR/bogus.out" "$TMPDIR/bogus.err" >&2
  fail "bogus CSS class check did not print HALT"
}
grep -Fq "$FIXTURE: zzz-not-a-class" "$TMPDIR/bogus.err" || {
  cat "$TMPDIR/bogus.out" "$TMPDIR/bogus.err" >&2
  fail "bogus CSS class check did not name fixture and class"
}
echo "PASS injected bogus CSS class is rejected"
