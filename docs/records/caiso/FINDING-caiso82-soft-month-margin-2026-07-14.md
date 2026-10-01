# FINDING (caiso-82): the C3a soft-month body overprice decomposes into two measured margin-composition defects — (i) the budget LP vacates the hydro trough hours real min-flow physics keeps wet, and (ii) the import ladder charges a hard carbon rung on marginal MW that reality supplies carbon-free at hub parity; (i) is implemented as the hydro min-flow floor probe (pre-registered below), (ii) banks as the G-26 measured-ladder lane

**Session:** caiso-82, 2026-07-14.
**Lane:** A of the caiso-81 handoff (rule-1 first open lane — the C3a 2024/25
body overprice, "soft-month margin composition: what sets price when gas
shouldn't be marginal").
**Baseline:** the caiso-80 keeper `2026-07-13-caiso-80-supply-demand`
(registered CI record; C3a +18.7/+28.4/+32.8 %, vs DA +8.9/+17.2/+29.1 %).
**Provenance note:** §1–§2 numbers reproduce from COMMITTED artifacts only
(the keeper payload's 8760-h `lmpDeltaHr` + `actual_lmp_hourly_CAISO.parquet`
+ `wecc_intertie_lmp_hourly_CAISO.parquet` + `caiso_citygate_daily.csv` +
EIA-930 CISO extracts). §3's model-side attribution used a THROWAWAY
session-container replay of the keeper recipe (never registered, rule-16
diagnostic clause); its role is attribution only — every load-bearing
magnitude is committed-data-derived.

## 1. Where the overprice lives (committed payload vs actuals)

Regime split of each month's mean gap by the ACTUAL price: L = actual ≤ $10
(surplus/curtailment), M = $10–100 (normal merit), H > $100. The gap is NOT
curtailment-hour-concentrated: the M-regime carries 50–95 % of the soft-month
gap, and the hour-of-day profile is BROAD — 2024 Mar–Jun overnight (h0–5)
prints +12–14 $/MWh with zero solar on the margin. December is nearly pure
M-regime (Dec-2023 +23.4 of +23.6; Dec-2025 +22.7 of +25.1 $/MWh).

The sharper cut is the carbon-inclusive gas-CC cost floor (7.0 HR × citygate
+ $2.5 VOM + 0.37 t/MWh × CARB allowance): **reality clears BELOW that floor
30–88 % of hours in every soft month; the model 0–39 %.** Hours where actual
< floor but model ≥ floor carry most of each month's gap (Dec-2025: 18.4 of
25.1; Jun-2023: 15.8 of 18.8; Feb-2024: 11.9 of 24.2 $/MWh).

**In those below-floor hours the actual price sits AT WECC hub import parity**
(minimum over Malin ×1.05+$5 / Palo Verde ×1.03+$4 — the keeper's own
delivery bases): act − parity = −9…+4 $/MWh in every month-year, with deep
2024-spring surplus matching the hubs' own negative prints exactly. No
month-year shows the +$13–19 unspecified/fossil carbon wedge the model's
marginal spot rungs charge. Measured net imports in these hours reach 7.6 GW
mean / 10.1 GW p95 (Dec-2025) — far past the ~5.2 GW the model can source
without climbing a carbon rung.

## 2. The hydro side: the LP vacates trough hours that are physically wet

Model monthly hydro is pinned to the measured EIA-930 NG:WAT budget
(caiso-76) and capped by the p95 envelope (caiso-72) — but the LP still
free-places within, and with perfect foresight it drains the troughs:

| year | measured p10 hourly WAT (across months) | model replay p10 | below-floor-hours wedge (actual − model hydro) |
|---|---|---|---|
| 2023 | 0.81–2.24 GW | 0.04–0.76 GW | +0.1…+0.9 GW |
| 2024 | 0.83–1.92 GW | 0.00–0.86 GW | +0.2…+1.0 GW |
| 2025 | 0.17–1.60 GW | 0.00–0.76 GW | +0.3…+0.8 GW |

Real CAISO hydro NEVER drops to zero: run-of-river units and FERC-license /
environmental minimum releases keep 0.8–2.2 GW flowing through every
(month × hod) bucket. The model back-fills those vacated trough hours with
gas at $40–65 offers or carbon-rung imports — in 2023 (wet year, prices below
even import parity for long stretches) this is the DOMINANT defect: the
model's marginal setter in below-floor hours matches NO import offer in
51–93 % of hours (domestic CC tranches at $40–65), while it simultaneously
over-imports vs the measured TI.

**Estimation-stage honesty gates (caiso-81 precedent, checked BEFORE any
solve):** the p05 (month × hod) floor construction fits inside every measured
monthly budget (60–87 % of budget, all 36 month-years) and its NORMALIZED
shape (p05 / monthly mean) is year-stable across a wet and two drier years —
r = 0.845/0.890/0.792 (23v24 / 24v25 / 23v25), mean ratio 0.752/0.767/0.746.
No regime break; the level rides the (measured/forecast) monthly budget.

## 3. The import side (banked lane, NOT probed this session)

The model-side attribution (throwaway replay) shows the marginal setter in
below-floor hours splits between domestic gas tranches (2023-dominant, the
hydro defect above) and the import ladder's CARBON RUNGS (2024/25: the
DSW_CCGT/DSW_CT/WECC_scarcity offers match the model λ in 30–60 % of
below-floor hours; Dec-2025 model λ 57.8 ≈ the scarcity rung's Palo Verde
×1.03 + $6 + $15.1 unspecified-carbon offer, vs actual 34.8 at parity).

The structural defect is the static spot-ladder COMPOSITION: beyond ~5.2 GW
of clean-priced supply (measured DMM firm blocks + 1.8 GW PNW_midC), every
model import MW pays a fossil/unspecified CARB rung — but the measured
CAISO−hub spread shows the real marginal import carries NO carbon wedge in
surplus-West hours (WEIM/EDAM GHG attribution assigns clean resources to
CAISO transfers; the West's surplus IS hydro/solar/wind). The spot tranche
capacities (1800/1800/2200/3000 MW) are the registered G-26 /
issue #1350 / audit C-6 gap: STATIC-FITTED-PENDING-MEASURED, with the
MISO_SEAM_LADDER_BY_YEAR / NEISO measured Q-Q derivations named as the
closure pattern. Supporting stability evidence banked this session: measured
import depth conditioned on the hub-surplus state is year-stable
(south-corridor depth-in-surplus p95 4.7/5.4/5.5 GW, 2023/24/25).

**Why it is NOT this session's probe:** it needs its own derive script +
tranche-EF composition design (zeroing fossil-rung EF would be a non-real
mechanism — rule 1; the real fix is measured clean DEPTH), and it pushes gas
volume DOWN against the open C2 5–7 % gas under-shoot (lane B). One
mechanism per probe; the hydro floor is the smaller, fully-measured delta.
Re-open as caiso-83 with `scripts/derive_caiso_import_tranches.py` following
the NEISO derivation.

## 4. The caiso-82 probe: hydro run-of-river / min-flow floor

`ScenarioConfig.hydro_dispatch_floor` (default off): per-unit hourly
`min_gen` at the measured per-(month × hod) p05 of the ISO's EIA-930 NG:WAT
(`constants.HYDRO_FLOOR_PERCENTILE`, the symmetric complement of the armed
p95 envelope), distributed pro-rata to each unit's monthly budget share,
clipped at unit capability and at 0 (CISO's WAT cell nets PS pumping
negative). Mechanism id `MECH_HYDRO_MINFLOW` (18), classified NON_THERMAL
(the `MECH_FIRM_IMPORT` must-flow class — excluded from merchant
forced-share gates, reported by D-2, ablated in the zero-forcing twin);
`D4_WINDOWS` row (0, 24) — all-hours by measurement, no off-window exists.
Zero fitted scalars: the percentile mirrors the envelope's, the level is the
year's own measured data (forecast: pooled climatology × hydro_year budget).
Implementation: `data/hydro.apply_hydro_minflow_floor`, applied before the
envelope at both solve seams (run_calibration.py / runner.py) so the
envelope's feasibility guard composes.

**Recipe:** the caiso-80 keeper recipe verbatim
(`scripts/probes/_caiso82_hydro_minflow_ab.py`, cloned from
`_caiso80_supply_consistent_demand_ab.py`) + the SINGLE delta
`hydro_dispatch_floor=True`. Years 2023 2024 2025, one invocation, main +
zero-forcing twin, registered as PROBES.

**Session-container smoke (2023 single-year, throwaway, run BEFORE
pre-registration was frozen — disclosed in full):** the floor engages as
designed (fleet mean 2,147 MW on 171 units; trough p10 0.04–0.76 →
0.40–2.11 GW, onto the measured band) and the LP stays feasible — but the
monthly mean λ is nearly UNMOVED (deltas −0.3…+1.3 $/MWh; the monthly-budget
reallocation nets out: water forced into flat-supply-curve troughs is water
removed from other hours), annual gas +0.2 TWh, gas-vs-CEMS hourly r
0.896 → 0.891 (noise-level), λ>150 h count identical. The floor is
structurally correct and price-inert at the mean. **The lane-A C3a closure
claim therefore moves to the import-composition mechanism (§3); this probe's
claim is structural fidelity** — the caiso-72 envelope precedent (a real
capability/obligation bound stays in whatever the residual does, rule 1),
completing the measured hydro placement pincer (budget = measured monthly,
ceiling = measured p95, floor = measured p05).

**Pre-registered directions (BEFORE the registered solve):**

1. Hydro trough dispatch rises onto the measured min-flow band in all three
   years (fleet p10 from ~0–0.9 GW to the floor's own p10, 0.53–0.68 GW —
   the workflow tripwire) and the twin drops back.
2. C3a ~NEUTRAL (2023 smoke: monthly deltas −0.3…+1.3 $/MWh). Any soft-month
   improvement is a bonus, NOT the promotion case; the import-composition
   share of the gap (§3) stays by construction.
3. C1 fuel-mix PASS holds (hydro monthly energy unchanged by construction;
   gas annual ~flat — smoke +0.2 TWh).
4. C2 stays within its current band (registered −6.2/−6.6 % under, 2024/25).
5. C4 gas fit within noise (smoke Δr −0.005).
6. C3c tail counts ~unchanged (smoke λ>150 count identical); the previously
   feared evening-thinning tail growth did NOT materialize in the smoke.
7. C5a/C6/C7/C8 hold; D-2 gains a reported (ungated, non-thermal)
   MECH_HYDRO_MINFLOW row; D-4 all-hours window binds nowhere off-window by
   construction.
8. FAIL conditions (pre-registered): any load-bearing gate flips PASS→FAIL,
   or the forced trough water measurably WORSENS a scored magnitude beyond
   band-edge noise — then the floor percentile choice is re-examined (p02
   before p05) rather than tuned to the residual.

**Promotion case:** rule-1 structural fidelity with all gates holding —
NOT fit improvement. Owner promotes (miso-62 pattern); registered as PROBES
either way.

**LOYO note:** nothing is pooled or fitted — each year rides its own
measured floor (the caiso-80 construction class), so the three registered
years ARE the per-year independent reads; the estimation-stage stability
gate (§2) is the cross-year transfer check, already passed.

## 5. Files

- Mechanism: `src/market_sim/config/scenarios.py` (`hydro_dispatch_floor`),
  `src/market_sim/config/constants.py` (`HYDRO_FLOOR_PERCENTILE`),
  `src/market_sim/data/hydro.py` (`apply_hydro_minflow_floor`),
  `src/market_sim/data/floor_mechanisms.py` (`MECH_HYDRO_MINFLOW`),
  seams in `scripts/run_calibration.py` + `src/market_sim/runner.py`,
  `scripts/legitimacy_diagnostics.py` (`D4_WINDOWS`),
  `tests/test_hydro_floor.py`.
- Probe: `scripts/probes/_caiso82_hydro_minflow_ab.py`; solve/register
  workflow `.github/workflows/caiso82-solve-register.yml`.
- Calibration-log entry: caiso-82 (registered after the CI solve lands).
