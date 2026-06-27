#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RENDERER="$ROOT/.agents/skills/headset-gen-subpage/render-model.py"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Positive fixture: HS-DEMO (always clean). WL327 is the intentionally-broken instance;
# its gate rejection is asserted in test-home.sh, so it is not a positive pipeline case here.
MODELS=(HS-DEMO)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expected_files() {
  local model="$1"
  ROOT="$ROOT" MODEL="$model" python3 - <<'PY'
import importlib.util
import os
import sys

root = os.environ["ROOT"]
model = os.environ["MODEL"]
skill_dir = os.path.join(root, ".agents", "skills", "headset-gen-subpage")
manifest_path = os.path.join(root, "headset", "models", model, "home.manifest")

spec = importlib.util.spec_from_file_location(
    "validate_home",
    os.path.join(skill_dir, "validate-home.py"),
)
validate_home = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_home)

with open(manifest_path, "r", encoding="utf-8") as f:
    home = validate_home.parse_manifest(f.read())

print(os.path.join("headset", "models", model, "index.html"))
for n, feature in enumerate(home.get("features") or []):
    link = feature.get("link") if isinstance(feature, dict) else None
    if not isinstance(link, str) or not link.endswith(".html") or "/" in link or "\\" in link:
        print("bad feature link at features[%d]: %r" % (n, link), file=sys.stderr)
        sys.exit(1)
    print(os.path.join("headset", "models", model, link))
PY
}

hash_files() {
  local list_file="$1"
  while IFS= read -r relpath; do
    shasum -a 256 "$ROOT/$relpath"
  done <"$list_file"
}

assert_written_and_not_dangling() {
  local model="$1"
  local list_file="$2"
  local output_file="$3"

  while IFS= read -r relpath; do
    [[ -f "$ROOT/$relpath" ]] || fail "$model did not write expected file: $relpath"
    grep -Fq "  - $relpath" "$output_file" || fail "$model render summary omitted: $relpath"
  done <"$list_file"
}

for model in "${MODELS[@]}"; do
  expected="$TMPDIR/$model.expected"
  first_out="$TMPDIR/$model.first.out"
  first_err="$TMPDIR/$model.first.err"
  second_out="$TMPDIR/$model.second.out"
  second_err="$TMPDIR/$model.second.err"
  first_hashes="$TMPDIR/$model.first.sha256"
  second_hashes="$TMPDIR/$model.second.sha256"

  expected_files "$model" >"$expected" || fail "$model expected-file derivation failed"

  if ! python3 "$RENDERER" "$model" >"$first_out" 2>"$first_err"; then
    cat "$first_out" "$first_err" >&2
    fail "$model first render-model run failed"
  fi
  assert_written_and_not_dangling "$model" "$expected" "$first_out"
  hash_files "$expected" >"$first_hashes"

  if ! python3 "$RENDERER" "$model" >"$second_out" 2>"$second_err"; then
    cat "$second_out" "$second_err" >&2
    fail "$model second render-model run failed"
  fi
  assert_written_and_not_dangling "$model" "$expected" "$second_out"
  hash_files "$expected" >"$second_hashes"

  if ! diff -u "$first_hashes" "$second_hashes" >"$TMPDIR/$model.hash.diff"; then
    cat "$TMPDIR/$model.hash.diff" >&2
    fail "$model render-model output changed between runs"
  fi

  echo "PASS $model render-model wrote:"
  sed 's/^/  - /' "$expected"
  echo "PASS $model determinism: re-run byte-identical"
  echo "PASS $model no dangling routes"
done
