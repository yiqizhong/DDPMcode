---
name: headset-gen-homepage
description: Generate a headset model's home page (index.html) from its home.manifest. Use whenever building a headset model home page — never hand-write index.html.
argument-hint: <MODEL>
---

# headset-gen-homepage

Build the home page for headset model **`$1`** by copying this skill's frame and filling its
slots from the model manifest. **Copy + fill — never generate the frame from scratch.**

Invoke: `@skills:headset-gen-homepage <MODEL>` (e.g. `@skills:headset-gen-homepage HS1234`).

## Inputs

- `$1` — the model folder name under `headset/models/`.
- Manifest: `headset/models/$1/home.manifest` — identity (marketing name, model number,
  firmware, PPID), device image, `connectionType` (+ what its block contains), and
  `features[]` (each `label` + `icon` + `link`).

## Procedure

1. **Copy the frame** to the model folder, rewriting the two stylesheet links from
   preview-relative (4 levels up, so the template renders in place) to output-relative. Run
   from the repo root:
   ```
   sed -e 's|href="../../../../shared/tokens.css"|href="../../../shared/tokens.css"|' \
       -e 's|href="../../../../headset/headset.css"|href="../../headset.css"|' \
       .agents/skills/headset-gen-homepage/templates/home-frame.html \
       > headset/models/$1/index.html
   ```
   Do not otherwise rewrite the frame.
2. Read `headset/models/$1/home.manifest`.
3. Fill the single-value `data-property` slots from the manifest:
   `device-marketing-name`, `device-model-number`, `firmware-version`, `device-ppid`, and the
   `device-image` container (`<img src="images/...">`). Omit the PPID line if absent.
4. **Control Zone** (`data-slot="control-zone"`): do NOT write a block from the keyword.
   a. **Copy** `.agents/skills/headset-gen-homepage/templates/connection/<connectionType>.html`
      verbatim into the `.control-zone`, then fill its value slots (`data-property="battery-level"`
      ← `manifest.battery`; if absent, leave `—%` and flag it). **If that file does not exist, STOP
      and ask the user — never invent a connection block or a new mode.**
   b. **Unpair is separate.** If the copied snippet marks the mode as paired (e.g. bluetooth), also
      **copy** `.agents/skills/headset-gen-homepage/templates/connection/unpair.html` right after the
      tag — **home page only**. Wired/unpaired modes get no Unpair. Sub-pages never include Unpair
      (omit it, never `display`-hide). Emit only the one needed mode.
5. **Feature Zone** (`data-slot="feature-zone"`): do NOT write button markup. For each
   `features[]` item, **copy**
   `.agents/skills/headset-gen-homepage/templates/feature-button.html` into the `.feature-zone`,
   fill `{label}`/`{link}`, and for the icon **insert**
   `.agents/skills/headset-gen-homepage/templates/icons/<feature.icon>.svg` into the `.feature-icon`
   div. If the item has no icon, delete the `.feature-icon` div; **if `<feature.icon>.svg` does not
   exist, STOP and ask — never draw an icon.** N items → N buttons. Generate each link target via
   `@skills:headset-gen-subpage $1 <subpage>`.
6. Strip `data-slot`/`data-instruction` from the output; keep the frame's classes/markup intact.

## Hard rules

- **Connection blocks are COPIED from
  `.agents/skills/headset-gen-homepage/templates/connection/<connectionType>.html`, never
  written from the connectionType keyword.** Unknown connectionType → halt and ask, never
  fabricate a block or a new mode. This is what stops a weak model from hallucinating a block.
- **Feature buttons are COPIED from
  `.agents/skills/headset-gen-homepage/templates/feature-button.html` (one per `features[]`
  item, values filled), never written from an inline pattern.**
- **Unpair is a standalone snippet**
  (`.agents/skills/headset-gen-homepage/templates/connection/unpair.html`), copied on the home page
  for paired modes only — never embedded inside the connection tag, never on sub-pages, never hidden.
- **Feature icons are COPIED from the registry**
  `.agents/skills/headset-gen-homepage/templates/icons/<id>.svg` (id = `feature.icon`); unknown id →
  halt, no icon → text-only. Never draw an icon.
- No `display`-hidden or pre-embedded-and-hidden variants in the output.
- No inline `<style>`; the frame links `shared/tokens.css` + `headset.css` only.
- After the copy, the output's CSS links must be `../../../shared/tokens.css` and
  `../../headset.css` (the `sed` in step 1 handles this). Never leave the 4-up preview paths.
- Invent nothing — every value comes from the manifest.

## Self-check

- All header slots filled (or PPID legitimately omitted)?
- Exactly one connection block, matching `connectionType`?
- Every feature button a real `<a href>` whose target sub-page exists?
- Zero `display`-hidden variants, zero inline `<style>`?
