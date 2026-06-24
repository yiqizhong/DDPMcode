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
> `headset-gen-subpage`, `headset-control-generic`) and `headset.css` exist; there is **no
> model data yet** and **no dedicated `headset-control-<id>` skills yet**. Control skills grow
> organically from real manifests (methodology §9.4) — do not pre-create them speculatively.

## Routing — generation MUST go through skills (do not hand-write)

- Generate a model **home page** → `@skills:headset-gen-homepage <MODEL>` (copy its frame,
  fill from the model manifest). **Never** hand-write `index.html`.
- Generate **any sub-page** (settings / configuration / any feature page, whatever it is
  called) → `@skills:headset-gen-subpage <MODEL> <SUBPAGE>`, with the title + control list
  from the manifest. **Never** hand-write sub-page HTML, and **never** create a
  sub-page-specific skill.
- Render a **control** inside a sub-page → if a `headset-control-<id>` skill exists, use it;
  otherwise `@skills:headset-control-generic`. **Never** hand-roll an ad-hoc control.

If a relevant skill exists but was not used, that is a violation — redo it through the skill.

## Non-negotiables (apply to every generated page)

- **Slots:** single value → `data-property="<name>"`; region (variant/list) → `data-slot` +
  `data-instruction`. Names map 1:1 to manifest fields. Fill by name, never by guessing.
- **No hiding:** never `display`-hide a variant and never pre-embed-and-hide. Conditional
  content is presence/absence — generate only the block the model needs.
- **Share styles:** every page links `../../../shared/tokens.css` then `../../headset.css`.
  No inline `<style>` blocks; promote reusable styles to `headset.css`.
- **Real routing:** feature entries are real `<a href>` links; every sub-page links back to
  `index.html`.
- **Invent nothing:** all content comes from the model manifest. Headset connection modes and
  features are defined by the manifest, not assumed from the mouse pilot.

## Self-check (after generating)

- Did every step go through its skill (no hand-written home/sub-page/control)?
- Every feature entry a real `<a href>` whose target sub-page exists, and every sub-page links
  back to `index.html`?
- Any `display`-hidden or pre-embedded-and-hidden variant? (There must be none.)
- Any content hand-written that should have come from the manifest? If so, redo from the manifest.

## Tree

```
.agents/skills/                # repo ROOT — Devin discovers skills here
  headset-gen-homepage/        # SKILL.md + templates/home-frame.html
  headset-gen-subpage/         # SKILL.md + templates/subpage-frame.html
  headset-control-generic/     # SKILL.md — fallback for controls with no dedicated skill
headset/
  AGENTS.md                    # this map
  headset.css                  # category layout (references shared/tokens.css)
  models/                      # one folder per model (manifests + generated pages); none yet
```
