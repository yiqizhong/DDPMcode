"""Sub-control archetype catalog — the SINGLE SOURCE OF TRUTH for the contract that
`validate-manifest.py` enforces (the machine-readable analog of a json-render `defineCatalog`).

Adding a new archetype = add a block here AND add its snippet under
`headset-shared/subcontrols/<archetype>.html`. The validator derives EVERY archetype rule
from this dict — it hardcodes no archetype names, option caps, or width sets of its own.

Per-archetype keys
──────────────────
  width        "compact" -> renders as a row (label left + widget right); `label` is ALWAYS
                            required (a labeled row with no name is broken).
               "full"    -> renders stacked (a `.subfn-label` heading above the widget);
                            `label` is required UNLESS the control is its card's SOLE
                            top-level control (then the card title covers it and it renders
                            headingless — e.g. a lone ANC/OFF segmented).
  conditional  which conditional channel this archetype may carry:
                 "reveals"    -> selector: option-value -> slot list (show/hide a panel)
                 "dependents" -> toggle: ordered slot list that greys out when OFF
                 None         -> carries neither
  options      "required" | "optional" | "forbidden" — whether this archetype takes an
               `options` list. Selectors (conditional == "reveals") are capped at MAX_OPTIONS
               because headset.css maps panels with positional :has() only up to nth-child(6);
               a non-selector option list (dropdown's <details> overlay) is uncapped.
  required     extra props that MUST be present (checked by KEY PRESENCE, so a numeric/bool
               prop may legitimately be 0 / false). `label` is intentionally NOT listed here —
               it is enforced positionally from `width` (see above).
  optional     props allowed but not required (whitelist / documentation).
  when         one-line data-shape trigger ("use this archetype when …"). Only the mechanical
               part of control selection lives here; the FUZZY heuristics (segmented-vs-dropdown
               count, segmented-vs-preset-grid semantics, the acoustic-environment icon rule)
               resist encoding and stay in prose — subcontrols/README.md + headset/AGENTS.md.

Run `python3 archetypes.py` to print the authoritative contract table (the json-render
`catalog.prompt()` analog) instead of hand-copying a parallel table into the docs.
"""

# headset.css positional :has() maps .segment / .segment-panel nth-child up to 6.
MAX_OPTIONS = 6

ARCHETYPES = {
    "toggle": {
        "width": "compact",
        "conditional": "dependents",
        "options": "forbidden",
        "required": [],
        "optional": ["label", "value"],
        "when": "Boolean on/off (2-state)",
    },
    "dropdown": {
        "width": "compact",
        "conditional": None,
        "options": "required",   # a manifest-authored dropdown needs its choices
        "required": [],
        "optional": ["label", "options"],
        "when": "Pick 1 of N — many options or tight space",
    },
    "slider": {
        "width": "full",
        "conditional": None,
        "options": "forbidden",
        "required": ["min", "max", "value"],
        "optional": ["label"],
        "when": "A value on an ordered range / stepped scale",
    },
    "segmented": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "required": [],
        "optional": ["label", "icons"],
        "when": "Pick 1 of N — 2-4 visible, or acoustic-environment icon modes",
    },
    "preset-grid": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "required": [],
        "optional": ["label"],
        "when": "Pick 1 preset / profile — 4-6 named cards",
    },
}

# Derived sets — the validator imports these instead of re-listing archetype names.
ALL_ARCHETYPES = set(ARCHETYPES)
SELECTOR_ARCHETYPES = {k for k, v in ARCHETYPES.items() if v["conditional"] == "reveals"}


# ---- catalog.prompt() analog: render the contract as a markdown table ----------------
# The single authoritative selection/contract table, DERIVED from ARCHETYPES above so it can
# never drift from what validate-manifest.py enforces. Docs point here instead of hand-copying.

_SHAPE = {
    "compact": "row (label left + widget right)",
    "full": "stacked (.subfn-label heading above)",
}
_COND = {"reveals": "reveals (show/hide panel)", "dependents": "dependents (grey-out)", None: "—"}
_OPTS = {"required": "required", "optional": "optional", "forbidden": "—"}

# Fixed authoring order (mechanical contract reads top-to-bottom; not the dict's insertion order).
_ORDER = ["toggle", "slider", "segmented", "preset-grid", "dropdown"]


def _required_props(name, spec):
    # `label` is positional, not in spec["required"]; render it with its rule, then the rest.
    label = "label" if spec["width"] == "compact" else "label\\*"
    return ", ".join([label] + list(spec["required"]))


def render_table():
    lines = [
        "# Sub-control archetype contract — DERIVED from archetypes.py",
        "",
        "> Authoritative + always in sync with the `validate-manifest.py` gate. Do NOT hand-copy a",
        "> parallel table into the docs; regenerate with `python3 archetypes.py`. The fuzzy heuristics",
        "> (segmented-vs-dropdown count, segmented-vs-preset-grid semantics, the acoustic-environment",
        "> icon rule) are NOT mechanical and stay in prose — subcontrols/README.md + headset/AGENTS.md.",
        "",
        "| Archetype | Use when (data shape) | Renders as | Conditional | Options | Required props |",
        "|---|---|---|---|---|---|",
    ]
    for name in _ORDER:
        spec = ARCHETYPES[name]
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (
            name, spec["when"], _SHAPE[spec["width"]], _COND[spec["conditional"]],
            _OPTS[spec["options"]], _required_props(name, spec),
        ))
    lines += [
        "",
        "\\* A full-width control may omit `label` ONLY when it is the card's sole top-level control",
        "  (then the card title covers it and it renders headingless); anywhere else a missing label is",
        "  dropped data (the BUG-002 class). A selector caps `options` at %d." % MAX_OPTIONS,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_table())
