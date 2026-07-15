# FINDING (caiso winter-pricing diagnosis, 2026-07-15): the CAISO winter over-pricing (Jan-2023 +71%, Feb +44%) and the 8.4× C3c tail are a delivered-gas LEVEL basis-source misalignment — the hub overlay prices every gas unit at the EIA N3050CA3 monthly *acquisition-cost survey* (+$24.34 basis in Jan-2023) while the marginal DEB bids at the *daily spot* the repo already carries ($16.13 Jan mean); hydro-year and winter-import under-modeling are measured red herrings

**Session:** caiso winter-pricing diagnosis, 2026-07-15 (paper design pass — no
LP solved, no model code touched).
**Baseline:** the caiso-80 keeper `2026-07-13-caiso-80-supply-demand`
(bundle `results/calibration/caiso80_supply_consistent_demand/`), scored
against the now-complete full-year 2023 actuals: Jan $222.0 vs $129.7 (+71%),
Feb $95.7 vs $66.4 (+44%), C3a +32.5%, C3b NRMSE 0.562, C3c 667 h >$200 vs 79
actual, C4 gas NRMSE 0.305. The demand-basis wedge is CLOSED
(`caiso_supply_consistent_demand=True`, FINDING-caiso80). Every number below
reproduces from committed repo data.

## 1. The primary root cause: monthly survey gas vs daily spot gas

The keeper's CAISO gas path (`gas_hub_basis_overlay=True`,
`gas_hub_basis_daily=False`) reprices EVERY CAISO gas unit in every covered
month at the FLAT monthly hub level

    level(m) = HenryHub_monthly(m) + basis(m) + CAISO_CITYGATE_TRANSPORT_ADDER (0.46)

where `basis(m)` is the CAISO row of `data/raw/gas_basis_by_iso_month.csv`,
sourced from **EIA N3050CA3 — the monthly California citygate survey**
(`fuel.py::apply_hub_basis_overlay` → `iso_hub_monthly_gas_prices` →
`load_winter_gas_basis`). N3050CA3 is an LDC purchase-portfolio **average
acquisition cost** (bidweek contracts settled at the prior month's top,
storage withdrawals, hedges) — NOT the daily spot index that CAISO's
cost-based DEB (default energy bid) formula prices the marginal unit at. The
repo already carries the correctly-aligned series: the measured CA Composite
Average citygate **daily spot** (`data/raw/gas-prices/caiso_citygate_daily.csv`,
EIA Weekly compact spot table, true-dated, 2023–2025) — but the keeper uses it
NOWHERE (the daily leg `_caiso_hub_daily_gas_prices` is gated behind
`gas_hub_basis_daily`, off in the keeper, and even when armed it renormalizes
the daily shape BACK to the survey monthly level, mean-preserving — caiso-54).

Model monthly level vs the measured daily-spot monthly mean (+0.46 transport
on both; CC floor = 7.0 HR × gas + $2.5 VOM + 0.37 t × ~$30 CARB):

| month | model $/MMBtu | daily-spot mean | ratio | CC floor model | CC floor spot | scored LMP model/actual |
|---|---|---|---|---|---|---|
| 2023-01 | 28.08 | 16.59 | **1.69** | $210 | $130 | 222.0 / 129.7 = **1.71** |
| 2023-02 | 11.17 | 7.54 | **1.48** | $92 | $66 | 95.7 / 66.4 = **1.44** |
| 2023-03 | 4.87 | 6.96 | **0.70** | $48 | $62 | model 53–54 vs DA 64.9 (UNDER) |
| 2023-10 | 3.56 | 4.60 | **0.77** | $39 | $46 | model 47.2 vs DA 57.5 (UNDER) |
| 2023-12 | 6.89 | 4.25 | **1.62** | $62 | $43 | caiso-82 Dec-23 gap +23.6 |
| 2024-02 | 5.86 | 2.88 | **2.03** | $55 | $34 | caiso-82 Feb-24 gap +24.2 |
| 2024-03 | 4.54 | 2.28 | **1.99** | $45 | $30 | caiso-82 "Mar–Jun overnight +12–14" |
| 2025-12 | 6.38 | 4.10 | **1.56** | $58 | $42 | caiso-82 Dec-25 gap +25.1 |

(Full 33-month table reproduces from the three committed files above; the
survey sits >1.2× spot in 24 of 33 covered months, mean ratio ≈1.3.)

The identification is exact where it matters most:

- **Jan-2023: gas ratio 1.69 = LMP ratio 1.71.** The model's Jan mean λ
  ($222, every CA zone — keeper payload `lmp.pMon`) IS the efficient-CC cost
  at $28 survey gas ($210–237); the actual ($129.7) IS the efficient-CC cost
  at the $16.6 measured daily-mean spot ($130). Feb: 1.48 vs 1.44.
- **The C3c tail is the same arithmetic.** At a flat $28/MMBtu the
  committed/econ CC rungs price ≥$210 for all 744 January hours — the
  caiso-53 root-cause note verbatim ("the measured $28/MMBtu citygate spike ×
  the repriced committed CC (~$213) crosses $200 where actual held below").
  At the true daily series, CC crosses $200 on no day (max $24.29 on Jan-12 →
  CC ~$185) and the tail collapses to the CT-rung/scarcity-overlay residual.
- **caiso-54 already proved shape-alone is not the fix** (2023 tail 454→455 h
  under `--gas-hub-basis-daily`): the daily factors are renormalized to the
  survey monthly mean, so the level defect survives the shape fix. The LEVEL
  is the defect.
- **Both signs of the monthly residual match**: Mar-2023 (0.70×) and Oct-2023
  (0.77×) — the two months where the survey sits BELOW spot — are exactly the
  months the model UNDER-prices. A residual-fitted knob cannot do that; a
  basis-source misalignment does.
- The wedge also reproduces the caiso-82 §1 soft-month M-regime gaps
  (Dec-23 ΔCC $18.5 vs gap +23.6; Feb-24 ΔCC $20.9 vs +24.2; Dec-25 ΔCC $16.0
  vs +25.1), i.e. a large share of the "reality clears below the model's
  carbon-inclusive CC floor" signature is the model's floor being computed on
  the wrong gas series.

## 2. Measured red herrings (do not chase)

- **Hydro-year mismatch — REFUTED in code.** `ScenarioConfig.hydro_year`
  ("normal") only acts on the forecast path
  (`data/hydro.py::build_hydro_fleet`: consumed under `forecast_budget`); the
  keeper backcast runs `hydro_eia930_monthly=True` + `hydro_backfill_year=2024`
  (caiso-76), which pins each month's budget to the year's OWN measured
  EIA-930 NG:WAT total — record-wet 2023 included (measured Jan-2023 fleet
  mean 1.99 GW is in the budget). The hourly ceiling is the year's own
  measured p95 (`eia_loader.py::measured_hydro_hourly_envelope` — own-year
  frames first, climatology only as forecast fallback). Placement-side, the
  caiso-82 min-flow floor probe measured the within-month reallocation
  **price-inert at the mean** (−0.3…+1.3 $/MWh). There is no hydro lever that
  moves a +$92/MWh January miss.
- **Winter import under-modeling — SECONDARY at most, and not the January
  driver.** The keeper payload's own import-hub node duals print Jan-2023
  PNW $28.67 / DSW $59.47 while every CA zone prints ~$222: the model is
  import-constrained AT its measured per-(month×hod) p95 corridor envelopes
  and still overshoots. Measured Jan-2023 net imports (EIA-930 CISO TI):
  mean 4.67 GW, p95 7.18 GW — the model's envelope already admits ≈ the
  measured depth; no admissible import-capability increase closes a gap that
  the gas level closes arithmetically. The real import-side defect is the
  caiso-82 §3 static-fitted spot-rung composition/carbon wedge (G-26 /
  issue #1350 / audit C-6) — a soft-month M-regime and local-tail lane, banked
  as caiso-83 with `derive_caiso_import_tranches.py` (NEISO Q-Q precedent)
  named as closure.
- **Winter gas TIMING (daily shape) — already fixed, insufficient.** The
  true-dated daily leg exists (`_caiso_hub_daily_gas_prices`, caiso-54) and is
  G-A1 mean-preserving; it redistributes the January tail but cannot lower a
  wrong monthly mean.

## 3. Secondary structural defects (each moves part of C3c/C3a)

- **The CAISO scarcity overlay's reserve measure omits import capability
  entirely.** `results/scarcity.py::caiso_scarcity_overlay` computes LOLP ×
  (VOLL − λ) on `reserve_headroom`, which counts thermal (RESERVE_FUEL_TYPES)
  + storage + curtailed VRE only; import tranches are `fuel_type="import"`
  pseudo-generators (`transmission.py::build_import_generators`) and
  contribute ZERO headroom even when unloaded within corridor capability. In
  the real market the power-balance penalty prices fire only after economic
  intertie bids exhaust (RA imports are must-offer, CPUC D.20-06-028). This
  is the open "C3c-2023 spurious tail 458→665, scarcity-overlay interaction"
  item: the overlay can fire while the LP itself still has unloaded
  sub-VOLL import supply — an internal inconsistency, not a parameter issue.
- **Static-fitted import spot rungs** (above, caiso-83 lane).
- **Offer peak multipliers (CT_PEAKER peak 4.0 / ST_GAS 4.2, residual-
  identified per the DOF ledger)** are multiplicative in fuel
  (`fleet.py::` peak_hr = base_hr × offer["peak"]), so any gas-level error is
  amplified ×4 on the peak rungs. NOT a candidate while the measured-input
  defect above is open (rule 1: structure first, offer tuning last); re-examine
  against DMM-observed conduct only if a tail residual survives caiso-84/85.

## 4. Disposition

Candidate bundles (one lever each on the caiso-80 recipe, all-years, rules
1/13/14/15/20/23/24 compliant) are specified in the session handoff:
caiso-84 (`caiso_citygate_spot_level` — the daily-spot level+shape swap,
PRIMARY), caiso-85 (`caiso_scarcity_import_headroom` — overlay reserve-measure
consistency), caiso-86 (the banked caiso-83 measured import ladder,
derive-first), optional caiso-84b shape-only control. Expected directions are
pre-registered in the handoff before any solve.

Rule-15 note: this FINDING documents the misalignment that licenses the swap —
the survey measures what LDC portfolios PAID (acquisition cost), the daily
spot measures what the marginal cost-based bid PAYS; both are measured EIA
series, and the marginal-offer representation requires the latter. The
forward story is unchanged: forecast years keep the HH-forward + climatological
basis path (no daily realization exists forward), exactly the F923
delivered-price admissibility class (rule 13).
