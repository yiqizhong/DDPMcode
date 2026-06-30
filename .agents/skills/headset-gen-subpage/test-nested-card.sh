#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VALIDATOR="$ROOT/.agents/skills/headset-gen-subpage/validate-manifest.py"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-content.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

NESTED_MANIFEST="$TMPDIR/nested-card.manifest"
cat >"$NESTED_MANIFEST" <<'MANIFEST'
title: Nested Card Fixture
functions:
  - id: nested-card-fixture
    title: Nested Card Fixture
    components:
      - title: Outer Group
        info: "Outer grouping help"
        components:
          - archetype: toggle
            label: Inner Toggle
            value: true
          - archetype: segmented
            label: Outer Choice
            options:
              - {label: One, value: one, selected: true}
              - {label: Two, value: two}
            reveals:
              two:
                - archetype: slider
                  label: Revealed Strength
                  min: 1
                  max: 5
                  value: 3
      - archetype: segmented
        label: Top Choice
        options:
          - {label: One, value: one, selected: true}
          - {label: Two, value: two}
        reveals:
          two:
            - title: Revealed Group
              components:
                - archetype: toggle
                  label: Revealed Toggle
                  value: true
MANIFEST

SECTION_MANIFEST="$TMPDIR/section-archetype.manifest"
cat >"$SECTION_MANIFEST" <<'MANIFEST'
title: Broken Section Fixture
functions:
  - id: broken-section-fixture
    title: Broken Section Fixture
    components:
      - archetype: toggle
        label: Parent Toggle
        value: true
        dependents:
          - archetype: section
            title: Old Section Shape
            components:
              - archetype: toggle
                label: Child Toggle
                value: true
MANIFEST

python3 "$VALIDATOR" "$NESTED_MANIFEST"
python3 "$RENDERER" "$NESTED_MANIFEST" >"$TMPDIR/nested-card.html"

grep -Fq '<p class="subfn-label">Outer Group</p>' "$TMPDIR/nested-card.html" || fail "missing outer nested-card label"
grep -Fq '<p class="subfn-label">Revealed Group</p>' "$TMPDIR/nested-card.html" || fail "missing reveal nested-card label"
grep -Fq '<div class="subfn-child">' "$TMPDIR/nested-card.html" || fail "nested card did not render subfn-child wrappers"
grep -Fq 'Outer grouping help' "$TMPDIR/nested-card.html" || fail "nested card info tooltip did not render"

OVER_DEPTH_MANIFEST="$TMPDIR/over-depth-nested-card.manifest"
cat >"$OVER_DEPTH_MANIFEST" <<'MANIFEST'
title: Over Depth Fixture
functions:
  - id: over-depth-fixture
    title: Over Depth Fixture
    components:
      - title: Safe Level
        components:
          - title: Too Deep
            components:
              - archetype: toggle
                label: Deep Toggle
                value: true
MANIFEST

if python3 "$VALIDATOR" "$OVER_DEPTH_MANIFEST" >"$TMPDIR/over-depth.out" 2>"$TMPDIR/over-depth.err"; then
  cat "$TMPDIR/over-depth.out" "$TMPDIR/over-depth.err" >&2
  fail "over-depth nested card should HALT"
fi
grep -Fq 'deeper nesting requires the not-yet-built declarative show/hide engine (D13)' "$TMPDIR/over-depth.err" || {
  cat "$TMPDIR/over-depth.out" "$TMPDIR/over-depth.err" >&2
  fail "over-depth error did not cite D13"
}
echo "HALT over-depth-nested-card"

if python3 "$VALIDATOR" "$SECTION_MANIFEST" >"$TMPDIR/section.out" 2>"$TMPDIR/section.err"; then
  cat "$TMPDIR/section.out" "$TMPDIR/section.err" >&2
  fail "legacy archetype: section should HALT"
fi
grep -Fq 'nested card slot' "$TMPDIR/section.err" || {
  cat "$TMPDIR/section.out" "$TMPDIR/section.err" >&2
  fail "section error did not point to nested card slot form"
}

echo "PASS nested assembled card slot regressions"
