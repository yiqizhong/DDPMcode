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
image: images/broken.png
connectionType: satellite
MANIFEST

cat >"$TMPDIR/feature-missing-icon.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-FEATURE
image: images/broken.png
connectionType: wired
features:
  - label: Audio Settings
    link: audio-settings.html
MANIFEST

cat >"$TMPDIR/unknown-icon.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-ICON
image: images/broken.png
connectionType: wired
features:
  - label: Audio Settings
    icon: nonexistent
    link: audio-settings.html
MANIFEST

cat >"$TMPDIR/no-features.manifest" <<'MANIFEST'
marketing-name: Homepage Only Headset
model-number: HOME-ONLY
image: images/home-only.png
connectionType: wired
MANIFEST
mkdir -p "$TMPDIR/images"; : > "$TMPDIR/images/home-only.png"

cat >"$TMPDIR/abs-image.manifest" <<'MANIFEST'
marketing-name: Abs Path Headset
model-number: BAD-ABS-IMAGE
image: C:\Users\Yiqi\5027.png
connectionType: wired
MANIFEST

cat >"$TMPDIR/missing-image-file.manifest" <<'MANIFEST'
marketing-name: Missing File Headset
model-number: BAD-MISSING-FILE
image: images/not-on-disk.png
connectionType: wired
MANIFEST

cat >"$TMPDIR/missing-image.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-MISSING-IMAGE
connectionType: wired
MANIFEST

cat >"$TMPDIR/image-none-without-reason.manifest" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-IMAGE-NONE
image: none
connectionType: wired
MANIFEST

cat >"$TMPDIR/image-none-with-reason.manifest" <<'MANIFEST'
marketing-name: Opt Out Headset
model-number: IMAGE-OPT-OUT
image: none
opt-out-reason: Test fixture has no supplied device image.
connectionType: wired
MANIFEST

expect_pass "$ROOT/headset/models/HS-DEMO/home.manifest" "HS-DEMO"
expect_pass "$ROOT/headset/models/FIXTURE/home.manifest" "FIXTURE"
expect_halt "$TMPDIR/missing-model.manifest" "missing-model-number" 'missing required field `model-number`'
expect_halt "$TMPDIR/missing-image.manifest" "missing-image" 'missing required field `image`'
expect_halt "$TMPDIR/image-none-without-reason.manifest" "image-none-without-reason" '`image: none` requires a non-empty `opt-out-reason`'
expect_pass "$TMPDIR/image-none-with-reason.manifest" "image-none-with-reason"
expect_halt "$TMPDIR/unknown-connection.manifest" "unknown-connectionType" 'connectionType `satellite` has no snippet connection/satellite.html'
expect_halt "$TMPDIR/feature-missing-icon.manifest" "feature-missing-icon" 'features[0]: feature missing `icon`'
expect_halt "$TMPDIR/unknown-icon.manifest" "unknown-icon" 'features[0].icon: icon id `nonexistent` has no asset icons/nonexistent.svg'
expect_pass "$TMPDIR/no-features.manifest" "no-features"
expect_halt "$TMPDIR/abs-image.manifest" "abs-image-path" 'must be a relative path inside the model folder'
expect_halt "$TMPDIR/missing-image-file.manifest" "missing-image-file" 'image file not found'
