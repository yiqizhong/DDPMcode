# Sub-page control snippets (registry — grows on demand)

One snippet per known control, named `<id>.html`. `headset-gen-subpage` **copies** the file
matching a manifest control's `id` into the sub-page's controls region and fills its value slots.
This is the **same copy-not-generate mechanism** as the homepage's connection / feature / icon
snippets — a weak model copies a canonical control instead of inventing one from a description.

**EMPTY for now** — no control designs exist yet. Controls grow on demand (methodology §9.4):
when a real control design arrives, drop in `<id>.html` built from `headset.css` classes, with
each model-specific value marked `data-property="<name>"`.

## Rules

- **Known control** (`<id>.html` exists) → COPY it, fill its `data-property` slots from the
  control's params. Never hand-write control markup when a snippet exists.
- **Unknown control** (no `<id>.html`) → `@skills:headset-control-generic` — the last-resort
  generator, constrained strictly to manifest params (invent nothing). When such a control
  recurs, promote it to a snippet here (§9.4).
- No inline `<style>`; reuse tokens + `headset.css`. New reusable styles go in `headset.css`.

## Value slots inside a control snippet

- `data-property="<name>"` for each model-specific value (e.g. a toggle state, slider value,
  dropdown selection). Structure is fixed by the snippet; only values are filled from the manifest.
