#!/usr/bin/env bash
# test-dropdown.sh — regression + correctness test for the dropdown archetype renderer.
# Run from the repo root: bash .agents/skills/headset-gen-subpage/test-dropdown.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
RENDERER="$HERE/render-content.py"
VALIDATOR="$HERE/validate-manifest.py"
MANIFEST="$REPO_ROOT/headset/models/FIXTURE/device-settings.manifest"
SCRATCHPAD=/tmp/test-dropdown-scratch

cd "$REPO_ROOT"

PASS=0
FAIL=0

ok()   { echo "[PASS] $*"; PASS=$((PASS + 1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Use the stable fixture model's device-settings manifest so the dropdown
# regression does not depend on volatile model instances.
# ---------------------------------------------------------------------------
test -f "$MANIFEST" || fail "missing fixture manifest: $MANIFEST"

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

# 3c. Selected item (1 hour) is the one marked.
SELECTED_LINE=$(echo "$OUTPUT" | grep 'dropdown-item--selected' | head -1)
if echo "$SELECTED_LINE" | grep -q '1 hour'; then
    ok "correct option (1 hour) is marked as selected"
else
    fail "wrong option marked as selected — expected '1 hour', got: $SELECTED_LINE"
fi

# 3d. All four options are present.
OPTION_COUNT=$(echo "$OUTPUT" | grep -c 'class="dropdown-item')
if [ "$OPTION_COUNT" -eq 4 ]; then
    ok "all 4 options are rendered"
else
    fail "expected 4 dropdown-item elements, got $OPTION_COUNT"
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
# 5. Regression: FIXTURE tracks the dropdown/snapshot baseline; HS-DEMO stays unchanged.
# ---------------------------------------------------------------------------
echo "--- 5. regression: FIXTURE dropdown baseline and HS-DEMO unchanged ---"

FIXTURE_EXPECTED="ab0ef42d208e78971e9f650454f06af03e7afc404887d5b00c6f18e3edb18819"
FIXTURE_SHA=""
FIXTURE_ALL_SAME=true
for i in $(seq 1 10); do
    SHA=$(python3 "$RENDERER" headset/models/FIXTURE/device-settings.manifest 2>/dev/null | sha256sum | awk '{print $1}')
    if [ -z "$FIXTURE_SHA" ]; then
        FIXTURE_SHA="$SHA"
    elif [ "$SHA" != "$FIXTURE_SHA" ]; then
        FIXTURE_ALL_SAME=false
        fail "FIXTURE device render $i non-deterministic: $SHA vs $FIXTURE_SHA"
    fi
done
if $FIXTURE_ALL_SAME; then
    ok "FIXTURE device renders are 10x byte-identical (sha256: ${FIXTURE_SHA:0:16}…)"
fi
if [ "$FIXTURE_SHA" = "$FIXTURE_EXPECTED" ]; then
    ok "FIXTURE device sha256 matches current dropdown baseline"
else
    fail "FIXTURE device sha256 CHANGED: got $FIXTURE_SHA, expected $FIXTURE_EXPECTED"
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
