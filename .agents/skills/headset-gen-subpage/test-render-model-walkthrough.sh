#!/usr/bin/env bash
# test-render-model-walkthrough.sh — FIX 2 regression: render-model.py <MODEL> must also
# render walkthrough.html when headset/models/<MODEL>/walkthrough.manifest exists, byte-
# identical to running shared-gen-walkthrough/render-walkthrough.py directly — so the
# documented Definition-of-Done path (render-model.py + verify-model.py) is complete without
# a third, separately-remembered script.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDER_MODEL="$ROOT/.agents/skills/headset-gen-subpage/render-model.py"
RENDER_WALKTHROUGH="$ROOT/.agents/skills/shared-gen-walkthrough/render-walkthrough.py"
MODELS_DIR="$ROOT/headset/models"
TMP_MODEL="_WTRENDERTEST"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR" "$MODELS_DIR/$TMP_MODEL"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

# WL527 is the reference model that carries a real walkthrough.manifest.
[[ -f "$MODELS_DIR/WL527/walkthrough.manifest" ]] || fail "fixture prerequisite missing: WL527/walkthrough.manifest"

rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/WL527" "$MODELS_DIR/$TMP_MODEL"
# Corrupt the on-disk walkthrough.html so a stale/hand-edited copy cannot masquerade as a
# correct render-model.py run — render-model.py must overwrite it from the manifest.
printf '\n<!-- stale walkthrough, must be overwritten -->\n' >>"$MODELS_DIR/$TMP_MODEL/walkthrough.html"

RENDER_MODEL_OUT="$TMPDIR/render-model.out"
python3 "$RENDER_MODEL" "$TMP_MODEL" >"$RENDER_MODEL_OUT" 2>&1 || {
  cat "$RENDER_MODEL_OUT" >&2
  fail "render-model.py should succeed on a model with walkthrough.manifest"
}

grep -Fq "walkthrough.html" "$RENDER_MODEL_OUT" || {
  cat "$RENDER_MODEL_OUT" >&2
  fail "render-model.py 'Wrote N file(s)' report did not include walkthrough.html"
}
echo "PASS render-model.py reports walkthrough.html in its written-file list"

[[ -f "$MODELS_DIR/$TMP_MODEL/walkthrough.html" ]] || fail "render-model.py did not write walkthrough.html"
if grep -Fq "stale walkthrough, must be overwritten" "$MODELS_DIR/$TMP_MODEL/walkthrough.html"; then
  fail "render-model.py did not overwrite the stale walkthrough.html"
fi
echo "PASS render-model.py overwrote the stale walkthrough.html"

# Byte-identical to render-walkthrough.py's own direct-to-stdout output.
DIRECT_OUT="$TMPDIR/direct-walkthrough.html"
python3 "$RENDER_WALKTHROUGH" headset "$TMP_MODEL" - >"$DIRECT_OUT" 2>"$TMPDIR/direct.err" || {
  cat "$TMPDIR/direct.err" >&2
  fail "render-walkthrough.py direct run failed"
}

if ! diff -u "$DIRECT_OUT" "$MODELS_DIR/$TMP_MODEL/walkthrough.html" >"$TMPDIR/walkthrough.diff"; then
  cat "$TMPDIR/walkthrough.diff" >&2
  fail "render-model.py's walkthrough.html is NOT byte-identical to render-walkthrough.py's direct output"
fi
echo "PASS render-model.py's walkthrough.html is byte-identical to render-walkthrough.py's direct output"

# A model with NO walkthrough.manifest must not gain a walkthrough.html and must not appear
# in the written-file report (regression guard: the new code path must be conditional).
rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/HS-DEMO" "$MODELS_DIR/$TMP_MODEL"
[[ ! -f "$MODELS_DIR/$TMP_MODEL/walkthrough.manifest" ]] || fail "test setup: HS-DEMO fixture unexpectedly has walkthrough.manifest"

NO_WT_OUT="$TMPDIR/no-walkthrough.out"
python3 "$RENDER_MODEL" "$TMP_MODEL" >"$NO_WT_OUT" 2>&1 || {
  cat "$NO_WT_OUT" >&2
  fail "render-model.py should succeed on a model without walkthrough.manifest"
}
[[ ! -f "$MODELS_DIR/$TMP_MODEL/walkthrough.html" ]] || fail "render-model.py wrote walkthrough.html for a model with no walkthrough.manifest"
grep -Fq "walkthrough.html" "$NO_WT_OUT" && fail "render-model.py report mentioned walkthrough.html for a model with no walkthrough.manifest"
echo "PASS render-model.py does not render walkthrough.html when walkthrough.manifest is absent"

echo "PASS render-model walkthrough regression"
