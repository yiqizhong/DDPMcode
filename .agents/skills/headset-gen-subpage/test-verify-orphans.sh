#!/usr/bin/env bash
# test-verify-orphans.sh — FIX 4 regression: verify-model.py must detect
#   (a) an orphan manifest — a *.manifest in a model dir that no home.manifest feature
#       links to, so it is never validated/rendered/reported by anything, and
#   (b) a stray HTML page — a hand-written *.html not produced by the render pipeline.
# Both are general checks (glob every model dir's top level), not fixture-specific.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$ROOT/.agents/skills/headset-gen-subpage"
VERIFY="$SKILL_DIR/verify-model.py"
MODELS_DIR="$ROOT/headset/models"
TMP_MODEL="_ORPHANTEST"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR" "$MODELS_DIR/$TMP_MODEL"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# 1. Orphan manifest: a *.manifest not reachable from home.manifest.features[].
#    Must be caught even with --manifests-only (no HTML needed on disk), so it also
#    covers gitignored-HTML fixture models (verify-all.sh's skip-drift branch).
# ---------------------------------------------------------------------------
rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/HS-DEMO" "$MODELS_DIR/$TMP_MODEL"
cat >"$MODELS_DIR/$TMP_MODEL/orphaned-feature.manifest" <<'MANIFEST'
title: Orphaned Feature
functions: []
MANIFEST

ORPHAN_OUT="$TMPDIR/orphan.out"
ORPHAN_ERR="$TMPDIR/orphan.err"
if python3 "$VERIFY" "$TMP_MODEL" --manifests-only >"$ORPHAN_OUT" 2>"$ORPHAN_ERR"; then
  cat "$ORPHAN_OUT" "$ORPHAN_ERR" >&2
  fail "verify-model.py --manifests-only should FAIL when an orphan manifest is present"
fi
grep -Fq "orphaned-feature.manifest: DRIFT orphan manifest" "$ORPHAN_OUT" || {
  cat "$ORPHAN_OUT" "$ORPHAN_ERR" >&2
  fail "orphan manifest was not named in --manifests-only output"
}
echo "PASS --manifests-only catches an orphan manifest"

# Same fixture, full (non --manifests-only) run must also catch it.
FULL_OUT="$TMPDIR/full.out"
FULL_ERR="$TMPDIR/full.err"
if python3 "$VERIFY" "$TMP_MODEL" >"$FULL_OUT" 2>"$FULL_ERR"; then
  cat "$FULL_OUT" "$FULL_ERR" >&2
  fail "verify-model.py (full run) should FAIL when an orphan manifest is present"
fi
grep -Fq "orphaned-feature.manifest: DRIFT orphan manifest" "$FULL_OUT" || {
  cat "$FULL_OUT" "$FULL_ERR" >&2
  fail "orphan manifest was not named in full verify-model.py output"
}
echo "PASS full verify-model.py run also catches an orphan manifest"

# ---------------------------------------------------------------------------
# 2. Stray HTML: a hand-written *.html not produced by the pipeline.
# ---------------------------------------------------------------------------
rm -rf "$MODELS_DIR/$TMP_MODEL"
cp -R "$MODELS_DIR/HS-DEMO" "$MODELS_DIR/$TMP_MODEL"
printf '<!DOCTYPE html>\n<title>Hand-written stray page</title>\n' >"$MODELS_DIR/$TMP_MODEL/stray-preview.html"

STRAY_OUT="$TMPDIR/stray.out"
STRAY_ERR="$TMPDIR/stray.err"
if python3 "$VERIFY" "$TMP_MODEL" >"$STRAY_OUT" 2>"$STRAY_ERR"; then
  cat "$STRAY_OUT" "$STRAY_ERR" >&2
  fail "verify-model.py should FAIL when a stray HTML page is present"
fi
grep -Fq "stray-preview.html: DRIFT stray page" "$STRAY_OUT" || {
  cat "$STRAY_OUT" "$STRAY_ERR" >&2
  fail "stray HTML was not named in verify-model.py output"
}
echo "PASS verify-model.py catches a stray HTML page"

# --manifests-only must NOT be affected by a stray HTML file (manifest-only concern).
if ! python3 "$VERIFY" "$TMP_MODEL" --manifests-only >"$TMPDIR/stray-manifests-only.out" 2>&1; then
  cat "$TMPDIR/stray-manifests-only.out" >&2
  fail "--manifests-only should still pass when only a stray HTML (not a manifest) is present"
fi
echo "PASS --manifests-only ignores stray HTML (manifest-only scope)"

# ---------------------------------------------------------------------------
# 3. Committed models regression: no false positives on the real repo (proves the checks
#    are general, not fixture-specific, and that the checked-in models are clean).
# ---------------------------------------------------------------------------
for model in FIXTURE HS-DEMO WL327 WL527 WL727 WL927; do
  model_dir="$MODELS_DIR/$model"
  [ -d "$model_dir" ] || continue
  if ! python3 "$VERIFY" "$model" --manifests-only >"$TMPDIR/$model.manifests-only.out" 2>&1; then
    cat "$TMPDIR/$model.manifests-only.out" >&2
    fail "$model should have no orphan manifests (false positive)"
  fi
done
echo "PASS no orphan-manifest false positives on committed models"

echo "PASS verify-orphans regression"
