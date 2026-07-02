#!/usr/bin/env bash
# Verify every headset model from repo root:
# - home.manifest schema
# - each feature-target subpage manifest schema
# - generated HTML drift against deterministic renderers
set -u -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
MODELS_DIR="$ROOT/headset/models"
VALIDATE_HOME="$HERE/validate-home.py"
VALIDATE_MANIFEST="$HERE/validate-manifest.py"
VALIDATE_WALKTHROUGH="$ROOT/.agents/skills/shared-gen-walkthrough/validate-walkthrough.py"
VERIFY_MODEL="$HERE/verify-model.py"
CHECK_CSS_CLASSES="$HERE/check-css-classes.py"
CHECK_REQUIREMENTS_COVERAGE="$HERE/check-requirements-coverage.py"
CHECK_COVERAGE_ATOMS="$HERE/check-coverage-atoms.py"

FAILURES=0
# Advisories are non-blocking review flags (e.g. a sole-toggle label that looks like it
# restates its card title — the master/member call the requirement-reader must make; D31).
# They never fail verification; we collect them here and print one consolidated reminder at
# the end so the build completes and nothing is silently swallowed.
ADVISORY_LOG="$(mktemp)"
trap 'rm -f "$ADVISORY_LOG"' EXIT

record_failure() {
  FAILURES=$((FAILURES + 1))
}

run_check() {
  local label="$1"
  shift
  echo "== $label =="
  echo "+ $*"
  # Capture combined output so we can both pass it through AND harvest ADVISORY lines for the
  # end-of-run summary. No `set -e`, so command substitution preserves the real exit code.
  local out
  out="$("$@" 2>&1)"
  local status=$?
  [ -n "$out" ] && printf '%s\n' "$out"
  printf '%s\n' "$out" | grep -a '^ADVISORY:' >>"$ADVISORY_LOG" 2>/dev/null || true
  if [ "$status" -eq 0 ]; then
    echo "OK: $label"
  else
    echo "FAIL: $label (exit $status)" >&2
    record_failure
  fi
  echo
}

subpage_manifests() {
  local model_dir="$1"
  local home_manifest="$model_dir/home.manifest"
  # Importlib-load render-model.py and call ITS subpage_from_link — the same rule the
  # renderer itself uses to resolve a feature link to a manifest stem — so there is exactly
  # one link-validation rule (mirrors how validate-home.py is already loaded below).
  ROOT="$ROOT" MODEL_DIR="$model_dir" HOME_MANIFEST="$home_manifest" SKILL_DIR="$HERE" python3 - <<'PY'
import importlib.util
import os
import sys

model_dir = os.environ["MODEL_DIR"]
home_manifest = os.environ["HOME_MANIFEST"]
skill_dir = os.environ["SKILL_DIR"]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_home = load_module(
    "validate_home_for_verify_all", os.path.join(skill_dir, "validate-home.py")
)
render_model = load_module(
    "render_model_for_verify_all", os.path.join(skill_dir, "render-model.py")
)

try:
    with open(home_manifest, "r", encoding="utf-8") as f:
        home = validate_home.parse_manifest(f.read())
except Exception as exc:
    print("cannot derive subpage manifests from %s: %s" % (home_manifest, exc), file=sys.stderr)
    sys.exit(1)

ok = True
for index, feature in enumerate(home.get("features") or []):
    if not isinstance(feature, dict):
        print("features[%d] is not a mapping" % index, file=sys.stderr)
        ok = False
        continue
    link = feature.get("link") if isinstance(feature, dict) else None
    try:
        subpage = render_model.subpage_from_link(link, index)
    except render_model.RenderHalt as exc:
        print(str(exc), file=sys.stderr)
        ok = False
        continue
    print(os.path.join(model_dir, subpage + ".manifest"))

sys.exit(0 if ok else 1)
PY
}

cd "$ROOT" || exit 2

MODELS=()
while IFS= read -r model_dir; do
  MODELS+=("$model_dir")
done <<EOF
$(find "$MODELS_DIR" -mindepth 1 -maxdepth 1 -type d | sort)
EOF
if [ "${#MODELS[@]}" -eq 0 ]; then
  echo "FAIL: no model directories found under headset/models" >&2
  exit 1
fi

echo "Verifying ${#MODELS[@]} headset model(s)"
echo

run_check "system CSS class existence" python3 "$CHECK_CSS_CLASSES"

for model_dir in "${MODELS[@]}"; do
  model="$(basename "$model_dir")"
  home_manifest="$model_dir/home.manifest"

  echo "## model: $model"

  if [ -f "$home_manifest" ]; then
    run_check "$model home.manifest" python3 "$VALIDATE_HOME" "$home_manifest"
  else
    echo "FAIL: $model missing home.manifest at $home_manifest" >&2
    record_failure
    echo
  fi

  subpage_list="$(mktemp)"
  if subpage_manifests "$model_dir" >"$subpage_list"; then
    while IFS= read -r manifest; do
      [ -n "$manifest" ] || continue
      if [ -f "$manifest" ]; then
        run_check "$model $(basename "$manifest")" python3 "$VALIDATE_MANIFEST" "$manifest"
      else
        echo "FAIL: $model feature target is missing manifest: $manifest" >&2
        record_failure
        echo
      fi
    done <"$subpage_list"
  else
    echo "FAIL: $model could not derive feature-target subpage manifests" >&2
    record_failure
    echo
  fi
  rm -f "$subpage_list"

  walkthrough_manifest="$model_dir/walkthrough.manifest"
  if [ -f "$walkthrough_manifest" ]; then
    run_check "$model walkthrough.manifest" python3 "$VALIDATE_WALKTHROUGH" "$walkthrough_manifest"
  fi

  run_check "$model requirements coverage" python3 "$CHECK_REQUIREMENTS_COVERAGE" "$model_dir"
  run_check "$model coverage atoms" python3 "$CHECK_COVERAGE_ATOMS" "$model_dir"

  # Drift only makes sense for models whose generated HTML is committed. Dev/demo
  # fixtures (e.g. FIXTURE, HS-DEMO) gitignore their *.html, so they are absent from
  # a fresh checkout (CI) — skip drift for those; their manifests/coverage still run.
  # Only gitignored HTML is skipped: a merely-uncommitted/new model still drift-checks.
  # The orphan-manifest check (verify-model.py --manifests-only) is manifest-side only —
  # it does not need any HTML on disk — so it runs for EVERY model, including gitignored
  # fixtures; the stray-HTML check rides inside the full drift call below, where HTML is
  # actually expected on disk.
  if git -C "$ROOT" check-ignore -q "headset/models/$model/index.html" 2>/dev/null; then
    run_check "$model orphan manifest check" python3 "$VERIFY_MODEL" "$model" --manifests-only
    echo "== $model generated HTML drift =="
    echo "SKIP: $model generated HTML is gitignored — drift not applicable"
    echo
  else
    run_check "$model generated HTML drift" python3 "$VERIFY_MODEL" "$model"
  fi
done

if [ -s "$ADVISORY_LOG" ]; then
  advisory_count=$(wc -l <"$ADVISORY_LOG" | tr -d ' ')
  echo "================ REVIEW FLAGS: $advisory_count advisory(ies), non-blocking ================"
  echo "Build/verify completed. These spots were flagged for the requirement-reader (the"
  echo "authoring LLM, or you) to eyeball — they do NOT fail verification:"
  echo
  awk '{ printf "  %d. %s\n", NR, $0 }' "$ADVISORY_LOG"
  echo "======================================================================================"
  echo
fi

if [ "$FAILURES" -gt 0 ]; then
  echo "VERIFY-ALL FAILED: $FAILURES failing check(s)" >&2
  exit 1
fi

echo "VERIFY-ALL OK"
