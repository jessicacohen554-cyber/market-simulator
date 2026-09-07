# ADDENDUM to PRECOMMIT-ercot253 — the 2021 AS requirement was ZERO; a measured cleared-DAM series replaces it (ercot-253)

> **Committed BEFORE the re-solve**, amending
> `docs/PRECOMMIT-ercot253-2021-rung-2026-09-06.md`. The first 2021 solve was
> **STOPPED ~5 minutes in and its partial bundle deleted** — nothing from it is
> registered, quoted or carried. Every prediction in the PRECOMMIT §3 stands
> except where §3a below amends it.

## 1. What the completeness pass missed

The launched solve logged `energy+reserve co-opt (ERCOT MULTI-PRODUCT): …
per-product req means [0, 0, 0, 0] MW` — **2021 had no ancillary-service
requirement at all**, against `[359, 1821, 0, 3897]` on the 2022 rung.

Cause: the requirement is read from ERCOT's published AS Plan
(`data/raw/ercot/ASPLANNP433_<year>.parquet`), which exists for **2022 onward
only** — MIS retention does not reach earlier delivery years, the same wall that
kills the 2021 SCED conduct tables (PRECOMMIT §2c). `ASPLANNP433_2022` spans
2022-01-01 .. 2023-01-06 and reaches no further back. The loader's contract for a
missing file is *all-zero, no-op*, and `spec.py`'s own comment says what that
means: it **fails loud in forecast and is silent in backcast**. With no
requirement the ORDC family never binds, so C3a / C3b / C3c would have measured a
missing input rather than the model. **My §2 completeness pass checked that the
2021 AS *credit* series existed and never checked the *requirement*.**

## 2. The replacement, and the owner ruling behind it

Owner ruling 2026-09-06 (clickable card): *"Build the measured cleared-AS
requirement"*, then, on the validation result below: *"Cleared-only, no offset,
limitation stated"*.

`scripts/data/build_ercot_as_cleared_requirement.py` sums the 60-Day DAM
Disclosure's per-resource **cleared awards** on both sides of the market —
`60d_DAM_Gen_Resource_Data_2021_*` (4 delivery quarters) plus
`60d_DAM_Load_Resource_Data_{2021,2022}` (posting years, each spanning deliveries
Nov 2 (Y−1) .. Nov 1 (Y), so delivery 2021 is fully covered) — to a system total
per product per hour, on the fleet's fixed-CST non-leap clock using the same
CPT→CST conversion the AS-Plan loader documents. Rule 13 `[R-MEASURED]`: an
ERCOT-published cleared MW quantity, never a price, regenerating identically for
any year the disclosure covers.

Written: `data/raw/ercot/ercot_2021_as_cleared_requirement_hourly.parquet` —
8,760 h, means **RegUp 271.4 / RRS 1,607.5 / ECRS 0.0 / NSPIN 1,948.3 MW**. ECRS
is zero because the product did not exist in 2021, so its 2023-06-10 onset stays
carried by the data with no hard-coded date, exactly as the plan path has it. One
hour (spring-forward) has no CPT posting of its own and is carried across from its
neighbour rather than left as a one-hour reserve collapse; the `covered` column
flags it.

Consumed through the new `scarcity.ercot_as_measured_requirement_mw`, which
prefers the plan and falls back only when the plan file is absent. **Every
training year and the 2022 rung are byte-identical** (verified: 2022 and 2023
return values identical to the plan-only path). Every fallback logs a WARNING
carrying the understatement below.

## 3. The validation, and why NO offset is added back

Measured on the **7,319 hours of 2022 where both sources exist** — the only such
year, since the Load Resource files cover delivery 2018-2021 fully and 2022
partially while the AS Plans start in 2022:

| product | plan mean | cleared mean | diff | corr | monthly diff range |
|---|---|---|---|---|---|
| RegUp | 363.2 | 348.3 | **−14.9 MW (−4.1 %)** | 0.9969 | −9.6 .. −22.5 |
| RRS | 2,828.6 | 2,075.5 | **−753.1 MW (−26.6 %)** | 0.9181 | −703.9 .. −775.4 (sd 22) |
| NSPIN | 3,977.4 | 3,707.7 | **−269.7 MW (−6.8 %)** | 0.9753 | −182.3 .. −362.9 |

**The identity does not hold, and the cause is identified rather than guessed:**
self-arranged AS counts toward the requirement and never appears as a DAM award.
The `2d_Self_Arranged_AS_*` reports are on disk — for **2026 only** — which names
the mechanism without valuing it for 2021 or 2022. The RRS gap is a standing
~750 MW block (stable across the 2022-10-15 RRS split), not a fixed fraction.

That offset is **deliberately not added back**. It is identifiable on 2022 alone
and would have to be transported across the post-Uri reform boundary to a
held-out year with **no second year to validate the transport against** — a free
parameter this seam refuses to carry (rule 21 `[R-DOF]`).

## 3a. Amended prediction — a FOURTH structural low bias, named before the solve

PRECOMMIT §3 named three reasons the model cannot reproduce Uri (metered load,
the shallow DAM availability view, the un-vintaged ORDC curve shape). **This adds
a fourth, and it points the same way:** the 2021 RRS requirement is understated by
roughly a quarter, which suppresses reserve scarcity and biases mean price and the
price tail **LOW**.

The PRECOMMIT's numeric predictions are **UNCHANGED** — C3a FAIL LOW, central
≈ −40 %, range −25 % to −55 %; C3c 60-160 h vs 258; C3b 0.25-0.60; C1 −3 to
−9 TWh; determination NOT-YET on {C3a, C3b} with C3c auto-ledgered. They were
written expecting a working AS requirement, so this amendment **adds a cause, not
a slack**: if C3a lands inside the predicted range it is now over-explained, and
that must be reported as such rather than read as accuracy.

## 4. Stop rules (unchanged, plus one)

Every PRECOMMIT §5 stop rule stands. Added: **the self-arranged offset is not to
be introduced later because the result was disappointing.** If the 2021 rung
misses low, that is the pre-registered consequence of a measured input being
74-96 % complete per product — not a licence to fit the missing quarter.
