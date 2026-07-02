#!/usr/bin/env python3
"""Minimal YAML-subset parser shared by every category/cross-category validator.

Not a skill (no SKILL.md — same pattern as headset-shared/). Category validators
(e.g. headset-gen-subpage/validate-manifest.py) and cross-category validators
(e.g. shared-gen-walkthrough/validate-walkthrough.py) load this module via the
existing importlib-by-path pattern. Dependency direction: category -> shared is
fine; shared must never import a category module.

Supports block maps, block sequences, scalars, and inline `{flow}` maps — the
subset every manifest in this repo is written in. Zero dependencies (stdlib only).
"""
import re


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
