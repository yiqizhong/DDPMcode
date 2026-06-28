#!/usr/bin/env python3
"""Read-probe: render a model through the deterministic pipeline and write a TABLE of every
repo file the generation READ.

Usage:  python3 trace-render.py <MODEL>
Writes: headset/models/<MODEL>/READ-LOG.md  — one row per file read (path + read count),
        so you can verify the generation consulted exactly the right snippets / snapshots /
        registry / manifests, every run.

It wraps `builtins.open` to log read-mode opens of files under the repo, then runs
`render-model.py <MODEL>` (which orchestrates render-home / render-subpage / render-content +
the gates). Writes are NOT logged (only reads). This works because generation goes through code;
a black-box agent's reads cannot be captured this way (use the Windsurf UI / `fs_usage` for that).
"""
import builtins
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

_real_open = builtins.open
_reads = {}


def _is_read(mode):
    return ("r" in mode or "+" in mode) and "w" not in mode and "a" not in mode and "x" not in mode


def _traced_open(file, mode="r", *args, **kwargs):
    try:
        p = os.path.abspath(file) if isinstance(file, (str, bytes, os.PathLike)) else ""
        if p and p.startswith(ROOT + os.sep) and _is_read(mode if isinstance(mode, str) else "r"):
            _reads[p] = _reads.get(p, 0) + 1
    except Exception:
        pass
    return _real_open(file, mode, *args, **kwargs)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    if len(argv) != 2:
        print("usage: trace-render.py <MODEL>", file=sys.stderr)
        return 2
    model = argv[1]

    render_model = _load("render_model_traced", os.path.join(HERE, "render-model.py"))

    builtins.open = _traced_open
    try:
        code = render_model.main(["render-model.py", model])
    finally:
        builtins.open = _real_open

    log_path = os.path.join(ROOT, "headset", "models", model, "READ-LOG.md")
    rows = sorted(((os.path.relpath(p, ROOT), n) for p, n in _reads.items()))
    rows.sort(key=lambda r: (-r[1], r[0]))
    with _real_open(log_path, "w", encoding="utf-8") as f:
        f.write("# Files read while generating model `%s`\n\n" % model)
        f.write("> Auto-written by `trace-render.py`. Every file the deterministic pipeline READ\n")
        f.write("> to bake this model (frame, snippets, snapshots, icon registry, manifests, gates).\n")
        f.write("> If a file you expected (e.g. a snapshot or `keywords.py`) is missing, the\n")
        f.write("> generation did not consult it.\n\n")
        f.write("| reads | file |\n|---|---|\n")
        for rel, n in rows:
            f.write("| %d | `%s` |\n" % (n, rel))
        f.write("\n_%d distinct files read._\n" % len(rows))

    print("read-log: %s (%d files)" % (os.path.relpath(log_path, ROOT), len(rows)), file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
