#!/usr/bin/env python3
"""Deterministic Phase-3 home-page renderer for headset model pages."""

import importlib.util
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SHARED_DIR = os.path.normpath(os.path.join(HERE, "..", "headset-shared"))
FRAME = os.path.normpath(os.path.join(HERE, "..", "headset-gen-homepage", "templates", "home-frame.html"))
CONNECTION_DIR = os.path.join(SHARED_DIR, "connection")
UNPAIR = os.path.join(CONNECTION_DIR, "unpair.html")
FEATURE_BUTTON = os.path.join(SHARED_DIR, "feature-button.html")
FEATURE_ICON_DIR = os.path.join(SHARED_DIR, "icons")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_lib = load_module("render_lib", os.path.join(HERE, "render-lib.py"))
RenderHalt = _lib.RenderHalt
read_text = _lib.read_text
halt = _lib.halt
rewrite_css_paths = _lib.rewrite_css_paths
find_tag_end = _lib.find_tag_end
replace_slot_contents = _lib.replace_slot_contents
set_data_property_text = _lib.set_data_property_text
set_data_property_html = _lib.set_data_property_html
remove_data_property_element = _lib.remove_data_property_element
fill_property_if_present = _lib.fill_property_if_present
mode_is_paired = _lib.mode_is_paired
render_device_image = _lib.render_device_image

validate_home = load_module("validate_home", os.path.join(HERE, "validate-home.py"))
render_content = load_module("render_content", os.path.join(HERE, "render-content.py"))


def parse_and_validate_home(path):
    try:
        manifest = validate_home.parse_manifest(read_text(path))
    except OSError as exc:
        halt("cannot read %s: %s" % (path, exc))
    except Exception as exc:
        halt("cannot parse %s: %s" % (path, exc))

    gate = validate_home.V()
    gate.manifest(manifest)
    if gate.errors:
        lines = ["%s is out of contract (%d issue(s)):" % (path, len(gate.errors))]
        lines.extend("  - %s" % error for error in gate.errors)
        halt("\n".join(lines))
    return manifest


def render_connection(home):
    return _lib.render_connection(
        home, CONNECTION_DIR, render_content.strip_html_comments,
        include_unpair=True, unpair_path=UNPAIR,
    )


def render_feature_button(feature):
    return _lib.render_feature_button(
        feature, FEATURE_BUTTON, FEATURE_ICON_DIR, render_content.strip_html_comments,
        collapsed=False,
    )


def render_feature_zone(home):
    features = home.get("features") or []
    return "\n".join(render_feature_button(feature) for feature in features)


def render_page(model):
    model_dir = os.path.join(ROOT, "headset", "models", model)
    home_manifest_path = os.path.join(model_dir, "home.manifest")
    home = parse_and_validate_home(home_manifest_path)

    page = rewrite_css_paths(read_text(FRAME))
    page = set_data_property_text(page, "device-marketing-name", home["marketing-name"])
    page = set_data_property_text(page, "device-model-number", home["model-number"])
    page = set_data_property_text(page, "firmware-version", home.get("firmware", ""))

    if home.get("ppid"):
        page = set_data_property_text(page, "device-ppid", "PPID: %s" % home["ppid"])
    else:
        page = remove_data_property_element(page, "device-ppid")

    page = set_data_property_html(page, "device-image", render_device_image(home))
    page = replace_slot_contents(page, "control-zone", render_connection(home))
    page = replace_slot_contents(page, "feature-zone", render_feature_zone(home))
    return render_content.strip_markers(page) + "\n"


def main(argv):
    if len(argv) != 2:
        print("usage: render-home.py <MODEL>", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(render_page(argv[1]))
    except RenderHalt as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
