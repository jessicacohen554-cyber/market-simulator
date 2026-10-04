# FINDING closeout-CAISO-w4: phase 0 (zero LP), the 2020 C1 CC_REGULAR miss (2026-10-04)

**Charter.** Desk, 2026-10-04: take a w4 on 2020, stacked on the w3 recipe with w3 as the control. The miss is 0.40
TWh, in Jun–Sep and Dec, with the clean rungs marginal $1–3 above λ. The desk asked what measured input still prices
the rungs out in those months: the Aug 2020 heat-event import bids/RA, summer hydro, or the Dec 2020 gas print.

**Control.** w3 probe `2026-10-04-closeout-caiso-w3-own`, 2020 leg `closeout_caiso_w3_a1_2020` (shard commit
`02a35542`).

**Branch.** `claude/closeout-caiso-w4`, cut from the w3 head `56c05f65`.

**Outcome: no admissible lever.**
- Both measured candidates fail their pre-fixed validation gates 0 of 4.
- So there is no PRECOMMIT and no solve; the w3 promotion request stands as it is.

## 1. Decomposition (w3 2020 leg)

Probes `_closeout_caiso_w4_cc_object.py` (output `_cc_object_w3.json`) and `_closeout_caiso_w4_2020_hours.py`
(output `_2020_hours_w3.json`).

**The CISO balance, model − actual (TWh).**

| Component | Δ, all hours | Δ in the CC over-run hours |
|---|--:|--:|
| CC_REGULAR (vs EIA-923 levelled on CEMS) | **+5.04** | +8.66 |
| net imports (EIA-930) | **+0.08** | −5.31 |
| CT_CHP / CT_PEAKER / ST_GAS | −1.83 / −1.88 / −1.24 | −1.17 / −0.68 / −1.04 |
| CC_CHP | +1.05 | +0.68 |
| hydro / solar | +1.11 / +1.31 | +1.09 / +0.61 |
| demand (model − EIA-930) | −1.86 | −1.51 |

**Scored gas family:** +2.6 TWh (62.91 vs 60.31), against a CC_REGULAR miss of +5.00. About half the CC miss is
intra-gas substitution, and the other half is import timing; annual net imports are matched.

Every other correction in the balance would push CC *up*: hydro over, solar over, demand under. The structural CC
over-run is therefore larger than the scored miss.

**By month (TWh, model − measured).**

| Month | CC | DSW | PNW | other gas | λ SP15 | clean-rung offer (formula hub) | marginal CC offer |
|---|--:|--:|--:|--:|--:|--:|--:|
| Jun | +1.21 | −0.69 | −0.17 | −0.54 | 24.7 | 26.7 | 26.6 |
| Jul | +1.19 | −0.35 | −0.35 | −0.79 | 29.4 | 29.0 | 27.3 |
| Aug | +1.20 | −0.56 | −0.03 | −1.04 | 39.5 | 39.5 | 32.0 |
| Sep | +1.00 | −1.43 | +0.59 | −0.75 | 40.5 | 42.5 | 34.9 |
| Oct | −0.32 | +0.61 | +0.31 | −1.04 | 39.1 | 31.0 | 39.2 |
| Dec | +0.97 | −1.58 | +0.65 | −0.41 | 43.9 | 44.1 | 40.4 |

**By hour band (Jun–Sep + Dec, TWh).**

| Band | CC | DSW |
|---|--:|--:|
| 00–05 | +2.40 | −2.07 |
| 17–21 | +1.16 | −1.64 |
| 22–23 | +0.79 | −0.80 |
| 06–16 | +1.23 | −0.10 |

The 06–16 band is intra-gas: other gas is −1.93 there.

**What limits DSW in the DSW-shortfall CC over-run hours** (object months; 2,166 hours; 5.88 TWh shortfall):
- corridor binding: 0.00 TWh;
- no rung armed: 0.00 TWh;
- rung at capability: 0.14 TWh;
- **rung priced, below capability: 5.75 TWh.** Rung offer − λ is p25 $0.00 / p50 $1.04 / p75 $3.78. By rung:
  overnight 1.97, daytime 2.97, late-evening 0.80.

So the rung is the marginal unit; depth is not the limit. The rung's offer is the R-CAISO-18 formula hub,
`AZ gas(month) × HR 13.0 × CISO net-load shape`. In Sep and Dec it sits $4–8 above the marginal CC offer, and in Oct
$8 below it.

**The desk's three candidates.**
- **Aug heat event:** not the object. August is +1.20, no larger than June or July.
- **Summer hydro:** not the object. Hydro is +1.11, over rather than under, and correcting it would raise CC.
- **Dec gas print:** not the object. The AZ EIA-923 rebuild for Dec 2020 is $3.31/MMBtu against $4.00 CA delivered;
  AZ is below CA in every 2020 month.
- **What actually varies the formula month to month is the CISO-proxy net-load shape** (Sep ×≈1.22, Oct low), not
  the gas level.

**There is no measured 2020 hourly hub print.**
- OASIS per-node `SingleZip` retention is about 39 months (lmp-data/CAISO README).
- The owner ruled 2026-10-02 that there will be no requester-pays fetch.
- The only measured 2020 Palo Verde price is the ICE daily on-peak index.

## 2. Candidates and their gates (fixed before computing, sent to the desk before any number)

| # | Candidate | Gate | Result |
|---|---|---|---|
| S1 | Formula shape driver: CISO-proxy net load → the hub's own region (EIA-930 `Region == "SW"`, BALANCE archive: AZPS, DEAA, EPE, GRIF, HGMA, PNM, SRP, TEPC, WALC). Same exponent, clip, HR and gas (rule 14, measured over proxy). | Beats the proxy vs the OASIS hourly Palo Verde print on BOTH r and RMSE in ≥ 3 of 4 years 2022–25 | **FAIL, 0 of 4** |
| S2 | Within-month day shape: CA citygate gas factor (w3 L2) → ICE "Palo Verde Peak" daily index, month-mean preserving (no basis fitted) | Beats w3 vs the OASIS daily-mean print on BOTH r and RMSE in ≥ 3 of 4 years 2022–25 | **FAIL, 0 of 4** |

**S1** (probe `_closeout_caiso_w4_shape_validation.py`, output `_shape_validation.json`). Hourly r / RMSE, proxy →
SW-own:

| Year | Proxy | SW-own |
|---|---|---|
| 2021 (reported) | 0.746 / 25.7 | 0.511 / 31.7 |
| 2022 | 0.867 / 48.8 | 0.680 / 64.7 |
| 2023 | 0.671 / 35.0 | 0.446 / 40.8 |
| 2024 | 0.736 / 22.4 | 0.597 / 26.7 |
| 2025 | 0.737 / 15.3 | 0.540 / 18.5 |

The desert-SW region's own net load has a far weaker midday trough than the hub print, and it moves the daytime bias
by +9 to +28 $/MWh in the object months. The CISO solar-driven shape is the better driver of the Palo Verde price.
That is consistent with WEIM transfers being priced on CAISO's net load.

**S2** (probe `_closeout_caiso_w4_ice_validation.py`, output `_ice_validation.json`; ICE workbooks
`eia.gov/electricity/wholesale/xls/archive/ice_electric-<y>final.xlsx`, scratch, not committed). Daily r / RMSE,
w3 → ICE:

| Year | w3 | ICE |
|---|---|---|
| 2022 | 0.941 / 36.3 | 0.786 / 67.2 |
| 2023 | 0.761 / 17.6 | 0.772 / 25.5 |
| 2024 | 0.874 / 11.4 | 0.840 / 12.3 |
| 2025 | 0.644 / 12.3 | 0.685 / 13.8 |

ICE wins on r in 2 years but loses on RMSE in every year. The on-peak bilateral index's day-to-day swings exceed the
DAM intertie's (the R-CAISO-12 level gap, now seen in variance too).

**Also checked, not proposed:**
- **2020 own-year clean depths.** The rungs are not depth-limited: 0.14 TWh at capability.
- **CISO-proxy formula bias by hod in printed years** (object months, overnight). It is +20.6 / +53.4 / +6.8 / −3.9 /
  +4.4 $/MWh in 2021–25 and changes sign. There is no structural basis for a re-shape, and fitting an exponent or hod
  profile to prints would be a tuned parameter (rule 1).
- **The intra-gas half** (CT_CHP / CT_PEAKER / ST_GAS under-run, about −5 TWh in 2020):
  - it is present in every year, with C1 CT_PEAKER −0.6 to −1.9 and ST_GAS about −1.2 in 2019–23;
  - its CHP limb is adjudicated (`chp_steam_duty_window` R; the WP-3 level re-derive);
  - a fix would be live in 2022–25. That makes it a separate full-span lane, not a 2020 lever.

## 3. Disposition

- **No PRECOMMIT and no shards.** No candidate cleared its gate, and the remaining levers are either tuned (a formula
  re-shape) or full-span (intra-gas).
- **The w3 promotion request stands unchanged:** three FAIL→PASS flips and one gated FAIL left, C1 CC_REGULAR 2020 at
  +5.00 / ±4.60.
- **S1 and S2 are recorded as DO-NOT-REDO** in the CAISO lever queue (`docs/mechanism-testing-matrix.md` §5.2).
  Neither has a `ScenarioConfig` field, so no matrix row was minted.
- **Downloads:** ICE workbooks only, held in scratch as a validation check. Nothing was committed.
