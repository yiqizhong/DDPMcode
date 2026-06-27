# System-wide generation-robustness plan

> Status: plan. Triggered by the WL327 Device Settings failure, but written for the CLASS of failure,
> not the instance. Do NOT hand-fix the device-settings HTML — fix the system so this class cannot
> recur for any model/page, now or later.

## 0. What the instance revealed (the class, not the case)

The Device Settings page broke because it was **hand-written by a model, bypassing the deterministic
pipeline**. The proof is inside the broken page itself: the parts the model **copied** (frame,
masthead, connection block, collapsed feature-nav) are structurally correct; only the parts it
**hand-wrote from memory** (the two function cards) are wrong (`h3.function-name` instead of the
nested `.function-title-text` shell, content rendered outside the card). Audio Settings is correct
*only because our pipeline produced it* — the model never touched it.

So the failure CLASS is: **anything produced or edited OUTSIDE the deterministic pipeline drifts from
its manifest** — and there is currently nothing that (a) forces generation through the pipeline or
(b) detects when an on-disk page no longer matches what the pipeline would produce.

## 1. Root-cause map (issue → class → where it lives → covered today?)

| Debug issue | Failure class | Freeze-line side | Covered by current system? |
|---|---|---|---|
| 1 — stale nav (Audio Settings missing Device link) | output went stale when a manifest changed | mechanical | render-model rebuilds all pages — but **not enforced** |
| 3 — function cards hand-written, wrong shell | page produced OUTSIDE the pipeline | mechanical | render-subpage produces it correctly — but **not enforced** |
| 6 — `icon: settings` not in registry (my finding) | authoring referenced a missing asset | mechanical | **YES** — validate-home HALTs |
| 4 — invented id `dell-audio-promotion` (snapshot `promotion-download` exists, unused) | authoring chose an id with no snapshot; a matching snapshot was silently skipped | intent | **NO** |
| 5 — toggle invented for promotion (snapshot has no toggle) | authoring invented a control the snapshot doesn't have | intent | **NO** (downstream of 4) |
| 2 — selected segment icon stays black | icon asset not themeable (hardcoded `fill`) | asset | **NO** |

Two clean buckets: **mechanical / below the freeze line** (1, 3, 6 — the pipeline can guarantee these)
and **intent + asset / above the freeze line** (4, 5, 2 — the schema gate can't see "valid but wrong").

## 2. The fix — three threads, each general

### Thread A — Enforce the pipeline + a drift gate (kills classes 1 & 3 and any future bypass)

The pipeline already produces correct, reproducible pages. The gap is that nothing **forces** its use
or **detects** drift. Close it mechanically:

- **A.1 — One manual action only: edit the manifest.** All pages come from `render-model.py <MODEL>`.
  Hand-writing or hand-editing any generated `.html` is forbidden (this is D19's "no off-pipeline
  hand-patching", finally enforced rather than asked).
- **A.2 — Reproducibility gate** (`verify-model.py <MODEL>`): render the model into a temp dir and
  assert every committed page is **byte-identical** to the renderer's output. ANY hand-edit (issue 3)
  or stale page (issue 1) fails it. Wire it into the SKILL self-check and a pre-commit / CI hook so a
  drifted page cannot be committed. This single check covers the entire "diverged from manifest" class.
- **A.3 — render-model always rebuilds the WHOLE model** (home + every `features[]` sub-page) from the
  manifests. A manifest change therefore can never leave a stale sibling page (issue 1 structurally
  impossible once A.1/A.2 hold).

> Net: once generation must go through render-model and the reproducibility gate runs, issues 1 and 3
> — and any future hand-edit or stale-page drift — cannot reach the repo.

### Thread B — Close the authoring-intent gaps the schema gate can't catch (classes 4 & 5)

These live ABOVE the freeze line (a structurally-valid manifest that encodes the wrong intent). The
gate validates shape, not "did you pick the right id/control." Add registry-AWARE authoring checks:

- **B.1 — Snapshot-match warning.** When a function takes the assembled path (no snapshot for its id)
  AND its id/title keywords match a registered snapshot in `functions/README.md`, HALT/warn:
  *"'promotion' matches snapshot promotion-download — set id to it."* Requires making the
  `functions/README.md` keyword table machine-readable (a small registry the gate consults). Catches
  issue 4 mechanically for any "a snapshot exists but a near-id was invented" case.
- **B.2 — Snapshot ⇒ no components.** A function whose id resolves to a snapshot must NOT also declare
  `components:` (the snapshot carries its own structure). HALT if it does. Catches issue 5's shape.
- **B.3 — Authoring rule (discipline, not mechanical):** always look an id up in `functions/README.md`
  before authoring it; an invented id is an authoring bug. Bake into the authoring SKILL/flow.
- **Honest limit:** a genuinely wrong-but-valid control choice with NO registry signal (no matching
  snapshot, no domain rule) cannot be mechanized — that stays strong-model authoring + human review.
  The gate's job is structure + asset existence + reproducibility, not taste.

### Thread C — Asset / registry hygiene (classes 2 & 6)

- **C.1 — Themeable-icon convention.** Every icon that sits where CSS sets `color` (segment icons,
  selected states) must use `fill="currentColor"`, never a hardcoded hex. Fix the existing
  `segment-icons/*.svg`, and add the rule to `ICON-INDEX.md`. Fixes issue 2 for ALL icons, not one.
- **C.2 — No inline/invented icons.** Icons are only ever copied from the registry; the gate already
  HALTs on a missing id (issue 6 covered). Add a check that scans emitted HTML for an `<svg>` that did
  not come from a registry file (catches a model hand-drawing an icon, as happened with `settings`).
- **C.3 — Grow the registry on demand.** A new icon need (e.g. `settings.svg`) = add the asset + an
  ICON-INDEX row (the existing §9.4 "grow on demand"); never inline-invent.

## 3. Priority

1. **Thread A** — highest leverage. Enforcement + the reproducibility gate eliminate the biggest class
   (bypass/drift), including the exact Device Settings failure, for every page forever.
2. **Thread C.1** — cheap, fixes a real visible bug class (icon theming) across all icons.
3. **Thread B** — closes the authoring-id/control gaps; needs the keyword table made machine-readable.

## 4. What this deliberately does NOT solve

"Intent → manifest" semantic mistakes with no registry/domain signal (a valid manifest that simply
encodes the wrong design) remain **authoring judgment**, mitigated by a strong authoring model + review
— not by more gates. The system guarantees: correct STRUCTURE, asset EXISTENCE, and REPRODUCIBILITY.
It does not guarantee the author wanted what they wrote. Pretending a gate can catch taste would just
rebuild the "monster of special cases" the methodology warns against (§2.1).

## 5. Self-review corrections (after critiquing this plan)

- **A.1 is a policy, not a mechanism.** Its only teeth are A.2 (the reproducibility gate). The gate IS
  the enforcement; "hand-writing forbidden" is just what the gate detects.
- **C.2 (scan for invented icons) is redundant — dropped.** A.2 already catches a hand-drawn icon: the
  page won't reproduce from the manifest, so verify-model flags it. Plus the home gate HALTs on a
  missing icon id. No separate scanner needed.
- **B.1 (keyword match) is heuristic / warn-only and is the ONLY thing that addresses the actual
  instance (issues 4/5).** It needs the `functions/README.md` keyword table made machine-readable.
  Lower confidence → deferred to a second phase.
- **B.2 is a clean general rule but does NOT catch this instance** (`dell-audio-promotion` has no
  snapshot, so "snapshot ⇒ no components" doesn't trigger). Honest gap: the 4/5 class is only softly
  covered (by the deferred B.1).
- **C.1 (currentColor) changes rendered output** (icons are baked into pages) → it couples to the
  baseline hashes and forces regeneration of affected pages. Sequence it SEPARATELY from the
  pure-addition gate work, not bundled.

**Reviewed execution order:** (1) Thread A `verify-model` + B.2 — pure additions, zero output change,
no instance touch [this handoff]; (2) C.1 icon `currentColor` — asset change, separate; (3) B.1
keyword table — heuristic, phase 2.
