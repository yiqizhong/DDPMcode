#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-manifest.py"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-content.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

MANIFESTS=(
  "headset/models/WL327/audio-settings.manifest"
  "headset/models/HS-DEMO/audio-settings.manifest"
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_clean_output() {
  local out="$1"
  if grep -Eq '\{[A-Za-z0-9_-]+\}' "$out"; then
    fail "$out contains leftover {placeholder}"
  fi
  if grep -Eq 'data-(property|slot|instruction)=' "$out"; then
    fail "$out contains leftover template marker attributes"
  fi
}

assert_snippet_sourced() {
  local manifest="$1"
  local out="$2"

  case "$manifest" in
    headset/models/WL327/audio-settings.manifest)
      grep -Fq '<div class="segmented-group">' "$out" || fail "WL327 missing segmented snippet markup"
      grep -Fq '<div class="slider-input-wrap" style="--min:1;--max:5;--val:3;">' "$out" || fail "WL327 missing slider snippet markup"
      grep -Fq '<svg id="eq-audio"' "$out" || fail "WL327 missing unwrapped eq-audio snapshot"
      ;;
    headset/models/HS-DEMO/audio-settings.manifest)
      grep -Fq '<svg id="eq-audio"' "$out" || fail "HS-DEMO missing eq-audio snapshot"
      grep -Fq 'Download Dell Audio' "$out" || fail "HS-DEMO missing promotion-download snapshot"
      ;;
  esac
}

assert_renderer_reads_snippets() {
  grep -Fq 'headset-shared", "components"' "$RENDERER" || fail "renderer does not load component snippets"
  grep -Fq 'function-frame.html' "$RENDERER" || fail "renderer does not load function-frame.html"
  grep -Fq 'templates", "functions"' "$RENDERER" || fail "renderer does not load function snapshots"
  grep -Fq 'segment-icons"' "$RENDERER" || fail "renderer does not load segment icons"
}

assert_renderer_reads_snippets

for manifest in "${MANIFESTS[@]}"; do
  abs="$ROOT/$manifest"
  echo "VALIDATE $manifest"
  python3 "$VALIDATOR" "$abs"

  first=""
  for i in $(seq 1 10); do
    out="$TMPDIR/$(basename "$manifest").$i.html"
    err="$TMPDIR/$(basename "$manifest").$i.err"
    python3 "$RENDERER" "$abs" >"$out" 2>"$err"
    hash="$(shasum -a 256 "$out" | awk '{print $1}')"
    if [[ -z "$first" ]]; then
      first="$hash"
    elif [[ "$hash" != "$first" ]]; then
      fail "$manifest run $i hash $hash != first hash $first"
    fi
    assert_clean_output "$out"
    if grep -Fq 'LLM-FALLBACK' "$out" "$err"; then
      echo "LANE-2 $manifest:"
      cat "$err"
    fi
  done

  assert_snippet_sourced "$manifest" "$TMPDIR/$(basename "$manifest").1.html"
  echo "PASS $manifest 10x byte-identical sha256=$first"
done
