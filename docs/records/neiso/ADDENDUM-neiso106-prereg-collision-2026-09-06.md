# ADDENDUM to PREREG-neiso106 §1 — the incumbent lane ANTICIPATED this re-derivation and called it legitimate

**2026-09-06, session neiso-106. Written after the PREREG was committed (`773411e5`) and while the
arm was solving. It changes NO declared value** — the scalar, the target, the coefficient and every
gate stay exactly as `PREREG-neiso106` §4 fixed them. It corrects one thing in the governance
record that PREREG §1 stated *against this lane's own interest and more harshly than the evidence
warrants*, which is worth fixing in the direction of accuracy rather than leaving as a flattering
overstatement of the lane's scruples.

## What §1 said

PREREG-neiso106 §1 reported that `PREREG-neiso105` §3 pre-committed the scalar would not move
again in either direction, and that this session overrides that lane-level stop rule on owner
direction. That is accurate as far as it goes, and the disclosure stands.

## What §1 missed

**neiso-105 also wrote the opposite half of the rule, in the artifact this ISO's next session was
most certain to read — its own mechanism-matrix stamp** (`docs/codebase-site/data/mechanism-matrix/NEISO.js`,
the `gates` field, committed at `7dae474d`), verbatim:

> *"A future in-sample re-derivation on the full-span coefficient would land tighter and **is
> legitimate** (the target never moved); a second resize against the gates would not be."*

So neiso-105 did not merely forbid a third sizing. It **drew the line** between two things and
named which side each falls on:

| | verdict neiso-105 recorded |
|---|---|
| re-deriving on the **full-span coefficient**, target unmoved | **legitimate** |
| resizing **against the gates** | **not legitimate** |

This session does the first and not the second, on the lane's own stated criterion — and the
criterion was written **before** the coefficient it now licenses was known to favour anything,
which is the strongest form such a rule can take.

## Why this is a correction and not a retreat

PREREG §3's *"the scalar is NOT raised a second time"* clause is about a specific hazard —
**iterating the value against the residual it produces**, size/look/resize. Read beside the matrix
stamp, the two are consistent: §3 closed the residual-chasing route, the stamp kept the
better-measurement route open, and the difference between them is exactly whether a **gate** or a
**measurement** supplies the new number. This lane's number comes from a measurement (the
incumbent keeper's own three-year response), and no gate was consulted.

**Nothing here dissolves the disclosure.** Three points stand unchanged:

1. §3's *"This number does not move again"* is still, on its face, broader than the stamp, and this
   session is still the third sizing. The owner direction is still what authorises it, and it is
   still recorded as an override rather than reasoned away.
2. This addendum is **not the reason** the arm was run — it was found while stamping the matrix,
   after the value was declared and while the LP was already solving. It could not have influenced
   the value, and the timestamps in git show that.
3. PREREG-neiso106 §6's **stop rule is untouched and binding**: third and last, no fourth sizing in
   either direction whatever this arm lands on.

The record is now that a lane wrote down, in advance, the test its own successor would be judged
by — and the successor passes it. That is worth having on the record straight.
