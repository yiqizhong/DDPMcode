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

## Deterministic executor (REQUIRED — the page is not done until this runs)

The canonical, reproducible generation path is the render scripts:
`python3 .agents/skills/headset-gen-subpage/render-model.py <MODEL>` builds the whole model, or
`python3 .agents/skills/headset-gen-subpage/render-subpage.py <MODEL> <SUBPAGE>` renders this
single sub-page. The Procedure below is the human-readable SPEC those scripts implement and must
stay in lock-step with them.

**Authoring the `.manifest` is NOT the deliverable — the rendered `.html` on disk is.** Writing the
manifest is the halfway point: you MUST then RUN the executor so that
`headset/models/<MODEL>/<SUBPAGE>.html` actually exists in the model folder, then confirm with
`verify-model.py`. Do NOT stop after the manifest and wait to be asked for the HTML — running the
render is part of THIS task, not an optional follow-up. (Definition of Done: see Hard rules.)

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
    components:                      # assembled path only (no snapshot). Ordered list of slots.
      - archetype: <enum>             # component slot: toggle | slider | segmented | preset-grid | dropdown
        ...<archetype value slots>... # per components/README.md (label / min,max,value / options / …)
        reveals:                      # OPTIONAL — ONLY on a selector archetype (segmented | preset-grid)
          <option-value>:             # key MUST equal one of THIS selector's option `value`s
            - <slot>                  # ordered list of revealed slots; same recursive slot shape
        dependents:                   # OPTIONAL — ONLY on a toggle
          - <slot>                    # ordered slot list (same shape as a reveals slot) that GREYS
            ...                       #   OUT (stays visible, non-interactive) when the toggle is OFF
```

`<slot>` is recursive and may be any of:

- a component: `{ archetype: <enum>, ...value slots }`
- a snapshot function ref: `{ function: <function-id> }` (copied by id, unwrapped inside the parent)
- a nested assembled card: `{ title: <string>, info?: <string>, components: [ <slot>... ] }`

**Two distinct conditional mechanisms — do not conflate:**
- **`reveals`** — the conditional-reveal / recursive-slot primitive (architecture §6.5 / §8 / §9.1).
  ONLY on a selector (segmented | preset-grid). A selected option SHOWS/HIDES a `.segment-panel`. A
  revealed slot may itself be a selector with its own `reveals`, a `{function:<id>}` snapshot ref, or
  a nested assembled card `{title, info?, components}` with its own recursive slots. The ONLY legal way to
  express "select X → show Y". It replaces any flat `condition:` field (a component must NEVER carry
  `condition:`). Do not hand-embed conditional panels.
- **`dependents`** — the toggle grey-out (`.subfn-group`) relationship. ONLY on a `toggle`.
  Its dependents STAY VISIBLE but grey out + go non-interactive when the toggle is OFF.
  Use this — not `reveals` — whenever a toggle owns dependent controls (e.g. Mic Noise Canceling →
  Canceling Strength).

## Validation (run BEFORE emitting — HALT and ask on any failure)

**Mechanical gate (run this first, every time):**
```
python3 .agents/skills/headset-gen-subpage/validate-manifest.py headset/models/$1/$2.manifest
```
It enforces the rules below deterministically (zero-dependency, stdlib only — it ALWAYS runs).
**Exit 0 → proceed. Non-zero → HALT**: fix the manifest at the source (do not guess, do not hand-edit
the generated HTML), then re-run. The HALT directive is no longer prose a weak model can reason
around — the script is the gate. (If python3 is somehow unavailable, fail closed: do not generate.)

Generation is deterministic; an out-of-contract manifest is an authoring bug. Every archetype rule
is derived from one machine-readable contract — `archetypes.py` (next to the validator); add a new
archetype there + its snippet, never by hardcoding. The script HALTs when:

- `archetype` is not in the catalog {toggle, slider, segmented, preset-grid, dropdown}.
- A component carries a legacy `condition:` field → migrate it to a selector's `reveals` or a toggle's `dependents`.
- A required prop is missing — `slider` without `min`/`max`/`value`; a `dropdown` without `options`.
- A `label` is missing where one renders — any compact row (`toggle`/`dropdown`) or full-width
  control (`slider`/`segmented`/`preset-grid`) that is NOT its card's sole top-level control (a lone
  top-level control renders headingless and legitimately omits it because the card title covers it).
  A dropped heading is the BUG-002 class.
- `reveals` appears on a non-selector archetype (incl. a `toggle`); for a toggle's grey-out
  dependents use `dependents` (reveals is selector-only). Or a `reveals` key matches no option `value`.
- `dependents` appears on any archetype other than `toggle`.
- A selector has more than **6** `options` (headset.css positional `:has()` maps `.segment` /
  `.segment-panel` `nth-child` only up to 6; panels are 1:1 with options). Dropdown option lists are uncapped.
- An option is missing its `value` or `label`; two options share the same `value` (or `label`); or
  more than one option is marked `selected` — a data error; ask which is correct.
- A function id resolves to a snapshot `functions/<id>.html` but also declares `components:` — snapshots carry their own structure.
- A bare `function` slot's id has no `functions/<id>.html` snapshot.
- An assembled function's `id` or `title` matches a registered snapshot keyword (e.g. "promotion" → `promotion-download`) and no valid opt-out is present. Fix: set `id: <snapshot-id>` and remove `components:`, OR add `snapshot-opt-out: <snapshot-id>` (must equal the matched snapshot) and a non-empty `opt-out-reason`. A `snapshot-opt-out` with no keyword match, or naming the wrong snapshot, or with an empty reason, is itself an error.

**Requirements coverage gate (system-level, when `requirements.md` exists):**
```
python3 .agents/skills/headset-gen-subpage/check-requirements-coverage.py headset/models/$1
python3 .agents/skills/headset-gen-subpage/check-coverage-atoms.py headset/models/$1
```
These are per-model mechanical gates. If `headset/models/$1/requirements.md` is absent, they print
`SKIP` and exit 0; absence is not a failure. The first gate HALTs on device identity drift,
function-list / feature-route drift, walkthrough title/count drift, or a missing `coverage.md` atom
for any numbered function-description clause. The second gate reads the atom table and mechanically
verifies each supported locator/value assertion against the manifests. The atom-table format is shown
in `templates/coverage-template.md`.

**Atom table format (`coverage.md`):**

| Atom ID | Requirement | Locator | Expected | Verdict |
|---|---|---|---|---|
| `Audio setting #1.a` | One fact/control requirement. | `audio-settings::noise-control::option(anc).selected` | `true` | `pass` |

- `Atom ID` starts with the numbered clause id plus a suffix, e.g. `Audio setting #1.a`.
- `Locator` uses stable names only: manifest stem, function `id`, component label/archetype selector,
  option `value`, and named channels such as `reveals.<option-value>` and `dependents`. Do not use
  positional paths like `/functions/0/components/0`.
- Supported mechanical assertions are deliberately bounded: function exists; component archetype/label;
  exact option set; selected option; reveal/dependent slot archetype/label; scalar values; and
  info/tooltip text. Use `n/a` for reviewer-only facts that do not fit this bounded grammar.
- `Verdict` is the independent reviewer's output: `pass`, `fail`, or `ambiguous`. The checker validates
  the row shape and supported manifest assertions; it does not decide the verdict.

**Independent requirements review (authoring-time only, NOT a code gate):** after authoring manifests
and rendering pages, hand `requirements.md`, `home.manifest`, all sub-page manifests,
`walkthrough.manifest` if present, and the rendered pages to an independent model/agent that did not
author the manifests. This is the D10 human/strong-model checkpoint: reasoning happens at authoring
time and is frozen into data. The reviewer writes/fills `coverage.md`: one atom per explicit fact,
stable locator, expected value, and `Verdict`. The mechanical atom checker proves only "the manifest
matches the authored atoms and did not drift." It does **not** prove the atoms faithfully reflect the
prose. Do not build an LLM-calling script and do not claim the review is mechanical.

Mark an atom `ambiguous` and escalate to the human when the source leaves any of these unclear:
missing default, unclear parent/child ownership, show/hide vs grey-out behavior, option count/range
mismatch, unclear tooltip target, or a snapshot-keyword conflict.

Reviewer checklist:
- Every numbered function-description clause is present in the intended page/card/control.
- Defaults match requirements: selected options, toggle states, slider values, dropdown selections.
- Option sets match exactly, including missing/extra modes and ordered ranges.
- Tooltips required by the source are present on the right function/control.
- Reveal/dependent behavior matches the requirement: show/hide vs grey-out, parent/child structure,
  and nested groups.
- Rendered HTML matches the manifest intent; no hand-patched output or dangling feature routes.

## Autonomous generation + self-correction loop

Run this loop for headset model generation:

1. Read `requirements.md`. Author all manifests (home + each subpage + walkthrough) — the one
   non-mechanical step (D10).
2. Run `.agents/skills/headset-gen-subpage/regen.sh` (validate + render + verify, all models).
3. If green → done. If a check fails → CLASSIFY it with the table below and act; loop back to step 2.
4. Stop and ESCALATE to the human ONLY for the semantic cases.

| Gate failure | Class | Action |
|---|---|---|
| drift (HTML != renderer output) | AUTOFIX (deterministic) | re-run the renderer (`regen.sh`); never hand-edit HTML |
| validate HALT: unknown key | AUTOFIX | correct the key per schema (obvious typo like `tooltip`->`info` → rename; otherwise fix/remove) |
| validate HALT: wrong archetype for option count | AUTOFIX | change archetype per rule (2-3 → segmented, 5-6 → preset-grid) |
| validate HALT: `label` == card `title` | AUTOFIX | remove the redundant label |
| validate HALT: slider min/max/value/stops | AUTOFIX | correct to the requirement's range |
| validate HALT: image absolute / `..` / missing | AUTOFIX | normalize to a relative existing path, or `image: none` + reason if there is genuinely no image |
| validate HALT: nested-card depth cap exceeded | ESCALATE | deeper nesting needs the unbuilt D13 engine — flag it |
| CSS-class not defined | AUTOFIX | use a class that exists in the linked CSS (or define it in CSS) |
| requirements-coverage HALT: missing function / device-identity mismatch | AUTOFIX if the manifest clearly dropped/garbled what requirements state; ESCALATE if which is right is unclear | fix manifest, or escalate |
| coverage-atom mismatch (manifest != atom) | AUTOFIX if the atom faithfully reflects the requirement and the manifest deviates; ESCALATE if it's unclear whether the atom or the manifest is wrong | fix manifest, or escalate |
| independent-review fail/ambiguous, or genuine prose ambiguity (e.g. the "4h" case) | ESCALATE | stop; present the requirement quote, the conflict, and options to the human |

Governing PRINCIPLE: **auto-fix when the correct fix is determinable from rules + requirements
without guessing intent; escalate the moment resolving it would require guessing what the human
meant.** When escalating, present: the requirement quote, what the manifest/atom currently says, why
it's ambiguous, and a recommendation.

AUTOFIX edits the MANIFEST (or CSS/snippet), never the rendered HTML (D19). After any fix, re-run
`.agents/skills/headset-gen-subpage/regen.sh`.

## Procedure

1. **Copy the frame** to the model folder, rewriting the two stylesheet links from
   preview-relative to output-relative. Run from the repo root:
   ```
   sed -e 's|href="../../../../shared/tokens.css"|href="../../../shared/tokens.css"|' \
       -e 's|href="../../../../shared/shell.css"|href="../../../shared/shell.css"|' \
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
     (`function-frame.html`), fills `title`/`info`, then copies one `headset-shared/components/<archetype>.html`
     per `components[]` entry, in order, strictly from manifest params (invent nothing).

   **Conditional reveals (the recursive slot):** when an assembled selector component (segmented |
   preset-grid) has `reveals`, emit its `.segment-panels` block — **one `.segment-panel` per option,
   in option order** (panel count MUST equal option count; an option with no `reveals` entry gets an
   empty panel). Fill panel N with the slot list for option N's `value`: a **component** slot →
   copy `components/<archetype>.html` — and if that component is a full-width control
   (segmented/slider/preset-grid) carrying a `label`, render `<p class="subfn-label">{label}</p>` as
   the panel's first child, above the control (a revealed control is never the card's sole control, so
   its `label` always renders — `.subfn-label` title rule: components/README.md); a **`function:` slot** → render that function id by the same
   two-path rule above (snapshot e.g. `eq-audio`, else assembled) **but UNWRAPPED**: the panel is
   already inside the parent card's body, so drop the nested card's outer shell
   (`.function-container` > `.function-top-section` > its anonymous `<div>`) and place only its inner
   content — `.function-header` + `.function-content` (plus any trailing `<script>`) — directly in the
   panel. Keeping the full shell would draw a card-inside-a-card. A **nested assembled card** slot →
   render a labeled `.subfn-group`: `title` becomes `.subfn-label`, optional `info` uses the existing
   info-tooltip snippet, and each inner slot is wrapped in `.subfn-child` before recursive rendering.
   A revealed component may itself be a selector with its own `reveals` (recurse). The reveal is wired purely
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
- No inline `<style>`; link `shared/tokens.css` + `shared/shell.css` + `headset.css` only.
- One framework for all sub-pages — never create a sub-page-specific skill.
- **Reproducible from the manifest (no off-pipeline hand-patching).** The output must be exactly what
  re-running this skill on the manifest produces. If the rendered page needs something the manifest
  cannot express, the gap is in the manifest/schema/snippets — fix it THERE (add a `reveals` entry, a
  snippet, an archetype), never by editing the generated HTML directly. Conditional content (a
  reveal) lives in `reveals`, not as a hand-placed `.segment-panel`.
- **Definition of Done = rendered HTML on disk, not the manifest.** The task is complete ONLY when
  `render-model.py <MODEL>` (or `render-subpage.py`) has been RUN, `headset/models/<MODEL>/<SUBPAGE>.html`
  exists, and `verify-model.py` passes. Authoring the manifest and stopping — leaving the render "for
  when asked" — is an INCOMPLETE task, not a handoff. Run the executor as the final step, every time.

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
- **Did you actually RUN the renderer?** `headset/models/$1/$2.html` must exist on disk now — not just the manifest. If you only wrote the manifest, the task is NOT done: run `render-model.py $1`.
- After generation, run `python3 .agents/skills/headset-gen-subpage/verify-model.py $1`; non-zero means output drifted from the manifest (hand-edited or stale) — regenerate via `render-model.py`, never hand-edit.
- Back link to `index.html` present? Nothing fabricated? `data-slot`/`data-instruction`/`data-property` stripped?
