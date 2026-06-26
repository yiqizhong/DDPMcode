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

> **Status: pilot skeleton.** Framework skills (`headset-gen-homepage`,
> `headset-gen-subpage`, `headset-function`) and `headset.css` exist; there is **no model data
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
  Function routing only recognizes the manifest's explicit `id` (D8). Keyword tables are
  authoring-time hints for choosing that id; generation never matches names/descriptions or
  overrides the manifest id.

If a relevant skill exists but was not used, that is a violation — redo it through the skill.

## Control Selection (Authoring Only)

These rules are for writing manifests and design snippets. Generation does not choose controls at
runtime: it renders the explicit archetype/id already frozen into the manifest (§7 / D10).

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
| Select: segmented vs dropdown | Use Segmented when there are <=5-6 options and they should stay visible, or when icon cards are needed. Use Dropdown when there are more options or space is tight. |
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
selector's **`reveals`** map (key = option `value` → ordered slot list; a slot is a sub-control or a
nested `{ function: <id> }`, recursively). There is no `condition:` field. Full schema:
`.agents/skills/headset-gen-subpage/SKILL.md` → Manifest schema; mechanism:
`.agents/skills/headset-shared/subcontrols/README.md` → Conditional reveals.

A toggle dependency is different: a `control-row` toggle whose child controls should stay visible
but grey out when OFF uses **`dependents`** (ordered slot list, same slot shape as `reveals`). It
renders as one `.subfn-group` containing the toggle row and `.subfn-child` dependents. Do not put
`reveals` on a `control-row`.

> A full equalizer is the `eq-audio` **function** (`functions/eq-audio.html`), not a `slider`
> sub-control. When a requirement mentions an EQ / equalizer / EQ curve, route it to the `eq-audio`
> function id (see `functions/README.md` keyword table) — at authoring time. If it appears only when
> a preset like "Custom" is chosen, place it as `{ function: eq-audio }` under that option's `reveals`.

Segmented vs preset-grid details live in `.agents/skills/headset-shared/subcontrols/README.md`;
do not duplicate that full rule here.

## Non-negotiables (apply to every generated page)

- **Manifest is the contract; validate before emitting.** Generation is deterministic and invents
  nothing (D8). HALT and ask on any out-of-contract manifest — unknown `archetype` or function `id`,
  a stray `condition:` field, `reveals` on a `control-row` (use `dependents` for toggle grey-out),
  `dependents` on anything other than `control-row`, a `reveals` key that matches no option,
  options+panels > 6, or duplicate option values. Do not paper over an authoring bug by hand-editing
  the HTML (see gen-subpage Validation).

- **Slots:** single value → `data-property="<name>"`; region (variant/list) → `data-slot` +
  `data-instruction`. Names map 1:1 to manifest fields. Fill by name, never by guessing.
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
  models/                      # one folder per model (manifests + generated pages); none yet
```
