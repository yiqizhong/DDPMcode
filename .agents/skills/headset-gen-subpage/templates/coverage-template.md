# Requirements Atom Table

Mechanical format:

| Atom ID | Requirement | Locator | Expected | Verdict |
|---|---|---|---|---|
| <Function heading #N.a> | <one fact/control requirement> | `<manifest-stem>::<function-id>::<stable-channel>` | `<expected manifest value>` | pass |

Rules:
- One row per atomic requirement fact/control, not one prose row per numbered clause.
- `Atom ID` must start with the numbered clause id plus a suffix, for example
  `Audio setting #1.a`; this lets the clause-level gate prove every numbered
  clause has at least one atom.
- `Locator` uses stable names only: manifest stem, function `id`, component
  label/archetype selector, option `value`, and named channels such as
  `reveals.<option-value>` and `dependents`.
- `Expected` is compared mechanically for supported locator types: function exists,
  component archetype/label, option set, selected option, reveal/dependent slots,
  scalar values, and info/tooltip text.
- Use `Locator: n/a` only for facts that cannot be expressed mechanically. The
  reviewer still fills `Verdict`.
- `Verdict` is the independent reviewer's output: `pass`, `fail`, or `ambiguous`.
  The mechanical checker validates the table shape and manifest values, but it
  does not prove the atom faithfully reflects the prose.
