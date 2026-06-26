# Sub-control snippets (the reusable atoms inside a function card)

One snippet per **sub-control archetype** — the small interactive pieces that stack inside a
function card's body (`.function-content`). A function card is assembled as: **card shell** (the
title + ⓘ header over a body) **+ a vertical list of these sub-controls**.

These are **copied, never generated from a description** (the §9.7.4 "copy, don't create" rule) —
the same mechanism as `connection/*.html`, `feature-button.html`, and `icons/*.svg`. Their styling
lives in `headset/headset.css`; the snippet is just the markup + value slots.

## The atoms (grow on demand — §9.4)

| Snippet | Archetype | Fills | headset.css classes |
|---|---|---|---|
| `toggle-row.html` | the standard labeled row: **name left + native switch right** | `{label}`, `{id}-state` | `.function-header`, `.switch*` |
| `slider.html` | min/max labels + native range + value bubble | `{min}/{max}/{val}`, `{label}` | `.slider-row`, `.slider-input`, `.slider-value` |
| `segmented.html` | row of 2–4 mutually-exclusive option buttons (radio semantics, zero JS) | `{id}`, `{label}`, `{labelN}`, `{valueN}` | `.segmented-control`, `.segment`, `.segment-input`, `.segment-icon`, `.segment-label` |
| `info-tooltip.html` | OPTIONAL ⓘ + hover tooltip (shared with the homepage firmware ⓘ) | `{info-text}` | `.info-tooltip*` |

> The archetype list is **open** (docs/function-card-architecture.md §9.3): add a new
> `<archetype>.html` here when a real design needs one (e.g. `dropdown.html`,
> `preset-grid.html`). The control-selection rules (which archetype for which data shape) are in
> docs §7. Unknown archetypes → the Layer-2 `headset-function` builder, then promote to a snippet here.

## Segmented control — icon usage rule

`segmented.html` has two forms: **with icons** and **without icons** (default). The choice is not
based on the function's name or keywords; it is based on what the control *does to the user's
listening experience*:

**Use icons when** the segmented control lets the user choose between modes that change how the
device mediates the acoustic environment around them — i.e. the options govern whether and how
external sound reaches the listener's ears (examples: active noise cancellation, transparency /
hear-through / pass-through, ambient mode, environment modes, wind reduction levels expressed as
modes). The semantic test: *"Do these options determine which sounds from the outside world the
user hears, and how?"* → yes → icons required.

**Use default (no icons) for everything else** — EQ presets, channel mode, mic pickup pattern,
LED brightness levels, button assignment choices, language selection, and so on.

The icon rule is **semantic, not lexical**: the function card's title or ID is irrelevant. A card
titled "Sound Environment" or "Hear-through Mode" triggers the rule just as much as one titled
"Noise Control"; a card titled "Noise Gate" (a mic threshold control, not an acoustic-environment
choice) does not.

## How an atom is used

- **Building a function snapshot** (`headset-gen-subpage/templates/functions/<id>.html`): assemble the
  card by copying the card shell + one of these per sub-control, filling the slots. The result is a
  frozen snapshot (a known Layer-1 function), copied verbatim at generation time.
- **`info-tooltip.html` is optional**: copy it into a row's `.function-icons` only when that control
  has info text; otherwise delete `.function-icons`. Whenever present, the hover tooltip is its
  mandatory bound behavior.

## Sub-function dependency (toggle OFF → grey out its sub-functions)

A function's toggle can own dependent sub-controls. Express it by structure (it is data):

```html
<div class="subfn-group">
  <!-- the parent toggle row; its switch <input> carries the .subfn-toggle class -->
  <div class="function-header"> … <input class="switch-input subfn-toggle" …> … </div>
  <!-- its dependent sub-controls carry .subfn-child -->
  <div class="slider-row subfn-child"> … </div>
</div>
```

When the `.subfn-toggle` is OFF, every `.subfn-child` in the group greys out + goes
non-interactive — pure CSS `:has()`, zero JS (see `headset.css`).

## Reference assembly

`headset-gen-subpage/templates/functions/collaboration.html` is a worked example: card shell +
two `toggle-row` (Mic Noise Cancellation, Sidetone) + one `slider`, with the Sidetone row + slider
wrapped in a `.subfn-group` (Sidetone OFF greys the slider), and an `info-tooltip` on each row.
