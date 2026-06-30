# Selector archetype selection — the deterministic rule

> Status: **active**. This is the authority for *how an authoring agent picks a select-family
> archetype* (`segmented` / `preset-grid` / `dropdown`). The mechanical half is enforced by
> `archetypes.py` + `validate-manifest.py`; this doc explains the rule and the reasoning the
> contract can't carry. When the two disagree, the contract (`archetypes.py`) wins.

## The problem this fixes

The archetype for a control is **chosen by the authoring agent and frozen into the manifest**;
generation just copies it. So a wrong-but-plausible choice is an authoring decision, not a render
bug — and nothing was pinning it. The validator already gated `segmented`-vs-`preset-grid` by
count, but **`dropdown` was ungated at any option count**, and the prose trigger for it was
subjective ("many options or tight space"). Result: for the *same input*, the same model picked
`dropdown` on one run and `segmented` on another — reproduced on two machines (`auto-off`,
`audio-guidance` in a real model run).

The cause is structural: the segmented-vs-dropdown boundary rested on a judgment ("is space
tight?") with no numeric line and no tiebreaker, so a stochastic model lands on either side.

## The rule

A "choose 1 of N" control resolves by **option count first**, with a small set of **declared
exceptions** — no free-form judgment:

| Options | Archetype | |
|---|---|---|
| boolean on/off | **toggle** | resolved upstream, before the select family |
| ordered **continuous** value | **slider** | a range/scale, not discrete choices |
| **2–3** | **segmented** | one horizontal row; **hard cap: 3 segments** |
| **4–6** | **preset-grid** | 2-column grid of buttons |
| **> 6** | **dropdown** | forced — overflows the 6-option selector cap |
| **≤ 6 as dropdown** | **dropdown** — only with a declared `dropdown-reason` | see below |

Because `segmented` is capped at 3, **4 options is always `preset-grid`** — the old
"4 = mode→segmented / preset→grid" semantic fork is gone. The 3 | 4 boundary is a hard line.

### The three declared exceptions (`dropdown-reason`)

A `dropdown` with **≤ 6 options** must justify itself; otherwise it should be a visible selector.
The only recognized reasons, frozen as data in the manifest:

- `ordered-value` — a value picked off an ordered/numeric list, set-and-forget (timeouts,
  durations, stepped levels). Example: `auto-off` power-off-after.
- `long-labels` — option labels too long to fit a segmented row.
- `inline-slot` — a declared structural need to sit as a compact header/row control, where a
  full-width selector physically cannot go.

No "space feels tight" escape hatch — that subjectivity is exactly what caused the flap.

## Why this is both deterministic and product-agnostic

**Deterministic.** Count is mechanical. The single remaining judgment — *keep options visible vs.
collapse them* — is converted into a **declared, defaulted exception**: the default is the visible
selector, and a dropdown for a short list is reachable only through a recognized, reviewable
reason that lives in the manifest. Two runs that produce the same tags produce the same archetype,
guaranteed. This reuses the pattern the codebase already trusts (`snapshot-opt-out` +
`opt-out-reason`).

**Product-agnostic.** The rule is expressed in abstract properties of the choice, not headset
nouns. The authoring mental model is four dimensions:

| Dimension | Nature | Drives |
|---|---|---|
| Cardinality (count) | objective (auto) | the whole count table above |
| Order | mostly detectable | continuous → slider; ordered value → `ordered-value` dropdown |
| Switch frequency × comparison cost | the one real judgment | frequent **or** compare-to-decide → keep visible; rare **and** set-and-forget → collapse |
| Label fit | measurable | long labels → `long-labels` dropdown |

Headset's specifics (durations → `ordered-value`, ANC modes → segmented, EQ presets → grid) are
*mappings* of these dimensions, not rules. A new product maps its own choices onto the same
dimensions; the core rule and the validator are untouched.

> On the third dimension: a `dropdown` is collapsed, so every look/switch costs 1–2 extra clicks
> and hides the alternatives while deciding. That is fine for something set once, and bad for
> something switched often or compared at a glance — which is why short, browsed choices stay
> visible and only ordered set-and-forget values collapse.

## Worked cases

| Input | Count | Result | Why |
|---|---|---|---|
| ANC / Transparency modes | 2–3 | segmented (icons) | ≤3, mode switch, compared |
| Audio Guidance: Tones / Voice | 2 | segmented | ≤3, no exception applies |
| Multimedia presets | 5 | preset-grid | 4–6 named presets, 2-col grid |
| Auto-off: power-off-after | 6–7 | dropdown | ordered value, set-and-forget → `ordered-value` |

## Implementation (mechanical enforcement)

- **`archetypes.py`** (single source of truth) carries per-archetype `min_options` / `max_options`
  (`segmented` 2–3, `preset-grid` 4–6, `dropdown` 2–∞), the `dropdown-reason` key + allowed
  values, and the small-dropdown threshold (6).
- **`validate-manifest.py`** derives the count bounds from the contract and HALTs on: a selector
  outside its count range (e.g. `segmented` with ≥4, `preset-grid` with ≤3), and a `dropdown`
  with ≤6 options that lacks a recognized `dropdown-reason`.
- Prose docs (`docs/component-catalog.md`, `headset-shared/components/README.md`,
  `headset/AGENTS.md`) point at this rule rather than restating overlapping ranges. The
  acoustic-environment **icon** rule remains a separate, genuinely-semantic prose rule.

## Non-goals

- `archetype` stays **authored** (not derived from tags) — the validator enforces it. Lower risk,
  reversible, consistent with the existing schema.
- No render-path or JS changes; no new runtime behavior.
