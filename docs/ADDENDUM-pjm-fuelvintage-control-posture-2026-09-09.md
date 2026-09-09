# ADDENDUM to PRECOMMIT-pjm-fuelvintage-2026-09-09 — the 2023 control is now UNCONDITIONAL

**Session:** `pjm-fuelvintage-1`, 2026-09-09. Written **before the control is launched** and
before any screen result exists, so it cannot be read as a post-hoc justification.

## What changed

PRECOMMIT §2 declared the same-HEAD 2023 control **conditional** — earned by rule 29(b)'s
LIVE-hunk case, but spent only if a load-bearing criterion failed, on the reasoning that G-4's bar
is a PASS → FAIL flip and PASS/FAIL is scored **absolutely** against actuals, so an all-PASS arm
would clear G-4 with no control in existence.

`FINDING-pjm-retiree-window-redistribution-2026-09-09.md` falsifies the premise that reasoning
rested on. It is not that HEAD *might* have drifted from the keeper: **HEAD's PJM 2023 fleet is
measurably different from the fleet the keeper solved**, by +720.0 MW of AEP-Ohio coal (W H
Sammis units 1-4, retired May 2020) plus the availability and offer deltas that ride the same
plant through `retiree_cems_cap`. That is a **measured** fleet delta on the backcast path, present
with the fuel flag **off**.

## Why that flips the decision

The conditional posture was sound while the only reason to doubt the keeper-as-control was
*bibliographic* — unresolvable `git_sha`s (PRECOMMIT §2) and two LIVE hunks named by another
lane's audit. An all-PASS arm would then have been self-evidently clean.

It is no longer sound, in **both** directions:

- **A PASS is no longer self-certifying.** An arm that comes back all-PASS could be an arm whose
  fuel-seam degradation is masked by 720 MW of phantom cheap coal — or the reverse. Without a
  same-HEAD control the two are not separable, and G-4 would be reporting a number it cannot
  attribute.
- **A FAIL is no longer attributable either**, which was the original reason to hold the control
  in reserve. That reason now applies to every outcome, not just the failing one.

There is also a governance reason, and it is the stronger one: this lane will report a
determination for a mechanism. **Reporting one against a control known to differ by an unrelated
undeclared 720 MW would be quoting a number the session knows is contaminated** — rule 1
`[R-STRUCT]`'s "never reach the right number through a mechanism that isn't real" applies to the
*comparison* as much as to the model.

## The decision

**The 2023 same-HEAD control is spent unconditionally**, launched on this session's own warm
container concurrently with SHARD S's armed leg, so it costs no wall clock. Exactly one declared
delta between the two legs (`gas_electric_power_monthly_level`), both at HEAD `0b67ee4b`, both on
the keeper's frozen recipe otherwise.

**Scope is unchanged: 2023 only** — rule 29(b) licenses a control "only for the years the screen
needs", and the screen year is 2023. The full span and the touchpoints remain **control-free** and
are scored absolutely; the 2023 pair is what carries every attribution claim this lane makes.

**Bundle:** `results/screen/pjm_ep_level_2023_control`, gitignored under the same rule-29(c) /
rule-31 standing as every other bundle in this lane — kept on local disk, never merged, never
`rm`'d before the owner rules.
