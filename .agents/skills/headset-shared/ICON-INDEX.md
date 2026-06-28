# Icon index — headset-shared (all icon registries in one place)

Agent lookup entry point: **whenever you need an icon, start here.** Identify the use-case,
follow the registry path, look up the file by key, copy it. Never search `dds2/` directly.
Never invent or draw an icon. If the key has no file → HALT and ask.

---

## Registry map

| Use-case | Key | Registry path | HALT rule |
|---|---|---|---|
| Feature button (home + sub-page nav) | `manifest.features[].icon` | `icons/<id>.svg` | id has no file → HALT |
| Segmented control — acoustic-environment modes only (`icons: true`) | `manifest…options[].value` | `segment-icons/<value>.svg` | value has no file → HALT; aliases apply (see below) |

---

## Registry 1 — Feature-button icons (`icons/`)

**Key:** `feature.icon` from the manifest (e.g. `icon: audio` → `icons/audio.svg`).  
**Size:** 24×24, fill `#0E0E0E`.

| id | File | Visual |
|---|---|---|
| `audio` | `icons/audio.svg` | Speaker — Audio Settings |
| `settings` | `icons/settings.svg` | Gear — Device Settings |

> To add: drop `<id>.svg` (24×24, `#0E0E0E`) into `icons/`, add a row here.

---

## Registry 2 — Segmented-control icons (`segment-icons/`)

**Key:** option `value` from the manifest (e.g. `value: anc` → `segment-icons/anc.svg`).  
**Scope:** ONLY for acoustic-environment segmented controls (`icons: true`). All other segmented controls have no icons.  
**Size:** 24×24 (width/height), viewBox 0 0 16 16 (dds2 source), fill `currentColor`.
**Theme rule:** icons placed where CSS sets `color` (segment icons, selected states) MUST use `fill="currentColor"`, never a hardcoded hex.
**Aliases:** `transparency` and `pass-through` both resolve to `hear-through.svg` — do NOT create separate files for them.

| value(s) | File | Visual | dds2 source |
|---|---|---|---|
| `anc` | `segment-icons/anc.svg` | Speaker muted — noise blocked | `dds2_audio-speaker-mute.svg` |
| `off` | `segment-icons/off.svg` | Speaker off — no processing | `dds2_audio-speaker-off.svg` |
| `hear-through`, `transparency`, `pass-through` | `segment-icons/hear-through.svg` | Ear — external sound let in | `dds2_ear.svg` |
| `ambient` | `segment-icons/ambient.svg` | Speaker with levels — ambient | `dds2_audio-speaker-levels.svg` |

> To add: pick the right `dds2/` source, copy it at 24×24 / `currentColor` into `segment-icons/`,
> add a row here. If the new value is an alias of an existing one, add it to the aliases column
> instead of creating a new file.

---

## How to expand this index

1. A new **icon type** (e.g. icons for a new control archetype) → add a new "Registry N" section,
   create its sub-directory, document its key + path + HALT rule here.
2. A new **icon within an existing registry** → add a row to that registry's table.
3. A new **alias** within an existing registry → extend the value(s) cell; do NOT create a new file.
