# Render-engine implementation plan — making Phase 3 deterministic by code

> Status: plan (reviewed against the codebase). Supersedes the earlier directive-template sketch
> (see §3 — that idea was rejected as reinvention). Prototype: `render-content.py` on branch
> `feat/renderer-prototype`.

## 0. What this is — and why it is NOT a new architecture

The codebase already defines a three-phase pipeline (`docs/ui-generation-flow.md`): **Phase 1 authoring**
(strong model reasons, freezes intent into a manifest) → **Phase 2 gate** (`validate-manifest.py`) →
**Phase 3 generation** (deterministic: copy frame, fill from `home.manifest`, copy/assemble each
function, strip markers → "baked reproducible HTML"). Phase 3's steps are written out, in order, in
three SKILL procedures: `headset-gen-homepage`, `headset-gen-subpage`, `headset-function`.

Phase 3 is **specified as deterministic** but **executed by an LLM following prose**. We proved an LLM
cannot do that deterministically (same manifest → 8–10 distinct pages, low or high effort). And the
codebase already anticipated the fix: **decision D17** says the snapshot is a derived product, the
`headset-function` assembly logic is *"the seed of a future build step,"* and a *"spec→assemble→snapshot"*
automation should land *"when cards multiply."* **D18/D19** set the discipline: minimal generation,
*"the output must be exactly what re-running produces; no off-pipeline hand-patching."*

**This plan implements that already-anticipated build machine (`render.py`).** It moves Phase 3 from
LLM-followed prose to code. It introduces **no new flow, no new vocabulary, no new architecture** — it
codifies the existing procedures and reuses every existing mechanism.

## 1. The wheels we REUSE (do not rebuild)

| Existing thing | Role in `render.py` | We do NOT |
|---|---|---|
| `ui-generation-flow.md` Phase 3 | the spec being implemented | redesign the flow |
| `gen-subpage/SKILL.md` Procedure 1–9 | the sub-page render steps, verbatim | re-derive steps |
| `gen-homepage/SKILL.md` Procedure 1–7 | the home-page render steps | re-derive steps |
| `headset-function/SKILL.md` Procedure 1–6 | the assemble path (D17's "seed") | reinvent assembly |
| `validate-manifest.py` + `archetypes.py` | the gate + contract; render runs **after** a clean gate | duplicate validation |
| `parse_manifest()` (in the validator) | the manifest parser, imported | write a new parser |
| `subpage-frame.html` / `home-frame.html` | read + slot-filled | regenerate frames |
| `components/*.html` | the markup units — **read from file** and filled | inline-copy their markup |
| `functions/*.html` snapshots | copied whole (+ the existing UNWRAP rule for nested) | re-render their internals (D18/§9.1) |
| `connection/*.html` + `unpair.html` | copied by `connectionType` | write connection markup |
| `ICON-INDEX.md` + `icons/` + `segment-icons/` | key→file copy (closed registry, HALT-on-miss) | a new icon mechanism |
| `feature-button.html` | repeated per `features[]` | write button markup |
| the strip step (`data-slot/instruction/property`) | the existing final step | a new cleanup |
| the CSS-path `sed` rewrite (4-up → output depth) | the existing step 1 | a new path scheme |

## 2. What `render.py` actually is

A program that **executes the SKILL procedures as code**:

- **Sub-page:** `gen-subpage` Procedure steps 1–9 — copy frame + rewrite CSS paths; read both manifests;
  fill device identity from `home.manifest` (omit PPID line if absent — already step 3); copy the
  `connection/<type>.html` block + battery; repeat `feature-button.html` per `features[]` with its
  icon; render the `functions[]` content area; keep the back link; strip markers.
- **Content area:** `headset-function` Procedure 1–6 — per function: snapshot exists → copy whole (rare
  per-slot override, D18); else assemble shell + one `components/<archetype>.html` per entry; build
  `.segment-panels` from `reveals` (one panel per option, in order); wrap `.subfn-group` from
  `dependents`; the `.subfn-label` rule; UNWRAP a nested `{function:<id>}`; segment icons via ICON-INDEX.
- **Home page:** `gen-homepage` Procedure 1–7 (incl. Unpair on paired home pages only; feature→sub-page
  build obligation).

The only "logic in code" is a **bounded per-archetype handler** (toggle/slider/segmented/preset-grid/
dropdown — the same closed set in `archetypes.py`). Each handler **reads its snippet file** and applies
the structure rule the procedure already specifies (repeat the segment unit per option, build N panels,
wrap a group, prepend a `.subfn-label`). This is the existing assembly logic, made executable — not new.

Honors: **D8** (id-only routing, no keyword match), **D11/D12** (reveals/dependents pre-embed + CSS
`:has()`, the deliberate §3.1 override), **D18** (snapshots are frozen leaves), **D19** (reproducible).

## 3. Considered and REJECTED — to avoid reinventing a wheel

**A `data-render-*` directive-template language on the snippets** (my earlier draft). Rejected: it
contradicts the codebase model, where assembly logic lives in the *procedure* (`headset-function`), and
a snippet is only *markup + `{slots}`*. Adding directives would invent a **parallel marker system**
beside the existing `{placeholder}` / `data-property` / `data-slot` — exactly the duplication the
review is meant to prevent. Instead `render.py` **reads the snippet's markup unit** and applies the
already-specified per-archetype logic in code. Snippets stay single-source, **zero new conventions**.

This is also how we pay down the prototype's only debt the *codebase-aligned* way: `render-content.py`
currently inlines atom markup (a second copy). The fix is **read the snippet file**, not annotate it.

## 4. Home manifest: reuse the `archetypes.py` + validator pattern (don't invent)

The `home.manifest` fields are today described **informally in two SKILL `Inputs` sections**, and the
PPID-omit rule lives in the procedures. We consolidate them into **one machine-readable home contract**
(mirroring `archetypes.py`) and **extend `validate-manifest.py` to gate `home.manifest`** (mirroring the
sub-page gate). Field optionality + absence rules are in `docs/home-manifest-schema.md` (required:
`marketing-name`/`model-number`/`connectionType`; optional-omit: `firmware`/`ppid`/`image`; conditional:
`battery` via the connection snippet; `features` optional → homepage-only when empty; `icon` via the
existing ICON-INDEX). **Same wheel (contract + gate), applied to home** — no new pattern.

## 5. Phased plan

- **Phase 1 — content area (pays down the prototype debt).** Implement `headset-function` Procedure +
  `gen-subpage` step 7 as code that **reads `components/*.html` + `functions/*.html`** (no inline
  markup). Accept: `valid.manifest` → 10/10 byte-identical, markup sourced from the snippet files,
  structure matches the procedure.
- **Phase 2 — full sub-page.** Implement `gen-subpage` steps 1–9 (frame, device identity, connection,
  feature-nav, content, back link, strip, CSS-path). Prereq: the home contract + home gate (§4). Accept:
  full-page 10/10 — the exact test the LLM failed.
- **Phase 3 — home page.** Implement `gen-homepage` Procedure 1–7 (incl. Unpair, feature→sub-page build
  obligation). Accept: `index.html` 10/10.
- **Phase 4 — wire in.** `render.py` becomes the executor the SKILLs delegate to; their prose procedures
  shrink to "run render.py" and become its human-readable spec (like `archetypes.py` ↔ the docs). The
  LLM's role narrows to authoring the manifest + drafting a NEW snippet/snapshot once (Lane 2). The gate
  still runs before render.
- **Phase 5 (optional) — designer picker.** Expose `archetypes.py` `alternatives` so an editor offers
  legal presentation swaps (dropdown↔segmented↔preset-grid); a swap is one gated manifest-field edit.

## 6. Truth-source reconciliation (per `navigation.md` §4 — no duplication)

| Topic | Single truth source (after this plan) | Others |
|---|---|---|
| Phase-3 assembly steps | the SKILL procedures **are the spec; `render.py` is the executor** — they must stay in lock-step (one implementation, prose mirrors code) | — |
| component contract | `archetypes.py` (exists) | validator + render read it |
| **home-manifest shape** | **new home contract** (consolidates the two SKILL `Inputs`) | SKILLs reference it; remove the informal duplication |
| routing / non-negotiables / control selection | `headset/AGENTS.md`, `AGENTS.md`, `component-catalog.md` (unchanged) | render.py must not restate them |
| design rationale | `function-card-architecture.md` (unchanged) | — |

This doc **replaces** the earlier `hybrid-compiler-design.md` directive sketch (avoid two overlapping
design docs). `home-manifest-schema.md` stays as the home field spec.

## 7. Risks & discipline (honoring existing decisions)

- **Drift between `render.py` and the SKILL prose** → make `render.py` THE executor; the procedure
  points to it. Never maintain two implementations of the same step.
- **Determinism masks bugs** (consistently wrong) → **golden-file tests**: commit a known manifest's
  expected HTML and diff every change. This also makes D19's "reproducible" discipline mechanical.
- **`dropdown` is a known gap** (D22: the full-row `dropdown.html` is deferred; no manifest uses
  `archetype: dropdown` yet). Phases 1–2 cover toggle/slider/segmented/preset-grid; dropdown lands with
  its snippet.
- **Snapshots stay frozen leaves** (D18 / §9.1) — copy whole, never re-render internals; nested ones use
  the existing UNWRAP rule.
- **Do not grow `render.py` with per-function special cases** (methodology §2.1 "the wrong abstraction is
  costlier than duplication") — a new presentation = a new snippet/archetype, never an `if` in the engine.
- **Lane 2 stays an authoring-time event** — the gate already forces every passing manifest to be
  Lane-1-renderable, so render-time fallback is rare; a genuinely new control = draft a snippet once,
  promote it (the existing §9.4 "grow on demand").
