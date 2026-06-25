---
name: headset-function
description: Generate a headset sub-page function (a setting/feature module like EQ, sidetone, mic gain) into the sub-page's function slot, by COPYING the function template and filling manifest values. Use for every sub-page function that has no dedicated snapshot yet — never hand-roll function markup from a description.
argument-hint: <function-id>
---

# headset-function

Generates one **function** — a self-contained setting/feature module that lives in a
headset sub-page's function area (e.g. EQ, sidetone, mic gain, sleep timer). It is not tied to
any specific function; it owns the **canonical function template** and only defines HOW to turn a
manifest function entry into a compliant module, so an unfamiliar function still renders
consistently.

Invoke: `@skills:headset-function <function-id>` — called by `headset-gen-subpage` for each
`functions[]` entry that has no dedicated snapshot in the registry.

## The template (copy, don't generate)

The function module shape is pre-written, NOT invented per call:

```
headset-function/
├── SKILL.md
└── templates/
    └── function-frame.html     ← the canonical function module shell — COPY this
```

**COPY `templates/function-frame.html`** into the sub-page's `data-slot="functions"` region and
fill its `data-property` value slots from the function's manifest params. Do not write the module
markup from the function's name — copy the shell, fill the values, build only the affordance from
the params.

> **Growth rule (methodology §9.4):** a function that recurs and needs a bespoke design graduates
> into a snapshot `headset-gen-subpage/templates/functions/<id>.html` (copied verbatim by
> `headset-gen-subpage`, never routed through here). Until a function has a snapshot, it renders
> through this template. There are 5–8 functions expected over time — do NOT pre-create their
> snapshots speculatively; let each grow from a real manifest/design.

## Inputs

- `$1` — the function id. Plus that function's `functions[]` entry from the sub-page manifest:
  its `label`, optional `description`, and affordance params (e.g. type, min/max/step, options,
  default). Use ONLY what the manifest gives.

## Procedure

1. **Copy** `templates/function-frame.html` into the sub-page's `data-slot="functions"` region —
   one copy per function. Never write the module shell from scratch.
2. Fill `data-property="function-label"` from the manifest `label`; fill
   `data-property="function-description"` from `description` (omit that element if absent).
3. Build the affordance inside `.function-control` from the function's params — a toggle / slider /
   dropdown / stepper as the params imply — using `shared/tokens.css` + `headset.css` classes only.
   Render strictly what the manifest specifies; if a param is missing, leave it out.
4. Strip `data-slot`/`data-instruction`/`data-property` markers on output (production pages carry
   no template markers — same rule as the gen skills).

## Hard rules

- **COPY the template — never generate the module shell from the function name.** Only the
  affordance inside `.function-control` is built from params, and only from manifest values.
- Invent nothing beyond what the manifest provides (no ranges, options, or defaults).
- No inline `<style>`; reuse tokens + `headset.css`. If a needed reusable style is missing, add it
  to `headset.css`, not inline.
- If a function has a dedicated snapshot `headset-gen-subpage/templates/functions/<id>.html`,
  `headset-gen-subpage` copies THAT directly — this skill is only the no-snapshot path.

## Self-check

- Was `templates/function-frame.html` COPIED (not hand-written), one per function?
- `function-label` / `function-description` and all affordance values taken from the manifest,
  nothing invented?
- Tokens / `headset.css` used (no hardcoded colors / inline styles)?
- Rendered inside the sub-page `data-slot="functions"` region; markers stripped on output?
