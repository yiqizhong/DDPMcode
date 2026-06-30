#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/shared-gen-walkthrough/validate-walkthrough.py"
RENDERER="$ROOT/.agents/skills/shared-gen-walkthrough/render-walkthrough.py"
MODELS_DIR="$ROOT/headset/models"
TMPDIR="$(mktemp -d)"
TMP_MODEL="_WTBAD"
trap 'rm -rf "$TMPDIR" "$MODELS_DIR/$TMP_MODEL"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expect_halt() {
  local manifest="$1"
  local label="$2"
  local expected="$3"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if python3 "$VALIDATOR" "$manifest" >"$out" 2>"$err"; then
    cat "$out" "$err" >&2
    fail "$label should HALT"
  fi
  grep -Fq "HALT" "$err" || fail "$label did not print HALT"
  grep -Fq "$expected" "$err" || {
    cat "$out" "$err" >&2
    fail "$label did not name expected violation: $expected"
  }
  echo "HALT $label"
}

GOOD="$TMPDIR/good-walkthrough.manifest"
cat >"$GOOD" <<'MANIFEST'
title: Getting Started
cta: Done
done-link: index.html
steps:
  - title: First step
    body: Start here.
    image: images/start.png
  - title: Second step
    body: Finish here.
MANIFEST

UNKNOWN_TOP="$TMPDIR/unknown-top.manifest"
cat >"$UNKNOWN_TOP" <<'MANIFEST'
title: Getting Started
subtitle: Not allowed
steps:
  - title: First step
    body: Start here.
MANIFEST

UNKNOWN_STEP="$TMPDIR/unknown-step.manifest"
cat >"$UNKNOWN_STEP" <<'MANIFEST'
title: Getting Started
steps:
  - title: First step
    body: Start here.
    nav: Next
MANIFEST

MISSING_BODY="$TMPDIR/missing-body.manifest"
cat >"$MISSING_BODY" <<'MANIFEST'
title: Getting Started
steps:
  - title: First step
MANIFEST

python3 "$VALIDATOR" "$GOOD"
expect_halt "$UNKNOWN_TOP" "unknown-top" 'unknown key `subtitle`'
expect_halt "$UNKNOWN_STEP" "unknown-step" 'unknown key `nav`'
expect_halt "$MISSING_BODY" "missing-body" "step 1 is missing required 'body'"

rm -rf "$MODELS_DIR/$TMP_MODEL"
mkdir -p "$MODELS_DIR/$TMP_MODEL"
cp "$UNKNOWN_STEP" "$MODELS_DIR/$TMP_MODEL/walkthrough.manifest"
if python3 "$RENDERER" headset "$TMP_MODEL" - >"$TMPDIR/render-bad.out" 2>"$TMPDIR/render-bad.err"; then
  cat "$TMPDIR/render-bad.out" "$TMPDIR/render-bad.err" >&2
  fail "renderer should HALT on an invalid walkthrough manifest"
fi
grep -Fq "HALT" "$TMPDIR/render-bad.err" || fail "renderer did not print HALT"
grep -Fq 'unknown key `nav`' "$TMPDIR/render-bad.err" || {
  cat "$TMPDIR/render-bad.out" "$TMPDIR/render-bad.err" >&2
  fail "renderer HALT did not include validator violation"
}
echo "HALT renderer-invalid-walkthrough"

echo "PASS walkthrough validation regressions"
