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
> yet** and **no dedicated `headset-function-<id>` skills or function snapshots yet**. Function
> skills/snapshots grow organically from real manifests (methodology §9.4) — do not pre-create
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

If a relevant skill exists but was not used, that is a violation — redo it through the skill.

## Non-negotiables (apply to every generated page)

- **Slots:** single value → `data-property="<name>"`; region (variant/list) → `data-slot` +
  `data-instruction`. Names map 1:1 to manifest fields. Fill by name, never by guessing.
- **No hiding:** never `display`-hide a variant and never pre-embed-and-hide. Conditional
  content is presence/absence — generate only the block the model needs.
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
