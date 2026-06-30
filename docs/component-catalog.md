# DDPM Component Catalog · headset category

> **Terminology**: The reusable controls inside cards (toggle/slider/segmented/preset-grid/dropdown) are collectively called **DDPM Component** (code identifier `component` / field `components:` / directory `headset-shared/components/`). The former name "sub-control" is deprecated.

> **Nature**: A **living catalog** recording all currently reusable UI components: what each is, when to use it, whether it is universal, and how the Agent calls it.
> **Update this file whenever a component is added, renamed, or removed.** Names use plain language; the real file/term in code is in parentheses (the mapping is preserved).
> For the design rationale ("why") see [`function-card-architecture.md`](function-card-architecture.md); for where to read/change things see [`navigation.md`](navigation.md).
> **Last updated**: 2026-06-26 · Maintenance rules at the bottom.

## 0. Quick reference (three kinds of reusable "pieces")

| Category | One-line description | Count | Location |
|---|---|---|---|
| **① In-card component building blocks** (`components/`) | Small controls assembled into function cards: toggle, dropdown, slider, segmented… | 6 files (+ toggle has no separate file) | `.agents/skills/headset-shared/components/` |
| **② Generic function-card shell** (blank card / `function-frame.html`) | The **blank template** used when no ready-made card exists: a title + empty body; assemble by inserting building blocks | 1 | `.agents/skills/headset-function/templates/` |
| **③ Swappable-content slots + wiring mechanisms** (slot / CSS) | The positions in templates that "can change content / will react" | 4 | Embedded in the files above + `headset.css` |

> The **① building blocks / ② shell / ③ slot mechanisms** above are the cross-product reusable "pieces." The **whole function cards** in the `functions/` directory are counted separately and split into two kinds:
> **ready-to-use cards** (`single-control`/`eq-audio`/`promotion-download`), and **demo examples** built during development to validate the architecture
> (`collaboration`/`auto-power-off`/`noise-control`) — see the appendix at the bottom for the inventory and distinction.

**Call model in one sentence**: `gen-subpage` reads `functions[]` from the manifest → if a function `id` **exactly matches an existing card in `functions/`** it copies the whole card (D8, id-only, not name-based); **otherwise** it uses `headset-function` to copy the ② blank shell + copies ① building blocks to **assemble on the spot**. "Which control to use" is decided at **authoring time** by consulting the selection table and frozen into the manifest; generation time only copies.

---

## ① In-card component building blocks (components · `components/`)

> These are the small controls assembled inside function cards. Grouped into four sets by "what they look like and where they go" — **A is the row container, B/C are control bodies, D is auxiliary.**

### A. Row container (standard row that holds one control)

| Piece | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Labeled control row** (`toggle.html`) | Standard labeled toggle row: title on the left, native switch on the right. **Highest frequency** | ✅ Universal | Copy into card body (`.function-content`); one row per toggle-type setting; fill `{label}`/`{id}-state` |

### B. Compact controls (placed in the right-side slot of a row / card header — **pick one, interchangeable**)

> Toggle and dropdown are **siblings of the same kind**: both go into the `CONTROL` slot on the right side of a `toggle`-derived row / single-control, both aligned right via `margin-left:auto`. Which one to use is decided by the data.

| Piece | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Switch** (toggle · **no separate file**, embedded in `toggle.html`) | Binary on/off (boolean) | ✅ Universal | Default right control of `toggle`; fill `{id}-state`, add `checked`=ON |
| **Dropdown** (`dropdown.html`) | Single-select for **>6 options**, or a declared exception for ≤6 (ordered value-list / long labels / inline slot — e.g. auto-off timeout 15min…8h). Custom `<details>` floating layer, `position:fixed` to escape scroll-container clipping | ✅ Universal | Swap into the `CONTROL` slot of `toggle`/single-control; a ≤6-option dropdown MUST carry a `dropdown-reason` (see `docs/component-selection-rule.md`) |

### C. Full-width controls (span the full row, placed in card body — **cannot go in header**)

| Piece | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Slider** (`slider.html`) | A value along an **ordered** range/step (volume, intensity, Sidetone level) | ✅ Universal | Copy into body; fill `{min}/{max}/{val}`; one `oninput` line drives the value bubble |
| **Segmented selector** (`segmented.html`) | Pick 1 from **2–3 items** in a row, all visible at once / with icons (mode switch: ANC/Transparency) | ✅ Universal | Copy into body; add/remove `.segment` for count; optional conditional panels. **Hard cap: 3** (4+ → preset grid) |
| **Preset grid** (`preset-grid.html`) | **4–6 presets** tiled (EQ presets, audio profiles) | ✅ Universal | Copy into body; 2-column grid; last item can span full row. **Cap: 6** |

### D. Auxiliary

| Piece | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Info tooltip** (`info-tooltip.html`) | ⓘ icon next to a control + hover explanation | ✅ Universal (optional) | Copy into that row's `.function-icons` only when a description exists; delete the div otherwise |

**Which control to use** (full rule in `docs/component-selection-rule.md`; mechanical contract in `archetypes.py`):
on/off → **switch**; ordered continuous value → **slider**; **2–3 → segmented** (hard cap 3); **4–6 → preset grid**; **>6 → dropdown**. A dropdown with ≤6 options is allowed **only** with a declared `dropdown-reason` (`ordered-value` / `long-labels` / `inline-slot`) — otherwise it must be the visible selector for that count.

---

## ② Generic function-card shell (blank card · `function-frame.html`)

> Used when a function has **no card with a matching id in `functions/`** — assemble a new card from scratch using this blank template.

| Piece | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Blank function-card shell** (`function-frame.html`) | A **blank card template**: title + optional ⓘ slot + empty body slot. Copy ① building blocks into the body as needed to assemble a new card | ✅ Universal (catch-all fallback) | `headset-function` copies it, fills the title, then copies ① building blocks in order into `data-slot="components"` |

---

## ③ Swappable-content slots + wiring mechanisms (slot / CSS · embedded in the files above + `headset.css`)

> These are not separate files; they are positions and rules in templates that "can change content / will react."

| Mechanism | What it is / when to use | Universality | How the Agent calls it |
|---|---|---|---|
| **Swappable control slot** (`CONTROL START/END` on the right side of header) | Used when the right-side header control needs to be swapped from the default **switch** to a **dropdown** | ✅ Universal, but **compact controls only**: switch ↔ dropdown (slider/segmented/preset are full-width and cannot enter the header) | Replace the entire `CONTROL` block with a switch or dropdown. **The only authority on swap rules is `toggle.html`**; single-control references it |
| **Two fill slots of the blank shell** (② shell's ⓘ slot / body slot) | Used when assembling a card from the ② blank shell | ✅ Universal | Copy ① building blocks in order into the body slot; only place an info-tooltip in the ⓘ slot when a description exists |
| **Segmented conditional panels** (`segment-panels`, inside segmented/preset) | A group of components **appears** when a segment is selected (select ANC → reveal XYZ) | ✅ Universal (cap: 6) | Expressed structurally: segment N selected → panel N shows, pure CSS `:has()`, 0 JS |
| **Parent-child toggle wiring** (`subfn-group`) | Child components **grey out** when the parent toggle is OFF (Sidetone off → slider greys) | ✅ Universal | Wrap the parent toggle + dependents in `.subfn-group`; pure CSS `:has()` greying |

---

## Maintenance rules (how to update this catalog)

When any of the following happens, update this file **in the same change**:

1. **New building block / shell / slot mechanism** → add a row to the corresponding ①②③ section (what / when / universality / call); update the count in the §0 quick reference.
2. **Rename / delete** → edit/remove the corresponding row; if the old name might be searched for, leave a "(now: …)" note at the old name in [`function-card-architecture.md`](function-card-architecture.md).
3. **Universality change** → update that row's universality flag.
4. **Call-rule change** (routing, swappable-control range, control selection table) → sync `headset/AGENTS.md` + the "How the Agent calls it" column here.
5. **Add/remove function cards** → real usable cards go in `functions/` (id-routed); demos/examples go in `examples/` (not routed); update the corresponding group in the appendix below, keep them separate.
6. Update the "Last updated" date at the top.

> **Constraints that apply to all components**: **no inline `<style>`** inside snippets — styles go entirely in `headset.css` using tokens from `shared/tokens.css`;
> markup is always **copied, not generated**; strip `data-slot`/`data-instruction`/`data-property` markers at generation time;
> **this system does not implement a11y** (no aria/role/keyboard nav/focus-ring, by project preference).

---

## Appendix · Existing function cards (A in `functions/` · B in `examples/`)

> Function cards come in two kinds: **A ready-to-use** (copy directly / fill slots when needed) and **B demo examples** (built during development to validate the architecture — **not product cards**).
> A lives in id-routed `functions/`; **B has been isolated to `examples/`** (not id-routed; gen-subpage does not copy from there).
> Note: even with A cards available, the **other** function cards in a real product still need to be **assembled on demand** using ①②③ — A is just the handful of cards already built.

### A. Ready-to-use cards (in `functions/`, id-routed)

| Card | Controls inside | How to use | Universality |
|---|---|---|---|
| **single-control** | 1 switch | **Universal template** for any "single header control, no content area" function; right control is swappable switch/dropdown (see toggle rules) | ✅ Universal template |
| **eq-audio** | 5 drag points | If the product has an audio equalizer, **use this card directly**; structure is hard-coded, fixed-purpose, limit one per page | ✅ Ready-made card for this function (fixed) |
| **promotion-download** | 2 buttons | Download/promo card; **fill slots** (icon/copy/CTA) to reuse across brands (default happens to be Dell) | ✅ Slot-fill reuse |

### B. Demo examples (in `examples/` · **not id-routed**, built during development to validate the architecture)

| Card | Controls inside | What it actually is | Notes |
|---|---|---|---|
| **collaboration** | 2 switches + 1 slider + ⓘ | **Reference assembly example**: shows how ①② are used to assemble a card | Still referenced as a teaching example by frame/SKILL/README/single-control (pointing to `examples/`) |
| **auto-power-off** | 1 dropdown | **"Swap switch for dropdown" proof card** (validates the swappable control slot) | The only empirical proof of the swap capability |
| **noise-control** | 1 switch + 1 slider | **Simplified test version** for weak-model testing (≠ the real three-mode segmented Noise Control from Figma) | Real three-mode version to be built |

> **Isolated (2026-06-26)**: Group B moved from `functions/` to `examples/` and removed from id routing; 4 teaching references updated
> (frame / SKILL / components README / single-control) + `functions/README` + preview host page; the test model **HS-DEMO**'s
> manifest updated to reference Group A real cards (`eq-audio` + `promotion-download`); old generated pages deleted (can be regenerated with gen-subpage).
> Result: teaching examples / swap proof preserved; id registry contains only real usable cards.
