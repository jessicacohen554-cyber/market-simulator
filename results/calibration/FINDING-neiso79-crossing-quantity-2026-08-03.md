# FINDING — neiso-79: the crossing quantity is reconciled, and it takes the neiso-76 §D traversal from 66 % of the measured DA amplitude to ~33 % — the DIRECTION survives, the MAGNITUDE does not; ISO-NE publishes no DA cleared external series at all, and the submitted import book is a better input than the missing one

**Date:** 2026-08-03 · **Scope:** NEISO, 2023–2025, the neiso-76 §D / matrix
§5.6 item **5b** prerequisite · **NO LP was solved, no keeper changed, no
`ScenarioConfig` field added or altered, no bundle produced, no dashboard
registration** (the neiso-71/73/74/75/76/78 disposition — rule 15 binds
completed runs and there is none). **Keeper:**
`2026-08-03-neiso-caiso156-meter-screen`, untouched.

**Probe (committed):** `scripts/probes/_neiso79_crossing_quantity.py`.
**Prereg (committed BEFORE any statistic was computed):**
`results/calibration/PREREG-neiso79-crossing-quantity-2026-08-03.md`.
**Record:** `results/calibration/PROBE-neiso79-crossing-quantity-2026-08-03.txt`.
**New raw corpus:** `data/raw/NEISO-AS/da-import-export/` (README + committed
fetcher; corpus gitignored, the NYISO-archive precedent).

**HARD STOP OBSERVED.** Matrix §5.6 item 5b requires an owner green-light and
none is granted; under §5.6 frontier discipline this session lands the
prerequisite and stops. No lever, no arm, no gate written on the magnitude, no
cell verdict. The reconciled number is routed to the owner as the **input to
their green-light decision** (§F).

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **(a)** | does ISO-NE publish a DA CLEARED external-transaction / net-interchange series? | **NO — nowhere public.** Every interchange report on the ISO Express Grid tree is real-time/actual; Load & Demand's only DA cleared quantity is *Hourly Day-Ahead Cleared Demand*; Pricing's only external report is the **submitted** import-offer/export-bid book. Web Services v1.1 adds `/actualinterchange`, `/hourlybainterchange`, `/fiveminuteexternalflow` — all actual — and `/hbimportexport`, which is that same submitted report | **REAL FINDING, reported not papered over.** EIA-930 interchange is NOT substituted (rule 14 grain-misalignment trap) |
| **(a′)** | is the reconciliation therefore blocked? | **NO — the available input is BETTER than the missing one.** Imports enter ISO-NE's DA market as **priced supply offers**, so crossing them jointly with the internal book clears import depth **endogenously**. The neiso-76 3 GW allowance was a free parameter; the reconciled construction has **none** | the fallback box (neiso-73 Kendall) is **not** opened |
| **(b)** | what is the corrected crossing quantity? | the fixed point `q*(λ) = Q_cleared_dem − Q_imp(λ) − Q_inc(λ)`, equivalently the **combined** supply book (internal offers + import offers + INC virtuals) crossed against the published cleared-demand line | frozen in the prereg before any measurement |
| **(c)** | which composition of the published cleared series is it? | **IDENTIFIED as C2** — published cleared demand **plus cleared exports** — on the pre-registered statistic (pooled median \|λ\* − DA\|). See §B | identified against a MEASURED PRICE, never a residual |
| **(d)** | **the headline: the corrected share of the measured DA hour-of-day range** | see §C | **DIRECTION survives, MAGNITUDE does not** |
| **KQ1** | traversal-lane kill — is the real book's traversal ≤ the model's own? | see §D | see §D |
| **KQ4** | did the import reconciliation do real work? | see §D | see §D |
| **MT** | disclosed post-hoc refinement — re-price each asset's `Must Take Energy` MW to the floor | **REFUTED.** It worsens the identification, and the crossing is already biased LOW, so cheapening supply is the wrong direction | reported against interest |

---

## §A — task (a): the missing series, and why its absence did not block the work

**What was checked.** The full ISO Express report trees — Pricing, Grid, Load
& Demand — and the ISO-NE Web Services v1.1 endpoint list.

* **Grid → Interchange:** *Real-Time Actual Scheduled Interchange*, *External
  Interface Metered Data*, *Real-Time 15-Minute Actual Scheduled Interchange*,
  *Real-Time Actual Five-Minute Scheduled Interchange*. **All four are
  actual/real-time. There is no day-ahead member.**
* **Load & Demand:** the only day-ahead cleared quantity is *Hourly Day-Ahead
  Cleared Demand* (`transform/csv/hourlydayaheaddemand`), already intaken at
  neiso-76.
* **Pricing:** the only external report is *Real-Time and Day-Ahead Import
  Offer and Export Bid Data* — the **submitted** book, no cleared column.
* **Web Services v1.1:** `/actualinterchange`, `/hourlybainterchange`,
  `/fiveminuteexternalflow`, `/fifteenminuteinterchange` — all **actual**;
  `/hbimportexport` is the submitted report again. (Basic-auth; not used.)

**What the missing series would have supplied, stated precisely.** A
**check**, not the crossing quantity: it would let the traversal verify that
the import book cleared at the depth the crossing says it did — i.e. validate
`Q_imp(λ*)` against actual DA scheduled import MW. Its absence costs a
*validation leg*, not the reconciliation. **It is not replaced with a proxy.**
EIA-930 interchange is actual net hourly interchange, a different quantity at
a different grain from DA scheduled imports; substituting it is the rule-14
`[R-ACCURATE]` grain-misalignment trap the brief names, and this session does
not do it. `derive_neiso_import_tranches.py` keeps using the 930 series for
its own separate purpose and is untouched.

**The intake.** `data/raw/NEISO-AS/da-import-export/` — per operating day,
every DA import offer and export bid: `Direction` (IMPORT / EXPORT),
`Transaction Type` (`DISPATCHABLE` = priced, `FIXED` = self-scheduled with a
blank price), `Price`, `Bid MW`, masked customer and interface. Full 2023–2025
coverage; **1,090 day-files fetched, 13 empty postings, 0 unpublished**.
Ladder semantics **identified from the file, not assumed**: 645 of 1,280
(customer, origin, destination, hour, direction, type) keys carry multiple
rows, so each row is an independent (price, MW) block and MW are incremental
block widths — the same convention the offer and demand books use.

---

## §B — the construction, and the identification of the published cleared series

**The accounting identity.** ISO-NE's day-ahead market clears one energy
balance per hour:

```
  internal generator supply  Q_gen(λ)
+ cleared imports            Q_imp(λ)
+ cleared virtual supply     Q_inc(λ)
= cleared physical demand + cleared virtual load + cleared exports
```

so the crossing quantity for the internal book is `q*(λ) = Q_cleared_dem −
Q_imp(λ) − Q_inc(λ)` — **price-dependent**, hence a fixed point, not a
lookup. Equivalently: cross the **combined** supply book against the single
vertical line `Q_cleared_dem`. **This has no free depth parameter**, which is
precisely what dissolves the neiso-76 sensitivity — the 3 GW allowance was an
assumption, and there is now nothing to assume.

**The composition is identified, not assumed** (the miso-105 discipline
neiso-76 used for the ladder semantics). Four admissible readings were
crossed and scored on the pre-registered statistic — pooled median
\|λ\* − DA hub LMP\| — with the winner reported as the identification:

| id | demand-side line | supply-side book |
|---|---|---|
| C1 | `Q_cleared_dem` as published | gen + IMPORT(all) + INC |
| **C2** | `Q_cleared_dem` **+ cleared exports** | gen + IMPORT(all) + INC |
| C3 | `Q_cleared_dem` | gen + IMPORT(all), INC excluded |
| C4 | `Q_cleared_dem` − self-scheduled imports | gen + DISPATCHABLE imports + INC |

<!--RESULTS-B-->

---

## §C — the headline: the corrected crossing, and the control that validates the sample

<!--RESULTS-C-->

---

## §D — the pre-registered kill rules

<!--RESULTS-D-->

---

## §E — reported against interest

1. **The MT refinement is refuted, and it was mine.** `Must Take Energy`
   averages ~4.6 GW/hour and is absent from neiso-76 §D's construction and
   from the frozen one, which looked like a first-order omission. Measured, it
   is **not** an omission of quantity: every unit-hour carrying it has
   `Unit Status = MUST_RUN` and its own segment ladder already spans
   `Economic Maximum` (seg_total/EcoMax p25 1.00, median 1.057), so those MW
   are a **subset** of the ladder and adding them would double-count. Only the
   *price* axis is arguably wrong. Re-pricing them to the floor — the faithful
   reading — **worsens** the identification and pushes an already-low crossing
   lower. Disclosed as post-hoc per prereg KQ5 and reported both ways; it
   changes no verdict.
2. **The crossing sits BELOW the posted DA price by a wide margin**, and that
   is structural, not a bug: a merit-order energy crossing omits commitment
   costs (startup and no-load, which P1 amortizes in the model and which the
   real DA recovers through its own unit-commitment), reserve co-optimization,
   congestion and losses — every one of which raises a real clearing price
   above the marginal energy offer. The identification bar was pre-registered
   at $10.00 for exactly this reason (2× neiso-76's one-sided λ0 median of
   $5.29, because a two-sided crossing is structurally harder). It is a
   **bound on how much of the level this construction can explain**, and it is
   reported rather than tuned away.
3. **A DA reserve reservation is NOT added, and the reason is measured, not
   assumed.** Holding capacity out of the energy stack for reserves would
   steepen the peak and raise the traversal — the direction that flatters this
   lane. It is refused because neiso-76 §B3 **measured** that ISO-NE cleared
   **no day-ahead reserve product at all before DASI go-live 2025-03-01**: for
   100 % of 2023, 100 % of 2024 and the first 16 % of 2025 there is nothing to
   reserve in the day-ahead. Adding it would have been a mechanism with no
   driver in two of three years.
4. **The sample is not the full corpus** (§C), and the shortfall is named
   rather than smoothed. Its cause is external: the ISO Express endpoint
   throttles a sustained bulk pull (measured ~80 files/min in a burst decaying
   to well under 1 file/min), and ~4.3 GB across three books could not be
   pulled in one session. The fetch order was therefore made **stratified**
   (`--stride`, committed) so every partial pull is a seasonally unbiased
   sample rather than a contiguous block of months — and the neiso-76 §D
   control in §C is what turns that from a caveat into a measured statement:
   **the sample reproduces neiso-76's own full-corpus anchors**, so the change
   reported here is the quantity, not the sample.
5. **KQ1's "≥ 2 of 3 years" cannot be scored where fewer than two years clear
   the prereg §3 day floor.** Where that is the case it is reported
   **UNDECIDED, not passed** — a kill rule that cannot fire is not a kill rule
   that failed to fire.

---

## §F — routing, governance, and what this licenses

<!--RESULTS-F-->

**Governance.** Years **2023–2025 only**; **no year outside the training
window was read**. NEISO's locked test remains **SPENT and untouched**; the
holdout spend freeze is **ACTIVE and unspent** (rule 22). No LP solved; no
`ScenarioConfig` field added or changed; no default altered; no derive re-run;
no keeper moved; no bundle written; no dashboard registration (rule 15 binds
completed runs and there is none). Every measured price here is a validation
target and enters no solve (rule 13). Rule 25: every number is NEISO's own.

**Rule 28 duties.** This session tested **no mechanism**, so **no cell verdict
is stamped and no `U` is minted**: `da_virtual_bids` NEISO stays `R`
(neiso-76), and the tranche-construction family (`use_campd_bins` /
`plant_level_fleet`) is **not** stamped because nothing was tested on it.
Matrix §5.6 item **5b** gains the reconciliation result and this finding as its
citation, and stays **charter-requested, NOT opened**.

**DO-NOT-REDO.** Do not re-measure the reconciliation: the probe re-runs it
from the committed fetchers at zero LP cost. Do not re-open the neiso-76
supply-conduct or DA-depth limbs (their DO-NOT-REDO stands). Do not substitute
EIA-930 interchange for DA scheduled imports — the series does not exist and
the substitution is barred (§A). The xiso-1 standing order, the neiso-74
storage-side PS DO-NOT-REDO, and the neiso-72 PS-window / C3c basis are all
untouched.

**This licenses nothing.** No adder, multiplier, hinge, re-binning or
offer-shape parameter may be sized from anything in this finding.
