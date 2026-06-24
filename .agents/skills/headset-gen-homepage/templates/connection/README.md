# Connection block snippets (closed set)

One file per **confirmed** connection mode, named `<connectionType>.html`. The
`headset-gen-homepage` skill **copies** the file matching `manifest.connectionType` verbatim
into the home page's `.control-zone`, then fills value slots. It never writes a connection
block from the keyword.

## Rules (this is the anti-hallucination mechanism)

- A connection block is **COPIED** from here, never **generated** from a word like "bluetooth".
  Copying leaves a weak model no room to invent icons, drop Unpair, or fake a layout.
- If `manifest.connectionType` has **no matching file** here, the skill **HALTS and asks** — it
  must never invent a block or a brand-new mode.
- Add a new mode only when a real model confirms it (modes grow like controls, methodology §9.4):
  drop in `<newmode>.html` built from existing `headset.css` classes; never speculate.

## Value slots inside a snippet

- Use `data-property="<name>"` for model-specific values (e.g. `battery-level`). The skill fills
  these from the manifest; structure is fixed by the snippet, only values are filled.

## Confirmed modes

- `bluetooth.html` — bluetooth tag + battery (`data-property="battery-level"`) + Unpair.
- `wired.html` — USB-C tag (no value slots).
