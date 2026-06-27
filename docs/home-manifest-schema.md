# Home manifest — structured schema (with explicit optional / absence rules)

> Status: draft schema for the deterministic renderer. Grounded in `subpage-frame.html`'s slots and
> the two real home manifests (`HS-DEMO/home.manifest` structured, `WL327/home.manifest` prose).
>
> Principle: **structured ≠ everything required.** Each field declares its optionality AND what the
> renderer does when it is absent. A missing OPTIONAL field is normal (the UI element is simply not
> emitted — presence/absence, the same rule used for cross-model variants). Only a missing REQUIRED
> field is a deliberate HALT.

## Field table

| field | type | req? | drives (UI) | rule when ABSENT |
|---|---|---|---|---|
| `marketing-name` | str | **required** | device name `<h1>` (home + subpage header) | HALT |
| `model-number` | str | **required** | model-number span | HALT |
| `firmware` | str | optional | "Firmware Version …" line in the ⓘ tooltip | **drop that line** |
| `ppid` | str | optional | "PPID: …" line in the ⓘ tooltip | **drop that line** |
| `image` | path | optional | `.device-image-place` | leave the place empty (no `<img>`) |
| `connectionType` | enum¹ | **required** | which `connection/<type>.html` is copied | HALT |
| `battery` | int 0–100 | conditional² | battery value inside the connection block | if the chosen snippet HAS a battery slot and battery is absent → render `—%`; if the snippet has no battery slot (e.g. wired) → ignored |
| `features` | list | **optional** | feature buttons (home) + obligates building each linked sub-page | **absent/empty → homepage only: no feature buttons, no sub-pages generated** |
| `features[].label` | str | required *(when a feature exists)* | button label | HALT |
| `features[].icon` | enum³ | required *(when a feature exists)* — **LLM-filled, not user-provided** | button icon (nav is icon-only) | HALT |
| `features[].link` | str | required *(when a feature exists)* | target sub-page (must be built) | HALT (dangling route) |

¹ `connectionType` must name an existing `connection/<type>.html` (today: `wired`, `bluetooth`). An
  unknown value → HALT (Lane 2: add the snippet first).
² `battery`'s relevance is decided by the connection snippet, not by a free-floating flag: the
  `bluetooth.html` snippet has a battery slot; `wired.html` does not. So "wired has no battery" is not
  a missing field — it is simply a snippet without that slot.
³ `features[].icon` uses the **existing icon mechanism** — `headset-shared/ICON-INDEX.md` (Registry 1,
  `icons/<id>.svg`). The LLM consults that index at authoring time and writes a concrete key (`icon: audio`);
  the index is a **closed set with a HALT-on-miss / never-invent rule** ("if the key has no file → HALT
  and ask"), so even the LLM's choice is bounded to existing keys. The renderer then deterministically
  copies `icons/<id>.svg`. Need a key the registry lacks → add the SVG + an index row (the normal
  "grows like controls", methodology §9.4) — not a render-time decision.

**Compound rule (ⓘ tooltip):** if BOTH `firmware` and `ppid` are absent, the tooltip has no content,
so the entire ⓘ icon + tooltip is omitted (not an empty popup).

**Generation logic (features):** `features` is optional. Empty/absent → generate the **homepage only**
(no feature buttons, no sub-pages). Each present `features[]` entry both renders a button AND obligates
generating its `link` sub-page (a button to an unbuilt page is a dangling-route violation, not a TODO).

## Who fills each field (the authoring ↔ rendering boundary)

The home manifest is frozen before the renderer runs; the renderer is purely mechanical. WHO populates
each field is split by whether the decision is semantic (judgment) or mechanical:

| field | filled by | why |
|---|---|---|
| `marketing-name`, `model-number`, `firmware`, `ppid`, `image`, `connectionType`, `battery` | the device's known data (human/source) | facts about the device |
| `features[].label`, `features[].link` | author / LLM | what the feature is + where it goes |
| `features[].icon` | **LLM, via the existing `ICON-INDEX.md` (closed registry, HALT-on-miss)** | "which icon fits this feature" is a SEMANTIC choice — the LLM picks a key from the index and writes it; the closed set + HALT keeps the choice bounded |
| the HTML | **renderer (code)** | mechanical copy + slot fill — deterministic |

`features[].icon` is the clean illustration of the whole architecture — and it already exists in the
codebase (`ICON-INDEX.md` + `icons/`): the *choice* of icon is an LLM judgment (consult the index, pick
a key) frozen into the manifest as `icon: audio`; the *use* of it (`copy icons/audio.svg`) is
deterministic code, guarded by the index's never-invent / HALT-on-miss rule. Judgment up front,
mechanism at the end, the manifest is the freeze line.

## The concern in action: a real model with no PPID (WL327)

`WL327` genuinely has no PPID. Under this schema that is fine — `ppid` is optional, so its line is
omitted. The frame tooltip template:

```html
<div class="info-tooltip-pop">
  <span class="info-tooltip-text">Firmware Version <span data-property="firmware-version">x.x.x.x</span></span>
  <span class="info-tooltip-text" data-property="device-ppid">PPID: XXXXXX</span>
</div>
```

renders for WL327 (firmware present, ppid absent) as:

```html
<div class="info-tooltip-pop">
  <span class="info-tooltip-text">Firmware Version 33.442.103.12</span>
</div>
```

The PPID line is simply not emitted — no empty box, no leaked `PPID: XXXXXX`. Deterministic, every
run. (Contrast: the current LLM flow ships `PPID: XXXXXX` as a placeholder and decides ad hoc what to
do when PPID is missing — omit, leak the placeholder, or invent one.)

## How the gate handles it (extend `validate-manifest.py` to cover home)

The home manifest gets the same kind of mechanical gate the sub-page manifest already has:
- missing a **required** field (`marketing-name`, `model-number`, `connectionType`) → **HALT** with
  the exact field named.
- missing an **optional** field (`firmware`, `ppid`, `image`, often `battery`, **and `features`
  itself**) → **passes** (the renderer omits the element; empty `features` → homepage only).
- a feature that IS present but is missing `label`/`icon`/`link` → **HALT** (each present feature needs
  all three; `icon` is the LLM's job to have filled).
- `connectionType` / `features[].icon` that name no snippet/asset → **HALT** (Lane 2).

So "will it error?" has a precise answer: only on a missing *required* field, deterministically, with
the field named — never a surprise crash mid-render, and never on a legitimately-absent optional field.

## Regularizing the two existing home manifests

**`HS-DEMO/home.manifest`** — already conformant; it simply omits the optional `ppid`, `image`, and
(being wired) `battery`. No change needed:

```yaml
marketing-name: DDPM Headset
model-number: HS-DEMO
firmware: 1.0.0.0
connectionType: wired
features:
  - label: Audio Settings
    icon: audio
    link: audio-settings.html
```

**`WL327/home.manifest`** — prose today; structured target. The prose feature line had no icon; that
is fine — the icon is not authored by hand, the LLM auto-selects it from `icons/` and writes the
concrete id during manifest authoring:

```yaml
marketing-name: Dell Pro 3 Wireless ANC Headset
model-number: WL327
firmware: 33.442.103.12
image: images/product.png
connectionType: bluetooth
battery: 76
# ppid: (absent — optional, omitted; WL327 has no PPID)
features:                # optional — if this whole block were absent, WL327 would be homepage-only
  - label: Audio Settings
    icon: audio          # LLM-selected from icons/ at authoring time (not hand-written)
    link: audio-settings.html
```

## Why this is flexibility WITHIN structure (not rigidity)

- Different models having different info is the **normal** case: declare the varying fields optional;
  absent → omitted, **no per-model code**. HS-DEMO (no ppid/image/battery) and WL327 (no ppid) both
  validate and render under one schema.
- A genuinely **new, unanticipated** field (e.g. a future `warranty-code`) → add it to the schema as
  optional, once. Adding an optional field does NOT break existing models — they don't have it, so it
  is omitted. (Same Lane-2 "grow on demand" pattern as snippets/archetypes.)
- What the schema does NOT allow is a model inventing arbitrary fields the renderer has never heard of
  — that is the deliberate trade for determinism, and the gate names the gap instead of guessing.
