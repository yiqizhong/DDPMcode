# Component-import scalability plan

> Status: **backlog**. NOT triggered by a failure. Written ahead of the first real-design import so
> the mechanism is ready before it is needed. Scope: make the deterministic render pipeline cheap to
> feed with *replacement* DDPM Component markup that originated in Figma and was converted to HTML
> **outside** this repo, then dropped in. This is a presentation swap, not a data-model change.

## 0. The workflow this plan serves (constraints, stated)

- Today's `components/*.html` snippets are **placeholders for testing**, not the final design.
- The real design lives in Figma. The import path is **Figma → external HTML/CSS conversion → drop the
  HTML in here**. We are NOT linking Figma live and NOT generating markup from a description.
- "Official design" is normally an **appearance change** (markup + CSS). The **data shape is stable** —
  a toggle stays label+boolean, a selector stays an `options` list, etc.

Consequence of that last point: the manifest data contract (`archetypes.py`) should NOT have to change
for an import. The whole cost lands on the **markup + CSS** layer. So the only scalability question that
matters is: *how cheaply can an externally-converted HTML component be conformed to what the renderer
expects, and how isolated can its CSS be?*

## 1. What "import a component" touches today — the three-artifact contract

A DDPM Component archetype exists as three coupled artifacts:

| Layer | File | Role | Changes on a reskin? |
|---|---|---|---|
| Data contract | `.agents/skills/headset-gen-subpage/archetypes.py` | width / conditional channel / options policy / required props. The validator derives every *archetype* rule from it — but snapshot-keyword routing, nested-snapshot existence, and "no `components:` on a snapshot" are separate hardcoded checks, and the manifest parser is a custom YAML subset (`validate-manifest.py:24–120`), not a general schema engine. | **No** (appearance-only) |
| Markup snippet | `.agents/skills/headset-shared/components/<arch>.html` | the copied markup with fill slots | **Yes** |
| Styles | `headset/headset.css` (one file, sectioned per component) | styles the snippet's class names | **Yes** |

The data layer is clean and single-sourced — not the problem. The problem is the **implicit contract
between the snippet and the renderer**.

### 1.1 The structural contract the renderer imposes (evidence)

`render-content.py` fills each archetype with a **per-archetype Python function**, and those functions
reach into the snippet's internals. The contract a snippet must satisfy is therefore not just "fill the
`{tokens}`" — it is a set of **landmark class names**, **repeatable-unit shapes**, and in two cases an
**externally-owned wrapper**. Mapped to code:

| Archetype | How it's filled | Coupling to snippet internals |
|---|---|---|
| `slider` | `{id}/{min}/{max}/{val}` token replace (`render_slider`, render-content.py:287) | **None beyond tokens** (it leaves a `data-property="{id}-value"` hook, but fills by token replacement, not `data-slot`). The low-coupling exemplar. |
| `toggle` | tokens + greps `.function-icons`, `.switch-input`, first `<input>` (`render_toggle`, :299) | grep on presentation class names |
| `dropdown` | greps `<li class="dropdown-item">`, `<ul class="dropdown-list">`; **builds the `.function-header` row wrapper in Python** (render-content.py:386–393) | snippet does NOT own its outer row |
| `segmented` / `preset-grid` | greps `<label class="segment">`, `.segment-panel`, `.segment-icon`, `{value1}/{label1}`; **builds the `.segmented-group` + container wrapper in Python** (render-content.py:487–491) | snippet does NOT own its outer wrapper |

Three properties fall out of this table:

1. **Implicit** — the contract lives only inside `render-content.py`. Nothing documents "to be a valid
   `segmented` snippet you MUST keep a `<label class="segment">` repeatable unit and a `.segment-panel`."
2. **Inconsistent** — `slider` is purely token-driven (structure-agnostic); the other four grep
   presentation class names; two of them don't even own their outer wrapper.
3. **Leaky** — for `dropdown` and the selectors, the outer markup is generated in Python, so a reskin
   that changes the wrapper structure forces a `render-content.py` edit, not just a snippet edit.
4. **Silent on breakage** — a snippet that violates the contract (e.g. a `dropdown` with no repeatable
   `<li class="dropdown-item">`) does NOT HALT. `render_dropdown` / `render_selector` call `lane2()`
   (render-content.py:94), which only appends to a `FALLBACKS` list and emits a `<!-- LLM-FALLBACK -->`
   comment. That list is printed only by the CLI `main()` (render-content.py:509–513); the real pipeline
   calls `render_content.render()` directly (render-subpage.py:233) and catches only `RenderHalt`. So a
   broken import renders a fallback comment, passes `validate-manifest.py` (which checks the manifest,
   not the snippet), and is **byte-stable forever**. This is the most important gap for imports.

### 1.2 Other artifacts an import may touch

`components/*.html` + `headset.css` is not the whole appearance surface. Depending on the archetype, an
import may also touch:

- **Segment-icon registry** — `segmented` with `icons: true` pulls SVGs from
  `.agents/skills/headset-shared/segment-icons/` (registry README there); the renderer HALTs on a missing
  icon (render-content.py:421–426). A reskin that changes the icon set or option values must update it.
- **Function-frame template** — `.agents/skills/headset-function/templates/function-frame.html` owns the
  card shell (`.function-container` / `.function-header` / `.function-content`) for assembled, no-snapshot
  functions; the renderer reads and fills it (render-content.py:222–235). Card-shell appearance lives
  here, not in `components/*.html`.
- **Function snapshots** — whole-card HTML under `.agents/skills/headset-gen-subpage/templates/functions/`
  bypasses component snippets entirely when a function id matches (render-content.py:214–216). Imports
  touching those cards (e.g. EQ/equalizer or promo visuals) must update the snapshot + CSS, not
  `components/*.html`.

## 2. The scalability tax, sized against the workflow

Given appearance-only imports, three cases:

- **Best case** — the converted HTML keeps the same DOM structure *and* the same landmark class names,
  changing only visual styling → the change is **CSS-only**. Already scalable.
- **Realistic case** — a Figma export brings its own `<div>` nesting and its own class names. To run
  through the renderer it must be **re-mapped onto the landmark-class contract** (and the `{token}` /
  `data-*` hooks), or the renderer must be edited. The re-mapping is manual *reverse-engineering* today,
  because the contract is undocumented (§1.1). This cost recurs per component × per import.
- **CSS** — `headset.css` is one 1.2k-line file with a flat, global class namespace. Imported styles can
  **collide**, and the file only grows. Sectioning exists but isolation does not. Worse for selectors,
  the CSS is **structurally** coupled, not just stylistic: conditional panels are wired by positional
  `:has(.segment:nth-child(N)) .segment-panel:nth-child(N)` up to 6 (headset.css:1036–1041) — the real
  reason `archetypes.py` caps `MAX_OPTIONS = 6`. A selector reskin therefore cannot freely reorder or
  restructure its segments/panels; "appearance-only" is more constrained here than elsewhere.

## 3. The core decision

Two strategies, not mutually exclusive:

**(A) Freeze and document the contract.** Leave the renderer as-is. Write the snippet↔renderer contract
down (landmark classes + tokens + data hooks + repeatable units, per archetype) and require every import
to conform to it. *Cheap, zero renderer-regression risk.* Downside: every import still does manual
conforming, and `dropdown`/selector can't be structurally reskinned without Python edits.

**(B) Decouple the renderer (make every archetype structure-agnostic).** Push all archetypes to the
`slider` model: the snippet owns 100% of its markup (including the wrapper the renderer currently
builds), and the renderer fills **only** via stable `data-slot` / `data-property` hooks plus a declared
repeatable-unit marker — never by grepping presentation class names. *Heavier; one-time refactor of
`toggle` / `dropdown` / selector.* Downside: real effort + regression risk, and the right generic hook
contract is best designed against a **real** imported component, not a placeholder.

**Recommendation: phase it.** Do **A now** (cheap, unblocks the first import and captures knowledge while
it is fresh). Do **B lazily, per archetype, triggered by the first real import of that archetype**
(second-instance rule) — not speculatively across all five. Given that imports are appearance-only,
B's payoff is real but not urgent; doing it against a real design avoids guessing the abstraction.

## 4. Threads

### Thread A — Document the contract + a fallback guard + an import procedure (now; doc + one guard)

1. Add `components/CONTRACT.md` (or extend `components/README.md`) — per archetype, the **machine-facing
   contract** that `render-content.py` actually depends on:
   - the `{token}` placeholders it replaces,
   - the `data-property` / `data-slot` hooks,
   - the **landmark class names** it greps (e.g. `dropdown-item`, `dropdown-list`, `segment`,
     `segment-panel`, `segment-icon`, `switch-input`, `function-icons`),
   - the **repeatable unit** shape (the `<li>` / `<label class="segment">` the renderer clones),
   - which **wrapper is Python-owned vs snippet-owned** (call out `dropdown` + selectors explicitly).
2. **Add a fallback guard so a broken import cannot pass silently (§1.1 property 4).** Byte-stability does
   NOT catch a degraded snippet — the `<!-- LLM-FALLBACK -->` comment is itself stable. Minimal fix: make
   `verify-model.py` fail if rendered output contains the string `LLM-FALLBACK` (a one-line grep — cheaper
   than a structural snippet-contract validator, and it closes the actual hole). A fuller per-archetype
   snippet-contract check can come later if reverse-engineering proves error-prone.
3. Add an **"import a converted component" checklist**: map converted HTML → landmark classes, keep the
   token/`data-*` hooks, drop CSS into the component's section, run `render-model.py` to regenerate, then
   run `verify-model.py` (the read-only byte gate; `test-pipeline.sh` runs two renders for byte-identity)
   and confirm it passes with **no `LLM-FALLBACK`** in the output.

This makes the contract a **single source** instead of something each importer reverse-engineers from
Python, and guarantees a malformed import fails loudly. It is the prerequisite that makes Thread B
optional rather than mandatory.

### Thread B — Make the renderer structure-agnostic (lazy; per archetype; code)

Per archetype, when its first real design lands:

1. Replace class-name greps with declared `data-slot="..."` markers the renderer already understands
   (`replace_slot_contents` / `remove_slot_element` exist — render-content.py:150, :162).
2. Move the Python-built wrapper into the snippet so the snippet owns its full markup
   (`dropdown` header at :386–393; selector group at :487–491).
3. Net effect: an imported component is conformed by **adding `data-slot` markers and keeping the
   tokens** — no presentation-class matching, no Python edit. `slider` already needs nothing beyond
   tokens; it is the low-coupling target (the `data-slot` mechanism is what the wrapper-leaky archetypes
   need to reach that state).

Order is demand-driven and scoped: do **`dropdown`, `segmented`, `preset-grid` first** — Python owns
their wrappers and repeat units, so they pay the most. **Skip `toggle`** unless a real imported toggle
genuinely cannot conform to the `.function-icons` / first-input / `.switch-input` contract.

### Thread C — CSS isolation (deferred; trigger-gated)

Trigger: the first imported design that brings conflicting class names, OR `headset.css` crossing a size
threshold we set. Then pick one:

- **Namespace convention** — every component's classes carry a component prefix, enforced by a small
  lint; `headset.css` stays one file but collisions become detectable.
- **Co-located CSS** — each component ships its CSS next to its snippet; a build step concatenates into
  `headset.css`, which becomes a generated layout-shell-plus-components artifact.

Keep `headset.css` as the layout shell either way.

## 5. Sequencing and triggers

| Thread | When | Risk | Blocks the first import? |
|---|---|---|---|
| A — document contract + fallback guard + checklist | now | low (one-line guard) | yes — do first |
| B — de-couple renderer, per archetype | on first real import of that archetype | medium (renderer regression) | no |
| C — CSS isolation | on first class-name collision / size threshold | medium | no |

## 6. Non-goals

- **No data-model change.** `archetypes.py` and the manifests stay as-is; imports are appearance-only.
  (If a real design *does* change a data shape, that is a different change — the existing
  "add an archetype = snippet + `archetypes.py` block in lockstep" rule already covers it.)
- **No live-Figma integration.** The import path is external conversion → drop-in HTML, by design.
- **No build system introduced for Thread A.** Thread C may add a concatenation step; A and B do not.

## 7. Questions resolved by review

1. **Is Thread B worth its risk vs Thread A + discipline?** Reserve B for the wrapper-leaky archetypes
   (`dropdown`, `segmented`, `preset-grid`); skip `toggle` unless a real import cannot conform. Thread A
   plus the §4 fallback guard cover the rest without touching the renderer.
2. **Thread C — namespace vs co-located+concat?** Namespace convention + a no-build lint first (pages
   link `shared/tokens.css` then `headset/headset.css`; a build step is the wrong first move for a
   no-build repo). Add concat only after repeated import pain, and only with a check that proves the
   generated `headset.css` is current.
3. **Must the import procedure run the drift gate?** Yes — but the gate is `verify-model.py` (read-only
   byte compare), not `render-model.py` (which only writes). And byte-stability alone is not enough:
   pair it with the `LLM-FALLBACK` guard (§4 Thread A), because a degraded snippet is byte-stable.
4. **Other artifacts an import touches** — documented in §1.2 (segment-icon registry, function-frame
   template, function snapshots).
