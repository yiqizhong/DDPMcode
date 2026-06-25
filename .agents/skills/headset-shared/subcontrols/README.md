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
| `info-tooltip.html` | OPTIONAL ⓘ + hover tooltip (shared with the homepage firmware ⓘ) | `{info-text}` | `.info-tooltip*` |

> The archetype list is **open** (docs/function-card-architecture.md §9.3): add a new
> `<archetype>.html` here when a real design needs one (e.g. `segmented.html`, `dropdown.html`,
> `preset-grid.html`). The control-selection rules (which archetype for which data shape) are in
> docs §7. Unknown archetypes → the Layer-2 `headset-function` builder, then promote to a snippet here.

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
