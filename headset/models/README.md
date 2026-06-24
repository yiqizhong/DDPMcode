# headset models

One folder per concrete headset model. **Empty for now** — no model data exists yet.

To add a model (e.g. `HS1234`):

1. Create `models/HS1234/`.
2. Write the manifests (清单) — content only, no HTML:
   - `home.manifest` — identity (marketing name, model number, firmware, PPID), device image,
     `connectionType` (+ what that block contains), and `features[]` (each `label` + `icon` +
     `link`).
   - one `<subpage>.manifest` per feature link — a `title` + a `controls[]` list (each control
     = `id` + parameters). `controls[]` may be empty.
   - Put only data you actually have — do not invent.
3. Generate the pages **through the skills** (see `../AGENTS.md`), never by hand:
   - `@skills:headset-gen-homepage HS1234` → `index.html`
   - `@skills:headset-gen-subpage HS1234 <subpage>` → one sub-page per feature link
   - controls → `@skills:headset-control-<id>` if it exists, else `@skills:headset-control-generic`
4. Never edit a template/skill to fit one model — differences belong in the manifest.
