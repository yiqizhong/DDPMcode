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
| `control-row.html` | the standard labeled row: **name left + native switch right** | `{label}`, `{id}-state` | `.function-header`, `.switch*` |
| `slider.html` | min/max labels + native range + value bubble | `{min}/{max}/{val}`, `{label}` | `.slider-row`, `.slider-input`, `.slider-value` |
| `segmented.html` | row of 2–4 mutually-exclusive option buttons (radio semantics, zero JS) | `{id}`, `{label}`, `{labelN}`, `{valueN}` | `.segmented-control`, `.segment`, `.segment-input`, `.segment-icon`, `.segment-label` |
| `preset-grid.html` | 2-column grid of 4–6 option buttons; last item can span full width via `.segment--span` | same as segmented + `{id}-preset` | `.preset-grid`, `.segment--span` + all `.segment*` |
| `info-tooltip.html` | OPTIONAL ⓘ + hover tooltip (shared with the homepage firmware ⓘ) | `{info-text}` | `.info-tooltip*` |

> The archetype list is **open** (docs/function-card-architecture.md §9.3): add a new
> `<archetype>.html` here when a real design needs one (e.g. `dropdown.html`,
> `preset-grid.html`). The control-selection rules (which archetype for which data shape) are in
> docs §7. Unknown archetypes → the Layer-2 `headset-function` builder, then promote to a snippet here.

## Segmented control vs Preset grid — when to use which

Both archetypes are mutually-exclusive selectors with the same radio semantics, selected state,
and optional conditional-panel system. The only difference is **layout** and **use context**:

| | `segmented.html` | `preset-grid.html` |
|---|---|---|
| Layout | Single horizontal row (`flex row`) | 2-column grid (`CSS grid`) |
| Item count | 2–4 | 4–6 (5+ always grid; 4 depends on semantics) |
| Item width | Equal, stretch to fill | Equal, 50% each; last may span full row |
| Icons | Required for acoustic-environment modes (see rule below); optional otherwise | Not used — label-only |
| Height | **56px** default; **80px** when icon present (auto via `:has`) | **56px** always (no icons) |
| Primary use | Mode switching (ANC/Transparency, channel, EQ mode) | Preset/profile selection (EQ presets, sound profiles, multimedia presets) |

**Decision rule — option count alone is not enough; semantics matter:**

| Count | Semantics | Use |
|---|---|---|
| 2–3 | any | segmented row (always) |
| 5–6 | any | preset-grid (always — doesn't fit in a row) |
| 4 | **mode switching** (e.g. ANC / Low / Off / Transparency) | segmented row |
| 4 | **preset / profile** (e.g. Default / Bass Boost / Speech / Treble) | preset-grid |

The key semantic question: *"Are these named configurations the user picks from, or modes the device switches between?"* Presets → grid. Modes → row.

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

**Icon lookup — use the segment-icon registry (never search dds2/ directly):**
When icons are required, copy each icon from `.agents/skills/headset-shared/segment-icons/<value>.svg`
where `<value>` is the option's `value` field from the manifest. The registry README has the full
value → file mapping (including aliases like `transparency` → `hear-through.svg`). If the value has
no file in `segment-icons/` → HALT and ask; never pull from `dds2/` directly or invent an icon.

## How an atom is used

- **Building a function snapshot** (`headset-gen-subpage/templates/functions/<id>.html`): assemble the
  card by copying the card shell + one of these per sub-control, filling the slots. The result is a
  frozen snapshot (a known Layer-1 function), copied verbatim at generation time.
- **`info-tooltip.html` is optional**: copy it into a row's `.function-icons` only when that control
  has info text; otherwise delete `.function-icons`. Whenever present, the hover tooltip is its
  mandatory bound behavior.

## Conditional reveals (selector option → show a panel) — the `reveals` field

Selector atoms (`segmented`, `preset-grid`) carry an optional `.segment-panels` block: the **Nth
panel shows when the Nth option is selected** (positional `:has(...:checked)`, zero JS). In the
manifest this is the selector's **`reveals`** map — key = an option `value`, value = the ordered
slot list that fills that option's panel (a sub-control `{ archetype, … }`, or a nested card
`{ function: <id> }`, recursively). It is the ONLY way to express "select X → show Y".

```
- archetype: preset-grid
  options: [ {label: Default, value: default}, …, {label: Custom, value: custom} ]
  reveals:
    custom:
      - { function: eq-audio }      # Custom selected → the eq-audio card drops into Custom's panel
```

Generation emits one `.segment-panel` per option in order (count = option count; an option with no
`reveals` entry → empty panel). Options + panels combined must stay ≤ 6 (CSS maps `:has()` only to
`nth-child(6)`). A nested `{ function: <id> }` slot is placed **UNWRAPPED** — drop the card's outer
`.function-container` / `.function-top-section` shell and put only its inner `.function-header` +
`.function-content` (plus any trailing `<script>`) into the panel, since the panel already sits inside
the parent card (the full shell would nest a card in a card). A subcontrol must NEVER carry a flat `condition:` field — that pre-schema form does
not exist; conditional content lives under the selector's `reveals`.

**Reveal vs grey-out are different:** `reveals` shows/hides a panel on option select; the
`.subfn-group` below greys a still-visible dependent when a toggle is OFF. Do not conflate them.

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

`headset-gen-subpage/templates/examples/collaboration.html` is a worked example: card shell +
two `control-row` (Mic Noise Cancellation, Sidetone) + one `slider`, with the Sidetone row + slider
wrapped in a `.subfn-group` (Sidetone OFF greys the slider), and an `info-tooltip` on each row.
