#!/usr/bin/env python3
"""Deterministic whole-model renderer for headset product pages."""

import importlib.util
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MODEL_ROOT = os.path.join(ROOT, "headset", "models")


class RenderHalt(Exception):
    pass


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_home = load_module("render_home", os.path.join(HERE, "render-home.py"))
render_subpage = load_module("render_subpage", os.path.join(HERE, "render-subpage.py"))


def halt(message):
    raise RenderHalt(message)


def rel(path):
    return os.path.relpath(path, ROOT)


def write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def subpage_from_link(link, feature_index):
    if not isinstance(link, str) or not link:
        halt("features[%d].link must be a non-empty <subpage>.html string" % feature_index)
    if "/" in link or "\\" in link or link in (".html", "..html"):
        halt("features[%d].link must be a direct <subpage>.html filename: %r" % (feature_index, link))
    if not link.endswith(".html"):
        halt("features[%d].link must end in .html: %r" % (feature_index, link))
    subpage = link[:-5]
    if not subpage or subpage in (".", "..") or subpage.startswith("."):
        halt("features[%d].link has an invalid sub-page stem: %r" % (feature_index, link))
    return subpage


def render_model(model):
    model_dir = os.path.join(MODEL_ROOT, model)
    home_manifest_path = os.path.join(model_dir, "home.manifest")
    if not os.path.isdir(model_dir):
        halt("model folder does not exist: %s" % rel(model_dir))

    # Gate home.manifest first; render-home.py uses the same gate internally when rendering.
    home = render_home.parse_and_validate_home(home_manifest_path)

    written = []
    home_output = os.path.join(model_dir, "index.html")
    write_text(home_output, render_home.render_page(model))
    written.append(home_output)

    seen = set()
    for n, feature in enumerate(home.get("features") or []):
        link = feature.get("link") if isinstance(feature, dict) else None
        subpage = subpage_from_link(link, n)
        if subpage in seen:
            halt("duplicate feature target %r; refusing to render the same sub-page twice" % link)
        seen.add(subpage)

        manifest_path = os.path.join(model_dir, "%s.manifest" % subpage)
        if not os.path.exists(manifest_path):
            halt("dangling feature route %r: missing %s" % (link, rel(manifest_path)))

        # Gate each sub-page manifest explicitly before rendering it.
        render_subpage.parse_and_validate(render_subpage.validate_manifest, manifest_path, manifest_path)

        output_path = os.path.join(model_dir, "%s.html" % subpage)
        write_text(output_path, render_subpage.render_page(model, subpage))
        written.append(output_path)

    return written


def main(argv):
    if len(argv) != 2:
        print("usage: render-model.py <MODEL>", file=sys.stderr)
        return 2

    try:
        written = render_model(argv[1])
    except (
        RenderHalt,
        render_home.RenderHalt,
        render_home.render_content.RenderHalt,
        render_subpage.RenderHalt,
        render_subpage.render_content.RenderHalt,
    ) as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1
    except OSError as exc:
        print("HALT: %s" % exc, file=sys.stderr)
        return 1

    print("Wrote %d file(s):" % len(written))
    for path in written:
        print("  - %s" % rel(path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
