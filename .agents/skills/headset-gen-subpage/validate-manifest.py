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

# The archetype contract is the single source of truth in archetypes.py (next to this
# script); the validator derives every archetype rule from it and hardcodes none of its own.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archetypes import (
    ARCHETYPES,
    ALL_ARCHETYPES,
    SELECTOR_ARCHETYPES,
    DROPDOWN_SMALL_MAX,
    DROPDOWN_REASONS,
    COUNT_RULE_HINT,
    OPTION_KEYS,
    FUNCTION_SLOT_KEYS,
    component_allowed_keys,
)

REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "functions")
sys.path.insert(0, REGISTRY)
from keywords import SNAPSHOT_KEYWORDS

# Every archetype's render path (render-content.py read_component) copies
# headset-shared/components/<archetype>.html by filename == archetype. Mirrored here so a
# deleted/renamed snippet is caught at the validation gate, not only as a lane-2 fallback
# (silently-broken output) at render time.
COMPONENT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "headset-shared", "components")
)

# The minimal YAML-subset parser is shared across category + cross-category validators;
# canonical copy lives in shared-lib (not a skill — same pattern as headset-shared/).
SHARED_LIB = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared-lib")
)
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("manifest_parser", os.path.join(SHARED_LIB, "manifest_parser.py"))
_manifest_parser = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_manifest_parser)
parse_manifest = _manifest_parser.parse_manifest

SUBPAGE_ALLOWED_KEYS = frozenset(("title", "functions"))
FUNCTION_ALLOWED_KEYS = frozenset((
    "id",
    "title",
    "info",
    "components",
    "snapshot-opt-out",
    "opt-out-reason",
))
NESTED_CARD_SLOT_KEYS = frozenset(("title", "info", "components"))
MAX_NESTED_CARD_DEPTH = 1


def keyword_matches(text, keyword):
    words = [re.escape(part) for part in str(keyword).lower().split()]
    if not words:
        return False
    pattern = r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(words) + r"(?![a-z0-9])"
    return re.search(pattern, str(text).lower()) is not None


def restates_title(label, title):
    """True when the label merely RESTATES the card title — the label's word set is a
    subset of the title's (exact match or an abbreviation like "Volume Tone" ⊆ "Volume
    Adjustment Tone"). This is the signature of a card master switch mis-authored as a
    labeled member row: the title already names the control, so the label just re-words
    it. Direction matters: only label ⊆ title counts. The reverse (title ⊆ label, e.g.
    "Enable Dell Audio Promotion" under "Dell Audio Promotion") is the established
    "Enable <feature>" toggle idiom, not a restatement, so it stays legal. Genuinely
    distinct grouped members (e.g. "Mic Noise Canceling" under "Collaboration") share no
    words and return False."""
    lt = set(re.findall(r"[a-z0-9]+", str(label).lower()))
    tt = set(re.findall(r"[a-z0-9]+", str(title).lower()))
    if not lt or not tt:
        return False
    return lt <= tt


# ---- validation ----

class V:
    def __init__(self):
        self.errors = []
        self.advisories = []

    def err(self, where, msg):
        self.errors.append("%s: %s" % (where, msg))

    def advisory(self, msg):
        self.advisories.append(msg)

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

    def snapshot_keyword_check(self, fn, function_id):
        """Check whether an assembled function's id/title matches a registered snapshot keyword.

        If matched and no valid opt-out is present → blocking HALT.
        If matched and a valid opt-out is present → advisory only (exit 0).
        If not matched but snapshot-opt-out is present → stale/blanket opt-out → blocking HALT.
        """
        haystack = "%s %s" % (function_id, fn.get("title", ""))
        matched_snapshot = None
        matched_keyword = None
        for snapshot_id, keywords in SNAPSHOT_KEYWORDS.items():
            for keyword in keywords:
                if keyword_matches(haystack, keyword):
                    matched_snapshot = snapshot_id
                    matched_keyword = keyword
                    break
            if matched_snapshot:
                break

        opt_out = fn.get("snapshot-opt-out")
        opt_reason = fn.get("opt-out-reason", "")

        if opt_out is not None:
            # opt-out present — validate it regardless of whether there's a keyword match
            if matched_snapshot is None:
                self.err(
                    "function[%s]" % function_id,
                    "`snapshot-opt-out: %s` is present but function '%s' does not match any "
                    "registered snapshot keyword — remove stale opt-out" % (opt_out, function_id)
                )
                return
            if opt_out != matched_snapshot:
                self.err(
                    "function[%s]" % function_id,
                    "`snapshot-opt-out: %s` does not match the keyword-matched snapshot '%s' — "
                    "set `snapshot-opt-out: %s` or correct the id" % (opt_out, matched_snapshot, matched_snapshot)
                )
                return
            if not opt_reason or not str(opt_reason).strip():
                self.err(
                    "function[%s]" % function_id,
                    "`snapshot-opt-out` requires a non-empty `opt-out-reason` explaining why "
                    "the assembled path is correct instead of snapshot '%s'" % matched_snapshot
                )
                return
            # Valid opt-out — downgrade to advisory
            self.advisory(
                "ADVISORY: function '%s' matches snapshot '%s' (keyword '%s') — "
                "consider setting id to it." % (function_id, matched_snapshot, matched_keyword)
            )
            return

        if matched_snapshot is not None:
            self.err(
                "function[%s]" % function_id,
                "id/title matches snapshot '%s' (keyword '%s') — set `id: %s` and remove "
                "`components:`, OR add `snapshot-opt-out: %s` with a non-empty `opt-out-reason` "
                "to confirm this is an assembled control, not the snapshot card"
                % (matched_snapshot, matched_keyword, matched_snapshot, matched_snapshot)
            )

    def component(self, sc, where, top_sole=False, card_title=None, nested_card_depth=0):
        if not isinstance(sc, dict):
            self.err(where, "component is not a mapping")
            return
        if "condition" in sc:
            self.err(where, "legacy `condition:` field — express conditional content via a selector's "
                            "`reveals` (show/hide) or a toggle's `dependents` (grey-out)")
        arch = sc.get("archetype")
        if arch is None:
            self.err(where, "component missing `archetype`")
            return
        spec = ARCHETYPES.get(arch)
        if spec is None:
            if arch == "section":
                self.err(
                    where,
                    "unknown archetype 'section'; use a nested card slot instead: "
                    "`title: <string>` + optional `info:` + `components: [<slot>...]` "
                    "(no `archetype` key)",
                )
                return
            self.err(where, "unknown archetype %r (allowed: %s)" % (arch, ", ".join(sorted(ALL_ARCHETYPES))))
            return
        if not os.path.exists(os.path.join(COMPONENT_DIR, "%s.html" % arch)):
            self.err(where, "archetype %r has no component snippet headset-shared/components/%s.html "
                            "(add the snippet, or add the archetype to archetypes.py + its snippet)"
                     % (arch, arch))
            return
        self.unknown_keys(where, sc, component_allowed_keys(arch))

        # Required props — checked by KEY PRESENCE so a numeric/bool prop may be 0 / false.
        for prop in spec["required"]:
            if prop not in sc:
                self.err(where, "`%s` is missing required prop `%s`" % (arch, prop))
        if arch == "slider":
            self.slider_value_sanity(sc, where)

        # Label — positional: controls need their own label unless they are the card's
        # sole top-level control (then the card title covers it).
        label = sc.get("label")
        if label is not None and card_title is not None:
            label_norm = str(label).strip().lower()
            title_norm = str(card_title).strip().lower()
            # A sole top-level toggle is the master/member fork (D30): the card may be a
            # single-feature card whose title IS the switch's name (no label → master switch
            # on the title row) OR a group card with one named member (a label distinct from
            # the title). Which one is a SEMANTIC call the requirement decides, not something
            # string math can settle — so we do NOT hard-block it (D31). Two tiers:
            #   • exact `label == title` — an unambiguous structural duplicate (D24a); no
            #     legitimate reading, so it stays a hard error.
            #   • label RESTATES the title (word-subset, e.g. "Volume Tone" ⊆ "Volume
            #     Adjustment Tone") but is not an exact dup — a heuristic *suspicion* that the
            #     author meant a master switch but wrote it in member form. It is only a proxy
            #     for a semantic judgment (and would false-flag a legit member whose name
            #     happens to sub-set the title), so it is a non-blocking ADVISORY: the build
            #     completes, the flag is surfaced at the end for the requirement-reader (LLM at
            #     authoring time, or a human) to decide. Scoped to the sole toggle.
            if label_norm and title_norm and label_norm == title_norm:
                self.err(
                    where,
                    "redundant `label` equals card title — omit it; the card title is the label",
                )
            elif arch == "toggle" and top_sole and restates_title(label_norm, title_norm):
                self.advisory(
                    "ADVISORY: %s: sole toggle `label` %r looks like it restates the card "
                    "title %r — if the on/off IS the whole function, drop the label so it "
                    "renders as the card's master switch; keep it only if this is a distinct "
                    "grouped feature. Flagged for review; not blocking." % (where, label, card_title)
                )
        if not top_sole and not sc.get("label"):
            if spec["width"] == "compact":
                self.err(where, "`%s` renders as a labeled row and needs a non-empty `label`" % arch)
            else:
                self.err(where, "full-width `%s` is not the card's sole control here, so it needs a "
                                "`label` (rendered as its .subfn-label heading; a missing one is "
                                "dropped data — the BUG-002 class)" % arch)

        # Options — governed by the catalog's per-archetype count window + the dropdown-reason gate.
        opts = sc.get("options")
        opt_rule = spec["options"]
        if opt_rule == "forbidden":
            if opts is not None:
                self.err(where, "`options` is not valid on `%s`" % arch)
            opts = []
        elif opts is None:
            if opt_rule == "required":
                self.err(where, "`%s` must have a non-empty `options` list" % arch)
            opts = []
        elif not isinstance(opts, list) or not opts:
            self.err(where, "`options` on `%s` must be a non-empty list" % arch)
            opts = []
        else:
            n = len(opts)
            # Count window from the contract (archetypes.py): segmented 2-3, preset-grid 4-6,
            # dropdown 2+. A violation means a different archetype is the deterministic answer.
            lo = spec.get("min_options")
            hi = spec.get("max_options")
            if lo is not None and n < lo:
                self.err(where, "`%s` needs at least %d options (got %d) — %s"
                         % (arch, lo, n, COUNT_RULE_HINT))
            if hi is not None and n > hi:
                self.err(where, "`%s` allows at most %d options (got %d) — %s"
                         % (arch, hi, n, COUNT_RULE_HINT))
            # A small dropdown (<= threshold) must justify itself; otherwise it should be a visible
            # selector. This is what pins segmented-vs-dropdown so the same input can't flap.
            if arch == "dropdown" and n <= DROPDOWN_SMALL_MAX:
                reason = sc.get("dropdown-reason")
                if reason is None:
                    self.err(where, "a `dropdown` with %d options must be a visible selector "
                                    "(2-3 -> segmented, 4-6 -> preset-grid) UNLESS it declares a "
                                    "`dropdown-reason` (%s)"
                             % (n, ", ".join(sorted(DROPDOWN_REASONS))))
                elif reason not in DROPDOWN_REASONS:
                    self.err(where, "`dropdown-reason: %r` is not recognized (allowed: %s)"
                             % (reason, ", ".join(sorted(DROPDOWN_REASONS))))
            seen_v, seen_l, n_selected = set(), set(), 0
            for o in opts:
                if not isinstance(o, dict):
                    self.err(where, "each option must be a mapping with `label` and `value`")
                    continue
                self.unknown_keys(where, o, OPTION_KEYS)
                v, l = o.get("value"), o.get("label")
                if v is None:
                    self.err(where, "an option is missing `value`")
                elif v in seen_v:
                    self.err(where, "duplicate option value %r" % v)
                if l is None or l == "":
                    self.err(where, "an option is missing `label`")
                elif l in seen_l:
                    self.err(where, "duplicate option label %r" % l)
                if o.get("selected") is True:
                    n_selected += 1
                seen_v.add(v)
                seen_l.add(l)
            if n_selected > 1:
                self.err(where, "%d options marked `selected` — at most one may be pre-selected" % n_selected)
            if arch in SELECTOR_ARCHETYPES and n_selected == 0:
                self.err(where, "a selector needs exactly one option marked `selected`")

        # reveals — only on the archetypes whose conditional channel is "reveals".
        if "reveals" in sc:
            if spec["conditional"] != "reveals":
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
                        self.slots(
                            slots,
                            "%s>reveals[%s]" % (where, key),
                            card_title=card_title,
                            nested_card_depth=nested_card_depth,
                        )

        # dependents — only on the archetype whose conditional channel is "dependents" (toggle).
        if "dependents" in sc:
            if spec["conditional"] != "dependents":
                alt = "`reveals`" if spec["conditional"] == "reveals" else "no conditional channel"
                self.err(where, "`dependents` is only valid on a `toggle`; `%s` carries %s" % (arch, alt))
            self.slots(
                sc.get("dependents"),
                "%s>dependents" % where,
                card_title=card_title,
                nested_card_depth=nested_card_depth,
            )

    def is_number(self, value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def slider_value_sanity(self, sc, where):
        values = {}
        for field in ("min", "max", "value"):
            if field not in sc:
                continue
            value = sc.get(field)
            values[field] = value
            if not self.is_number(value):
                self.err(where, "slider field `%s` must be a number (got %r)" % (field, value))
        if all(field in values and self.is_number(values[field]) for field in ("min", "max")):
            if values["min"] >= values["max"]:
                self.err(
                    where,
                    "slider requires min < max (got min %s, max %s)" % (values["min"], values["max"]),
                )
        if all(field in values and self.is_number(values[field]) for field in ("min", "max", "value")):
            if values["value"] < values["min"] or values["value"] > values["max"]:
                self.err(
                    where,
                    "slider value %s is outside min %s and max %s"
                    % (values["value"], values["min"], values["max"]),
                )
        if "stops" in sc:
            stops = sc.get("stops")
            if not isinstance(stops, int) or isinstance(stops, bool) or stops < 2:
                self.err(where, "slider field `stops` must be an integer >= 2 (got %r)" % stops)

    def nested_card(self, card, where, nested_card_depth):
        if nested_card_depth > MAX_NESTED_CARD_DEPTH:
            self.err(
                where,
                "nested assembled card depth %d exceeds the pure-CSS cap of %d; deeper nesting "
                "requires the not-yet-built declarative show/hide engine (D13)"
                % (nested_card_depth, MAX_NESTED_CARD_DEPTH),
            )
        self.unknown_keys(where, card, NESTED_CARD_SLOT_KEYS)
        if not card.get("title"):
            self.err(where, "nested card slot missing required `title`")
        components = card.get("components")
        if components is None:
            self.err(where, "nested card slot missing required `components` list")
            return
        if not isinstance(components, list):
            self.err(where, "`components` must be a list")
            return
        self.slots(
            components,
            "%s>components" % where,
            top_level=True,
            top_sole=(len(components) == 1),
            card_title=card.get("title"),
            nested_card_depth=nested_card_depth,
        )

    def is_nested_card_slot(self, slot):
        return (
            isinstance(slot, dict)
            and "function" not in slot
            and "archetype" not in slot
            and ("title" in slot or "components" in slot or "info" in slot)
        )

    def slots(self, slots, where, top_level=False, top_sole=False, card_title=None, nested_card_depth=0):
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
                self.unknown_keys(sw, slot, FUNCTION_SLOT_KEYS)
                fid = slot["function"]
                snap = os.path.join(REGISTRY, "%s.html" % fid)
                if not os.path.exists(snap):
                    self.err(sw, "function slot %r has no snapshot functions/%s.html (a bare function "
                                 "slot must reference an existing snapshot)" % (fid, fid))
            elif self.is_nested_card_slot(slot):
                self.nested_card(slot, sw, nested_card_depth + 1)
            else:
                self.component(
                    slot,
                    sw,
                    top_sole=(top_level and top_sole),
                    card_title=card_title,
                    nested_card_depth=nested_card_depth,
                )

    def function(self, fn, where):
        if not isinstance(fn, dict):
            self.err(where, "function entry is not a mapping")
            return
        self.unknown_keys(where, fn, FUNCTION_ALLOWED_KEYS)
        fid = fn.get("id")
        if not fid:
            self.err(where, "function missing `id`")
            return
        where = "function[%s]" % fid
        has_snapshot = os.path.exists(os.path.join(REGISTRY, "%s.html" % fid))
        if not has_snapshot:
            self.snapshot_keyword_check(fn, fid)
        if has_snapshot and "components" in fn:
            self.err(where, "snapshot functions/%s.html carries its own structure; remove `components:` "
                            "from function `%s`" % (fid, fid))
            return
        subs = fn.get("components")
        if subs is None:
            if not has_snapshot:
                self.err(where, "no `components` and no snapshot functions/%s.html (cannot render)" % fid)
            return
        if not isinstance(subs, list):
            self.err(where, "`components` must be a list")
            return
        # A lone top-level full-width control renders headingless (no `label` needed).
        self.slots(
            subs,
            "%s>components" % where,
            top_level=True,
            top_sole=(len(subs) == 1),
            card_title=fn.get("title"),
        )

    def manifest(self, m):
        if not isinstance(m, dict):
            self.err("manifest", "top level is not a mapping")
            return
        self.unknown_keys("manifest", m, SUBPAGE_ALLOWED_KEYS)
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
    for advisory in v.advisories:
        print(advisory, file=sys.stderr)
    if v.errors:
        print("HALT — %s is out of contract (%d issue(s)):" % (path, len(v.errors)), file=sys.stderr)
        for e in v.errors:
            print("  - %s" % e, file=sys.stderr)
        return 1
    print("OK — %s passes schema validation" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
