#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
VALIDATOR="$SKILL_DIR/validate-manifest.py"
HOME_VALIDATOR="$SKILL_DIR/validate-home.py"
VERIFY_ALL="$SKILL_DIR/verify-all.sh"
MODELS_DIR="$ROOT/headset/models"
TMPDIR="$(mktemp -d)"
TMP_MODEL="_GATETEST"
trap 'rm -rf "$TMPDIR" "$MODELS_DIR/$TMP_MODEL"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expect_halt() {
  local validator="$1"
  local manifest="$2"
  local label="$3"
  local expected="$4"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if python3 "$validator" "$manifest" >"$out" 2>"$err"; then
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

DUPLICATE_LABEL="$TMPDIR/duplicate-label.manifest"
cat >"$DUPLICATE_LABEL" <<'MANIFEST'
title: Duplicate Label Fixture
functions:
  - id: duplicate-label-fixture
    title: Noise Control
    components:
      - archetype: segmented
        label: " noise control "
        options:
          - {label: ANC, value: anc, selected: true}
          - {label: Transparency, value: transparency}
MANIFEST

MISSING_IMAGE="$TMPDIR/missing-image.manifest"
cat >"$MISSING_IMAGE" <<'MANIFEST'
marketing-name: Missing Image Headset
model-number: BAD-MISSING-IMAGE
connectionType: wired
MANIFEST

expect_halt "$VALIDATOR" "$DUPLICATE_LABEL" "duplicate-label" 'redundant `label` equals card title'
expect_halt "$HOME_VALIDATOR" "$MISSING_IMAGE" "missing-image" 'missing required field `image`'

rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/WL527" "$MODELS_DIR/$TMP_MODEL"
printf '\n<!-- injected drift for gate regression -->\n' >>"$MODELS_DIR/$TMP_MODEL/audio-settings.html"

if bash "$VERIFY_ALL" >"$TMPDIR/gate-drift.out" 2>"$TMPDIR/gate-drift.err"; then
  cat "$TMPDIR/gate-drift.out" "$TMPDIR/gate-drift.err" >&2
  fail "verify-all should fail on injected drift"
fi
grep -Fq "_GATETEST" "$TMPDIR/gate-drift.out" || fail "gate output did not name temp model"
grep -Fq "audio-settings.html: DRIFT" "$TMPDIR/gate-drift.out" || {
  cat "$TMPDIR/gate-drift.out" "$TMPDIR/gate-drift.err" >&2
  fail "gate output did not name drifted page"
}
echo "PASS verify-all catches injected drift"

rm -rf "$MODELS_DIR/$TMP_MODEL"
echo "PASS system gate regressions"
