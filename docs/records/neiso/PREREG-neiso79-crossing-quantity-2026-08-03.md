# PREREG — neiso-79: reconciling the crossing quantity for the neiso-76 §D stack traversal

**Date:** 2026-08-03 · **Scope:** NEISO, 2023–2025 · **NO LP will be solved,
no keeper changes, no bundle, no dashboard registration, no `ScenarioConfig`
field, no arm.** **Keeper:** `2026-08-03-neiso-caiso156-meter-screen`,
untouched.

**This document is committed BEFORE any measurement statistic is computed.**
Everything in §1 was established from report metadata and structural
inspection only (which reports exist, what columns they carry, whether the
years are covered); no crossing, no hour-of-day statistic, and no comparison
against C3b/C3c or any residual has been run at the time of writing.

---

## 0. What this session is and is not

neiso-76 §D found that crossing the real submitted DA offer book at the real
hourly quantity gives an hour-of-day price range of **$17.03 / $21.11 /
$24.06** (66 / 73 / 54 % of the measured DA range, peaking HE20–21) against
the keeper's own **$7.03 / $6.82 / $13.30** (27.1 / 23.6 / 29.9 %) — and
reported against interest that the read is **depth-sensitive**: at
demand − 3 GW (roughly NEISO's HQ + NB net position) it halves to **36 / 34 /
31 %**, only 4–7 pp above the keeper. *Direction survives, magnitude does
not.* The reconciliation neiso-76 named but did not do is the first task of
any successor charter (matrix §5.6 item **5b**).

**This session lands that prerequisite and stops.** Item 5b requires an owner
green-light and **none is granted**; §5.6 frontier discipline bars a lever
without one. No mechanism is proposed, no gate is written on the magnitude,
and the reconciled number is routed to the owner as the **input to their
green-light decision**, not as evidence for a lever.

Rule 13 `[R-MEASURED]` binds throughout: every price here is a **validation
target**, not a solve input. Rule 23 `[R-FROZEN-DERIVE]` binds the
identification: every construction choice below is justified against the
**measured book and the market's own accounting identity**, never against
C3b/C3c movement or any residual.

---

## 1. The data gap, resolved (task a) — established before this prereg

**ISO-NE publishes no day-ahead CLEARED external-transaction series and no
day-ahead net-interchange series, anywhere public.** Verified against the
full ISO Express report trees (Pricing, Grid, Load & Demand) and the
authenticated Web Services v1.1 endpoint list:

* Grid tree, Interchange section — *Real-Time Actual Scheduled Interchange*,
  *External Interface Metered Data*, and the 15-minute and five-minute
  variants. **All actual/real-time.** No day-ahead member.
* Load & Demand tree — the only day-ahead cleared quantity is *Hourly
  Day-Ahead Cleared Demand* (`transform/csv/hourlydayaheaddemand`, already
  intaken at neiso-76).
* Pricing tree — the only external report is *Real-Time and Day-Ahead Import
  Offer and Export Bid Data*: the **SUBMITTED** book, no cleared column.
* Web Services v1.1 — `/actualinterchange`, `/hourlybainterchange`,
  `/fiveminuteexternalflow` are all **actual**; `/hbimportexport` is this same
  submitted report. (Basic-auth; not used.)

**What the missing series would have supplied, stated precisely.** It would
be a **check on the crossing, not the crossing quantity itself**: it would let
the traversal verify that the import book cleared at the depth the crossing
says it did, i.e. validate `Q_imp(λ*)` against the actual DA scheduled import
MW. Its absence therefore costs a *validation leg*, not the reconciliation.

**What it must NOT be replaced with.** EIA-930 interchange is **actual net
hourly interchange** — a different quantity at a different grain from DA
scheduled imports. Substituting it is the rule-14 `[R-ACCURATE]`
grain-misalignment trap the brief names, and this session does not do it.
`scripts/data/derive_neiso_import_tranches.py` uses the 930 series for its own
separate purpose and is untouched.

**The fallback is not needed, because the intake is better than the missing
series.** New corpus `data/raw/NEISO-AS/da-import-export/` (committed
fetcher + README, gitignored corpus, full 2023–2025 coverage verified):
per operating day, every DA import offer and export bid with `Direction`
(IMPORT / EXPORT), `Transaction Type` (`DISPATCHABLE` = priced /
`FIXED` = self-scheduled price-insensitive), `Price` and `Bid MW`. Imports
enter ISO-NE's DA market **as priced supply offers**, so a joint crossing
clears the import depth **endogenously**. That is what removes the neiso-76
depth sensitivity: the 3 GW allowance was an assumption, and there is now no
free depth parameter to assume.

Because task (a) resolved without a dead end, the **FALLBACK BOX (the
neiso-73 Kendall net-basis reopen) is NOT opened** by this session.

---

## 2. The construction, frozen now

### 2.1 The accounting identity

ISO-NE's day-ahead market clears one energy balance per hour:

```
  internal generator supply        Q_gen(λ)
+ cleared imports                  Q_imp(λ)          [IMPORT rows]
+ cleared virtual supply           Q_inc(λ)          [INC bid type]
= cleared physical demand + cleared virtual load + cleared exports
```

The published *Hourly Day-Ahead Cleared Demand* is the demand-side cleared
quantity. The crossing quantity for the **internal generator book** is
therefore

```
  q*(λ) = Q_cleared_dem − Q_imp(λ) − Q_inc(λ)
```

which is **price-dependent**, and so is not a quantity to be looked up but a
**fixed point to be solved**. Equivalently and identically: cross the
**combined supply book** — internal offers + import offers + INC virtuals —
against the single vertical line `Q_cleared_dem`. That is the frozen
construction. It has **no free depth parameter**.

`FIXED` imports (no price) enter as price-insensitive supply at the bottom of
the stack; `DISPATCHABLE` imports enter at their offer price. `EXPORT` rows
are on the demand side and are handled by §2.2's composition test, not added
to supply.

### 2.2 The composition of `Q_cleared_dem` is IDENTIFIED, not assumed

The published series' composition (does it include exports? DECs? is it net
of INCs?) is not stated in the report. Following the miso-105 discipline
neiso-76 used for the ladder semantics, **all admissible compositions are
enumerated and the one that reproduces the posted DA LMP is reported as the
identification**; if none does, that is a real result and is reported as
such. The candidate set, frozen now:

| id | demand-side line | supply-side book |
|---|---|---|
| **C1** | `Q_cleared_dem` as published | gen + IMPORT(all) + INC |
| **C2** | `Q_cleared_dem` + cleared EXPORT | gen + IMPORT(all) + INC |
| **C3** | `Q_cleared_dem` | gen + IMPORT(all) (INC excluded — i.e. the published series is already net of INC) |
| **C4** | `Q_cleared_dem` − FIXED imports | gen + DISPATCHABLE imports + INC |

Selection statistic, frozen: **median absolute error of the crossing price λ\*
against the posted DA hub LMP**, pooled over all sampled hours per year, plus
the share of hours within $2. The composition with the lowest pooled median
|λ\* − DA| **in all three years** is the identification. A composition that
wins in some years and not others is reported as **unidentified**, and the
headline is then reported for every tied composition rather than for a
picked one.

This is a comparison against a **measured market price**, not a residual
(rule 14 `[R-ACCURATE]`; rule 23 `[R-FROZEN-DERIVE]`).

### 2.3 The reported statistic

For the identified composition, per year: the **capacity-weighted hour-of-day
mean crossing price**, its **range** (max − min over the 24 hour-of-day
cells), and the **hour of the max**. Reported as a share of the measured DA
hod range ($25.96 / $28.96 / $44.47), against **all three** neiso-76 /
keeper anchors:

* neiso-76 at raw EIA-930 demand — **65.6 / 72.9 / 54.1 %**
* neiso-76 at demand − 3 GW — **36.4 / 33.6 / 30.9 %**
* the keeper's own — **27.1 / 23.6 / 29.9 %**

The keeper's own hod range is recomputed from its committed
`hourly/system_<year>.parquet` sidecars by the same path neiso-76 used, as a
loader check (it must reproduce $7.03 / $6.82 / $13.30).

---

## 3. Sample — widened deliberately, and by how much

neiso-76 pulled the demand book at a **41-day** Phase-0 sample (the 15th of
every month 2023–2025 plus the five 2025 C3c event days). That was right for
a per-hour λ0 error statistic. It is **not** sufficient here: this session's
statistic is an hour-of-day **mean per year**, and 13–14 sample days a year
leaves ~13 observations per (year, hour-of-day) cell — far too thin to put an
hod *range* (a max-minus-min over 24 such cells, which is upward-biased by
sampling noise) beside neiso-76 §D's **full-corpus** traversal anchor.

**The sample is therefore widened to every published operating day of
2023–2025 for all three books** — internal offers (already the neiso-76 §D
basis: 1,063 day-files, 359/351/353), demand bids (41 → all published days,
a ~26× increase, ~2.5 GB), and the new import/export book (~380 MB). Stated
in advance, with the reason: **removing sampling as a confound**, not
enlarging until a number moves. New committed full-corpus fetcher
`scripts/data/fetch_neiso_da_demand_bids.py`; the 41-day probe path is
unchanged and still works.

**Sufficiency bar, pre-registered:** a year is reportable only if it carries
**≥ 300 published operating days present in ALL THREE books simultaneously**
(the binding constraint is the intersection, since the three reports have
independent publication gaps). A year below 300 is reported with its actual
day count and flagged as under-sampled; below **200** it is not given a
headline share at all. If the corpora cannot be completed in-session, the
statistic is reported on the achieved intersection with the count stated, and
the shortfall is named.

---

## 4. Kill rules — pre-registered, before any statistic is computed

Let **S_y** be the corrected crossing hod range as a share of the measured DA
hod range, year y ∈ {2023, 2024, 2025}, on the identified composition.

* **KQ1 — THE TRAVERSAL-LANE KILL (the outright one).** The quantity-dimension
  lane dies if **S_y ≤ the keeper's own share in at least two of the three
  years** (keeper: 27.1 / 23.6 / 29.9 %). If the real book, crossed at the
  correctly reconciled quantity, traverses **no more than the model's own
  stack does**, then the shape of the model's stack in the quantity dimension
  is **not** the defect, neiso-76 §D's surviving "direction" claim is
  withdrawn, and matrix item 5b is closed as REFUTED rather than routed. This
  is the kill the brief asks for and it is the one that would end the lane.
* **KQ2 — magnitude-survival, the honest middle.** If KQ1 does not fire but
  **S_y < 40 % in at least two of three years**, the corrected read is
  reported as **direction-only**: the magnitude does not survive
  reconciliation any better than it survived the 3 GW sensitivity, and the
  routing to the owner must say so in those words. This is not a kill — it is
  a pre-committed bar on how the result may be described.
* **KQ3 — identification failure.** If **no** composition in §2.2 reaches a
  pooled median |λ\* − DA| below **$10.00** in all three years, the crossing
  is **not identified against the market's own price** and no headline share
  is reported at all. The session then reports the identification failure as
  its result. ($10 is set at roughly twice neiso-76's demand-book λ0 median
  error of $5.29 — the crossing here is two-sided and structurally harder, so
  a looser bar than K3(ii)'s $2 is honest; a bar tighter than the known
  achievable would guarantee failure, and one looser than $10 would admit a
  crossing that is not tracking the market.)
* **KQ4 — the depth sensitivity must be RE-RUN, not inherited.** The
  reconciled crossing is re-reported with the import book **removed entirely**
  (gen + INC only, against the same demand line). If that variant's share is
  within **5 pp** of the reconciled one, the import reconciliation did no
  work and must be reported as immaterial rather than as the fix.
* **KQ5 — no residual conditioning, ever.** No construction choice,
  composition selection, sample restriction, or filter may be made on the
  basis of C3b/C3c movement, the amplitude residual, or the model's own
  price. Selection is on §2.2's measured-price statistic alone. Any
  post-hoc filter not named in this document is disclosed explicitly as
  post-hoc and its effect reported both ways.

**If the external series had been unavailable AND no substitute existed**
(the brief's contingency): the fallback was the neiso-73 Kendall net-basis
reopen. It is **not** taken — §1 resolved with a better input than the
missing series. Recorded here so the contingency is on the record as
discharged, not forgotten.

---

## 5. Governance

Years **2023–2025 only**. NEISO's locked test is **SPENT and never
re-grantable**; the holdout spend freeze is **ACTIVE**. Every intake above is
train-years-scoped by construction (the fetchers default to 2023–2025 and
cite rule 22). No LP is solved; no `ScenarioConfig` field is added or
changed; no default is altered; no derive is re-run; no keeper moves; no
bundle is produced; no dashboard registration is made (rule 15 binds
completed runs and there is none). Nothing measured here is armed (rule 13).

Rule 28 duties: this session tests **no** mechanism cell, so no verdict is
stamped. Matrix §5.6 item **5b** gains the reconciliation result and this
prereg as a citation — the item stays **charter-requested, not opened**, and
`da_virtual_bids` NEISO stays `R` (neiso-76). The tranche-construction family
(`use_campd_bins` / `plant_level_fleet`) is **not** stamped: nothing was
tested on it.

**This licenses nothing.** No adder, multiplier, hinge, re-binning or
offer-shape parameter may be sized from anything in this document or from the
measurement it pre-registers.
