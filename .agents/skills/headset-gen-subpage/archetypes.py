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
    },
    "dropdown": {
        "width": "compact",
        "conditional": None,
        "options": "required",   # a manifest-authored dropdown needs its choices
        "required": [],
        "optional": ["label", "options"],
    },
    "slider": {
        "width": "full",
        "conditional": None,
        "options": "forbidden",
        "required": ["min", "max", "value"],
        "optional": ["label"],
    },
    "segmented": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "required": [],
        "optional": ["label", "icons"],
    },
    "preset-grid": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "required": [],
        "optional": ["label"],
    },
}

# Derived sets — the validator imports these instead of re-listing archetype names.
ALL_ARCHETYPES = set(ARCHETYPES)
SELECTOR_ARCHETYPES = {k for k, v in ARCHETYPES.items() if v["conditional"] == "reveals"}
