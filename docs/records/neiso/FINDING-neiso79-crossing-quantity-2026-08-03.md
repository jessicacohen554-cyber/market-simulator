# FINDING — neiso-79: the crossing quantity is reconciled, and it takes the neiso-76 §D traversal from 66 / 73 / 54 % of the measured DA amplitude to 30 / 37 / 38 % — the DIRECTION survives (KQ1 does not fire), the MAGNITUDE does not (KQ2 fires); ISO-NE publishes no DA cleared external series at all, and the submitted import book is a better input than the missing one

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
| **(c)** | which composition of the published cleared series is it? | narrowed to **C2 or C3** — the two are statistically indistinguishable at NEISO (cleared exports ≈ INC virtual supply, so they nearly cancel); C1/C4 refuted in every year. C2 wins 2023–24, C3 wins 2025 | **UNIDENTIFIED between C2 and C3** on the pre-registered rule; both reported, and they differ immaterially (§B) |
| **KQ3** | is the crossing identified against the market's own price (median \|λ\*−DA\| < $10 in all three years)? | $7.86 / $8.33 / **$11.12** — 2023 and 2024 clear it, **2025 does not** | **FIRES on 2025** → the three-year headline share is **WITHHELD** per the prereg; the numbers below are the measured statistic with two of three years identified, not a certified headline |
| **(d)** | the corrected share of the measured DA hour-of-day range | **29.7 / 36.7 / 37.7 %**, against neiso-76 §D's 65.6 / 72.9 / 54.1 % at metered demand and the keeper's own 27.1 / 23.5 / 29.9 % | see §C |
| **CONTROL** | is that fall caused by the QUANTITY or by the smaller sample? | neiso-76's own §D read, recomputed on **this** sample, gives **68.6 / 79.8 / 59.3 %** — at or ABOVE their full-corpus anchors in every year | **the quantity, not the sample** |
| **KQ1** | traversal-lane kill — is the real book's traversal ≤ the model's own in ≥2 years? | **0 / 3** | **does NOT fire — the lane is NOT refuted** |
| **KQ2** | direction-only bar — share < 40 % in ≥2 years? | **3 / 3** | **FIRES — the magnitude does NOT survive reconciliation; report as direction-only** |
| **KQ4** | did the import reconciliation do real work? | with imports 29.7 / 36.7 / 37.7 % vs without **49.6 / 61.0 / 49.4 %** — 19.9 / 24.3 / 11.6 pp | does not fire — the import book carries the bulk of the correction |
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

**Corpus.** 864 operating days present in **all three** books, 20,733 hours
crossed — **300 / 288 / 276** days in 2023 / 2024 / 2025 (prereg §3 tiers: 2023
**OK**, 2024 and 2025 **UNDER-SAMPLED** — above the 200-day reportable floor,
below the 300-day bar; §E4 has the cause and §C the control that bounds its
effect).

**Result — the composition is C2/C3, and KQ3 FIRES on 2025:**

| construction | comp | 2023 median \|λ\*−DA\| | 2024 | 2025 |
|---|---|--:|--:|--:|
| **FROZEN** | C1 | 9.25 | 9.85 | 14.68 |
| | **C2** | **7.86** | **8.33** | 12.10 |
| | **C3** | **7.86** | 8.47 | **11.12** |
| | C4 | 9.25 | 9.85 | 14.68 |
| MT (post-hoc) | C2 | 8.77 | 9.20 | 13.13 |
| | C3 | 8.78 | 9.28 | 12.09 |

**C1 and C4 are refuted outright** — netting self-scheduled imports out of the
demand line instead of adding them to supply is arithmetically the same thing,
and both readings that leave exports off the demand line are $1.4–2.6 worse in
every year. **C2 and C3 are statistically indistinguishable** (they differ by
$0.00 in 2023 and $0.14 in 2024): C2 adds ~1–2 GW of cleared exports to the
demand line while C3 removes ~1.3–1.9 GW of INC virtual supply from the supply
book, and at NEISO those two are close to the same size, so they nearly cancel.
C2 wins 2023–24 and C3 wins 2025, so under the pre-registered rule the
composition is **UNIDENTIFIED between C2 and C3** and results are reported for
the pooled-best (C3) with C2 differing immaterially.

**KQ3 fires, and it fires on 2025 alone.** The bar was a pooled median under
**$10.00 in all three years**. 2023 ($7.86) and 2024 ($8.33) clear it
comfortably; **2025 does not** ($11.12 at best). Under the pre-registered rule
the **three-year headline share is therefore WITHHELD**: this crossing is
identified against the market's own price in 2023 and 2024 and **not** in 2025.
The §C numbers are reported as what they are — the measured statistic, with two
of three years identified — and **not** as a certified three-year headline.
That is the pre-registration binding, and it is honoured rather than
reinterpreted.

---

## §C — the headline: the corrected crossing, and the control that validates the sample

**Corpus and tiers as in §B.** Composition C3 (C2 immaterially different).

| year | corrected hod range | peak | **share of measured DA hod range** | neiso-76 §D at demand | at demand−3 GW | keeper |
|---|--:|:--|--:|--:|--:|--:|
| 2023 | **$7.71** | HE21 | **29.7 %** | 65.6 % | 36.4 % | 27.1 % |
| 2024 | **$10.63** | HE19 | **36.7 %** | 72.9 % | 33.6 % | 23.5 % |
| 2025 | **$16.78** | HE19 | **37.7 %** | 54.1 % | 30.9 % | 29.9 % |

**THE CONTROL — and it is what makes the above a statement about the QUANTITY
rather than about the sample.** The same probe, on the same 864 days, crossing
the internal book alone at EIA-930 demand — i.e. **neiso-76 §D's own
construction**:

| year | at EIA-930 demand (this sample) | neiso-76's full corpus | at demand−3 GW (this sample) | neiso-76's |
|---|--:|--:|--:|--:|
| 2023 | **68.6 %** | 65.6 % | **37.4 %** | 36.4 % |
| 2024 | **79.8 %** | 72.9 % | **36.9 %** | 33.6 % |
| 2025 | **59.3 %** | 54.1 % | **33.2 %** | 30.9 % |

**The sample reproduces neiso-76's anchors — slightly ABOVE them in every year,
on both reads.** So the sample is not depressing the traversal; if anything it
flatters it. The fall from **68.6 / 79.8 / 59.3 %** to **29.7 / 36.7 / 37.7 %**
is the **crossing quantity**, and nothing else.

**Three readings of that, in order of what they settle:**

1. **The reconciled crossing lands essentially where neiso-76's own 3 GW
   sensitivity said it would** — 29.7 / 36.7 / 37.7 % against 37.4 / 36.9 /
   33.2 % for a flat 3 GW allowance on this sample. neiso-76's instinct to flag
   the depth sensitivity was right, and the *correct, endogenous, measured*
   import depth confirms **the pessimistic end of it**. The measured DA import
   depth is not 3 GW but **~4–4.4 GW** (submitted 1.0–1.7 GW self-scheduled +
   3.0–3.2 GW priced, of which the crossing clears a price-dependent part),
   plus 1.3–1.9 GW of INC virtual supply — so the internal book is crossed
   ~4–5 GW shallower than at raw metered demand, in a materially flatter part
   of the stack.
2. **DIRECTION SURVIVES.** The real book's traversal exceeds the model's in
   **all three years** — +2.6 / +13.2 / +7.8 pp over the keeper's 27.1 / 23.5 /
   29.9 %. **KQ1 does not fire.** The quantity-dimension suspicion is not
   refuted.
3. **MAGNITUDE DOES NOT.** The headline neiso-76 §D number — 66 / 73 / 54 % —
   does not survive contact with the correct quantity. What survives is a
   **3–13 pp** gap, not a 38–49 pp one, and in 2023 the gap is **2.6 pp**.

---

## §D — the pre-registered kill rules

Scored on the FROZEN construction, composition C3, all three years above the
prereg §3 reportable floor.

| kill rule | measured | verdict |
|---|---|---|
| **KQ1** — the outright lane kill: is the real book's traversal ≤ the model's own in ≥ 2 of 3 years? | **0 / 3** years at-or-below the keeper (29.7 vs 27.1, 36.7 vs 23.5, 37.7 vs 29.9 %) | **does NOT fire** — the traversal lane is **not refuted**; the real book does traverse more than the model's |
| **KQ2** — the direction-only bar: share < 40 % in ≥ 2 of 3 years? | **3 / 3** years below (29.7 / 36.7 / 37.7 %) | **FIRES** — the corrected read **must be reported as DIRECTION-ONLY**, and the magnitude must not be quoted as surviving reconciliation |
| **KQ3** — identification vs the market's own price | best pooled median $7.86 / $8.33 / **$11.12**; the $10.00 bar is missed in 2025 | **FIRES on 2025** — the three-year headline is withheld (§B) |
| **KQ4** — did the import reconciliation do real work (≥ 5 pp)? | with imports 29.7 / 36.7 / 37.7 % vs **without** 49.6 / 61.0 / 49.4 % — **19.9 / 24.3 / 11.6 pp** | **does NOT fire** — the import book is doing the bulk of the correction, and removing it recovers most of the §D headline |
| **KQ5** — no residual conditioning | the only post-hoc construction is the MT variant, disclosed and reported both ways (§E1); every selection is on the measured DA price | honoured |

**KQ2 firing is the substantive answer to the brief.** Both kill rules that
could have been kind to this lane were pre-registered before the numbers
existed, and the one that fired is the one that constrains how the result may
be described.

**KQ4 is the mechanical explanation of the whole finding.** Deleting the import
book from the supply side recovers 49.6 / 61.0 / 49.4 % — most of neiso-76 §D's
headline. The §D read was, in effect, **crossing the internal book at a
quantity that the real market serves with 4–5 GW of imports and virtuals**, and
that is precisely the reconciliation error this session was sent to find.

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

**1. The prerequisite is discharged; the charter is NOT opened.** Matrix §5.6
item 5b's first task — "reconcile the crossing quantity (published DA cleared
demand net of scheduled imports and cleared virtual supply)" — is done, on
measured data, with the depth sensitivity **removed rather than re-assumed**.
No lever is proposed, no `ScenarioConfig` field exists, no arm is
pre-registered, no G-gate is written on the magnitude, and no cell verdict is
stamped. Item 5b stays **charter-requested**.

**2. What the owner now has for the green-light decision, stated plainly.**

* The quantity-dimension suspicion is **not refuted** (KQ1 does not fire): the
  real submitted book, crossed correctly, traverses **more** than the model's
  stack in all three years.
* But the margin is **3–13 pp of the measured DA amplitude, not 38–49 pp**
  (KQ2 fires). On the keeper's own basis that is a move from 27.1 / 23.5 /
  29.9 % to at most 29.7 / 36.7 / 37.7 % — **it does not close the amplitude
  defect**, which needs ~100 %. In 2023 it is worth **2.6 pp**.
* So a stack-traversal lever, if chartered and if it worked perfectly, would
  recover **at most about a third to a half** of NEISO's diurnal amplitude
  gap — and 2025's C3c gate, which neiso-75 sized as the one gate the
  amplitude lane could close, would need far more than that.
* **The honest recommendation this session can support: item 5b is worth a
  charter only if the owner's target is amplitude FIDELITY rather than the C3c
  gate.** It cannot close C3c-2025 on this evidence, and neiso-75 §2.4 already
  established it cannot close C3c-2023 at all.

**3. Two things a successor must NOT do.** (a) Do not re-run the neiso-76 §D
traversal at metered demand and quote 66 / 73 / 54 % — that read is now
measured to be crossing the book ~4–5 GW too deep, and its magnitude is
superseded by this reconciliation. (b) Do not substitute EIA-930 interchange
for DA scheduled imports; the DA cleared series does not exist (§A) and the
substitution is a rule-14 grain misalignment.

**4. Open question named, not opened.** The crossing sits a median $7.8–11.0
**below** the posted DA (§E2). Whatever closes that gap — commitment-cost
recovery, reserve co-optimization post-DASI, congestion, losses — is a
*level* mechanism, and NEISO's measured defect is a **trough that is too dear**
(neiso-76 §B4), not a level miss. Nothing here recommends work on it; it is
named so the next session does not rediscover it as a surprise.

**5. C3c-2023 is unchanged and still routed to the owner** (CHARTER-neiso75
§5, three options). Nothing measured here touches it.

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
