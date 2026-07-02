#!/usr/bin/env bash
# Regenerate every headset model from manifests, then run the detect-only all-model gate.
set -u -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
MODELS_DIR="$ROOT/headset/models"
RENDER_MODEL="$HERE/render-model.py"
VERIFY_ALL="$HERE/verify-all.sh"

FAILURES=0
SUMMARY=()

record_failure() {
  FAILURES=$((FAILURES + 1))
  SUMMARY+=("$1")
}

manifest_hint() {
  local model="$1"
  local log_file="$2"
  local matches
  matches="$(grep -Eo 'headset/models/[^[:space:]:]+\.manifest' "$log_file" | sort -u || true)"
  if [ -n "$matches" ]; then
    printf '%s\n' "$matches"
  else
    printf 'headset/models/%s/home.manifest or a feature-target subpage manifest\n' "$model"
  fi
}

run_capture() {
  local label="$1"
  local log_file="$2"
  shift 2

  echo "== $label =="
  echo "+ $*"
  "$@" >"$log_file" 2>&1
  local status=$?
  cat "$log_file"
  if [ "$status" -eq 0 ]; then
    echo "OK: $label"
  else
    echo "FAIL: $label (exit $status)" >&2
  fi
  echo
  return "$status"
}

cd "$ROOT" || exit 2

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

MODELS=()
while IFS= read -r model_dir; do
  MODELS+=("$model_dir")
done <<EOF
$(find "$MODELS_DIR" -mindepth 1 -maxdepth 1 -type d | sort)
EOF

if [ "${#MODELS[@]}" -eq 0 ]; then
  echo "REGEN FAILED: no model directories found under headset/models" >&2
  exit 1
fi

echo "Regenerating ${#MODELS[@]} headset model(s)"
echo

for model_dir in "${MODELS[@]}"; do
  model="$(basename "$model_dir")"
  render_log="$TMPDIR/$model.render-model.log"

  # render-model.py renders the whole model, including walkthrough.html when
  # walkthrough.manifest is present — no separate walkthrough render step needed.
  if ! run_capture "$model render-model" "$render_log" python3 "$RENDER_MODEL" "$model"; then
    echo "REGEN HALT: render-model.py failed for model $model" >&2
    echo "Manifest needing upstream fix:" >&2
    manifest_hint "$model" "$render_log" | sed 's/^/  - /' >&2
    echo "Renderer output above is authoritative; fix the manifest source, then rerun regen.sh." >&2
    exit 1
  fi
done

if [ "$FAILURES" -eq 0 ]; then
  verify_log="$TMPDIR/verify-all.log"
  if ! run_capture "verify-all" "$verify_log" bash "$VERIFY_ALL"; then
    record_failure "verify-all failed after regeneration"
  fi
fi

if [ "$FAILURES" -gt 0 ]; then
  echo "REGEN FAILED: $FAILURES failing step(s)" >&2
  for item in "${SUMMARY[@]}"; do
    echo "  - $item" >&2
  done
  exit 1
fi

echo "REGEN OK: regenerated ${#MODELS[@]} model(s) and verify-all passed"
