---
name: probe-flat
description: Diagnostic probe (baseline). Manually invoke to confirm Devin discovers a single-level skill at .agents/skills/<name>/SKILL.md. Throwaway — delete after testing.
triggers: ["user"]
---

# probe-flat (baseline control)

This skill sits at the **documented single-level depth**:
`.agents/skills/probe-flat/SKILL.md`. It is the positive control for the nested-discovery
test — if Devin can run this but not `probe-deep`, then nested grouping is NOT supported.

When invoked, reply with **exactly** this line and nothing else:

```
PROBE-FLAT OK — discovered at .agents/skills/probe-flat/SKILL.md (depth 1)
```
