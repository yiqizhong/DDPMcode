#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
VERIFY="$SKILL_DIR/verify-model.py"
RENDER_MODEL="$SKILL_DIR/render-model.py"
VALIDATOR="$SKILL_DIR/validate-manifest.py"
RENDER_CONTENT="$SKILL_DIR/render-content.py"
MODELS_DIR="$ROOT/headset/models"
TMP_MODEL="_VERIFYTEST"
TMP_MANIFEST="$(mktemp)"
TMP_VALID_MANIFEST="$(mktemp)"
TMP_OUT="$(mktemp)"
TMP_ERR="$(mktemp)"

cleanup() {
  rm -rf "$MODELS_DIR/$TMP_MODEL"
  rm -f "$TMP_MANIFEST" "$TMP_VALID_MANIFEST" "$TMP_OUT" "$TMP_ERR"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_hash_prefix() {
  local manifest="$1"
  local expected_prefix="$2"
  local hash
  hash="$(python3 "$RENDER_CONTENT" "$ROOT/$manifest" | shasum -a 256 | awk '{print $1}')"
  [[ "$hash" == "$expected_prefix"* ]] || fail "$manifest hash $hash did not start with $expected_prefix"
  echo "PASS $manifest render-content sha256=$hash"
}

if [[ ! -f "$MODELS_DIR/HS-DEMO/index.html" || ! -f "$MODELS_DIR/HS-DEMO/audio-settings.html" ]]; then
  python3 "$RENDER_MODEL" HS-DEMO
fi

python3 "$VERIFY" HS-DEMO >"$TMP_OUT" 2>"$TMP_ERR" || {
  cat "$TMP_OUT" "$TMP_ERR" >&2
  fail "HS-DEMO verify-model should pass"
}
grep -Fq "index.html: OK" "$TMP_OUT" || fail "HS-DEMO verify output did not name index.html OK"
grep -Fq "audio-settings.html: OK" "$TMP_OUT" || fail "HS-DEMO verify output did not name audio-settings.html OK"
echo "PASS HS-DEMO verify-model"

rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/HS-DEMO" "$MODELS_DIR/$TMP_MODEL"
printf '\n' >>"$MODELS_DIR/$TMP_MODEL/audio-settings.html"

if python3 "$VERIFY" "$TMP_MODEL" >"$TMP_OUT" 2>"$TMP_ERR"; then
  cat "$TMP_OUT" "$TMP_ERR" >&2
  fail "drifted temp model verify-model should fail"
fi
grep -Fq "audio-settings.html: DRIFT" "$TMP_OUT" || fail "drift output did not name audio-settings.html"
echo "PASS drift detection fails as expected"

cat >"$TMP_MANIFEST" <<'MANIFEST'
title: Audio Settings
functions:
  - id: eq-audio
    components:
      - archetype: toggle
        label: Equalizer
MANIFEST

if python3 "$VALIDATOR" "$TMP_MANIFEST" >"$TMP_OUT" 2>"$TMP_ERR"; then
  cat "$TMP_OUT" "$TMP_ERR" >&2
  fail "snapshot manifest with components should halt"
fi
grep -Fq "function[eq-audio]" "$TMP_ERR" || fail "B.2 HALT did not name function[eq-audio]"
grep -Fq "snapshot functions/eq-audio.html" "$TMP_ERR" || fail "B.2 HALT did not mention snapshot path"
echo "PASS B.2 snapshot with components halts"

cat >"$TMP_VALID_MANIFEST" <<'MANIFEST'
title: Audio Settings
functions:
  - id: eq-audio
MANIFEST

python3 "$VALIDATOR" "$TMP_VALID_MANIFEST" >/dev/null || fail "snapshot manifest without components should pass"
python3 "$VALIDATOR" "$ROOT/headset/models/WL327/audio-settings.manifest" >/dev/null || fail "WL327 audio-settings regression should pass"
python3 "$VALIDATOR" "$ROOT/headset/models/HS-DEMO/audio-settings.manifest" >/dev/null || fail "HS-DEMO audio-settings regression should pass"
echo "PASS B.2 valid and regression manifests"

assert_hash_prefix "headset/models/WL327/audio-settings.manifest" "5f77a7f226ea"
assert_hash_prefix "headset/models/HS-DEMO/audio-settings.manifest" "d8aa56479f4b"
