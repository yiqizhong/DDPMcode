# DDPM — agent map

> Full methodology (reference): [`docs/methodology.md`](docs/methodology.md). It is reference
> only — **this repo wins on any conflict** (the doc's §x.x references resolve there).

Product-UI pages are generated in **three layers**, with each device **category
isolated** from the others:

- **Design-token layer** — `shared/tokens.css`. Shared visual constants. Rarely changes.
- **Category-template layer** — per category: framework **skills** at the repo-root
  `.agents/skills/`, namespaced `<category>-…` (holding slot-based template assets), plus a
  per-category layout stylesheet (e.g. `.agents/skills/headset-*`, `headset/headset.css`).
  Generation goes through the skills, not hand-written HTML.
- **Model-data layer** — one folder per concrete model holding its manifests (清单) and the
  generated, content-baked pages (e.g. `headset/models/<MODEL>/`).

## Skills live at the repo root (methodology §9.5 reconciliation)

The methodology (§9.5) nests skills inside each category folder. Devin only discovers
`SKILL.md` files at the repo-root `.agents/skills/` and does **not** scan nested directories
(per the Devin skills docs). So all skills live at the root and are **namespaced with a
`<category>-` prefix** (e.g. `headset-gen-homepage`) to keep category isolation. The
methodology's isolation / on-demand-loading intent is preserved through naming + scoped
skill descriptions; only the literal folder location differs. `AGENTS.md` files stay nested
per category (that convention is read hierarchically and is unaffected).

## Skill naming & descriptions — how this stays navigable at scale

Skills are flat at the root, so the **naming convention is the grouping** and the
**description is what keeps the agent from getting confused**. These are hard rules, not
style suggestions (methodology §9.7.1 / §9.7.3).

### Naming taxonomy: `<category>-<role>-<name>`

- `<category>` — the device category (`headset`, `mouse`, …). Always first, so the root
  list sorts into per-category clusters (`headset-*` together, then `mouse-*`, …). The reserved
  prefix `shared` marks a **cross-category** skill (e.g. `shared-gen-walkthrough`) — a
  category-agnostic template that links only the shared layer, not any category stylesheet.
- `<role>` — `gen` (page framework) or `function` (a sub-page function/setting module).
- `<name>` — for `gen`: `homepage` | `subpage`. For `function`: omitted for the template-backed
  generator (`headset-function`). A per-function skill name such as `headset-function-eq` is rare
  and not the default path.

Examples: `headset-gen-homepage`, `headset-gen-subpage`, `headset-function`. Known functions
normally live as snapshots at `templates/functions/<id>.html` (D6/D17/D18); create
`headset-function-<id>` only when that function genuinely needs generation logic. There are no
per-function skills currently. Sorting alone then clusters category → role → name; the flat list
reads like nested folders without needing nesting.

### Description rules (this is what prevents "too many skills" from confusing the agent)

Devin loads only each skill's name + one-line `description` at startup, then activates **one**
skill at a time. So skill COUNT is cheap; what matters is that descriptions are:

- **Triggers, not summaries** — write "when you MUST use me" (e.g. "Use whenever generating a
  headset home page; never hand-write index.html"), not "generates a home page".
- **Category-scoped** — every description names its category, so a `headset-*` skill is never
  picked for a mouse task and vice-versa. This is what makes a flat list of 100+ skills safe:
  the agent only ever faces the few that match the current category + role.
- **Mutually exclusive** — no two skills' triggers overlap. If two descriptions could both
  match the same task, tighten them until exactly one does.

### Anti-sprawl rules (keep the count from exploding in the first place)

- **Sub-pages never get their own skill** — one `<category>-gen-subpage` holds all of them
  (§9.3). Adding a sub-page = a new manifest, never a new skill.
- **Don't pre-create function skills speculatively** — a known recurring function normally earns a
  `templates/functions/<id>.html` snapshot after it recurs in real manifests (§9.4). A
  `<category>-function-<id>` skill is the rare path for functions that need real generation logic;
  default to snapshots. Until then it renders via `<category>-function` (which copies the
  `function-frame.html` shell).

### Physical grouping does NOT work — flat is settled (tested 2026-06-24)

§9.7.3 suggests grouping skills in sub-directories. This was tested empirically with probe
skills at depth 1 and depth 2, run through Devin: Devin discovers
`.agents/skills/<skill-name>/SKILL.md` (depth 1) but **does NOT discover**
`.agents/skills/<group>/<skill-name>/SKILL.md` (depth 2 / nested) — the nested probe came back
"skill not found" while the flat one resolved. So skills **must be exactly one level deep**;
the flat-root + `<category>-` naming convention above is the permanent grouping mechanism, not
a temporary default. Do not re-litigate this without re-running the probe.

## Markup is copied from snippets, never generated from a description

A weak model handed a keyword ("bluetooth connection") or an inline markup pattern will happily
fabricate the HTML — wrong icons, missing parts, an invented mode. So **any non-trivial markup
is copied verbatim from a pre-written snippet file, never generated**, in two forms:

- **Variant** (pick 1 of N by an enum) — e.g. connection blocks. The skill picks the snippet whose
  filename matches the manifest's enum value (`connection/<connectionType>.html`) and fills its
  value slots. **If the enum value has no snippet, the skill HALTS and asks** — never invents the
  shape or a new enum value.
- **List item** (repeat one shape N times with different data) — e.g. feature buttons
  (`feature-button.html`). The skill copies the one snippet once per `features[]` item and fills
  `{label}`/`{icon}`/`{link}`; it never writes the button markup from a pattern.

Free-form affordance generation is a last resort (the `*-function` no-snapshot path, which still
copies the `function-frame.html` shell) and even then is constrained to manifest-provided values.
This is §9.7.4's "copy, don't create" — the structural defense against markup hallucination.

## Working rules

- When working inside a category, read that category's `AGENTS.md` first (plus this file),
  then route through its `<category>-*` skills.
- Every page links `shared/tokens.css` then the category stylesheet. **Never duplicate a
  full `<style>` block across files** — share the tokens instead.
- Categories are isolated: a change in one category must not require editing another.
- **Features are a build contract, not just buttons.** The moment a model's requirement /
  manifest declares `features[]`, every feature is one **built, routed sub-page** — not merely a
  home-page button. Generating the home page is **incomplete** until each feature's `link` target
  sub-page actually exists and the button navigates to it. A feature button whose target page was
  not built (a dangling route / 404) is a **violation, not a TODO**. (methodology §6.3: feature
  count = home-page button count = sub-pages to generate; the manifest is the product's page map.)

## Categories

- `headset/` — **pilot** category. See `headset/AGENTS.md`. Framework skills + rules
  (`headset-gen-homepage`, `headset-gen-subpage`, `headset-function`) plus two committed **test
  fixture** models (`FIXTURE`, `HS-DEMO`) under `headset/models/`; no real product-model data yet and
  no dedicated `headset-function-<id>` skills; known functions default to snapshots that grow from real manifests.
- **Cross-category (`shared-*`)** — category-agnostic templates that link only the shared layer
  (`shared/tokens.css` + their own shared stylesheet), never a category's CSS. Current:
  `shared-gen-walkthrough` (multi-step walkthrough / onboarding; styles in `shared/walkthrough.css`,
  per-model instances at `<category>/models/<MODEL>/walkthrough.manifest`). A deliberate, scoped
  exception to category isolation — only for genuine UX shells whose layout is not device-specific.
