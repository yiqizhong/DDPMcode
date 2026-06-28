#!/usr/bin/env python3
"""Deterministic renderer for a multi-step walkthrough page.

CROSS-CATEGORY: this skill is not namespaced to a device category. It renders a
`<category>/models/<MODEL>/walkthrough.manifest` into `walkthrough.html` in the same folder,
linking THREE stylesheets: shared/tokens.css (design tokens), <category>/<category>.css (frame +
masthead shell from the category layer), and shared/walkthrough.css (content-area + stepper).
The frame and masthead are identical to the home/subpage; only the content area differs.
The output is a JS-free stepper: hidden radios + CSS `:checked` reveal one step at a time
(the D11/D12 "runtime reveal inside one panel" pattern), so it stays a static, reproducible
artifact like every other generated page.

Usage:
    render-walkthrough.py <CATEGORY> <MODEL>      # writes <CATEGORY>/models/<MODEL>/walkthrough.html
    render-walkthrough.py <CATEGORY> <MODEL> -    # prints to stdout instead of writing

The Procedure in SKILL.md is the human-readable SPEC this script implements; keep them in lock-step.
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
FRAME = os.path.join(HERE, "templates", "walkthrough-frame.html")
STEP = os.path.join(HERE, "templates", "step.html")
ARROW_SVG = os.path.join(ROOT, "dds2", "dds2_arrow-right.svg")       # Next button icon
ARROW_LEFT_SVG = os.path.join(ROOT, "dds2", "dds2_arrow-left.svg")   # Back button icon
# (both copied, recolored to currentColor)

# shared/walkthrough.css maps step radios -> panels positionally (:nth-of-type up to N); keep in
# sync with that file's positional rule set.
MAX_STEPS = 6

TOP_KEYS = {"title", "cta", "done-link"}


class RenderHalt(Exception):
    pass


def halt(message):
    raise RenderHalt(message)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def text(value):
    return html.escape(str(value), quote=False)


def attr(value):
    return html.escape(str(value), quote=True)


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_manifest(raw):
    """Minimal, dependency-free parse of the walkthrough schema: top-level scalars
    (title / cta / done-link) + a `steps:` list of `{title, body, image?}` maps."""
    data = {"steps": []}
    current = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        is_item = stripped.startswith("- ")
        if is_item:
            stripped = stripped[2:].strip()
            current = {}
            data["steps"].append(current)
        if ":" not in stripped:
            halt("cannot parse line (no key): %r" % line.strip())
        key, _, value = stripped.partition(":")
        key, value = key.strip(), _unquote(value.strip())
        if key == "steps":
            current = None
            continue
        if is_item or (indent > 0 and current is not None):
            current[key] = value
        elif indent == 0 and key in TOP_KEYS:
            data[key] = value
            current = None
        else:
            halt("unexpected key %r outside a step" % key)
    return data


def validate(manifest):
    steps = manifest.get("steps") or []
    if not steps:
        halt("walkthrough has no steps[]")
    if len(steps) > MAX_STEPS:
        halt("too many steps (%d > MAX_STEPS=%d); shared/walkthrough.css only maps %d positionally"
             % (len(steps), MAX_STEPS, MAX_STEPS))
    for i, step in enumerate(steps, start=1):
        for required in ("title", "body"):
            if not step.get(required):
                halt("step %d is missing required %r" % (i, required))


def rewrite_css_paths(markup, category):
    # preview depth (4 up) -> output depth (3 up): <category>/models/<MODEL>/walkthrough.html
    # Three links to rewrite:
    #   shared/tokens.css       — depth 4 -> depth 3
    #   headset/headset.css     — depth 4, category-specific -> depth 2 with actual category
    #   shared/walkthrough.css  — depth 4 -> depth 3
    return (
        markup
        .replace('href="../../../../shared/tokens.css"', 'href="../../../shared/tokens.css"')
        .replace('href="../../../../headset/headset.css"',
                 'href="../../%s.css"' % category)
        .replace('href="../../../../shared/walkthrough.css"', 'href="../../../shared/walkthrough.css"')
    )


def strip_markers(markup):
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
    markup = re.sub(r'\s*data-(slot|property|instruction)="[^"]*"', "", markup)
    markup = re.sub(r"[ \t]+\n", "\n", markup)
    markup = re.sub(r"\n{3,}", "\n\n", markup)
    return markup.strip() + "\n"


def replace_placeholders(markup, values):
    for key, value in values.items():
        markup = markup.replace("{" + key + "}", attr(value))
    return markup


def fill_slot(markup, slot_name, content):
    # Match the element carrying data-slot="<name>" regardless of tag (<main>, <div>, …) and replace
    # its inner content up to its OWN close tag. Slots are empty (comment-only) in the templates, so
    # the non-greedy match to the captured tag's close is unambiguous.
    pattern = (r'(<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*\bdata-slot="%s"[^>]*>).*?(</(?P=tag)>)'
               % re.escape(slot_name))
    return re.sub(pattern, lambda m: m.group(1) + "\n" + content + "\n  " + m.group(3),
                  markup, count=1, flags=re.S)


def _icon(svg_path, css_class):
    # COPY a dds2 arrow asset; recolor its hardcoded fill to inherit the button's text color.
    svg = read_text(svg_path).strip().replace('fill="#0E0E0E"', 'fill="currentColor"')
    return '<span class="%s">%s</span>' % (css_class, svg)


def render_nav(index, count, cta, done_link):
    # Figma walkthrough nav, position-dependent:
    #   first step  -> Next (primary + arrow) + Skip (tertiary)
    #   middle step -> Back (icon-only) + Next (primary + arrow) + Skip (tertiary)
    #   last step   -> Back (icon-only) + Finish/CTA (primary, no arrow)
    back = ('<label class="wt-btn wt-back" for="wt-step-%d">%s</label>'
            % (index - 1, _icon(ARROW_LEFT_SVG, "wt-btn-arrow")))
    parts = []
    if index > 1:
        parts.append(back)
    if index < count:
        parts.append('<label class="wt-btn wt-next" for="wt-step-%d"><span>Next</span>%s</label>'
                     % (index + 1, _icon(ARROW_SVG, "wt-btn-arrow")))
        parts.append('<a class="wt-btn wt-skip" href="%s">Skip</a>' % attr(done_link))
    else:
        parts.append('<a class="wt-btn wt-next wt-done" href="%s"><span>%s</span></a>'
                     % (attr(done_link), text(cta)))
    return "\n    ".join(parts)


def render_step(step, index, count, cta, done_link):
    markup = read_text(STEP)
    markup = replace_placeholders(markup, {
        "progress": round(index * 100 / count),
        "title": step["title"],
        "body": step["body"],
    })
    image = step.get("image")
    if image:
        markup = markup.replace("{image}", attr(image))
    else:
        # No image -> keep the .wt-media box as a uniform light-gray placeholder (like every other
        # empty/unconfigured template region); just drop the <img>.
        markup = re.sub(r'\s*<img class="wt-image"[^>]*>', "", markup, count=1)
    markup = fill_slot(markup, "nav", render_nav(index, count, cta, done_link))
    return markup


def render_walkthrough(manifest):
    steps = manifest["steps"]
    count = len(steps)
    cta = manifest.get("cta", "Get started")
    done_link = manifest.get("done-link", "index.html")

    radios = "\n  ".join(
        '<input type="radio" name="wt-step" id="wt-step-%d" class="wt-radio"%s>'
        % (i, " checked" if i == 1 else "")
        for i in range(1, count + 1)
    )
    panels = "\n".join(render_step(step, i, count, cta, done_link)
                       for i, step in enumerate(steps, start=1))
    return (
        '%s\n'
        '  <div class="wt-stage">\n%s\n  </div>'
    ) % (radios, panels)


def render_page(category, model):
    model_dir = os.path.join(ROOT, category, "models", model)
    manifest_path = os.path.join(model_dir, "walkthrough.manifest")
    if not os.path.exists(manifest_path):
        halt("no walkthrough manifest at %s" % os.path.relpath(manifest_path, ROOT))

    manifest = parse_manifest(read_text(manifest_path))
    validate(manifest)

    page = rewrite_css_paths(read_text(FRAME), category)
    page = re.sub(r'(data-property="walkthrough-title">)[^<]*(</title>)',
                  lambda m: m.group(1) + text(manifest.get("title", "Walkthrough")) + m.group(2),
                  page, count=1)
    page = fill_slot(page, "walkthrough", render_walkthrough(manifest))
    return strip_markers(page)


def main(argv):
    if len(argv) not in (3, 4):
        print("usage: render-walkthrough.py <CATEGORY> <MODEL> [-]", file=sys.stderr)
        return 2
    category, model = argv[1], argv[2]
    to_stdout = len(argv) == 4 and argv[3] == "-"
    try:
        html_out = render_page(category, model)
    except RenderHalt as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    if to_stdout:
        sys.stdout.write(html_out)
    else:
        out_path = os.path.join(ROOT, category, "models", model, "walkthrough.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        print("wrote %s" % os.path.relpath(out_path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
