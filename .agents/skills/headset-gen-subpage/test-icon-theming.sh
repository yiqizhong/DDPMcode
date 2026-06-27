#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-content.py"
ICON_DIR="$ROOT/.agents/skills/headset-shared/segment-icons"
CSS="$ROOT/headset/headset.css"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

for icon in "$ICON_DIR"/*.svg; do
  grep -Fq 'fill="currentColor"' "$icon" || fail "$(basename "$icon") missing fill=\"currentColor\""
  if grep -Fq '#0E0E0E' "$icon"; then
    fail "$(basename "$icon") still hardcodes #0E0E0E"
  fi
done
echo "PASS segment icon SVGs use currentColor"

grep -A12 '^\.segment-icon {' "$CSS" | grep -Fq 'color: var(--color-text-strong);' \
  || fail ".segment-icon does not set the unselected icon color to var(--color-text-strong)"
grep -A4 '^\.segment:has(.segment-input:checked) \.segment-icon {' "$CSS" | grep -Fq 'color: var(--color-surface);' \
  || fail "selected segment icon rule does not set color to var(--color-surface)"
echo "PASS segment icon CSS covers unselected and selected states"

SYNTH="$TMPDIR/synthetic-icons.manifest"
cat >"$SYNTH" <<'YAML'
title: Synthetic Icon Theming
functions:
  - id: synthetic-noise-control
    title: Noise Control
    components:
      - archetype: segmented
        icons: true
        options:
          - label: ANC
            value: anc
            selected: true
          - label: Off
            value: off
YAML

FIRST=""
FIRST_OUT="$TMPDIR/synthetic.1.html"
for i in $(seq 1 10); do
  OUT="$TMPDIR/synthetic.$i.html"
  python3 "$RENDERER" "$SYNTH" >"$OUT"
  HASH="$(shasum -a 256 "$OUT" | awk '{print $1}')"
  if [[ -z "$FIRST" ]]; then
    FIRST="$HASH"
  elif [[ "$HASH" != "$FIRST" ]]; then
    fail "synthetic render $i sha256 $HASH != first run $FIRST"
  fi
done
grep -Fq 'fill="currentColor"' "$FIRST_OUT" || fail "synthetic render did not emit currentColor segment icons"
if grep -Fq '#0E0E0E' "$FIRST_OUT"; then
  fail "synthetic render still emits hardcoded #0E0E0E segment icon fill"
fi
echo "PASS synthetic segment-icon render is 10x byte-identical sha256=$FIRST"

HS_EXPECTED="d8aa56479f4b017668d3f8fdcf66998da6466c5f97fd8e1f8341a8c08dfa5ca3"
HS_HASH="$(python3 "$RENDERER" "$ROOT/headset/models/HS-DEMO/audio-settings.manifest" | shasum -a 256 | awk '{print $1}')"
[[ "$HS_HASH" == "$HS_EXPECTED" ]] || fail "HS-DEMO content hash changed: got $HS_HASH, expected $HS_EXPECTED"
echo "PASS HS-DEMO content hash unchanged sha256=$HS_HASH"
