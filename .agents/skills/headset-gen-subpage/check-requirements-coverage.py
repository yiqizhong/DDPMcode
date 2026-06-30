#!/usr/bin/env python3
"""Check requirements.md coverage against headset manifests.

This gate is intentionally mechanical. It checks identity, feature/page existence,
walkthrough step title coverage, and coverage-map entries. It does not judge
whether a function-description clause is semantically implemented correctly.

Usage: python3 check-requirements-coverage.py <headset/models/MODEL>
Exit 0 = OK or SKIP when requirements.md is absent. Exit 1 = HALT.
"""

import importlib.util
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parse_manifest = load_module("validate_manifest_for_requirements", "validate-manifest.py").parse_manifest


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def norm(value):
    return " ".join(str(value or "").strip().lower().split())


def key_norm(value):
    return re.sub(r"[^a-z0-9]+", "", norm(value))


def heading_text(line, level):
    return line[level:].strip().strip("#").strip()


def clean_heading(value):
    return re.sub(r"\s*:\s*$", "", str(value or "").strip())


def parse_key_value_list(lines):
    out = {}
    for raw in lines:
        line = raw.strip()
        if not line.startswith("-"):
            continue
        item = line[1:].strip()
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        out[key_norm(key)] = value.strip()
    return out


def split_top_sections(text):
    sections = {}
    current = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            current = clean_heading(heading_text(stripped, 2))
            sections.setdefault(key_norm(current), [])
            continue
        if current is not None:
            sections[key_norm(current)].append(raw)
    return sections


def parse_functions(lines):
    functions = []
    for raw in lines:
        line = raw.strip()
        if not line.startswith("-"):
            continue
        value = line[1:].strip()
        if value:
            functions.append(value)
    return functions


def parse_function_clauses(lines):
    clauses = []
    heading = None
    current = None
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("### "):
            heading = clean_heading(heading_text(stripped, 3))
            current = None
            continue
        if heading is None:
            continue
        match = re.match(r"^(\d+)\s*[.:]\s*(.*)$", stripped)
        if match:
            clause = {
                "heading": heading,
                "number": int(match.group(1)),
                "text": match.group(2).strip(),
            }
            clause["id"] = "%s #%d" % (heading, clause["number"])
            clauses.append(clause)
            current = clause
            continue
        if current is not None and stripped:
            current["text"] = (current["text"] + " " + stripped).strip()
    return clauses


def parse_onboarding_steps(lines):
    steps = []
    current = None
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("### "):
            title = clean_heading(heading_text(stripped, 3))
            if key_norm(title).startswith("step"):
                current = {"heading": title, "title": ""}
                steps.append(current)
            else:
                current = None
            continue
        if current is None:
            continue
        if stripped.startswith("-") and ":" in stripped:
            key, value = stripped[1:].split(":", 1)
            if key_norm(key) == "title":
                current["title"] = value.strip()
    return steps


def parse_requirements(path):
    text = read_text(path)
    sections = split_top_sections(text)
    return {
        "device": parse_key_value_list(sections.get("device", [])),
        "functions": parse_functions(sections.get("functions", [])),
        "clauses": parse_function_clauses(sections.get("functiondescriptions", [])),
        "onboarding": parse_onboarding_steps(sections.get("onboardingwalkthroughoptional", [])),
    }


def parse_manifest_file(path):
    return parse_manifest(read_text(path))


def feature_target_manifest(model_dir, link):
    if not isinstance(link, str) or not link.endswith(".html") or "/" in link or "\\" in link:
        return None
    return os.path.join(model_dir, link[:-5] + ".manifest")


class Checker:
    def __init__(self, model_dir):
        self.model_dir = os.path.abspath(model_dir)
        self.errors = []

    def err(self, msg):
        self.errors.append(msg)

    def device_identity(self, requirements, home):
        device = requirements["device"]
        mappings = (
            ("Name", "name", "marketing-name"),
            ("Model", "model", "model-number"),
            ("Firmware", "firmware", "firmware"),
        )
        for label, req_key, home_key in mappings:
            expected = (device.get(req_key) or "").strip()
            actual = (home.get(home_key) or "").strip()
            if expected and expected != actual:
                self.err(
                    "Device %s mismatch: requirements `%s` != home.manifest `%s`"
                    % (label, expected, actual)
                )

        expected_connection = device.get("connectiontype")
        actual_connection = home.get("connectionType")
        if expected_connection and key_norm(expected_connection) != key_norm(actual_connection):
            self.err(
                "Device Connection type mismatch: requirements `%s` != home.manifest `%s`"
                % (expected_connection.strip(), actual_connection)
            )

        required_image = (device.get("image") or "").strip()
        manifest_image = home.get("image")
        if required_image:
            if manifest_image in (None, "", "none"):
                self.err("requirements Image is present but home.manifest image is `%s`" % manifest_image)
        elif manifest_image != "none":
            self.err("requirements Image is blank but home.manifest image is `%s` (expected `none`)" % manifest_image)

    def function_list(self, requirements, home):
        req_functions = requirements["functions"]
        req_by_norm = {key_norm(item): item for item in req_functions}
        manifest_features = home.get("features") or []
        feature_by_norm = {}

        for index, feature in enumerate(manifest_features):
            if not isinstance(feature, dict):
                self.err("home.manifest features[%d] is not a mapping" % index)
                continue
            label = feature.get("label")
            feature_by_norm[key_norm(label)] = feature
            if key_norm(label) not in req_by_norm:
                self.err("home.manifest feature `%s` has no corresponding requirements function" % label)
            link = feature.get("link")
            target = feature_target_manifest(self.model_dir, link)
            if target is None:
                self.err("home.manifest feature `%s` has invalid link `%s`" % (label, link))
            elif not os.path.exists(target):
                self.err("home.manifest feature `%s` points to missing manifest `%s`" % (label, target))

        for req_function in req_functions:
            matched = feature_by_norm.get(key_norm(req_function))
            if matched is None:
                self.err(
                    "requirements function `%s` has no matching home.manifest feature" % req_function
                )
                continue
            target = feature_target_manifest(self.model_dir, matched.get("link"))
            if target is None or not os.path.exists(target):
                self.err(
                    "requirements function `%s` maps to feature link `%s` but its .manifest is missing"
                    % (req_function, matched.get("link"))
                )

    def walkthrough(self, requirements):
        req_steps = requirements["onboarding"]
        manifest_path = os.path.join(self.model_dir, "walkthrough.manifest")
        if not req_steps or not os.path.exists(manifest_path):
            return
        manifest = parse_manifest_file(manifest_path)
        manifest_steps = manifest.get("steps") or []
        if len(req_steps) != len(manifest_steps):
            self.err(
                "Walkthrough step count mismatch: requirements %d != walkthrough.manifest %d"
                % (len(req_steps), len(manifest_steps))
            )
            return
        for index, req_step in enumerate(req_steps):
            expected = req_step.get("title", "").strip()
            actual = str(manifest_steps[index].get("title", "")).strip() if isinstance(manifest_steps[index], dict) else ""
            if expected != actual:
                self.err(
                    "Walkthrough step %d title mismatch: requirements `%s` != walkthrough.manifest `%s`"
                    % (index + 1, expected, actual)
                )

    def coverage_map(self, requirements):
        clauses = requirements["clauses"]
        if not clauses:
            return
        path = os.path.join(self.model_dir, "coverage.md")
        if not os.path.exists(path):
            self.err("coverage.md is missing for requirements function-description clauses")
            return
        text = read_text(path)
        atom_ids = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("|") or not line.endswith("|"):
                continue
            cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
            if not cells or cells[0] in ("Atom ID", "---"):
                continue
            if cells[0] and not set(cells[0]) <= set("-:"):
                atom_ids.append(cells[0])
        for clause in clauses:
            old_needle = "| %s |" % clause["id"]
            has_old_clause_row = old_needle in text
            has_atom = any(atom_id == clause["id"] or atom_id.startswith(clause["id"] + ".") for atom_id in atom_ids)
            if not has_old_clause_row and not has_atom:
                self.err("coverage.md missing clause entry: %s" % clause["id"])

    def run(self):
        requirements_path = os.path.join(self.model_dir, "requirements.md")
        if not os.path.exists(requirements_path):
            print("SKIP — %s has no requirements.md" % self.model_dir)
            return 0

        home_path = os.path.join(self.model_dir, "home.manifest")
        try:
            requirements = parse_requirements(requirements_path)
            home = parse_manifest_file(home_path)
        except Exception as exc:
            print("HALT — requirements coverage check could not read inputs: %s" % exc, file=sys.stderr)
            return 1

        self.device_identity(requirements, home)
        self.function_list(requirements, home)
        self.walkthrough(requirements)
        self.coverage_map(requirements)

        if self.errors:
            print(
                "HALT — %s requirements coverage failed (%d issue(s)):"
                % (self.model_dir, len(self.errors)),
                file=sys.stderr,
            )
            for error in self.errors:
                print("  - %s" % error, file=sys.stderr)
            return 1
        print("OK — %s requirements coverage passes" % self.model_dir)
        return 0


def main(argv):
    if len(argv) != 2:
        print("usage: check-requirements-coverage.py <headset/models/MODEL>", file=sys.stderr)
        return 2
    model_dir = argv[1]
    if not os.path.isdir(model_dir):
        print("HALT — model folder does not exist: %s" % model_dir, file=sys.stderr)
        return 1
    return Checker(model_dir).run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
