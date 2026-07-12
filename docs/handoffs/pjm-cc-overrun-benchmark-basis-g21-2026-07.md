# PJM G-21 — the CC_REGULAR "+21 TWh over-run" is mostly benchmark construction, not dispatch

> **CORRECTION & IMPLEMENTATION (2026-07-11, post-owner-review) — read this first;
> it supersedes the CAMPD-basis framing in §1(a), §2 and §3 below.**
>
> The owner flagged that my original evidence leaned on "CAMPD = grid-delivered
> truth," which is wrong: CAMPD net (gross × parasitic) still carries
> behind-the-meter host self-supply and non-grid load, so it is **not** the
> grid-delivered basis the model is scored on. The corrected, stronger proof
> uses CAMPD only where it is unimpeachable — **coal, where every unit is
> CEMS-metered** — and it reframes the defect from "the reconcile deflates CC"
> to the precise mechanism below.
>
> **The defect is EIA-930's fuel SPLIT, and CAMPD-coal proves it.** The old
> `reconcile_vintage_classes` scaled the gas family and the coal family each to
> their own EIA-930 cell. But EIA-930's coal/gas attribution is wrong against
> CEMS:
>
> | ISO | 930 coal − CEMS coal (2023/24/25) | reading |
> |---|---|---|
> | **PJM** | **+10 / +7 / +11** | 930 over-counts coal, under-counts gas |
> | **MISO** | **−17 / −18 / −21** | 930 *under*-counts coal (mirror image) |
> | ERCOT | −0.4 / −1.5 / −1.1 | 930 split ≈ CEMS (anchor safe) |
> | CAISO/NYISO/NEISO | ~0 (no coal) | n/a |
>
> Our row-level EIA-923 coal tracks CEMS to within ~1 TWh (our classification is
> right); **EIA-930 is the outlier.** Forcing the 923 split onto 930 therefore
> scaled PJM's correct 923 gas (383.6) DOWN to 930's too-low 368.3 and dumped
> ~85% of that spurious −15 onto CC_REGULAR (→ read +21 over vs a true ~+3),
> while scaling coal UP to 930's inflated 122 (hiding a real +2 model coal
> over-run). Crucially PJM's **total** fossil is within ~1.6% of 930 — only the
> per-family split breached the ±3% deadband (gas +4.2%, coal −5.9%, offsetting).
>
> **Fix (implemented this session):** `reconcile_vintage_classes` now reconciles
> the **combined** gas+coal total to EIA-930 as one family, scaling every fossil
> class by the same factor so the CEMS-validated 923 split is preserved — it
> corrects the fossil *level*, never the *split*. Verified old-vs-new on
> identical data (`scripts` throwaway `verify_combined_reconcile.py`):
> **PJM 2024 stops firing → CC_REGULAR actual 321.7→335.1 (model +3, in band),
> coal 122.4→112.5 (CEMS-matching, exposing model coal +2).** No-coal ISOs
> (CAISO/NYISO/NEISO) are byte-identical (combined = gas). ERCOT complete years
> unchanged (anchor safe). **MISO** (not calibrated) is correctly *exposed*: its
> gas over-run and coal under-run grow, because 930's split was flattering them.
> Tests: `tests/test_vintage_reconcile_foldin.py` (12 pass; new guards for the
> offsetting-in-band case and combined split-preservation).
>
> **Fleet-group sweep (the WA-Parish question, all 6 ISOs, 2024).** The
> plant-level `_fleet_group_by_code` map (drives the CAMPD backfill + per-plant
> displays, NOT the row-level scored totals) buckets some genuinely mixed-fuel
> plants wholly to one class: coal↔gas mis-bucket ERCOT 2.75 (p3470: 2.4 TWh gas
> at a coal plant — the WA-Parish pattern, confirmed), PJM 1.4, **MISO 6.2**;
> CC↔CT mis-bucket PJM 4.97 (Doswell p52019), NYISO 3.0, **MISO 13.9**;
> CAISO/NEISO ~0. Impact is confined to the CAMPD backfill (preliminary vintages)
> and per-plant display tables — the row-level 923 family totals are correct — so
> it's the second-order defect (b). Recommended follow-up: bucket the backfill by
> unit prime-mover class, not plant (unimplemented this session).
>
> **[Update 2026-07-11 — IMPLEMENTED.** The non-ERCOT plant-level CAMPD backfill
> now splits a mixed plant's net across its classes by measured EIA-923
> prime-mover class shares (`_plant_class_shares`; prior-year shares for
> incomplete vintages), and the fix also removed a mixed-plant **double-count**
> (plants mapped to their under-gate minority class were booked the whole plant
> net on top of the adequately-reported majority row), so complete-year
> non-ERCOT scored benchmarks change. ERCOT byte-identical. See the
> `docs/calibration-log.md` G-21 fleet-group entry and issue #2049 (keeper
> re-score review).**]
>
> Everything from the header down is the original 2026-07-11 diagnosis; where it
> says "CAMPD basis" or quotes "329.3 measured," read the corrected numbers above.

**Date:** 2026-07-11. **Branch:** `claude/pjm-cc-regular-overrun-09cmbk`.
**Scope:** diagnosis (rule 1: structure before tuning) of the pjm-98 follow-up
charter: (1) the aggregate CC_REGULAR over-run + low mean LMP, (2) the open
eastern CT under-run, (3) the failing C7 2023 CT_PEAKER cell, (4) the C3c
scarcity tail. One single-year 2024 throwaway replay of the keeper config
(rule 16 — solved into `results/calibration/pjm_g21_keeper2024_diag`, never
registered; driver `scripts/diag_g21_keeper2024_solve.py`) regenerated the
dispatch/flows/floors parquets the slim committed bundles lack; everything else
is computed from committed payloads, bench files, and the measured
CAMPD/EIA-923 sources. **No keeper change, no fitted value, no measured input
edited.** Keeper stays `2026-07-10-pjm-97-measured-interfaces`; all promotion
calls below are flagged for the OWNER.

## Headline

**Two benchmark-construction defects — not model dispatch — manufacture most of
the headline C1 story, and they also mislabeled the eastern residual G-20/pjm-98
chased.** On the CEMS-measured (CAMPD) basis the keeper's 2024 CC_REGULAR
over-run is **+8.8 TWh, not +21.1**, and pjm-98's is **+11.0, not +23.3**;
pjm-98's "2023 CC flip out of band" (+8.9 → measured +5.0, inside the 8 TWh
band) and "2024 CT_PEAKER flip out of band" (−8.2 → measured −1.3) **both
disappear on the measured basis**. Separately, the "eastern CT under-run
(Dominion −90%, EMAAC −84%)" that G-20 §5b left open is **~80% a
plant-bucketing artifact**: the missing eastern "CT" energy is combined-cycle
energy at mixed CC+CT plants (Doswell, Linden, …) that the benchmark's
last-generator-wins plant→group map books under CT_PEAKER. The REAL open
residuals are: the eastern **CC** under-run (Dominion/SWMAAC — exactly what
pjm-98's floor fixes), a genuine **ST_GAS −6 TWh** mid-merit under-run, the
**seam volume** misses (under-export ~8 TWh 2023/2024, over-export ~10 TWh
2025), and the **peak-hour price-formation gap** (C3a summer months, C3b top,
C3c tail — one gap, not three).

## 1. The two benchmark defects, mechanically

Both live in the scoring/benchmark layer; neither touches the LP.

**(a) Proportional EIA-930 family reconcile deflates CEMS-measured classes**
(`render_calibration_html.reconcile_vintage_classes`). PJM's EIA-923 gas total
runs ~18–26 TWh above the EIA-930 grid gas series (CHP behind-the-meter residue
beyond `btm.parquet`, ~6.5 TWh of non-CEMS CHP/small-gas, EIA-923-net vs
CAMPD-net differences ~+6, plant↔BA assignment). The reconcile closes that gap
by scaling EVERY gas class by the same factor (~0.946 in 2024), so 85% of the
subtraction lands on CC_REGULAR — pushing its "actual" **12.3 TWh below the
CAMPD-measured value of a fully-CEMS-covered class** (317.0 scored vs 329.3
measured, 2024). The measured data to allocate the gap properly is already in
the pipeline (CAMPD covers CC_REGULAR/CT_PEAKER/ST_GAS/coal ~100%; the
un-anchored remainder is exactly the CHP/OTHER mass the gap physically sits
in).

**(b) Last-generator-wins plant→group bucketing** (`_fleet_group_by_code`:
`out[code] = g.plant_group` over per-generator fleet rows, iteration order
decides; consumed by the CAMPD backfill `_backfill_eia923_with_campd`, the
payload per-plant fit tables and `volErr` zone×month tables). A mixed CC+CT
plant is booked WHOLE to one class. Doswell (52019: 589 MW CC + 497 MW CT,
plant HR smeared 9.03 across both) and Linden (2406: 1,300 MW CC + CTs) land
under CT_PEAKER, so ~10 TWh/yr of their measured CC generation is displayed —
and, when the CAMPD backfill fires on an under-reported vintage, SCORED — as
CT_PEAKER actual. The 2023 official CT actual (26.1 TWh) sits **+6.2 above the
measured 19.9**; the model's +0.2 "pass" there was two artifacts cancelling.
(The raw `_eia923_frame` benchmark is prime-mover-split and correct; the defect
enters via the backfill and the display/audit tables.)

## 2. C1 on three bases (model vs actual, TWh; band = min(2% load, 8) = 8)

`campd` = CAMPD hourly net (gross × parasitic), plant totals allocated to
classes by each plant's EIA-923 prime-mover class shares (prior-year shares for
the incomplete 2025 vintage). `e923` = raw prime-mover-split EIA-923.
`official` = the reconciled/backfilled `classFull` the verdict scores.

| yr | class | pjm-97 | pjm-98 | campd | e923 | official | 97−campd | 98−campd | 97−off | 98−off |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | CC_REGULAR | 314.5 | 323.7 | 318.7 | 325.7 | 314.8 | **−4.1** | **+5.0** | −0.2 | +8.9 |
| 2023 | CT_PEAKER | 26.3 | 23.4 | 19.9 | 21.6 | 26.1 | **+6.4** | **+3.5** | +0.2 | −2.7 |
| 2023 | ST_GAS | 7.2 | 6.9 | 9.1 | 8.9 | 8.6 | −1.9 | −2.2 | −1.4 | −1.7 |
| 2024 | CC_REGULAR | 338.1 | 340.2 | 329.3 | 335.1 | 317.0 | **+8.8** | **+11.0** | +21.1 | +23.3 |
| 2024 | CT_PEAKER | 20.1 | 19.9 | 21.2 | 23.9 | 28.1 | **−1.1** | **−1.3** | −7.9 | −8.2 |
| 2024 | ST_GAS | 6.9 | 7.0 | 13.1 | 13.1 | 12.4 | **−6.1** | −6.0 | −5.5 | −5.4 |
| 2025 | CC_REGULAR | 331.2 | 331.8 | 323.4 | 323.3 | 319.9 | **+7.7** | **+8.4** | +11.3 | +11.9 |
| 2025 | CT_PEAKER | 29.1 | 29.2 | 23.9 | 10.0* | 24.7 | **+5.3** | +5.4 | +4.4 | +4.5 |
| 2025 | ST_GAS | 10.7 | 10.6 | 14.7 | 12.4* | 14.3 | −4.1 | −4.1 | −3.7 | −3.7 |

\* incomplete 2025 vintage (27–72% reporting); campd is the usable measured
number there.

Re-reading pjm-98's honest-cost ledger on the measured basis: the 2023 CC flip
(+8.9→+5.0, in band), the 2024 CT flip (−8.2→−1.3, in band) and most of the
2024 CC magnitude (+23.3→+11.0) **were artifacts of (a)+(b)**; pjm-98 even
*improves* the true 2023 CT over-run (+6.4→+3.5). Its real measured-basis costs
are ~+2 TWh of CC in 2024 (+8.8→+11.0, band is 8) and ~+0.7 in 2025, against
the eastern spatial fix and the all-years C3b improvement it buys. The C7 2023
CT worsening (0.491→0.436) is real and stands (§4).

## 3. Q1 answered — who should be generating the CC surplus, and why LMP is low anyway

On the measured basis the keeper's 2024 CC +8.8 nets against: **ST_GAS −6.1**
(real, mid-merit: Central_PA −4.2 [Brunner Island-type gas-ST fleet], SWMAAC
−0.5, W_APS −0.5), **oil −0.9**, **nuclear −1.7**, plus coal **+4.1** the other
way (model coal also over-runs on the correct basis). The seam compounds it:
the model under-exports ~8 TWh (24.6 vs measured 32.6), i.e. it generates ~8
TWh LESS than the measured-export world — had the seam cleared the measured
volume, the incremental energy would come off the model's cheap margin
(CC/coal), so the under-export currently *masks* roughly that much additional
CC-cheapness bias; conversely 2025's ~10 TWh over-export inflates that year's
CC/CT/coal over-runs by about the same mechanism. The eastern CC under-run
(Dominion −23.9, SWMAAC −5.9 in 2024; Dominion −39 in 2023) is spatial, offset
by the west (AEP +5.8, EMAAC +12.8, ComEd +3.2, Central_PA +3.0) — the G-20
wheel-through, unchanged.

**The price level is NOT "cheap CC at the margin all year".** Monthly C3a
decomposition (2024, keeper config @ current data): Feb/Mar/Dec run +$3–4 HIGH;
the entire annual gap is **summer** (Jul −11.1, Aug −7.6, Sep −4.8, May/Jun
−3, Oct −4.1 $/MWh vs DA). The model's price-duration curve is flat-topped:
p99 = $48.5, max ≈ $100, 0 h > $200 (actual DA 2024: 297 h > $75, 18 RT
shortage intervals ≥ $300). In the top-150 load hours the model still
**net-exports ~1.5 GW**, leaves **~17 GW of CT idle**, and clears **$34.6**
load-weighted. The composition misses (ST_GAS/CT hours) contribute, but the
dominant C3a driver is the peak price-formation gap in §5.

## 4. Q2/Q3 answered — the eastern CT under-run and the C7 2023 cell

Correct-split (unit-class) eastern CT **actuals** are small: Dominion
3.0/3.9/1.9 TWh (2023/24/25), EMAAC 0.8/0.8/0.2, SWMAAC 0.9/0.6/0.6 — vs the
plant-bucketed 7.4/8.7/9.6 and 10.4/10.6/5.6 that G-20's tables (and the
Dominion CT −90% / EMAAC CT −84% headline cells) were computed from. The gap IS
Doswell/Linden-class CC energy mislabeled CT. Remaining real CT residuals,
2024: Dominion −3.0 (the NOVA peakers: Remington, Ladysmith, Louisa, Marsh Run
— each at ~20% of measured), W_APS −2.0, SWMAAC −0.3; EMAAC is +1.1 OVER. The
"offer/capture-layer" investigation G-20 queued for eastern CT should be
re-scoped to (i) the small Dominion/W_APS peaker fleet and (ii) the REAL big
prize, eastern CC (which pjm-98 addresses) + ST_GAS.

**C7 2023 CT_PEAKER (off-peak cv_ratio 0.491, gate 0.5)** is a *western*
artifact of the same coin: 2023 is the year model CT over-runs the west
(AEP +6.4 TWh class-wide on the measured basis) running mid-merit
flat-off-peak (model off-peak CV 0.223 vs actual 0.455 — model CT too FLAT
off-peak, i.e. too much steady overnight/shoulder CT in the west, not too
little). pjm-98's committed CC crowds shoulder CT harder (0.436), consistent.
Any fix lives in west-CT vs coal merit interleaving at 2023's $2.54 gas, not in
the east.

## 5. Q4 answered — C3c scarcity: the overlay is validated but INERT; the gap is peak supply depth

`derive_pjm_ordc_overlay.py` (published two-step $850 ORDC cascade + measured
`as_req_mw`) **validates against measured MCPs** (RT SR maxima 2024 = exactly
2×/1×$850; deficient intervals price ≥$300 in 100% of cases) — the mechanism is
real and rule-13 admissible. But applied to the keeper's 2024 dispatch it fires
**0 hours**: model online reserve averages 16.6 GW, never approaches the
~3.6 GW requirement, and in the 18 measured RT shortage hours the model's
online reserve (median 15.1 GW) is *above* its all-year median — model
tightness is uncorrelated with real scarcity. `temp_dependent_derate` (the
pjm-93/95 route to a thinner peak fleet) was REFUTED on PJM's own CAMPD
capability envelope (rule 24, pjm-95 demotion 2026-07-10) and is not
re-openable on current evidence. So the C3c tail (and the July/August C3a gap)
is blocked on a genuine structural question: **why does the model carry
~15–17 GW of idle-but-offered supply and net exports through real scarcity
hours?** Candidate admissible identifications (each measured, none built):
DA-market reserve procurement above the RT requirement, measured PJM energy
offers for the peaker/dual-fuel fleet conditioned on net load
(`fetch_pjm_energy_offers.py` exists; the ercot-50/neiso-58 offer-surface
pattern), and seam behavior at coincident-peak (neighbor scarcity pulls
exports; the ladder is quantile-static). This mirrors the NEISO Limb-B finding
(tail forms while the model holds GW of cheap headroom) — same charter shape.

## 6. Proposed benchmark repairs (OWNER sign-off — they change C1 for every ISO)

1. **Bucket the CAMPD backfill and all per-plant/zone tables by unit class,
   not plant** — replace the last-wins `{plant_code: plant_group}` map with the
   plant's EIA-923 prime-mover class shares (or CAMPD unit types). Pure bug-fix
   in spirit (the raw benchmark frame already splits correctly); kills the
   phantom eastern-CT cells that misdirected G-20/pjm-98's CT leg.
2. **Anchor the vintage reconcile on CEMS coverage** — scale only the
   non-CAMPD-anchored mass of each gas class to close the 923↔930 family gap
   (CC_REGULAR/CT_PEAKER/ST_GAS are ~fully anchored; the gap physically sits in
   the CHP/OTHER remainder). Alternative: score CEMS classes' C1 against CAMPD
   directly. Either way rule 14 (prefer measured) applied to the scorer.
   Note the residual ~8 TWh CAMPD-vs-930 gas gap (parasitic-factor estimates,
   930 telemetry) is irreducible basis noise ~2% and should stay on the family
   C2 gate, not per-class C1.

Until (2) is decided, C1's CC_REGULAR/CT_PEAKER cells for PJM should be read
against the §2 table, not at face value.

## 7. Keeper recommendation (owner's call, per the standing rule)

pjm-98 (`2026-07-11-pjm-98-cc-mustrun`) re-read on the measured basis: the
mechanism is structurally real (measured LDA/voltage commitment), fixes the
real eastern CC under-run, improves C3b all years and the true 2023 CT
over-run, and its scored C1 costs were 60–90% benchmark artifact; its remaining
real costs are ~+2 TWh CC 2024 (to +11.0 vs an 8-band), ~+0.7 CC 2025, and the
real C7 2023 CT worsening (0.491→0.436). **Recommendation: decide pjm-98's
promotion together with benchmark repairs (1)+(2)** — if the repairs land, the
C1 ledger it is being judged on changes materially in its favor; if the owner
prefers not to touch the scorer, the honest measured-basis numbers above are
the ones to weigh against the G-20 §5 over-forcing flag. Not self-served: no
keeper file touched this session.

## 8. Open real residuals (ranked, post-artifact)

1. **Peak price-formation gap** (C3a summer −7..−11 $/MWh, C3b top, C3c 0h vs
   51h) — §5 charter; biggest scored-criterion payoff.
2. **ST_GAS −6 TWh** (2024; −4.1 2025, −1.9 2023) — real mid-merit under-run,
   Central_PA-centred; model ST_GAS is 51–78% floor-forced (immaterial-class
   D-2), i.e. it never clears economically even in cheap-gas years when the
   real fleet ran 13 TWh. Offer/delivered-gas identification wanted.
3. **Seam volumes**: under-export 8 TWh (2023/2024), over-export 10 (2025)
   under the measured ladder — G-20 already ruled the ladder stays (rule 13);
   the residual is its quantile-static shape vs conditions.
4. **Eastern CC spatial** (if pjm-98 not promoted) — Dominion −24..−39,
   SWMAAC −6..−12 by year.
5. **West CT flat-off-peak 2023** (C7 cell) — merit interleaving vs coal at
   $2.54 gas.
6. Doswell plant-level HR smear (9.03 across CC and CT units) — check whether
   per-unit HRs materially move its CC block's merit position (small, but it is
   the single biggest under-run plant).

## Appendix — reproduction

- Throwaway 2024 keeper replay: `scripts/diag_g21_keeper2024_solve.py` (rule-16
  probe, `results/calibration/pjm_g21_keeper2024_diag`, not registered).
- Three-basis class table: CAMPD via `rcf._campd_hourly_frame` + parasitic
  factors, allocated to classes by per-plant EIA-923 prime-mover shares;
  official = committed `frontend/data/backcast/bench/PJM/<yr>.json.gz`
  `classFull`; model = committed run payload `gmModel`.
- Note: today's raw-data head gives a slightly different keeper baseline than
  the Jul-10 solve (2024 CC 332.5 vs 338.1, CT 22.4 vs 20.1, coal +1.6 —
  config-identical replay, `_shared` benchmark hashes changed; an EIA-923
  refresh moved delivered fuel costs). Diagnosis conclusions are basis-level
  and unaffected, but any future probe must be measured against a same-day
  baseline re-solve, not the committed Jul-10 payload numbers.
