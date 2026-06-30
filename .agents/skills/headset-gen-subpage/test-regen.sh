#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
REGEN="$SKILL_DIR/regen.sh"
VERIFY_ALL="$SKILL_DIR/verify-all.sh"
MODELS_DIR="$ROOT/headset/models"
TMPDIR="$(mktemp -d)"
TMP_MODEL="_REGENTEST"
trap 'rm -rf "$TMPDIR" "$MODELS_DIR/$TMP_MODEL"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[[ -x "$REGEN" ]] || fail "regen.sh must exist and be executable"

rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/WL527" "$MODELS_DIR/$TMP_MODEL"
printf '\n<!-- injected drift for regen regression -->\n' >>"$MODELS_DIR/$TMP_MODEL/audio-settings.html"

if bash "$VERIFY_ALL" >"$TMPDIR/verify-drift.out" 2>"$TMPDIR/verify-drift.err"; then
  cat "$TMPDIR/verify-drift.out" "$TMPDIR/verify-drift.err" >&2
  fail "verify-all should report injected drift before regen"
fi
grep -Fq "_REGENTEST" "$TMPDIR/verify-drift.out" || fail "verify-all output did not name temp model"
grep -Fq "audio-settings.html: DRIFT" "$TMPDIR/verify-drift.out" || {
  cat "$TMPDIR/verify-drift.out" "$TMPDIR/verify-drift.err" >&2
  fail "verify-all output did not report the drifted page"
}
echo "PASS verify-all reports injected drift"

if ! bash "$REGEN" >"$TMPDIR/regen.out" 2>"$TMPDIR/regen.err"; then
  cat "$TMPDIR/regen.out" "$TMPDIR/regen.err" >&2
  fail "regen should re-render drifted pages and end green"
fi
grep -Fq "_REGENTEST" "$TMPDIR/regen.out" || fail "regen output did not include temp model"
grep -Fq "VERIFY-ALL OK" "$TMPDIR/regen.out" || {
  cat "$TMPDIR/regen.out" "$TMPDIR/regen.err" >&2
  fail "regen did not run the all-model gate to green"
}
if grep -Fq "injected drift for regen regression" "$MODELS_DIR/$TMP_MODEL/audio-settings.html"; then
  fail "regen did not overwrite the injected drift"
fi
echo "PASS regen resolves drift and verifies all models"

rm -rf "$MODELS_DIR/$TMP_MODEL"
echo "PASS regen regression"
