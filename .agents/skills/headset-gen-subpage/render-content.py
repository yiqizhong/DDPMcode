#!/usr/bin/env python3
"""Deterministic Phase-1 content-area renderer for headset sub-page manifests.

Scope: render only the manifest's `functions[]` list into the inner HTML for `.content-area`.
The page frame, connection block, feature nav, and homepage paths are later phases.
"""

import html
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(HERE, ".."))
COMPONENT_DIR = os.path.join(SKILLS_DIR, "headset-shared", "components")
SEGMENT_ICON_DIR = os.path.join(SKILLS_DIR, "headset-shared", "segment-icons")
SNAPSHOT_DIR = os.path.join(HERE, "templates", "functions")
FUNCTION_FRAME = os.path.join(SKILLS_DIR, "headset-function", "templates", "function-frame.html")

FALLBACKS = []
SEGMENT_ICON_ALIASES = {
    "transparency": "hear-through",
    "pass-through": "hear-through",
}


class RenderHalt(Exception):
    pass


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validator = _load_module("validate_manifest", os.path.join(HERE, "validate-manifest.py"))
parse_manifest = validator.parse_manifest

sys.path.insert(0, HERE)
import archetypes as AR  # noqa: E402


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def text(value):
    return html.escape(str(value), quote=False)


def attr(value):
    return html.escape(str(value), quote=True)


def strip_html_comments(markup):
    def keep_fallback(match):
        body = match.group(1).strip()
        if body.startswith("LLM-FALLBACK:"):
            return match.group(0)
        return ""

    return re.sub(r"<!--(.*?)-->", keep_fallback, markup, flags=re.S)


def strip_markers(markup):
    markup = strip_html_comments(markup)
    markup = re.sub(r'\s*data-instruction="[^"]*"', "", markup, flags=re.S)
    markup = re.sub(r'\s*data-(property|slot)="[^"]*"', "", markup)
    markup = re.sub(r"[ \t]+\n", "\n", markup)
    markup = re.sub(r"\n{3,}", "\n\n", markup)
    return markup.strip()


def snapshot_path(function_id):
    return os.path.join(SNAPSHOT_DIR, "%s.html" % function_id)


def component_path(archetype):
    return os.path.join(COMPONENT_DIR, "%s.html" % archetype)


def read_component(archetype):
    path = component_path(archetype)
    if not os.path.exists(path):
        lane2("unknown archetype %r has no component snippet" % archetype)
        return None
    return strip_html_comments(read_text(path)).strip()


def lane2(message):
    FALLBACKS.append(message)
    return "<!-- LLM-FALLBACK: %s -->" % message


def replace_placeholders(markup, values):
    for key, value in values.items():
        markup = markup.replace("{" + key + "}", attr(value))
    return markup


def add_class_to_first(markup, existing_class, new_class):
    pattern = r'class="([^"]*\b%s\b[^"]*)"' % re.escape(existing_class)

    def repl(match):
        classes = match.group(1).split()
        if new_class not in classes:
            classes.append(new_class)
        return 'class="%s"' % " ".join(classes)

    return re.sub(pattern, repl, markup, count=1)


def add_checked_to_first_input(markup):
    return re.sub(r"(<input\b(?![^>]*\bchecked\b)[^>]*)(>)", r"\1 checked\2", markup, count=1, flags=re.S)


def remove_element_by_class(markup, class_name):
    pattern = r'\s*<div class="%s">\s*</div>' % re.escape(class_name)
    markup = re.sub(pattern, "", markup, count=1, flags=re.S)
    pattern = r'\s*<div class="%s">.*?</div>' % re.escape(class_name)
    return re.sub(pattern, "", markup, count=1, flags=re.S)


def fill_element_by_class(markup, class_name, content):
    pattern = r'(<div class="%s">).*?(</div>)' % re.escape(class_name)
    return re.sub(pattern, lambda m: m.group(1) + "\n" + content + "\n  " + m.group(2),
                  markup, count=1, flags=re.S)


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
    raise ValueError("unterminated tag")


def replace_slot_contents(markup, slot_name, content):
    pos = markup.find('data-slot="%s"' % slot_name)
    if pos == -1:
        return markup
    tag_start = markup.rfind("<", 0, pos)
    tag_end = find_tag_end(markup, tag_start)
    close_start = markup.find("</div>", tag_end)
    if close_start == -1:
        return markup
    return markup[:tag_end + 1] + "\n" + content + "\n      " + markup[close_start:]


def remove_slot_element(markup, slot_name):
    pos = markup.find('data-slot="%s"' % slot_name)
    if pos == -1:
        return markup
    tag_start = markup.rfind("<", 0, pos)
    tag_end = find_tag_end(markup, tag_start)
    close_end = markup.find("</div>", tag_end)
    if close_end == -1:
        return markup
    return markup[:tag_start] + markup[close_end + len("</div>"):]


def set_data_property_text(markup, property_name, value):
    pattern = (
        r'(<(?P<tag>[a-zA-Z][\w:-]*)\b(?=[^>]*data-property="%s")[^>]*>)'
        r".*?"
        r"(</(?P=tag)>)"
    ) % re.escape(property_name)
    return re.sub(pattern, lambda m: m.group(1) + text(value) + m.group(3),
                  markup, count=1, flags=re.S)


def apply_snapshot_overrides(markup, function_entry):
    for key, value in function_entry.items():
        if key in ("id", "title", "info", "components"):
            continue
        if 'data-property="%s"' % key not in markup:
            continue
        if isinstance(value, bool):
            pattern = r'(<input\b(?=[^>]*data-property="%s")[^>]*)(>)' % re.escape(key)
            if value:
                markup = re.sub(pattern, r"\1 checked\2", markup, count=1, flags=re.S)
            else:
                markup = re.sub(r'(<input\b(?=[^>]*data-property="%s")[^>]*)\schecked\b' % re.escape(key),
                                r"\1", markup, count=1, flags=re.S)
        else:
            pattern = r'(<input\b(?=[^>]*data-property="%s")[^>]*\bvalue=")[^"]*(")' % re.escape(key)
            if re.search(pattern, markup, flags=re.S):
                markup = re.sub(pattern, lambda m: m.group(1) + attr(value) + m.group(2),
                                markup, count=1, flags=re.S)
            else:
                markup = set_data_property_text(markup, key, value)
    return markup


def render_info(info_text):
    snippet = read_component("info-tooltip")
    return replace_placeholders(snippet, {"info-text": info_text})


def render_function(function_entry, path="fn"):
    function_id = function_entry["id"]
    snap = snapshot_path(function_id)
    if os.path.exists(snap):
        return strip_markers(apply_snapshot_overrides(read_text(snap), function_entry))

    components = function_entry.get("components")
    if components is None:
        return lane2("function %s has no snapshot and no components" % function_id)

    frame = read_text(FUNCTION_FRAME)
    frame = set_data_property_text(frame, "function-title", function_entry.get("title", ""))
    sole = len(components) == 1
    card_level_toggle = sole and is_card_level_toggle(components[0])
    info_text = function_entry.get("info")
    if card_level_toggle and not info_text:
        info_text = components[0].get("info")
    if info_text:
        frame = replace_slot_contents(frame, "function-info", render_info(info_text))
    else:
        frame = remove_slot_element(frame, "function-info")

    if card_level_toggle:
        component = components[0]
        control_id = function_id
        frame = append_to_function_header(
            frame,
            render_switch_widget(
                component,
                control_id,
                controller=bool(component.get("dependents")),
            ),
        )
        rendered = render_dependents(component.get("dependents") or [], "%s.1" % path)
    else:
        rendered = []
        for idx, slot in enumerate(components, start=1):
            control_id = function_id if sole else "%s-%d" % (function_id, idx)
            rendered.append(render_slot(slot, "%s.%d" % (path, idx), sole=sole, top_level=True,
                                        control_id=control_id))
    frame = replace_slot_contents(frame, "components", "\n".join(rendered))
    return collapse_empty_content(strip_markers(frame))


def is_card_level_toggle(component):
    return (
        isinstance(component, dict)
        and component.get("archetype") == "toggle"
        and not component.get("label")
    )


def append_to_function_header(markup, content):
    marker = '\n      </div>\n      <div class="function-content"'
    if marker not in markup:
        return markup
    return markup.replace(marker, "\n%s%s" % (content, marker), 1)


def collapse_empty_content(markup):
    """Drop a body-less `.function-content` (a header-only card, e.g. a card-level
    toggle with no dependents) so the parent's 8px inter-item gap doesn't render an
    empty separator below the title row. Only matches whitespace-only content, so
    cards with real body content are untouched."""
    return re.sub(r'\s*<div class="function-content">\s*</div>', "", markup)


def unwrap_function(markup):
    script = ""
    script_at = markup.find("<script")
    if script_at != -1:
        script = markup[script_at:].strip()
        markup = markup[:script_at]
    match = re.search(
        r'<div class="function-container">\s*<div class="function-top-section">\s*<div>\s*(.*?)'
        r"\s*</div>\s*</div>\s*</div>\s*$",
        markup,
        flags=re.S,
    )
    inner = match.group(1).strip() if match else markup.strip()
    return inner + (("\n" + script) if script else "")


def is_nested_card_slot(slot):
    return (
        isinstance(slot, dict)
        and "function" not in slot
        and "archetype" not in slot
        and ("title" in slot or "components" in slot or "info" in slot)
    )


def render_nested_card(card, path):
    components = card.get("components") or []
    if card.get("info"):
        label = (
            '<div class="function-header">\n'
            '  <div class="function-title">\n'
            '    <p class="subfn-label">%s</p>\n'
            '  </div>\n'
            '  <div class="function-icons">\n%s\n  </div>\n'
            '</div>'
        ) % (text(card.get("title", "")), render_info(card["info"]))
    else:
        label = '<p class="subfn-label">%s</p>' % text(card.get("title", ""))

    sole = len(components) == 1
    children = []
    for idx, child in enumerate(components, start=1):
        rendered = render_slot(
            child,
            "%s.card%d" % (path, idx),
            sole=sole,
            top_level=True,
            control_id="%s-card%d" % (path.replace(".", "-"), idx),
        )
        children.append('<div class="subfn-child">\n%s\n</div>' % rendered)
    return '<div class="subfn-group">\n%s\n%s\n</div>' % (label, "\n".join(children))


def render_slot(slot, path, sole=False, top_level=False, control_id=None):
    if isinstance(slot, dict) and "function" in slot:
        function_id = slot["function"]
        snap = snapshot_path(function_id)
        if not os.path.exists(snap):
            return lane2("nested function %s has no snapshot" % function_id)
        return unwrap_function(strip_markers(read_text(snap)))
    if is_nested_card_slot(slot):
        return render_nested_card(slot, path)
    return render_component(
        slot,
        sole=sole,
        top_level=top_level,
        control_id=control_id or path.replace(".", "-"),
        path=path,
    )


def render_component(component, sole, top_level, control_id, path):
    archetype = component.get("archetype")
    spec = AR.ARCHETYPES.get(archetype)
    if spec is None:
        return lane2("unknown archetype %s" % archetype)
    if archetype == "dropdown":
        return render_dropdown(component, control_id)

    label = ""
    if spec["width"] == "full" and not (sole and top_level) and component.get("label"):
        label = '<p class="subfn-label">%s</p>\n' % text(component["label"])

    if archetype == "toggle":
        return render_toggle(component, control_id, path)
    if archetype == "slider":
        return label + render_slider(component, control_id)
    if archetype in ("segmented", "preset-grid"):
        return label + render_selector(component, archetype, control_id, path)

    return lane2("archetype %s is not implemented" % archetype)


def render_slider(component, control_id):
    snippet = read_component("slider")
    if snippet is None:
        return lane2("slider snippet is missing")
    return replace_placeholders(snippet, {
        "id": control_id,
        "min": component["min"],
        "max": component["max"],
        "val": component["value"],
    })


def render_toggle(component, control_id, path):
    snippet = read_component("toggle")
    if snippet is None:
        return lane2("toggle snippet is missing")
    snippet = replace_placeholders(snippet, {
        "id": control_id,
        "label": component.get("label", ""),
    })
    if not component.get("label"):
        snippet = remove_element_by_class(snippet, "function-title")
    if component.get("info"):
        snippet = fill_element_by_class(snippet, "function-icons", render_info(component["info"]))
    else:
        snippet = remove_element_by_class(snippet, "function-icons")
    if component.get("value") is True:
        snippet = add_checked_to_first_input(snippet)

    dependents = component.get("dependents")
    if not dependents:
        return snippet

    snippet = add_class_to_first(snippet, "switch-input", "subfn-toggle")
    children = render_dependents(dependents, path)
    return '<div class="subfn-group">\n%s\n%s\n</div>' % (snippet, "\n".join(children))


def render_switch_widget(component, control_id, controller=False):
    snippet = read_component("toggle")
    if snippet is None:
        return lane2("toggle snippet is missing")
    snippet = replace_placeholders(snippet, {
        "id": control_id,
        "label": component.get("label", ""),
    })
    if component.get("value") is True:
        snippet = add_checked_to_first_input(snippet)
    if controller:
        snippet = add_class_to_first(snippet, "switch-input", "subfn-toggle")
    match = re.search(r'<label class="switch">.*?</label>', snippet, flags=re.S)
    if not match:
        return lane2("toggle snippet has no switch widget")
    return match.group(0)


def render_dependents(dependents, path):
    children = []
    for idx, dependent in enumerate(dependents, start=1):
        children.append(
            '<div class="subfn-child">\n%s\n</div>' %
            render_slot(dependent, "%s.dep%d" % (path, idx))
        )
    return children


def extract_dropdown_li_unit(snippet):
    """Return the first <li …>…</li> block from the dropdown snippet as the repeatable option unit."""
    match = re.search(r'<li class="dropdown-item[^"]*"[^>]*>.*?</li>', snippet, flags=re.S)
    return match.group(0) if match else None


def render_dropdown(component, control_id):
    snippet = read_component("dropdown")
    if snippet is None:
        return lane2("dropdown snippet is missing")

    li_unit = extract_dropdown_li_unit(snippet)
    if li_unit is None:
        return lane2("dropdown snippet has no repeatable option unit")

    options = component.get("options", [])

    # Build the <li> list; mark the selected option
    selected_label = ""
    items = []
    for option in options:
        value = option.get("value", "")
        label = option.get("label", str(value))
        selected = option.get("selected") is True
        # Produce a clean li — reset class to base, then add --selected if needed
        li = re.sub(r'class="dropdown-item[^"]*"', 'class="dropdown-item"', li_unit, count=1)
        li = re.sub(r'data-value="[^"]*"', 'data-value="%s"' % attr(value), li, count=1)
        li = re.sub(r'data-property="[^"]*"', 'data-property="%s-option"' % attr(control_id), li, count=1)
        # Replace text content inside <li …>…</li>
        li = re.sub(r'>([^<]*)</li>', lambda m: ">%s</li>" % text(label), li, count=1)
        if selected:
            li = li.replace('class="dropdown-item"', 'class="dropdown-item dropdown-item--selected"', 1)
            selected_label = label
        items.append(li)

    # If no option is explicitly selected, show the first option's label as default
    if not selected_label and options:
        selected_label = options[0].get("label", str(options[0].get("value", "")))

    # Fill {id} placeholders throughout the snippet
    filled = replace_placeholders(snippet, {"id": control_id})

    # Replace the entire <ul class="dropdown-list">…</ul> block with our rendered items
    filled = re.sub(
        r'<ul class="dropdown-list">.*?</ul>',
        '<ul class="dropdown-list">\n    %s\n  </ul>' % "\n    ".join(items),
        filled,
        count=1,
        flags=re.S,
    )

    # Set the displayed selected value in the trigger span
    filled = set_data_property_text(filled, "%s-value" % control_id, selected_label)

    # Wrap in the same compact labeled row as toggle.html:
    #   .function-header > .function-title > .function-label  +  <details> widget
    # (no .function-icons — dropdown has no info slot in the archetype spec)
    label_html = text(component.get("label", ""))
    return (
        '<div class="function-header">\n'
        '  <div class="function-title">\n'
        '    <p class="function-label">%s</p>\n'
        '  </div>\n'
        '%s\n'
        '</div>'
    ) % (label_html, filled)


def extract_segment_unit(snippet):
    match = re.search(r'<label class="segment(?: segment--span)?">.*?</label>', snippet, flags=re.S)
    if not match:
        return None
    unit = match.group(0)
    unit = unit.replace("{value1}", "{value}")
    unit = unit.replace("{label1}", "{label}")
    return unit


def extract_panel_unit(snippet):
    match = re.search(r'<div class="segment-panel">.*?</div>', snippet, flags=re.S)
    return match.group(0) if match else '<div class="segment-panel"></div>'


def fill_panel(unit, content):
    open_tag_end = unit.find(">")
    close_tag_start = unit.rfind("</div>")
    if open_tag_end == -1 or close_tag_start == -1:
        return '<div class="segment-panel">%s</div>' % content
    if not content:
        return unit[:open_tag_end + 1] + "</div>"
    return unit[:open_tag_end + 1] + "\n%s\n" % content + unit[close_tag_start:]


def segment_icon(value):
    key = SEGMENT_ICON_ALIASES.get(str(value), str(value))
    path = os.path.join(SEGMENT_ICON_DIR, "%s.svg" % key)
    if not os.path.exists(path):
        raise RenderHalt("missing segment icon for value %s" % value)
    return read_text(path).strip()


def render_segment(unit, option, control_id, suffix, with_icon, span):
    segment = replace_placeholders(unit, {
        "id": control_id,
        "value": option.get("value", ""),
        "label": option.get("label", ""),
    })
    if span:
        segment = segment.replace('class="segment"', 'class="segment segment--span"', 1)
    if option.get("selected") is True:
        segment = add_checked_to_first_input(segment)
    if with_icon:
        segment = re.sub(
            r'<span class="segment-icon">.*?</span>',
            '<span class="segment-icon">%s</span>' % segment_icon(option.get("value")),
            segment,
            count=1,
            flags=re.S,
        )
    else:
        segment = re.sub(r'\s*<span class="segment-icon">.*?</span>', "", segment, count=1, flags=re.S)
    return segment.replace("{id}-mode", "%s-%s" % (attr(control_id), suffix))


def render_selector(component, archetype, control_id, path):
    snippet = read_component(archetype)
    if snippet is None:
        return lane2("%s snippet is missing" % archetype)
    unit = extract_segment_unit(snippet)
    if unit is None:
        return lane2("%s snippet has no repeatable segment unit" % archetype)

    options = component["options"]
    suffix = "mode" if archetype == "segmented" else "preset"
    use_icons = bool(component.get("icons")) and archetype == "segmented"
    odd_count = len(options) % 2 == 1
    segments = []
    for idx, option in enumerate(options, start=1):
        span = archetype == "preset-grid" and odd_count and idx == len(options)
        segments.append(render_segment(unit, option, control_id, suffix, use_icons, span))

    container_class = "segmented-control" if archetype == "segmented" else "preset-grid"
    panels = ""
    reveals = component.get("reveals")
    if reveals:
        panel_unit = extract_panel_unit(snippet)
        rendered_panels = []
        for idx, option in enumerate(options, start=1):
            value = option.get("value")
            slots = reveals.get(value)
            if slots is None:
                slots = reveals.get(str(value))
            content = ""
            if slots:
                content = "\n".join(render_slot(slot, "%s.panel%d.%d" % (path, idx, slot_idx))
                                    for slot_idx, slot in enumerate(slots, start=1))
            rendered_panels.append(fill_panel(panel_unit, content))
        panels = "\n  <div class=\"segment-panels\">\n%s\n  </div>" % "\n".join(rendered_panels)

    return (
        '<div class="segmented-group">\n\n'
        '  <div class="%s">\n%s\n  </div>%s\n\n'
        '</div>'
    ) % (container_class, "\n".join(segments), panels)


def render(manifest_path):
    manifest = parse_manifest(read_text(manifest_path))
    return "\n".join(render_function(fn, "fn%d" % idx)
                     for idx, fn in enumerate(manifest.get("functions") or [], start=1))


def main(argv):
    if len(argv) != 2:
        print("usage: render-content.py <subpage.manifest>", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(render(argv[1]) + "\n")
    except RenderHalt as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    if FALLBACKS:
        print("LANE-2 (LLM fallback) needed for %d item(s):" % len(FALLBACKS), file=sys.stderr)
        for item in FALLBACKS:
            print("  - " + item, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
