# FINDING — NWPP-NEXT-20 (closeout-NWPP wave 1): the two seam fixes, lever C and R-3 censuses, the EIA-930 peak item

Lane closeout-NWPP (charter from the Backcast close-out desk, 2026-10-02; plan §3.9). **Zero LP.** Keeper #20
(`2026-10-01-nwppnext16c-combined-vintage`, pin `33014efc`) is unchanged and byte-identical on its own recipe: every edit below
is on the default-off priced-seam path (`reference_price_interface`, which no NWPP keeper arms) or is documentation.

Probes (all read committed files; run from the repo root):
`scripts/probes/_nwppnext20_seam_pricetaker_phase0.py` (§1), `scripts/probes/_nwppnext20_leverc_bridger_shape_phase0.py` (§2; needs
keeper #20's 2023 leg `a54c7b97a9c588564bab90746f2dbbc44fd56838` extracted), `scripts/probes/_nwppnext20_r3_bridger_ceiling_phase0.py` (§3).

## 1. NEXT-20: the two seam fixes (owner card 2026-10-02 "Fix both, then solve")

### 1a. CAISO seam → CISO net load

`INTERFACE_NEIGHBORS["NWPP"]` CAISO block: `load_shape_kind="net"` (demand − solar − wind of CISO). Categorical and physical,
the form CAISO's own WECC_DSW corridor uses; within-day r vs CAISO RT rises from 0.37 / 0.24 / 0.08 to 0.56 / 0.58 / 0.62
(2023/24/25, FINDING-nwppnext19 §6a). The shape has mean 1, so the annual seam level and the `hr_by_year` anchors are
unchanged (CAISO seam mean 41.6 / 35.7 / 56.5 / 84.2 / 49.8 / 40.0 / 37.9 in both forms). Net-shape range: min −0.41 (2025,
three duck-belly hours, −$15.6/MWh) to max 2.44 (2022). Pre-existing data note, not fixed here: CISO 2019 hours 8463–8465 read
14–96 MW `Demand` in EIA-930 (both shapes take ~0 there).

### 1b. WECC_CAN anchor → BC Hydro's all-hours WEIM price

The Mid-C **Peak** ICE index was peak-only and sat $12–38 above measured BPAT. Admissible all-hours replacement found and
landed: the RTPD LMP at **`ELAP_BCHA-APND`**, BC Hydro / Powerex's WEIM load-aggregation point. That is the price on the
**Canadian** side of the seam, the analogue of the CAISO seam's MALIN anchor. Canada is outside the footprint (ruling N1),
so this is a counterparty price, not the footprint's own outcome (rule 13). Fetched from OASIS
(`scripts/data/fetch_nwpp_bcha_elap.py`, the NWPP-13 client) into `data/raw/nwpp-weim/bcha_elap_hourly.parquet` (README §5).
Retention began **2023-06-22** on the fetch date.

| year | priced hours | BCHA mean $/MWh | hour-matched HH + basis | HR (new) | HR (Mid-C Peak, old) |
|---|---:|---:|---:|---:|---:|
| 2023 (Jun 22 – Dec) | 4,633 | 88.47 | 2.451 | **36.10** | 37.11 |
| 2024 | 8,784 | 41.21 | 2.006 | **20.55** | 30.73 |
| 2025 | 8,760 | 34.99 | 3.336 | **10.49** | 13.90 |
| flat (2019–2022, forward) | | | | **22.38** | 27.25 |

BCHA vs measured BPAT, monthly means: 2023 BCHA sits ~$15–50 above BPAT in **every** month (Jun 65 vs 33, Aug 99 vs 49,
Oct 102 vs 66). That matches BC's 2023 drought, when BC Hydro was a record net importer. 2024–25 track BPAT within a few
dollars (2024 41.2 vs 44.9; 2025 35.0 vs 34.4), apart from January 2024 (72 vs 182, the cold snap on the US side). Hourly
r BCHA vs BPAT: 0.33 / 0.52 / 0.62. The 2023 premium is a counterparty fact, not a bias of the anchor. Misalignment
(rule 14): the seam also carries AESO's 325 MW MATL leg, which has no price here.

Seam reference-price annual mean, $/MWh, old → new (`neighbor_reference_price`): 2019 64.7 → 53.2 · 2020 50.2 → 41.3 ·
2021 101.4 → 83.2 · **2022 169.7 → 139.4** · 2023 87.2 → 84.8 · 2024 61.5 → 41.1 · 2025 46.3 → 34.9 (measured BPAT 2023
Jun–Dec / 2024 / 2025: 48.7 / 45.0 / 34.4).

**Residual risk, stated:** 2019–2022 price at the flat HR × that year's gas, and the flat mean (22.38) is pulled up by
2023's drought HR. With 2022 gas at $6.23 the Canada seam reads $139 in 2022 and $53 in 2019, likely above the true
Canadian-side price. No measured BCHA price exists before 2022-04 (BCHA joined WEIM then) or before the retention edge.
This is the construction every registered seam uses (SPP-51 / NWPP-20). It is flagged as a PRECOMMIT watch item, not
re-fitted.

### 1c. Price-taker against keeper #20 (handoff step 4)

Each seam's 8 export and 8 import tranches are cleared against keeper #20's P1 price, averaged over the seam's border
zones, hurdle applied. NWPP's price is held fixed, so this is an **upper bound** on the seam's reach. In the armed LP,
NWPP's price rises toward the seam and the flow self-limits.

| year | seam | net export, prior form | **net export, fixed** | measured |
|---|---|---:|---:|---:|
| 2023 | CAISO | 21.97 | **14.49** | 8.69 |
| | WECC_SW | 3.11 | 3.11 | (see note) |
| | WECC_CAN | 22.64 | **22.28** | (see note) |
| 2024 | CAISO | 36.19 | **28.29** | 11.39 |
| | WECC_SW | 6.68 | 6.68 | |
| | WECC_CAN | 27.50 | **17.07** | |
| 2025 | CAISO | 20.60 | **14.54** | 12.50 |
| | WECC_SW | 0.19 | 0.19 | |
| | WECC_CAN | 15.97 | **3.57** | |
| **footprint** | 2023 / 2024 / 2025 | 47.7 / 70.4 / 36.8 | **39.9 / 52.1 / 18.3** | **−6.63 / −3.12 / +5.43** (Σ(NG−D), the served schedule's base) |

TWh, export-positive. The CAISO "measured" column is the members' CISO legs. These mirror CISO's own book to within
0.06 TWh (`nwpp_net_interchange` docstring, NWPP-34), so they are reliable. Per-seam WECC_SW / WECC_CAN figures from the
member DIBA files are **not** reliable: that sum (+12.5 / +17.0 / +21.2 TWh in total) inherits BPAT's per-leg
over-report, and it is the series the served schedule refuses. Only the footprint total is admissible.

Reading:
- Both fixes cut the over-export: the CAISO net shape by 6–8 TWh/yr, the BCHA anchor by 10–12 TWh in 2024–25.
- The fixed seams still sit far above the measured net position against keeper #20's flat price, by 34–55 TWh. The
  keeper's NWPP price ($29–51 mean, flat within month) is below every seam level.
- Under an armed solve, that gap has to close through NWPP's own price. This is exactly the mechanism lever B is
  meant to test. It is also the largest risk to C4 gas, CT_PEAKER energy and rule 20.

Fallback HRs for 2019–2022: CAISO 11.05, WECC_SW 14.43, WECC_CAN 22.38.

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
