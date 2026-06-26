# Segment-icon registry — acoustic-environment modes (closed set)

One SVG per option `value`, named `<value>.svg`. A segmented control with `icons: true`
in the manifest copies the icon whose filename matches the option's `value` field.

## How to use (agent instruction)

When assembling a segmented control with `icons: true`:

1. For each `options[]` entry, look up `<value>.svg` in **this directory**.
2. Copy the SVG into the `.segment-icon` span of that segment.
3. **If `<value>.svg` does not exist here → HALT and ask.** Never pull directly from `dds2/`,
   never draw/invent an icon, never leave `.segment-icon` empty.
4. If a manifest option's `value` is an alias (e.g. `transparency` maps to `hear-through.svg`),
   the alias column below tells you the canonical filename to use.

## Value → file mapping

| Option value(s) | File | Visual meaning | Source in dds2/ |
|---|---|---|---|
| `anc` | `anc.svg` | Speaker muted / noise blocked | `dds2_audio-speaker-mute.svg` |
| `off` | `off.svg` | Speaker off / no noise processing | `dds2_audio-speaker-off.svg` |
| `hear-through`, `transparency`, `pass-through` | `hear-through.svg` | Ear / external sound let in | `dds2_ear.svg` |
| `ambient` | `ambient.svg` | Speaker with added level lines | `dds2_audio-speaker-levels.svg` |

> **Alias rule:** `transparency` and `pass-through` are aliases for `hear-through`. Use
> `hear-through.svg` for all three — do NOT create separate `transparency.svg` or
> `pass-through.svg` files.

## Rules (same anti-hallucination mechanism as `icons/` and `connection/`)

- Icons are **COPIED** from this directory, never drawn or invented.
- All files are 24×24 (width/height="24") with the original dds2 16×16 viewBox — SVG scales
  automatically; do not alter path data.
- Fill is `#0E0E0E` on all paths (matches `.feature-text` and the feature icon convention).
- This set covers **only acoustic-environment mode values** (ANC, off, hear-through, ambient).
  Non-acoustic segmented controls (`icons: false` or absent) never use this directory.
- To add a new value: drop in `<value>.svg` at 24×24 / `#0E0E0E`, sourced from `dds2/`, and
  add a row to the table above. Never add a value speculatively — only when a real manifest needs it.

## Confirmed icons

- `anc.svg` — speaker-mute (from `dds2_audio-speaker-mute.svg`)
- `off.svg` — speaker-off (from `dds2_audio-speaker-off.svg`)
- `hear-through.svg` — ear (from `dds2_ear.svg`)
- `ambient.svg` — speaker-levels (from `dds2_audio-speaker-levels.svg`)
