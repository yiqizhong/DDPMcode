# Sub-page function snapshots (registry — grows on demand)

One snapshot per **bespoke** function, named `<id>.html`. `headset-gen-subpage` **copies** the
file matching a manifest function's `id` into the sub-page's function region and fills its value
slots. This is the **same copy-not-generate mechanism** as the homepage's connection / feature /
icon snippets — a weak model copies a canonical function instead of inventing one from a description.

**EMPTY for now** — no bespoke function designs exist yet. Functions grow on demand (methodology
§9.4): 5–8 are expected over time, but when a real function design arrives, drop in `<id>.html`
built from `headset.css` classes, with each model-specific value marked `data-property="<name>"`.

## Rules

- **Keyword match** — before id lookup, check if the requirement description matches a keyword
  pattern in the Known-function matching table below. If it matches, treat the function as the
  named template id (COPY it). This overrides whatever id the manifest happens to assign.
- **Bespoke function** (`<id>.html` exists here) → COPY it, fill its `data-property` slots from the
  function's params. Never hand-write function markup when a snapshot exists.
- **No snapshot yet** (no `<id>.html`) → `@skills:headset-function` — it copies the canonical
  `function-frame.html` template and fills it, constrained strictly to manifest params (invent
  nothing). When such a function recurs and needs a bespoke design, promote it to a snapshot here (§9.4).
- No inline `<style>`; reuse tokens + `headset.css`. New reusable styles go in `headset.css`.

## Known-function matching

Keyword matching is **case-insensitive, partial match** on the requirement description or feature title.
Match any one keyword in a row to trigger the template.

| Keywords (any one triggers) | Template | Notes |
|---|---|---|
| `audio equalizer` · `equalizer` · `eq` · `sound eq` · `eq curve` · `frequency eq` | `eq-audio.html` | 5-band interactive EQ curve; 6-stop snap (+3 → −2 dB) |
| `download dell audio` · `download app` · `promotion` · `qr code` · `mobile app download` | `promotion-download.html` | App icon + description + CTA button; close button dismisses card |
| *(structural)* function has **exactly one boolean parameter** and no sliders / sub-controls | `toggle-single.html` | Title left, toggle right in header; no content area below |

**How to apply:** when a keyword triggers a match, resolve the template id to the value in the
Template column, then follow the normal Bespoke-function copy rule. Do not re-derive markup from
the description — copy the snapshot verbatim.

## Value slots inside a function snapshot

- `data-property="<name>"` for each model-specific value (e.g. a toggle state, slider value,
  dropdown selection). Structure is fixed by the snapshot; only values are filled from the manifest.
