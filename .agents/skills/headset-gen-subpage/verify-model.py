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


def expected_manifests(model, home):
    """{home.manifest, walkthrough.manifest (optional), each feature-linked <stem>.manifest} —
    the manifest set reachable from home.manifest. Any other top-level *.manifest in the model
    dir is an orphan: not validated, not rendered, not reported by anything (FIX 4)."""
    names = {"home.manifest"}
    for n, feature in enumerate(home.get("features") or []):
        link = feature.get("link") if isinstance(feature, dict) else None
        subpage = render_model.subpage_from_link(link, n)
        names.add("%s.manifest" % subpage)
    if os.path.exists(os.path.join(MODEL_ROOT, model, "walkthrough.manifest")):
        names.add("walkthrough.manifest")
    return names


def check_orphan_manifests(model, home, offending):
    """Any top-level *.manifest in the model dir not reachable from home.manifest.features[]
    (and not home.manifest / walkthrough.manifest itself) is orphaned: never validated,
    rendered, or reported. Runs independent of whether the model's HTML is on disk / committed,
    so it covers gitignored-HTML fixture models too."""
    model_dir = os.path.join(MODEL_ROOT, model)
    expected = expected_manifests(model, home)
    ok = True
    for name in sorted(os.listdir(model_dir)):
        path = os.path.join(model_dir, name)
        if not os.path.isfile(path) or not name.endswith(".manifest"):
            continue
        if name not in expected:
            print("%s: DRIFT orphan manifest — not reachable from home.features" % name)
            ok = False
            offending.add(name)
    return ok


def check_stray_html(model, pages, offending):
    """Any top-level *.html in the model dir that isn't one of the expected rendered pages
    (index.html, each feature sub-page, walkthrough.html when applicable) is a stray,
    hand-written file — the "never hand-write HTML" rule had no mechanical enforcement for
    new files until this check. Only meaningful where HTML is expected on disk (the caller
    skips this for gitignored-HTML fixture models, same as the byte-drift check)."""
    model_dir = os.path.join(MODEL_ROOT, model)
    expected = {page for page, _module, _argv in pages}
    ok = True
    for name in sorted(os.listdir(model_dir)):
        path = os.path.join(model_dir, name)
        if not os.path.isfile(path) or not name.endswith(".html"):
            continue
        if name not in expected:
            print("%s: DRIFT stray page — not produced by the pipeline" % name)
            ok = False
            offending.add(name)
    return ok


def verify_model(model, manifests_only=False):
    model_dir = os.path.join(MODEL_ROOT, model)
    if not os.path.isdir(model_dir):
        return halt("model folder does not exist: %s" % rel(model_dir))

    home_manifest_path = os.path.join(model_dir, "home.manifest")
    try:
        home = parse_and_validate_home(home_manifest_path)
        pages = expected_pages(model, home)
    except (ValueError, render_model.RenderHalt) as exc:
        return halt(str(exc))

    offending = set()
    ok = check_orphan_manifests(model, home, offending)

    if manifests_only:
        if not ok:
            print("DRIFT: offending manifest(s): %s" % ", ".join(sorted(offending)), file=sys.stderr)
            return 1
        return 0

    if not check_stray_html(model, pages, offending):
        ok = False

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
    manifests_only = False
    args = argv[1:]
    if "--manifests-only" in args:
        manifests_only = True
        args = [a for a in args if a != "--manifests-only"]
    if len(args) != 1:
        print("usage: verify-model.py <MODEL> [--manifests-only]", file=sys.stderr)
        return 2
    return verify_model(args[0], manifests_only=manifests_only)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
