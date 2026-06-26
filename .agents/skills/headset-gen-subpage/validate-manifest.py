#!/usr/bin/env python3
"""Validate a headset sub-page manifest against the generation schema.

Mechanical enforcement of the HALT rules in headset-gen-subpage/SKILL.md so a weak
model cannot reason around prose. Zero dependencies (stdlib only) so it ALWAYS runs.

Usage:  python3 validate-manifest.py <path/to/subpage.manifest>
Exit 0 = valid (generation may proceed).  Exit 1 = HALT (prints each violation).
"""
import os
import re
import sys

SELECTOR_ARCHETYPES = {"segmented", "preset-grid"}
ALL_ARCHETYPES = {"toggle", "slider", "segmented", "preset-grid", "dropdown"}
MAX_OPTIONS = 6  # headset.css positional :has() maps .segment / .segment-panel nth-child up to 6
FULL_WIDTH = {"segmented", "preset-grid", "slider"}

REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "functions")


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

    def subcontrol(self, sc, where):
        if not isinstance(sc, dict):
            self.err(where, "sub-control is not a mapping")
            return
        if "condition" in sc:
            self.err(where, "legacy `condition:` field — express conditional content via a selector's "
                            "`reveals` (show/hide) or a toggle's `dependents` (grey-out)")
        arch = sc.get("archetype")
        if arch is None:
            self.err(where, "sub-control missing `archetype`")
            return
        if arch not in ALL_ARCHETYPES:
            self.err(where, "unknown archetype %r (allowed: %s)" % (arch, ", ".join(sorted(ALL_ARCHETYPES))))

        opts = sc.get("options")
        if arch in SELECTOR_ARCHETYPES:
            if not isinstance(opts, list) or not opts:
                self.err(where, "selector `%s` must have a non-empty `options` list" % arch)
                opts = []
            if len(opts) > MAX_OPTIONS:
                self.err(where, "%d options exceeds the max of %d (CSS :has() maps nth-child up to 6)"
                         % (len(opts), MAX_OPTIONS))
            seen_v, seen_l = set(), set()
            for o in opts:
                if not isinstance(o, dict):
                    continue
                v, l = o.get("value"), o.get("label")
                if v in seen_v:
                    self.err(where, "duplicate option value %r" % v)
                if l in seen_l:
                    self.err(where, "duplicate option label %r" % l)
                seen_v.add(v)
                seen_l.add(l)
        elif opts is not None:
            self.err(where, "`options` is only valid on a selector (segmented | preset-grid), not `%s`" % arch)

        if "reveals" in sc:
            if arch not in SELECTOR_ARCHETYPES:
                self.err(where, "`reveals` is only valid on a selector (segmented | preset-grid); for a "
                                "toggle's grey-out children use `dependents` on a toggle")
            else:
                option_values = {str(o.get("value")) for o in opts if isinstance(o, dict)}
                rev = sc.get("reveals") or {}
                if not isinstance(rev, dict):
                    self.err(where, "`reveals` must be a mapping of option-value -> slot list")
                else:
                    for key, slots in rev.items():
                        if str(key) not in option_values:
                            self.err(where, "`reveals` key %r matches no option value (have: %s)"
                                     % (key, ", ".join(sorted(option_values)) or "none"))
                        self.slots(slots, "%s>reveals[%s]" % (where, key))

        if "dependents" in sc:
            if arch != "toggle":
                self.err(where, "`dependents` is only valid on a `toggle`; `%s` is not a toggle "
                                "— a selector's conditional children use `reveals`" % arch)
            self.slots(sc.get("dependents"), "%s>dependents" % where)

    def slots(self, slots, where):
        if slots is None:
            return
        if not isinstance(slots, list):
            self.err(where, "expected a list of slots")
            return
        for n, slot in enumerate(slots):
            sw = "%s[%d]" % (where, n)
            if not isinstance(slot, dict):
                self.err(sw, "slot is not a mapping")
                continue
            if "function" in slot:
                fid = slot["function"]
                snap = os.path.join(REGISTRY, "%s.html" % fid)
                if not os.path.exists(snap):
                    self.err(sw, "function slot %r has no snapshot functions/%s.html (a bare function "
                                 "slot must reference an existing snapshot)" % (fid, fid))
            else:
                self.subcontrol(slot, sw)

    def function(self, fn, where):
        if not isinstance(fn, dict):
            self.err(where, "function entry is not a mapping")
            return
        fid = fn.get("id")
        if not fid:
            self.err(where, "function missing `id`")
            return
        where = "function[%s]" % fid
        subs = fn.get("subcontrols")
        has_snapshot = os.path.exists(os.path.join(REGISTRY, "%s.html" % fid))
        if subs is None:
            if not has_snapshot:
                self.err(where, "no `subcontrols` and no snapshot functions/%s.html (cannot render)" % fid)
            return
        if not isinstance(subs, list):
            self.err(where, "`subcontrols` must be a list")
            return
        for n, sc in enumerate(subs):
            self.subcontrol(sc, "%s>subcontrols[%d]" % (where, n))

    def manifest(self, m):
        if not isinstance(m, dict):
            self.err("manifest", "top level is not a mapping")
            return
        if not m.get("title"):
            self.err("manifest", "missing `title`")
        fns = m.get("functions")
        if fns is None:
            self.err("manifest", "missing `functions` list")
            return
        if not isinstance(fns, list):
            self.err("manifest", "`functions` must be a list")
            return
        for n, fn in enumerate(fns):
            self.function(fn, "functions[%d]" % n)


def main(argv):
    if len(argv) != 2:
        print("usage: validate-manifest.py <subpage.manifest>", file=sys.stderr)
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
    print("OK — %s passes schema validation" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
