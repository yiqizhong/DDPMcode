---
name: headset-gen-subpage
description: Generate any headset sub-page (settings/configuration/feature page) from its manifest. Use for every sub-page — never hand-write sub-page HTML and never make a per-page skill.
argument-hint: <MODEL> <SUBPAGE>
---

# headset-gen-subpage

One framework that holds ANY headset sub-page. It does not know or care what the sub-page is
called or contains — name and controls come from the manifest. There is intentionally NO
per-sub-page skill: the name is content, so it lives in the manifest, not in a skill name.

Invoke: `@skills:headset-gen-subpage <MODEL> <SUBPAGE>`
(e.g. `@skills:headset-gen-subpage HS1234 mic-settings`).

## Inputs

- `$1` — model folder under `headset/models/`. `$2` — sub-page file stem.
- Manifest: `headset/models/$1/$2.manifest` — a `title` and a `controls[]` list (each control
  = an `id` + parameters). `controls[]` may be empty.

## Procedure

1. **Copy the frame** to the model folder, rewriting the two stylesheet links from
   preview-relative (4 levels up, so the template renders in place) to output-relative. Run
   from the repo root:
   ```
   sed -e 's|href="../../../../shared/tokens.css"|href="../../../shared/tokens.css"|' \
       -e 's|href="../../../../headset/headset.css"|href="../../headset.css"|' \
       .agents/skills/headset-gen-subpage/templates/subpage-frame.html \
       > headset/models/$1/$2.html
   ```
   Do not otherwise rewrite the frame.
2. Read `headset/models/$1/$2.manifest`.
3. Fill `data-property="subpage-title"` (the `<title>` and the `<h1>`) from `title`.
4. **Controls** (`data-slot="controls"`): for each `controls[]` item, render it via the control
   layer — if a `headset-control-<id>` skill exists, call `@skills:headset-control-<id>`;
   otherwise call `@skills:headset-control-generic`. N controls → N rendered controls. If
   `controls[]` is empty, keep the placeholder note (do not fabricate controls).
5. Keep the back link `<a class="back-link" href="index.html">` so the page returns home.
6. Strip `data-slot`/`data-instruction` from the output.

## Hard rules

- Invent nothing: title and controls come from the manifest. Never fabricate EQ presets,
  sidetone/mic controls, ANC toggles, or any control the manifest does not list.
- Every sub-page MUST keep the back link to `index.html`.
- No inline `<style>`; link `shared/tokens.css` + `headset.css` only.
- One framework for all sub-pages — never create a sub-page-specific skill.

## Self-check

- Title filled from the manifest (not guessed)?
- Each listed control rendered via a `headset-control-*` skill (known) or
  `headset-control-generic` (unknown)?
- Back link to `index.html` present?
- No fabricated controls; empty `controls[]` left as the placeholder note?
