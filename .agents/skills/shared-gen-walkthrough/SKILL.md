---
name: shared-gen-walkthrough
description: Generate a multi-step walkthrough / onboarding page (Step 1/2/3 … with Next/Back) from a model's walkthrough.manifest. CROSS-CATEGORY — use for any device category; never hand-write a walkthrough, never make a per-walkthrough skill.
argument-hint: <CATEGORY> <MODEL>
---

# shared-gen-walkthrough

A **cross-category** framework for a multi-step guided flow (onboarding / setup / feature tour). It is
NOT namespaced to a device category — the same template renders a walkthrough for a headset, a mouse,
or any future category. The walkthrough's content (its steps) is **content**, so it lives in a
manifest, not in a skill name; there is intentionally NO per-walkthrough skill.

Invoke: `@skills:shared-gen-walkthrough <CATEGORY> <MODEL>`
(e.g. `@skills:shared-gen-walkthrough headset HS1234`).

## Frame and masthead

The walkthrough page uses the **same outer frame and masthead** as the home and sub-pages — the
`.frame` (1378×735, flex-column) and `.masthead` (64px, 3 SVG window-control buttons, static) are
inherited verbatim from the category stylesheet. The masthead is copied verbatim from
`headset-gen-subpage/templates/subpage-frame.html` into `walkthrough-frame.html`; no device data is
shown (no device name, model, or firmware).

The only structural difference from home/subpage is the content area below the masthead.

## Three stylesheets

The rendered `walkthrough.html` links THREE stylesheets in this order:

1. `../../../shared/tokens.css` — design tokens (colors, typography, radii, shadows).
2. `../../<category>.css` — the category shell: `.frame`, `.masthead`, `.control-button` etc.
   (e.g. `../../headset.css` for a headset walkthrough). The renderer substitutes the actual
   `<category>` argument, so the skill stays cross-category.
3. `../../../shared/walkthrough.css` — content-area layout + stepper styles ONLY. No frame/masthead
   styles here; those come from the category stylesheet for free.

The template `walkthrough-frame.html` uses depth-4 preview paths (e.g. `../../../../headset/headset.css`)
so it renders correctly when previewed in place. `render-walkthrough.py`'s `rewrite_css_paths(markup,
category)` rewrites all three to output depth (depth 3), substituting the actual category name into
the category stylesheet link.

## Content area (below the masthead)

Below the masthead, `<main class="wt-content-area">` fills the remaining frame height (`flex: 1`).
It has padding: 0 top (flush against masthead), 64px left, 64px right, 64px bottom.

Inside it a **two-column grid** (`1fr 1fr`, 32px gap) holds:
- **Left column** (`.wt-col-text`) — follows the Figma walkthrough frame (node 67:1274), top to bottom:
  a **progress bar** (`.wt-progress`, 281×6; the brand fill width is baked per step = index/count),
  then a 64px gap, then the **text block** (`.wt-eyebrow` fixed "FEATURE HIGHLIGHT" 20px label +
  `.wt-title` Roboto-Light 56px + `.wt-text` body 16px), and the **buttons pinned to the bottom**
  (position-derived: `Back` icon-only on steps 2+, `Next` primary + arrow, `Skip` tertiary; the last
  step is `Back` + the final CTA with no arrow).
- **Right column** (`.wt-col-image`): the step image in `.wt-media`. When a step has no `image` key
  the renderer drops the `<img>` but KEEPS the `.wt-media` box as a uniform **light-gray placeholder**
  (`--color-surface-muted`) — the same empty-state convention as the rest of the system.

The Next/CTA arrow is COPIED from `dds2/dds2_arrow-right.svg` (recolored to `currentColor`). There are
no progress dots — the progress bar conveys position.

## Deterministic executor (REQUIRED — the page is not done until this runs)

The canonical, reproducible path is the render script:
`python3 .agents/skills/shared-gen-walkthrough/render-walkthrough.py <CATEGORY> <MODEL>` writes
`<CATEGORY>/models/<MODEL>/walkthrough.html` (add a trailing `-` to print to stdout instead). The
Procedure below is the human-readable SPEC the script implements and must stay in lock-step with it.

**Authoring the `.manifest` is NOT the deliverable — the rendered `walkthrough.html` on disk is.**
Writing the manifest is the halfway point: you MUST then RUN the executor so the `.html` exists in the
model folder. Do NOT stop after the manifest and wait to be asked for the HTML. (Definition of Done:
see Hard rules.)

## Inputs

- `$1` — device category (`headset`, …). `$2` — model folder under `<category>/models/`.
- **Walkthrough manifest**: `<category>/models/<MODEL>/walkthrough.manifest`.

## Manifest schema (the generation contract)

```
title: <page + browser-tab title>
cta: <final-step button label>          # optional, default "Get started"
done-link: <href for the final CTA>     # optional, default "index.html" (back to the device home)
steps:                                   # 1–6 steps (MAX_STEPS = 6; see Hard rules)
  - title: <step heading>
    body: <one paragraph of step copy>
    image: <relative image src>          # optional; the media block is dropped if absent
  - title: …
    body: …
```

- `title` + `body` are **required** on every step; `image` is optional. The eyebrow above the title is
  a **fixed** template label ("FEATURE HIGHLIGHT") — not a manifest field; it is the same on every step.
- The step **navigation is derived from position, never authored**:
  - first step → `Next` (primary + arrow) + `Skip` (tertiary → `done-link`)
  - middle step → `Back` (icon-only) + `Next` + `Skip`
  - last step → `Back` + the final CTA (`cta` text, primary, no arrow → `done-link`); no Skip.

  Do not put nav in the manifest. (`cta` defaults to "Get started"; the FIXTURE uses "Finish".)

## Procedure

1. Read `<category>/models/<MODEL>/walkthrough.manifest`; HALT if it is missing, has no `steps[]`, has
   a step missing `title`/`body`, or has more than `MAX_STEPS` steps.
2. **Copy the frame** `templates/walkthrough-frame.html`; the renderer calls `rewrite_css_paths(markup,
   category)` to rewrite all three preview-depth CSS links to output depth, substituting the actual
   category into the category stylesheet link. Do not otherwise edit the frame.
3. Fill the `walkthrough-title` from `title`.
4. Build the stepper into the `data-slot="walkthrough"` region on `<main class="wt-content-area">`:
   - one hidden `<input class="wt-radio">` per step (first `checked`);
   - one **copy** of `templates/step.html` per step (the §9.7.4 copy-not-generate unit), filling
     `{progress}` (= index/count %) / `{title}` / `{body}` (the eyebrow is fixed in the template),
     keeping the `.wt-media` block only if the step has an `image`, and filling the derived `.wt-nav`
     (Back / Next / Skip / final CTA by position — see the schema's nav rule).
5. Strip `data-slot` / `data-property` / `data-instruction` and template comments from the output.

The result is a **JS-free** stepper: hidden radios + CSS `:checked` reveal one step at a time (the
D11/D12 "runtime reveal inside one panel" override). No script is added.

## Hard rules

- **THREE stylesheets in order**: `shared/tokens.css` → `<category>/<category>.css` →
  `shared/walkthrough.css`. Never an inline `<style>`. The category stylesheet provides the frame and
  masthead; `shared/walkthrough.css` provides content-area + stepper ONLY.
- **Markup is COPIED, never written from a description.** The step shell comes from
  `templates/step.html`, copied once per `steps[]` entry — never hand-rolled.
- **Navigation is derived, not authored.** Back/Next/CTA come from each step's position; never place
  them in the manifest or hand-edit them into the HTML.
- **Steps cap at `MAX_STEPS` (6).** `shared/walkthrough.css` maps step radios to panels positionally
  (`:nth-of-type` / `:nth-child`) up to 6 — the renderer HALTs past that. Raising the cap = adding the
  positional rules in the CSS **and** bumping `MAX_STEPS`, in lock-step.
- **Reproducible from the manifest (no off-pipeline hand-patching).** Re-running the renderer on the
  manifest must produce the exact same HTML; if the page needs something the manifest can't express,
  fix the schema/frame/step snippet/CSS — never the generated HTML.
- **Definition of Done = rendered HTML on disk, not the manifest.** The task is complete ONLY when
  `render-walkthrough.py <CATEGORY> <MODEL>` has been RUN and
  `<CATEGORY>/models/<MODEL>/walkthrough.html` exists. Stopping after the manifest — leaving the render
  "for when asked" — is an INCOMPLETE task, not a handoff. Run the executor as the final step.

## Self-check

- **Did you RUN the renderer?** `<category>/models/<MODEL>/walkthrough.html` must exist on disk now — not just the manifest. If you only wrote the manifest, the task is NOT done.
- Every step copied from `templates/step.html` (no hand-written step markup)?
- Output links `shared/tokens.css` + `../../<category>.css` + `shared/walkthrough.css` — in that order?
- Masthead is the static 3-button window controls, copied verbatim — no device data?
- Nav derived correctly (step 1 = Next only; last = Back + CTA to `done-link`); ≤ 6 steps?
- `data-slot` / `data-property` / `data-instruction` stripped; would a re-render reproduce this exact HTML?

## Tree

```
.agents/skills/shared-gen-walkthrough/
  SKILL.md                       # this file
  render-walkthrough.py          # deterministic renderer (self-contained, no cross-skill imports)
  templates/
    walkthrough-frame.html       # page shell — .frame + .masthead (verbatim from subpage) + .wt-content-area slot
    step.html                    # the repeatable step unit (copy-not-generate); 2-col text/image
shared/walkthrough.css           # content-area + stepper styles only (frame/masthead from category CSS)
<category>/models/<MODEL>/walkthrough.manifest   # per-model instance (input)
<category>/models/<MODEL>/walkthrough.html       # generated output
```
