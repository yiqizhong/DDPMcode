#!/usr/bin/env python3
"""Validate a shared walkthrough manifest against the generation schema.

Mechanical enforcement of the HALT rules in shared-gen-walkthrough/SKILL.md so the
renderer consumes only the fixed `{title, cta?, done-link?, steps[]}` contract.
Zero dependencies (stdlib only) so it ALWAYS runs.

Usage:  python3 validate-walkthrough.py <path/to/walkthrough.manifest>
Exit 0 = valid (generation may proceed).  Exit 1 = HALT (prints each violation).
"""
import importlib.util
import os
import sys

MAX_STEPS = 6
TOP_ALLOWED_KEYS = frozenset(("title", "cta", "done-link", "steps"))
STEP_ALLOWED_KEYS = frozenset(("title", "body", "image"))

# The minimal YAML-subset parser is shared across category + cross-category validators;
# canonical copy lives in shared-lib (not a skill — same pattern as headset-shared/).
SHARED_LIB = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared-lib")
)
_spec = importlib.util.spec_from_file_location(
    "manifest_parser", os.path.join(SHARED_LIB, "manifest_parser.py")
)
_manifest_parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_manifest_parser)
parse_manifest = _manifest_parser.parse_manifest


# ---- validation ----

class V:
    def __init__(self):
        self.errors = []

    def err(self, where, msg):
        self.errors.append("%s: %s" % (where, msg))

    def unknown_keys(self, where, obj, allowed):
        for key in obj:
            if key not in allowed:
                self.err(
                    where,
                    "unknown key `%s` (allowed: %s)" % (
                        key,
                        ", ".join("`%s`" % k for k in sorted(allowed)),
                    ),
                )

    def _missing(self, m, field):
        return field not in m or m.get(field) is None or m.get(field) == ""

    def _string_if_present(self, where, m, field):
        if field not in m or m.get(field) is None:
            return
        if not isinstance(m.get(field), str) or m.get(field) == "":
            self.err(where, "`%s` must be a non-empty string when present" % field)

    def manifest(self, m):
        if not isinstance(m, dict):
            self.err("manifest", "top level is not a mapping")
            return
        self.unknown_keys("manifest", m, TOP_ALLOWED_KEYS)
        if self._missing(m, "title"):
            self.err("manifest", "missing `title`")
        for field in ("title", "cta", "done-link"):
            self._string_if_present("manifest.%s" % field, m, field)

        steps = m.get("steps")
        if steps is None:
            self.err("manifest", "missing `steps` list")
            return
        if not isinstance(steps, list):
            self.err("manifest", "`steps` must be a list")
            return
        if not steps:
            self.err("manifest", "walkthrough has no steps[]")
            return
        if len(steps) > MAX_STEPS:
            self.err(
                "manifest.steps",
                "too many steps (%d > MAX_STEPS=%d); shared/walkthrough.css only maps %d positionally"
                % (len(steps), MAX_STEPS, MAX_STEPS),
            )
        for n, step in enumerate(steps, start=1):
            where = "step %d" % n
            if not isinstance(step, dict):
                self.err(where, "step is not a mapping")
                continue
            self.unknown_keys(where, step, STEP_ALLOWED_KEYS)
            for required in ("title", "body"):
                if self._missing(step, required):
                    self.err(where, "step %d is missing required %r" % (n, required))
            for field in ("title", "body", "image"):
                self._string_if_present("%s.%s" % (where, field), step, field)


def main(argv):
    if len(argv) != 2:
        print("usage: validate-walkthrough.py <walkthrough.manifest>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print("cannot read %s: %s" % (path, e), file=sys.stderr)
        return 2
    try:
        manifest = parse_manifest(text)
    except Exception as e:
        print("HALT: cannot parse %s: %s" % (path, e), file=sys.stderr)
        return 1
    v = V()
    v.manifest(manifest)
    if v.errors:
        print("HALT — %s is out of contract (%d issue(s)):" % (path, len(v.errors)), file=sys.stderr)
        for e in v.errors:
            print("  - %s" % e, file=sys.stderr)
        return 1
    print("OK — %s passes walkthrough schema validation" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
