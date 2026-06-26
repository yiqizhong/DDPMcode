# Debug Handoff: Dell Pro 3 Wireless ANC Headset (WL327) UI Generation

**Date:** 2026-06-26
**Model:** WL327
**Product:** Dell Pro 3 Wireless ANC Headset

> ## ⚠️ CORRECTION (2026-06-26, supersedes the diagnosis below)
> The "Issue Identified" / "Key Learnings" below diagnose the **wrong root cause**. They say
> generation should have keyword-matched "EQ" → `eq-audio`. That contradicts architecture **D8**:
> generation is **id-routed only and never keyword-matches**; the keyword table is an *authoring-time*
> guide. Keyword routing applies when **writing the manifest**, not at generation.
>
> **Actual root cause:** the architecture's conditional-reveal / recursive-slot primitive
> (§6.5 / §8 / §9.1) was implemented only at the CSS+snippet layer — there was **no manifest schema
> and no generation step** for it. So "Custom → show EQ" had no legal manifest expression: the author
> shoehorned it into a `slider` subcontrol with an invented `condition:` field, then hand-patched the
> EQ card into the output. That made the manifest diverge from the HTML and the output
> non-reproducible (re-running gen-subpage would re-emit the slider).
>
> **General fix (D19, 2026-06-26):** defined the `reveals` schema (selector option → ordered slot
> list; a slot is a sub-control or a nested `{ function: <id> }`, recursive), added the gen-subpage /
> headset-function steps that emit it, added generation-time validation (HALT on unknown
> archetype/id, stray `condition:`, mismatched `reveals` key, >6 panels, duplicate option values), and
> a reproducibility rule (no off-pipeline hand-patching). This manifest was rewritten to use `reveals`
> (Custom → `{ function: eq-audio }`; ANC → strength slider) and the duplicate "Speech Boost" preset
> was corrected to "Treble Boost". See `docs/function-card-architecture.md` D19.

## Summary
Successfully generated UI for WL327 headset following DDPM methodology. Created home page and Audio Settings sub-page with three function cards (Noise Control, Collaboration, Multimedia).

## Issue Identified
**Problem:** Did not use the `eq-audio` template for the Multimedia function's EQ control.

**Root Cause:** Made a judgment call based on context interpretation rather than following keyword matching rules. The user's requirement stated "when user choose Custom, then it has EQ, then user can adjust it" which contains "EQ" - this should have matched the `eq-audio` template per the keyword reference table:
- `sound eq` → `eq-audio`
- `eq curve` → `eq-audio`

**Incorrect Interpretation:** Interpreted the requirement as preset selector with simple EQ slider for Custom mode, not a full 5-band equalizer curve.

**Secondary Issue:** When initially copying the EQ template into the Custom segment panel, incorrectly removed the "Audio Equalizer" function header. Assumed only the EQ chart content (subtitle + SVG) should be embedded, not the full template with title.

**Tertiary Issue:** Noise Control segmented control icons were black because I hand-created SVG paths with hardcoded `fill="#0E0E0E"` instead of using `fill="currentColor"` or copying proper icons from the shared icons directory. This prevented CSS from controlling icon color based on selected/unselected state.

## Resolution
Updated the Multimedia function to include the full `eq-audio` template (5-band EQ curve) inside the Custom segment's conditional panel, including the "Audio Equalizer" function header. The EQ chart now appears with its title when users select "Custom" from the preset grid. Changed Noise Control segmented control icons from hardcoded `fill="#0E0E0E"` to `fill="currentColor"` to allow CSS to control color based on selection state.

## Files Generated

### Manifests
- `headset/models/WL327/home.manifest` - Device identity, connection, features
- `headset/models/WL327/audio-settings.manifest` - Sub-page title and function definitions

### Pages
- `headset/models/WL327/index.html` - Home page with device info, Bluetooth connection, Audio Settings button
- `headset/models/WL327/audio-settings.html` - Audio Settings sub-page with three function cards

### Assets
- `headset/models/WL327/images/product.png` - Product image copied from user's Downloads

## Function Cards Implemented

### 1. Noise Control
- ANC/OFF segmented control with icons
- ANC strength slider (1-5) in conditional panel when ANC is selected
- Uses `segmented.html` with conditional panels

### 2. Collaboration
- Mic Noise Canceling toggle
- Uses `control-row.html` (toggle)

### 3. Multimedia
- Preset grid with 5 options: Default, Bass Boost, Speech Boost, Speech Boost, Custom
- Full 5-band EQ curve (Bass, Low-Mid, Mid-range, High-Mid, Treble) in Custom panel
- Uses `preset-grid.html` with conditional panel containing `eq-audio` template

## Key Learnings
1. **Follow keyword matching strictly:** When manifest mentions "EQ", use the `eq-audio` template per the reference table
2. **Conditional panels support nested templates:** Can place full function templates (like EQ chart) inside segment panels
3. **Context interpretation vs keyword matching:** Keyword matching takes precedence over contextual interpretation

## DDPM Methodology Compliance
- Used `headset-gen-homepage` skill for home page generation
- Used `headset-gen-subpage` skill for sub-page generation
- Copied connection snippets from `headset-shared/connection/`
- Copied feature button from `headset-shared/feature-button.html`
- Used subcontrol snippets: `segmented.html`, `slider.html`, `control-row.html`, `preset-grid.html`
- No inline styles, all styling via `shared/tokens.css` and `headset.css`
- Proper manifest-driven generation with data-property filling
