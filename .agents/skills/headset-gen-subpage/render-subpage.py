#!/usr/bin/env python3
"""Deterministic Phase-2 full sub-page renderer for headset model pages."""

import html
import importlib.util
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SHARED_DIR = os.path.normpath(os.path.join(HERE, "..", "headset-shared"))
FRAME = os.path.join(HERE, "templates", "subpage-frame.html")
CONNECTION_DIR = os.path.join(SHARED_DIR, "connection")
FEATURE_BUTTON = os.path.join(SHARED_DIR, "feature-button.html")
FEATURE_ICON_DIR = os.path.join(SHARED_DIR, "icons")


class RenderHalt(Exception):
    pass


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_manifest = load_module("validate_manifest", os.path.join(HERE, "validate-manifest.py"))
validate_home = load_module("validate_home", os.path.join(HERE, "validate-home.py"))
render_content = load_module("render_content", os.path.join(HERE, "render-content.py"))


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def text(value):
    return html.escape(str(value), quote=False)


def attr(value):
    return html.escape(str(value), quote=True)


def halt(message):
    raise RenderHalt(message)


def parse_and_validate(module, path, label):
    try:
        manifest = module.parse_manifest(read_text(path))
    except OSError as exc:
        halt("cannot read %s: %s" % (path, exc))
    except Exception as exc:
        halt("cannot parse %s: %s" % (path, exc))

    gate = module.V()
    gate.manifest(manifest)
    if gate.errors:
        lines = ["%s is out of contract (%d issue(s)):" % (label, len(gate.errors))]
        lines.extend("  - %s" % error for error in gate.errors)
        halt("\n".join(lines))
    return manifest


def rewrite_css_paths(markup):
    return (
        markup
        .replace('href="../../../../shared/tokens.css"', 'href="../../../shared/tokens.css"')
        .replace('href="../../../../shared/shell.css"', 'href="../../../shared/shell.css"')
        .replace('href="../../../../headset/headset.css"', 'href="../../headset.css"')
    )


def find_tag_end(markup, start):
    quote = None
    i = start
    while i < len(markup):
        ch = markup[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == ">":
            return i
        i += 1
    halt("unterminated HTML tag")


def replace_slot_contents(markup, slot_name, content):
    pos = markup.find('data-slot="%s"' % slot_name)
    if pos == -1:
        halt("frame missing data-slot=%s" % slot_name)
    tag_start = markup.rfind("<", 0, pos)
    tag_end = find_tag_end(markup, tag_start)
    close_start = markup.find("</div>", tag_end)
    if close_start == -1:
        halt("frame slot %s has no closing div" % slot_name)
    return markup[:tag_end + 1] + "\n" + content + "\n" + markup[close_start:]


def set_data_property_text(markup, property_name, value):
    pattern = (
        r'(<(?P<tag>[a-zA-Z][\w:-]*)\b(?=[^>]*data-property="%s")[^>]*>)'
        r".*?"
        r"(</(?P=tag)>)"
    ) % re.escape(property_name)
    replacement = lambda match: match.group(1) + text(value) + match.group(3)
    updated, count = re.subn(pattern, replacement, markup, flags=re.S)
    if count == 0:
        halt("frame missing data-property=%s" % property_name)
    return updated


def set_data_property_html(markup, property_name, value):
    pattern = (
        r'(<(?P<tag>[a-zA-Z][\w:-]*)\b(?=[^>]*data-property="%s")[^>]*>)'
        r".*?"
        r"(</(?P=tag)>)"
    ) % re.escape(property_name)
    updated, count = re.subn(pattern, lambda match: match.group(1) + value + match.group(3),
                             markup, count=1, flags=re.S)
    if count == 0:
        halt("frame missing data-property=%s" % property_name)
    return updated


def remove_data_property_element(markup, property_name):
    pattern = (
        r'\n?[ \t]*<(?P<tag>[a-zA-Z][\w:-]*)\b'
        r'(?=[^>]*data-property="%s")[^>]*>.*?</(?P=tag)>'
    ) % re.escape(property_name)
    return re.sub(pattern, "", markup, count=1, flags=re.S)


def add_class_to_first(markup, existing_class, new_class):
    pattern = r'class="([^"]*\b%s\b[^"]*)"' % re.escape(existing_class)

    def repl(match):
        classes = match.group(1).split()
        if new_class not in classes:
            classes.append(new_class)
        return 'class="%s"' % " ".join(classes)

    updated, count = re.subn(pattern, repl, markup, count=1)
    if count == 0:
        halt("snippet missing class %s" % existing_class)
    return updated


def fill_property_if_present(markup, property_name, value):
    if 'data-property="%s"' % property_name not in markup:
        return markup
    return set_data_property_text(markup, property_name, value)


def render_connection(home):
    connection_type = home.get("connectionType")
    path = os.path.join(CONNECTION_DIR, "%s.html" % connection_type)
    if not os.path.exists(path):
        halt("connection snippet does not exist: %s" % path)

    markup = render_content.strip_html_comments(read_text(path))
    if 'data-property="battery-level"' in markup:
        battery = "%s%%" % home["battery"] if "battery" in home else "—%"
        markup = fill_property_if_present(markup, "battery-level", battery)
    return markup.strip()


def render_feature_button(feature):
    icon_id = feature.get("icon")
    icon_path = os.path.join(FEATURE_ICON_DIR, "%s.svg" % icon_id)
    if not icon_id or not os.path.exists(icon_path):
        halt("missing/unknown feature icon: %s" % icon_id)

    markup = render_content.strip_html_comments(read_text(FEATURE_BUTTON))
    markup = add_class_to_first(markup, "feature-button", "feature-button--collapsed")
    markup = markup.replace("{label}", text(feature["label"]))
    markup = markup.replace("{link}", attr(feature["link"]))
    icon = read_text(icon_path).strip()
    markup, count = re.subn(
        r'(<div class="feature-icon">).*?(</div>)',
        lambda match: match.group(1) + icon + match.group(2),
        markup,
        count=1,
        flags=re.S,
    )
    if count == 0:
        halt("feature-button snippet missing .feature-icon")
    return markup.strip()


def render_feature_nav(home):
    features = home.get("features") or []
    return "\n".join(render_feature_button(feature) for feature in features)


def render_device_image(home):
    image = home.get("image")
    if not image or image == "none":
        return ""
    return '<img src="%s" alt="%s">' % (attr(image), attr(home["marketing-name"]))


def render_page(model, subpage):
    model_dir = os.path.join(ROOT, "headset", "models", model)
    subpage_manifest_path = os.path.join(model_dir, "%s.manifest" % subpage)
    home_manifest_path = os.path.join(model_dir, "home.manifest")

    subpage_manifest = parse_and_validate(validate_manifest, subpage_manifest_path, subpage_manifest_path)
    home_manifest = parse_and_validate(validate_home, home_manifest_path, home_manifest_path)

    page = rewrite_css_paths(read_text(FRAME))
    page = set_data_property_text(page, "subpage-title", subpage_manifest["title"])
    page = set_data_property_text(page, "device-marketing-name", home_manifest["marketing-name"])
    page = set_data_property_text(page, "device-model-number", home_manifest["model-number"])
    page = set_data_property_text(page, "firmware-version", home_manifest.get("firmware", ""))

    if home_manifest.get("ppid"):
        page = set_data_property_text(page, "device-ppid", "PPID: %s" % home_manifest["ppid"])
    else:
        page = remove_data_property_element(page, "device-ppid")

    page = set_data_property_html(page, "device-image", render_device_image(home_manifest))
    page = replace_slot_contents(page, "control-zone", render_connection(home_manifest))
    page = replace_slot_contents(page, "feature-nav-collapsed", render_feature_nav(home_manifest))

    if subpage_manifest.get("functions"):
        page = replace_slot_contents(page, "functions", render_content.render(subpage_manifest_path))

    return render_content.strip_markers(page) + "\n"


def main(argv):
    if len(argv) != 3:
        print("usage: render-subpage.py <MODEL> <SUBPAGE>", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(render_page(argv[1], argv[2]))
    except RenderHalt as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    except render_content.RenderHalt as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
