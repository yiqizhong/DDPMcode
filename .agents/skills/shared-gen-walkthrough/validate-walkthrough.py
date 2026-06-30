#!/usr/bin/env python3
"""Validate a shared walkthrough manifest against the generation schema.

Mechanical enforcement of the HALT rules in shared-gen-walkthrough/SKILL.md so the
renderer consumes only the fixed `{title, cta?, done-link?, steps[]}` contract.
Zero dependencies (stdlib only) so it ALWAYS runs.

Usage:  python3 validate-walkthrough.py <path/to/walkthrough.manifest>
Exit 0 = valid (generation may proceed).  Exit 1 = HALT (prints each violation).
"""
import re
import sys

MAX_STEPS = 6
TOP_ALLOWED_KEYS = frozenset(("title", "cta", "done-link", "steps"))
STEP_ALLOWED_KEYS = frozenset(("title", "body", "image"))


# ---- minimal YAML-subset parser (block maps, block seqs, scalars, inline {flow}) ----

def _scalar(tok):
    tok = tok.strip()
    if tok and tok[0] in "\"'" and tok[-1] == tok[0]:
        return tok[1:-1]
    low = tok.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", tok):
        return float(tok)
    return tok


def _parse_inline_map(text):
    inner = text.strip()[1:-1]
    out = {}
    for part in inner.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError("bad inline mapping: " + text)
        k, v = part.split(":", 1)
        out[k.strip()] = _scalar(v)
    return out


def _strip_comment(line):
    if line.lstrip().startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", line).rstrip()


def _tokenize(text):
    rows = []
    for raw in text.splitlines():
        clean = _strip_comment(raw)
        if not clean.strip():
            continue
        indent = len(clean) - len(clean.lstrip(" "))
        rows.append((indent, clean.strip()))
    return rows


def _parse(rows, i, indent):
    first = rows[i][1]
    if first.startswith("- "):
        seq = []
        while i < len(rows) and rows[i][0] == indent and rows[i][1].startswith("- "):
            after = rows[i][1][2:].strip()
            block = [(indent + 2, after)] if after else []
            i += 1
            while i < len(rows) and rows[i][0] > indent:
                block.append(rows[i])
                i += 1
            if not block:
                seq.append(None)
            elif block[0][1].startswith("{"):
                seq.append(_parse_inline_map(block[0][1]))
            elif ":" in block[0][1] and not block[0][1].startswith("{"):
                val, _ = _parse(block, 0, indent + 2)
                seq.append(val)
            else:
                seq.append(_scalar(block[0][1]))
        return seq, i
    m = {}
    while i < len(rows) and rows[i][0] == indent and not rows[i][1].startswith("- "):
        line = rows[i][1]
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            j = i + 1
            if j < len(rows) and rows[j][0] > indent:
                child, i = _parse(rows, j, rows[j][0])
                m[key] = child
            else:
                m[key] = None
                i += 1
        elif rest.startswith("{"):
            m[key] = _parse_inline_map(rest)
            i += 1
        else:
            m[key] = _scalar(rest)
            i += 1
    return m, i


def parse_manifest(text):
    rows = _tokenize(text)
    if not rows:
        return {}
    val, _ = _parse(rows, 0, rows[0][0])
    return val


# ---- validation ----

class V:
    def __init__(self):
        self.errors = []

    def err(self, where, msg):
        self.errors.append("%s: %s" % (where, msg))

    def unknown_keys(self, where, obj, allowed):
        for key in obj:
            if key not in allowed:
                self.err(
                    where,
                    "unknown key `%s` (allowed: %s)" % (
                        key,
                        ", ".join("`%s`" % k for k in sorted(allowed)),
                    ),
                )

    def _missing(self, m, field):
        return field not in m or m.get(field) is None or m.get(field) == ""

    def _string_if_present(self, where, m, field):
        if field not in m or m.get(field) is None:
            return
        if not isinstance(m.get(field), str) or m.get(field) == "":
            self.err(where, "`%s` must be a non-empty string when present" % field)

    def manifest(self, m):
        if not isinstance(m, dict):
            self.err("manifest", "top level is not a mapping")
            return
        self.unknown_keys("manifest", m, TOP_ALLOWED_KEYS)
        if self._missing(m, "title"):
            self.err("manifest", "missing `title`")
        for field in ("title", "cta", "done-link"):
            self._string_if_present("manifest.%s" % field, m, field)

        steps = m.get("steps")
        if steps is None:
            self.err("manifest", "missing `steps` list")
            return
        if not isinstance(steps, list):
            self.err("manifest", "`steps` must be a list")
            return
        if not steps:
            self.err("manifest", "walkthrough has no steps[]")
            return
        if len(steps) > MAX_STEPS:
            self.err(
                "manifest.steps",
                "too many steps (%d > MAX_STEPS=%d); shared/walkthrough.css only maps %d positionally"
                % (len(steps), MAX_STEPS, MAX_STEPS),
            )
        for n, step in enumerate(steps, start=1):
            where = "step %d" % n
            if not isinstance(step, dict):
                self.err(where, "step is not a mapping")
                continue
            self.unknown_keys(where, step, STEP_ALLOWED_KEYS)
            for required in ("title", "body"):
                if self._missing(step, required):
                    self.err(where, "step %d is missing required %r" % (n, required))
            for field in ("title", "body", "image"):
                self._string_if_present("%s.%s" % (where, field), step, field)


def main(argv):
    if len(argv) != 2:
        print("usage: validate-walkthrough.py <walkthrough.manifest>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print("cannot read %s: %s" % (path, e), file=sys.stderr)
        return 2
    try:
        manifest = parse_manifest(text)
    except Exception as e:
        print("HALT: cannot parse %s: %s" % (path, e), file=sys.stderr)
        return 1
    v = V()
    v.manifest(manifest)
    if v.errors:
        print("HALT — %s is out of contract (%d issue(s)):" % (path, len(v.errors)), file=sys.stderr)
        for e in v.errors:
            print("  - %s" % e, file=sys.stderr)
        return 1
    print("OK — %s passes walkthrough schema validation" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
