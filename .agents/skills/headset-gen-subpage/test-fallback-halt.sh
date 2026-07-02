#!/usr/bin/env bash
# test-fallback-halt.sh — FIX 1 regression: a lane-2 (LLM-fallback) marker must HALT the
# composed render paths (render-subpage.py / render-content.py's own CLI), not silently
# succeed with exit 0 and a broken <!-- LLM-FALLBACK: ... --> comment baked into the page.
#
# Builds an isolated fixture (copy of .agents/skills/ + a scratch model dir) in a temp
# directory so the corrupted/missing component snippet never touches the real repo files.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

FIXTURE_ROOT="$TMPDIR/fixture-root"
mkdir -p "$FIXTURE_ROOT"
cp -R "$ROOT/.agents" "$FIXTURE_ROOT/.agents"
mkdir -p "$FIXTURE_ROOT/headset/models/FBHALT"

cat >"$FIXTURE_ROOT/headset/models/FBHALT/home.manifest" <<'MANIFEST'
marketing-name: Fallback Halt Fixture
model-number: FBHALT-1
connectionType: bluetooth
image: none
opt-out-reason: test fixture, no image needed
features:
  - label: Subpage
    icon: audio
    link: subpage.html
MANIFEST

cat >"$FIXTURE_ROOT/headset/models/FBHALT/subpage.manifest" <<'MANIFEST'
title: Subpage
functions:
  - id: some-fn
    title: Some Function
    components:
      - archetype: toggle
MANIFEST

FIXTURE_VALIDATOR="$FIXTURE_ROOT/.agents/skills/headset-gen-subpage/validate-manifest.py"
FIXTURE_RENDER_SUBPAGE="$FIXTURE_ROOT/.agents/skills/headset-gen-subpage/render-subpage.py"
FIXTURE_RENDER_CONTENT="$FIXTURE_ROOT/.agents/skills/headset-gen-subpage/render-content.py"
FIXTURE_TOGGLE_SNIPPET="$FIXTURE_ROOT/.agents/skills/headset-shared/components/toggle.html"

# ---------------------------------------------------------------------------
# 1. Baseline: with the toggle snippet present, the fixture renders clean (exit 0,
#    no HALT, no LLM-FALLBACK) — proves the fixture itself is valid before we break it.
# ---------------------------------------------------------------------------
python3 "$FIXTURE_VALIDATOR" "$FIXTURE_ROOT/headset/models/FBHALT/subpage.manifest" >/dev/null \
  || fail "fixture subpage.manifest should validate cleanly before corruption"

BASE_OUT="$TMPDIR/base.out"
BASE_ERR="$TMPDIR/base.err"
python3 "$FIXTURE_RENDER_SUBPAGE" FBHALT subpage >"$BASE_OUT" 2>"$BASE_ERR" || {
  cat "$BASE_OUT" "$BASE_ERR" >&2
  fail "fixture render-subpage.py should succeed before corruption"
}
grep -Fq "LLM-FALLBACK" "$BASE_OUT" && fail "baseline render should not contain LLM-FALLBACK"
echo "PASS baseline fixture render is clean"

# ---------------------------------------------------------------------------
# 2. validate-manifest.py catches a DELETED component snippet at the validation gate
#    (the "cheap" mechanical check from FIX 1's additional bullet) — this is the common
#    case and closes most of the gap by itself.
# ---------------------------------------------------------------------------
cp "$FIXTURE_TOGGLE_SNIPPET" "$TMPDIR/toggle.html.orig"
rm -f "$FIXTURE_TOGGLE_SNIPPET"

if python3 "$FIXTURE_VALIDATOR" "$FIXTURE_ROOT/headset/models/FBHALT/subpage.manifest" \
    >"$TMPDIR/validate.out" 2>"$TMPDIR/validate.err"; then
  cat "$TMPDIR/validate.out" "$TMPDIR/validate.err" >&2
  fail "validate-manifest.py should HALT when the archetype's component snippet is missing"
fi
grep -Fq "no component snippet" "$TMPDIR/validate.err" || {
  cat "$TMPDIR/validate.out" "$TMPDIR/validate.err" >&2
  fail "validate-manifest.py HALT did not name the missing component snippet"
}
echo "PASS validate-manifest.py HALTs on a deleted component snippet"

# Restore the snippet file, then corrupt its CONTENT instead (structurally broken, still
# present on disk) — a manifest that already passed validation (e.g. validated before the
# snippet was corrupted by a later commit) must still be caught by the RENDERER itself,
# not just the validator. This is the "surviving lane2 path" the composed render paths
# must HALT on.
cp "$TMPDIR/toggle.html.orig" "$FIXTURE_TOGGLE_SNIPPET"
python3 - "$FIXTURE_TOGGLE_SNIPPET" <<'PY'
import re
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the <label class="switch">...</label> control so render_switch_widget's
# "toggle snippet has no switch widget" lane-2 fallback fires, while the file itself
# still exists (so validate-manifest.py's snippet-existence check does NOT catch this —
# it is a structural corruption, not a missing file).
corrupted = re.sub(r'<label class="switch">.*?</label>', "<!-- control removed -->", content, flags=re.S)
assert corrupted != content, "corruption pattern did not match toggle.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(corrupted)
PY

python3 "$FIXTURE_VALIDATOR" "$FIXTURE_ROOT/headset/models/FBHALT/subpage.manifest" >/dev/null \
  || fail "validate-manifest.py should NOT catch a structurally-corrupted-but-present snippet (this proves the render-time gap FIX 1 covers)"
echo "PASS validator does not catch structural corruption (confirms the render-time gap this test targets)"

# ---------------------------------------------------------------------------
# 3. The composed render path (render-subpage.py) must HALT — non-zero exit, no HTML
#    written with a lane-2 fallback baked in.
# ---------------------------------------------------------------------------
SUBPAGE_OUT="$TMPDIR/subpage.out"
SUBPAGE_ERR="$TMPDIR/subpage.err"
if python3 "$FIXTURE_RENDER_SUBPAGE" FBHALT subpage >"$SUBPAGE_OUT" 2>"$SUBPAGE_ERR"; then
  cat "$SUBPAGE_OUT" "$SUBPAGE_ERR" >&2
  fail "render-subpage.py should HALT (non-zero exit) when a lane-2 fallback fires"
fi
grep -Fq "HALT" "$SUBPAGE_ERR" || {
  cat "$SUBPAGE_OUT" "$SUBPAGE_ERR" >&2
  fail "render-subpage.py did not print HALT"
}
grep -Fq "lane-2" "$SUBPAGE_ERR" || {
  cat "$SUBPAGE_OUT" "$SUBPAGE_ERR" >&2
  fail "render-subpage.py HALT did not mention the lane-2 fallback"
}
grep -Fq "LLM-FALLBACK" "$SUBPAGE_OUT" && fail "render-subpage.py must not print a page containing LLM-FALLBACK to stdout"
echo "PASS render-subpage.py HALTs on a surviving lane-2 fallback instead of emitting a broken page"

# ---------------------------------------------------------------------------
# 4. render-content.py's standalone CLI also exits non-zero (fail-closed), not 0-with-a-
#    warning-on-stderr, when FALLBACKS is non-empty.
# ---------------------------------------------------------------------------
CONTENT_OUT="$TMPDIR/content.out"
CONTENT_ERR="$TMPDIR/content.err"
if python3 "$FIXTURE_RENDER_CONTENT" "$FIXTURE_ROOT/headset/models/FBHALT/subpage.manifest" \
    >"$CONTENT_OUT" 2>"$CONTENT_ERR"; then
  cat "$CONTENT_OUT" "$CONTENT_ERR" >&2
  fail "render-content.py CLI should exit non-zero when FALLBACKS is non-empty"
fi
grep -Fq "LANE-2" "$CONTENT_ERR" || {
  cat "$CONTENT_OUT" "$CONTENT_ERR" >&2
  fail "render-content.py CLI did not report the LANE-2 fallback on stderr"
}
echo "PASS render-content.py CLI exits non-zero on a surviving lane-2 fallback"

echo "PASS fallback-halt regression"
