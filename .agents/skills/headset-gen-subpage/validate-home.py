#!/usr/bin/env python3
"""Validate a headset home manifest against the generation schema.

Mechanical enforcement of the HALT rules in docs/home-manifest-schema.md so a
home page renderer can consume only structured, registry-backed data.

Usage:  python3 validate-home.py <path/to/home.manifest>
Exit 0 = valid (generation may proceed).  Exit 1 = HALT (prints each violation).
"""

import importlib.util
import os
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SKILL_DIR, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Reuse the existing manifest parser; do not maintain a second YAML subset parser.
parse_manifest = _load_module("validate_manifest", "validate-manifest.py").parse_manifest
home_schema = _load_module("home_schema", "home-schema.py")


class V:
    def __init__(self):
        self.errors = []

    def err(self, where, msg):
        self.errors.append("%s: %s" % (where, msg))

    def _missing(self, m, field):
        return field not in m or m.get(field) is None or m.get(field) == ""

    def _string_if_present(self, m, field):
        if field not in m or m.get(field) is None:
            return
        if not isinstance(m.get(field), str) or m.get(field) == "":
            self.err("manifest.%s" % field, "`%s` must be a non-empty string when present" % field)

    def _connection(self, m):
        ctype = m.get("connectionType")
        if self._missing(m, "connectionType"):
            return
        if not isinstance(ctype, str):
            self.err("manifest.connectionType", "`connectionType` must be a string")
            return
        path = home_schema.registry_path("connection", ctype)
        if not os.path.exists(path):
            self.err(
                "manifest.connectionType",
                "connectionType `%s` has no snippet %s" % (
                    ctype,
                    home_schema.registry_display("connection", ctype),
                ),
            )

    def _battery(self, m):
        if "battery" not in m or m.get("battery") is None:
            return
        value = m.get("battery")
        if not isinstance(value, int) or value < 0 or value > 100:
            self.err("manifest.battery", "`battery` must be an integer from 0 to 100 when present")

    def _features(self, m):
        if "features" not in m or m.get("features") in (None, []):
            return
        features = m.get("features")
        if not isinstance(features, list):
            self.err("manifest.features", "`features` must be a list when present")
            return
        for n, feature in enumerate(features):
            where = "features[%d]" % n
            if not isinstance(feature, dict):
                self.err(where, "feature is not a mapping")
                continue
            for field in home_schema.FEATURE_REQUIRED_FIELDS:
                if field not in feature or feature.get(field) is None or feature.get(field) == "":
                    self.err(where, "feature missing `%s`" % field)
            icon = feature.get("icon")
            if icon is None or icon == "":
                continue
            if not isinstance(icon, str):
                self.err("%s.icon" % where, "`icon` must be a string")
                continue
            path = home_schema.registry_path("feature-icon", icon)
            if not os.path.exists(path):
                self.err(
                    "%s.icon" % where,
                    "icon id `%s` has no asset %s" % (
                        icon,
                        home_schema.registry_display("feature-icon", icon),
                    ),
                )

    def manifest(self, m):
        if not isinstance(m, dict):
            self.err("manifest", "top level is not a mapping")
            return
        for field in home_schema.REQUIRED_FIELDS:
            if self._missing(m, field):
                self.err("manifest", "missing required field `%s`" % field)
        for field in ("marketing-name", "model-number", "firmware", "ppid", "image"):
            self._string_if_present(m, field)
        self._connection(m)
        self._battery(m)
        self._features(m)


def main(argv):
    if len(argv) != 2:
        print("usage: validate-home.py <home.manifest>", file=sys.stderr)
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
    print("OK — %s passes home schema validation" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
