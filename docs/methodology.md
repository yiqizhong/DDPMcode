# Product UI Generation · Template Framework & Core Mechanisms Methodology

> Using the Mouse category as a Pilot example · The mechanisms are universal and apply to every product category
> Scope: Display, Keyboard, Headset, Mouse, Audio, and other six-to-seven product categories
> Version 1.0

---

> ⚠️ **Status: reference only — the codebase is the source of truth.**
> Parts of this framework are out of date. Where it conflicts with the repo, follow the
> repo's `AGENTS.md` / `README.md`. Known divergences already settled in code:
> - **§9.5 skill location** — skills live **flat at repo-root** `.agents/skills/`, namespaced
>   `<category>-<role>-<name>` (not nested per category). Nested grouping (§9.7.3) was tested
>   2026-06-24 and fails Devin discovery.
> - **Pilot category** — the real pilot is **headset** (`headset/`); "Mouse" here is only a
>   teaching example.
> - **§3 markup** — markup is **copied verbatim from pre-written snippet files, never generated**
>   from a `data-instruction` description; an unknown enum value **halts and asks** (see
>   `AGENTS.md` → "Markup is copied from snippets").

---

## Table of Contents

- [How to Read This Document](#how-to-read-this-document)
- [1. Top-Level Mental Model: The Three-Layer Architecture](#1-top-level-mental-model-the-three-layer-architecture)
- [2. Template Structure and Directory Hierarchy](#2-template-structure-and-directory-hierarchy)
- [3. The Slot Mechanism: How to Leave Slots, How to Mark Them for the AI](#3-the-slot-mechanism-how-to-leave-slots-how-to-mark-them-for-the-ai)
- [4. Core Mechanism One: Variants — Using the Control Zone as an Example](#4-core-mechanism-one-variants--using-the-control-zone-as-an-example)
- [5. Core Mechanism Two: Lists — Using the Feature Zone as an Example](#5-core-mechanism-two-lists--using-the-feature-zone-as-an-example)
- [6. Clickability and Routing](#6-clickability-and-routing)
- [7. The Operational Entry Point: The Model Spec (Manifest)](#7-the-operational-entry-point-the-model-spec-manifest)
- [8. How to Apply This to Other Product Categories](#8-how-to-apply-this-to-other-product-categories)
- [9. Scaling Rules: Using a Skill Tree for Fine-Grained Rules and Multi-Level Subpages](#9-scaling-rules-using-a-skill-tree-for-fine-grained-rules-and-multi-level-subpages)
- [10. Execution Rule Checklist (Ready to Paste into AGENTS.md)](#10-execution-rule-checklist-ready-to-paste-into-agentsmd)

---

## How to Read This Document

This document is not a content list for any specific model. It is a methodology for building product UIs. It uses the Mouse category as a teaching example (Pilot), but every structural division, mechanism, and rule in it is universal — when you build a Keyboard, Headset, Display, or any new category, replace "Mouse" in the examples with your target category and the whole method still holds.

Suggested reading order: Start with Chapter 1 to build the overall mental model (the three-layer architecture). Read Chapter 2 to understand the physical structure and directory layout of templates. Chapter 3 explains the core carrier — the "slot": how the template is left empty and how slots are marked for the AI to fill. Chapters 4 and 5 cover the two core mechanisms (variants / lists). Chapter 6 covers clickable routing. Chapter 7 lands the method on the "manifest" as the operational entry point. Chapter 8 covers replicating this to other categories. Chapter 9 solves the scaling problem of "more and more rules, deeper and deeper pages" (the Skill-vs-content boundary). Chapter 10 is the hard-rule checklist for the AI/team to execute against.

> **The Methodology in One Sentence**
> The template only handles "what it looks like" and "what slots exist"; all product differences are expressed as "data (the manifest)." Variants use discrete states, lists use data-driven rendering. Each category is physically isolated and stored separately, sharing only the design tokens.

---

## 1. Top-Level Mental Model: The Three-Layer Architecture

Before writing any template, establish a mental model that runs through everything. The entire product-UI system is composed of three mutually independent layers, each minding its own business. To judge whether a design is healthy, check whether these three layers are tangled together.

### 1.1 The Responsibility of Each Layer

| Layer | Question It Answers | Change Frequency | Who Maintains It |
|------|---------|---------|---------|
| Design System Layer (Design Tokens / Shared Components) | "Looks alike" — color, font, button style, shadow, radius, base canvas dimensions | Almost never (only on design-language upgrades) | Shared by all categories; change one place, takes effect globally |
| Category Template Layer | "Structure is right" — this category's page skeleton, zone division, layout dimensions | Only when the category's design changes | Each category has its own set; mutually independent |
| Model Data Layer (Model Config / Manifest) | "What to fill in" — what this specific model is called, what features it has, how it connects | A new one is added for every new model | One per model; only added, never alters the template |

**The Gold Standard:** When you ship a new model, can you get away with only adding a new "model data (manifest)" and not touching the template or design system at all? If yes, the architecture is healthy. If you still have to go back and edit the template, it means some difference that should have been data got hardcoded into structure — and that is the root cause of instability.

### 1.2 Why You Must Split Into Three Layers

Tangling these three things together is the fundamental reason most UI code rots over time. The most typical anti-pattern: write every model, every feature, every connection state into one HTML file, then toggle them with "hide/show." This leads to a file that quickly bloats into a "grab-bag of all possibilities"; every new model means going back to edit this shared file; the information "what features does this model actually have" gets buried in display state, hard to find and hard to maintain; and editing one place often breaks another by accident.

Once layered, change is isolated where it belongs: visual change only touches the design system layer, layout change only touches the category template layer, model difference only touches the data layer. Each layer thereby becomes stable and predictable.

---

## 2. Template Structure and Directory Hierarchy

This chapter lands Chapter 1's three-layer model onto concrete files and directories, and makes explicit the key decision of "physical isolation between categories."

### 2.1 The Physical Isolation Principle: Each Category Stored Separately

Because different product categories have substantial differences in their feature pages, layouts, and dimensions (similar framework, very different details), we adopt a strategy that looks "duplicative" but is actually more stable: build an independent, complete, self-contained set of templates for each category — even if two categories share 80% of their structure, store each separately.

**This is not laziness; it is the correct engineering trade-off.** The often-misused DRY ("Don't Repeat Yourself") principle has a corresponding reverse wisdom: the wrong abstraction is more expensive than duplication. When the difference between categories is "structural" rather than "content," forcing an abstraction into "one generic template + a pile of conditional branches" produces a monster crammed with special cases that nobody dares touch; physical isolation instead keeps each set focused, readable, and maintainable.

Decision rule: structural difference between categories → isolation first; content difference between models within a category → data-driven (see Chapter 5).

### 2.2 The Only Shared Line: Design Tokens

Physical isolation does not mean everything goes its own separate way. We keep one extremely thin, low-coupling shared line — the Design Tokens: color, font, shadow, radius, base canvas dimensions. Every category template references the same set of tokens. This way, visual consistency is automatically guaranteed (all categories are forever the same primary navy, the same font), while layout stays completely free. On a design-language upgrade, you change only one place.

> **Why Share Only Tokens, Not Layout**
> Tokens are the bottom-layer visual constants that "should least diverge"; sharing them costs almost nothing and pays off enormously (prevents "changing the color six or seven times").
> Layout is the part that is "genuinely different between categories"; sharing it would reintroduce coupling and betray the point of isolation. So: share visual constants, isolate structural layout.

### 2.3 Recommended Directory Structure

Landing the above principles onto directories gives the following structure. Each category is a self-contained folder holding its complete set of pages and its own rule file.

```
repo/
├── shared/
│   └── tokens.css          ← The only shared thing: color / font / size baselines
│
├── mouse/                  ← Mouse category (this document's Pilot example)
│   ├── AGENTS.md           ← Mouse's generation rules (constrain AI and team)
│   ├── index.html          ← Home page
│   ├── mouse-settings.html ← Subpage
│   ├── button-customization.html
│   └── models/             ← (Optional) per-model manifest data
│
├── keyboard/               ← Keyboard category, same structure, own content
│   ├── AGENTS.md
│   └── ...
│
├── headset/                ← Headset category
├── display/                ← Display category
└── ...                     ← One folder per remaining category
```

When working on a category, you enter only its own folder and never touch other directories. This way the logic of Mouse, Keyboard, and Headset is severed at the file level and they never cross-contaminate.

### 2.4 Correspondence with AGENTS.md / the AI Generation Architecture

This directory structure is also the landing point for the AI auto-generation system. Each category folder holds an AGENTS.md (directory-level rules) stating that category's template structure, feature forms, and generation specs. When an AI (such as Devin) works in a given category directory, it loads only that directory's AGENTS.md plus the root-level common rules; other categories' rules never enter context — physical isolation (folders) and rule isolation (separate AGENTS.md) doubly guarantee "no cross-contamination."

| Three-Layer Model | Maps to the AGENTS.md System |
|---------|---------------------|
| Design System Layer | Root-level common rules + `shared/tokens.css` |
| Category Template Layer | Each category folder's `AGENTS.md` (defines what that category's pages look like and what features they have) |
| Model Data Layer | The "manifest" provided when generating a specific model (see Chapter 7); the AI fills from it without altering the template |

---

## 3. The Slot Mechanism: How to Leave Slots, How to Mark Them for the AI

Chapter 2 says "the template only carries layout + empty slots." This chapter makes the "empty slot" idea concrete: how exactly a slot is left, what marks it, how the AI reads that mark and fills it, and whether the mark stays or goes after filling. This is the key link connecting "template" and "manifest."

### 3.1 The Core Shift: Data Consumption Moves From "Runtime" to "Generation Time"

To understand the slot mechanism, first understand a fundamental shift. In the old way of thinking, the page is "live": write every possibility (the wired block, the bluetooth block, all features) into the HTML up front, then use `data-property` to show/hide and read values in real time in the browser based on user input.

But your workflow has already confirmed three things — generate one model at a time, generate only one connection state by default (change it via a separate prompt), and produce content-baked-in finished HTML. Together these three mean:

> **Data is filled in "at the moment the AI generates this model's page," not "at browser runtime."**

Once data consumption moves from runtime to generation time, the mechanism of "using attributes for runtime show/hide and value-fetch" loses its reason to exist. The image is baked in as `<img src="mouse-ms3320w.png">` at generation time, rather than being "fetched at runtime." This is the fundamental basis for deciding whether `data-property` stays or goes.

### 3.2 The Role Shift of `data-property`: From "Runtime Binding Point" to "Generation-Time Fill Marker"

The `data-property` in your current HTML carries two responsibilities at once, and the two have different fates under the new workflow:

| Responsibility | Meaning | Fate |
|------|------|------|
| A. Slot marker | Marks "this position is an empty slot to be filled, and what fills it" (e.g. `data-property="device-marketing-name"` = fill the model name here) | **Keep**, but its role becomes "a fill marker for the AI to read" |
| B. Runtime binding | Write multiple UI sets up front and show/hide or fetch values at runtime via attributes (e.g. both wired and bluetooth blocks written, switched by attribute) | **Retired**, replaced by "generate only the needed block at generation time" |

In one sentence: **`data-property` is not a question of keep-or-delete; it is demoted — from "a mechanism the page depends on at runtime" to "a fill-in marker for the AI at generation time."** It is still useful (helping the AI fill the right spot precisely) but no longer drives runtime behavior.

### 3.3 Template vs. Finished Page: The Different Fates of the Same `data-property`

Separate "template" from "finished page" and the keep-or-delete question dissolves:

| | Purpose | What to Do With `data-property` |
|---|------|----------------------|
| **Category template (empty skeleton)** | For the AI to reference; marks each slot | **Keep**, as a "where-to-fill + what-to-fill" marker |
| **Generated finished model page** | For the user to use; clickable, navigable | **Removable**, content is baked in, the marker does nothing for the browser |

That is: **keep `data-property` as a slot marker in the template; the AI reads it and fills in the manifest data; the generated finished page may keep or drop these markers (no impact on runtime).** Recommendation: keep the finished page clean (drop unused markers), keep the markers in the template skeleton (useful to the AI).

### 3.4 How to Leave Slots: Two Kinds of Slots, Two Ways to Leave Them

Slots come in two kinds, corresponding to the two mechanisms in Chapters 4 and 5, and are left differently:

**(1) Single-value slots — mark directly with `data-property`, keep it.**

Title, model, image, firmware version — these are "fill one value at one position" slots, and the approach is the simplest: leave a `data-property` on the element to mark what slot it is, and the AI fills the corresponding value from the manifest.

```html
<!-- Template skeleton: leave the slots -->
<h1 data-property="device-marketing-name">Device Name</h1>
<span data-property="device-model-number">Model Number</span>
<div data-property="device-image"></div>

<!-- Finished page after the AI fills from the manifest (marker optional) -->
<h1>DDPM Mouse</h1>
<span>MS3320W</span>
<div><img src="mouse-ms3320w.png" alt="DDPM Mouse"></div>
```

These `data-property` should stay — they are clean slot markers and involve no runtime show/hide.

**(2) Variant / list slots — do not pre-embed multiple sets then hide; switch to "generate only the needed one at generation time."**

Connection type (wired/bluetooth) is a variant slot; the feature zone is a list slot. The old way wrote every possibility into the template and hid the rest with `display:none` via `data-property` — **this is exactly the responsibility-B that should be retired.**

```html
<!-- ❌ Old way: write both blocks, switch at runtime via attribute + display:none -->
<div data-property="connection-type-wired">...USB-C...</div>
<div data-property="connection-type-bluetooth" style="display:none">...bluetooth + Unpair...</div>
```

New way: in the template, leave only one **empty slot with instructions** telling the AI "generate the corresponding block here per connectionType"; at generation time, write only the needed block (see Chapter 4's variant mechanism).

```html
<!-- ✅ New way: leave one empty slot + an instruction for the AI -->
<div data-slot="control-zone"
     data-instruction="Per the manifest's connectionType, generate only the corresponding block:
       wired → USB-C tag;
       bluetooth → bluetooth tag + battery + Unpair (all three in one block).
       Generate only the needed one; do not pre-embed all then hide.">
</div>
```

### 3.5 How to Mark for the AI: The Slot-Marking Spec

To let the AI reliably "recognize the slot + fill it correctly," it is recommended that slot markers follow a uniform convention. You can use `data-property` (single value) and `data-slot` (zone), paired with `data-instruction` for fill instructions:

| Marker | Purpose | Example |
|------|------|------|
| `data-property="<name>"` | Single-value slot; marks what value to fill | `data-property="firmware-version"` |
| `data-slot="<zone-name>"` | Zone-type slot (variant/list); content must be generated by rule | `data-slot="feature-zone"` |
| `data-instruction="<instructions>"` | Fill/generate instructions for the AI; spell out the rules and constraints | See the control-zone example above |

Writing guidelines:

- **Names correspond one-to-one with manifest fields.** The template slot name `device-marketing-name` has a "marketing name" in the manifest to match; the AI maps by name, not by guessing.
- **Zone slots must carry `data-instruction`.** Any slot that must "pick one block per connectionType" or "loop over the feature array" must have the rule written into the instruction, so the AI knows how to generate rather than just fill a value.
- **The content of `data-instruction` may match the category's AGENTS.md rules.** Let the template's instructions and the category rules corroborate each other, so the constraints the AI reads on both sides are consistent.
- **Single-value slots use `data-property`, zone slots use `data-slot`; responsibilities are clear.** Seeing `data-property` means "fill one value," seeing `data-slot` means "generate a block by rule."

### 3.6 The Full Correspondence: Slot → Manifest → Finished Page

Stringing the three together is the closed loop of the whole mechanism:

```
Template skeleton (leave slots)   Manifest (provide data)        Finished page (AI generates)
─────────────────────────────    ──────────────────────────    ─────────────────────────
data-property=                    marketing-name: DDPM Mouse     <h1>DDPM Mouse</h1>
  "device-marketing-name"

data-property=                    image: mouse-ms3320w.png       <img src="mouse-ms3320w.png">
  "device-image"

data-slot="control-zone"          connectionType: wired          <div>...USB-C tag...</div>
+ data-instruction                                                (generate only the wired block)

data-slot="feature-zone"          features:                      <a href="mouse-settings.html">
+ data-instruction                  - Mouse Settings →             Mouse Settings</a>
                                      mouse-settings.html         <a href="button-customization
                                    - Button Customization →        .html">Button Customization</a>
                                      button-customization.html
```

> **Chapter Summary**
> 1. Data consumption moves from "runtime" to "generation time," so the "runtime show/hide and value-fetch" use of `data-property` is retired.
> 2. `data-property` is demoted to a "generation-time fill marker": keep it in the template as a slot marker, drop it in the finished page.
> 3. Single-value slots use `data-property` directly and keep it; variant/list slots do not pre-embed multiple sets and hide them — switch to empty slot + `data-slot` + `data-instruction`, generating only the needed content at generation time.
> 4. Slot names correspond one-to-one with manifest fields; zone slots must carry fill instructions; the AI maps and fills accordingly.

---

## 4. Core Mechanism One: Variants — Using the Control Zone as an Example

This chapter covers the first core mechanism. First, establish a key distinction that determines which mechanism you should use.

### 4.1 The Key Distinction: Variant vs. List

The "variable content" in a UI actually comes in two kinds, handled by completely different mechanisms; never mix them:

- **Variant problem:** Pick one out of a "finite, mutually exclusive, enumerable" set of forms. For example, a device's connection method — either wired or bluetooth, never both at once. This is handled by a "discrete state machine" (this chapter).
- **List problem:** A same-kind set of indefinite, growable count. For example, feature buttons — some models have 2, some have 4, future ones may have 5. This is handled by "data-driven loop rendering" (Chapter 5).

The Control Zone is a typical variant problem; the Feature Zone is a typical list problem. Get these two straight and most of the confusion dissolves.

### 4.2 The Spec for Writing the Control Zone

The pain point of the Control Zone: the bluetooth-connection UI must appear together with the "Unpair" button — the two are strongly correlated. If you control show/hide at the granularity of "a single element," you get bugs like "the bluetooth icon shows, the battery shows, but Unpair was forgotten" — because these elements are independent in the code and merely happen to need to appear together.

**The correct principle: package "all the UI of one connection mode" into an indivisible whole, and switch at the granularity of "mode," not "element."**

Concretely — make each connection method a complete, self-contained block:

- **The "wired block"** = the USB-C tag and everything it should contain internally.
- **The "bluetooth block"** = bluetooth tag + battery indicator + Unpair button, all three written in the same block as one indivisible unit.

The key: Unpair is no longer "an independent element that happens to also need to show," but an inherent part of the bluetooth block — structurally it belongs to bluetooth and cannot exist apart from it. This way, "strong correlation" is encoded into the structure, rather than relying on a human to remember "don't forget to also turn on Unpair when switching to bluetooth."

### 4.3 Drive With a Single Enum, Make Illegal States Unrepresentable

To further raise stability: express the current mode with "a single enum value" rather than "a pile of boolean switches."

**Anti-pattern (error-prone):** Use three booleans `showWired`, `showBluetooth`, `showUnpair` — they can combine into 8 states, most of which are illegal (e.g. "wired + Unpair").

**Pattern (stable):** Use a single enum `connectionType` that can only be `"wired"` or `"bluetooth"`. The fewer and more mutually exclusive the possible values, the less room for bugs.

```
connectionType = "wired"       // render only the wired block
connectionType = "bluetooth"   // render only the bluetooth block (carries Unpair)
```

This is state-machine thinking: states are finite and mutually exclusive (wired / bluetooth, extensible to charging, disconnected, etc. in the future), each state maps to a whole block of UI, and switching states means replacing the whole block. The system can never enter a "half-wired half-bluetooth" illegal in-between state.

### 4.4 Generate Only One State by Default

Combined with the actual generation workflow: one model at a time, with one connection state by default. So the template need not "write both wired and bluetooth then hide one"; it writes only the needed block per this model's `connectionType`. Other connection states, when needed, are swapped in by a separate prompt telling the AI to replace this block. This keeps the generated output clean, carrying no unused hidden code.

> **Control Zone Spec Summary**
> 1. Each connection method = one self-contained, indivisible block; strongly correlated elements (e.g. bluetooth + Unpair) must be written within the same block.
> 2. Drive the whole-block switch with a single enum `connectionType`; do not use multiple boolean switches.
> 3. By default generate only the one state the current model needs; do not pre-embed all states then hide.

---

## 5. Core Mechanism Two: Lists — Using the Feature Zone as an Example

The pain point of the Feature Zone: some models have 2 features, some have 3–4, and future products will add new feature modules. If you write every feature button into the HTML up front then hide them, you fall into "every new feature means editing the shared template, and the feature list is buried in display state."

### 5.1 The Data-Driven Rendering Principle

**The correct principle: the template only defines "what one feature button looks like" and "which slot they sit in"; what features exist is decided by data.**

That is, split the Feature Zone into two parts — on the template side, an empty container + one "feature button" rendering rule (given an icon and text, produce a button); on the data side, each model's feature array. At render time, loop over the array and produce as many buttons as there are items; the template does not care whether it's 2 or 4.

This directly answers two concrete questions:

- **"Some models have 2, some have 4"** → just different array lengths; zero template change.
- **"Future new feature modules"** → add an item to the data; the template structure stays unchanged. The extension point is always in the data, not the code structure.

### 5.2 The Feature Registry

When the same feature is reused across multiple models, introducing a "feature registry" is more stable: maintain a list of "all possible features for the category" (each feature registered with id → icon, copy, navigation target), and have model data reference only the feature's id.

| Benefit | Explanation |
|------|------|
| Single definition | The same feature is defined in only one place; change it once and all referencing models update in sync |
| No drift | Naturally avoids "the same feature looking different across models" |
| Clear extension | Adding a feature = one registry entry + referencing its id in the models that use it; a fixed process |

### 5.3 Slot Overflow: A Fallback Rule You Must Design Explicitly

Since "the space is exactly this big" is a fixed premise, you must answer in advance: what happens when a model's feature count exceeds the Feature Zone's capacity? This fallback rule should be defined at the template layer, applying uniformly to all models of the category, rather than waiting for it to blow up the layout.

Common fallback strategies (pick one, and write it into the category's AGENTS.md): scroll within the zone; paginate; truncate + a "more" entry; or set an explicit feature-count cap for the category and reject over-limit models at review time. The point is not which one you pick, but that you "explicitly designed overflow behavior" — which is exactly the value of a fixed template.

> **Feature Zone Spec Summary**
> 1. The template only defines "button style + empty slot," not specific features; features are rendered data-driven.
> 2. Use a feature registry to define features uniformly (id → icon/copy/navigation); models reference only the id.
> 3. You must explicitly design a fallback for "feature count exceeds the space" (scroll/paginate/truncate+more/cap) and state which one in the category rules.

---

## 6. Clickability and Routing

The generated page must be clickable and navigable, not a completely static display page. This chapter covers how to land that requirement in the most robust way.

### 6.1 Implement Navigation With Real Links

The essence of "clickable + navigable": a feature button is not an ordinary container but a real link pointing to another page. The plainest, most robust way in HTML is the anchor link `<a href="target-page">` — click and it navigates, no front-end framework needed, no JS router needed; plain HTML does it.

### 6.2 A Product = a Set of Interlinked Pages

So a model is not an isolated home page but a set of interlinked pages: each feature button on the home page points to a corresponding subpage, and the subpage has a "back" link returning to the home page.

```
mouse/MS3320W/
├── index.html                  ← Home page
│     each feature button = <a href="...">
├── mouse-settings.html         ← Click "Mouse Settings" to land here
│     contains a "back" link → index.html
└── button-customization.html   ← Click "Button Customization" to land here
```

### 6.3 Hierarchy: Top-Level Entries on the Home Page, Sub-Features on Subpages

This Pilot adopts the "top-level entry → subpage" page hierarchy: the home page Feature Zone holds the entry buttons for top-level feature categories (e.g. Mouse Settings, Button Customization); clicking any entry navigates to the corresponding subpage; the specific sub-features (e.g. DPI adjustment, pointer speed, scroll settings) are displayed on the subpage. In other words, the home page is the first level (top-category entries) and the subpage is the second level (sub-features).

**Key design point:** "which top-level entries exist" and "where each entry navigates" are bound — each feature in the manifest carries both `label` (button text) and `link` (navigation target). When generating the home page, write both into the `<a>` tag: the text shows `label`, the `href` is `link`. This makes the button clickable by birth, with a clear navigation target.

### 6.4 Site Structure Comes From the Manifest

Thus the manifest describes not only "what to display" but also the entire product's page map: how many top-level entries = how many buttons on the home page = how many subpages to generate; what sub-features each entry has = what goes in the corresponding subpage. One manifest spells out both the content and where you can navigate to and what's there.

---

## 7. The Operational Entry Point: The Model Spec (Manifest)

All the preceding mechanisms ultimately get "fed" to the generation workflow through one thing: the "manifest." The manifest is a given model's product requirements doc / content spec — a table that, before you write any HTML, spells out in structured text "what this page should present and where it can navigate."

### 7.1 What the Manifest Should Contain

| Section | Content | What It Drives |
|------|------|---------|
| Model identity | Marketing name, model number, firmware version, PPID, etc. | Header text |
| Device image | Main image path | Device image zone |
| Connection method | wired / bluetooth (one by default) | Which block the Control Zone renders (variant mechanism) |
| Features (top-level entries) | Each entry's text `label` + navigation target `link` | Feature Zone button count and navigation (list mechanism + routing) |
| Subpage content | Which sub-features each subpage displays | Each subpage's content |

### 7.2 Manifest Example (Mouse Pilot)

The following is an illustrative structure (sub-features are placeholders; fill in real ones in practice):

```
Model identity:
  Marketing name: DDPM Mouse
  Model:          MS3320W
  Firmware ver:   1.0.0.0

Device image:
  Main image:     mouse-ms3320w.png

Connection method: wired

Features (top-level entry → subpage):
  Entry 1 — Mouse Settings        → mouse-settings.html
  Entry 2 — Button Customization  → button-customization.html

Subpage content:
  mouse-settings.html:       DPI adjustment, pointer speed, scroll settings
  button-customization.html: key remapping, macro settings
```

> **The Role of the Manifest**
> The manifest is a "generation-time input," not a "runtime dependency." Because you generate one model at a time and never need to dynamically switch models within a page, the manifest's mission is to help you and the AI align on "what to generate this time"; the AI then produces content-baked-in, link-ready, clickable-and-navigable finished HTML, and the manifest's mission is complete once generation finishes.

---

## 8. How to Apply This to Other Product Categories

This document uses Mouse as the example, but all mechanisms are universal. To replicate it to Keyboard, Headset, Display, or any category, follow these steps.

1. Create an independent folder for the new category under repo (e.g. `keyboard/`), physically isolated from other categories; reference the same `shared/tokens.css` to keep visual consistency.
2. Design the category's own template skeleton — zone division and dimensions per that category's real form (Keyboard, Headset, Display feature zones are inherently different structures, which is exactly the reason to store each separately).
3. Identify the "variants" and "lists" in the category: anything "pick one of a finite mutually exclusive set" (e.g. connection method, working mode) uses Chapter 4's state-machine mechanism; anything "an indefinite same-kind set" (e.g. feature entries) uses Chapter 5's data-driven rendering.
4. Build a feature registry for the category, registering all its possible features (id → icon/copy/navigation).
5. Reuse Chapter 6's clickable routing: top-level entries on the home page, sub-features on subpages, linked with real `<a href>`.
6. Write the above rules into the category folder's `AGENTS.md`, so the AI and the team are constrained into a stable pattern at generation time.
7. For each new model, add only one manifest (Chapter 7), without altering the template.

**Substitution mapping:** Replace "Mouse / connection method / Mouse Settings" in the example with the target category's "category name / that category's mutually exclusive variant / that category's top-level feature entries." The mechanism stays the same; only the content changes.

### 8.1 Long-Term Risk and Mitigation: Drift

With each category stored separately, the only real long-term risk is drift — six or seven template sets each evolve, and over time the headset's connection tag and the mouse's connection tag quietly grow apart, eroding design consistency.

Mitigation relies not on "forbidding duplication" but on discipline: first, shared design tokens hold the baseline visual consistency; second, each category's `AGENTS.md` hard-states "must reference `shared/tokens`, must follow the unified design spec," so the AI auto-aligns at generation time; third, periodically have humans or AI spot-check whether common elements across categories are still consistent. Put the responsibility for consistency on "the rule files + tokens," not on "code must not repeat."

---

## 9. Scaling Rules: Using a Skill Tree for Fine-Grained Rules and Multi-Level Subpages

The preceding chapters solved "how to generate a single page." But as subpages multiply and controls get finer, a problem emerges that truly determines whether the system can scale: **if you pile all generation rules into AGENTS.md, then as pages multiply and rules get finer, this file will eventually become unwritable and the AI's context burden will balloon without limit.** This chapter solves this "rule explosion + multi-level subpages" problem.

### 9.1 The Essence of the Problem: Mistaking "On-Demand Rules" for "Always-On Rules"

Rules actually come in two natures, and mixing them causes the explosion:

| Type | How It Loads | Carrier | Consequence |
|------|---------|------|------|
| Always-on rules | Fully loaded at the start of every session, occupying context throughout | `AGENTS.md` | The bigger, the heavier the burden — must stay small |
| On-demand rules | Not loaded normally; read into context only when actually used | Skill (`SKILL.md`) | Can be unlimited; any one task loads only what it uses |

The root of context explosion is writing fine, fragmented rules that should be "on-demand" (how to generate DPI, how to lay out a subpage) as "always-on." **The fix is not to write rules shorter, but to move them from "always-on" to "on-demand" — i.e. from AGENTS.md into Skills.**

How Skills save context: at session start, the AI sees only each Skill's "name + one-line description" (very cheap); only when a Skill is relevant to the current task or is explicitly invoked does it read the full body. So you can have hundreds of Skills, but any one task loads only the one or two it needs — **the total rule count can grow without limit, while the per-task context burden stays constant.**

### 9.2 The Decisive Boundary: What Is a Skill, What Is Content

This is the foundation of this chapter and of the whole scaling system. There is only one criterion for judging whether something should be a Skill:

> **Predictable and reusable → Skill; unpredictable and different for every product → content (written into the manifest).**

Specific content can never be a Skill; only generic things can. By example:

| Thing | Predictable? | Belongs to |
|------|-----------|------|
| How to generate a home page (empty skeleton + slots) | Determined up front | Skill |
| How to generate "a generic subpage" framework | Determined up front | Skill |
| How to draw controls like DPI, primary key, left/right adjust | Just these few, recurring, determined up front and highly reusable | Skill (with preset template) |
| Whether this subpage is called Mouse Settings or Mouse Configuration | Known only when you see the requirement | Content (manifest) |
| Which features this subpage holds, and each one's parameters | Known only when you see the requirement | Content (manifest) |

**Critical warning: the name itself is content.** The moment you want to name a Skill `gen-mouse-settings`, you have already welded a piece of content ("what this subpage is called") into the Skill. The correct subpage Skill carries no specific name; it is called `gen-subpage`, and what it's called is decided by the manifest's `title` field. This way it never breaks because the user renames things (mouse setting → mouse configuration).

### 9.3 A Subpage Needs No "Dedicated Skill," Only a "Framework Skill + Manifest"

A correction follows directly from 9.2: **there is no such Skill as `gen-mouse-settings`.** What exists is a generic "subpage framework" Skill that doesn't care what the subpage is called or contains; it does just one thing, determined up front:

> Give me a subpage manifest (title + a set of controls + each control's parameters), and I'll lay it out per the unified framework, invoke the corresponding control Skill for each, and wire up the back-to-home link.

So Mouse Settings and Button Customization use **the same framework Skill**; the difference is only the manifest fed in:

```
Manifest A → gen-subpage → title "Mouse Settings", holds [DPI, pointer speed, scroll]
Manifest B → gen-subpage → title "Button Customization", holds [key remap, macro]
```

The framework is written up front (independent of name and content); the name and content come from the manifest (filled only when the requirement appears). **Any new subpage, any new name in the future needs no new Skill — just write a new manifest.** This unties the knot of "how can a subpage Skill possibly be written up front": you don't think up each subpage's Skill in advance, you write up front one framework Skill that can hold any subpage.

### 9.4 The Control Layer: Known → Template / Unknown → Fallback / High-Frequency → Promote

The specific controls inside a subpage (DPI, left/right adjust) differ from the subpage name — they have reusability (a DPI slider appears across many models). So controls are handled this way, forming a mechanism that grows naturally:

- **Known controls → promote into a Skill (with preset template).** Recurring ones like DPI, toggle, dropdown become Skills like `control-dpi`, storing the template fragment, default params, and styles in the Skill directory. When needed, take the ready template directly, no on-the-spot invention.
- **Unknown controls → go to a generic fallback Skill.** A `control-generic` Skill, targeting no specific control, only writes "how to generate a compliant control from scratch per the design tokens and standard control structure." The first time you meet an unseen control, generate it via this.
- **High-frequency → promote into a dedicated Skill.** A control originally generated via the fallback, if reused repeatedly later, gets solidified into a dedicated control Skill.

This way the control library need not predict all controls up front; it "grows naturally as you use it."

### 9.5 The Corrected Structure

```
mouse/
├── AGENTS.md                       ← Outline + signposts (always-on, tiny)
│
├── .agents/skills/                 ← Skill count converges, writable up front
│   ├── gen-homepage/SKILL.md       ← Generic home-page framework
│   ├── gen-subpage/SKILL.md        ← ★Generic subpage framework (holds any subpage)
│   ├── control-dpi/SKILL.md        ← Known control + preset template
│   ├── control-toggle/SKILL.md     ← Known control + preset template
│   └── control-generic/SKILL.md    ← ★Fallback generation rule for unknown controls
│
└── models/                         ← Content grows without limit, unpredictable
    └── MS3320W/
        ├── home.manifest            ← Home-page content
        ├── mouse-settings.manifest  ← Subpage content: name + control list (filled per requirement)
        └── button-customization.manifest
```

Note the fundamental difference between the two columns: **the Skill column is finite and writable up front (home framework, subpage framework, a few controls, fallback); the manifest column is infinite and unpredictable (each model's, each subpage's specific name and content).** Rules don't explode (Skills converge), content grows freely (add as many manifests as you like).

### 9.6 AGENTS.md Holds Only the "Map," Not the Details

Under this structure, AGENTS.md retreats to its proper role — a tiny "map / signpost" that only says "which Skill for which task," holding no specific generation rules:

> Generate the home page → use `gen-homepage`; generate any subpage → use `gen-subpage`, filling title and controls per the manifest; controls inside a subpage → known ones use the corresponding `control-*`, unknown ones use `control-generic`.

The AI reads this small map first, then fetches on demand the Skills it actually needs this time. When generating Mouse Settings, it loads only `gen-subpage` + the few `control-*` it uses, never pulling in the rules of Button Customization, Keyboard, or Headset. **The total rule count can grow without limit, AGENTS.md stays forever small and writable, and the per-generation context burden stays constant.**

> **Chapter Summary**
> 1. Move "on-demand rules" from AGENTS.md into Skills; dissolve "rule explosion" with "on-demand loading."
> 2. Criterion: predictable and reusable → Skill; unpredictable and per-product → content (manifest). The name itself is content.
> 3. Subpages get no dedicated Skill, only one generic `gen-subpage` framework Skill; name and content come from the manifest.
> 4. Controls: known → template Skill, unknown → `control-generic` fallback, high-frequency → promote to dedicated Skill.
> 5. AGENTS.md holds only the "map" (which Skill for which task); all detail sinks into Skills.

### 9.7 Getting the AI to Actually Use Skills: Forced Invocation and Template Source Files

After sinking rules into Skills, you hit a real pain point: **with many Skills, the AI may "pretend not to see them," regenerate things from its own general ability, and not read or use the Skills.** This section solves "how to force the AI to invoke Skills," plus a powerful physical means — putting pre-written template source files inside the Skill.

#### 9.7.1 Why the AI Skips Skills

Whether the AI invokes a Skill depends on the "description" line it sees at session start, and then **it decides for itself** whether to use it. The problem is in "deciding for itself" — when the trigger signal isn't strong enough, or there are so many Skills that it can't choose, it takes the shortcut: generate directly from general ability and skip the Skill. So "forcing it to use them" is not a single switch but pressure applied from multiple layers at once, sealing off the "generate it myself" escape route.

#### 9.7.2 Four Layers of Pressure: Seal Off "Skipping"

**Layer 1 — Write the Skill's description as a "trigger," not an "intro."** The most effective and most overlooked move. The description should not say "what this skill does" but "**when you must use me**."

- ❌ Weak (intro): `framework for generating subpages`
- ✅ Strong (trigger): `When the task involves generating any subpage (settings page, config page, etc.), you must use this skill; do not write subpage HTML yourself.`

Writing "must" and "do not generate it yourself" right into the description hands the criterion to the AI's lips, leaving fewer excuses to skip.

**Layer 2 — Write AGENTS.md as "hard routing," not "suggestions."** Upgrade the wording from "use Y when X" to imperative form:

> Generating a subpage **must and may only** go through `@skills:gen-subpage`. It is **forbidden** to bypass the skill and write subpage HTML by hand. If a relevant skill exists but was not used, it counts as a violation and must be redone.

**Layer 3 — Use "explicit invocation" to bypass "self-judgment."** The most reliable approach is not to let the AI decide whether to use them, but to **name** the invocation in the instruction/rules. A Skill's auto-trigger (AI judges) is exactly the path it will "pretend not to see"; explicit trigger (`@skills:xxx`) it cannot bypass. So hard-wire the invocation chain into the prompt template or AGENTS.md flow:

> When generating a model page, invoke explicitly in order: home page → `@skills:gen-homepage`; each subpage → `@skills:gen-subpage`; each control → the corresponding `@skills:control-*`.

**Layer 4 — Add a "self-check + redo" rule so skipping gets caught.**

> After finishing, self-check: did this generation invoke all relevant skills? Is there any hand-written content where a skill could have been used? If so, you must discard and redo using the skill.

#### 9.7.3 Facing the Root Cause: Too Many Skills Dilutes Attention

"The AI gets confused when there are many skills" is real. The fix is layered convergence + controlling the count visible per layer: group Skills with directories (e.g. control Skills under `controls/`), don't lay dozens flat in front of the AI; ensure that **for any task at any level, the AI has only a few Skills to choose from**; the more mutually exclusive and non-overlapping the descriptions, the less the AI suffers choice paralysis among similar Skills and gives up. In a word: at every step, let the AI face only "a few, clear, mutually exclusive Skill options with strong trigger words."

#### 9.7.4 The Physical Means: Put Pre-Written Template Source Files Inside the Skill

This is the most powerful move against "regenerating from scratch" — **when a ready template sits inside the Skill and the rule just says "copy this file," the AI's room for improvisation is physically compressed.**

Key realization: **a Skill is not a Markdown file, it is a folder.** `SKILL.md` is merely the entry description; the folder can hold any supporting assets, including pre-written HTML template source files:

```
gen-subpage/
├── SKILL.md                    ← Entry: instructions + pointers to the templates below
└── templates/
    ├── subpage-frame.html      ← Pre-written subpage framework source file
    ├── control-slot.html       ← Control placeholder fragment
    └── back-link.html          ← Back-link fragment
```

Then in `SKILL.md`, point to these source files with **relative paths**, and write the rule as "copy + fill," not "generate":

> When generating a subpage, **copy** `templates/subpage-frame.html` as the skeleton; **do not write from scratch**. Per the manifest, fill the title into the `data-property="subpage-title"` slot, and for each control, copy `templates/control-slot.html` and invoke the corresponding control skill to fill it.

The three benefits of doing this exactly counter "skipping the Skill":

- **Demotes from "creation" to "copy + fill-in-the-blanks."** The AI need not invent what a subpage looks like; it just takes the ready file and fills slots. Room to go off-track is greatly compressed and output is more consistent.
- **Gives the AI a hard reason it "must use the Skill."** The template source file exists only in the Skill directory; to produce correctly the AI must read and copy it — it cannot "pretend it doesn't exist," because there is nowhere else to get this template.
- **Template and rule are same-source, same-version.** Change the template by changing that file in the Skill directory, and all references automatically use the new version, with no "rule says one thing, template is another" drift.

Implementation note: **use paths relative to the Skill directory** (e.g. `templates/subpage-frame.html`), so the reference holds wherever the Skill is copied — any category, any repo. This is also an expression of the Skill being self-contained and portable.

#### 9.7.5 The Optimal Combination: Physical Layer + Behavioral Layer Together

Stacking the two things gives the strongest combo against "the AI skipping Skills and generating junk":

1. **Put ready template source files inside the Skill** → make the Skill the only source of correct output, physically cutting off the "generate it myself" escape route.
2. **Strong trigger words in the description + hard routing in AGENTS.md + explicit `@skills:` invocation + post-generation self-check** → seal off skipping at the behavioral level.

With the physical layer (templates only in the Skill) and the behavioral layer (rules force invocation) working together, the AI has "no reason to skip," "gets caught if it skips," and "can't produce correct output even if it does."

> **Section Summary**
> 1. The AI skips Skills because of "self-judgment + too many Skills"; the fix is multi-layer pressure + fewer visible options per layer.
> 2. The description must read as a "when you must use me" trigger; AGENTS.md uses imperative form; key flows name `@skills:` explicitly; self-check and redo after generation.
> 3. A Skill is a folder and can hold pre-written HTML templates; the rule says "copy + fill" not "generate," referenced by relative path.
> 4. Templates exist only in the Skill directory, physically cutting off the AI's "generate it myself" route — the most powerful forcing mechanism.

---

## 10. Execution Rule Checklist (Ready to Paste into AGENTS.md)

The following compresses this methodology into hard rules, ready to serve as the content of a category's AGENTS.md, constraining every generation by the AI and team.

### 10.1 Structure and Isolation

- Each product category uses an independent, self-contained folder and templates, physically isolated, with no cross-references.
- All categories share only `shared/tokens.css` (color, font, size baselines), not layout structure.
- The template carries only "layout + empty slots + single-part styles"; product differences are all sunk into data (the manifest).

### 10.2 Slots and Markers

- The template declares each fill position with slot markers: single value uses `data-property="<name>"`, a zone (variant/list) uses `data-slot="<zone-name>"`.
- Zone slots must carry `data-instruction="<instructions>"` spelling out generation rules and constraints, consistent with the category rules.
- Slot names must correspond one-to-one with manifest fields; the AI fills by name, not by guessing.
- It is forbidden to "pre-embed multiple UI sets then hide with `display:none`"; variant/list slots are uniformly switched to empty slot + generate only the needed content at generation time.
- `data-property` is used only as a generation-time fill marker, never for runtime show/hide or value-fetch; markers in the finished page may be removed (no runtime impact).

### 10.3 Control Zone (Variant)

- Each connection method = one indivisible self-contained block; strongly correlated elements (e.g. bluetooth + Unpair) must be written within the same block.
- Drive the whole-block switch with a single enum `connectionType`; do not patch show/hide with multiple boolean switches.
- By default generate only the one connection state the current model needs; do not pre-embed all states then hide.

### 10.4 Feature Zone (List)

- Feature Zone buttons must be rendered from a data array; it is forbidden to hardcode specific features in the template then hide them.
- Use a feature registry to define features uniformly (id → icon/copy/navigation); model data references only the id.
- You must explicitly design a fallback for "feature count exceeds the space" (scroll/paginate/truncate+more/cap) and state which one in this rule set.

### 10.5 Clickability and Routing

- Feature entries must be real `<a href>` links, clickable and navigable; it is forbidden to generate non-interactive purely static display pages.
- Adopt the two-level structure "top-level entries on the home page, sub-features on subpages"; subpages must contain a link back to the home page.
- Each feature carries both `label` and `link` in the data, written into the `<a>` tag together at generation time.

### 10.6 Rule Scaling (Skill vs. Content)

- Split rules by nature: always-on outline goes in `AGENTS.md` (keep it tiny), on-demand detail goes in Skills (`SKILL.md`).
- Hold the boundary: predictable and reusable → make a Skill; unpredictable and per-product → leave as content (manifest). It is forbidden to write specific content (including subpage names) into a Skill.
- Subpages get no dedicated Skill; uniformly use one generic `gen-subpage` framework Skill, with title and control list provided by the manifest.
- Controls: known controls use the corresponding `control-*` Skill (with preset template); unknown controls go to the `control-generic` fallback; high-frequency ones get promoted to a dedicated Skill.
- `AGENTS.md` holds only the "map" (which Skill for which task), not specific generation detail.
- A Skill's description must read as a "when you must use me" trigger and explicitly state "do not generate it yourself"; pure intros are forbidden.
- Key flows must invoke `@skills:` explicitly by name, not rely on the AI's self-judgment; AGENTS.md uses imperative form (must/forbidden) and requires post-generation self-check of "is there any hand-written content where a skill could have been used," redoing if so.
- Any Skill with a pre-written template stores the template source file inside the Skill directory, referenced by relative path; the rule says "copy + fill" not "generate from scratch," making the Skill the only source of correct output.
- Converge Skills by directory grouping, ensuring that for any task at any level the AI faces only a few selectable Skills with mutually exclusive, non-overlapping descriptions.

### 10.7 Generation Workflow

- Generate one model at a time; with one manifest as input, produce content-baked-in, link-complete finished HTML.
- Add only a manifest for a new model, without modifying the template; register a new feature in the registry first, then reference it in the model.
- After generation, run a clickability self-check: each entry is clickable, navigation targets exist, subpages can go back.

---

*This methodology is validated with Mouse as the Pilot. The mechanisms are universal and can be directly replicated to Keyboard, Headset, Display, Audio, and all other product categories.*
