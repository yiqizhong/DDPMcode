# Function Card Architecture · Design Discussion and Decision Record

> **Nature of this document**: This is not a final spec; it is a **thinking log / design journal**.
> It faithfully records the discussions — spanning dozens of turns — around "what exactly is a function card inside a sub-page, how is it organized, how does it interact": what was proposed at each step, what options were considered, the points of contention, the decisions made, and **several times I reversed my own judgment**. Written intentionally in a verbose, rich style, prioritizing fidelity over brevity.
>
> **Status**: The architecture is still converging; the "To-do / Open items" at the end lists what has not yet landed. **The codebase is the source of truth**;
> where it conflicts with [`methodology.md`](methodology.md), the codebase wins (parts of that methodology are now outdated).
>
> **How to read**: §0 provides the starting point; §1–8 are the discussion evolution in chronological order; §4 and §5 are the two disputes you called out for separate recording (Skill/Snippet/Snapshot, and Slot vs other forms); §9 is the current converged model; §10 is
> the decision log (including revoked decisions); §11 to-do; §12 glossary.

---

## 0. Starting point and background

### 0.1 Three-layer architecture and "the codebase is the source of truth"

The entire product UI generation system has three layers:

- **Design-token layer** `shared/tokens.css` — visual constants (color/font/radius/shadow etc.), shared across all categories, rarely changes.
- **Category-template layer** — each category's (headset/mouse/…) own page skeleton + layout styles; headset is the pilot.
- **Model-data layer** — one manifest per concrete model + the content-baked finished pages that are generated from it.

There is an external methodology document (`docs/methodology.md`, "Product UI Generation Methodology v1.0") that is **a reference, not law**. Parts of its framework are now outdated; **the codebase wins on any conflict**. Confirmed divergences:
- §9.5 nests skills inside the category directory; **the codebase lays all skills flat at the repo root** `.agents/skills/`, named with a `<category>-...` prefix (Devin only discovers `SKILL.md` at depth 1; nesting empirically failed, 2026-06-24).
- The methodology uses "Mouse" as an example; **the real pilot is headset**.
- §3 favors `data-instruction` to let the AI generate; **the codebase is stricter: markup is always copied verbatim from pre-written snippets, never generated from a description**; unknown enum → HALT and ask.

### 0.2 Code state before the discussion started

Before the "function card" discussion, the headset category had only 4 skills:
- `headset-gen-homepage` — generates the home page `index.html` from `home.manifest`.
- `headset-gen-subpage` — generates any sub-page from a sub-page manifest (one framework for all sub-pages).
- `headset-control-generic` — **fallback generator for unknown controls** (§9.4 fallback).
- `headset-shared` — not a skill; shared snippets: `connection/` (wired/bluetooth/unpair), `icons/`, `feature-button.html`.

The registry `headset-gen-subpage/templates/controls/` was **empty at that point** (README only); `headset/models/` had no real manifest; icons had only `audio.svg`.

### 0.3 Methodology sections referenced (throughout)

- **§3 Slot mechanism**: templates leave only "empty slots + markers"; data is filled at generation time.
- **§4 Variant**: pick one from a finite, mutually exclusive enum (e.g. connection type wired/bluetooth); discrete state machine, select the matching whole block per enum.
- **§5 List**: a same-kind set of indefinite count (e.g. 2/3/4 feature buttons); data-driven loop rendering.
- **§5.2 Registry**: each thing defined once, referenced by id, prevents drift.
- **§9.3**: a sub-page needs no dedicated skill; one framework skill + manifest is enough.
- **§9.4 Control layer**: known → snippet/skill with preset template; unknown → fallback generation; high-frequency → promote and solidify.
- **§9.7**: strong trigger words + hard routing + explicit invocation + self-check + "copy not create" to prevent weak-model hallucination.

---

## 1. Origin: asking about "feature generated skills"

**Your input (paraphrased)**: The methodology mentions some skills; there was a block for "feature generated skills" used to generate product function/feature capabilities, right? The functions inside sub-page feature content must have a similar skill plan, right?

**Key distinction — "feature" is used at two levels**:
- **Feature Zone / feature buttons (§5)**: the entry buttons on the home page that navigate to sub-pages (Mic Settings, EQ…). These are **list items**, data-driven from `home.manifest`'s `features[]`, copying the same `feature-button.html`. **Not a skill.**
- **The "functions/controls" inside a sub-page (§9.4)**: the interactive elements that actually implement a product function. **This is the block that has a skill plan** = the control layer.

**Conclusion at the time (confirmed)**: The control layer was basically empty — only the fallback `headset-control-generic`, no concrete control snapshots, no dedicated `headset-control-<id>` skill. This is the §9.4 "grow on demand" design: first the framework and fallback; specific controls are added when real manifests appear.

---

## 2. First landing: `control-generic` → `headset-function`

**Your input**: Rename `headset-control-generic` — "Control Generic" is too broad — rename it to **`headset-function`**. Write a template first, since there will be many different functions later, roughly 5, 6, 7, 8 of them.

**My handling and judgment**:
- Note: this skill was originally positioned as "fallback generator for unknown controls"; renaming it + writing a template naturally upgrades it to "a generator that produces a function module per a unified template."
- Performed a **full vocabulary migration from control → function** (the connection zone `control-zone` is a separate concept and was left alone):
  - skill `headset-control-generic` → `headset-function`
  - Registry directory `templates/controls/` → `templates/functions/`
  - Manifest field `controls[]` → `functions[]`; slot `data-slot="controls"` → `data-slot="functions"`
  - Future dedicated skill naming `headset-control-<id>` → `headset-function-<id>`
  - Sync-updated: root `AGENTS.md`, `headset/AGENTS.md`, `README.md`, `headset/models/README.md`, `gen-subpage` SKILL + frame, registry README; `docs/methodology.md` left unchanged (reference only).
- Added `headset-function/templates/function-frame.html` and `.function-module` styles etc. in `headset.css`.

**Function form given at the time = single-line module**: `.function-module` = label + optional description + one affordance area (single line). **⚠️ This form was later proven wrong** (see §5).

**Status**: This batch of renames was `git add`-ed but **never committed** (you then moved into architecture discussion and never returned to this batch; it remains uncommitted as of §11).

---

## 3. Key background input: two-layer architecture + 10–20 functions

**Your input (paraphrased)**: Headset features/functions are usually fixed, roughly **10–20**; they vary by model, but a batch is a standard set like a template. The architecture, as you recalled, is **two layers** (you may have thought of three earlier):
1. **Layer 1: existing template Skills** — generate fixed functions. For example, Collaboration: its layout/structure/internal sub-functions are all pre-designed and fixed; when a new headset requirement mentions Collaboration, invoke the corresponding Skill, copy the template in wholesale, and the template doesn't need to change.
2. **Layer 2: handle new/unknown functions** — when a function name not in the library appears, create a new Skill specifically to build that unknown function.

**My mapping + question at the time**:
- Layer 2 = the `headset-function` we just renamed (comes with a fallback template). Already exists.
- Layer 1 (known-function library) = currently empty; the slot I reserved is the `functions/<id>.html` snapshot registry.
- Raised a structural question: should Layer 1 be "independent skills" or "snapshot files"? Also noted the number should be updated from 5–8 → 10–20; and proposed "pre-building already-designed known functions is not speculative."

---

## 4. [Dispute A] Skill vs Snippet vs Snapshot

> This is one of the two disputes you called out for separate recording. Below: definitions of the three terms, the evolution of your position, the full pros/cons comparison, and the final ruling.

### 4.1 What the three terms actually mean

- **Snapshot / Snippet file**: A piece of **static HTML + value slots** (`data-property=...`), stored in the registry directory (e.g. `functions/collaboration.html` or `headset-shared/connection/bluetooth.html`). `gen-subpage`/`gen-homepage` looks it up by id and **copies + fills values**. It **makes no decisions** — it is simply material to be copied. (In this document "snapshot" and "snippet" are basically synonymous, both referring to this "static material to be copied"; the subtle difference is "snapshot" more strongly implies "the frozen finished appearance of a known thing.")
- **Independent Skill**: A **folder** with a `SKILL.md`, discoverable by Devin, callable via `@skills:`. It can **run logic, make decisions, invoke other skills**, and the folder can hold template snippets and other assets.

**Key insight**: If a known function is "hard-coded and fixed," making it a Skill equals "snapshot file + a SKILL.md wrapper layer + discovery cost" — the wrapper adds no new capability. **A Skill only pays off when it needs to do something a static file cannot (logic/decisions/invoking sub-skills).**

### 4.2 Evolution of your position (recorded faithfully)

- Initially (§3) you described Layer 1 as "invoking the corresponding Skill"; I accordingly recommended "one independent Skill per known function."
- You then asked "what does the snapshot-file registry mean?" — I explained (the snapshot item in 4.1 + the flow of `gen-subpage` looking up by id and copying).
- You then explicitly relaxed: "**Putting the fixed, unchanging content into the function templates under `headset-gen-subpage` is also fine. Copying directly works; even 10 functions is no problem. Actually the logic of both paths is the same, the thinking is the same — it's just a different storage location.**"
- In other words: **Skill vs snapshot is not the deciding factor in this architecture — both paths have the same logic, only the storage location differs**; you lean toward snapshots, and count doesn't matter.

### 4.3 Full pros/cons comparison

**Option A: Snapshot files**

Pros:
- **Zero resident-context cost**: Devin doesn't discover them; their descriptions don't enter the session's opening budget; they only enter context when actually copied. No matter how many there are, they don't cost the session opening.
- **No "AI skips the skill" failure mode**: `gen-subpage` has one hard instruction "copy `functions/<id>.html` by id" — it's a deterministic path lookup; "the AI deciding for itself whether to use it" doesn't exist as a failure surface (the core pain point of §9.7).
- **Lightweight**: one function = one HTML file; no frontmatter/description/procedure/self-check boilerplate. Changing a function = changing that one file.
- **Consistent with the existing codebase**: `connection/*.html`, `feature-button.html`, `icons/*.svg` already work this way — copy snippets, none have independent skills.
- **Unlimited extension without polluting the namespace**: adding the 21st = dropping one file; the skill list doesn't change.

Cons:
- **Cannot hold logic**: can only "copy + fill values"; conditional rendering / invoking sub-skills / multi-step decisions are not possible.
- **Weak self-advertisement**: you need `ls functions/` to know what exists (relies on README/convention); unlike a skill's description announcing "when I should be used."

**Option B: One independent Skill per known function**

Pros:
- **Can hold logic**: SKILL.md can write generation steps, conditional logic, `@skills:` component invocation — suitable for complex functions that need to be assembled on the spot.
- **Self-describing / callable by name**: description states "when to use me"; explicit invocation; the directory is the function directory.
- **Strong isolation**: each function ships its own template + rules + self-check; boundaries are clear.

Cons:
- **Resident context cost × N**: Devin loads each skill's name+description at session start; 10–20 means 10–20 lines always resident, and aggravates "too many skills → choice paralysis" (§9.7.3's own warning).
- **Re-introduces the "AI skips the skill" failure mode**: a skill is "the AI judges for itself whether to invoke it" — exactly the path it will "pretend not to see"; requires strong trigger words + hard routing + self-check to close.
- **Heavy boilerplate**: one full SKILL.md per function; 10–20 to write and maintain.
- **Pure waste for fixed functions**: wrapping a hard-coded function in a skill shell adds cost without adding capability.
- **Inconsistent with the existing pattern**: having "connection blocks use snapshots, functions use skills" running in parallel is exactly drift.
- **Cannot nest**: Devin only recognizes depth-1 (empirically tested); must be laid flat at the root.

### 4.4 Ruling and subsequent refinement

**Ruling criterion (one sentence)**: **function is "fixed, hard-coded material" → snapshot file; function "needs to run generation logic" → Skill.**
- Known functions default to **snapshot/data**; **no skill per function**.
- The only place that needs logic is "assembling unknown functions on the spot" — already covered by **a single** `headset-function` (Layer 2); logic is concentrated in that one skill.
- This is the confirmed "codebase wins" point where "§9.4 says make it a skill, but the codebase changed it to snapshots."

**Subsequent refinement (after §8)**: What is stored as snapshots is **precisely "component snippets" `components/<type>.html`, not whole functions**. A function is no longer a frozen snapshot but "data-driven assembly" (see §5, §9).

---

## 5. [Dispute B] Is it "one whole block" or "a slot list"? (form dispute)

> The other dispute you called out. This section faithfully records the evolution of understanding of "what form a function card actually takes," **including two times I reversed myself**.

### 5.1 Form v1: single-line module (rename round)

In §2 I made a function a single-line `.function-module` (label + description + one affordance). **The error**: treating "function" as a single control.

### 5.2 Form v2: function = one whole Content Area template; and (incorrectly) proposing 1:1

**Your input (paraphrased)**: An independent Skill also has a Template and pre-written HTML; the flow is to look up the corresponding Skill — **this Skill is actually the sub-page, i.e. the content of the Content Area**; look up the Skill by function/content; if it already has a template, copy-paste directly.

Based on this I **inferred 1:1**: one sub-page = one function = one whole Content Area template, and proposed **removing the `functions[]` list**. **⚠️ This step was later overturned by a screenshot (next subsection).** At the time I clearly stated this was an [inference] and asked you to confirm whether it was 1:1.

### 5.3 Form v3: screenshot overturns 1:1 — Content Area is a "function list"

**Your input**: You sent an **Audio Settings** sub-page screenshot and pointed out: it's not 1:1. The Content Area of a sub-page can hold 1/2/3 functions — the count is not fixed. This screenshot has three functions: **Noise Control, Collaboration, Multimedia**.

**This directly proved**:
- One sub-page's (Audio Settings) Content Area = **a list of functions** (variable count), not a single function.
- My previous-round "1:1, remove the list" **is void**; **the original `functions[]` list direction was correct** and should be kept.
- What needs to change: a "function" is **a whole card with a title and multiple components inside** (Collaboration = title + two toggles + slider), not a single line. So the v1 `.function-module`/`function-frame.html` form needs to be upgraded to a "card block."

The four-level hierarchy was therefore fixed: **Feature (home button/sub-page) → Content Area (holds 1~N functions) → Function (titled card) → Component (small controls inside a function).**

### 5.4 Form v4: frozen snapshot doesn't work → data-driven assembly

Until this point I recommended "known function = frozen snapshot, copy as-is." **You exposed this with real cases**:

**Your input (several real use cases)**:
- The next headset has Collaboration and Mic Noise Cancellation but **no Sidetone**. (delete a component)
- Or: has Collaboration but no Mic Noise Cancellation and no Sidetone; it renames Mic Noise Cancellation to **Noise Cancellation** — similar name, but **a completely different function**. (swap for another)
- Noise Control: most products have ANC/Transparency/Off (3 modes); the next one might have a **4th or 5th mode**; or the reverse — **only ANC + Transparency, removing Off**. (option count inside a component is changing)

**I conceded the v4 correction** (this is a granularity refinement, not another reversal; the core principle "fixed structure + differences go into data" didn't change — I just put "fixed" at the wrong layer):
- A "hard-coded collaboration.html" cannot be copied as-is — the moment you copy it you need to delete elements / rename / change option counts, which means patching the copied HTML — fragile and messy.
- **Push "fixed material" down to the component layer**: what's fixed is `components/<type>.html` (the **shape** of toggle/slider/segmented/preset-grid); **function = data-driven assembly** (card shell + copy component snippets per a list).
- **Identity by id, not name**: "looks similar but is not the same thing" → different id → different snippet (unknown → Layer 2 assembles on the spot); never "rename and reuse."
- Your delete/change/add operations are all data changes; the material stays untouched.

### 5.5 Form v5 (converged): recursive slot list

**Your input**: This kind of function card is fundamentally made up of individual "**slots**," arranged top to bottom: what goes in the first slot, the second, the third; sometimes one slot, sometimes two — not fixed.

**I confirmed and added a point: slots are recursive.** This is exactly the methodology's slot (§3) + list (§5) — you rederived it yourself. The entire architecture collapses into **one primitive**:

> **An ordered slot list; what fills each slot is decided by data; the count is variable; it is recursive.**

And: the "slots" you described are the **already-existing `data-slot`** in the templates (the home page `feature-zone` and sub-page `functions` zone are both slots) — now just applied recursively inside function cards. This shows the model is self-consistent: from Content Area down to the innermost component, the only thing happening throughout is "slot + data fill."

### 5.6 Form evolution summary

| Version | Form | Trigger / basis | Outcome |
|---|---|---|---|
| v1 | Single-line `.function-module` | Done opportunistically during the rename round | Upgraded by v3 |
| v2 | function = whole Content Area; **1:1** | You said "Skill is the sub-page" | **Overturned by v3** |
| v3 | Content Area = function list; function = card | Audio Settings screenshot | Kept (back to list) |
| v4 | function = data-driven assembly; fixed material pushed to component layer | Real delete/change/add use cases | Kept |
| v5 | **Recursive slot list** (synthesized) | Your "slot" mental model | **Current converged form** |

---

## 6. Real use cases and data (solidifying all concrete material that appeared in the discussion)

### 6.1 Audio Settings screenshot (reference spec)

Sub-page title **Audio Settings**, Content Area with three functions:

1. **Noise Control** — three-way segmented control, 3 icon cards: **ANC** (selected, blue background/white text, headset icon), **Transparency** (white, icon), **Off** (white, icon).
2. **Collaboration** — title + ⓘ info icon; contains: **Mic Noise Cancellation** (OFF + toggle on right), **Sidetone** (OFF + toggle on right), below a **slider 1—2—3** (currently at 2).
3. **Multimedia** — title + ⓘ; preset grid: **Default** (selected, blue), **Bass Boost**, **Speech Boost**, **Treble Boost**, **Custom** at the bottom (full row).

→ Form summary: this screen uses only **3~4 archetypes**: segmented (icon cards), `toggle`, slider, option-grid (presets). Names (ANC, Mic Noise Cancellation, Bass Boost) and option counts are all **data**, not new material.

### 6.2 Collaboration's "fixed base + model-specific increments"

- Base = Mic Noise Cancellation + Sidetone + slider, shared across 10 models.
- A future model adds a **dedicated sub-function under Collaboration** → add a nuance/alternative on top of the base template.
- Handling: fixed base components + one **extra slot**; the increment/alternative comes from manifest data, **the base file stays untouched**; if the new component isn't in the library → Layer 2 assembles it and inserts it into the slot. (This is v4/v5's "slot + data" applied at the component layer.)

### 6.3 Variant case inventory (all handled by changing data only)

| Case | Handling |
|---|---|
| Collaboration without Sidetone | Remove `sidetone` from that function's component (slot) list |
| Noise Control with only ANC + Transparency (remove Off) | `modes` list of segmented = `[anc, transparency]` |
| Noise Control adding a 4th/5th mode | Add an item to the `modes` list |
| Mic Noise Cancellation → Noise Cancellation (not the same function) | Switch to a different id `noise-cancellation`; known → copy snippet, unknown → `headset-function` assembles on the spot |

### 6.4 Sidetone 5 modes: Dropdown or Slider?

The criterion is **whether those 5 are ordered steps**: ordered (levels 1–5) → Slider; unordered named items (5 presets) → Dropdown. "Ordered or not" is a data property. You also noted "by convention Sidetone must use a slider" — treat that as a **hard domain convention**.

### 6.5 Conditional reveal: selecting ANC exposes sub-functions (variable, nestable)

**Your input**: After selecting ANC mode, some toggle-able sub-functions appear; **these are made-up examples** — in practice there may be some, may be none, may be two, or even sub-functions nested inside sub-functions one or two levels deep. Whether they exist, how many, how many levels — all are data that varies by product.

→ Model landing point: this is "slots" nesting one level deeper. When a mode is selected, 0/1/2+ sub-functions (still §5 lists) emerge from its internal **conditional slot** per data; the sub-function itself can also be "a card with slots" (recursive). The weak model doesn't decide whether they exist / how many / how deep — the data decides.

### 6.6 Function presets and the standard framework (default-dominant — defaults are the vast majority)

**Your input (background context)**: As long as a function card can be matched to an ID, **it almost always has a preset display state and composition; unless the user explicitly requests a change, most combinations are fixed ("rock solid")**. In other words: **preset (default) is the vast majority; override is the exception.**

**Standard component framework (most common slot form)**: **Title (function name) on the left, component (Toggle / Dropdown) on the right**. Most "toggle-type" functions use this standard row; it is the highest-frequency archetype at the component layer.

**Presets for several functions (authored once, models use the default directly)**:
| Function | Archetype | Default composition | Variability range (only when explicitly requested) |
|---|---|---|---|
| Noise Control | Segment Control (fixed) | 3 large cards: ANC / Transparency / Off | Add/remove one item (±1) |
| Multimedia | Mode grid | 5 modes by default | Up to 6 (2×3 layout); default is usually rock solid |
| Sidetone | Compound (two slots) | Top: Toggle + Bottom: Slider | Fixed layout once the product supports it |

**The implication, and how it resolves the §4 "snapshot vs data" debate**: for a standard model, "supports a function = reference its ID = get the fixed preset" — the experience is equivalent to "copy a ready-made one"; override in the manifest only when an explicit change is requested. Therefore:
- **The preset is exactly the "snapshot" originally wanted**, but **stored as data (composition definition)** so it can be overridden.
- Standard path through preset → **simple like a snapshot** (referencing the ID gives the fixed composition); exception via override → **flexible like data** (delete/change/add).
- This also corrects the tone of §5.4: that section, to illustrate that overriding is real, made variability sound very significant; **the actual weight is the reverse — fixed defaults are the vast majority, variability is the minority**. The two are not contradictory: "fixed" applies to the default; "flexible" applies when overriding; the key is that the preset is stored as data rather than frozen HTML, so both ends hold.

**Implication for workload**: authoring cost is manageable — author each of the ~10–20 functions' preset compositions once; most models just "reference the ID," no need to rewrite for each device.

---

### 6.7 Collaboration reference implementation (built and verified 2026-06-25)

The Collaboration card was **fully built + verified item-by-item** from Figma per this architecture (browser-tested rendering, computed colors/dimensions, interaction states). The first card to walk the full "snapshot" end-to-end pipeline, producing reusable building blocks.

**Reusable pieces built:**
- Card shell `headset-function/templates/function-frame.html` (title + optional ⓘ slot + component body slot).
- Components `headset-shared/components/`: `toggle.html` / `slider.html` / `info-tooltip.html` + README.
- All styles in `headset.css`; new tokens `--color-control-inactive`, `--radius-card`.
- `headset-function` (Layer-2) SKILL updated to the "shell + copy components" assembly model.

**Finished reference card:** `functions/collaboration.html` (now moved to `examples/collaboration.html` as a teaching example, not id-routed) = shell + 2×`toggle` (Mic Noise Cancellation / Sidetone) + 1×slider; Sidetone row + slider wrapped in `.subfn-group`; every row has an optional ⓘ. Pure HTML + data-property, no inline styles; interaction driven entirely by native controls + CSS (only one `oninput` line for the slider).

**Review decisions (landed):**
| Item | Decision |
|---|---|
| Shell panel background color | Kept original grey; briefly changed to white then **reverted** — zero primary-color changes in the template |
| Controls | Native checkbox switch (`:checked` driven), range slider (blue fill `--color-accent` + one-line `oninput` bubble) |
| ⓘ | Optional property; only rendered when info is present; must include a hover tooltip |
| Tooltip | Firmware ⓘ and card ⓘ **merged into one set** `.info-tooltip*`; same position as firmware; **min 220 / max 250px** |
| Wiring | Toggle off → child sub-functions grey out; `.subfn-group` + `:has()` pure CSS (Sidetone off → slider greys) |

**Verification method:** One-off preview host page `headset/_preview-collaboration.html` (fetch-injected snippets + linked real CSS), verified with `preview_screenshot/inspect/eval`. Dev artifacts (preview page + `.claude/launch.json`) are gitignored.

---

### 6.8 Weak-model validation (Haiku 4.5, 2026-06-25)

Handed "build a new card" to **Haiku 4.5** (cold-start sub-agent, given only the `headset-function` skill + `components/` building blocks + card shell + one reference card `collaboration.html`). Requirement: a Noise Control card = Mic Noise Cancellation toggle + intensity slider (1–3), slider greys when toggle is OFF.

**Result: passed.** Haiku assembled `functions/noise-control.html` (now moved to `examples/noise-control.html`) purely by **copying** the shell + `toggle` + `slider` — `.subfn-group` wiring correct (toggle `.subfn-toggle`, slider `.subfn-child`), native controls, zero inline styles, zero hallucination; browser-tested rendering correct, grey/restore (opacity 0.4↔1) correct. **Proved that "copy-not-generate + reusable building blocks" is weak-model-friendly** — the most desired property of the entire architecture.

Minor issues (harmless): created an extra `_preview-*` (gitignored); left an empty `.function-icons` div on a row with no info.

> Note: this `noise-control.html` is a **simplified test version** (toggle + intensity), different from the real Figma Noise Control's three-way segmented (ANC/Transparency/Off); **kept as-is**, name to be resolved when the real segmented version appears.

---

## 7. Control selection: when to use toggle / slider / dropdown (hard-coded vs inferred)

**Your input (paraphrased)**: An LLM sometimes needs logic-based reasonable inference. For example: what UI for on/off, how sub-functions display, how mode-switching is laid out, whether Sidetone 5 modes uses dropdown or slider… Some logic can be hard-coded (Sidetone → slider), some can't be hard-coded and the strong model has to infer. When exactly do you use toggle/dropdown/slider?

**My framework — split into two "moments"**:

| | Authoring time (design → data) | Generation time (data → HTML) |
|---|---|---|
| Who acts | Strong model + human review | Weak model, assembles from data |
| Cognition | High: can reason and judge | Zero: deterministic copy + fill |
| Output | Explicit, reviewable composition data + rule tables | Page HTML |

**Conclusion**: **LLMs should reason, but reasoning happens only at authoring time, and the result must be frozen into data; generation time does not reason.**

**Most "which control to use" decisions are actually table lookups, not per-case guessing. The rules have two levels.**

**Level 1: data shape → archetype family**

| Shape of the parameter | Control family | Nature |
|---|---|---|
| On/off (boolean, 2 mutually exclusive) | Toggle | Hard-coded rule |
| A value along an **ordered** range/step | Slider | Hard-coded rule |
| Pick 1 from N **unordered** items | **Select family** (see Level 2) | Hard-coded rule |
| A clickable action / entry point | **Button family** (see Level 2) | Hard-coded rule |
| A set of presets, tiled cards | Option-grid | Default rule, overridable |

**Level 2: which presentation within a family** (interchangeable presentations for the same data shape; most criteria can be hard-coded)

| Scenario | Options | Criterion (hard-coded rule) | Default |
|---|---|---|---|
| Single-select enum (Select family) | **Segmented vs Dropdown** | Count + space: ≤5~6 items, all must be visible / icon cards → Segmented; more items or tight space → Dropdown | Segmented for typical counts |
| Action / entry (Button family) | **Button vs Hyperlink-button** | Semantics: navigates to another page/view → Hyperlink (real `<a href>`, consistent with existing `feature-button`); executes an in-place action (apply/reset/toggle behavior) → Button | Navigation defaults to Hyperlink |

> Note: the button/link rule is already half-embodied in the codebase — the existing `feature-button.html` is an `<a href>` (navigation uses hyperlink); Level 2 just writes the current state down explicitly.

**With the three tables in place, most "which control to use" shifts from "inference" to "table lookup"**: ① Level 1 shape → family; ② Level 2 presentation within family (segmented/dropdown, button/link); ③ domain convention table (Sidetone → slider, noise reduction → icon segmented, on/off → toggle…). For anything still genuinely ambiguous, **let the strong model infer once at authoring time → write it as explicit data → human review**; thereafter generation time reads the data and doesn't infer.

**Key principle**: **the archetype id written explicitly in the data = the single source of truth; the three tables are only authoring-time guides + defaults, not runtime arbiters.** No "magic auto-select component" engine — presentation choice is partly rules (count/space) and partly design intent (icon cards vs text grid vs dropdown); full automation would erase design intent (§2.1: wrong abstraction costs more than duplication).

> Formally writing these three tables into `AGENTS.md` is a to-do (§11) — they are the mechanism carrier for "ensuring the AI picks the right control," and they are **used only at authoring time, not consulted at generation time**.

---

## 8. Interaction model: from "baked static" to "real interaction" to "native components"

### 8.1 Starting point: methodology advocates baking at generation time

§3.1 moves data consumption from "runtime" to "generation time": generate one state at a time, bake content in, no runtime show/hide. The premise is "one model at a time, one connection state, static display."

### 8.2 You chose "real interaction"

For dynamic behaviors like "selecting ANC immediately reveals XYZ, switching modes redraws," I offered two paths — A (static mockup) / B (real interaction) — **you chose B: real interaction.**

**Boundary clarification — two kinds of state, only one becomes interactive**:

| State axis | Handling | Changes? |
|---|---|---|
| Cross-product/model/connection (which device, wired/bluetooth, which functions exist) | Baked in at generation time (§3.1 still applies) | No change, static |
| Inside a single device panel, end-user operations (toggle switch, select mode, drag slider, conditional reveal) | Runtime | ✅ Real interaction |

Honest note: choosing real interaction means the control layer **does need "pre-embedded + runtime show/hide"** (XYZ pre-exists in the DOM; selecting ANC reveals it) — which is exactly what §3.1 originally said not to do. This is a **deliberate, knowing override**, justified because §3.1 assumed "static display page," which does not apply to "an operable control panel"; the product decision takes precedence.

### 8.3 Your key insight: behavior is native to the components → use native form controls, zero JS

**Your input (paraphrased)**: Real interaction doesn't require the weak model to guess or reconstruct — these interactions are native to the components: a Toggle inherently has on/off; Segmented/Button inherently has selected/unselected (hover at most); a Slider inherently has drag/value update. Use the component and the state is already inside it — no need to build a separate layer for the weak model. And confirmed again: pure front-end, no persistence, resets to default on refresh.

**I confirmed and upgraded (conceding this is better than the `headset.js` runtime I had proposed)**: use **native HTML form controls** — behavior provided by the browser:

| Component | Native element | Built-in behavior (0 JS) |
|---|---|---|
| Toggle | `<input type="checkbox">` (CSS-styled as a switch) | check/uncheck, selected state |
| Segmented | A group of `<input type="radio" name=…>` | mutually exclusive single-select, selected state |
| Slider | `<input type="range">` | drag, value update |
| Dropdown | Intentional custom: `<details>/<summary>` + CSS + minimal script | preserves Figma's custom list appearance; float positioning see C1 |

- Selected/hover states written into `headset.css` via CSS (`:checked`/`:hover`).
- **Even "selecting ANC reveals XYZ" can be pure CSS**: `#mode-anc:checked ~ .anc-extra { display:block }` (sibling selector, 0 JS).
- Therefore **the `headset.js` layer is removed**. Honestly noted exceptions retained (all one-liner native attributes, not a framework): display slider value in real time → one `oninput`; when a conditional element cannot be a CSS sibling of the trigger, one JS line as fallback.
- **Dropdown registered exception:** Dropdown is not a native `<select>`; it intentionally uses `<details>/<summary>` + custom list + minimal script to match Figma's custom list appearance. This is a registered exception in the "native-first / near-zero JS" model; the resulting float-clipping handling is addressed in C1.

### 8.4 Depth boundary for nested conditional reveal

- **Shallow (mode → directly attached sub-functions, one level)**: pure CSS `:checked ~`, 0 JS.
- **Deep nesting (reveal even deeper things based on state inside a sub-function)**: CSS sibling chains become brittle. Use **a generic declarative show/hide engine** for this — markup writes `data-show-when="mode==anc"`, one general-purpose JS block written once reads and acts. **Still: generic engine reads data, weak model only declares the relationship, no bespoke JS.**

### 8.5 Scope confirmed

**Pure front-end, no persistence, resets to default on refresh** — an operable UI panel demo. (Confirmed by you twice.)

---

## 9. Current converged model (synthesized)

### 9.1 One primitive: recursive slot list

```
Content Area      = an ordered slot list → each slot holds one function card (Noise Control / Collaboration / …)
  └─ Function card  = an ordered slot list → each slot holds one component (toggle / slider / segmented / …)
       └─ A slot     = can also hold "a card that itself has slots" (nested: the sub-functions revealed on selecting ANC)
            └─ …     recurse down
```

> **An ordered slot list; what fills each slot is decided by data; the count is variable; it is recursive.**

The weak model does exactly one thing from start to finish: **see a slot → copy the matching snippet per the archetype in the data → fill values.** How many slots, what fills each, whether to nest — all data.

**Two principles locked in (D20, 2026-06-26):**
1. **Nesting capability is universal; behavior is data-driven.** Every **assembled card**'s body is a slot list; any slot can hold a component or a **nested function card** (which has its own slots, recursion without limit); no per-function special cases; the card shell (`function-frame.html`) is consistent across all cards. Sub-function **show/hide/grey-out/always-visible** is not a property of the card; it is data written into the manifest as needed: requirement = "appears when an option is selected" → `reveals` (show/hide); requirement = "still visible but disabled when toggle is off" → `dependents` (grey-out); requirement = "always present" → plain slot. Generation time does not decide — it renders from data.
2. **Snapshot cards (Layer 1, e.g. `eq-audio`) are frozen leaves.** Copied wholesale; the manifest's `components`/`reveals`/`dependents` are not read; any internal nesting (if present) is baked into the snapshot HTML and is not model-specific. Recursive slot logic applies fully to **assembled cards**; snapshot cards are **intentional endpoints** (preserving D18's "minimal generation"). Making a snapshot card also carry on-demand nested slots = re-opening D18 — **not doing this for now** (stability first).

### 9.2 Layer structure (template/rule side ↔ data side)

```
Template / rule side                              Data side (manifest)
────────────────────────────────────────         ──────────────────────────────────
1. tokens.css      Design constants               (none)
2. headset.css     Layout + component styles      (none)
                   + :checked/:hover states
                   + shallow conditional reveal
3. Page frames     gen-homepage/gen-subpage        home.manifest: identity+connection+features[]
   (skeleton + data-slot slots, copy+fill)         <subpage>.manifest: title + functions[] (slot list)
4. Functions       Card shell (title + ⓘ)          Each function: id + component slot list (+ default composition, overridable)
   = data-driven assembly
5. Components      components/<type>.html          Each component: archetype + values (label/options/default/ordered?)
   (native form control snippets,                  + optional reveals (conditional sub-slots, 0/N, nestable)
    behavior provided by browser)
```

### 9.3 Two layers (known/unknown) land on "component archetype"

- **Known archetypes** (`toggle` / segmented/slider/preset-grid…) → snippet exists → copy + fill (Layer 1). Archetype count is small and bounded (~10), grows on demand, completable.
- **Unknown archetype** → `headset-function` (Layer 2) assembles on the spot; solidified into a snippet once it recurs (§9.4).
- **Known functions' "default composition"** (standard Collaboration = which components) = data (registry, §5.2), referenced by id, overridable per model (delete/change/add).
- **Preset-first (defaults are the vast majority, see §6.6)**: each function ID has a fixed preset composition ("rock solid"); standard models just "reference the ID to get the preset"; overrides are the exception. Presets stored as data rather than frozen HTML, so both "standard = simple" and "exception = changeable" hold.
- **Highest-frequency component archetype = standard row**: Title on left + component on right (Toggle/Dropdown). Sidetone is a fixed compound (top Toggle + bottom Slider); Noise Control uses fixed Segment Control; Multimedia uses fixed mode grid (default 5, max 6 in a 2×3 layout).
- **The archetype list is open / provisional (user confirmed 2026-06-25)**: the archetypes listed (`toggle`, segmented, slider, dropdown, option-grid/preset-grid, standard row…) are just the **starting point as of now, not a closed enum** — they will be supplemented or changed. Adding/changing an archetype follows the "unknown → assemble on the spot → solidify once it recurs" path (§9.4), and **updates the Level 2 decision tables in §7 + any affected presets at the same time**. This is "grow on demand" in practice — no need to enumerate everything upfront.

### 9.4 Mapping to the methodology

- Aligned with: §3 (slots), §4 (variants: archetype enum selects a snippet), §5 (lists: slot lists, mode lists), §5.2 (registry: default composition by id), §9.3 (one framework skill per sub-page type), §9.4 (known snippet / unknown fallback / high-frequency promote), §9.7.4 (copy not create).
- **Extension** (codebase goes one level deeper than the methodology): the methodology treats "control" as a single-layer atom; real functions are **composite**, so they are split into **function card + component atom two layers**, with recursion applied into the card interior.
- **Override**: §3.1 "bake at generation time, no runtime show/hide" is **overridden at the control interaction layer by real interaction** (8.2); cross-model/connection state is still baked.

### 9.5 Honest boundaries and risks

- **Abstractions can leak**: if two visual modes are genuinely different (Noise Control's icon cards vs Multimedia's plain text grid), make them two archetypes — don't force a merge (§2.1 "wrong abstraction costs more than duplication"). The archetype count may therefore be one or two larger, but remains bounded.
- **Deep nesting show/hide**: pure CSS sibling chains can become brittle; needs the generic declarative engine as a fallback (8.4).
- **Real interaction violates §3.1**: deliberate knowing override, see 8.2.

---

## 10. Decision log

| # | Decision | When introduced | Rationale | Status |
|---|---|---|---|---|
| D1 | Methodology is reference; codebase is authoritative | Start | User stated explicitly; methodology is partly outdated | Active |
| D2 | `headset-control-generic` → `headset-function`; full control→function vocabulary migration | §2 | Name too broad; keep consistent to prevent drift | **git add-ed, not committed** |
| D3 | Function form = single-line module | §2 | Understanding at the time | **Revoked** (superseded by D9) |
| D4 | Two-layer architecture: known → copy / unknown → assemble on the spot | §3 | User background | Active |
| D5 | One sub-page = one function (1:1); remove the list | 5.2 | Misread "Skill is the sub-page" | **Revoked** (overturned by screenshot) |
| D6 | Known functions use snapshot/data; no skill per function | §4 | See 4.3 pros/cons; logic only needs to live in one place | Active |
| D7 | Content Area = function list (1~N) | 5.3 | Audio Settings screenshot | Active |
| D8 | Fixed material pushed to component layer; function = data-driven assembly; identity by id | 5.4 | Real delete/change/add use cases | Active |
| D9 | Function = card block (title + components), not single line | 5.3/5.4 | Screenshot | Active (replaces D3) |
| D10 | Control selection: three tables (① shape→family ② presentation within family: segmented/dropdown, button/link ③ domain conventions) + infer once at authoring time and freeze into data; no runtime selection engine | §7 | Converge inference into table lookups | Active (written into headset/AGENTS.md) |
| D11 | Real interaction (not static mockup) | 8.2 | User chose B | Active |
| D12 | Use native form controls + CSS, near-zero JS; remove `headset.js`; Dropdown is a registered exception (`<details>/<summary>` + minimal script, no native `<select>`) | 8.3 | Browser provides behavior natively, more consistent with "copy not construct"; Dropdown exceptional to preserve Figma custom list appearance | Active (replaces the earlier headset.js proposal) |
| D13 | Deep nested show/hide uses generic declarative engine `data-show-when` as fallback | 8.4 | CSS sibling chains are brittle | Active (deep nesting only) |
| D14 | Pure front-end, no persistence, resets to default on refresh | 8.2/8.5 | User confirmed twice | Active |
| D15 | Converge to "recursive slot list" as the single primitive | 5.5 | User's "slot" mental model | **Current model** |
| D16 | **Preset-first**: each function ID has one fixed preset composition; defaults are the vast majority; overrides are the exception; presets stored as data | 6.6 | User background: "almost every ID has a preset, rock solid" | Active (solidifies D6/D8, not a reversal) |
| D17 | **Snapshot = derived artifact + "change atom → rebuild snapshot" discipline**; no build machine for now (only 2 cards, methodology accepts copying). Snapshot is assembled from shell + atoms; `headset-function` assembly logic is the seed of a future build step; automate "spec → assemble → snapshot" when card count grows | F analysis | Drift is real (cleaning ⓘ SVG forced editing snippet + 3 baked-in copies at once) but cheap right now | Active: discipline established, machine deferred |
| D18 | **Minimal generation**: manifest = sub-page title + **function id list (+ rare overrides)**; gen-subpage on a function only "copies snapshot + strips markers"; per-function value-fill is nearly a no-op (almost nothing in known cards varies by model); no complex fill engine | G analysis | Almost everything in a frozen snapshot is baked; what truly varies by model is "which functions are present" (the list) | Active: pending real gen-subpage run to validate |
| D19 | **Recursive slot / conditional reveal lands as manifest `reveals` schema + generation steps + generation-time validation**: the "conditional sub-slot" in §6.5/§8/§9.1 had previously only reached the CSS+snippet layer (`.segment-panels` positional `:has`); no manifest syntax, no gen-subpage steps. Now defines `reveals` (selector option value → ordered slot list; slot = component or nested `{function:<id>}`, recursively); replaces the improvised `condition:`; gen-subpage/headset-function add reveals generation steps; new generation-time validation (unknown archetype/id, leftover `condition:`, reveals key mismatch, >6 options, duplicate option values → HALT); establishes "output must be regenerable from manifest; patching output directly is forbidden" discipline (elevates D17 to page level) | WL327 first run exposed (EQ treated as slider, HTML hand-patched, manifest↔output diverged) | Architecture always had the recursive primitive; what was missing was the schema and generation layers; WL327 is gen-subpage's first real run and hit the §11 unimplemented items | Active: WL327 regeneration verified |
| D20 | **Toggle `dependents` (grey-out) schema + universal title slot `.subfn-label` + nested-universal / snapshot-frozen principle + mechanical validator**: BUG-002 exposed `reveals` being misused on control-row, and named full-width component titles being dropped. Added `dependents` (grey-out sub-slots for control-row, dual to `reveals` show/hide); `.subfn-label` title slot is universal for both reveals and dependents (restores dropped "ANC Strength"/"Canceling Strength"); §9.1 locks in "nesting capability is universal, behavior is data-driven, snapshots are frozen leaves (no re-opening D18)." **Key stability**: upgrades HALT from SKILL.md prose to a **zero-dependency mechanical validator** `validate-manifest.py` (mandatory pre-generation run before gen-subpage; non-zero = stop), curing "weak model bypasses prose rules" (BUG-002's stated skip reason). Also fixes the "options+panels total ≤6" wording bug (actually ≤6 options; panels and options are 1:1) | BUG-002 + user "stability" directive | Prose rules get bypassed by weak models under pressure to be helpful; per-instance fixes don't prevent recurrence — need universal + mechanical gate | Active: validator tested on real manifests passes; 5 categories of bad manifests HALT |
| D21 | Explicitly split the component layer into **two levels: shape (container: row/stacked) × component (control: toggle/dropdown/slider/segmented/preset-grid)**. `control-row` is a **row shape** (holding interchangeable compact controls toggle/dropdown), **not** a peer of segmented/slider/preset-grid; stacked shape = `.subfn-label` title + full-width component; title belongs to the shape (cannot be dropped). Decision flow for "nested sub-functions" changed to **first pick shape (horizontal/vertical) then pick component** (see `headset/AGENTS.md`). **No renaming the code archetype enum for now** (enum stays: `control-row | slider | segmented | preset-grid | dropdown`) — renaming/splitting would touch manifest schema, validator, snippets, all models: destabilizing, deferred. | User's design-perspective discussion (pick shape first, then component; pointed out dropdown is both an archetype and inside control-row = hierarchy confusion) | Scattered logic caused dropped titles, `reveals` misuse on control-row, etc.; two-level model makes title structural (belonging to shape), matches designers' mental model; but code refactor scope is large — stability first, land in docs only | Active (docs layer; code archetype rename deferred) |
| D22 | Rename archetype `control-row` to `toggle`; enum becomes **pure components** `toggle | slider | segmented | preset-grid | dropdown`; **container shape is inferred by the generator** (compact components toggle/dropdown → row; full-width components slider/segmented/preset-grid → stacked + `.subfn-label`). Lands D21's two-level model in code. **CSS class names unchanged** (`.function-header`/`.switch`/`.subfn-toggle` etc.); **generated HTML unchanged** (only manifest archetype string + snippet filename control-row.html→toggle.html). `dropdown.html` updated to a full labeled row = grow-on-demand to-do (no manifest currently uses `archetype: dropdown`). | User asked "why not rename the enum"; grep evidence: only 1 real model uses it, dropdown has never been a top-level archetype → rename is cheapest right now. | control-row is a shape name intruding into the component enum; 1-model pilot stage has the lowest rename cost; delaying only gets more expensive as manifests grow; validator and schema updated in sync, no impact on generation stability. | Active (code layer; dropdown.html full-row version deferred) |
| D23 | **Nested assembled card slot** — any assembled slot list (`components`, selector `reveals`, toggle `dependents`) may contain a titled sub-card `{ title, info?, components:[...] }`, recursively; each inner slot is a component, a `{function:<id>}` snapshot, or another nested card. Rendered with existing `.subfn-group`/`.subfn-label`/`.subfn-child` only (no new CSS; the grey-out selector is tightened to direct-child so nesting can't leak). Legacy `archetype: section` now HALTs with a pointer to this form. | WL527 Automated Actions needed a labelled "When Headset Removed" subgroup, expressed wrongly as invalid `archetype: section`. | Completes the §9.1/D20 recursive-slot primitive without a parallel "section" archetype; grouping is structural slot data, behaviour stays parent-owned (`reveals`/`dependents`/plain). | Active: nested-card validator + renderer + regression; WL527 "When Headset Removed" renders + greys out. |
| D24 | **Mechanical fidelity hardening + enforced gate** — (a) `validate-manifest.py` rejects unknown keys, enforces archetype↔option-count (2–3 segmented / 5–6 preset-grid), and HALTs when a component `label` duplicates its card `title`; (b) a sole top-level compact toggle may omit its `label` (card title is the label); (c) home `image` policy = explicit-or-opt-out: key required, value a **relative, existing** path (absolute / OS-specific / `..` / missing all HALT) OR `image: none` + `opt-out-reason`; (d) an all-model gate `verify-all.sh` (validate every model + byte-drift `verify-model.py`, checking only manifest-declared pages, ignoring auxiliary HTML) wired into `.githooks/pre-commit` + a CI workflow. | WL527 shipped hand-written HTML diverging from the renderer, plus `tooltip:`/`button`/`section` typos, duplicate labels, and an absolute Windows image path — none caught because nothing ran the validators automatically. | Validators don't prevent recurrence unless every path runs them automatically and the schema blocks known-bad authoring states before render (D20). | Active: all checks + regressions pass; gate green across 4 models. |
| D25 | **Validation loophole closures** — sliders require numeric `min < max`, value in range, `stops ≥ 2`; selectors require exactly one `selected`; new `validate-walkthrough.py` (wired into the gate) schema-checks walkthrough manifests; nested cards are depth-capped to the level the pure-CSS grey-out supports (deeper needs the unbuilt D13 declarative engine). | Probing found these silently accepted (`value:99,max:3`; zero-selected; walkthrough manifests entirely unvalidated). | Same as D20: invalid manifests must HALT mechanically before a weak model emits stale / ambiguous / CSS-unsupported UI. | Active: regressions pass. |
| D26 | **CSS-class-existence gate** — `check-css-classes.py` (zero-dep) discovers linked stylesheets, parses defined `.class` selectors, scans literal `class="…"` across snippets / templates / rendered pages, and HALTs on any class absent from linked CSS (a file's own inline `<style>` counts). Wired into `verify-all.sh`. | Bug 7/8 were hallucinated classes (`download-button`, `wt-button--primary`); model authors can no longer invent them (HTML is rendered), but snippet/snapshot authors still could. | Renderer determinism doesn't prove CSS coverage; check it mechanically against the actual stylesheets, no suppressions. | Active: clean repo passes; injected bogus class HALTs. |
| D27 | **Requirements↔manifest fidelity layer (#7)** — when a model has `requirements.md`: (a) `check-requirements-coverage.py` matches the requirements function list, device identity, and walkthrough titles against the manifests; (b) a per-model `coverage.md` **atom table** (`Atom ID | Requirement | Locator | Expected | Verdict`) decomposes each control-level requirement fact to a **stable** locator (function id / archetype / option value / `reveals.<v>` / `dependents`, never positional) + expected value, verified mechanically by `check-coverage-atoms.py` (reuses `parse_manifest`, no LLM). Models without `requirements.md` skip. **Boundary**: the checker proves "manifest matches the authored atoms (no drift)"; it does NOT prove the atoms reflect the prose — that stays an independent reviewer (`Verdict` = pass/fail/ambiguous) + human escalation of ambiguity (missing default, unclear parent/child, show/hide vs grey-out, count/range mismatch, unclear tooltip target, snapshot-keyword conflict). | #7 — free-prose control behaviour can't be mechanically checked for semantic fidelity; "read N times" is the weak D20-class prose rule. | Split the problem: make the manifest's encoding machine-addressable and check the author's explicit claims mechanically; reserve the human/strong-model only for "do the atoms reflect the prose." The first WL527 atom run surfaced a 4-review-missed requirements omission (Power off after `4h`), escalated and resolved by the human. | Active: 46 WL527 atoms pass; wrong-value / unresolvable-locator HALT; gate green across 4 models. |
| D28 | **Card-level on/off toggle renders on the title row** — when a function's sole top-level component is a `toggle` that omits its `label` (the card title is its label — the A4 case), the switch is hoisted into the card's top `.function-header` (standard §6.6 row: title left, toggle right) and its `dependents` render below in `.function-content`, grey-out re-wired. Multi-component cards (Collaboration) and non-toggle-primary cards (Noise Control segmented) are unaffected. A header-only card (sole toggle, no dependents — e.g. Busy Light) collapses its now-empty `.function-content` so the parent's 8px inter-item gap renders no empty separator below the title. General renderer rule; no manifest change; no new CSS class. | A4 removed the duplicate label but left the toggle in an orphan body sub-row → the switch floated, misaligned, below the title; and after hoisting, a body-less card still showed an 8px gap under a header with nothing beneath it. | Completes A4: "the card title IS the toggle's label" implies they share one row. A pure visual/layout bug that structural drift checks cannot catch — caught only by rendering and looking. | Active: render-content rule + grey-out selector + regression; visually verified (Auto Off / Audio Guidance / Busy Light / Wear Detection on the title row; Collaboration / Noise Control unchanged; grey-out works). |
| D29 | **Autonomous self-correction loop** — `regen.sh` (deterministic backbone: re-render every model from its manifests + run `verify-all.sh`, which resolves drift) plus an **AUTOFIX/ESCALATE failure taxonomy** codified in `headset-gen-subpage/SKILL.md`. Machine-determinable failures (drift, unknown key, archetype↔option-count, `label==title`, slider range, image path, CSS-class) are fixed at the manifest / CSS / snippet **source** and regenerated — rendered HTML is never hand-edited (D19). `verify-all.sh` and the pre-commit hook stay **detect-only** (drift is surfaced at commit, not silently auto-regenerated). Only intent-judgment (semantic) cases — atom-vs-prose, genuine prose ambiguity (the "4h" case), independent-review fail — escalate to a human. | User directive: automate every machine-determinable fix; reserve humans for intent. | Governing rule: auto-fix when the correct fix is determinable from rules + requirements without guessing intent; escalate the moment resolving it would require guessing what the human meant. | Active: regen.sh + loop section + drift auto-resolve demo verified; 17 tests pass. |

---

## 11. To-do / Open items

**Completed (2026-06-25):**
- [x] `headset-function` rename migration committed (130da31).
- [x] Function form upgraded from single-line to card: `function-frame.html` remade as card shell; `.function-*` card styles landed (§6.7).
- [x] Added `headset-shared/components/`: `toggle` / `slider` / `info-tooltip` (§6.7); `segmented` / `dropdown` / `preset-grid` etc. to be added on demand.
- [x] Collaboration card built and verified item-by-item; firmware ⓘ and card ⓘ merged into one tooltip set (§6.7).
- [x] **Three control-selection tables written into `headset/AGENTS.md`** (D10): ① shape→family; ② presentation within family (Segmented/Dropdown count threshold, Button/Hyperlink semantics); ③ domain conventions. Authoring-time use only.

**Completed (2026-06-26, D19):**
- [x] **Ran `gen-subpage` to produce a real sub-page**: WL327 `home.manifest` + `audio-settings.manifest` → `index.html` + `audio-settings.html` (first real run; exposed and fixed schema/generation-layer gaps).
- [x] **Noise Control (`segmented`) + Multimedia (`preset-grid`) + conditional sub-functions**: conditional show/hide landed as `reveals` schema (select ANC → slider panel; select Custom → `eq-audio` card); uses positional `:has` CSS per §8.
- [x] **Manifest schema + generation-time validation**: `reveals`/`components[]` schema written into `headset-gen-subpage/SKILL.md`; unknown/out-of-range/duplicate → HALT.

**Completed (2026-06-29, validation hardening + #7 fidelity — D23–D27):**
- [x] **Nested assembled card slot** (D23) + **depth cap** (D25): WL527 "When Headset Removed" renders and greys out.
- [x] **Mechanical fidelity gates** (D24–D26): unknown-key / archetype-count / `label==title` / slider range / exactly-one-selected / image path policy / walkthrough-manifest validator / CSS-class existence; **all-model `verify-all.sh`** wired into `.githooks/pre-commit` + CI.
- [x] **Requirements↔manifest fidelity** (#7, D27): coverage gate + `coverage.md` **atom table** + `check-coverage-atoms.py` (WL527 = 46 atoms); independent-review `Verdict` column + ambiguity escalation is the still-human part.
- [x] **Card-level on/off toggle on the title row** (D28): completes A4's layout — the toggle was orphaned/misaligned below the title; now shares the title row, grey-out re-wired. Visually verified (the first visual check of this work, not just structural).
- [x] **Autonomous self-correction loop** (D29): `regen.sh` deterministic backbone + AUTOFIX/ESCALATE taxonomy in the gen skill; mechanical errors auto-fix at the manifest source and regenerate, only intent-judgment cases escalate to a human.

**Not yet done:**
- [ ] **Deep-nesting declarative engine (D13)**: still unbuilt; nested cards are depth-capped (D25) as the stopgap.
- [ ] **Variant model validation**: produce a model that "removes Sidetone / Noise Control with only 2 modes" to prove data changes leave material untouched.
- [ ] **Storage format for known functions' "default composition"** + `gen-subpage` override-merge logic (override path currently only supports per-slot data-property overrides).
- [ ] Icons: only `audio.svg` exists; Noise Control's segment icons are still hand-drawn placeholders (not from `icons/`); pending real acoustic icons.

---

## 12. Glossary

- **Feature (home-page entry)**: A button in the home page Feature Zone; one item in `features[]`; clicking navigates to a sub-page. **Not a skill** — copies `feature-button.html`.
- **Sub-page**: e.g. "Audio Settings," with a title + Content Area; generated by the single framework skill `gen-subpage`; **no dedicated skill per sub-page** (§9.3).
- **Content Area**: The content region of a sub-page = a column of **function slots** (1~N, variable).
- **Function / Function card**: A titled card inside the Content Area (Noise Control / Collaboration / Multimedia). Internally = a column of **component slots**. **Data-driven assembly, not a frozen snapshot.**
- **Component**: The small control inside a function (switch/slider/segmented/preset grid). Uses **native form control snippets**; behavior is provided by the browser.
- **Slot**: A fill position in a template (the `data-slot` in code). **Recursive**: Content Area, function card, and component layer are all "slot lists."
- **Archetype**: The "shape category" of a component (`toggle` / segmented/slider/dropdown/preset-grid…). **Few in number and bounded**; names/options are data.
- **Snippet / Snapshot**: Static HTML material (+ value slots) to be copied. Component snippets, connection blocks, and feature-buttons all belong to this category.
- **Skill**: A folder with `SKILL.md` that can run logic. Here there are only framework skills (`gen-homepage`/`gen-subpage`) and the unknown-function assembler (`headset-function`); **no skill per known function**.
- **Layer 1 / Known**: Snippet/default composition exists → copy + fill.
- **Layer 2 / Unknown**: `headset-function` assembles on the spot → solidified once it recurs (§9.4).
- **Manifest / Composition data**: The content data for a model/sub-page. Specifies which functions exist, which component slots each function has, each component's values and archetype, and conditional reveals.
- **Reveal / Conditional show-hide**: Conditional slots that only appear in a certain state (e.g. when ANC is selected); 0/N, nestable; shallow = CSS; deep = declarative engine.
- **Authoring time vs generation time**: Reasoning/judgment happens only at authoring time and is frozen into data; generation time performs deterministic assembly without inference.

---

*This record is continuously updated as the discussion progresses. The latest converged model is in §9; items not yet landed are in §11.*
