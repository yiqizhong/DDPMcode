#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
CHECKER="$SKILL_DIR/check-requirements-coverage.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

copy_wl527() {
  local dest="$1"
  rm -rf "$dest"
  cp -R "$ROOT/headset/models/WL527" "$dest"
}

mutate_file() {
  local path="$1"
  local old="$2"
  local new="$3"
  PATH_TO_MUTATE="$path" OLD_TEXT="$old" NEW_TEXT="$new" python3 - <<'PY'
import os
import sys

path = os.environ["PATH_TO_MUTATE"]
old = os.environ["OLD_TEXT"]
new = os.environ["NEW_TEXT"]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
if old not in text:
    print("missing text to mutate in %s: %r" % (path, old), file=sys.stderr)
    sys.exit(1)
with open(path, "w", encoding="utf-8") as f:
    f.write(text.replace(old, new, 1))
PY
}

mutate_all() {
  local path="$1"
  local old="$2"
  local new="$3"
  PATH_TO_MUTATE="$path" OLD_TEXT="$old" NEW_TEXT="$new" python3 - <<'PY'
import os
import sys

path = os.environ["PATH_TO_MUTATE"]
old = os.environ["OLD_TEXT"]
new = os.environ["NEW_TEXT"]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
if old not in text:
    print("missing text to mutate in %s: %r" % (path, old), file=sys.stderr)
    sys.exit(1)
with open(path, "w", encoding="utf-8") as f:
    f.write(text.replace(old, new))
PY
}

expect_pass() {
  local model_dir="$1"
  local label="$2"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if ! python3 "$CHECKER" "$model_dir" >"$out" 2>"$err"; then
    cat "$out" "$err" >&2
    fail "$label should pass"
  fi
  grep -Fq "OK" "$out" || {
    cat "$out" "$err" >&2
    fail "$label did not print OK"
  }
  echo "PASS $label"
}

expect_skip() {
  local model_dir="$1"
  local label="$2"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if ! python3 "$CHECKER" "$model_dir" >"$out" 2>"$err"; then
    cat "$out" "$err" >&2
    fail "$label should skip cleanly"
  fi
  grep -Fq "SKIP" "$out" || {
    cat "$out" "$err" >&2
    fail "$label did not print SKIP"
  }
  echo "SKIP $label"
}

expect_halt() {
  local model_dir="$1"
  local label="$2"
  local expected="$3"
  local out="$TMPDIR/$label.out"
  local err="$TMPDIR/$label.err"

  if python3 "$CHECKER" "$model_dir" >"$out" 2>"$err"; then
    cat "$out" "$err" >&2
    fail "$label should HALT"
  fi
  grep -Fq "HALT" "$err" || {
    cat "$out" "$err" >&2
    fail "$label did not print HALT"
  }
  grep -Fq "$expected" "$err" || {
    cat "$out" "$err" >&2
    fail "$label did not name expected violation: $expected"
  }
  echo "HALT $label"
}

expect_skip "$ROOT/headset/models/HS-DEMO" "HS-DEMO-no-requirements"
expect_pass "$ROOT/headset/models/WL527" "WL527-requirements-coverage"

DROPPED_FUNCTION="$TMPDIR/dropped-function"
copy_wl527 "$DROPPED_FUNCTION"
mutate_file "$DROPPED_FUNCTION/home.manifest" "  - label: Automated Actions
    icon: settings
    link: automated-actions.html
" ""
expect_halt "$DROPPED_FUNCTION" "dropped-function" 'requirements function `Automated actions` has no matching home.manifest feature'

EXTRA_FEATURE="$TMPDIR/extra-feature"
copy_wl527 "$EXTRA_FEATURE"
mutate_file "$EXTRA_FEATURE/home.manifest" "  - label: Device Settings
    icon: settings
    link: device-settings.html
" "  - label: Device Settings
    icon: settings
    link: device-settings.html
  - label: Extra Settings
    icon: settings
    link: device-settings.html
"
expect_halt "$EXTRA_FEATURE" "extra-feature" 'home.manifest feature `Extra Settings` has no corresponding requirements function'

WRONG_MODEL="$TMPDIR/wrong-model"
copy_wl527 "$WRONG_MODEL"
mutate_file "$WRONG_MODEL/home.manifest" "model-number: WL527" "model-number: WL527X"
expect_halt "$WRONG_MODEL" "wrong-model" "Device Model mismatch"

WRONG_FIRMWARE="$TMPDIR/wrong-firmware"
copy_wl527 "$WRONG_FIRMWARE"
mutate_file "$WRONG_FIRMWARE/home.manifest" "firmware: 12.432.486.11" "firmware: 12.432.486.12"
expect_halt "$WRONG_FIRMWARE" "wrong-firmware" "Device Firmware mismatch"

DROPPED_IMAGE="$TMPDIR/dropped-image"
copy_wl527 "$DROPPED_IMAGE"
mutate_file "$DROPPED_IMAGE/home.manifest" "image: images/5027.png" "image: none"
expect_halt "$DROPPED_IMAGE" "dropped-image" 'requirements Image is present but home.manifest image is `none`'

WALKTHROUGH_TITLE="$TMPDIR/walkthrough-title"
copy_wl527 "$WALKTHROUGH_TITLE"
mutate_file "$WALKTHROUGH_TITLE/walkthrough.manifest" "  - title: Convenient Buttons" "  - title: Wrong Buttons"
expect_halt "$WALKTHROUGH_TITLE" "walkthrough-title" "Walkthrough step 2 title mismatch"

MISSING_COVERAGE="$TMPDIR/missing-coverage"
copy_wl527 "$MISSING_COVERAGE"
mutate_all "$MISSING_COVERAGE/coverage.md" "Audio setting #2." "Audio setting #2 DROPPED."
expect_halt "$MISSING_COVERAGE" "missing-coverage-clause" "coverage.md missing clause entry: Audio setting #2"

echo "PASS requirements coverage regressions"
