---
name: headset-gen-subpage
description: Generate any headset sub-page (settings/configuration/feature page) from its manifest. Use for every sub-page — never hand-write sub-page HTML and never make a per-page skill.
argument-hint: <MODEL> <SUBPAGE>
---

# headset-gen-subpage

One framework that holds ANY headset sub-page. It does not know or care what the sub-page is
called or contains — name and controls come from the manifest. There is intentionally NO
per-sub-page skill: the name is content, so it lives in the manifest, not in a skill name.

A sub-page SHARES the model's device identity, connection, and feature list with the home page
(single source of truth: `home.manifest`). Only the title + functions are sub-page-specific.

Invoke: `@skills:headset-gen-subpage <MODEL> <SUBPAGE>`
(e.g. `@skills:headset-gen-subpage HS1234 mic-settings`).

## Inputs

- `$1` — model folder under `headset/models/`. `$2` — sub-page file stem.
- **Sub-page manifest**: `headset/models/$1/$2.manifest` — a `title` and a `functions[]` list
  (each function = an `id` + parameters). `functions[]` may be empty.
- **Model manifest**: `headset/models/$1/home.manifest` — device identity (marketing-name,
  model-number, firmware, PPID), device image, `connectionType` (+ battery), and `features[]`
  (each `label` + `icon` + `link`). The sub-page reuses these so it stays in sync with the home page.

## Manifest schema (the generation contract)

The sub-page manifest is the SOLE source of what renders. Its shape is fixed — generation does not
invent, infer, or keyword-match (D8). Authoring-time choices (which `id`, which `archetype`) are
frozen here by the human / strong model BEFORE generation; see `headset/AGENTS.md` → Control Selection.

```
title: <string>                       # the sub-page / feature title (fills <title> and <h2>)
functions:                            # ordered; the page renders EXACTLY these, in order, none extra
  - id: <function-id>                 # routing key. functions/<id>.html copied whole if it exists.
    title: <string>                   # card title — assembled path only (snapshots carry their own)
    info: <string?>                   # optional ⓘ tooltip text
    subcontrols:                      # assembled path only (no snapshot). Ordered list of sub-control slots.
      - archetype: <enum>             # control-row | slider | segmented | preset-grid | dropdown
        ...<archetype value slots>... # per subcontrols/README.md (label / min,max,value / options / …)
        reveals:                      # OPTIONAL — ONLY on a selector archetype (segmented | preset-grid)
          <option-value>:             # key MUST equal one of THIS selector's option `value`s
            - <slot>                  # ordered list of revealed slots; each slot is either:
            ...                       #   a sub-control:  { archetype: <enum>, ...value slots }
                                      #   a nested card:  { function: <function-id> }
        dependents:                   # OPTIONAL — ONLY on a control-row (toggle)
          - <slot>                    # ordered slot list (same shape as a reveals slot) that GREYS
            ...                       #   OUT (stays visible, non-interactive) when the toggle is OFF
```

**Two distinct conditional mechanisms — do not conflate:**
- **`reveals`** — the conditional-reveal / recursive-slot primitive (architecture §6.5 / §8 / §9.1).
  ONLY on a selector (segmented | preset-grid). A selected option SHOWS/HIDES a `.segment-panel`. A
  revealed slot may itself be a selector with its own `reveals` (recursion). The ONLY legal way to
  express "select X → show Y". It replaces any flat `condition:` field (a subcontrol must NEVER carry
  `condition:`). Do not hand-embed conditional panels.
- **`dependents`** — the toggle grey-out (`.subfn-group`) relationship. ONLY on a `control-row`
  (toggle). Its dependents STAY VISIBLE but grey out + go non-interactive when the toggle is OFF.
  Use this — not `reveals` — whenever a toggle owns dependent controls (e.g. Mic Noise Canceling →
  Canceling Strength).

## Validation (run BEFORE emitting — HALT and ask on any failure)

Generation is deterministic; an out-of-contract manifest is an authoring bug, not something to
paper over. HALT (do not guess, do not hand-fix the HTML) when:

- `archetype` is not in the enum {control-row, slider, segmented, preset-grid, dropdown}.
- A subcontrol carries a legacy `condition:` field → tell the author to migrate it to the selector's `reveals`.
- `reveals` appears on a non-selector archetype (incl. a `control-row`) → HALT; for a toggle's
  grey-out dependents use `dependents` (reveals is selector-only). Or a `reveals` key matches no option `value`.
- `dependents` appears on any archetype other than `control-row` (toggle) → HALT.
- A selector's `options` + revealed `.segment-panel`s combined exceed **6** (headset.css positional
  `:has()` only maps to `nth-child(6)`; a 7th panel never shows).
- Two options in one selector share the same `value` (or the same `label`) — a data error; ask which is correct.
- A `function` slot's id has neither a `functions/<id>.html` snapshot nor enough params to assemble.

## Procedure

1. **Copy the frame** to the model folder, rewriting the two stylesheet links from
   preview-relative to output-relative. Run from the repo root:
   ```
   sed -e 's|href="../../../../shared/tokens.css"|href="../../../shared/tokens.css"|' \
       -e 's|href="../../../../headset/headset.css"|href="../../headset.css"|' \
       .agents/skills/headset-gen-subpage/templates/subpage-frame.html \
       > headset/models/$1/$2.html
   ```
   Do not otherwise rewrite the frame.
2. Read BOTH `headset/models/$1/$2.manifest` (this sub-page) AND `headset/models/$1/home.manifest`
   (the model's device identity / connection / features).
3. **Device identity** (from `home.manifest` — the SAME values as the home page): fill
   `device-marketing-name` (the `<h1>`), `device-model-number`, `firmware-version`, `device-ppid`
   (omit the PPID line if absent), and the `device-image` container (`<img src="images/...">`).
4. **Feature title** (from the sub-page manifest): fill `subpage-title` — both the `<title>` and the
   `.feature-title` `<h2>` — from `title`.
5. **Control Zone** (`data-slot="control-zone"`): **copy**
   `.agents/skills/headset-shared/connection/<home.manifest.connectionType>.html`
   and fill battery from `home.manifest.battery`. **CONNECTION SYNC:** connectionType + battery MUST
   equal the home page (same `home.manifest`). **Sub-pages get NO Unpair** — never copy `unpair.html`.
   Halt if the connection snippet does not exist.
6. **Collapsed feature nav** (`data-slot="feature-nav-collapsed"`): for each `home.manifest.features[]`
   item, **copy** `.agents/skills/headset-shared/feature-button.html` (the SAME file as the home page)
   and **add the `feature-button--collapsed` class** to it. Fill `{label}`/`{link}` and insert
   `.agents/skills/headset-shared/icons/<feature.icon>.svg` into its `.feature-icon`. The label IS
   filled (same as the home page) — it shows icon-only and reveals the label on hover. **ICON SYNC:**
   the same icon as the home page's feature button. Halt on a missing/unknown icon.
7. **Functions** (`data-slot="functions"`): **presence/absence — the page shows EXACTLY the functions
   the manifest lists, in order, no more, no less.** For each `functions[]` item, render it by **one of
   two paths, decided by whether a snapshot exists** (architecture §6.6 / D18):
   - **Snapshot path** — `functions/<function.id>.html` exists → **copy it whole**; it is already a
     complete card. The manifest's per-slot params are a **rare override**: replace a `data-property`
     value only where the manifest provides one; **no params → keep the snapshot unchanged** (do not
     empty it, do not invent).
   - **Assembled path** — no snapshot → `@skills:headset-function <id>`. It copies the card shell
     (`function-frame.html`), fills `title`/`info`, then copies one `headset-shared/subcontrols/<archetype>.html`
     per `subcontrols[]` entry, in order, strictly from manifest params (invent nothing).

   **Conditional reveals (the recursive slot):** when an assembled selector subcontrol (segmented |
   preset-grid) has `reveals`, emit its `.segment-panels` block — **one `.segment-panel` per option,
   in option order** (panel count MUST equal option count; an option with no `reveals` entry gets an
   empty panel). Fill panel N with the slot list for option N's `value`: a **sub-control** slot →
   copy `subcontrols/<archetype>.html` — and if that sub-control is a full-width control
   (segmented/slider/preset-grid) carrying a `label`, render `<p class="subfn-label">{label}</p>` as
   the panel's first child, above the control (a revealed control is never the card's sole control, so
   its `label` always renders — `.subfn-label` title rule: subcontrols/README.md); a **`function:` slot** → render that function id by the same
   two-path rule above (snapshot e.g. `eq-audio`, else assembled) **but UNWRAPPED**: the panel is
   already inside the parent card's body, so drop the nested card's outer shell
   (`.function-container` > `.function-top-section` > its anonymous `<div>`) and place only its inner
   content — `.function-header` + `.function-content` (plus any trailing `<script>`) — directly in the
   panel. Keeping the full shell would draw a card-inside-a-card. A revealed
   sub-control may itself be a selector with its own `reveals` (recurse). The reveal is wired purely
   by the existing positional CSS (`headset.css` `.segment-panels` `:has(...:checked)`) — add no JS,
   embed no panel by hand. Empty `functions[]` → keep the placeholder note.

   **Function routing is id-only (architecture D8):** look up `functions/<id>.html` using the
   manifest's `id` field exactly as written — do not perform keyword matching, name inference, or
   description-based lookup. The keyword reference table in `functions/README.md` is an
   authoring-time guide for choosing the right `id` when writing a manifest; it is not executed here.
8. Keep the back link `<a class="back-link" href="index.html">` so the page returns home.
9. Strip `data-slot`/`data-instruction`/`data-property` from the output (no template markers in
   production — this also removes the device-image placeholder gray).

## Hard rules

- **Device identity, connection block, and feature icons come from `home.manifest` and MUST match
  the home page** (single source of truth — never re-enter or change them on the sub-page). The only
  sub-page differences are: the title (feature name), the functions, the back link, the collapsed
  (icon-only) feature nav, and NO Unpair.
- **Functions are COPIED from
  `.agents/skills/headset-gen-subpage/templates/functions/<id>.html`** (registry), never written from
  a description. Only when no snapshot exists does `headset-function` generate one (by copying its
  `function-frame.html` template).
- **Connection blocks / feature buttons / icons are COPIED** from the shared snippets in headset-shared,
  never written from a keyword. Unknown connection mode or icon id → halt and ask.
- Invent nothing: every value comes from a manifest.
- Every sub-page MUST keep the back link to `index.html`. NO Unpair on sub-pages.
- No inline `<style>`; link `shared/tokens.css` + `headset.css` only.
- One framework for all sub-pages — never create a sub-page-specific skill.
- **Reproducible from the manifest (no off-pipeline hand-patching).** The output must be exactly what
  re-running this skill on the manifest produces. If the rendered page needs something the manifest
  cannot express, the gap is in the manifest/schema/snippets — fix it THERE (add a `reveals` entry, a
  snippet, an archetype), never by editing the generated HTML directly. Conditional content (a
  reveal) lives in `reveals`, not as a hand-placed `.segment-panel`.

## Self-check

- Device identity (name/model/firmware/PPID/image) filled from `home.manifest` and identical to the
  home page?
- Feature title filled from the sub-page manifest (the `<title>` and the `<h2>`)?
- Connection block copied for `home.manifest.connectionType` (synced with home), with NO Unpair?
- Collapsed nav: one icon-only button per `home.manifest.features[]`, each icon synced with the home page?
- Each function COPIED from `functions/<id>.html` (bespoke) or via `headset-function` (no snapshot)?
- Manifest validated: every `archetype` in the enum, no stray `condition:` field, every `reveals` key
  matches an option `value`, options+panels ≤ 6, no duplicate option value/label? (HALT on any failure.)
- Every conditional reveal came from a `reveals` entry (positional `.segment-panel`s, count = option
  count) — no hand-embedded panel, no added JS?
- Output reproducible: would re-running this skill on the manifest produce this exact HTML? (No off-pipeline edits.)
- Back link to `index.html` present? Nothing fabricated? `data-slot`/`data-instruction`/`data-property` stripped?
