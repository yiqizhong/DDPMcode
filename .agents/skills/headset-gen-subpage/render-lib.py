#!/usr/bin/env python3
"""Shared helpers for the headset-gen-subpage renderers (render-home.py,
render-subpage.py, render-content.py). Extracted because these were byte-identical
(or near-identical, differing only in halt-vs-silent failure semantics) copies
across the renderer modules; consolidated here as the single implementation, with
parameters where behavior legitimately differs (e.g. `render_feature_button`'s
`collapsed` flag, `render_connection`'s `include_unpair` flag). Halting is the
unified failure mode for a missing slot/property/class — that indicates a template
regression, not a legitimately-absent, manifest-driven region (those are handled by
the caller checking manifest data before calling in, e.g. render-content.py only
calls `replace_slot_contents` for "function-info" when `info` is present, and uses
`remove_slot_element` otherwise).
"""

import html
import importlib.util
import os
import re


class RenderHalt(Exception):
    pass


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def text(value):
    return html.escape(str(value), quote=False)


def attr(value):
    return html.escape(str(value), quote=True)


def halt(message):
    raise RenderHalt(message)


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


def replace_slot_contents(markup, slot_name, content, closing_indent="\n"):
    """Replace the inner HTML of the FIRST element carrying `data-slot="<slot_name>"`.

    CONSTRAINT: every `data-slot` element in a frame template MUST be a leaf (no
    nested `<div>` inside it in the template) — this works by finding the first
    `</div>` after the slot's open tag, so a nested div would close too early.

    `closing_indent` is the whitespace inserted right before the matched closing
    `</div>` (call-site formatting only; does not affect valid-input semantics).
    Halts if the slot or its closing `</div>` is missing — a missing slot in a
    frame template is a template regression, not a legitimately-absent region.
    """
    pos = markup.find('data-slot="%s"' % slot_name)
    if pos == -1:
        halt("frame missing data-slot=%s" % slot_name)
    tag_start = markup.rfind("<", 0, pos)
    tag_end = find_tag_end(markup, tag_start)
    close_start = markup.find("</div>", tag_end)
    if close_start == -1:
        halt("frame slot %s has no closing div" % slot_name)
    return markup[:tag_end + 1] + "\n" + content + closing_indent + markup[close_start:]


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


def fill_property_if_present(markup, property_name, value):
    if 'data-property="%s"' % property_name not in markup:
        return markup
    return set_data_property_text(markup, property_name, value)


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


def mode_is_paired(raw_connection_snippet):
    lower = raw_connection_snippet.lower()
    return "paired mode" in lower and "does not pair" not in lower


def render_connection(home, connection_dir, strip_html_comments, include_unpair=False, unpair_path=None):
    """Copy the connectionType snippet, fill battery, and (home page only) append Unpair.

    `strip_html_comments` is injected (render-content.strip_html_comments) rather than
    imported, to avoid a render-lib -> render-content dependency edge.
    """
    connection_type = home.get("connectionType")
    path = os.path.join(connection_dir, "%s.html" % connection_type)
    if not os.path.exists(path):
        halt("connection snippet does not exist: %s" % path)

    raw = read_text(path)
    markup = strip_html_comments(raw)
    if 'data-property="battery-level"' in markup:
        battery = "%s%%" % home["battery"] if "battery" in home else "—%"
        markup = fill_property_if_present(markup, "battery-level", battery)

    if not include_unpair:
        return markup.strip()

    parts = [markup.strip()]
    if mode_is_paired(raw):
        if not os.path.exists(unpair_path):
            halt("unpair snippet does not exist: %s" % unpair_path)
        parts.append(strip_html_comments(read_text(unpair_path)).strip())
    return "\n".join(parts)


def render_feature_button(feature, feature_button_path, feature_icon_dir, strip_html_comments,
                          collapsed=False):
    icon_id = feature.get("icon")
    icon_path = os.path.join(feature_icon_dir, "%s.svg" % icon_id)
    if not icon_id or not os.path.exists(icon_path):
        halt("missing/unknown feature icon: %s" % icon_id)

    markup = strip_html_comments(read_text(feature_button_path))
    if collapsed:
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


def render_device_image(home):
    image = home.get("image")
    if not image or image == "none":
        return ""
    return '<img src="%s" alt="%s">' % (attr(image), attr(home["marketing-name"]))
