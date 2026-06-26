# headset-shared — shared snippet assets (NOT a skill)

This folder is **not a skill** (no `SKILL.md`, so Devin ignores it). It holds the component
snippets shared between `headset-gen-homepage` and `headset-gen-subpage`, kept in ONE place so
there is a single source of truth — which is what keeps the home page and sub-pages in sync.

- `ICON-INDEX.md` — **single entry point for all icon lookups**. Read this first whenever you
  need any icon; it maps use-case → registry → file key, and lists every confirmed icon.
- `connection/` — connection-block snippets (`bluetooth.html`, `wired.html`) + the standalone
  `unpair.html`. Copied into the control-zone by both the home and sub-page skills.
- `icons/` — feature-button icon registry (see ICON-INDEX.md Registry 1).
- `segment-icons/` — segmented-control icon registry, acoustic-environment modes only
  (see ICON-INDEX.md Registry 2).
- `feature-button.html` — the ONE feature button (icon + label). The home page copies it as-is
  (always expanded); the sub-page nav copies it **and adds the `feature-button--collapsed` class**,
  which collapses it to icon-only and expands it back to icon+label on hover (the "variant" is a
  CSS class on the same markup — there is no separate collapsed file).

Both skills reference these by full repo-root path (`.agents/skills/headset-shared/...`). Do not
copy these into a skill folder — one copy here is what prevents home/sub drift.
