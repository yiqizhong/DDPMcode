# Debug Log — Device Settings Generation (WL327)
**Date:** 2026-06-27  
**Session:** Device Settings page generated for the first time from new PRD

---

## Issue 1 — Audio Settings page missing Device Settings nav link

**Status:** CONFIRMED  
**Location:** `audio-settings.html` lines 88–99

**Root cause:** `audio-settings.html` was a pre-existing page generated in a prior session, before Device Settings existed in `home.manifest`. When `home.manifest` was updated to add Device Settings this session, `audio-settings.html` was never regenerated. Its `feature-nav-collapsed` block still reflects the single-feature state and contains only the Audio Settings button.

**Evidence:** `audio-settings.html:88–99` — only one `<a class="feature-button feature-button--collapsed">` present.

**Fix path:** Regenerate `audio-settings.html` via `@skills:headset-gen-subpage WL327 audio-settings`. The skill reads `home.manifest.features[]` as the source of truth for the nav, so re-running it picks up Device Settings automatically.

---

## Issue 2 — Selected segmented control icon stays black

**Status:** CONFIRMED  
**Location:** `headset.css` lines 1011–1013 vs. SVG `fill` attributes in `audio-settings.html`

**Root cause:** The CSS selected state sets `color: var(--color-surface)` on `.segment-icon`. But the SVG `<path>` elements inside the icon use hardcoded `fill="#0E0E0E"`. CSS `color` only affects SVG fill when the SVG uses `fill: currentColor` — hardcoded hex values ignore it entirely. The segment label text (`segment-label`) works correctly because it is a text node that respects `color`. The icon paths do not.

**Deep analysis — why `color` is ignored:**

CSS `color` and SVG `fill` are two separate properties and do not automatically link.

- The CSS rule sets the `color` property on `.segment-icon`. This affects text color and anything that explicitly inherits from `color`.
- An SVG `<path fill="#0E0E0E">` has its fill set as a **presentation attribute** directly on the element. Presentation attributes sit at a lower specificity than CSS properties, but only the `fill` CSS property can override an SVG fill attribute — the `color` property **never affects `fill`** regardless of specificity.
- The opt-in is `fill="currentColor"`: this CSS keyword tells SVG "use whatever the `color` property resolves to." With it, the path inherits from `color` and the selected-state override works. With a hardcoded hex value, the path is wired to that color and ignores `color` entirely.
- The CSS rule *does* execute — it sets `color` on the container — but since none of the SVG paths inside use `fill="currentColor"`, nothing visually changes.

**Evidence:**
- `headset.css:1011–1013`:
  ```css
  .segment:has(.segment-input:checked) .segment-icon {
    color: var(--color-surface);
  }
  ```
- SVG path in `audio-settings.html:125`: `fill="#0E0E0E"` (hardcoded, ignores `color`)

**Fix path:** Change the SVG `<path fill="#0E0E0E">` inside icon segmented controls to `fill="currentColor"`, so the CSS `color` override propagates to the fill on selection.

---

## Issue 3 — Auto Off not in function card shell; no CSS applied

**Screenshot:** `screenshots/device-settings-bug.png`  
![Device Settings broken rendering](screenshots/device-settings-bug.png)

**Status:** CONFIRMED  
**Location:** `device-settings.html` — hand-written, wrong structure

**Root cause (two problems):**

1. **Structural mismatch.** The correct inner structure (per `single-control.html` and `audio-settings.html`) is:
   ```html
   <div class="function-container">
     <div class="function-top-section">
       <div>                          <!-- anonymous wrapper — required -->
         <div class="function-header">
           <div class="function-title">
             <p class="function-title-text">...</p>
   ```
   My hand-written version used `<h3 class="function-name">` directly inside `function-top-section` and placed `function-content` as a *sibling* of `function-top-section` rather than nesting both inside the anonymous `<div>`. `headset.css` targets the nested structure; the mismatch means card styles do not apply.

2. **Wrong CSS class for the title.** Used `h3.function-name` — not a `headset.css` class. Should be `p.function-title-text` inside `.function-title` inside `.function-header`.

**Deep analysis — exactly why the card doesn't render:**

The CSS rules that produce the white card are:
```css
/* headset.css:487–493 */
.function-top-section {
  border-radius: var(--radius-card);
  border: 1px solid var(--color-surface);
  background: var(--color-surface);   /* ← white card background */
}

/* headset.css:495–503 */
.function-top-section > div {
  padding: 16px;                       /* ← internal spacing */
}
```

What my hand-written HTML produced:
```html
<div class="function-top-section">
  <h3 class="function-name">Auto Off</h3>   <!-- h3, not a div — .function-top-section > div never matches → NO padding -->
</div>
<div class="function-content">              <!-- sibling of function-top-section → OUTSIDE the card -->
  <div class="function-header">             <!-- dropdown renders here, off-card on gray background -->
```

Two cascading failures:
- `.function-top-section > div` never matches because there is no `<div>` child — only an `<h3>`. So no 16px padding; the title is edge-flush inside the card.
- `function-content` is a **sibling** of `function-top-section`, placed entirely outside the white card. The dropdown row renders on the raw gray page background with no card border, no background, no padding.

**Root cause (process):** `device-settings.html` was hand-written instead of routing through `@skills:headset-function`, which would have copied `function-frame.html` as the shell and produced the correct structure. This is a direct violation of the AGENTS.md rule: *"never hand-roll an ad-hoc function from a description."*

**Fix path:** Delete the hand-written function cards in `device-settings.html` and regenerate both functions via the assembled path (`@skills:headset-function`), which copies `function-frame.html` and fills it strictly from manifest params.

---

## Issue 4 — Promotion template not used; dell-audio-promotion assembled from scratch

**Status:** CONFIRMED  
**Location:** `functions/promotion-download.html` — snapshot exists but was not used

**Root cause:** The manifest was written with `id: dell-audio-promotion`. At generation time, the skill looked for `functions/dell-audio-promotion.html` — not found. So it fell through to the assembled (no-snapshot) path and the function was hand-constructed. 

But `functions/promotion-download.html` **already exists** as a ready-to-copy snapshot. The `functions/README.md` keyword table explicitly maps `"promotion"` → `promotion-download`. The correct authoring action was to set the manifest `id` to `promotion-download` — then the snapshot would have been copied verbatim with no hand-writing needed.

**Evidence:**  
- `functions/README.md:45`: `download dell audio · promotion · qr code` → `promotion-download`  
- `functions/promotion-download.html` — complete card with `.promo-body`, `.promo-cta`, close button

**Deep analysis — why EQ was found but promotion was not:**

The skill routes by **exact filename match only** (architecture D8 — id-only routing). At generation time:

> look for `functions/<manifest.id>.html` — if it exists, copy it; if not, assemble from scratch.

There is no fuzzy matching, no keyword inference, no name similarity check at generation time.

| Function | Manifest `id` set | Snapshot filename | Match? | Result |
|---|---|---|---|---|
| EQ | `eq-audio` | `functions/eq-audio.html` ✅ exists | Exact | Copied verbatim |
| Promotion | `dell-audio-promotion` | `functions/dell-audio-promotion.html` ❌ does not exist | None | Hand-assembled |

`eq-audio` was set correctly because it is intuitive and self-describing — easy to guess right. `promotion-download` is not guessable from the phrase "Dell audio promotion" — the correct id must come from the `functions/README.md` keyword table, which maps:

> `"promotion" · "download app" · "qr code" · "mobile app download"` → `promotion-download`

The manifest was written without consulting that table, so the id was invented (`dell-audio-promotion`) rather than looked up (`promotion-download`).

**Process gap:** Always read `functions/README.md` before setting a function `id` in any manifest. That is the only place the id→snapshot mapping is defined. An invented id that has no snapshot silently falls through to the assembled path — no error is raised at authoring time.

**Fix path:** Change `device-settings.manifest` function id from `dell-audio-promotion` to `promotion-download`. Regenerate. The snapshot gets copied as-is; the manifest can optionally override `data-property` value slots (title, description, cta label).

---

## Issue 5 — Wrong control type invented for Dell Audio Promotion (toggle added incorrectly)

**Status:** CONFIRMED  
**Location:** `device-settings.manifest` — `archetype: toggle` on `dell-audio-promotion`; `device-settings.html` — hand-written toggle row

**Root cause:** The PRD requirement was ambiguous: *"Dell audio promotion."* — no control type specified. Without consulting `functions/README.md` or the snapshot, the control was invented by guessing from the requirement text. "Promotion" sounded like a feature that could be enabled/disabled, so `archetype: toggle` was authored into the manifest.

**Why this is wrong:** Reading `functions/promotion-download.html` reveals the actual intended design has **no toggle at all**. It is a fixed informational card:

```
[ App icon ]  [ Description text        ]
[ View QR Code button ]         [ × close ]
```

The user can dismiss the card (close button), not toggle it on/off. There is no boolean state.

**Root cause chain:**
1. PRD requirement was vague — no control type given
2. `functions/README.md` was not consulted → snapshot not found → actual design not seen
3. Toggle invented from the word "promotion" sounding like a configurable setting
4. `archetype: toggle` written into `device-settings.manifest` — wrong control entirely
5. Toggle row hand-written into `device-settings.html` — compounds Issue 3 (hand-written structure)

**Relationship to Issue 4:** This is a downstream consequence of Issue 4. If `functions/README.md` had been read first, the id `promotion-download` would have been used, the snapshot would have been copied, and no control type would have needed to be authored — the snapshot defines its own fixed structure with no toggle.

**Fix path:** Remove `components` entirely from the `dell-audio-promotion` function entry in the manifest (snapshots carry their own structure — no `components` needed). Set `id: promotion-download`. The toggle row in `device-settings.html` is also removed when the page is regenerated from the corrected manifest.

---

## Summary

| # | Issue | Confirmed? | Fix |
|---|---|---|---|
| 1 | Audio Settings missing Device Settings nav | ✅ | Regenerate `audio-settings.html` |
| 2 | Selected segment icon stays black | ✅ | Change SVG `fill` to `currentColor` |
| 3 | Auto Off not in card shell / no CSS | ✅ | Delete hand-written cards; use `headset-function` assembled path |
| 4 | Promotion snapshot not used | ✅ | Change manifest `id` to `promotion-download` |
| 5 | Toggle invented for promotion (wrong control) | ✅ | Remove `components` from manifest; use `promotion-download` snapshot (no toggle) |
