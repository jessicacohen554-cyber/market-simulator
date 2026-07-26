# NYISO price formation (nyiso-76): two construction fixes, and the keeper-vs-main drift they uncovered

Session branch `claude/nyiso-price-formation-c3-v8x7ds`, 2026-07-26. Charter: the
nyiso-76 C3a/C3b/C3c price-formation lane. Baseline keeper
`2026-07-26-nyiso-75-solar-shape` (bundle `results/calibration/nyiso75_solar_shape`).
All arms solved in-session, 3 years / bundle (rule 16), scored on P1.

## 0. Headline

Both chartered defect fixes were built, tested and committed **default-off and
byte-identical when off**. Neither closes the NYISO price-formation gap, and the
lane's most consequential result is neither fix — it is that **the committed
NYISO keeper no longer reproduces on current `main`** (§3). The keeper was solved
at git `af74927`; `main` is 81 commits further on, and replaying the keeper's
exact configuration on today's code moves 2023 C3a from **+17.8 % to −0.9 %**,
2025 from **−3.2 % to −12.2 %**, and swaps **+8.2 TWh of ST_GAS for −5.7 TWh of
CC_REGULAR** in 2023. Every "improvement" and "regression" measured against the
committed keeper's sidecars — including the charter's own baseline table — is
dominated by that drift.

| deliverable | status |
|---|---|
| P1 / S2 `nyiso_ordc_measured_step_span` | **built, committed, default-off.** A real construction defect (§1) — but **exactly inert** on the current keeper config (§3.2). |
| P2 `dual_fuel_oil_daily_parity` + NY Harbor ULSD daily intake | **built, committed, default-off.** A real granularity defect — but a **negative result** on the winter hypothesis (§2). |
| P3 / W1 `nyiso_iroquois_winter_spread` | **not exercised** — deliberately, see §4. |
| NYISO determination | **unchanged (NOT-YET).** No keeper promoted, no keeper shard edited. |

Runs registered: `2026-07-26-nyiso-76-ordc-span` (S2), `-77-ordc-span` (S2+P2),
`-78-oil-daily` (P2 alone), `-79-control` (both off, current main).

## 1. S2 — the ORDC measured-step-span defect is real, and quantified

With `nyiso_dynamic_reserve_requirements` on, each dynamic family's reserve
balance row enforces the MEASURED as-enforced requirement while its ORDC
shortfall-step widths were still built from the STATIC published MW. The
`_nyiso_design` docstring already claimed the steps "translate with the hourly
requirement"; the code did not.

Measured directly off the design (no solve needed —
`data/raw/NYISO-AS/requirements/`, weather-year 2023):

| family | measured req min/med/max MW | static width sum | hours req > width | mean forced real reserve |
|---|---|---|---|---|
| nyca_30min_total | 2620 / 2620 / 2620 | 2620 | 0 | 0 MW |
| nyca_10min_total | 1310 / 1310 / 1310 | 1310 | 0 | 0 MW |
| nyca_10min_spin | 655 / 655 / 655 | 655 | 0 | 0 MW |
| east_10min_total | 1200 / 1200 / 1200 | 1200 | 0 | 0 MW |
| **seny_30min_total** | **0 / 1800 / 1800** | **1300** | **6,061 of 8,760** | **325 MW (500 MW when binding)** |
| nyc_30min_total | 0 / 1000 / 1000 | 1000 | 0 | 0 MW |
| nyc_10min_total | 0 / 500 / 500 | 500 | 0 | 0 MW |

SENY (downstate, ⊃ NYC) is the sole affected family, and the defect is
arithmetic rather than a judgement call: with `Σwidths = 1300` and `RHS = 1800`,
the row `R + ΣS ≥ 1800` **cannot** be satisfied by shortfall alone, so the LP is
required to hold ≥500 MW of real downstate 30-min reserve in 69 % of hours —
while NYISO's published RCPF prices that product all the way down to zero
reserve. Any shortfall is then priced on a ramp ~38 % too steep (at a 500 MW
shortfall: $250/MWh on the static span vs $187.50 on the measured one).

The fix scales each dynamic family's published width vector by
`requirement[t] / requirement_static` into hourly `(n_steps, T)` widths. The
published RCPF penalties are requirement-INDEPENDENT
(`pen[k] = max_pen·(k+1)/n_ramp` for an n_ramp-step linear ramp, whatever the
span), so the widths alone carry the requirement and the curve's published shape
is preserved exactly; total step width equals the hour's requirement, which is
what keeps the balance row feasible at zero reserve. No new mechanism (rule 19),
no tuned value (rule 5).

**It is nevertheless inert today.** Control vs S2 arm is *identical* in every
class, every year, and every price statistic (§3.2). The reason is a rule-19
[R-ONE-MECH] overlap that has already been resolved from the supply side: the
original S2 probe (`docs/handoffs/nyiso-overrun-underrun-2026-07.md` §3: summer
+10.9 → +9.2, 36-mo MAE 4.33 → 4.22) was measured on keeper
`nyiso62_cc_hr_regate`, **before** `nyiso_scr_edrp_reserve_eligible` and
`nyiso_hydro_reserve_eligible` were added to the downstate reserve supply. Those
levers relieve the same SENY tightness, so the forced 500 MW is now met with
slack and costs nothing, and the SENY ORDC steps never set a price.

Per rule 1 [R-STRUCT] the fix stays in the codebase regardless: a demand curve
whose span contradicts its own balance row is wrong whatever it does to the fit,
and the defect would bite again the moment downstate reserve supply tightens
(a retirement, a deliverability limit, a colder year).

## 2. P2 — the daily oil-parity cap works, and refutes its own hypothesis

The dual-fuel cap prices a switch-capable gas unit at delivered oil parity, and
that parity is the measured EIA-923 Petroleum receipt — **monthly**, a flat
plateau across every day of the month — while the gas side of the same `min()`
is already daily. The overrun/underrun handoff proposed this as the winter root
cause: 120 of the 744 Jan-2025 hours clear on the flat cap, so the polar-vortex
peak cannot form.

Built as specified: a new intake
(`scripts/data/fetch_ny_harbor_distillate_daily.py` →
`data/raw/oil-prices/ny_harbor_ulsd_daily.csv`, 747 trading days 2023-2025) of
the EIA daily New York Harbor ULSD spot — the free daily benchmark for the exact
product a NY dual-fuel tank holds (NYSDEC 6 NYCRR Part 225-1 / ECL §19-0325 cap
NY distillate at 15 ppm sulfur) — shaped onto the monthly receipt by the same
trade-date staircase construction the gas daily shape uses. Mean preservation
holds per month **exactly** by construction (verified: per-month factor means are
1.0 to 1e-12 in all three years; annual mean unchanged), so the delivered LEVEL
stays the EIA-923 receipt — which alone carries transport, storage and
distributor margin that a FOB cargo quote does not — and only the within-month
profile moves.

The mechanism fires as designed: 320 gas tranches / 16.5 GW capped, and the
Jan-2025 polar-vortex days lift the cap **+5.8 %** while the mild first week
falls −5.1 %.

**And that is the whole size of it.** Control → P2 alone, the only live effect
this session produced:

| metric | control | P2 | actual |
|---|---|---|---|
| 2025 C3a mean | −12.2 % | −12.0 % | — |
| 2025 C3b NRMSE | 0.208 | 0.206 | gate 0.20 |
| 2025 p99 price | $165.0 | $169.1 | — |
| 2025 hours > $300 | 9 | 9 | 42 |
| Jan-2025 vs actual | −18.5 % | −17.4 % | — |

Distillate is a globally-traded commodity whose intra-month swing is only ±5 %;
it does not spike on a New York cold day the way Transco Z6 NY gas does
($97.9/MMBtu on 2025-01-17). **The flat oil-parity cap is not the winter root
cause** — the ~18 % Jan-2025 under-price is ~17 pp larger than the entire
granularity error it removes. The fix is correct and stays in (default-off);
this candidate is closed and future winter work should look elsewhere.

## 3. The drift finding — the committed keeper does not reproduce on `main`

### 3.1 The measurement

`2026-07-26-nyiso-79-control` is the keeper's own configuration
(`replay_keeper.py results/calibration/nyiso75_solar_shape`) replayed on current
`main` with both nyiso-76 flags **off**. It is the only valid baseline for this
lane; the committed keeper sidecars are not.

| metric | keeper (git af74927) | control (current main) |
|---|---|---|
| 2023 C3a mean | **+17.8 %** | **−0.9 %** |
| 2024 C3a mean | +1.2 % | **−9.1 %** |
| 2025 C3a mean | −3.2 % | **−12.2 %** |
| 2023 C3b NRMSE | 0.216 (FAIL) | 0.120 (pass) |
| 2024 C3b NRMSE | 0.176 (pass) | 0.196 (pass) |
| 2025 C3b NRMSE | 0.170 (pass) | **0.208 (FAIL)** |
| hours > $300 (model) 23/24/25 | 19 / 6 / 17 | 3 / 0 / 9 |
| 2023 ST_GAS TWh | 9.33 | **17.21** |
| 2023 CC_REGULAR TWh | 31.32 | **25.75** |
| C7 D-1 ST_GAS cv_ratio 23/24/25 | 0.542 / 0.658 / 0.606 (pass) | **0.439 / 0.489** (FAIL) / 0.547 |
| C8 D-2 ST_GAS forced share 23/24/25 | 31.4 % / 41.7 % / 28.2 % | **43.0 % / 53.8 % / 40.5 %** |

The dispatch move is a near-pure downstate substitution — ST_GAS up ~+900 MW in
8,414 of 8,760 hours in 2023, flat across every load quintile, with CC_REGULAR
falling to match and total generation unchanged (147.3 → 147.2 TWh). It is a
merit-order inversion, so it is forcing, not economics: the D-2
`reliability_floor` attribution on ST_GAS rises from 2.93 to 7.39 TWh.

### 3.2 What is NOT causing it

Control → S2 arm is **identical** in every class and year:

```
2023  control -> S2:  IDENTICAL
2024  control -> S2:  IDENTICAL
2025  control -> S2:  IDENTICAL
```

and identical in every price statistic (C3b 0.120/0.196/0.208, C3a
−0.9/−9.1/−12.2, p1/p50/p99, tail counts). Neither nyiso-76 fix contributes any
part of the drift. An earlier reading in this session attributed the ST_GAS/CC
swap and the C1/C7/C8 regressions to S2; the control refutes that, and the
attribution above supersedes it.

### 3.3 What is

Not isolated in this session — it needs a bisect, which is its own task. The
engine files touched between `af74927` and `main` are:

```
src/market_sim/config/constants.py
src/market_sim/config/fuel_trajectories.py
src/market_sim/config/scenarios.py
src/market_sim/data/cache_control.py
src/market_sim/data/fleet/__init__.py
src/market_sim/data/fleet/arrays.py
src/market_sim/data/fleet/offer_surfaces.py
src/market_sim/data/renewables.py
```

The signature — a downstate CC↔ST_GAS merit inversion at constant total energy,
with the `reliability_floor` binding 2.5× harder — points at the offer-surface /
fleet-array or floor-sizing side rather than the renewables side (solar and wind
energy each move < 0.15 TWh between the two runs, so the
`driver="netload"` reliability limbs are not being re-flagged by a VRE change).
`eb5326e` ("nyiso-75: close the solar flat-CF fallback finding") landed 30
minutes after the keeper's own commit and is the nearest NYISO-scoped suspect,
but it is not confirmed.

**This is the binding issue for NYISO, ahead of any price-formation lever.** The
keeper on the dashboard is not what the model now produces; until that is
reconciled, no NYISO calibration claim measured against it is safe, and neither
promoting nor rejecting a price-formation change can be scored honestly.

## 4. Disposition

- **S2 and P2 stay in the codebase**, both `GATED` and default-off, both
  byte-identical when off (default `cache_key` verified unchanged at
  `b3c4f0a6985cc683`; an armed run enters the key as a distinct scenario), both
  covered by new tests (7 for S2, 5 for P2; 408 tests green across the touched
  modules).
- **No keeper promotion, no keeper-shard edit, no attestation.** The lane cannot
  produce a defensible determination while §3 stands.
- **P3 / W1 (`nyiso_iroquois_winter_spread`) was deliberately not exercised.**
  Its documented value (winter −16.0 → −4.4) was measured against the same
  pre-drift baseline as S2's, and on current `main` the winter residual is a
  different quantity (2024 Dec −30.9 %, 2025 Jan −18.5 %, Jun −38.0 %). Running
  it now would produce another number attributable to nothing. It should be
  re-measured against a reconciled keeper.
- **Next task, in order:** (1) bisect `af74927..main` for the NYISO downstate
  CC→ST_GAS inversion; (2) re-solve and re-register the NYISO keeper on the
  reconciled code; (3) only then re-open the price-formation lane, where the
  first question is the `reliability_floor` sizing that now forces 40-54 % of
  ST_GAS (rule 23 [R-FROZEN-DERIVE] — it re-derives only when its source data
  changes, never against this residual).
- **Closed, do not re-chase:** the flat oil-parity cap as the winter root cause
  (§2), and the SENY ORDC over-fire as a live price lever (§1 — already relieved
  by the SCR/EDRP + hydro reserve-supply levers).

## 5. Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python numpy pandas pyarrow pydantic pyyaml scipy highspy
PYTHONPATH=$PWD:$PWD/src .venv/bin/python scripts/data/curate_capacity_deliverability.py
# control (both flags off, current main) — the valid baseline
PYTHONPATH=$PWD/src:$PWD .venv/bin/python scripts/replay_keeper.py \
    results/calibration/nyiso75_solar_shape \
    --set nyiso_ordc_measured_step_span=false --out-dir results/calibration/nyiso76_control
# the two fixes
... --set nyiso_ordc_measured_step_span=true  --out-dir results/calibration/nyiso76_ordc_span
... --set dual_fuel_oil_daily_parity=true     --out-dir results/calibration/nyiso76_oildaily
```
