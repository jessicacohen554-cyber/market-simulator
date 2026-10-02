# FINDING — closeout-NWPP wave 1: lever C and R-3 censuses, the EIA-930 peak item, hygiene

Lane closeout-NWPP (charter from the Backcast close-out desk, 2026-10-02; plan §3.9). **Zero LP.** Keeper #20
(`2026-10-01-nwppnext16c-combined-vintage`, pin `33014efc`) is unchanged.

Probes (read committed files; run from the repo root): `scripts/probes/_nwpp_closeout_w1_leverc_bridger_shape.py` (§2; needs
keeper #20's 2023 leg `a54c7b97a9c588564bab90746f2dbbc44fd56838` extracted) and `scripts/probes/_nwpp_closeout_w1_r3_bridger_ceiling.py` (§3).

## 1. The NEXT-20 seam fixes — landed by the parallel NWPP chain, not here

The charter's NEXT-20 item (CAISO seam → net load; WECC_CAN anchor off the peak-only Mid-C index) was implemented in parallel
by session NWPP-NEXT-20 (`session_01GpoZnzVZBHaRnQ9TQH5Ztp`) and merged first. Main's construction
(`FINDING-nwppnext20-seam-phase0-2026-10-02.md`) is the one in force: CAISO_COI / CAISO_NEVP on CISO net load, WECC_CAN on
`ELAP_BCHA-APND` (`weim_hourly_counterparty.parquet`) priced in 2023–25 only, WECC_SW deleted, unpriced counterparties served as
the measured residual. The solve is `HANDOFF-nwppnext21-2026-10-02.md`. This lane's duplicate implementation (a single CAISO
block on net load, a second BCHA store, a 2019–22 flat-HR Canada fallback and a separate PRECOMMIT) was withdrawn at the merge
with main (rule 19: one mechanism; rule 26). Independent corroboration from the withdrawn version, for the record: the same
BCHA retention edge (2023-06-22) and 2023 BCHA premium of ~$15–50/MWh over BPAT every month; a matched-window HR of
36.10 / 20.55 / 10.49 against main's 37.64 / 20.60 / 10.51.

## 2. Lever C — coal commitment bridge by parameters: FAILS THE CENSUS (stays U, not queued)

**D-2 census (rule 19):** these mechanisms already floor NWPP coal in keeper #20.
- `coal_mustrun_per_plant` is a fuel-free tranche, all 8,760 h, sized at the plant's measured P5 CF. Bridger: 289 / 289 /
  207 / 134 / 252 / 316 / 316 / 316 / 316 / 289 / 289 / 289 MW by month.
- `coal_committed_nested_on_mustrun` leaves Bridger a committed tranche of 2.1 MW.
- The soft take floor and the monthly pile act at month-ends only.

`floors/2023_P1.npz` has zero `min_gen` on all 73 coal rows in all hours. Bridger's must-run tranche (316–326 MW) already
equals all four units at measured minimum load: the CEMS p10 loading while online, summed over the four units, is 322 MW.

**The existing bridges are ISO-named arms over a generic detector.** `caiso_ra_mustoffer_min_gen` takes `fuel_types`, and
MISO calls it for coal. But `COMMITMENT_PARAMS_BY_FUEL` has no coal entry. The detector anchors on the committed tranche,
2.1 MW at Bridger. The MISO rule-19 reconciliation nets out `must_run_pct`, which gives Bridger a level of about 0.

**Residual shape, Aug–Oct 2023:**

| | Aug | Sep | Oct |
|---|---:|---:|---:|
| model GWh / CEMS GWh | 1,412 / 1,170 | 316 / 892 | 215 / 1,267 |
| model hours at must-run only | 1 | 602 | 744 / 744 |
| CEMS mean units online | 4.00 | 3.86 | 3.95 |
| CEMS median loading when online (of p99.5) | 0.71 | 0.59 | 0.82 |

This is a **level** miss, not a decommitment miss. CEMS keeps all four units on at 59–82 % loading. The model never
cycles Bridger below its must-run tranche (0 hours below 5 % of nameplate). Upper bound for a bridge holding CEMS-online
units at minimum load during model-off hours:
- at measured LSL: **0.03 TWh**;
- at 30 % / 40 % (unmeasured, contradicted by the meter): 0.49 / 0.80 TWh;
- against a Sep+Oct gap of 1.63 TWh.

**Verdict:** a bridge would stack on `coal_mustrun_per_plant` (rule 19) or replace it for about zero gain. No PRECOMMIT.
The Aug–Oct residual points back to price formation (lever B) and the captive-mine variable cost (retest
`coal_captive_marginal_fuel_price` in composition, plan §3.9 step 5).

## 3. R-3 census — Bridger 2023 Feb–May take ceiling (receipts + stocks, declared `stock_min`)

**Data.** Plant 8066's stocks are **published**: `data/raw/coal-stocks/coal_stocks_2018..2024.csv`, EIA-923 Page 2, month-end,
SUB.
- Stocks: Dec 2022 798 kt, the lowest year-end on record. 2023 by month (kt): 565, 620, 768, 790, 808, 752, 718, 643,
  615, 487, 511, 523. The pile was rebuilt Feb–May.
- Receipts, `coal_receipts_2023.csv` Page 5: 4.70 Mt in 2023 vs 5.61 Mt in 2022. Feb–May (kt): 313, 276, 132, 238.
- No R-3 implementation exists yet in any lane. The nearest is NEXT-9's `coal_monthly_pile_measured_receipts` (R).

| form | `stock_min` | binds on keeper #20? | Feb–May removed |
|---|---|---|---:|
| per-month, `R_m + S_{m−1} − stock_min` | 0 | **never** (every month's ceiling 1.4–1.7 TWh > model) | 0 |
| per-month | 487 kt (2023 low: same-year outcome, inadmissible) | Jan, Feb, Mar | 0.95 TWh |
| per-month | 798 kt (pre-2023 minimum) | refuted: measured burn breaks it every month | — |
| cumulative, `S_dec + ΣR − stock_min` (model's own burn) | 0 | Feb–Jul | **≈1.08 TWh** |

- Feb–May 2023: keeper #20 Bridger 3.06 TWh vs CEMS 1.22 gross / 1.12 net, a gap of 1.84–1.94 TWh.
- The cumulative form closes about 56–59 % of that gap. But its ceiling limb **is the arm already adjudicated R**
  (NEXT-9, at stock_min 0, Bridger lots all contract).
- Fixing all of Feb–May was worth +0.036 r (#18: 0.662 → 0.698). A ~57 % fix on #20 (0.669) points to about 0.69,
  **below the floor**, unless the displaced energy lands in Jun–Oct. NEXT-9 and NEXT-16 arm D both saw it land in Nov–Dec.
- Rule 19: R-3 must enter as the measured-inflow replacement on the existing `coal_fuel_inventory_monthly_pile` identity,
  never as a second row.
- Rule 28: re-arming the NEXT-9 ceiling needs R-3 itself as the new evidence.

**Reading:** R-3's per-month form, as ruled, is inert for Bridger. Its cumulative form is the NEXT-9 limb (R) and alone
projects below the floor. **Not queued ahead of lever B.** It is the natural composition partner if lever B lands and Feb–May
remains the residual (then plan §3.9 step 6, the ledger row).

## 4. Side item — EIA-930 NWPP peak "discontinuity" (68.6 / 68.7 GW 2019–20 vs ~49–51 GW): an artifact, never on the solve path

The only source is the close-out audit C.7 line (`AUDIT-eia860-capacity-vintage-settlement-2026-10-02.md:222`), which is
copied into plan line 72 and the matrix §5.9 head. It summed the members' **raw** `Demand`, in which Avista (AVA) posts
~41,000 MW (28–30× its median) on:
- 2019-12-21 08:00 UTC (41,267 MW) and 2019-10-07 21:00 UTC;
- 2020-09-05 07:00 UTC, and twice on 2020-10-06.

The raw column is dirty in 2021–25 too (PACE 65.8 GW 2023, NEVP 68.6 GW 2024, AVA 811 GW 2025); the audit's screen caught
those but not AVA 2019–20.

`Demand (Adjusted)`, which the model's loader reads (`eia930/demand.py:807-829` over `frames.py::_pool_hourly_frame`), has
coincident peaks of 46.5 / 43.3 / 49.7 / 49.4 / 49.3 / 52.6 / 51.0 GW. 2020 has PSEI missing in EIA-930 and filled from
FERC-714 in the loader. Keeper #20's P1 demand peaks at 44.0 / 46.5 / 46.4 / 48.0 / 46.7 / 50.2 / 47.8 GW and reproduces
the TWh hard stops exactly.

**Disposition:** no loader fix. The 2.5×-median screen was deliberately refused in `frames.py:971-976`, because it would
delete CHPD's real January 2024 cold-snap hours. The C.7 line should read the Adjusted peaks above. That audit belongs to
the W0 lane; the correction is routed to the desk, not edited here.

## 5. Hygiene

- `iso_configs.py` NWPP docstring: corrected. The forecast path uses legacy bins (`CAMPD_BINNING_ISOS`), while the
  backcast synthesizes per-plant tranches from `thermal_tranches_NWPP.csv`, so every keeper records
  `use_campd_bins: true` (NWPP-43).
- Keeper #20 lacks `unit_marginal_<Y>.parquet`. Per rule 15 it is written by the next span's solves and enforced by
  `promote_keeper.py` preflight. It is not backfilled outside a promotion.
