# WL527 Debug Log

---

## Bug 1 — Device image: absolute Windows path embedded in HTML

**Stage where mistake happened:** HTML generation

**Affected files:**
- `headset/models/WL527/index.html` line 61
- `headset/models/WL527/audio-settings.html` line 61
- `headset/models/WL527/automated-actions.html` line 61
- `headset/models/WL527/device-settings.html` line 61

**Source of truth:** `Untitled 2.md` line 11:
```
- Image: C:\Users\Yiqi_Zhong\Downloads\5027.png
```

**What was generated (wrong):**
```html
<img src="C:\Users\Yiqi_Zhong\Downloads\5027.png" alt="Dell Pro 5 Wireless ANC Headset">
```

**What should have been generated:**
```html
<img src="images/5027.png" alt="Dell Pro 5 Wireless ANC Headset">
```

**What the agent should have done:** On reading a local file path from the requirements, copy the image file into the model folder (`headset/models/WL527/images/`) and reference it with a relative path. Instead it pasted the raw absolute Windows path directly as an `src` attribute.

**Effect:** Broken image on any machine other than the original author's, or if the file is moved out of Downloads.

**Fix applied:** Copied `5027.png` → `headset/models/WL527/images/5027.png` and updated all four `<img src>` references to `images/5027.png`.

---

## Bug 2 — Walkthrough steps: fake placeholder image used instead of light-gray box

**Stage where mistake happened:** Manifest authoring (then HTML generation faithfully reproduced it)

**Affected files:**
- `headset/models/WL527/walkthrough.manifest` lines 7, 10, 13
- `headset/models/WL527/walkthrough.html` (all three `.wt-media` blocks)

**Source of truth:** `Untitled 2.md` lines 44, 49, 54 — all three `Image:` fields are empty:
```
### Step 1
- Image:

### Step 2
- Image:

### Step 3
- Image:
```

**Rule violated:** `.agents/skills/shared-gen-walkthrough/SKILL.md`:
> *"When a step has no `image` key the renderer drops the `<img>` but KEEPS the `.wt-media` box as a uniform light-gray placeholder (`--color-surface-muted`)"*

**What was authored in the manifest (wrong):**
```yaml
- title: Multimedia Presets
  body: ...
  image: ../../../headset/assets/dell-audio-icon.png   ← invented substitute
- title: Convenient Buttons
  body: ...
  image: ../../../headset/assets/dell-audio-icon.png   ← invented substitute
- title: Active Noise Cancellation
  body: ...
  image: ../../../headset/assets/dell-audio-icon.png   ← invented substitute
```

**What should have been in the manifest:**
```yaml
- title: Multimedia Presets
  body: ...
  # no image field at all
- title: Convenient Buttons
  body: ...
  # no image field at all
- title: Active Noise Cancellation
  body: ...
  # no image field at all
```

**What should have been generated in HTML (per skill rule):**
```html
<div class="wt-media">
  <!-- no <img> — CSS renders this as --color-surface-muted light-gray box -->
</div>
```

**Status:** Not yet fixed.

---

## Bug 3 — "Custom" preset button missing `segment--span`

**Stage where mistake happened:** HTML generation

**Affected file:** `headset/models/WL527/audio-settings.html` line 360

**Rule violated:** `.agents/skills/headset-shared/components/preset-grid.html` line 10:
> *"Add `.segment--span` to the last item to make it span the full row width (e.g. 'Custom')."*

The snippet's own last `<label>` (line 45) is shown as:
```html
<label class="segment segment--span">
```
It even uses "Custom" as the explicit example.

**What was generated (wrong):**
```html
<label class="segment">
    <input type="radio" name="multimedia-preset" value="custom" class="segment-input">
    <span class="segment-label">Custom</span>
</label>
```

**What should have been generated:**
```html
<label class="segment segment--span">
    <input type="radio" name="multimedia-preset" value="custom" class="segment-input">
    <span class="segment-label">Custom</span>
</label>
```

**Effect:** "Custom" occupies only the left half of the second row instead of spanning full width.

**Status:** Not yet fixed.

---

## Bug 4 — EQ snapshot not copied into Custom panel

**Stage where mistake happened:** HTML generation

**Affected file:** `headset/models/WL527/audio-settings.html` lines 368–370

**Manifest instruction (correct):** `headset/models/WL527/audio-settings.manifest` lines 53–55:
```yaml
        reveals:
          custom:
            - {function: eq-audio}
```

**Snapshot that should have been copied:** `.agents/skills/headset-gen-subpage/templates/functions/eq-audio.html` (196 lines — full interactive 5-band EQ with Catmull-Rom spline, drag handles, gradient fill, and inline JS)

**What was generated (wrong):**
```html
<div class="segment-panel">
    <!-- EQ function would be inserted here from eq-audio snapshot -->
</div>
```

**What should have been generated:** The full 196-line content of `eq-audio.html` copied verbatim inside the `segment-panel` div.

**How the failure happened:** The agent recognized the `{function: eq-audio}` reference, acknowledged the snapshot existed in a comment, then stopped — narrating the action it should have taken instead of taking it. `eq-audio.html` was never opened and its content was never inserted.

**Effect:** Selecting "Custom" reveals an empty white panel — no EQ controls appear.

**Status:** Not yet fixed.

---

## Bug 5 — Sidetone slider not greyed out when Sidetone is OFF

**Stage where mistake happened:** HTML generation (manifest was correct)

**Affected file:** `headset/models/WL527/audio-settings.html` lines 304–336

**Product requirement:** `Untitled 2.md` line 22:
> *"user can adjust sidetone when it's on"* — slider must grey out when toggle is OFF.

**Manifest (correct):** `headset/models/WL527/audio-settings.manifest` lines 35–43:
```yaml
      - archetype: toggle
        label: Sidetone
        value: false
        dependents:
          - archetype: slider
            label: Sidetone Level
            min: 1
            max: 3
            value: 2
```

**Rule violated:** `.agents/skills/headset-shared/components/slider.html` lines 5–6:
> *"If this slider is a toggle's dependent (manifest `dependents`), wrap it in a `.subfn-child` div inside the toggle's `.subfn-group` so it greys out when the toggle is OFF."*

**What was generated (wrong) — flat siblings, no wrapping:**
```html
<div class="function-header">
    <p class="function-label">Sidetone</p>
    <label class="switch">
        <input type="checkbox" class="switch-input">
        ...
    </label>
</div>
<div class="slider-row">           ← flat sibling, no CSS link to toggle state
    <p class="slider-label">1</p>
    <div class="slider-input-wrap">...</div>
    <p class="slider-label">3</p>
</div>
```

**What should have been generated — wrapped in `.subfn-group` + `.subfn-child`:**
```html
<div class="subfn-group">
    <div class="function-header">
        <p class="function-label">Sidetone</p>
        <label class="switch">
            <input type="checkbox" class="switch-input">
            ...
        </label>
    </div>
    <div class="subfn-child">      ← CSS: greys out when toggle is unchecked
        <div class="slider-row">
            <p class="slider-label">1</p>
            <div class="slider-input-wrap">...</div>
            <p class="slider-label">3</p>
        </div>
    </div>
</div>
```

**Effect:** Slider is always active regardless of toggle state — user can drag it even when Sidetone is OFF.

**Status:** Not yet fixed.

---

## Bug 6 — Duplicate label on Auto Off, Audio Guidance, Busy Light

**Stage where mistake happened:** Manifest authoring — HTML generation was not at fault (it faithfully rendered what the manifest described)

**Affected files:**
- `headset/models/WL527/device-settings.manifest` lines 8, 27, 41
- `headset/models/WL527/device-settings.html` lines 147+168, 259+280, 326+346

**Product requirement:** `Untitled 2.md` lines 32–34 — plain on/off controls, no sub-hierarchy:
```
1. Auto OFF, user can turn it on or off.
2. Audio Guidance. user can turn it on or off.
3. Busy Light. user can turn it on or off
```

**Architecture rule:** `docs/function-card-architecture.md` §6.6:
> *"Standard component framework: Title (function name) on the left, component (Toggle/Dropdown) on the right."*
The card `title` IS the toggle's label. A standalone primary toggle does not get a second `label` field.

**What was authored in the manifest (wrong) — example: Auto Off:**
```yaml
- id: auto-off
  title: Auto Off        ← card title → renders as function-title-text
  tooltip: "..."
  components:
    - archetype: toggle
      label: Auto Off    ← component label → renders as SECOND function-label row (duplicate)
      tooltip: "..."
      value: true
```

**What should have been in the manifest:**
```yaml
- id: auto-off
  title: Auto Off        ← only this; no label field on the toggle component
  tooltip: "..."
  components:
    - archetype: toggle
      value: true
      dependents: [...]
```

**What was rendered in HTML (wrong) — two "Auto Off" rows:**
```html
<p class="function-title-text">Auto Off</p>   ← row 1 (card title)
...
<p class="function-label">Auto Off</p>         ← row 2 (duplicate sub-label)
```

**Effect:** Each card visually shows the function name twice — once as the large card title and once as a sub-label on the toggle row.

**Status:** Not yet fixed.

---

## Bug 7 — Download Dell Audio: invented CSS class name

**Stage where mistake happened:** HTML generation

**Affected file:** `headset/models/WL527/device-settings.html` (Download Dell Audio section)

**CSS file checked:** `headset/headset.css` — has **no `.download-button` class** anywhere. The only promotion-related rule is `.function-close` (line 657), which is for the card's close button layout, not for a CTA button.

**What was generated (wrong):**
```html
<button class="download-button" type="button">Download Dell Audio</button>
```

**Effect:** Renders as an unstyled browser-default button — no brand color, no border-radius, no padding from the design system.

**Root cause:** The agent invented `download-button` from imagination without reading `headset.css` to verify what button classes exist.

**Status:** Not yet fixed.

---

## Bug 8 — Walkthrough buttons: invented CSS class names

**Stage where mistake happened:** HTML generation

**Affected file:** `headset/models/WL527/walkthrough.html` (all `.wt-nav` sections)

**CSS file checked:** `shared/walkthrough.css` — actual button classes defined (lines 152–203):
- `.wt-btn` — base style (all buttons)
- `.wt-next` — primary blue Next button
- `.wt-done` — primary blue final CTA
- `.wt-back` — icon-only back, accent-outlined
- `.wt-skip` — tertiary, transparent
- `.wt-btn-arrow` — arrow icon inside a button

**What was generated (wrong):**
```html
<button class="wt-button wt-button--primary">Next <svg>...</svg></button>
<button class="wt-button wt-button--tertiary">Skip</button>
<button class="wt-button wt-button--icon-only"><svg>...</svg></button>
```

None of `wt-button`, `wt-button--primary`, `wt-button--tertiary`, `wt-button--icon-only` exist in any stylesheet.

**What should have been generated (step 1 — Next + Skip):**
```html
<button class="wt-btn wt-next">Next <span class="wt-btn-arrow"><svg>...</svg></span></button>
<button class="wt-btn wt-skip">Skip</button>
```

**What should have been generated (steps 2+ — Back + Next + Skip):**
```html
<button class="wt-btn wt-back"><svg>← arrow</svg></button>
<button class="wt-btn wt-next">Next <span class="wt-btn-arrow"><svg>→ arrow</svg></span></button>
<button class="wt-btn wt-skip">Skip</button>
```

**What should have been generated (last step — Back + CTA, no Skip):**
```html
<button class="wt-btn wt-back"><svg>← arrow</svg></button>
<button class="wt-btn wt-done">Finish</button>
```

**Root cause:** Same as Bug 7 — the agent invented a BEM naming convention (`wt-button--primary` etc.) without reading `walkthrough.css` to find the actual class names first.

**Status:** Not yet fixed.

---

## Bug 9 — "Sensor Sensitivity" label not rendered above segmented control

**Stage where mistake happened:** HTML generation (manifest was correct)

**Affected file:** `headset/models/WL527/automated-actions.html` lines 191–201

**Product requirement:** `Untitled 2.md` line 28:
> *"under Wear Detection, it has Sensor Sensitivity, two modes: Low and Normal"*

**Manifest (correct):** `headset/models/WL527/automated-actions.manifest` lines 12–16:
```yaml
          - archetype: segmented
            label: Sensor Sensitivity     ← explicitly named
            options:
              - {label: Low, value: low}
              - {label: Normal, value: normal, selected: true}
```

**Rule violated:** `.agents/skills/headset-shared/components/segmented.html` lines 30–32:
> *"If this control is a named sub-function (has a `label` and sits in a toggle's `.subfn-child`), render `<p class="subfn-label">{label}</p>` as the first child of that wrapper, above this group."*

**What was generated (wrong) — label used only for `name` attribute, never rendered visually:**
```html
<div class="segmented-group">
    <div class="segmented-control">
        <label class="segment">
            <input type="radio" name="sensor-sensitivity-mode" ...>   ← label used here only
            <span class="segment-label">Low</span>
        </label>
        <label class="segment">
            <input type="radio" name="sensor-sensitivity-mode" value="normal" checked>
            <span class="segment-label">Normal</span>
        </label>
    </div>
</div>
```

**What should have been generated:**
```html
<p class="subfn-label">Sensor Sensitivity</p>   ← missing — required by snippet rule
<div class="segmented-group">
    <div class="segmented-control">
        <label class="segment">
            <input type="radio" name="sensor-sensitivity-mode" ...>
            <span class="segment-label">Low</span>
        </label>
        <label class="segment">
            <input type="radio" name="sensor-sensitivity-mode" value="normal" checked>
            <span class="segment-label">Normal</span>
        </label>
    </div>
</div>
```

**Root cause:** The agent treated `label` as a single-purpose technical key — it derived the radio `name` attribute (`sensor-sensitivity-mode`) from it, proving the value was read. But the `label` field is dual-purpose: it also requires a visible `<p class="subfn-label">` paragraph above the control. The agent satisfied the mechanical use and silently dropped the presentational one. Same pattern as Bug 5.

**Effect:** The Low/Normal buttons appear with no heading — the user cannot tell what they control.

**Status:** Not yet fixed.

---

## Status summary

| Bug | Fixed? |
|-----|--------|
| Absolute image path in HTML | Yes |
| Fake placeholder in walkthrough | No |
| `segment--span` dropped on Custom button | No |
| EQ snapshot comment instead of paste | No |
| Sidetone slider not greyed out when OFF | No |
| Duplicate label on Auto Off / Audio Guidance / Busy Light | No |
| Download Dell Audio: invented CSS class name | No |
| Walkthrough buttons: invented CSS class names | No |
| "Sensor Sensitivity" label not rendered | No |
