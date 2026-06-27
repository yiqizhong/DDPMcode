# Bug Report: Canceling Strength does not grey out when Mic Noise Canceling is OFF

**Date:** 2026-06-26
**Model:** WL327 — Dell Pro 3 Wireless ANC Headset
**File affected:** `headset/models/WL327/audio-settings.html`
**Manifest affected:** `headset/models/WL327/audio-settings.manifest`
**Status:** Open

---

## Symptom

The Canceling Strength segmented control (Low / Medium / High) remains fully interactive and fully opaque when the Mic Noise Canceling toggle is switched to OFF. It should grey out and become non-interactive.

---

## Expected Behavior

Per product requirement:
> *"when the Mic noise canceling is off, the canceling strength is not workable."*

`headset.css` (line 893) implements this via:

```css
.subfn-group:has(.subfn-toggle:not(:checked)) .subfn-child {
  opacity: 0.4;
  pointer-events: none;
}
```

This requires `.subfn-toggle` and `.subfn-child` to both be **descendants of the same `.subfn-group`**.

---

## Root Cause

Two compounding failures:

### Failure 1 — Invalid manifest (authoring error)

The manifest used `reveals` on a `control-row` archetype:

```yaml
- archetype: control-row
  label: Mic Noise Canceling
  value: true
  reveals:          # SCHEMA VIOLATION: reveals is only valid on segmented | preset-grid
    true:
      - archetype: segmented
        ...
```

The skill schema (`headset-gen-subpage` SKILL.md) explicitly states `reveals` is only legal on selector archetypes (`segmented` | `preset-grid`). A `control-row` is a boolean toggle. Its toggle-dependency relationship is expressed by HTML structure (`.subfn-group` wrapper), not by a `reveals` entry in the manifest. The validation rule says: **HALT when `reveals` appears on a non-selector archetype**.

### Failure 2 — Validation skipped (generation error)

The agent did not HALT. It recognized the semantic intent and tried to implement it, producing a structurally wrong `.subfn-group` placement:

```
.function-content
  ├── .function-header          ← .subfn-toggle lives HERE (outside .subfn-group)
  │     └── input.subfn-toggle
  └── .subfn-group              ← sibling of .function-header; :has() never finds the toggle
        └── .segmented-group.subfn-child
```

The CSS selector `.subfn-group:has(.subfn-toggle:not(:checked))` never matches because `.subfn-toggle` is not a descendant of `.subfn-group`.

### Failure 3 — Schema expressiveness gap (deeper contributing cause)

The two failures above are mechanical. The deeper reason the wrong choice was made is that **the manifest schema has no first-class field for the toggle→dependent grey-out relationship.**

- For selector reveals, the schema offers an explicit, documented field: `reveals:`.
- For the `.subfn-group` toggle dependency, there is **no manifest field at all** — it exists only as a structural/assembly convention (`components/README.md` lines 114–128, and the `slider.html` snippet comment that says "if this slider is a sub-function of a toggle, wrap it in a `.subfn-group`").

So at authoring time there was a clean, named keyword (`reveals`) sitting right there, and **nothing obvious** to express "this toggle owns these dependents." The schema actively nudged the author toward the wrong construct. `components/README.md` lines 111–112 even warn that the two are different mechanisms — but the schema provides a slot for only one of them.

**Implication:** fixing only this model's HTML + manifest will not prevent recurrence. The same misauthoring is the path of least resistance for any future toggle-with-dependents, until the schema gains an explicit way to declare the `.subfn-group` dependency (e.g. an `owns:` / `dependents:` field on a `control-row`, parallel to `reveals:` on a selector).

### Failure 4 — Dropped component label ("Canceling Strength" is missing)

**Symptom:** the requirement explicitly names the sub-function — *"Mic noise canceling has its sub function, which is **canceling strength**... 3 modes: low, medium, high."* — but the rendered control is bare Low / Medium / High buttons with **no heading anywhere**. A grep for "Canceling Strength" in `audio-settings.html` returns nothing.

**The manifest captured it correctly:**
```yaml
- archetype: segmented
  label: Canceling Strength   # ← provided, but had nowhere to render
  options: [Low, Medium, High]
```

**Why it was dropped — verified against the snippets:**

- `segmented.html` (header, line 3) documents its fill slots as **only** `{id}`, `{labelN}`, `{valueN}` — there is **no control-level title slot**.
- `slider.html` likewise fills only `{min}`/`{max}`/`{val}` — no title slot (the ANC Strength slider in Noise Control is also headingless: just `1 … 5`).
- `control-row.html` is the **only** component with a label (`.function-label`), but its comment requires the right-side widget to be a **compact** control (switch / dropdown): *"Slider, segmented, and preset-grid are full-width controls and must NOT be placed in .function-header."*

**Root reason (architectural):** the function-card architecture provides a title in exactly two places — (1) the **function card** itself (`.function-title-text`), and (2) a **control-row** label for a *compact* right-side widget. There is **no construct for a labeled full-width component** — a named `segmented`/`slider`/`preset-grid` that is not the card's sole control. The architecture assumes each full-width selector is the one main control of its card, so the **card title** labels it (that's why ANC/OFF needs no label). "Canceling Strength" is exactly the unsupported case: a named sub-function containing a full-width 3-mode selector, sitting beneath another control in the same card. The flat `segmented` atom has nowhere to put that title, so `label: Canceling Strength` was silently dropped.

**This is the same root as Failure 3 — flattening of a 2-level requirement.** The Collaboration requirement is genuinely two levels deep:
```
Collaboration (function)
  └─ Mic Noise Canceling (sub-function: title + toggle)
       └─ Canceling Strength (sub-sub-function: title + 3-mode selector)
```
The atoms are essentially flat (function → control). Forcing 2-level nesting into flat atoms loses the **intermediate level's metadata** — its toggle-dependency (Failure 3) *and* its title (Failure 4). The architecture *does* have a titled, nestable container — a **function card** (`{ function: <id> }` via `reveals`, recursive) — but the manifest flattened the sub-function into a label-less `segmented` atom instead of modeling it as a nested card.

**Root cause in one line:** the requirement is a nested sub-function with its own title, but the only titled container in the architecture is a function card; modeling it as a flat `segmented` component left its title (`Canceling Strength`) with no rendering slot, so it was dropped.

---

## Why the Validation Was Skipped

The HALT directive is text in `SKILL.md` — it has no mechanical enforcement. The LLM agent, trained to complete tasks helpfully, pattern-matched the `reveals` entry to a known intent ("toggle should reveal a component") and bridged the schema gap with reasoning rather than stopping. **Helpfulness pressure overrode schema compliance.**

This is the same failure mode the DDPM "copy, don't create" principle is designed to prevent. For structural constraints (no snippet → no output) compliance is harder to reason around. For text-only rules (HALT), it is not.

---

## Fix Required

### 1. Correct the manifest — remove `reveals` from `control-row`

```yaml
- archetype: control-row
  label: Mic Noise Canceling
  value: true
  # no reveals — toggle dependency is expressed by .subfn-group structure in HTML
```

### 2. Correct the HTML — `.subfn-group` must wrap both the toggle row and the dependent control

**Wrong (current):**
```html
<div class="function-content">
  <div class="function-header">               <!-- toggle is here -->
    ...
    <input class="switch-input subfn-toggle" checked>
    ...
  </div>
  <div class="subfn-group">                   <!-- sibling — :has() cannot reach toggle -->
    <div class="segmented-group subfn-child">
      ...
    </div>
  </div>
</div>
```

**Correct:**
```html
<div class="function-content">
  <div class="subfn-group">                   <!-- wraps BOTH toggle and child -->
    <div class="function-header">             <!-- toggle inside .subfn-group -->
      ...
      <input class="switch-input subfn-toggle" checked>
      ...
    </div>
    <div class="segmented-group subfn-child"> <!-- greys out when toggle is OFF -->
      ...
    </div>
  </div>
</div>
```
