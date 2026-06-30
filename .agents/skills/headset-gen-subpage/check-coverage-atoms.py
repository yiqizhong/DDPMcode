#!/usr/bin/env python3
"""Mechanically check requirements coverage atoms against headset manifests.

This is the control-level layer above check-requirements-coverage.py. It does not
read prose semantically and it does not call an LLM. It only verifies that each
machine-checkable atom's stable locator resolves in the manifest and that the
manifest value at that locator matches the atom's Expected cell.

Usage: python3 check-coverage-atoms.py <headset/models/MODEL>
Exit 0 = OK or SKIP when requirements.md/coverage.md is absent. Exit 1 = HALT.
"""

import importlib.util
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ("Atom ID", "Requirement", "Locator", "Expected", "Verdict")
VERDICTS = frozenset(("pass", "fail", "ambiguous"))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parse_manifest = load_module("validate_manifest_for_atom_coverage", "validate-manifest.py").parse_manifest


class AtomError(Exception):
    pass


class UnsupportedLocator(Exception):
    pass


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def clean_cell(value):
    value = str(value or "").strip()
    if len(value) >= 2 and value[0] == "`" and value[-1] == "`":
        return value[1:-1].strip()
    return value


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")


def split_table_row(line):
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator(cells):
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def parse_atom_table(path):
    rows = []
    header = None
    for line_no, line in enumerate(read_text(path).splitlines(), 1):
        cells = split_table_row(line)
        if cells is None:
            continue
        if is_separator(cells):
            continue
        if header is None:
            header = cells
            if header != list(COLUMNS):
                raise AtomError(
                    "%s:%d has coverage table header `%s`; expected `%s`"
                    % (path, line_no, " | ".join(header), " | ".join(COLUMNS))
                )
            continue
        if len(cells) != len(COLUMNS):
            raise AtomError("%s:%d has %d cells; expected %d" % (path, line_no, len(cells), len(COLUMNS)))
        atom = dict(zip(COLUMNS, [clean_cell(cell) for cell in cells]))
        if not atom["Atom ID"]:
            raise AtomError("%s:%d Atom ID is blank" % (path, line_no))
        if not atom["Requirement"]:
            raise AtomError("%s:%d Requirement is blank for %s" % (path, line_no, atom["Atom ID"]))
        if not atom["Locator"]:
            raise AtomError("%s:%d Locator is blank for %s" % (path, line_no, atom["Atom ID"]))
        if not atom["Expected"]:
            raise AtomError("%s:%d Expected is blank for %s" % (path, line_no, atom["Atom ID"]))
        verdict = atom["Verdict"].lower()
        if verdict not in VERDICTS:
            raise AtomError(
                "%s:%d Verdict for %s is `%s`; expected pass | fail | ambiguous"
                % (path, line_no, atom["Atom ID"], atom["Verdict"])
            )
        atom["Verdict"] = verdict
        rows.append(atom)
    if header is None:
        raise AtomError("%s has no atom coverage table" % path)
    return rows


def parse_manifest_file(path):
    return parse_manifest(read_text(path))


def find_function(manifest, function_id):
    for fn in manifest.get("functions") or []:
        if isinstance(fn, dict) and str(fn.get("id")) == function_id:
            return fn
    raise AtomError("function `%s` not found" % function_id)


def top_components(fn):
    comps = fn.get("components")
    if comps is None:
        return []
    if not isinstance(comps, list):
        raise AtomError("function `%s` components is not a list" % fn.get("id"))
    return comps


def sole_component(fn):
    comps = top_components(fn)
    if len(comps) != 1 or not isinstance(comps[0], dict) or "archetype" not in comps[0]:
        raise AtomError("function `%s` does not have a single addressable component" % fn.get("id"))
    return comps[0]


def slots_from_context(ctx):
    if isinstance(ctx, list):
        return ctx
    if isinstance(ctx, dict) and "components" in ctx:
        comps = ctx.get("components")
        if isinstance(comps, list):
            return comps
    raise AtomError("current locator context has no slot list")


def component_key_matches(component, key):
    candidates = [
        component.get("label"),
        component.get("title"),
        component.get("archetype"),
    ]
    return any(slug(candidate) == key for candidate in candidates if candidate is not None)


def find_component(ctx, key):
    slots = slots_from_context(ctx)
    matches = [
        slot for slot in slots
        if isinstance(slot, dict) and "archetype" in slot and component_key_matches(slot, key)
    ]
    if not matches:
        raise AtomError("component `%s` not found" % key)
    if len(matches) > 1:
        raise AtomError("component `%s` is ambiguous" % key)
    return matches[0]


def find_card(ctx, key):
    slots = slots_from_context(ctx)
    matches = [
        slot for slot in slots
        if isinstance(slot, dict) and "archetype" not in slot and "function" not in slot and slug(slot.get("title")) == key
    ]
    if not matches:
        raise AtomError("card `%s` not found" % key)
    if len(matches) > 1:
        raise AtomError("card `%s` is ambiguous" % key)
    return matches[0]


def require_selector(ctx):
    if isinstance(ctx, dict) and "archetype" in ctx:
        return ctx
    if isinstance(ctx, dict) and "id" in ctx:
        return sole_component(ctx)
    raise AtomError("current locator context is not a selector component")


def require_toggle(ctx):
    if isinstance(ctx, dict) and "archetype" in ctx:
        if ctx.get("archetype") != "toggle":
            raise AtomError("component `%s` is not a toggle" % ctx.get("label", ctx.get("archetype")))
        return ctx
    if isinstance(ctx, dict) and "id" in ctx:
        comp = sole_component(ctx)
        if comp.get("archetype") != "toggle":
            raise AtomError("function `%s` sole component is not a toggle" % ctx.get("id"))
        return comp
    raise AtomError("current locator context is not a toggle component")


def find_option(ctx, value):
    selector = require_selector(ctx)
    for option in selector.get("options") or []:
        if isinstance(option, dict) and str(option.get("value")) == value:
            return option
    raise AtomError("option `%s` not found" % value)


def flatten_tokens(parts):
    tokens = []
    for part in parts:
        tokens.extend([token for token in part.split(".") if token])
    return tokens


def resolve_locator(model_dir, locator):
    if locator.lower() == "n/a":
        raise UnsupportedLocator("review-only locator")
    parts = locator.split("::")
    if len(parts) < 2:
        raise UnsupportedLocator("unsupported locator grammar")

    manifest_stem, function_id = parts[0], parts[1]
    manifest_path = os.path.join(model_dir, manifest_stem + ".manifest")
    if not os.path.exists(manifest_path):
        raise AtomError("manifest `%s.manifest` not found" % manifest_stem)
    manifest = parse_manifest_file(manifest_path)
    ctx = find_function(manifest, function_id)

    tokens = flatten_tokens(parts[2:])
    i = 0
    while i < len(tokens):
        token = tokens[i]

        match = re.fullmatch(r"component\(([^)]+)\)", token)
        if match:
            ctx = find_component(ctx, slug(match.group(1)))
            i += 1
            continue

        match = re.fullmatch(r"card\(([^)]+)\)", token)
        if match:
            ctx = find_card(ctx, slug(match.group(1)))
            i += 1
            continue

        match = re.fullmatch(r"option\(([^)]+)\)", token)
        if match:
            ctx = find_option(ctx, match.group(1))
            i += 1
            continue

        if token == "options":
            selector = require_selector(ctx)
            ctx = [str(option.get("value")) for option in (selector.get("options") or []) if isinstance(option, dict)]
            i += 1
            continue

        if token == "reveals":
            selector = require_selector(ctx)
            if i + 1 >= len(tokens):
                raise UnsupportedLocator("reveals requires an option value")
            value = tokens[i + 1]
            reveals = selector.get("reveals") or {}
            if value not in reveals:
                raise AtomError("reveals.%s not found" % value)
            ctx = reveals[value]
            i += 2
            continue

        if token == "dependents":
            toggle = require_toggle(ctx)
            if "dependents" not in toggle:
                raise AtomError("dependents not found")
            ctx = toggle.get("dependents") or []
            i += 1
            continue

        if token in ("selected", "info", "value", "min", "max", "stops", "archetype", "label", "title"):
            if not isinstance(ctx, dict):
                raise AtomError("property `%s` cannot be read from this locator context" % token)
            if token not in ctx:
                raise AtomError("property `%s` not found" % token)
            ctx = ctx[token]
            i += 1
            continue

        raise UnsupportedLocator("unsupported locator token `%s`" % token)

    return ctx


def scalar_expected(value):
    low = value.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value.strip()):
        return float(value.strip())
    return value.strip()


def parse_descriptor(text):
    text = text.strip()
    match = re.fullmatch(r'(function|toggle|slider|segmented|preset-grid|dropdown|card)(?:\s+"([^"]+)")?', text)
    if not match:
        raise UnsupportedLocator("unsupported expected descriptor `%s`" % text)
    return (match.group(1), match.group(2) or "")


def slot_descriptor(slot):
    if isinstance(slot, dict) and "function" in slot:
        return ("function", str(slot.get("function")))
    if isinstance(slot, dict) and "archetype" in slot:
        return (str(slot.get("archetype")), str(slot.get("label") or ""))
    if isinstance(slot, dict) and "title" in slot:
        return ("card", str(slot.get("title")))
    return ("unknown", "")


def node_descriptor(node):
    if isinstance(node, dict) and "id" in node:
        return ("function", str(node.get("title") or node.get("id")))
    if isinstance(node, dict) and "archetype" in node:
        return (str(node.get("archetype")), str(node.get("label") or ""))
    if isinstance(node, dict) and "function" in node:
        return ("function", str(node.get("function")))
    if isinstance(node, dict) and "title" in node:
        return ("card", str(node.get("title")))
    return None


def descriptor_matches(actual, expected):
    actual_kind, actual_name = actual
    expected_kind, expected_name = expected
    if actual_kind != expected_kind:
        return False
    return not expected_name or actual_name == expected_name


def assert_matches(actual, expected):
    if isinstance(actual, list):
        if all(isinstance(item, str) for item in actual):
            expected_values = [item.strip() for item in expected.split(",") if item.strip()]
            if set(actual) != set(expected_values):
                raise AtomError("expected options {%s}; got {%s}" % (", ".join(expected_values), ", ".join(actual)))
            return
        expected_descriptors = [parse_descriptor(part) for part in expected.split(";") if part.strip()]
        actual_descriptors = [slot_descriptor(slot) for slot in actual]
        for descriptor in expected_descriptors:
            if not any(descriptor_matches(actual, descriptor) for actual in actual_descriptors):
                raise AtomError(
                    "expected slot %s; got %s"
                    % (
                        format_descriptor(descriptor),
                        ", ".join(format_descriptor(item) for item in actual_descriptors) or "none",
                    )
                )
        return

    descriptor = node_descriptor(actual)
    if descriptor is not None and re.match(r"^(function|toggle|slider|segmented|preset-grid|dropdown|card)(\s|$)", expected):
        expected_descriptor = parse_descriptor(expected)
        if not descriptor_matches(descriptor, expected_descriptor):
            raise AtomError("expected %s; got %s" % (format_descriptor(expected_descriptor), format_descriptor(descriptor)))
        return

    if expected.lower() == "present":
        if actual in (None, ""):
            raise AtomError("expected present value; got blank")
        return

    expected_scalar = scalar_expected(expected)
    if actual != expected_scalar:
        raise AtomError("expected `%s`; got `%s`" % (expected_scalar, actual))


def format_descriptor(descriptor):
    kind, name = descriptor
    if name:
        return '%s "%s"' % (kind, name)
    return kind


class Checker:
    def __init__(self, model_dir):
        self.model_dir = os.path.abspath(model_dir)
        self.errors = []
        self.skipped = []
        self.checked = 0

    def run_atom(self, atom):
        atom_id = atom["Atom ID"]
        locator = atom["Locator"]
        expected = atom["Expected"]
        try:
            actual = resolve_locator(self.model_dir, locator)
            assert_matches(actual, expected)
            self.checked += 1
        except UnsupportedLocator as exc:
            self.skipped.append("%s: %s" % (atom_id, exc))
        except Exception as exc:
            self.errors.append("%s: %s" % (atom_id, exc))

    def run(self):
        requirements_path = os.path.join(self.model_dir, "requirements.md")
        coverage_path = os.path.join(self.model_dir, "coverage.md")
        if not os.path.exists(requirements_path) or not os.path.exists(coverage_path):
            print("SKIP — %s has no requirements.md + coverage.md atom table" % self.model_dir)
            return 0

        try:
            atoms = parse_atom_table(coverage_path)
        except Exception as exc:
            print("HALT — coverage atom table is invalid: %s" % exc, file=sys.stderr)
            return 1

        for atom in atoms:
            self.run_atom(atom)

        if self.errors:
            print(
                "HALT — %s coverage atoms failed (%d issue(s)):"
                % (self.model_dir, len(self.errors)),
                file=sys.stderr,
            )
            for error in self.errors:
                print("  - %s" % error, file=sys.stderr)
            return 1

        print(
            "OK — %s coverage atoms pass (%d checked, %d skipped)"
            % (self.model_dir, self.checked, len(self.skipped))
        )
        for skipped in self.skipped:
            print("SKIP atom — %s" % skipped)
        return 0


def main(argv):
    if len(argv) != 2:
        print("usage: check-coverage-atoms.py <headset/models/MODEL>", file=sys.stderr)
        return 2
    model_dir = argv[1]
    if not os.path.isdir(model_dir):
        print("HALT — model folder does not exist: %s" % model_dir, file=sys.stderr)
        return 1
    return Checker(model_dir).run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
