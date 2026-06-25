# Connection block snippets (closed set)

One file per **confirmed** connection mode, named `<connectionType>.html`. The home and
sub-page skills **copy** the file matching `manifest.connectionType` verbatim into the
`.control-zone`, then fill value slots. Neither skill ever writes a connection block from
the keyword.

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

## Unpair is a separate snippet

`unpair.html` is **not** part of any connection tag. It is copied separately, on the **home page
only**, after the tag, for **paired** modes (bluetooth and future wireless modes). Wired modes get
no Unpair. Sub-pages never include Unpair — they simply omit it (never `display`-hide).

## Confirmed modes

| mode | snippet | paired? (gets Unpair on home) | value slots |
|------|---------|-------------------------------|-------------|
| bluetooth | `bluetooth.html` | yes → also copy `unpair.html` | `battery-level` |
| wired | `wired.html` | no | none |

`unpair.html` — standalone Unpair button (home only, paired modes only).
