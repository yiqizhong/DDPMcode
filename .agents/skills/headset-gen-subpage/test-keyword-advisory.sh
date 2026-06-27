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
if ! run_validator "$MATCH" "$MATCH_OUT" "$MATCH_ERR"; then
  cat "$MATCH_OUT" "$MATCH_ERR" >&2
  fail "keyword-match advisory manifest should remain structurally valid"
fi
grep -Fq "ADVISORY: function 'dell-audio-promotion' matches snapshot 'promotion-download' (keyword 'promotion')" "$MATCH_ERR" \
  || fail "expected promotion-download advisory for dell-audio-promotion"
echo "PASS assembled keyword match exits 0 and prints advisory"

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
echo "PASS assembled function without keyword has no advisory"

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
