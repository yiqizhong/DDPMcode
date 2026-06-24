---
name: probe-deep
description: Diagnostic probe (nested). Manually invoke to test whether Devin discovers a skill nested one grouping level deep at .agents/skills/<group>/<name>/SKILL.md. Throwaway — delete after testing.
triggers: ["user"]
---

# probe-deep (nested-discovery test)

This skill sits **one grouping level deeper** than the documented path:
`.agents/skills/probe-group/probe-deep/SKILL.md`. This is exactly the structure you'd use to
group skills by category, e.g. `.agents/skills/headset/control-eq/SKILL.md`.

If Devin can discover and run this skill, **nested grouping works** and skills may be
organized in sub-directories. If Devin cannot find it (while `probe-flat` works), nested
grouping is **not** supported — keep the flat-root + `<category>-` prefix convention.

When invoked, reply with **exactly** this line and nothing else:

```
PROBE-DEEP OK — discovered at .agents/skills/probe-group/probe-deep/SKILL.md (depth 2)
```
