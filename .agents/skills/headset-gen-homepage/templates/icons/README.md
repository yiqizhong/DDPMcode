# Feature-icon registry (closed set)

One SVG per icon id, named `<id>.svg`. A manifest feature references an icon by id
(`icon: audio`); `headset-gen-homepage` inserts `<id>.svg` into the feature button's
`.feature-icon` slot.

## Rules (same anti-hallucination mechanism as connection snippets)

- Icons are **COPIED** from here, never drawn or invented.
- If a feature's `icon` id has **no `<id>.svg`** here, the skill **HALTS and asks** — never
  invents an icon.
- If a feature has **no `icon` at all**, the button is text-only (delete the `.feature-icon` div).
- Add an icon only when a real feature needs it (grows like controls, methodology §9.4): drop in
  `<id>.svg` at 24×24, fill `#0E0E0E` (matches `.feature-text`).

## Confirmed icons

- `audio.svg` — speaker (from the Audio Settings feature design).
