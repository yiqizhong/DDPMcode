#!/usr/bin/env bash
# Run the headset-gen-subpage toolchain regression suite:
# - every test-*.sh in this directory (discovered by glob, so new tests are
#   picked up automatically)
# - verify-model-test.sh
# - the shared-gen-walkthrough validation test
set -u -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
WALKTHROUGH_TEST="$ROOT/.agents/skills/shared-gen-walkthrough/test-walkthrough-validation.sh"

FAILURES=0

record_failure() {
  FAILURES=$((FAILURES + 1))
}

run_check() {
  local label="$1"
  shift
  echo "== $label =="
  echo "+ $*"
  "$@"
  local status=$?
  if [ "$status" -eq 0 ]; then
    echo "OK: $label"
  else
    echo "FAIL: $label (exit $status)" >&2
    record_failure
  fi
  echo
}

TESTS=()
while IFS= read -r test_script; do
  TESTS+=("$test_script")
done <<EOF
$(find "$HERE" -maxdepth 1 -name 'test-*.sh' -type f | sort)
EOF
TESTS+=("$HERE/verify-model-test.sh")
TESTS+=("$WALKTHROUGH_TEST")

if [ "${#TESTS[@]}" -eq 0 ]; then
  echo "FAIL: no test scripts found" >&2
  exit 1
fi

echo "Running ${#TESTS[@]} test script(s)"
echo

for test_script in "${TESTS[@]}"; do
  if [ -f "$test_script" ]; then
    run_check "$(basename "$test_script")" bash "$test_script"
  else
    echo "FAIL: missing test script $test_script" >&2
    record_failure
    echo
  fi
done

if [ "$FAILURES" -gt 0 ]; then
  echo "RUN-TESTS FAILED: $FAILURES failing check(s)" >&2
  exit 1
fi

echo "RUN-TESTS OK"
