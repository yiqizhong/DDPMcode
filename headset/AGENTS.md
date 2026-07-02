# headset — agent map

The **map** for generating headset pages. It holds routing + non-negotiables only; the
detailed generation rules live in the skills under the repo-root `.agents/skills/`. Read
this first.

> **Skill location (methodology §9.5 reconciliation).** §9.5 nests skills inside the
> category folder. Devin only discovers `SKILL.md` at the **repo root** `.agents/skills/`
> (it does not scan nested dirs — per the Devin skills docs), so these skills live at the
> root, **namespaced with the `headset-` prefix** to keep category isolation. The
> methodology's isolation/on-demand intent is preserved via naming + scoped descriptions;
> only the folder location differs.

> **Status: pilot.** Framework skills (`headset-gen-homepage`,
> `headset-gen-subpage`, `headset-function`) and `headset.css` exist, plus two committed **test
> fixture** models (`FIXTURE`, `HS-DEMO`) under `models/`; there is **no real product-model data
> yet** and **no dedicated `headset-function-<id>` skills**. Function snapshots exist and grow
> organically from real manifests (methodology §9.4) — do not pre-create
> them speculatively.

## Routing — generation MUST go through skills (do not hand-write)

- Generate a model **home page** → `@skills:headset-gen-homepage <MODEL>` (copy its frame,
  fill from the model manifest). **Never** hand-write `index.html`.
- Generate **any sub-page** (settings / configuration / any feature page, whatever it is
  called) → `@skills:headset-gen-subpage <MODEL> <SUBPAGE>`, with the title + function list
  from the manifest. **Never** hand-write sub-page HTML, and **never** create a
  sub-page-specific skill.
- Render a **function** inside a sub-page → **copy**
  `headset-gen-subpage/templates/functions/<id>.html` if it exists; otherwise (no snapshot)
  `@skills:headset-function`. **Never** hand-roll an ad-hoc function from a description.
  Function routing only recognizes the manifest's explicit `id` (D8). Generation never matches
  names/descriptions or overrides the manifest id — so choosing the right `id` is an AUTHORING
  responsibility, governed by the next rule.

- **MANDATORY: look a function up in the snapshot registry BEFORE you invent an `id`.** For every
  function, first check the keyword registry —
  `.agents/skills/headset-gen-subpage/templates/functions/keywords.py` (machine source) /
  `functions/README.md` (human table). If the requirement matches a registered snapshot's keyword, you
  **MUST** set `id` to that snapshot id and you **MUST NOT** add a `components:` list to it — the
  snapshot already defines its own structure. Do not invent a new id and assemble a control by guessing.
  - Example (the exact recurring bug): "Dell Audio Promotion" → keyword `promotion` →
    use `id: promotion-download` (a fixed promo card: app icon + description + QR/download CTA + close
    button; it has **NO** toggle). Writing `id: dell-audio-promotion` + `archetype: toggle` is WRONG.
  - This is mechanically enforced: `validate-manifest.py` **HALTs** when an assembled function's
    `id`/`title` matches a registered snapshot keyword, and the render pipeline then refuses to
    generate. The only ways past it are the real fix (use the snapshot id, drop `components`) or an
    explicit, justified `snapshot-opt-out: <snapshot-id>` + non-empty `opt-out-reason:` on that function.

If a relevant skill exists but was not used, that is a violation — redo it through the skill.

## Control Selection (Authoring Only)

These rules are for writing manifests and design snippets. Generation does not choose controls at
runtime: it renders the explicit archetype/id already frozen into the manifest (§7 / D10).

> **Authoritative per-archetype contract** (shape, conditional channel, options rule, required props,
> count windows) is generated from the catalog — run `python3 .agents/skills/headset-gen-subpage/archetypes.py`.
> It is always in sync with the validator; never hand-maintain a parallel copy of it. Select-family
> choice (segmented vs preset-grid vs dropdown) is now **mechanical** — the deterministic rule is
> `docs/component-selection-rule.md`; only the acoustic-environment **icon** rule stays as prose below.

**Data shape → archetype family**

| Data shape | Family |
|---|---|
| Boolean 2-state | Toggle |
| Ordered range / stepped value | Slider |
| Choose 1 from N unordered items | Select family (segmented/dropdown) |
| Clickable action / entry | Button family (button/link) |
| A visible grid of preset cards | Option-grid (preset-grid) |

**Within-family presentation**

| Family | Rule |
|---|---|
| Select: segmented / preset-grid / dropdown | By option count (deterministic): **2–3 → segmented** (hard cap 3), **4–6 → preset-grid**, **>6 → dropdown**. A ≤6-option `dropdown` is allowed ONLY with a declared `dropdown-reason` (`ordered-value` / `long-labels` / `inline-slot`); otherwise use the visible selector for that count. Full rationale: `docs/component-selection-rule.md`. |
| Button: button vs link | Use a real hyperlink (`<a href>`, like `feature-button`) for navigation to another page/view. Use a button for in-place actions. |

**Domain conventions**

| Domain | Archetype |
|---|---|
| Sidetone | Slider |
| Acoustic environment modes (ANC / Transparency / hear-through / similar) | Icon Segmented |
| On/off | Toggle |

**Conditional behavior ("when the user picks X, show Y" / "when this toggle is OFF, grey Y")**

Decide this at authoring and freeze it as data — never leave it for generation to infer, and never
hand-patch it into the output. A selector option that should reveal more controls is written as the
selector's **`reveals`** map (key = option `value` → ordered slot list; a slot is a component, a
snapshot function ref `{ function: <id> }`, or a nested assembled card `{ title, info?, components }`,
recursively). There is no `condition:` field. Full schema:
`.agents/skills/headset-gen-subpage/SKILL.md` → Manifest schema; mechanism:
`.agents/skills/headset-shared/components/README.md` → Conditional reveals.

A toggle dependency is different: a `toggle` component whose child controls should stay visible
but grey out when OFF uses **`dependents`** (ordered slot list, same slot shape as `reveals`). It
renders as one `.subfn-group` containing the toggle row and `.subfn-child` dependents. Do not put
`reveals` on a `toggle`.

> A full equalizer is the `eq-audio` **function** (`functions/eq-audio.html`), not a `slider`
> component. When a requirement mentions an EQ / equalizer / EQ curve, route it to the `eq-audio`
> function id (see `functions/README.md` keyword table) — at authoring time. If it appears only when
> a preset like "Custom" is chosen, place it as `{ function: eq-audio }` under that option's `reveals`.

**Nesting a child — the decision procedure (component enum, derived shape)**

A child under a function card is authored by choosing, in this order:

1. **Component (the real function)** — from the data shape (tables above): on/off → toggle;
   ordered continuous range → slider; then pick-1-of-N **by count** — 2–3 → segmented, 4–6 →
   preset-grid, >6 → dropdown (a ≤6 dropdown needs a declared `dropdown-reason`).
2. **Shape (container) is derived, not authored.** Two shapes: **row** (name left, a compact widget
   right — one line) and **stacked** (a `.subfn-label` title on top, a full-width widget below).
3. **Shape follows the component's width:**
   - compact (`toggle`, `dropdown`) → **row** shape: label left + widget right. The `toggle`
     component is the standard compact boolean row; `dropdown` is the other compact swappable widget.
   - full-width (`segmented`, `slider`, `preset-grid`) → **stacked** shape, with its
     `label` rendered as a `.subfn-label` title above it. The title is part of the stacked shape —
     never omit it for a named child.
4. **Condition (when it appears) — orthogonal to shape/component:** always present → a plain slot in
   `components[]`; appears on a selector choice → `reveals` on the selector (show/hide); stays
   visible but greys when a toggle is OFF → `dependents` on the `toggle` (grey-out).
5. **Or a whole nested card:** a child can be a titled assembled card (`{ title, info?, components }`)
   with its own recursive slot list. A child can also be an entire snapshot function
   (`{ function: <id> }`) dropped (unwrapped) into a reveal panel or a dependent.

The **row** shape is what compact components (`toggle`, `dropdown`) render as; the **stacked** shape
is `.subfn-label` + a full-width component.
Mechanism detail (markup, CSS classes): `.agents/skills/headset-shared/components/README.md`.
Schema + the mechanical HALT gate: `.agents/skills/headset-gen-subpage/SKILL.md`
(`validate-manifest.py`).

Segmented vs preset-grid details live in `.agents/skills/headset-shared/components/README.md`;
do not duplicate that full rule here.

## Requirements Fidelity Review (Authoring Only)

If a model folder has `requirements.md`, the mechanical coverage gate verifies identity,
function-list routing, walkthrough title/count sync, and `coverage.md` atom entries for every
numbered function-description clause. The atom checker then mechanically verifies each supported
stable locator/value assertion against the manifests. It does not judge whether each atom is the
right interpretation of the prose.

`coverage.md` is an atom table:

| Atom ID | Requirement | Locator | Expected | Verdict |
|---|---|---|---|---|
| `Audio setting #1.a` | One explicit fact/control requirement. | `audio-settings::noise-control::option(anc).selected` | `true` | `pass` |

Locator rules: use stable names only — manifest stem, function `id`, component label/archetype
selector, option `value`, and named channels such as `reveals.<option-value>` and `dependents`.
Never use positional paths like `/functions/0/components/0`. Supported mechanical assertions are
bounded to function existence, component archetype/label, option set, selected option, reveal or
dependent slot archetype/label, scalar values, and info/tooltip text. Use `Locator: n/a` for facts
that remain reviewer-only.

After authoring manifests and rendering pages, an **independent** model/agent that did not author the
manifests must audit `requirements.md` against `home.manifest`, every sub-page manifest,
`walkthrough.manifest` if present, and the rendered pages. This is the D10 human/strong-model
checkpoint: reasoning happens at authoring time and is frozen into the atom table. `Verdict` is the
reviewer's output: `pass`, `fail`, or `ambiguous`. The atom checker proves only that the manifest
matches the authored atoms and has not drifted; it does **not** prove the atoms faithfully reflect
the prose. It is deliberately **not** an LLM review and must not be implemented as an LLM-calling
script.

Mark `Verdict: ambiguous` and escalate to the human for missing defaults, unclear parent/child
ownership, show/hide vs grey-out ambiguity, option count/range mismatch, unclear tooltip target, or a
snapshot-keyword conflict.

Reviewer checklist:
- Every numbered function-description clause appears in the right rendered page/card/control.
- Defaults match: selected options, toggle states, slider values, and dropdown selections.
- Option sets and ranges match exactly; no extra or missing modes.
- Required tooltips are present on the correct function/control.
- Reveal/dependent behavior matches the source: show/hide vs grey-out, parent/child ownership, and
  nested groups.
- The rendered pages are reproducible from manifests; no hand-patched HTML or dangling feature route.

## Non-negotiables (apply to every generated page)

- **Manifest is the contract; validate before emitting (mechanical gate).** Generation is
  deterministic and invents nothing (D8). Before generating a sub-page, run
  `python3 .agents/skills/headset-gen-subpage/validate-manifest.py headset/models/<MODEL>/<SUBPAGE>.manifest`
  — non-zero exit = HALT (fix the manifest at source; never hand-edit the generated HTML). The script
  is the enforcement (zero-dependency, always runs), not prose; every archetype rule is derived from one
  contract file, `archetypes.py` (add a new archetype there + its snippet — nothing about archetypes is
  hardcoded in the validator). It catches: unknown `archetype`, stray `condition:`, a missing required
  prop (`slider` min/max/value, `dropdown` options), a missing `label` where one renders (non-sole
  compact rows and non-sole full-width controls — the BUG-002 class), `reveals` on a `toggle` (use `dependents` for
  toggle grey-out), `dependents` on a non-toggle, a `reveals` key matching no option, >6 selector
  options, a missing/duplicate option value or label, >1 option `selected`, a `function` slot with
  no snapshot, and a component `archetype` with no `headset-shared/components/<archetype>.html`
  snippet.

- **`verify-model.py <MODEL>` also enforces two mechanical no-orphan / no-stray rules.** An orphan
  manifest — a `*.manifest` in the model folder that no `home.manifest` feature `link`s to — is
  never validated, rendered, or reported by anything else, so `verify-model.py` fails it (run with
  `--manifests-only` to check this without requiring rendered HTML on disk, e.g. for gitignored dev
  fixtures). A stray page — a hand-written `*.html` in the model folder that the pipeline did not
  produce — fails the same way, giving "never hand-write HTML" mechanical enforcement for new files,
  not just drift on expected ones.

- **The deliverable is the rendered HTML on disk, not the manifest — RUN the renderer.** Writing the
  `.manifest` is the halfway point; the task is complete ONLY when
  `python3 .agents/skills/headset-gen-subpage/render-model.py <MODEL>` has been RUN, the page files
  (`index.html` + every sub-page `.html` + `walkthrough.html` when `walkthrough.manifest` exists —
  render-model.py renders all of it in one run) exist in `headset/models/<MODEL>/`, and
  `verify-model.py` passes. Stopping after the manifest and waiting to be asked for the HTML is an INCOMPLETE task, not a
  handoff — a manifest with no rendered page is a violation, not a TODO. Run the executor as the final
  step, every time.

- **Slots:** single value → `data-property="<name>"`; region (variant/list) → `data-slot` +
  `data-instruction`. Names map 1:1 to manifest fields. Fill by name, never by guessing.
  **Constraint:** a `data-slot` element in a frame template MUST be a leaf (no nested `<div>`
  inside it) — the filler locates the FIRST `</div>` after the slot's open tag as its close.
- **No hiding for cross-model variant axes:** connection blocks, function lists, and other
  generation-time product/model choices are still presence/absence. Never `display`-hide a
  not-selected variant or pre-embed-and-hide alternate product variants.
- **Runtime reveals are allowed inside one device panel:** terminal user interactions such as
  segmented conditional panels, selected states, sub-function greying, and shallow conditional
  reveals may pre-embed panel content and reveal it with CSS `:has()` / `:checked`. This is the
  explicit D11/D12 override for interactive controls, not a license to hide cross-model variants.
- **Share styles:** every page links `../../../shared/tokens.css` then `../../headset.css`.
  No inline `<style>` blocks; promote reusable styles to `headset.css`.
- **No template placeholders in product pages:** the dev tints (pale blue control-zone; pink
  feature-zone / content-area) and the gray image placeholder are template-only affordances,
  scoped to `[data-slot]` / `[data-property]` in `headset.css`. Finished product pages strip
  those markers (step 6), so every placeholder disappears automatically — they render clean.
  Never re-introduce a placeholder background on a generated product page.
- **Real routing (build contract):** feature entries are real `<a href>` links **whose target
  sub-page is actually built**. Declaring a `features[]` entry **obligates generating** its `link`
  sub-page via `@skills:headset-gen-subpage` — not just rendering the button. A button pointing at
  a page that was not built (dangling route / 404) is a violation, not a TODO. Every sub-page links
  back to `index.html`.
- **Connection blocks are copied, not written:** the connection block is COPIED verbatim from a
  predefined snippet
  (`.agents/skills/headset-shared/connection/<connectionType>.html`) and then
  value-filled — never generated from the connectionType keyword. If the mode has no snippet,
  HALT and ask; never fabricate. (This is what stops a weak model from hallucinating a block out
  of a word like "bluetooth".)
- **Invent nothing:** all content comes from the model manifest. Headset connection modes and
  features are defined by the manifest, not assumed from the mouse pilot.

## Self-check (after generating)

- **Did you RUN the renderer?** The page `.html` files must exist on disk now — not just the manifests. If only manifests were written, the task is NOT done: run `render-model.py <MODEL>`.
- Did every step go through its skill (no hand-written home/sub-page/function)?
- Every feature entry a real `<a href>` whose target sub-page was **actually built this run**
  (not left as a dangling route / TODO), and every sub-page links back to `index.html`?
- Any `display`-hidden or pre-embedded-and-hidden variant? (There must be none.)
- Any content hand-written that should have come from the manifest? If so, redo from the manifest.

## Tree

```
.agents/skills/                # repo ROOT — Devin discovers skills here (folders with a SKILL.md)
  headset-gen-homepage/        # SKILL.md + templates/home-frame.html
  headset-gen-subpage/         # SKILL.md + templates/subpage-frame.html + templates/functions/
  headset-function/            # SKILL.md + templates/function-frame.html — no-snapshot function generator
  headset-shared/              # NOT a skill — snippets shared by both gen skills:
                               #   connection/ · icons/ · feature-button.html (collapsed = +.feature-button--collapsed class)
headset/
  AGENTS.md                    # this map
  headset.css                  # category layout (references shared/tokens.css)
  models/                      # one folder per model (manifests + generated pages); FIXTURE + HS-DEMO test fixtures so far, no real product model yet
```
