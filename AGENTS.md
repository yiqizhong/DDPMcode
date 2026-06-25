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
  list sorts into per-category clusters (`headset-*` together, then `mouse-*`, …).
- `<role>` — `gen` (page framework) or `control` (a sub-page control).
- `<name>` — for `gen`: `homepage` | `subpage`. For `control`: `generic` (the fallback) or a
  specific control id (`dpi`, `eq`, …).

Examples: `headset-gen-homepage`, `headset-gen-subpage`, `headset-control-generic`,
`headset-control-eq`. Sorting alone then clusters category → role → name; the flat list reads
like nested folders without needing nesting.

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
- **Don't pre-create control skills speculatively** — a control earns a `<category>-control-<id>`
  skill only after it recurs in real manifests (§9.4). Until then it renders via
  `<category>-control-generic`.

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

Free-form generation is a last resort (the `*-control-generic` fallback) and even then is
constrained to manifest-provided values. This is §9.7.4's "copy, don't create" — the structural
defense against markup hallucination.

## Working rules

- When working inside a category, read that category's `AGENTS.md` first (plus this file),
  then route through its `<category>-*` skills.
- Every page links `shared/tokens.css` then the category stylesheet. **Never duplicate a
  full `<style>` block across files** — share the tokens instead.
- Categories are isolated: a change in one category must not require editing another.

## Categories

- `headset/` — **pilot** category. See `headset/AGENTS.md`. Framework skills + rules only
  (`headset-gen-homepage`, `headset-gen-subpage`, `headset-control-generic`); no model data
  and no dedicated `headset-control-<id>` skills yet (those grow from real manifests).
