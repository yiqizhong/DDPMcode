"""Component archetype catalog — the SINGLE SOURCE OF TRUTH for the contract that
`validate-manifest.py` enforces (the machine-readable analog of a json-render `defineCatalog`).

Adding a new archetype = add a block here AND add its snippet under
`headset-shared/components/<archetype>.html`. The validator derives EVERY archetype rule
from this dict — it hardcodes no archetype names, option caps, or width sets of its own.

Per-archetype keys
──────────────────
  width        "compact" -> renders as a row (label left + widget right); `label` is required
                            unless the control is the card's SOLE top-level control and the
                            card title covers it.
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
  min_options  / max_options — the inclusive option-count window this archetype accepts (None =
               unbounded). The validator derives the count gate from these; they are the
               mechanical half of select-family selection (segmented 2-3, preset-grid 4-6,
               dropdown 2-..). A <=DROPDOWN_SMALL_MAX dropdown additionally needs a
               `dropdown-reason` (see that key) so it can't silently stand in for a selector.
  required     extra props that MUST be present (checked by KEY PRESENCE, so a numeric/bool
               prop may legitimately be 0 / false). `label` is intentionally NOT listed here —
               it is enforced positionally from `width` (see above).
  optional     props allowed but not required (whitelist / documentation).
  when         one-line data-shape trigger ("use this archetype when …"). Select-family choice is
               now MECHANICAL: count windows (min_options/max_options) plus the dropdown-reason
               gate pin segmented-vs-preset-grid-vs-dropdown (see docs/component-selection-rule.md).
               Only the acoustic-environment ICON rule stays genuinely semantic, in prose —
               components/README.md + headset/AGENTS.md.

Run `python3 archetypes.py` to print the authoritative contract table (the json-render
`catalog.prompt()` analog) instead of hand-copying a parallel table into the docs.
"""

# headset.css positional :has() maps .segment / .segment-panel nth-child up to 6.
MAX_OPTIONS = 6

# A dropdown with <= this many options must declare a `dropdown-reason`; otherwise it should be a
# visible selector (2-3 -> segmented, 4-6 -> preset-grid). This is the rule that pins
# segmented-vs-dropdown so the same input can't flap to a different archetype across runs.
DROPDOWN_SMALL_MAX = MAX_OPTIONS
DROPDOWN_REASONS = frozenset(("ordered-value", "long-labels", "inline-slot"))

# One-line corrective shown wherever a select-family count rule is violated.
COUNT_RULE_HINT = (
    "select-family count rule: 2-3 -> segmented (cap 3); 4-6 -> preset-grid; >6 -> dropdown; "
    "a <=%d-option dropdown needs a `dropdown-reason` (%s)"
    % (DROPDOWN_SMALL_MAX, ", ".join(sorted(DROPDOWN_REASONS)))
)

ARCHETYPES = {
    "toggle": {
        "width": "compact",
        "conditional": "dependents",
        "options": "forbidden",
        "required": [],
        "optional": ["label", "info", "value"],
        "when": "Boolean on/off (2-state)",
    },
    "dropdown": {
        "width": "compact",
        "conditional": None,
        "options": "required",   # a manifest-authored dropdown needs its choices
        "min_options": 2,
        "max_options": None,     # uncapped (its own <details> overlay, no positional CSS limit)
        "required": [],
        "optional": ["label", "options", "dropdown-reason"],
        "when": "Pick 1 of N — >6 options, or a declared exception (ordered value / long labels / inline slot)",
    },
    "slider": {
        "width": "full",
        "conditional": None,
        "options": "forbidden",
        "required": ["min", "max", "value"],
        "optional": ["label", "stops"],
        "when": "A value on an ordered range / stepped scale",
    },
    "segmented": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "min_options": 2,
        "max_options": 3,        # hard cap: 3 segments per row; 4+ -> preset-grid
        "required": [],
        "optional": ["label", "icons"],
        "when": "Pick 1 of N — 2-3 options visible in a row (hard cap 3), incl. icon modes",
    },
    "preset-grid": {
        "width": "full",
        "conditional": "reveals",
        "options": "required",
        "min_options": 4,
        "max_options": MAX_OPTIONS,   # 4-6 named presets / profiles
        "required": [],
        "optional": ["label"],
        "when": "Pick 1 preset / profile — 4-6 named cards in a 2-col grid",
    },
}

# Derived sets — the validator imports these instead of re-listing archetype names.
ALL_ARCHETYPES = set(ARCHETYPES)
SELECTOR_ARCHETYPES = {k for k, v in ARCHETYPES.items() if v["conditional"] == "reveals"}

OPTION_KEYS = frozenset(("label", "value", "selected"))
FUNCTION_SLOT_KEYS = frozenset(("function",))


def component_allowed_keys(name):
    spec = ARCHETYPES[name]
    keys = {"archetype"}
    keys.update(spec["required"])
    keys.update(spec["optional"])
    if spec["options"] != "forbidden":
        keys.add("options")
    if spec["conditional"]:
        keys.add(spec["conditional"])
    return frozenset(keys)


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
    label = "label\\*" if spec["width"] == "compact" else "label\\*"
    return ", ".join([label] + list(spec["required"]))


def render_table():
    lines = [
        "# Component archetype contract — DERIVED from archetypes.py",
        "",
        "> Authoritative + always in sync with the `validate-manifest.py` gate. Do NOT hand-copy a",
        "> parallel table into the docs; regenerate with `python3 archetypes.py`. Select-family choice",
        "> is mechanical (count windows + the dropdown-reason gate; docs/component-selection-rule.md);",
        "> only the acoustic-environment icon rule stays in prose — components/README.md + AGENTS.md.",
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
        "\\* A compact or full-width control may omit `label` ONLY when it is the card's sole top-level",
        "  control (then the card title covers it and it renders headingless); anywhere else a missing",
        "  label is dropped data (the BUG-002 class).",
        "",
        "Select-family count windows: `segmented` 2-3 (hard cap 3), `preset-grid` 4-6, `dropdown` 2+.",
        "A `dropdown` with <=%d options must carry a `dropdown-reason` (%s); otherwise use the"
        % (DROPDOWN_SMALL_MAX, ", ".join(sorted(DROPDOWN_REASONS))),
        "visible selector for that count. See docs/component-selection-rule.md.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_table())
