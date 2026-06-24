# Nested-skill-discovery probe

Goal: empirically settle whether Devin discovers skills nested one grouping level deep
(`.agents/skills/<group>/<name>/SKILL.md`), since the Devin docs neither confirm nor prohibit
it. Two throwaway probe skills are installed:

| Skill | Path | Depth | Role |
|-------|------|-------|------|
| `probe-flat` | `.agents/skills/probe-flat/SKILL.md` | 1 (documented) | baseline / positive control |
| `probe-deep` | `.agents/skills/probe-group/probe-deep/SKILL.md` | 2 (nested) | the thing under test |

Both have `triggers: ["user"]`, so they never auto-activate — they only run when you invoke
them explicitly. They cannot affect any real generation task.

## ⚠️ Prerequisite: Devin reads the git remote, not your local working tree

Devin clones the repo from GitHub. These probe files must be **committed and pushed** (a
branch is fine) before Devin can see them:

```
git add .agents/skills/probe-flat .agents/skills/probe-group .agents/skills/_PROBE_README.md
git commit -m "Add nested-skill-discovery probes"
git push            # or push a throwaway branch, then point Devin at it
```

## How to run the test in Devin

Run **both** checks — they corroborate each other:

1. **Listing check.** Ask Devin: *"List every skill available to you, by name."*
   Look for whether **both** `probe-flat` and `probe-deep` appear.
2. **Explicit-invocation check.** In a Devin prompt, send `@skills:probe-flat`, then in another
   send `@skills:probe-deep`. A discovered probe prints its one-line sentinel; an undiscovered
   one resolves to "skill not found" (or similar).

## Interpreting the result

| `probe-flat` | `probe-deep` | Conclusion |
|--------------|--------------|------------|
| works | works | **Nested grouping IS supported.** You may organize skills as `.agents/skills/<group>/<skill>/SKILL.md` (e.g. group by category). |
| works | not found | **Nested grouping is NOT supported.** Keep the flat-root + `<category>-` prefix convention (see `../../AGENTS.md`). |
| not found | not found | Discovery itself is misconfigured — wrong branch/location, or the push didn't land. Re-check before concluding anything about nesting. |

## Cleanup (after you have your answer)

```
rm -rf .agents/skills/probe-flat .agents/skills/probe-group .agents/skills/_PROBE_README.md
git add -A && git commit -m "Remove discovery probes"
```
