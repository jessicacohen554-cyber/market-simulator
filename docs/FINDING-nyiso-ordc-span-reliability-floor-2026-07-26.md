# NYISO price formation (nyiso-76): two construction fixes, and the keeper-vs-main drift they uncovered

Session branch `claude/nyiso-price-formation-c3-v8x7ds`, 2026-07-26. Charter: the
nyiso-76 C3a/C3b/C3c price-formation lane. Baseline keeper
`2026-07-26-nyiso-75-solar-shape` (bundle `results/calibration/nyiso75_solar_shape`).
All arms solved in-session, 3 years / bundle (rule 16), scored on P1.

## 0. Headline

> **Naming.** The charter labelled its work items P1/P2/P3 by priority. Those
> labels are NOT used here: in this codebase `P0`/`P1`/`P2` are the solve
> passes, and `P2` is archived. **Every run in this lane is P1-only** —
> `passes=['P1']`, `commitment=False`, and the persisted dispatch carries P1
> rows exclusively in all five bundles. The lane's arms are named ORDC-SPAN,
> OIL-DAILY and WINTER-SPREAD throughout.

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
| ORDC-SPAN — `nyiso_ordc_measured_step_span` | **built, committed, default-off.** A real construction defect (§1) — but **exactly inert** on the current keeper config (§3.2). |
| OIL-DAILY — `dual_fuel_oil_daily_parity` + NY Harbor ULSD daily intake | **built, committed, default-off.** A real granularity defect — but a **negative result** on the winter hypothesis (§2). |
| WINTER-SPREAD — `nyiso_iroquois_winter_spread` | **not exercised** — deliberately, see §4. |
| NYISO determination | **unchanged (NOT-YET).** No keeper promoted, no keeper shard edited. |

Runs registered: `2026-07-26-nyiso-76-ordc-span` (ORDC-span alone),
`-77-ordc-span` (combined), `-78-oil-daily` (oil cap alone), `-79-control`
(both off, current main), `-80-old-outages` (the bisect).

## 1. ORDC-SPAN — the measured-step-span defect is real, and quantified

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

**It is nevertheless inert today.** Control vs the ORDC-span arm is *identical* in every
class, every year, and every price statistic (§3.2). The reason is a rule-19
[R-ONE-MECH] overlap that has already been resolved from the supply side: the
original probe (the arm that handoff calls "S2" —
`docs/handoffs/nyiso-overrun-underrun-2026-07.md` §3: summer
+10.9 → +9.2, 36-mo MAE 4.33 → 4.22) was measured on keeper
`nyiso62_cc_hr_regate`, **before** `nyiso_scr_edrp_reserve_eligible` and
`nyiso_hydro_reserve_eligible` were added to the downstate reserve supply. Those
levers relieve the same SENY tightness, so the forced 500 MW is now met with
slack and costs nothing, and the SENY ORDC steps never set a price.

Per rule 1 [R-STRUCT] the fix stays in the codebase regardless: a demand curve
whose span contradicts its own balance row is wrong whatever it does to the fit,
and the defect would bite again the moment downstate reserve supply tightens
(a retirement, a deliverability limit, a colder year).

## 2. OIL-DAILY — the daily oil-parity cap works, and refutes its own hypothesis

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

**And that is the whole size of it.** Control → the oil-daily arm, the only
live effect this session produced:

| metric | control | oil-daily | actual |
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

Control → the ORDC-span arm is **identical** in every class and year:

```
2023  control -> ordc-span:  IDENTICAL
2024  control -> ordc-span:  IDENTICAL
2025  control -> ordc-span:  IDENTICAL
```

and identical in every price statistic (C3b 0.120/0.196/0.208, C3a
−0.9/−9.1/−12.2, p1/p50/p99, tail counts). Neither nyiso-76 fix contributes any
part of the drift. An earlier reading in this session attributed the ST_GAS/CC
swap and the C1/C7/C8 regressions to the ORDC-span fix; the control refutes that, and the
attribution above supersedes it.

### 3.3 What is — ISOLATED, single file

`2026-07-26-nyiso-80-old-outages` is the keeper's config on current `main` with
**exactly one file reverted** — `data/raw/campd-unit-outages-NYISO.csv` restored
to its pre-`6a8f285` bytes (7,460 rows vs 4,423) — and everything else at HEAD.
It reproduces the de-designated keeper **to every digit**:

| metric | keeper | control (HEAD) | HEAD + old extract |
|---|---|---|---|
| C3a 2023 / 2024 / 2025 | +17.8 / +1.2 / −3.2 % | −0.9 / −9.1 / −12.2 % | **+17.8 / +1.2 / −3.2 %** |
| C3b 2023 / 2024 / 2025 | 0.216 / 0.176 / 0.170 | 0.120 / 0.196 / 0.208 | **0.216 / 0.176 / 0.170** |
| hours > $300 | 19 / 6 / 17 | 3 / 0 / 9 | **19 / 6 / 17** |
| D-1 ST_GAS cv_ratio | 0.542 / 0.658 / 0.606 | 0.439 / 0.489 / 0.547 | **0.542 / 0.658 / 0.606** |
| D-2 ST_GAS forced share | 31.4 / 41.7 / 28.2 % | 43.0 / 53.8 / 40.5 % | **31.4 / 41.7 / 28.2 %** |

**Commit `6a8f285` ("neiso-65: adopt guard-corrected CAMPD extracts, all six
ISOs + layup companions") is the sole and complete drift source.** Nothing else
in the 81 commits touches NYISO. No further bisect is needed.

### 3.4 The extract change is CORRECT — the defect is a coupling

`6a8f285` is not a regression to revert. The economic-layup charter
(`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`) established that
`filter_revealed_outages` was booking sustained economic layup as mechanical
outage, so every ISO booked **23–46 % of its CC capacity-year as outage against
a real EFOR + planned-maintenance norm of ~10–15 %**. The owner adopted the fix.
Under rule 14 [R-ACCURATE] the corrected extract **stays**.

What it exposed is a coupling in `model/interchange/core.py:154`:

```python
avail_cap = fleet_arrays.pmax[rows, np.newaxis] * fleet_arrays.availability[rows, :]
target = frac * avail_cap.sum(axis=0)
```

The reliability floor is sized as a fraction of **available** capacity. The
removed windows are overwhelmingly the class that moved — of the ≥5-day events
starting 2023-2025 that the guard reclassified:

| class | events removed | unit MW |
|---|---|---|
| **ST_GAS** | **787** | **55,810** |
| CC_REGULAR | 214 | 30,394 |
| CC_CHP | 131 | 6,222 |
| ST_CHP | 14 | 2,520 |

So un-deleting 55.8 GW of ST_GAS availability **mechanically inflated the
downstate steam floor's MW target**, with no change to any coefficient. That is
the whole causal chain: floor target up → ST_GAS forced up 8.2 TWh → CC_REGULAR
displaced 5.7 TWh at constant total energy → diurnal profile flattened (C7) →
forced-energy budget breached (C8) → marginal price down ~$5/MWh.

This is the textbook rule-14 signature, in CLAUDE.md's own words: *"If swapping
a hand estimate for real data makes the backcast worse, that is a signal that
something else in the model is miscalibrated and the estimate was silently
compensating for it."* The phantom outages were silently holding the floor down.

**This is the binding issue for NYISO, ahead of any price-formation lever.**

## 4. Disposition

- **Both fixes stay in the codebase**, both `GATED` and default-off, both
  byte-identical when off (default `cache_key` verified unchanged at
  `b3c4f0a6985cc683`; an armed run enters the key as a distinct scenario), both
  covered by new tests (7 for the ORDC span, 5 for the oil cap; 408 tests green
  across the touched
  modules).
- **No keeper promotion, no keeper-shard edit, no attestation.** The lane cannot
  produce a defensible determination while §3 stands.
- **WINTER-SPREAD (`nyiso_iroquois_winter_spread`) was deliberately not exercised.**
  Its documented value (winter −16.0 → −4.4) was measured against the same
  pre-drift baseline as the ORDC span's, and on current `main` the winter residual is a
  different quantity (2024 Dec −30.9 %, 2025 Jan −18.5 %, Jun −38.0 %). Running
  it now would produce another number attributable to nothing. It should be
  re-measured against a reconciled keeper.
- **NYISO keeper DE-DESIGNATED 2026-07-26** (owner instruction).
  `keepers/NYISO.json` carries no `keeper` key and records the reason;
  `status/NYISO.js` is deleted so the Calibration Status page drops the lane
  rather than rendering a scorecard the model can no longer produce. Verified
  CI-safe: the unscoped `build_status.py --check` and `audit_keepers.py --check`
  that `ci.yml` runs both exit 0 (5 keepers in sync, NYISO skipped).

### 4.1 The replacement path

The bisect is done (§3.3) and the extract stays (§3.4), so the replacement is a
**rule-23 [R-FROZEN-DERIVE] sanctioned re-derivation**: those coefficients are
frozen against *residuals*, but re-derive when their **source data** updates and
the commit cites the data change. The precedent is in the CSV itself — the live
NYC/LI ST_GAS rows read *"re-derived 2026-07-19 on the corrected
campd-unit-outages-NYISO.csv (1598→2641 rows; stale extract overstated the
availability denominator)"*. That extract has since changed again, in the
opposite direction, and the coefficients have not followed.

The live floors now over-forcing are:

| limb | floor_pct | note |
|---|---|---|
| NYC ST_GAS persistent 24 h base | **0.496** | `threshold = −50.0` — always on |
| NYC ST_GAS evening ramp (`NYC_ST_ev`, h14-21) | 0.533 → 1.0 | |
| Long_Island ST_GAS persistent 24 h base | **0.436** | `threshold = −50.0` — always on |
| Long_Island ST_GAS evening ramp (`LI_ST_ev`) | 0.572 → 0.815 | |

**Do NOT re-derive by running `scripts/data/derive_reliability_coeffs.py --iso
NYISO`.** Measured this session: a blind run is destructive. It emits 40 limbs /
8 enabled and **drops every curated limb** — both persistent 24 h bases, all
four ramp families (`NYC_ST_ev`, `LI_ST_ev`, `CH_ST_ev`, `NYC_CT_ev`), and the
`distribution` / `ramp_group` columns entirely — and it **re-enables the
`r1_disabled` NYC CT_PEAKER limb** that rule 17 permanently disabled (it came
back `r1_disabled=False, enabled=True`). The script predates the curated rows
and cannot regenerate them. The CSV was restored byte-identical after the test.

So the re-derivation must be either:
1. **extend the derive script** to emit the ramp-family and persistent-base
   limbs and to honour `R1_DISABLED_LIMBS` on output (core-infrastructure work,
   rule 27 — Opus/Fable only), or
2. **re-derive the four curated coefficients directly** against the corrected
   extract, reproducing the bespoke calculation the 2026-07-19 entry describes
   (*"when-available cool-day CF p25"* / *"avail cool-day evening p25"*), and
   record the new `threshold_basis` citing `6a8f285`.

Option 2 is the smaller, better-scoped change and matches how these rows were
last updated.

**Open design question to settle before re-deriving (owner call).** The two
persistent bases carry `threshold = −50.0` — an always-true gate, not a driver.
Under rule 17 [R-FLOOR-WINDOW] a floor needs a driver and a window; an
always-on floor has neither, and D-4 only passes it because its declared window
is all 24 hours. It may well be legitimate — NYC in-city must-run is a genuine
around-the-clock requirement (the nyiso-75 in-city must-run charter, PR #2916) —
but re-deriving its *level* does not answer whether an always-on reliability
floor should be sized off **available** capacity at all, when "available" now
includes economically-laid-up steam, which is precisely the capacity that is
*not* reliability-committed. An `installed`-based (or layup-netted) base is the
alternative. Decide this deliberately rather than inheriting it.

### 4.2 Then

- Re-solve 2023-2025 in ONE bundle (rule 16) with `dual_fuel_oil_daily_parity`
  armed — the one genuine improvement this lane produced.
- Score C1 / C7 / C8. If the floor is what flattened ST_GAS, D-1 `cv_ratio`
  should recover and the D-2 forced share fall back toward the 30 % budget.
- Build the attestation + DOF ledger (rule 20 — union with the prior keeper's
  curated entries; a blind `build_dof_ledger.py` rebuild drops 9 of them), then
  promote as the replacement keeper.
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
