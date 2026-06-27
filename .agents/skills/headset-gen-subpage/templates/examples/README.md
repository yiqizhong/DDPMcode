# Example / reference cards (NOT id-routed)

These are **reference / demo function cards** built during development to validate the architecture.

> **`headset-gen-subpage` does NOT look here for `id` routing.** It only routes to
> `../functions/<id>.html`. Nothing in this folder is ever auto-copied into a product page by id.
> Real, routable product cards live in `../functions/`.

Use these as **worked examples** when assembling a new card via `@skills:headset-function`
(card shell `function-frame.html` + `components/*` atoms):

| File | What it demonstrates |
|---|---|
| `collaboration.html` | Reference assembly: card shell + 2× `toggle` (Mic Noise Cancellation, Sidetone) + `slider`, with Sidetone wrapped in a `.subfn-group` (OFF greys the slider) + per-row `info-tooltip`. |
| `auto-power-off.html` | Proof of the **swappable header slot**: `single-control` shell with the default toggle switch replaced by `dropdown.html` (fixed-position list escapes overflow clipping). |
| `noise-control.html` | Weak-model assembly test — a **simplified** Noise Control (toggle + strength slider). **NOT** the real Figma 3-mode (ANC / Transparency / Off); kept as a test artifact, real version TBD. |

To build a real product card, design it **per the product's requirements** and either drop a new
snapshot in `../functions/<id>.html` or assemble it via `headset-function`. Do not treat the cards
here as ready-to-ship product cards.
