#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-home.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expect_pass() {
  local manifest="$1"
  local label="$2"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if ! python3 "$VALIDATOR" "$manifest" >"$out" 2>"$err"; then
    cat "$out" "$err" >&2
    fail "$label should pass"
  fi
  grep -Fq "OK" "$out" || fail "$label did not print OK"
  echo "PASS $label"
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

cat >"$TMPDIR/missing-model.manifest" <<'MANIFEST'
marketing-name: Broken Headset
connectionType: wired
MANIFEST

cat >"$TMPDIR/unknown-connection.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-CONNECTION
connectionType: satellite
MANIFEST

cat >"$TMPDIR/feature-missing-icon.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-FEATURE
connectionType: wired
features:
  - label: Audio Settings
    link: audio-settings.html
MANIFEST

cat >"$TMPDIR/unknown-icon.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-ICON
connectionType: wired
features:
  - label: Audio Settings
    icon: nonexistent
    link: audio-settings.html
MANIFEST

cat >"$TMPDIR/no-features.manifest" <<'MANIFEST'
marketing-name: Homepage Only Headset
model-number: HOME-ONLY
connectionType: wired
MANIFEST

expect_pass "$ROOT/headset/models/HS-DEMO/home.manifest" "HS-DEMO"
expect_pass "$ROOT/headset/models/WL327/home.manifest" "WL327"
expect_halt "$TMPDIR/missing-model.manifest" "missing-model-number" 'missing required field `model-number`'
expect_halt "$TMPDIR/unknown-connection.manifest" "unknown-connectionType" 'connectionType `satellite` has no snippet connection/satellite.html'
expect_halt "$TMPDIR/feature-missing-icon.manifest" "feature-missing-icon" 'features[0]: feature missing `icon`'
expect_halt "$TMPDIR/unknown-icon.manifest" "unknown-icon" 'features[0].icon: icon id `nonexistent` has no asset icons/nonexistent.svg'
expect_pass "$TMPDIR/no-features.manifest" "no-features"
