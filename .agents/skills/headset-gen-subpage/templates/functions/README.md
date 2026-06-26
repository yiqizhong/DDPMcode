# Sub-page function snapshots (registry — grows on demand)

One snapshot per **bespoke** function, named `<id>.html`. `headset-gen-subpage` **copies** the
file matching a manifest function's `id` into the sub-page's function region and fills its value
slots. This is the **same copy-not-generate mechanism** as the homepage's connection / feature /
icon snippets — a weak model copies a canonical function instead of inventing one from a description.

**This dir is the id-routed registry: only real, ready-to-use cards live here** (currently
`eq-audio`, `promotion-download`, `single-control`). Reference / demo cards (e.g. `collaboration`,
`auto-power-off`, `noise-control`) live in the sibling **`../examples/`** and are **NOT id-routed** —
`headset-gen-subpage` never copies from there; they are worked examples for assembling new cards.
Functions grow on demand (§9.4): when a real design arrives, drop a new `<id>.html` **here**, built
from `headset.css` classes, each model-specific value marked `data-property="<name>"`.

## Rules

**Generation-time (weak model executing headset-gen-subpage):**
- **Bespoke function** (`<id>.html` exists here) → COPY the file whose name matches the manifest
  function's `id` exactly. The snapshot is a **complete card** — it goes in **as-is**; the manifest's
  per-slot params are a **rare override** (replace a `data-property` value only where provided; no
  params → keep the snapshot's content unchanged). The page shows **exactly the functions the manifest
  lists** (presence/absence) — none extra, and an unlisted function is never rendered. Function routing
  is **id-only** (architecture D8: "身份认 id，不认名字") — the manifest's `id` field is the sole lookup
  key; no keyword matching or name inference is performed at generation time.
- **No snapshot yet** (no `<id>.html` matching the manifest `id`) → `@skills:headset-function` —
  it copies the canonical `function-frame.html` template and fills it, constrained strictly to
  manifest params (invent nothing). When such a function recurs and needs a bespoke design,
  promote it to a snapshot here (§9.4).
- No inline `<style>`; reuse tokens + `headset.css`. New reusable styles go in `headset.css`.

## Known-function reference table (authoring-time only)

> **IMPORTANT — authoring vs. generation:**
> This table is a **reference for human authors and strong models when writing or reviewing a
> manifest** — it helps you pick the correct `id` for a function. It is **not executed at
> generation time**. The weak model generating a sub-page does NOT perform keyword matching;
> it only looks up `functions/<manifest.id>.html` as described above (D8).

The keywords below are **whole-word / phrase matches** (case-insensitive). They are not partial
substring matches — e.g. `equalizer` does not trigger on `frequency` or `request`.

| Authoring keywords (whole-word/phrase) | Correct `id` to use | Notes |
|---|---|---|
| `audio equalizer` · `equalizer` · `sound eq` · `eq curve` · `frequency eq` | `eq-audio` | 5-band interactive EQ curve; 6-stop snap (+3 → −2 dB) |
| `download dell audio` · `download app` · `promotion` · `qr code` · `mobile app download` | `promotion-download` | App icon + description + CTA button; close button dismisses card |
| *(structural)* function has **exactly one boolean parameter** and no sliders / sub-controls | `single-control` | Title left, toggle right in header; no content area below — authoring guidance only, not auto-applied at generation time |

**How to use this table (authoring only):** when designing a manifest and you recognise a function
that matches a keyword pattern, set the manifest function's `id` to the value in the "Correct id"
column. The generation step will then copy the correct snapshot by that id. Do not re-derive markup
from the description — copy the snapshot verbatim.

## Value slots inside a function snapshot

- `data-property="<name>"` for each model-specific value (e.g. a toggle state, slider value,
  dropdown selection). Structure is fixed by the snapshot; only values are filled from the manifest.
