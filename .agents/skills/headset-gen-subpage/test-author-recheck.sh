#!/usr/bin/env bash
# Exercises author-recheck.py (D31 tier-2 orchestrator) with a STUBBED decision, so the
# edit → re-validate loop is tested deterministically without any live LLM call.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
RECHECK="$HERE/author-recheck.py"
VALIDATE="$HERE/validate-manifest.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

REQ="$TMPDIR/req.txt"
printf 'volume adjustment tone. user can turn it on or off. when on, pick Every Level or Min & Max Only.\n' >"$REQ"

# A manifest carrying the restatement flag: card "Volume Adjustment Tone" + sole toggle
# labeled "Volume Tone" (a title restatement) gating a segmented mode.
write_manifest() {
  cat >"$1" <<'YAML'
title: Audio Settings
functions:
  - id: volume-adjustment-tone
    title: Volume Adjustment Tone
    components:
      - archetype: toggle
        label: Volume Tone
        dependents:
          - archetype: segmented
            label: Tone Mode
            options:
              - {label: Every Level, value: every-level, selected: true}
              - {label: Min & Max Only, value: min-max}
YAML
}

# Sanity: the fixture must actually be flagged (advisory) before we resolve it.
# (Capture then grep via here-string: `... | grep -q` trips pipefail on grep's early-exit SIGPIPE.)
write_manifest "$TMPDIR/base.manifest"
base_out="$(python3 "$VALIDATE" "$TMPDIR/base.manifest" 2>&1)"
grep -q '^ADVISORY:.*volume-adjustment-tone' <<<"$base_out" \
  || fail "fixture should raise the restatement advisory before recheck"

# --- Case 1: decision=master → label removed, re-validates clean (no advisory) --------------
write_manifest "$TMPDIR/master.manifest"
AUTHOR_RECHECK_DECISIONS='{"volume-adjustment-tone":"master"}' \
  python3 "$RECHECK" "$TMPDIR/master.manifest" "$REQ" --in-place 2>/dev/null
if grep -q 'label: Volume Tone' "$TMPDIR/master.manifest"; then
  fail "master decision should have removed the toggle's label"
fi
grep -q 'title: Volume Adjustment Tone' "$TMPDIR/master.manifest" \
  || fail "master decision must not disturb the card title"
out="$(python3 "$VALIDATE" "$TMPDIR/master.manifest" 2>&1)"
grep -q '^OK —' <<<"$out" || fail "master result should pass validation cleanly"
if grep -q '^ADVISORY:' <<<"$out"; then
  fail "master result should no longer be flagged"
fi
echo "PASS master → label removed, revalidates clean, no advisory"

# --- Case 2: decision=member → label kept -------------------------------------------------
write_manifest "$TMPDIR/member.manifest"
AUTHOR_RECHECK_DECISIONS='{"volume-adjustment-tone":"member"}' \
  python3 "$RECHECK" "$TMPDIR/member.manifest" "$REQ" --in-place 2>/dev/null
grep -q 'label: Volume Tone' "$TMPDIR/member.manifest" \
  || fail "member decision should keep the toggle's label"
echo "PASS member → label kept"

# --- Case 3: no/blank decision → undecided, left flagged (never blocks) --------------------
# set -e already asserts exit 0: a non-zero recheck would abort the script here.
write_manifest "$TMPDIR/undecided.manifest"
AUTHOR_RECHECK_DECISIONS='{}' \
  python3 "$RECHECK" "$TMPDIR/undecided.manifest" "$REQ" --in-place 2>/dev/null
grep -q 'label: Volume Tone' "$TMPDIR/undecided.manifest" \
  || fail "undecided must leave the manifest untouched"
echo "PASS undecided → left flagged, manifest untouched, exit 0"

# --- Case 4: legitimate group member is never flagged, so recheck is a no-op ---------------
cat >"$TMPDIR/legit.manifest" <<'YAML'
title: Audio Settings
functions:
  - id: collaboration
    title: Collaboration
    components:
      - archetype: toggle
        label: Mic Noise Canceling
        dependents:
          - archetype: segmented
            label: Canceling Strength
            options:
              - {label: Low, value: low, selected: true}
              - {label: High, value: high}
YAML
AUTHOR_RECHECK_DECISIONS='{"collaboration":"master"}' \
  python3 "$RECHECK" "$TMPDIR/legit.manifest" "$REQ" --in-place 2>"$TMPDIR/legit.err"
grep -q 'label: Mic Noise Canceling' "$TMPDIR/legit.manifest" \
  || fail "a non-flagged member must never be edited, even if a stub decision exists"
grep -q 'no restatement flags' "$TMPDIR/legit.err" \
  || fail "recheck should report nothing to reconsider for a non-flagged manifest"
echo "PASS legit member → untouched (nothing flagged)"

echo "PASS author-recheck orchestrator"
