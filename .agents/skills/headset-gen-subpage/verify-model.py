#!/usr/bin/env python3
"""Verify that a headset model's pages reproduce exactly from its manifests.

Read-only gate: imports the deterministic renderers, captures their stdout, and compares
that output byte-for-byte with the on-disk pages. It never writes generated pages.
"""

import contextlib
import importlib.util
import io
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MODEL_ROOT = os.path.join(ROOT, "headset", "models")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_home = load_module("validate_home", os.path.join(HERE, "validate-home.py"))
render_home = load_module("render_home_for_verify", os.path.join(HERE, "render-home.py"))
render_subpage = load_module("render_subpage_for_verify", os.path.join(HERE, "render-subpage.py"))
render_model = load_module("render_model_for_verify", os.path.join(HERE, "render-model.py"))
render_walkthrough = load_module(
    "render_walkthrough_for_verify",
    os.path.join(HERE, "..", "shared-gen-walkthrough", "render-walkthrough.py"),
)


def rel(path):
    return os.path.relpath(path, ROOT)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def halt(message):
    print("HALT: %s" % message, file=sys.stderr)
    return 1


def parse_and_validate_home(path):
    try:
        manifest = validate_home.parse_manifest(read_text(path))
    except OSError as exc:
        raise ValueError("cannot read %s: %s" % (path, exc))
    except Exception as exc:
        raise ValueError("cannot parse %s: %s" % (path, exc))

    gate = validate_home.V()
    gate.manifest(manifest)
    if gate.errors:
        lines = ["%s is out of contract (%d issue(s)):" % (path, len(gate.errors))]
        lines.extend("  - %s" % error for error in gate.errors)
        raise ValueError("\n".join(lines))
    return manifest


def capture_renderer(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = module.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def rendered_bytes(page, module, argv):
    code, stdout, stderr = capture_renderer(module, argv)
    if code != 0:
        detail = stderr.strip() or stdout.strip() or "renderer exited %d" % code
        return None, detail
    return stdout.encode("utf-8"), None


def first_diff_hint(actual, expected):
    if actual == expected:
        return "sizes on disk %d / rendered %d" % (len(actual), len(expected))

    actual_lines = actual.decode("utf-8", "replace").splitlines()
    expected_lines = expected.decode("utf-8", "replace").splitlines()
    total = max(len(actual_lines), len(expected_lines))
    for idx in range(total):
        a = actual_lines[idx] if idx < len(actual_lines) else "<missing>"
        e = expected_lines[idx] if idx < len(expected_lines) else "<missing>"
        if a != e:
            return "sizes on disk %d / rendered %d; first differing line %d" % (
                len(actual),
                len(expected),
                idx + 1,
            )
    return "sizes on disk %d / rendered %d" % (len(actual), len(expected))


def expected_pages(model, home):
    pages = [("index.html", render_home, ["render-home.py", model])]
    seen = {"index.html"}
    for n, feature in enumerate(home.get("features") or []):
        link = feature.get("link") if isinstance(feature, dict) else None
        subpage = render_model.subpage_from_link(link, n)
        page = "%s.html" % subpage
        if page in seen:
            raise ValueError("duplicate feature target %r; refusing to verify the same page twice" % link)
        seen.add(page)
        pages.append((page, render_subpage, ["render-subpage.py", model, subpage]))
    # A model may also carry a cross-category walkthrough page (rendered by the shared
    # shared-gen-walkthrough skill). When its manifest is present, verify walkthrough.html too so the
    # byte gate covers it instead of flagging it as an unexpected on-disk page.
    if os.path.exists(os.path.join(MODEL_ROOT, model, "walkthrough.manifest")):
        pages.append(("walkthrough.html", render_walkthrough,
                      ["render-walkthrough.py", "headset", model, "-"]))
    return pages


def verify_model(model):
    model_dir = os.path.join(MODEL_ROOT, model)
    if not os.path.isdir(model_dir):
        return halt("model folder does not exist: %s" % rel(model_dir))

    home_manifest_path = os.path.join(model_dir, "home.manifest")
    try:
        home = parse_and_validate_home(home_manifest_path)
        pages = expected_pages(model, home)
    except (ValueError, render_model.RenderHalt) as exc:
        return halt(str(exc))

    ok = True
    offending = set()
    for page, module, argv in pages:
        path = os.path.join(model_dir, page)
        expected, error = rendered_bytes(page, module, argv)
        if error is not None:
            print("%s: DRIFT renderer failed: %s" % (page, error))
            ok = False
            offending.add(page)
            continue
        if not os.path.exists(path):
            print("%s: DRIFT missing on disk; renderer produced %d bytes" % (page, len(expected)))
            ok = False
            offending.add(page)
            continue
        actual = read_bytes(path)
        if actual == expected:
            print("%s: OK" % page)
        else:
            print("%s: DRIFT %s" % (page, first_diff_hint(actual, expected)))
            ok = False
            offending.add(page)

    if not ok:
        print("DRIFT: offending page(s): %s" % ", ".join(sorted(offending)), file=sys.stderr)
        return 1
    return 0


def main(argv):
    if len(argv) != 2:
        print("usage: verify-model.py <MODEL>", file=sys.stderr)
        return 2
    return verify_model(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
