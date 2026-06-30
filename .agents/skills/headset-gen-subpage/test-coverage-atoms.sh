#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
CHECKER="$SKILL_DIR/check-coverage-atoms.py"
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

write_correct_atoms() {
  local model_dir="$1"
  cat >"$model_dir/coverage.md" <<'EOF'
# Atom Coverage

| Atom ID | Requirement | Locator | Expected | Verdict |
|---|---|---|---|---|
| Audio setting #1.a | Noise Control exists. | `audio-settings::noise-control` | `function "Noise Control"` | pass |
| Audio setting #1.b | Noise Control modes are ANC, Transparency, Off. | `audio-settings::noise-control::options` | `anc, transparency, off` | pass |
| Audio setting #1.c | ANC is selected by default. | `audio-settings::noise-control::option(anc).selected` | `true` | pass |
| Audio setting #1.d | ANC reveals Adaptive ANC. | `audio-settings::noise-control::reveals.anc` | `toggle "Adaptive ANC"` | pass |
| Audio setting #2.a | Sidetone owns a sidetone-level dependent. | `audio-settings::collaboration::component(sidetone).dependents` | `slider "Sidetone Level"` | pass |
| Audio setting #3.a | Custom preset reveals EQ. | `audio-settings::multimedia::component(presets).reveals.custom` | `function "eq-audio"` | pass |
| Automated actions #1.a | When removed owns Pause Music. | `automated-actions::wear-detection::dependents.card(when-headset-removed)::component(pause-music)` | `toggle "Pause Music"` | pass |
| Device settings #1.a | Auto Off owns Power-off dropdown. | `device-settings::auto-off::dependents` | `dropdown "Power off after"` | pass |
| Device settings #2.a | Audio Guidance has tones and voice. | `device-settings::audio-guidance::dependents.component(guidance-type)::options` | `tones, voice` | pass |
| Device settings #4.a | Download Dell Audio uses the promotion snapshot. | `device-settings::promotion-download` | `function "Download Dell Audio"` | pass |
| Manual review #1 | Human-only prose fidelity note. | `n/a` | `reviewer confirmed` | pass |
EOF
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

CORRECT="$TMPDIR/correct"
copy_wl527 "$CORRECT"
write_correct_atoms "$CORRECT"
expect_pass "$CORRECT" "all-correct"

WRONG_EXPECTED="$TMPDIR/wrong-expected"
copy_wl527 "$WRONG_EXPECTED"
write_correct_atoms "$WRONG_EXPECTED"
mutate_file "$WRONG_EXPECTED/coverage.md" '`anc, transparency, off`' '`anc, transparency`'
expect_halt "$WRONG_EXPECTED" "wrong-expected" "Audio setting #1.b"

UNRESOLVABLE="$TMPDIR/unresolvable"
copy_wl527 "$UNRESOLVABLE"
write_correct_atoms "$UNRESOLVABLE"
mutate_file "$UNRESOLVABLE/coverage.md" '`audio-settings::noise-control::reveals.anc`' '`audio-settings::missing-function::reveals.anc`'
expect_halt "$UNRESOLVABLE" "unresolvable-locator" "Audio setting #1.d"

expect_skip "$ROOT/headset/models/HS-DEMO" "missing-requirements-or-coverage"

echo "PASS coverage atom regressions"
