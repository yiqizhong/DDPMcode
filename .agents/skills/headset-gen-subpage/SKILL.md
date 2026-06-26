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
   the manifest lists, no more, no less.** For each `functions[]` item, **copy**
   `.agents/skills/headset-gen-subpage/templates/functions/<function.id>.html` **whole** — the snapshot
   is already a complete card, so it goes in **as-is**. The manifest's per-slot params are a **rare
   override**: replace a `data-property` value only where the manifest provides one; **no params → keep
   the snapshot's content unchanged** (do not empty it, do not invent). If no snapshot exists, fall back
   to `@skills:headset-function` (strictly from manifest params — invent nothing). Empty `functions[]`
   → keep the placeholder note (nothing listed → nothing rendered).
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

## Self-check

- Device identity (name/model/firmware/PPID/image) filled from `home.manifest` and identical to the
  home page?
- Feature title filled from the sub-page manifest (the `<title>` and the `<h2>`)?
- Connection block copied for `home.manifest.connectionType` (synced with home), with NO Unpair?
- Collapsed nav: one icon-only button per `home.manifest.features[]`, each icon synced with the home page?
- Each function COPIED from `functions/<id>.html` (bespoke) or via `headset-function` (no snapshot)?
- Back link to `index.html` present? Nothing fabricated? `data-slot`/`data-instruction`/`data-property` stripped?
