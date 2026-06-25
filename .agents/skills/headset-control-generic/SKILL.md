---
name: headset-control-generic
description: Render a sub-page control that has no snippet in the controls registry yet, built from the design tokens. Use as the LAST-RESORT fallback for any unknown/new control — don't hand-roll controls.
argument-hint: <control-id>
---

# headset-control-generic

The last-resort generator for controls that do not yet have a snippet in the registry
(`headset-gen-subpage/templates/controls/<id>.html`). It is not tied to any specific control; it
only defines HOW to build a compliant control from the design system, so an unfamiliar control
still renders consistently.

Invoke: `@skills:headset-control-generic <control-id>` (called by `headset-gen-subpage` only when
a control has no snippet in the registry).

> **Growth rule (methodology §9.4):** known, repeated controls graduate into a snippet
> `headset-gen-subpage/templates/controls/<id>.html` (copied, not generated). Until a control has
> a snippet, it renders through here. Do not pre-create control snippets speculatively — let them
> grow from real manifests/designs.

## Inputs

- `$1` — the control id. Plus that control's `controls[]` entry from the sub-page manifest:
  its label and parameters (e.g. min/max/step/options/default). Use ONLY what the manifest gives.

## How to build a compliant control

1. Use the design tokens (`shared/tokens.css`) and `headset.css` classes — never hardcode
   colors, fonts, radii, or shadows. Match the existing brand/typography/spacing.
2. Structure: a labeled row — control label (from the manifest) + the input affordance
   (slider / toggle / dropdown / stepper as the parameters imply).
3. Render inside the sub-page's `data-slot="controls"` region; no inline `<style>`.
4. Render strictly what the manifest specifies. If a parameter is missing, leave it out — do
   NOT invent ranges, options, or defaults.

## Hard rules

- Invent nothing beyond what the manifest provides for this control.
- No inline `<style>`; reuse tokens + `headset.css`. If a needed reusable style is missing, add
  it to `headset.css`, not inline.

## Self-check

- Are all values (label, range, options, default) taken from the manifest, nothing invented?
- Tokens/`headset.css` used (no hardcoded colors/inline styles)?
- Rendered inside the sub-page controls slot?
