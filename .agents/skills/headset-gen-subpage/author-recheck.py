#!/usr/bin/env python3
"""author-recheck.py — authoring-phase orchestrator for the D31 master/member advisory.

This is the automated "path b" closed loop, run at AUTHORING time, BEFORE render:

    validate → for each restatement flag → consult the requirement (LLM, once per field,
    read B) → deterministically apply the decision to the manifest SOURCE → re-validate.

For each *restatement* advisory (a sole top-level `toggle` whose `label` looks like it
restates the card title, e.g. `Volume Tone` under `Volume Adjustment Tone`) it asks an LLM,
given the requirement, whether the on/off IS the whole function (→ MASTER: drop the label so
it renders as the card's title-row master switch) or a distinctly named grouped feature (→
MEMBER: keep the label). A MASTER decision is applied deterministically by Python (the toggle's
`label:` line is removed); MEMBER leaves the manifest as authored. The result is re-validated;
if an edit fails to clear the flag or introduces an error it is reverted and the field stays
flagged. Unresolved / declined fields are never blocked — they remain advisory.

Determinism boundary: this tool edits the MANIFEST (the source of truth). `render-model.py`
never calls an LLM and stays byte-deterministic. The LLM's only role is the master/member
judgment; the edit itself is deterministic Python.

Usage:
    author-recheck.py <manifest> <requirements-file> [--in-place] [--report-only]

    <requirements-file>  plain-text requirement the field is judged against (the LLM reads it).
    --in-place           write resolved manifest back to <manifest> (default: write to stdout).
    --report-only        decide + report but never write (implies no edits persisted).

LLM wiring (either):
    AUTHOR_RECHECK_LLM_CMD   a shell command that reads a prompt on stdin and prints a JSON
                             object {"decision":"master"|"member","reason":"..."} on stdout.
    (default)                shells to `codex exec -m $AUTHOR_RECHECK_MODEL` (default model
                             gpt-5.4-mini), read-only sandbox.
    AUTHOR_RECHECK_DECISIONS a JSON map {function_id: "master"|"member"} used INSTEAD of any
                             LLM call — for deterministic tests.

Exit code is always 0 (advisory aid; it informs, it never gates).
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VM = _load("validate_manifest_for_recheck", os.path.join(HERE, "validate-manifest.py"))


def flagged_fields(manifest):
    """Return [{fid, title, label}] for every function whose SOLE top-level component is a
    toggle with a label that RESTATES the card title (word-subset) but is not an exact
    duplicate. Mirrors the advisory branch in validate-manifest.py exactly."""
    out = []
    for fn in manifest.get("functions") or []:
        if not isinstance(fn, dict):
            continue
        comps = fn.get("components")
        if not (isinstance(comps, list) and len(comps) == 1 and isinstance(comps[0], dict)):
            continue
        comp = comps[0]
        if comp.get("archetype") != "toggle":
            continue
        label = comp.get("label")
        title = fn.get("title")
        if label is None or title is None:
            continue
        ln, tn = str(label).strip().lower(), str(title).strip().lower()
        if not ln or not tn or ln == tn:  # exact dup is a hard error, not our advisory
            continue
        if VM.restates_title(ln, tn):
            out.append({"fid": fn.get("id"), "title": title, "label": label})
    return out


def has_errors(text):
    """True if the manifest text fails hard validation (parse or contract errors)."""
    try:
        m = VM.parse_manifest(text)
    except Exception:
        return True
    v = VM.V()
    v.manifest(m)
    return bool(v.errors)


def function_span(lines, fid):
    """[start, end) line indices of the `- id: <fid>` function block, or None."""
    head = re.compile(r"^\s*-\s+id:\s*['\"]?" + re.escape(str(fid)) + r"['\"]?\s*$")
    any_head = re.compile(r"^\s*-\s+id:")
    start = next((i for i, ln in enumerate(lines) if head.match(ln)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if any_head.match(lines[i])), len(lines))
    return start, end


def remove_label_line(text, fid, label):
    """Deterministically drop the toggle's `label: <label>` line inside function <fid>.
    Matched BY VALUE, so a dependent's differently-valued label (e.g. `Tone Mode`) is never
    touched. Returns new text, or None if the exact line was not found (caller keeps original)."""
    lines = text.split("\n")
    span = function_span(lines, fid)
    if span is None:
        return None
    start, end = span
    want = str(label).strip()
    line_re = re.compile(r"^\s*label:\s*['\"]?(.*?)['\"]?\s*$")
    for i in range(start, end):
        m = line_re.match(lines[i])
        if m and m.group(1).strip() == want:
            del lines[i]
            return "\n".join(lines)
    return None


def consult_llm(field, requirements_text):
    """Ask whether <field> is a MASTER switch or a named MEMBER, given the requirement.
    Returns 'master' | 'member' | None (undecided). Honors AUTHOR_RECHECK_DECISIONS (stub)
    first, then AUTHOR_RECHECK_LLM_CMD, then a default codex invocation."""
    stub = os.environ.get("AUTHOR_RECHECK_DECISIONS")
    if stub:
        try:
            decision = json.loads(stub).get(field["fid"])
        except Exception:
            decision = None
        return decision if decision in ("master", "member") else None

    prompt = (
        "You are deciding one field in a headset UI manifest.\n"
        "A card titled %r has a single on/off toggle whose label is %r.\n\n"
        "Two legal shapes:\n"
        "- MASTER: the on/off IS the whole function; the card title already names it, so the "
        "toggle should have NO label (it renders as the card's title-row master switch).\n"
        "- MEMBER: the toggle names a DISTINCT feature grouped under the card; the label stays.\n\n"
        "Decide strictly from the requirement below — does the on/off belong to the function "
        "itself (MASTER) or is it a distinctly named sub-feature (MEMBER)?\n\n"
        "=== REQUIREMENT ===\n%s\n=== END ===\n\n"
        'Reply with ONE line of JSON and nothing else: {"decision":"master"|"member","reason":"..."}'
        % (field["title"], field["label"], requirements_text)
    )

    cmd = os.environ.get("AUTHOR_RECHECK_LLM_CMD")
    if cmd:
        argv, shell = cmd, True
    else:
        model = os.environ.get("AUTHOR_RECHECK_MODEL", "gpt-5.4-mini")
        argv = ["codex", "exec", "-m", model, "--sandbox", "read-only", "--skip-git-repo-check", "-"]
        shell = False
    try:
        proc = subprocess.run(
            argv, shell=shell, input=prompt, capture_output=True, text=True, timeout=600
        )
    except Exception as exc:
        sys.stderr.write("author-recheck: LLM call failed (%s) — leaving field flagged\n" % exc)
        return None
    matches = re.findall(r'"decision"\s*:\s*"(master|member)"', proc.stdout or "")
    return matches[-1] if matches else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("requirements")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv[1:])

    with open(args.manifest, encoding="utf-8") as f:
        text = f.read()
    with open(args.requirements, encoding="utf-8") as f:
        requirements_text = f.read()

    try:
        manifest = VM.parse_manifest(text)
    except Exception as exc:
        sys.stderr.write("author-recheck: cannot parse %s: %s\n" % (args.manifest, exc))
        return 0

    fields = flagged_fields(manifest)
    report = []
    for field in fields:  # read B: each field is consulted at most once, no re-loop
        decision = consult_llm(field, requirements_text)
        if decision == "master":
            edited = remove_label_line(text, field["fid"], field["label"])
            if edited is not None and not has_errors(edited) and not any(
                f["fid"] == field["fid"] for f in flagged_fields(VM.parse_manifest(edited))
            ):
                text = edited
                report.append((field, "master", "label removed → master switch"))
            else:
                report.append((field, "master", "auto-edit failed/unsafe — LEFT FLAGGED"))
        elif decision == "member":
            report.append((field, "member", "kept as distinct member (advisory may persist)"))
        else:
            report.append((field, "undecided", "LLM undecided — LEFT FLAGGED"))

    if not args.report_only:
        if args.in_place:
            with open(args.manifest, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            sys.stdout.write(text)

    if report:
        sys.stderr.write("\n==== author-recheck: %d field(s) reconsidered ====\n" % len(report))
        for field, decision, action in report:
            sys.stderr.write(
                "  - function[%s] label %r vs title %r → %s: %s\n"
                % (field["fid"], field["label"], field["title"], decision.upper(), action)
            )
    else:
        sys.stderr.write("author-recheck: no restatement flags — nothing to reconsider\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
