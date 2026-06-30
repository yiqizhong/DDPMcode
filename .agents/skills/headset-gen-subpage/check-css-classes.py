#!/usr/bin/env python3
"""Verify that literal HTML class tokens are defined by linked local stylesheets.

System-level mechanical gate: scans the shared snippet/template library and rendered
model HTML, then HALTs if any literal class="..." token has no matching .class selector
in the local stylesheets those pages/templates link.

Zero dependencies (stdlib only) so it can run everywhere verify-all.sh runs.
"""

import argparse
import glob
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

LINK_RE = re.compile(
    r"<link\b(?=[^>]*\brel\s*=\s*['\"]stylesheet['\"])[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"][^>]*>",
    re.IGNORECASE,
)
CLASS_ATTR_RE = re.compile(r"\bclass\s*=\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
LITERAL_CLASS_RE = re.compile(r"^-?[_a-zA-Z][-_a-zA-Z0-9]*$")
CSS_CLASS_RE = re.compile(r"(?<![a-zA-Z0-9_-])\.(-?[_a-zA-Z][-_a-zA-Z0-9]*)")
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.IGNORECASE | re.DOTALL)


def rel(path):
    path = os.path.abspath(path)
    if os.path.commonpath([ROOT, path]) != ROOT:
        return path
    return os.path.relpath(path, ROOT)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def iter_files(patterns):
    seen = set()
    for pattern in patterns:
        for path in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            path = os.path.abspath(path)
            if path in seen or not os.path.isfile(path):
                continue
            seen.add(path)
            yield path


def is_local_stylesheet_href(href):
    href = href.strip()
    if not href or href.startswith(("http://", "https://", "//", "data:", "#")):
        return False
    return True


def strip_url_suffix(href):
    return href.split("#", 1)[0].split("?", 1)[0]


def discover_stylesheets():
    """Resolve every local stylesheet linked by generation templates or rendered pages."""
    html_patterns = (
        ".agents/skills/**/*.html",
        "headset/models/*/*.html",
    )
    stylesheets = {}
    missing = []
    for html_path in iter_files(html_patterns):
        html = read_text(html_path)
        for match in LINK_RE.finditer(html):
            href = strip_url_suffix(match.group(1))
            if not is_local_stylesheet_href(href):
                continue
            css_path = os.path.normpath(os.path.join(os.path.dirname(html_path), href))
            css_path = os.path.abspath(css_path)
            if os.path.isfile(css_path):
                stylesheets[css_path] = None
            else:
                missing.append("%s links missing stylesheet %s" % (rel(html_path), match.group(1)))
    return sorted(stylesheets), missing


def remove_css_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def remove_attribute_selectors(selector):
    return re.sub(r"\[[^\]]*\]", "", selector)


def remove_strings(selector):
    return re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", "", selector)


def class_selectors_from_css(css):
    css = remove_css_comments(css)
    classes = set()
    start = 0
    for index, char in enumerate(css):
        if char == "{":
            selector = css[start:index].strip()
            start = index + 1
            if not selector or selector.startswith("@"):
                continue
            selector = remove_strings(remove_attribute_selectors(selector))
            for match in CSS_CLASS_RE.finditer(selector):
                classes.add(match.group(1))
        elif char == "}":
            start = index + 1
    return classes


def defined_classes(stylesheets):
    classes = set()
    for path in stylesheets:
        classes.update(class_selectors_from_css(read_text(path)))
    return classes


def html_sources(extra_html):
    patterns = (
        ".agents/skills/headset-shared/**/*.html",
        ".agents/skills/headset-gen-subpage/templates/**/*.html",
        ".agents/skills/shared-gen-walkthrough/templates/**/*.html",
        "headset/models/*/*.html",
    )
    paths = list(iter_files(patterns))
    for path in extra_html:
        paths.append(os.path.abspath(path))
    return sorted(dict.fromkeys(paths))


def literal_class_tokens(value):
    for token in value.split():
        if "{{" in token or "}}" in token or "{" in token or "}" in token:
            continue
        if LITERAL_CLASS_RE.fullmatch(token):
            yield token


def inline_style_classes(text):
    """Classes defined in a file's own inline <style> blocks."""
    classes = set()
    for block in STYLE_BLOCK_RE.finditer(text):
        classes.update(class_selectors_from_css(block.group(1)))
    return classes


def scan_files(paths):
    """path -> (used class tokens, classes defined in that file's own inline <style>).

    A class is valid for a file if a linked stylesheet defines it OR the file's own
    inline <style> defines it. Real rendered pages carry zero inline styles, so this
    masks nothing there; it only lets self-contained preview artifacts pass."""
    scanned = {}
    for path in paths:
        text = read_text(path)
        tokens = set()
        for match in CLASS_ATTR_RE.finditer(text):
            tokens.update(literal_class_tokens(match.group(2)))
        if not tokens:
            continue
        scanned[path] = (tokens, inline_style_classes(text))
    return scanned


def main(argv):
    parser = argparse.ArgumentParser(
        description="HALT when HTML uses a literal class not defined by linked CSS."
    )
    parser.add_argument(
        "--extra-html",
        action="append",
        default=[],
        help="Additional HTML fixture to scan, used by regression tests.",
    )
    args = parser.parse_args(argv[1:])

    stylesheets, missing_stylesheets = discover_stylesheets()
    if missing_stylesheets:
        print("HALT: missing linked stylesheet(s):", file=sys.stderr)
        for item in missing_stylesheets:
            print("  - %s" % item, file=sys.stderr)
        return 1
    if not stylesheets:
        print("HALT: no local linked stylesheets discovered", file=sys.stderr)
        return 1

    defined = defined_classes(stylesheets)
    scanned = scan_files(html_sources(args.extra_html))

    offenders = []
    for path, (classes, inline) in scanned.items():
        allowed = defined | inline
        for name in sorted(classes - allowed):
            offenders.append((path, name))

    if offenders:
        print("HALT: undefined CSS class(es) (%d):" % len(offenders), file=sys.stderr)
        for path, name in offenders:
            print("  - %s: %s" % (rel(path), name), file=sys.stderr)
        return 1

    used_count = len(set().union(*(t for t, _ in scanned.values()))) if scanned else 0
    print(
        "CSS-CLASSES OK: %d used class(es), %d defined class(es), %d stylesheet(s)"
        % (used_count, len(defined), len(stylesheets))
    )
    for path in stylesheets:
        print("  - %s" % rel(path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
