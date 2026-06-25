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
4. **Controls** (`data-slot="controls"`): do NOT write control markup. For each `controls[]` item:
   - If `.agents/skills/headset-gen-subpage/templates/controls/<control.id>.html` exists, **copy**
     it into the controls region and fill its `data-property` value slots from the control's params.
   - Otherwise fall back to `@skills:headset-control-generic` (last-resort generation, strictly
     from manifest params — invent nothing). When such a control recurs, promote it to a snippet.
   N controls → N rendered controls. If `controls[]` is empty, keep the placeholder note.
5. Keep the back link `<a class="back-link" href="index.html">` so the page returns home.
6. Strip `data-slot`/`data-instruction`/`data-property` from the output (no template markers in
   production — this also removes the device-image placeholder gray).

## Hard rules

- **Controls are COPIED from
  `.agents/skills/headset-gen-subpage/templates/controls/<id>.html`** (registry), never written
  from a description. Only when no snippet exists does `headset-control-generic` generate one
  (strictly from manifest params). This is the same copy-not-generate defense as the homepage snippets.
- Invent nothing: title and controls come from the manifest. Never fabricate EQ presets,
  sidetone/mic controls, ANC toggles, or any control the manifest does not list.
- Every sub-page MUST keep the back link to `index.html`.
- No inline `<style>`; link `shared/tokens.css` + `headset.css` only.
- One framework for all sub-pages — never create a sub-page-specific skill.

## Self-check

- Title filled from the manifest (not guessed)?
- Each listed control COPIED from
  `.agents/skills/headset-gen-subpage/templates/controls/<id>.html` (known) or, if none,
  rendered via `headset-control-generic` (unknown)?
- Back link to `index.html` present?
- No fabricated controls; empty `controls[]` left as the placeholder note?
