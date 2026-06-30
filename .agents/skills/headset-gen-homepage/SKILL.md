---
name: headset-gen-homepage
description: Generate a headset model's home page (index.html) from its home.manifest. Use whenever building a headset model home page — never hand-write index.html.
argument-hint: <MODEL>
---

# headset-gen-homepage

Build the home page for headset model **`$1`** by copying this skill's frame and filling its
slots from the model manifest. **Copy + fill — never generate the frame from scratch.**

Invoke: `@skills:headset-gen-homepage <MODEL>` (e.g. `@skills:headset-gen-homepage HS1234`).

## Deterministic executor (REQUIRED — the page is not done until this runs)

The canonical, reproducible generation path is the render scripts:
`python3 .agents/skills/headset-gen-subpage/render-model.py <MODEL>` builds the whole model, or
`python3 .agents/skills/headset-gen-subpage/render-home.py <MODEL>` renders this single home page.
The Procedure below is the human-readable SPEC those scripts implement and must stay in lock-step
with them.

**Authoring the `.manifest` is NOT the deliverable — the rendered `index.html` on disk is.** Writing
the manifest is the halfway point: you MUST then RUN the executor so that
`headset/models/<MODEL>/index.html` (and every feature sub-page, per step 7) actually exists in the
model folder, then confirm with `verify-model.py`. Do NOT stop after the manifest and wait to be asked
for the HTML — running the render is part of THIS task, not an optional follow-up.

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
       -e 's|href="../../../../shared/shell.css"|href="../../../shared/shell.css"|' \
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
   a. **Copy** `.agents/skills/headset-shared/connection/<connectionType>.html`
      verbatim into the `.control-zone`, then fill its value slots (`data-property="battery-level"`
      ← `manifest.battery`; if absent, leave `—%` and flag it). **If that file does not exist, STOP
      and ask the user — never invent a connection block or a new mode.**
   b. **Unpair is separate.** If the copied snippet marks the mode as paired (e.g. bluetooth), also
      **copy** `.agents/skills/headset-shared/connection/unpair.html` right after the
      tag — **home page only**. Wired/unpaired modes get no Unpair. Sub-pages never include Unpair
      (omit it, never `display`-hide). Emit only the one needed mode.
5. **Feature Zone** (`data-slot="feature-zone"`): do NOT write button markup. For each
   `features[]` item, **copy**
   `.agents/skills/headset-shared/feature-button.html` into the `.feature-zone`,
   fill `{label}`/`{link}`, and for the icon **insert**
   `.agents/skills/headset-shared/icons/<feature.icon>.svg` into the `.feature-icon`
   div. If the item has no icon, delete the `.feature-icon` div; **if `<feature.icon>.svg` does not
   exist, STOP and ask — never draw an icon.** N items → N buttons.
6. Strip `data-slot`/`data-instruction`/`data-property` from the output (no template markers in
   production — this also removes the device-image placeholder gray); keep classes/markup intact.
7. **Build every feature's target page — no dangling routes.** A `features[]` entry is a build
   obligation, not just a button. For **each** feature, generate its `link` target sub-page via
   `@skills:headset-gen-subpage $1 <subpage>`. The home page is **NOT done** until every feature
   button navigates to a sub-page that actually exists; a button whose target was not built (404 /
   dangling route) is a **failure, not a TODO**. Declaring `features[]` = building their pages.

## Hard rules

- **Connection blocks are COPIED from
  `.agents/skills/headset-shared/connection/<connectionType>.html`, never
  written from the connectionType keyword.** Unknown connectionType → halt and ask, never
  fabricate a block or a new mode. This is what stops a weak model from hallucinating a block.
- **Feature buttons are COPIED from
  `.agents/skills/headset-shared/feature-button.html` (one per `features[]`
  item, values filled), never written from an inline pattern.**
- **Every `features[]` entry obligates a built, routed sub-page.** Generate each feature's `link`
  target via `@skills:headset-gen-subpage` (step 7); a feature button whose target page does not
  exist (dangling route / 404) is a violation. Declaring features = building their pages.
- **Unpair is a standalone snippet**
  (`.agents/skills/headset-shared/connection/unpair.html`), copied on the home page
  for paired modes only — never embedded inside the connection tag, never on sub-pages, never hidden.
- **Feature icons are COPIED from the registry**
  `.agents/skills/headset-shared/icons/<id>.svg` (id = `feature.icon`); unknown id →
  halt, no icon → text-only. Never draw an icon.
- No `display`-hidden or pre-embedded-and-hidden variants in the output.
- No inline `<style>`; the frame links `shared/tokens.css` + `shared/shell.css` + `headset.css` only.
- After the copy, the output's CSS links must be `../../../shared/tokens.css`,
  `../../../shared/shell.css` and `../../headset.css` (the `sed` in step 1 handles this).
  Never leave the 4-up preview paths.
- Invent nothing — every value comes from the manifest.
- **Definition of Done = rendered HTML on disk, not the manifest.** The task is complete ONLY when
  `render-model.py <MODEL>` (or `render-home.py`) has been RUN, `headset/models/<MODEL>/index.html`
  plus every feature sub-page exist, and `verify-model.py` passes. Stopping after the manifest —
  leaving the render "for when asked" — is an INCOMPLETE task. Run the executor as the final step.

## Self-check

- All header slots filled (or PPID legitimately omitted)?
- Exactly one connection block, matching `connectionType`?
- Every feature button a real `<a href>` whose target sub-page was **actually built this run** (step 7), not left dangling?
- Zero `display`-hidden variants, zero inline `<style>`?
- **Did you actually RUN the renderer?** `headset/models/$1/index.html` must exist on disk now — not just the manifest. If you only wrote the manifest, the task is NOT done: run `render-model.py $1`.
- After generation, run `python3 .agents/skills/headset-gen-subpage/verify-model.py $1`; non-zero means output drifted from the manifest (hand-edited or stale) — regenerate via `render-model.py`, never hand-edit.
