#!/usr/bin/env python3
"""Shared helpers for the headset-gen-subpage renderers (render-home.py,
render-subpage.py). Extracted because these were byte-identical copies
across both files.
"""

import html
import importlib.util
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
