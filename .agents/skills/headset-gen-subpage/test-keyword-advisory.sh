#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-manifest.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

run_validator() {
  local manifest="$1"
  local out="$2"
  local err="$3"
  set +e
  python3 "$VALIDATOR" "$manifest" >"$out" 2>"$err"
  local status=$?
  set -e
  return "$status"
}

# ---- Case 1: keyword match with NO opt-out → HALT --------------------------------
MATCH="$TMPDIR/match.manifest"
cat >"$MATCH" <<'YAML'
title: Device Settings
functions:
  - id: dell-audio-promotion
    title: Dell Audio Promotion
    components:
      - archetype: toggle
        label: Show promotion
        value: true
YAML

MATCH_OUT="$TMPDIR/match.out"
MATCH_ERR="$TMPDIR/match.err"
if run_validator "$MATCH" "$MATCH_OUT" "$MATCH_ERR"; then
  cat "$MATCH_OUT" "$MATCH_ERR" >&2
  fail "keyword-match with no opt-out should HALT (exit non-zero)"
fi
grep -Fq "promotion-download" "$MATCH_ERR" \
  || fail "HALT message should name the matched snapshot id 'promotion-download'"
grep -Fq "promotion" "$MATCH_ERR" \
  || fail "HALT message should name the matched keyword 'promotion'"
echo "PASS assembled keyword match with no opt-out HALTs and names promotion-download"

# Sanity: the REAL WL327/device-settings.manifest (dell-audio-promotion + toggle) also HALTs
REAL_DEVICE="$ROOT/headset/models/WL327/device-settings.manifest"
REAL_OUT="$TMPDIR/real.out"
REAL_ERR="$TMPDIR/real.err"
if run_validator "$REAL_DEVICE" "$REAL_OUT" "$REAL_ERR"; then
  cat "$REAL_OUT" "$REAL_ERR" >&2
  fail "WL327/device-settings.manifest should HALT (dell-audio-promotion has no opt-out)"
fi
grep -Fq "promotion-download" "$REAL_ERR" \
  || fail "WL327/device-settings.manifest HALT message should name promotion-download"
echo "PASS WL327/device-settings.manifest HALTs as expected"

# ---- Case 2: keyword match WITH valid opt-out → advisory only, exit 0 ---------------
OPTOUT="$TMPDIR/optout.manifest"
cat >"$OPTOUT" <<'YAML'
title: Device Settings
functions:
  - id: dell-audio-promotion
    title: Dell Audio Promotion
    snapshot-opt-out: promotion-download
    opt-out-reason: A real on/off setting for promo notifications, not the download card.
    components:
      - archetype: toggle
        label: Enable Dell Audio Promotion
        value: false
YAML

OPTOUT_OUT="$TMPDIR/optout.out"
OPTOUT_ERR="$TMPDIR/optout.err"
if ! run_validator "$OPTOUT" "$OPTOUT_OUT" "$OPTOUT_ERR"; then
  cat "$OPTOUT_OUT" "$OPTOUT_ERR" >&2
  fail "valid opt-out should pass validation (exit 0)"
fi
grep -Fq "ADVISORY:" "$OPTOUT_ERR" \
  || fail "valid opt-out should still print the advisory"
grep -Fq "passes schema validation" "$OPTOUT_OUT" \
  || fail "valid opt-out should print schema validation success"
echo "PASS valid snapshot-opt-out passes with advisory only"

# ---- Case 3: opt-out with WRONG snapshot id → HALT ---------------------------------
WRONG_SNAP="$TMPDIR/wrong-snap.manifest"
cat >"$WRONG_SNAP" <<'YAML'
title: Device Settings
functions:
  - id: dell-audio-promotion
    title: Dell Audio Promotion
    snapshot-opt-out: eq-audio
    opt-out-reason: Testing wrong snapshot id.
    components:
      - archetype: toggle
        label: Enable Dell Audio Promotion
        value: false
YAML

WRONG_SNAP_OUT="$TMPDIR/wrong-snap.out"
WRONG_SNAP_ERR="$TMPDIR/wrong-snap.err"
if run_validator "$WRONG_SNAP" "$WRONG_SNAP_OUT" "$WRONG_SNAP_ERR"; then
  cat "$WRONG_SNAP_OUT" "$WRONG_SNAP_ERR" >&2
  fail "opt-out naming wrong snapshot should HALT"
fi
echo "PASS opt-out with wrong snapshot id HALTs"

# ---- Case 4: opt-out with NO keyword match → HALT (stale/blanket opt-out) ----------
NO_MATCH_OPTOUT="$TMPDIR/no-match-optout.manifest"
cat >"$NO_MATCH_OPTOUT" <<'YAML'
title: Device Settings
functions:
  - id: sidetone-level
    title: Sidetone Level
    snapshot-opt-out: promotion-download
    opt-out-reason: Trying to add a blanket opt-out where there is no keyword match.
    components:
      - archetype: slider
        min: 0
        max: 10
        value: 5
YAML

NO_MATCH_OPTOUT_OUT="$TMPDIR/no-match-optout.out"
NO_MATCH_OPTOUT_ERR="$TMPDIR/no-match-optout.err"
if run_validator "$NO_MATCH_OPTOUT" "$NO_MATCH_OPTOUT_OUT" "$NO_MATCH_OPTOUT_ERR"; then
  cat "$NO_MATCH_OPTOUT_OUT" "$NO_MATCH_OPTOUT_ERR" >&2
  fail "opt-out with no keyword match should HALT (stale opt-out)"
fi
echo "PASS stale opt-out (no keyword match) HALTs"

# ---- Case 5: opt-out with empty reason → HALT --------------------------------------
EMPTY_REASON="$TMPDIR/empty-reason.manifest"
cat >"$EMPTY_REASON" <<'YAML'
title: Device Settings
functions:
  - id: dell-audio-promotion
    title: Dell Audio Promotion
    snapshot-opt-out: promotion-download
    opt-out-reason: ''
    components:
      - archetype: toggle
        label: Enable Dell Audio Promotion
        value: false
YAML

EMPTY_REASON_OUT="$TMPDIR/empty-reason.out"
EMPTY_REASON_ERR="$TMPDIR/empty-reason.err"
if run_validator "$EMPTY_REASON" "$EMPTY_REASON_OUT" "$EMPTY_REASON_ERR"; then
  cat "$EMPTY_REASON_OUT" "$EMPTY_REASON_ERR" >&2
  fail "opt-out with empty reason should HALT"
fi
echo "PASS opt-out with empty opt-out-reason HALTs"

# ---- Case 6: normal assembled function with NO keyword match → no HALT, no advisory --
NO_MATCH="$TMPDIR/no-match.manifest"
cat >"$NO_MATCH" <<'YAML'
title: Device Settings
functions:
  - id: sidetone-level
    title: Sidetone Level
    components:
      - archetype: slider
        min: 0
        max: 10
        value: 5
YAML

NO_MATCH_OUT="$TMPDIR/no-match.out"
NO_MATCH_ERR="$TMPDIR/no-match.err"
if ! run_validator "$NO_MATCH" "$NO_MATCH_OUT" "$NO_MATCH_ERR"; then
  cat "$NO_MATCH_OUT" "$NO_MATCH_ERR" >&2
  fail "no-keyword manifest should remain structurally valid"
fi
if grep -Fq "ADVISORY:" "$NO_MATCH_ERR"; then
  cat "$NO_MATCH_ERR" >&2
  fail "unexpected advisory for no-keyword assembled function"
fi
echo "PASS assembled function without keyword match has no HALT and no advisory"

# ---- Case 7: regression — real subpage manifests still pass -------------------------
for manifest in "$ROOT/headset/models/WL327/audio-settings.manifest" "$ROOT/headset/models/HS-DEMO/audio-settings.manifest"; do
  OUT="$TMPDIR/$(basename "$(dirname "$manifest")").out"
  ERR="$TMPDIR/$(basename "$(dirname "$manifest")").err"
  if ! run_validator "$manifest" "$OUT" "$ERR"; then
    cat "$OUT" "$ERR" >&2
    fail "$manifest should still pass validation"
  fi
  grep -Fq "passes schema validation" "$OUT" || fail "$manifest did not print schema validation success"
done
echo "PASS real subpage manifests keep exit-0 validation behavior"

# ---- Case 8: regression — HS-DEMO render hash unchanged ---------------------------
RENDER_HASH="$(python3 "$ROOT/.agents/skills/headset-gen-subpage/render-content.py" \
  "$ROOT/headset/models/HS-DEMO/audio-settings.manifest" | shasum -a 256 | cut -c1-12)"
if [ "$RENDER_HASH" != "d8aa56479f4b" ]; then
  fail "HS-DEMO/audio-settings render hash changed: got $RENDER_HASH, expected d8aa56479f4b (gate-only change must not affect generation)"
fi
echo "PASS HS-DEMO/audio-settings render hash is unchanged (d8aa56479f4b)"

echo ""
echo "All tests passed."
