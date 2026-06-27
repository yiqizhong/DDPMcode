#!/usr/bin/env bash
# test-dropdown.sh — regression + correctness test for the dropdown archetype renderer.
# Run from the repo root: bash .agents/skills/headset-gen-subpage/test-dropdown.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
RENDERER="$HERE/render-content.py"
VALIDATOR="$HERE/validate-manifest.py"
MANIFEST=/tmp/test-dropdown-manifest.manifest
SCRATCHPAD=/tmp/test-dropdown-scratch

cd "$REPO_ROOT"

PASS=0
FAIL=0

ok()   { echo "[PASS] $*"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Write the test manifest to a temp path (no model directory pollution).
# ---------------------------------------------------------------------------
cat > "$MANIFEST" <<'EOF'
title: Power Settings

functions:
  - id: auto-power-off
    title: Auto Power-Off
    components:
      - archetype: dropdown
        label: Turn off after
        options:
          - label: 15 minutes
            value: 15min
          - label: 30 minutes
            value: 30min
          - label: 1 hour
            value: 1h
          - label: 2 hours
            value: 2h
          - label: 4 hours
            value: 4h
            selected: true
          - label: 8 hours
            value: 8h
EOF

# ---------------------------------------------------------------------------
# 1. Gate: validate-manifest.py accepts the dropdown manifest.
# ---------------------------------------------------------------------------
echo "--- 1. validate-manifest gate ---"
if python3 "$VALIDATOR" "$MANIFEST" > /dev/null 2>&1; then
    ok "validate-manifest accepts the dropdown manifest"
else
    fail "validate-manifest REJECTED the dropdown manifest"
    python3 "$VALIDATOR" "$MANIFEST"
fi

# ---------------------------------------------------------------------------
# 2. render-content produces output (no HALT, no LANE-2 fallback).
# ---------------------------------------------------------------------------
echo "--- 2. renderer: no HALT, no lane-2 fallback ---"
RENDER_STDERR=$("$REPO_ROOT/.agents/skills/headset-gen-subpage/render-content.py" "$MANIFEST" > /dev/null 2>&1 && echo "" || true)
RENDER_STDERR=$(python3 "$RENDERER" "$MANIFEST" 2>&1 >/dev/null || true)
if echo "$RENDER_STDERR" | grep -q "HALT"; then
    fail "renderer HALTed: $RENDER_STDERR"
elif echo "$RENDER_STDERR" | grep -q "LANE-2"; then
    fail "renderer fired LANE-2 fallback: $RENDER_STDERR"
else
    ok "renderer produced output with no HALT and no LANE-2 fallback"
fi

# ---------------------------------------------------------------------------
# 3. Render once and capture output for content checks.
# ---------------------------------------------------------------------------
echo "--- 3. content checks ---"
OUTPUT=$(python3 "$RENDERER" "$MANIFEST" 2>/dev/null)

# 3a. <details> / <summary> structure sourced from dropdown.html is present.
if echo "$OUTPUT" | grep -q '<details class="dropdown">'; then
    ok "output contains <details class=\"dropdown\"> from snippet"
else
    fail "output is missing <details class=\"dropdown\">"
fi

if echo "$OUTPUT" | grep -q '<summary class="dropdown-trigger">'; then
    ok "output contains <summary class=\"dropdown-trigger\">"
else
    fail "output is missing <summary class=\"dropdown-trigger\">"
fi

if echo "$OUTPUT" | grep -q '<ul class="dropdown-list">'; then
    ok "output contains <ul class=\"dropdown-list\">"
else
    fail "output is missing <ul class=\"dropdown-list\">"
fi

# 3b. Selected option is marked with dropdown-item--selected.
if echo "$OUTPUT" | grep -q 'dropdown-item--selected'; then
    ok "selected option is marked with dropdown-item--selected"
else
    fail "no dropdown-item--selected class found in output"
fi

# 3c. Selected item (4 hours) is the one marked.
SELECTED_LINE=$(echo "$OUTPUT" | grep 'dropdown-item--selected' | head -1)
if echo "$SELECTED_LINE" | grep -q '4 hours'; then
    ok "correct option (4 hours) is marked as selected"
else
    fail "wrong option marked as selected — expected '4 hours', got: $SELECTED_LINE"
fi

# 3d. All six options are present.
OPTION_COUNT=$(echo "$OUTPUT" | grep -c 'class="dropdown-item')
if [ "$OPTION_COUNT" -eq 6 ]; then
    ok "all 6 options are rendered"
else
    fail "expected 6 dropdown-item elements, got $OPTION_COUNT"
fi

# 3e. No leftover {placeholder} strings.
if python3 -c "import sys, re; sys.exit(0 if re.search(r'\{[a-z][a-z0-9-]*\}', sys.stdin.read()) else 1)" <<< "$OUTPUT" 2>/dev/null; then
    fail "leftover {placeholder} found in output"
    echo "$OUTPUT" | python3 -c "import sys, re; [print(l) for l in sys.stdin if re.search(r'\{[a-z][a-z0-9-]*\}', l)]"
else
    ok "no leftover {placeholder} strings"
fi

# 3f. No data-instruction / data-slot attributes remain.
if echo "$OUTPUT" | grep -qE 'data-(instruction|slot)='; then
    fail "leftover data-instruction or data-slot attribute found"
else
    ok "no data-instruction or data-slot attributes in output"
fi

# 3g. No LLM-FALLBACK comment.
if echo "$OUTPUT" | grep -q 'LLM-FALLBACK'; then
    fail "LLM-FALLBACK comment found in output"
else
    ok "no LLM-FALLBACK comment in output"
fi

# ---------------------------------------------------------------------------
# 4. Determinism: render 10x and assert byte-identical sha256.
# ---------------------------------------------------------------------------
echo "--- 4. determinism (10 renders) ---"
mkdir -p "$SCRATCHPAD"
SHA_FIRST=""
ALL_SAME=true
for i in $(seq 1 10); do
    SHA=$(python3 "$RENDERER" "$MANIFEST" 2>/dev/null | sha256sum | awk '{print $1}')
    if [ -z "$SHA_FIRST" ]; then
        SHA_FIRST="$SHA"
    elif [ "$SHA" != "$SHA_FIRST" ]; then
        ALL_SAME=false
        fail "render $i produced different sha256: $SHA (first was $SHA_FIRST)"
    fi
done
if $ALL_SAME; then
    ok "10 renders are byte-identical (sha256: ${SHA_FIRST:0:16}…)"
fi

# ---------------------------------------------------------------------------
# 5. Regression: WL327 and HS-DEMO must produce the SAME sha as before change.
# ---------------------------------------------------------------------------
echo "--- 5. regression: WL327 and HS-DEMO unchanged ---"

WL327_EXPECTED="c3030d1edcb98213733cb76a5912ee4332d42fea12284c248f99bf39fe53e160"
WL327_SHA=""
WL327_ALL_SAME=true
for i in $(seq 1 10); do
    SHA=$(python3 "$RENDERER" headset/models/WL327/audio-settings.manifest 2>/dev/null | sha256sum | awk '{print $1}')
    if [ -z "$WL327_SHA" ]; then
        WL327_SHA="$SHA"
    elif [ "$SHA" != "$WL327_SHA" ]; then
        WL327_ALL_SAME=false
        fail "WL327 render $i non-deterministic: $SHA vs $WL327_SHA"
    fi
done
if $WL327_ALL_SAME; then
    ok "WL327 renders are 10x byte-identical (sha256: ${WL327_SHA:0:16}…)"
fi
if [ "$WL327_SHA" = "$WL327_EXPECTED" ]; then
    ok "WL327 sha256 matches pre-change baseline"
else
    fail "WL327 sha256 CHANGED: got $WL327_SHA, expected $WL327_EXPECTED"
fi

HSDEMO_SHA=""
HSDEMO_ALL_SAME=true
for i in $(seq 1 10); do
    SHA=$(python3 "$RENDERER" headset/models/HS-DEMO/audio-settings.manifest 2>/dev/null | sha256sum | awk '{print $1}')
    if [ -z "$HSDEMO_SHA" ]; then
        HSDEMO_SHA="$SHA"
    elif [ "$SHA" != "$HSDEMO_SHA" ]; then
        HSDEMO_ALL_SAME=false
        fail "HS-DEMO render $i non-deterministic: $SHA vs $HSDEMO_SHA"
    fi
done
if $HSDEMO_ALL_SAME; then
    ok "HS-DEMO renders are 10x byte-identical (sha256: ${HSDEMO_SHA:0:16}…)"
fi

# Verify HS-DEMO sha also hasn't changed vs a live baseline (computed earlier in this session)
HSDEMO_EXPECTED="d8aa56479f4b017668d3f8fdcf66998da6466c5f97fd8e1f8341a8c08dfa5ca3"
if [ "$HSDEMO_SHA" = "$HSDEMO_EXPECTED" ]; then
    ok "HS-DEMO sha256 matches pre-change baseline"
else
    fail "HS-DEMO sha256 CHANGED: got $HSDEMO_SHA, expected $HSDEMO_EXPECTED"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
