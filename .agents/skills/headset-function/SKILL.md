---
name: headset-function
description: Build a headset sub-page function CARD (a setting/feature like Noise Control, Collaboration, Multimedia) from the card shell + sub-control snippets, filling manifest values. Use for any sub-page function that has no dedicated snapshot yet — never hand-roll function markup from a description.
argument-hint: <function-id>
---

# headset-function

Builds one **function card** — a titled card that lives in a sub-page's Content Area, holding a
vertical list of sub-controls (toggles, sliders, …). It is not tied to any specific function; it
**assembles** a card from pre-written pieces (the card shell + sub-control snippets), so an
unfamiliar function still renders consistently. This is the Layer-2 (no-snapshot) path.

Invoke: `@skills:headset-function <function-id>` — called by `headset-gen-subpage` for each
`functions[]` entry that has no dedicated snapshot in the registry.

## Copy, don't generate — the pieces

```
headset-function/templates/function-frame.html        ← the card SHELL (title + ⓘ slot + body)
headset-shared/subcontrols/<archetype>.html           ← the sub-controls (toggle-row / slider / …)
headset-shared/subcontrols/info-tooltip.html          ← the optional ⓘ + tooltip
```

A card = **shell + a list of sub-controls**. Both come from files — never write the markup from the
function's name. Build only the affordance values from the manifest.

> **Growth rule (methodology §9.4):** a function that recurs and needs a bespoke design graduates
> into a snapshot `headset-gen-subpage/templates/functions/<id>.html` (copied verbatim by
> `headset-gen-subpage`, never routed through here — e.g. `functions/collaboration.html`). Until a
> function has a snapshot, it is assembled here. Do NOT pre-create snapshots speculatively.

## Inputs

- `$1` — the function id. Plus that function's `functions[]` entry from the sub-page manifest: its
  `title`, optional info text, and its **sub-controls** (each: an archetype + that archetype's value
  params — label, on/off state, min/max/value, options, …) and any sub-function dependencies.
  Use ONLY what the manifest gives.

## Procedure

1. **Copy the shell** `templates/function-frame.html` into the sub-page's `data-slot="functions"`
   region — one copy per function. Fill `data-property="function-title"` from the manifest `title`.
2. **Title ⓘ** (`data-slot="function-info"`): if the function has info text, COPY
   `headset-shared/subcontrols/info-tooltip.html` into it and fill `{info-text}`; else delete that div.
3. **Sub-controls** (`data-slot="subcontrols"`): for each sub-control, in order, COPY the matching
   `headset-shared/subcontrols/<archetype>.html` into `.function-content` and fill its value slots
   (and its own ⓘ via `info-tooltip.html`, if it has info). Pick the archetype per the control-selection
   rules in docs/function-card-architecture.md §7. If an archetype has no snippet yet, build it from
   `headset.css` per those rules and §9.4 (then it can be promoted to `subcontrols/<archetype>.html`).
4. **Sub-function dependency**: if a toggle owns dependent sub-controls, wrap them together in a
   `.subfn-group` — the parent switch `<input>` gets the `.subfn-toggle` class, the dependents get
   `.subfn-child` — so they grey out when the toggle is OFF (pure CSS, see `headset.css`).
5. Strip `data-slot`/`data-instruction`/`data-property` markers on output.

## Hard rules

- **COPY the shell + COPY each sub-control snippet — never generate the markup from the function or
  control name.** Only the value slots are filled, and only from manifest values.
- Invent nothing beyond what the manifest provides (no ranges, options, defaults, or controls).
- No inline `<style>`; reuse tokens + `headset.css`. If a needed reusable style is missing, add it to
  `headset.css`, not inline.
- If a function has a dedicated snapshot `functions/<id>.html`, `headset-gen-subpage` copies THAT
  directly — this skill is only the no-snapshot path.

## Self-check

- Card SHELL copied (not hand-written), title filled from the manifest?
- Each sub-control COPIED from `headset-shared/subcontrols/<archetype>.html`, values from the manifest?
- Optional ⓘ present only where there's info text, via `info-tooltip.html`?
- Toggle dependencies wrapped in `.subfn-group` (`.subfn-toggle` / `.subfn-child`)?
- Tokens / `headset.css` used (no hardcoded colors / inline styles); markers stripped on output?
