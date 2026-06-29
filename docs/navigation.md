# Project Navigation · Reading Map (what to read at each stage)

> **Purpose**: No need to read the whole repo from scratch every time. Start here → find the **specific files** to read/change for your task.
> This is an **entry index + task router** — it does not duplicate content from elsewhere, it only points the way. Last updated: 2026-06-26.

---

## 1. In one sentence: what is this project

A **product UI generation system** (headset as pilot). A strong model **freezes design intent** at authoring time into "pre-written snippets + manifest data";
**a weak model at generation time only copies snippets + fills values — no generation, no inference** ("copy, don't create"). Three layers:

```
Design tokens shared/tokens.css  →  Category styles headset/headset.css  →  Page frames (skills)  →  Model data (manifest)
```

---

## 2. File structure overview (one line per file + which layer it belongs to)

```
AGENTS.md                       Root agent map: three-layer architecture, skill naming/anti-sprawl, copy-not-create, build contract
docs/
  navigation.md                 ← You are here (reading map)
  component-catalog.md          [Component catalog] all reusable components + when to use + universality + how to call (living catalog)
  function-card-architecture.md [Design journal] why it was designed this way: D1–D22 decisions, §7 control selection, §8 interaction model (long, historical)
  methodology.md                External methodology (reference only; codebase wins on conflicts; top has "superseded by code" list)
headset/
  AGENTS.md                     [headset operational contract] routing, non-negotiable rules, control-selection three tables, directory tree — read this before working
  headset.css                   Category layout + all component styles + interaction (:has/:checked/subfn/panels/dropdown)
  models/<MODEL>/               Model manifests + generated finished pages (no real models yet; HS-DEMO is gitignored)
shared/tokens.css               Design tokens (color/font/radius…), shared across all categories
.agents/skills/                 Skills discovered by Devin at the repo root (folder + SKILL.md)
  headset-gen-homepage/         Generates index.html (home-frame.html)
  headset-gen-subpage/          Generates any sub-page (subpage-frame.html)
    templates/functions/        [Ready-to-use cards · id-routed] eq-audio / promotion-download / single-control + README
    templates/examples/         [Demo/teaching examples · not routed] collaboration / auto-power-off / noise-control + README
  headset-function/             Fallback card assembler when no snapshot exists (function-frame.html = card shell)
  headset-shared/               Not a skill; shared snippets:
    components/                 6 atomic snippets (.html) + README (atomic rules + segmented/preset details)
    connection/                 Connection block snippets (bluetooth/wired/unpair)
    icons/  feature-button.html Icon library + feature button
```

---

## 3. Task-based reading / change routes (core)

| What I want to do | Files to read/change (in order) | Notes |
|---|---|---|
| **Edit an atomic snippet** (toggle/slider/segmented/preset/dropdown/info) | `components/<name>.html` (the snippet itself) → `components/README.md` (atomic rules) → `headset/headset.css` (its styles) | Snippets have no inline `<style>`; all styles are in headset.css |
| **Add/change a function card** | Snapshot exists → edit `functions/<id>.html` directly; none → assemble from `headset-function/templates/function-frame.html` (card shell) + `components/*` (atoms); consult `component-catalog.md` | Cards are routed by manifest `id` (D8) |
| **Change the "swappable control (swap)" rule** | **Edit only** `components/toggle.html` (sole authority); `single-control.html` references it — do not rewrite the rule there | Only switch ↔ dropdown allowed in header |
| **Change the "which control to use" selection rule** | `headset/AGENTS.md` §"Control Selection" (operational) | Why it was defined that way → `function-card-architecture.md` §7 |
| **Change routing** (which id → which card / keywords) | `functions/README.md` + `headset-gen-subpage/SKILL.md` + `headset/AGENTS.md` routing section | Generation is id-only; keyword table is authoring-time only |
| **Change styles / add a token** | Component styles → `headset/headset.css`; color etc. tokens → `shared/tokens.css` | Inline `<style>` forbidden; tokens first |
| **Add a connection block / feature button / icon** | `headset-shared/connection|icons|feature-button.html` + their respective READMEs | Also copy-snippet; unknown enum → HALT |
| **Understand why the overall design is this way** | `function-card-architecture.md` (decision log D1–D22 + sections) | Long; only read when you need the "why" |
| **Find out what components exist and their universality** | `component-catalog.md` | One-stop catalog |

---

## 4. Single-source truth reference (prevent drift / avoid re-reading)

Every topic has **one** source of truth — always go to it when making changes:

| Topic | Single source of truth | Role of other files |
|---|---|---|
| Three-layer architecture / skill naming / anti-sprawl | `AGENTS.md` (root) | — |
| headset routing + non-negotiable rules + control selection tables | `headset/AGENTS.md` | — |
| Component catalog / universality | `docs/component-catalog.md` | — |
| Swap rule (swappable header control) | `components/toggle.html` | single-control references it |
| segmented vs preset-grid details | `components/README.md` | AGENTS only provides the family-level table |
| Design decision rationale ("why") | `function-card-architecture.md` | Historical/thinking log, not current spec |
| Styles | `headset/headset.css` | Tokens are in tokens.css |
| methodology.md | — | **Reference only** (top section lists points superseded by code); codebase wins on conflicts |

---

## 5. Shortest onboarding sequence for new sessions

1. This page (navigation.md) — know where things are.
2. `headset/AGENTS.md` — hard rules + directory tree for working.
3. Need to touch a component → `docs/component-catalog.md` to find it → jump to its file.
4. Only read `function-card-architecture.md` when you need the "why behind the design."

> Maintenance: update §2 and §4 of this page + the top date whenever the file structure or single-source assignments change.
