#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-manifest.py"
HOME_VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-home.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

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

TOOLTIP_MANIFEST="$TMPDIR/tooltip-key.manifest"
cat >"$TOOLTIP_MANIFEST" <<'MANIFEST'
title: Audio Settings
functions:
  - id: noise-control
    title: Noise Control
    components:
      - archetype: segmented
        icons: true
        options:
          - {label: ANC, value: anc, selected: true}
          - {label: Transparency, value: transparency}
          - {label: "Off", value: off}
        reveals:
          anc:
            - archetype: toggle
              label: Adaptive ANC
              tooltip: "Automatically adjusts Active Noise Cancellation levels based on your surroundings"
              value: false
MANIFEST

PRESET_GRID_MANIFEST="$TMPDIR/preset-grid-3-options.manifest"
cat >"$PRESET_GRID_MANIFEST" <<'MANIFEST'
title: Audio Settings
functions:
  - id: multimedia
    title: Multimedia
    components:
      - archetype: preset-grid
        label: Presets
        options:
          - {label: Bass Boost, value: bass-boost, selected: true}
          - {label: Speech Boost, value: speech-boost}
          - {label: Custom, value: custom}
MANIFEST

UNKNOWN_HOME_MANIFEST="$TMPDIR/unknown-home-key.manifest"
cat >"$UNKNOWN_HOME_MANIFEST" <<'MANIFEST'
marketing-name: Broken Headset
model-number: BAD-HOME-KEY
image: images/broken.png
connectionType: wired
tooltip: "This key is not in home-schema.py"
MANIFEST

expect_halt "$VALIDATOR" "$TOOLTIP_MANIFEST" "tooltip-key" 'unknown key `tooltip`'
expect_halt "$VALIDATOR" "$PRESET_GRID_MANIFEST" "preset-grid-3-options" "preset-grid"
expect_halt "$HOME_VALIDATOR" "$UNKNOWN_HOME_MANIFEST" "unknown-home-key" 'unknown key `tooltip`'

BAD_SLIDER_RANGE="$TMPDIR/bad-slider-range.manifest"
cat >"$BAD_SLIDER_RANGE" <<'MANIFEST'
title: Slider Fixture
functions:
  - id: slider-fixture
    title: Slider Fixture
    components:
      - archetype: slider
        min: 0
        max: 3
        value: 99
MANIFEST

BAD_SLIDER_TYPE="$TMPDIR/bad-slider-type.manifest"
cat >"$BAD_SLIDER_TYPE" <<'MANIFEST'
title: Slider Fixture
functions:
  - id: slider-fixture
    title: Slider Fixture
    components:
      - archetype: slider
        min: low
        max: 3
        value: 2
MANIFEST

BAD_SLIDER_ORDER="$TMPDIR/bad-slider-order.manifest"
cat >"$BAD_SLIDER_ORDER" <<'MANIFEST'
title: Slider Fixture
functions:
  - id: slider-fixture
    title: Slider Fixture
    components:
      - archetype: slider
        min: 3
        max: 3
        value: 3
MANIFEST

BAD_SLIDER_STOPS="$TMPDIR/bad-slider-stops.manifest"
cat >"$BAD_SLIDER_STOPS" <<'MANIFEST'
title: Slider Fixture
functions:
  - id: slider-fixture
    title: Slider Fixture
    components:
      - archetype: slider
        min: 0
        max: 3
        value: 2
        stops: 1
MANIFEST

GOOD_SLIDER="$TMPDIR/good-slider.manifest"
cat >"$GOOD_SLIDER" <<'MANIFEST'
title: Slider Fixture
functions:
  - id: slider-fixture
    title: Slider Fixture
    components:
      - archetype: slider
        min: 0
        max: 3
        value: 2
        stops: 4
MANIFEST

ZERO_SELECTED="$TMPDIR/zero-selected.manifest"
cat >"$ZERO_SELECTED" <<'MANIFEST'
title: Selector Fixture
functions:
  - id: selector-fixture
    title: Selector Fixture
    components:
      - archetype: segmented
        options:
          - {label: ANC, value: anc}
          - {label: "Off", value: off}
MANIFEST

EXACTLY_ONE_SELECTED="$TMPDIR/exactly-one-selected.manifest"
cat >"$EXACTLY_ONE_SELECTED" <<'MANIFEST'
title: Selector Fixture
functions:
  - id: selector-fixture
    title: Selector Fixture
    components:
      - archetype: segmented
        options:
          - {label: ANC, value: anc, selected: true}
          - {label: "Off", value: off}
MANIFEST

expect_halt "$VALIDATOR" "$BAD_SLIDER_RANGE" "bad-slider-range" "slider value 99 is outside min 0 and max 3"
expect_halt "$VALIDATOR" "$BAD_SLIDER_TYPE" "bad-slider-type" 'slider field `min` must be a number'
expect_halt "$VALIDATOR" "$BAD_SLIDER_ORDER" "bad-slider-order" "slider requires min < max (got min 3, max 3)"
expect_halt "$VALIDATOR" "$BAD_SLIDER_STOPS" "bad-slider-stops" 'slider field `stops` must be an integer >= 2'
python3 "$VALIDATOR" "$GOOD_SLIDER"

expect_halt "$VALIDATOR" "$ZERO_SELECTED" "zero-selected" 'a selector needs exactly one option marked `selected`'
python3 "$VALIDATOR" "$EXACTLY_ONE_SELECTED"

echo "PASS manifest hardening regressions"
