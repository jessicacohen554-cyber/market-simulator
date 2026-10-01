# FINDING — capx D77: the CCS retrofit emission-rate seam, reproduced, repaired, and screened

**Lane:** capx D77 · **Branch:** `claude/capx-d77-ccs-emission-rate-seam-pvfezi` (fresh off
`origin/main` `2fa2f23a`) · **Date:** 2026-09-06 · **Model:** `claude-opus-5` (rule 27 `[R-PUSH]`)
**Data profile:** `neiso` · **PRECOMMIT:** `docs/handoffs/PRECOMMIT-capx-d77-2026-09-06.md`
(pushed at `ae8dd2a0`, **before** either solve)
**Charter:** pack §D77 + `FINDING-scn-ws2b-2026-09-06.md` §5.3 / §8 item 1 +
`FINDING-capx-d50-2026-09-04.md` / `FINDING-capx-d65-2026-09-05.md`

---

## 0. Bottom line

**WS2b's leading candidate is the mechanism, confirmed at zero LP, and the repair holds.** The
overwrite is `data/fleet/campd_bins.py::apply_plant_emission_rates_v2`, reached from
`build_dispatch_fleet` — which `runner.py` calls at line **2479, after `evolve_fleet` at 2237**, in
every forecast year. `fuel_class("gas_cc_ccs") == "gas"`, so a converted unit still matches its own
host plant's measured **gas** row and is assigned its uncaptured rate. It is **not** a stale cache:
on the CAMPD path `build_dispatch_fleet` opens `dispatch_fleet = fleet + inline_imports` — a
concatenation, not a copy — so the override corrupts the **persistent** generators, which is why
WS2b saw 0.3745 again in 2029 and 2030 and why the next year's retirement and CCS screens read it
too.

**The screen PASSES every structural STOP gate, and the correction is large.** On a same-HEAD
one-field A/B of `neiso-t1f` 2026–2030 (both legs 5/5 years, 14 invariants scored, **0 FAIL /
0 WARN**):

| year | CO2 arm | CO2 control | **Δ** | CCS TWh arm | CCS TWh ctl | Δ |
|---|---|---|---|---|---|---|
| 2026 | 15.8319 | 15.8319 | **0.0000** | 0.000 | 0.000 | 0.000 |
| 2027 | 17.0960 | 17.0960 | **0.0000** | 0.000 | 0.000 | 0.000 |
| 2028 | 12.9276 | 15.8562 | **−2.9286 (−18.5 %)** | 10.386 | 1.719 | +8.667 |
| 2029 | 6.7954 | 14.0210 | **−7.2256 (−51.5 %)** | 25.363 | 8.549 | +16.814 |
| 2030 | 6.9545 | 13.3680 | **−6.4135 (−48.0 %)** | 20.454 | 16.717 | +3.737 |

2026 and 2027 are identical **to four decimals in every reported row**, which is the pre-2028
inertness measured rather than argued. From 2028 the converted fleet carries
**0.0443–0.0503 t/MWh** against the control's uncaptured ~0.44.

**The simulated repair is LARGER than WS2b's fixed-dispatch arithmetic, and for the reason WS2b
named.** WS2b's §5.4 recomputation was explicitly an upper bound on *mis-attribution* at frozen
dispatch. Here dispatch also moves: NEISO carries an RGGI price, so a correctly-rated CCS unit pays
one tenth of the carbon adder and the LP re-orders. Gas CC falls 13.75 → 11.73 TWh, gas CT
1.83 → 1.41, biomass 8.35 → 8.23, imports 32.84 → 31.57, and load-weighted price falls
$67.67 → $57.30 at 2030.

**One pre-registered gate reads FAIL as literally written and the diagnosis is unambiguous: it is
the retrofit SET moving, which the PRECOMMIT pre-declared is NOT a STOP.** Details in §4.

---

## 1. Phase 0 — the premise, reproduced with ZERO LP

Three measurements, each independently sufficient:

1. **`fuel_class("gas_cc")` and `fuel_class("gas_cc_ccs")` both return `"gas"`.** Conversion does
   not escape the restoration's match key.
2. **The map's value IS WS2b's number.** The NEISO 2028 forecast-mode v2 map carries 69
   `(plant, class)` rows, 45 gas; the plant closest to WS2b's 0.3745 is **plant_code 55041 at
   0.3745 t/MWh**. WS2b's "0.3745 → 0.3745" is the measured host rate being re-booked, to four
   decimals — and plant 55041 is in the 2028 retrofit cohort of both legs of this session's screen
   (`CC_REGULAR_Central_p55041_econ`).
3. **Driving a post-retrofit unit through the function reproduces the defect exactly.** A
   generator carrying `fuel_type="gas_cc_ccs"`, `heat_rate=8.4113`, `emission_rate_co2=0.0375`
   comes out at **0.3745 — 10.0× its intended rate**. An unabated sibling at the same plant is
   unchanged, so the function is correct for everything except a converted unit.

### 1.1 The quoted overwrite

```python
# src/market_sim/data/fleet/campd_bins.py :: apply_plant_emission_rates_v2   (pre-fix)
for gen in generators:
    triple = rates.get((int(gen.plant_code), fuel_class(gen.fuel_type)))
    if triple is None:
        continue
    co2, nox, so2 = triple
    touched = False
    if co2 > 0.0:
        gen.emission_rate_co2 = co2        # <-- restores the UNCAPTURED host rate
```

`apply_plant_emission_rates` (the v1 branch, keyed on `plant_code` alone) carries the identical
line and the identical defect.

**Why two of `ccs.py`'s three writes survived and one did not:** this function writes CO2, NOx and
SO2 only. `heat_rate` and `fuel_type` are never touched by it, so they persist; `emission_rate_co2`
is assigned unconditionally.

**Why the rate did not follow the 12 % heat-rate rise** (WS2b's open question): the forward-year
rate is a **plant-keyed CAMPD measurement**, not a recomputation from the model's heat rate. No
heat-rate linkage exists on this path, for an abated or an unabated unit alike. WS2b was right that
a *re-derived* rate would have risen and right to read the flat 0.3745 as evidence of a
restoration rather than a recomputation.

### 1.2 Semantics the repair preserves (rule 13 `[R-MEASURED]`)

The forward-year rate for an existing unit is the multi-year CAMPD-derived measured rate — an
admissible measured input. The measured quantity is the **host stack's** intensity, so a unit with
a capture island emits `measured_host_rate × (1 − capture)`: the measured input still enters, every
year, and the capture applies on top. A converted unit is never silently returned to its
uncaptured rate.

## 2. Phase 1 — the fix

**Route: apply the capture where the measured rate is restored.** The alternative — exempt
converted units from restoration — was enumerated and **rejected on structure, not on any
residual**: (a) the same override books **NOx and SO2**, and a capture retrofit does not zero a
unit's NOx/SO2 measurement, so an exemption would silently freeze both (and, under
`control_retrofit_forward`, drop announced SCR/FGD stepping); (b) it freezes the CO2 basis at the
retrofit year, so a lane whose estimator basis moves per year (the hindcast `as_of_year` bound)
drifts away from the measured input — the opposite of rule 13; (c) it puts the capture in one file
and the exemption in another, which must then agree (rule 19 `[R-ONE-MECH]`).

**Mechanism:** one `Generator` attribute, `ccs_capture_fraction: float = 0.0` — a physical property
of the unit, **not** a `ScenarioConfig` field and not a tunable (rule 24 `[R-REGISTRY]`). Stamped
where a capture island comes into existence (`ccs.py::apply_ccs_retrofit` ←
`config.ccs_retrofit_capture_rate`; `new_entry.py`'s CCS build ← `config.ccs_capture_rate`), read
where a measured host rate is booked, in both override functions:

```python
gen.emission_rate_co2 = co2 * (1.0 - float(gen.ccs_capture_fraction))
```

**Zero DOF (rule 21 `[R-DOF]`):** the value is always one of two already-registered `ScenarioConfig`
fields; nothing is chosen, nothing is swept, no residual can be closed by it. **No new
`ScenarioConfig` field ⇒ no gate, no default, no matrix row** (rule 28 duty (c) not engaged).
NOx/SO2 are deliberately **not** scaled — the model carries no capture co-benefit parameter and
inventing one would be a new free parameter.

Diff: `data/fleet/__init__.py` (+25), `model/capacity_evolution/ccs.py` (+16),
`model/capacity_evolution/new_entry.py` (+9), `data/fleet/campd_bins.py` (+33 incl. docstrings),
`results/cache.py` (+58, the epoch entry). All five blobs byte-verified against local after push
(rule 27): line counts and hashes MATCH.

### 2.1 Tests

`tests/unit/model/test_ccs_retrofit_rate_seam.py` — **10 cases, all passing**: the WS2b table as a
seam test (a unit's rate across its own retrofit year, *through* the restoration); the three
untouched writes; an explicit pin that the rate does **not** follow the heat-rate rise, with the
reason, so nobody "repairs" it into a new DOF; a non-cohort control; idempotence across 2029/2030;
NOx/SO2 unscaled; the v1 branch; and the unabated-fleet no-op.

Also passing, run before the screen: `tests/regression/test_persisted_identity.py`,
`test_fleet_arrays_golden.py`, `test_45u_backcast_inertness.py`, `test_fleet_unification.py`,
`test_fleet_facade.py` (34), plus `tests/unit/model/test_ccs_retrofit.py`,
`tests/unit/data/test_campd_bins.py`, `tests/unit/pipeline/test_runner.py`,
`tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py` (150).

**Backcast / hindcast / crossover byte-identity is asserted, not argued**: `apply_ccs_retrofit`
returns at `if year < config.ccs_retrofit_available_year`, so `ccs_capture_fraction` is 0.0 on
every generator and `co2 * (1.0 - 0.0)` is the pre-fix expression. The screen's own 2026 and 2027
rows are the empirical confirmation (identical to four decimals).

### 2.2 Deliberately NOT changed — routed

`ccs.py` computes the residual as `old_er × (1 − capture)` and the captured tonnage as
`old_er × capture`, both off the **unpenalized** rate, while the retrofit raises the heat rate 12 %.
Physically the parasitic load raises gross stack CO2 per **net** MWh, so the residual would be
`old_er × (1 + pen) × (1 − capture)` — roughly 12 % higher than what ships. Correcting it would
move the §45Q credit and the transport cost and therefore the retrofit set, so it is a **separate,
second-order defect** and is out of this fix's scope. This repair makes the dispatch fleet agree
with `ccs.py`'s stated semantics and nothing more. **Routed to the director (§8 item 2).**

## 3. Cache: BEHAVIOUR MOVES, NO KEY MOVES

Measured on the same tree with only `src/market_sim` stashed — **every key identical pre- and
post-fix**: default `e5ecd4105ada3e58`, bare backcast `6a2845e50951394e`, and the bare per-ISO
2026–2030 forecast keys ERCOT `78b01278f2eb64eb`, CAISO `41367ccc55859d4c`, PJM `577a950add853227`,
MISO `a6b9ed663987311b`, NYISO `81af4882eeda50f5`, NEISO `f1b2dc5e9f2a47e3`. Both legs of this
session's screen hashed to the same key `18515067bf4d2fbe`; the two `--out-dir` roots are the only
isolation.

This is the same-key invalidation class in its pure form and the 2026-08-31 epoch entry's predicted
recurrence: a pre-fix bundle whose horizon reaches 2028 sits at **exactly** the key a post-fix run
computes. Epoch entry added to `src/market_sim/results/cache.py` ("Epoch 2026-09-06b"), with the
invalidated set (§8 census) and the not-invalidated set (every backcast; every horizon ending
before 2028). The PRECOMMIT §3 pre-declared the affected bare keys **before** either solve.

## 4. Phase 2 — the screen (rule 29 `[R-SCREEN]`)

**One leg plus its control**, NEISO `t1f` 2026–2030 — the span where the mechanism's own measured
footprint is largest (the 3 GW/yr ISO cap binding in 2028–2030). Screen year named in the PRECOMMIT
on **footprint**, never on residual.

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-d77/<arm>
```

| leg | tree | cache key | wall | peak RSS | years | invariants |
|---|---|---|---|---|---|---|
| control | `origin/main` `2fa2f23a` = branch HEAD **minus exactly this session's one commit** | `18515067bf4d2fbe` | 7.3 min | 3.26 GB | 5/5 | 0 FAIL / 0 WARN (14) |
| arm | branch HEAD `ae8dd2a0` | `18515067bf4d2fbe` | 7.0 min | 3.29 GB | 5/5 | 0 FAIL / 0 WARN (14) |

**HEAD GUARD held on both legs** (`H1 == H0 == ae8dd2a0…`, `rc=0`).

### 4.1 G-DRIFT — form 4 VOID for the t1f lane, and the same-HEAD control proved BOTH verdicts

The charter predicted "form 4 VOID and a same-HEAD control, which is the honest comparison anyway".
It was right, and the audit resolved into **two** windows with **opposite** answers, both then
confirmed empirically at zero extra cost:

- **Against the t1f control `ff-t1f-d65-ctl/neiso` (sha `43b3a737`, same key `18515067bf4d2fbe`) —
  form 4 VOID.** `git diff 43b3a737 HEAD` over the rule-29 window is 48 files / +5,687 lines,
  including `policy/carbon.py` (+215, the S2 carbon **floor**, which is live on RGGI NEISO),
  `policy/cap_and_trade.py`, `model/capacity_evolution/retirements.py` (+194),
  `data/outages.py`, `data/cod_ramp.py`. **Confirmed:** that bundle reads 2975/5897/8803 MW and
  1.1/8.3/17.1 TWh; my same-HEAD control reads 2984/5896/8833 MW and 1.719/8.549/16.717 TWh.
  Two bundles, one key, different answers.
- **Against the newest bare NEISO run
  `results/scn-campaign-load-2026-09-06/NEISO/REF` (sha `29b1c757`) — form 4 VALID.** Its window to
  HEAD is ten files, every hunk classified INERT with its reason (PRECOMMIT §4a): the P1 basis seed
  is gated on `xyear_warmstart is None` and the forecast passes an explicit bool
  (`runner.py:3551`), so it can never arm on this path; the `malloc_trim` removal is RSS-only; the
  new `nyiso_ct_peaker_bands_measured` field hard-errors outside NYISO and is default-off;
  `backcast_config.py` is never entered by a `mode="forecast"` run; the rest is diagnostics or
  backcast CLIs `run_full_horizon.py` does not import. **Confirmed:** my same-HEAD control
  reproduces that bundle's CO2 trajectory **exactly** — 15.8319 / 17.0960 / 15.8562 / 14.0210 /
  13.3680 against the sidecar's 15.83 / 17.10 / 15.86 / 14.02 / 13.37, and CCS MW 2984 / 5896 /
  8833 on both — *across a different `forecast_xyear_warmstart` posture and therefore a different
  cache key*, which is what a warm start is supposed to do (path, not optimum).

So the code audit was right in both directions. Spending the control was the right call and it
turned G-DRIFT from an argument into a measurement.

### 4.2 STOP gates — result

| # | gate | result |
|---|---|---|
| 1 | **identity** — every converted unit `= measured host × (1 − 0.90)` to 1e-9 | **PASS** every year (12 units 2028, 23 in 2029, 24 in 2030) |
| 2 | **the other three writes byte-identical to the control** | **FAIL as literally written** — 4 units 2029, 9 units 2030. **Diagnosed below.** |
| 3 | **confinement** — no unit outside the cohort moves its rate | **PASS** every year |
| 4 | **retrofit MW in the D50/D65 band** | 2028 **identical** (2984.4 both); 2029 +87.8 MW; 2030 **−2184.6 MW**. Pre-declared **NOT a STOP** |
| 5 | **no collateral** — zero-carbon rows identical | **PASS** — nuclear 26.482, hydro 6.974, wind 6.281, solar 5.768 identical to the digit in every year |
| 6 | **no invariant regression** | **PASS** — 0 FAIL / 0 WARN, 14 scored, both legs |

**Gate 2, diagnosed — it is gate 4 in disguise, not a defect.** Every one of the 13 differing units
is a **cohort-membership** difference: a unit that retrofits in one leg and not the other. In all 13
the heat-rate ratio is **exactly ×1.12 or ×(1/1.12) to nine decimals** — the retrofit penalty
applied or not applied, nothing else — and the fuel-type pair is always exactly
`{gas_cc, gas_cc_ccs}`. **Zero units differ for any other reason.** Re-measured the honest way —
**conditioned on units whose retrofit status is the same in both legs** — gate 2 is a clean PASS in
every year, including all 24 converted units at 2030:

| year | units sharing retrofit status | of which converted | heat-rate diffs |
|---|---|---|---|
| 2026 | 646 | 0 | **0** |
| 2027 | 409 | 0 | **0** |
| 2028 | 409 | 12 | **0** |
| 2029 | 403 | 21 | **0** |
| 2030 | 399 | 24 | **0** |

This refinement was made **after** seeing the result and is flagged as such. The literal gate as
written could only have passed if the retrofit set were frozen, which the PRECOMMIT's own gate 4
said it would not be; the conditioned form tests what gate 2 was for — that the fix does not touch
the heat-rate / VOM / fuel-type paths. VOM is not carried in `FleetContext`, so it rests on the
code (the diff touches no VOM statement) and on the seam test's explicit assertion.

### 4.3 Why the 2030 retrofit set shrinks, stated as a mechanism

2028 is identical (2984.4 MW both legs, the cap binding). From 2029 the sets diverge, and by 2030
the arm retrofits **664 MW against the control's 2937 MW**. The retrofit screen values the uplift
against **the prior year's hourly price signal**. With correctly-rated CCS running near-baseload,
2029's load-weighted price is $53.78 in the arm against $60.43 in the control — 11 % lower — so
fewer residual hosts clear the payback hurdle in 2030. **The repair is self-limiting: cheap abated
CC depresses the energy price that justifies the next retrofit.** That is a real economic response
to a corrected marginal cost, not an artifact — and it is exactly the merit-order re-ordering the
PRECOMMIT pre-declared would not be a STOP. Capacity trajectory is otherwise unmoved: reserve
margin, retirements, thermal / renewable / storage builds are **identical in every year**.

## 5. Full screen tables

arm  key 18515067bf4d2fbe  wall 421.7s  RSS 3294MB
ctl  key 18515067bf4d2fbe  wall 439.6s  RSS 3261MB

| year | CO2 arm | CO2 ctl | Δ Mt | Δ % | CCS TWh arm | CCS TWh ctl | Δ | CCS MW arm | CCS MW ctl | Δ | LW $ arm | LW $ ctl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 15.8319 | 15.8319 | **+0.0000** | +0.0% | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 | +0.0 | 51.89 | 51.89 |
| 2027 | 17.0960 | 17.0960 | **+0.0000** | +0.0% | 0.000 | 0.000 | +0.000 | 0.0 | 0.0 | +0.0 | 51.40 | 51.40 |
| 2028 | 12.9276 | 15.8562 | **-2.9286** | -18.5% | 10.386 | 1.719 | +8.667 | 2984.4 | 2984.4 | +0.0 | 51.97 | 55.66 |
| 2029 | 6.7954 | 14.0210 | **-7.2256** | -51.5% | 25.363 | 8.549 | +16.814 | 5984.2 | 5896.4 | +87.8 | 53.78 | 60.43 |
| 2030 | 6.9545 | 13.3680 | **-6.4135** | -48.0% | 20.454 | 16.717 | +3.737 | 6648.3 | 8832.9 | -2184.6 | 57.30 | 67.67 |

Other headline rows (arm vs control):

- **2028** reserve margin 0.0394 vs 0.0394; max hourly $283.6 vs $283.6; retire 0 vs 0 MW; builds thermal 0 vs 0 MW; renew 0 vs 0 MW; storage 0 vs 0 MW
- **2029** reserve margin 0.0440 vs 0.0440; max hourly $284.9 vs $284.9; retire 2 vs 2 MW; builds thermal 0 vs 0 MW; renew 1802 vs 1802 MW; storage 0 vs 0 MW
- **2030** reserve margin 0.0840 vs 0.0840; max hourly $84.9 vs $87.3; retire 0 vs 0 MW; builds thermal 1000 vs 1000 MW; renew 1198 vs 1198 MW; storage 0 vs 0 MW

2028/2029/2030 generation by fuel (TWh, arm vs control):

| fuel | 2028 arm | 2028 ctl | 2029 arm | 2029 ctl | 2030 arm | 2030 ctl |
|---|---|---|---|---|---|---|
| biomass | 7.379 | 7.728 | 7.922 | 8.321 | 8.232 | 8.351 |
| gas_cc | 29.104 | 35.777 | 10.464 | 23.567 | 11.725 | 13.752 |
| gas_cc_ccs | 10.386 | 1.719 | 25.363 | 8.549 | 20.454 | 16.717 |
| gas_ct | 1.559 | 1.808 | 1.512 | 1.845 | 1.405 | 1.831 |
| gas_st | 0.464 | 0.464 | 0.463 | 0.464 | 0.459 | 0.462 |
| hydro | 6.974 | 6.974 | 6.974 | 6.974 | 6.974 | 6.974 |
| import | 28.346 | 29.794 | 29.145 | 32.152 | 31.567 | 32.835 |
| nuclear | 26.482 | 26.482 | 26.482 | 26.482 | 26.482 | 26.482 |
| oil | 0.003 | 0.003 | 0.002 | 0.002 | 0.000 | 0.000 |
| solar | 3.252 | 3.252 | 4.622 | 4.622 | 5.768 | 5.768 |
| wind | 3.664 | 3.664 | 5.529 | 5.529 | 6.281 | 6.281 |

## 6. What the WS2b arithmetic looks like against a measured repair

WS2b §5.4 recomputed NEISO 2030 BAU CO2 as 14.887 → 9.128 Mt at **fixed dispatch**, and said
plainly that this was an upper bound on mis-attribution rather than a prediction of the repaired
run. Both halves of that caution were right, and one of them for a reason WS2b could not have seen:

1. **The dispatch response is real and it is large**, so the simulated repair exceeds the frozen
   arithmetic: −6.41 Mt on the 2030 control here, with 3.7 TWh of CCS generation displacing gas CC,
   gas CT, biomass and imports.
2. **WS2b's own baseline has since moved.** Its BAU (sha `0c349d2f`) and the newest bare NEISO run
   (sha `29b1c757`) share cache key `5e2c52ea81694c10` and disagree by up to **1.52 Mt/yr**
   (§7). WS2b's 14.887 is not the current baseline; this session's control reads 13.368.

So the *direction* and *order of magnitude* of WS2b's §5.4 correction reproduce, its qualitative
conclusion (the seam decides the sign of NEISO's headline CO2 answer under CES) stands, and its
specific numbers need re-basing before quoting.

## 7. Disclosed because it was found, not because it is this lane's to fix

**Two committed bare-NEISO bundles at the SAME cache key, solved at different shas, disagree.**
`results/scn-ws2-ladder/neiso/BAU` (`0c349d2f`) and
`results/scn-campaign-load-2026-09-06/NEISO/REF` (`29b1c757`) both carry key `5e2c52ea81694c10`
and identical resolved configs (the only three field differences are new fields absent from the
older record, all at neutral defaults). Their CO2 trajectories:

| year | WS2b BAU | campaign REF | Δ |
|---|---|---|---|
| 2026 | 16.3081 | 15.83 | 0.478 |
| 2027 | 17.7888 | 17.10 | 0.689 |
| 2028 | 16.9614 | 15.86 | 1.101 |
| 2029 | 15.3855 | 14.02 | 1.366 |
| 2030 | 14.8871 | 13.37 | **1.517** |

Prices and reserve margins move too. The `0c349d2f → 29b1c757` window carries `policy/carbon.py`
(+215, the S2 floor), `policy/cap_and_trade.py`, `retirements.py`, `campd_bins.py` and `eia860.py`,
none of which moves a key. **The cache key does not identify a solve across code changes** — which
is the general form of the hazard D77's own fix creates and the epoch ledger exists to record.
Routed, not acted on.

## 8. BLAST RADIUS — for D65-B's batch and the director's re-score card, as a table, not an act

### 8.1 Committed forecast bundles carrying a CCS retrofit ledger

**45 committed forecast bundles carry a non-empty CCS retrofit ledger.**

| ISO | bundle | span | cache key | peak CCS MW | 2030 CCS MW | 2030 CCS TWh | 2030 CO2 Mt |
|---|---|---|---|---|---|---|---|
| CAISO | `ff-t1f-d46/caiso` | 2026-2030 | `772b1e5abc7fc80c` | 8852 | 8852 | 45.0 | 25.81 |
| CAISO | `ff-t1f-d60/caiso` | 2026-2030 | `29f8eb372810195f` | 8622 | 8622 | 43.1 | 28.52 |
| ERCOT | `scn-ws2-ladder/ercot/CES-20` | 2026-2030 | `075e6aa30813f061` | 8957 | 8957 | 66.8 | 257.68 |
| ERCOT | `scn-ws2-ladder/ercot/CES-40` | 2026-2030 | `383509581661faba` | 8956 | 8956 | 67.3 | 257.64 |
| ERCOT | `ff-t1f-d46/ercot` | 2026-2030 | `873d8c0e6cab52ae` | 2742 | 2742 | 16.0 | 285.04 |
| MISO | `ff-t1f-s123/verify` | 2026-2030 | `587dc5b32ba71ceb` | 8992 | 8992 | n/r | 387.41 |
| MISO | `ff-t1f-d45r/miso` | 2026-2030 | `8d8bc63a0d4378a9` | 4631 | 4631 | 17.8 | 345.28 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon_plus25` | 2026-2050 | `7784d408fc955785` | 15251 | 8994 | n/r | 14.34 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31` | 2026-2050 | `a4b11ef4aaa1be35` | 15049 | 8997 | n/r | 14.68 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/base` | 2026-2050 | `0365174ab16cc318` | 15049 | 8997 | n/r | 14.68 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gaspm5` | 2026-2050 | `1de43201e2040f7f` | 15009 | 8997 | n/r | 14.65 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gasup150` | 2026-2050 | `13f9357712250600` | 14743 | 8982 | n/r | 14.58 |
| NEISO | `ff-t3-neiso-golden/bau/fc6/arms/carbon_plus25` | 2026-2050 | `f7cced798488ddac` | 13317 | 8998 | 23.0 | 14.60 |
| NEISO | `ff-t3-neiso-golden/bau` | 2026-2050 | `706e7ba8e6582d42` | 13135 | 8998 | 23.1 | 14.88 |
| NEISO | `ff-t3-neiso-golden/bau/fc6/arms/base` | 2026-2050 | `706e7ba8e6582d42` | 13135 | 8998 | 23.1 | 14.88 |
| NEISO | `ff-t3-neiso-golden/bau/fc6/arms/gaspm5` | 2026-2050 | `2d017ed9675aa386` | 13114 | 8987 | 23.1 | 14.88 |
| NEISO | `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon25` | 2026-2050 | `7924eccc695c0168` | 11484 | 8997 | n/r | 14.87 |
| NEISO | `ff-t3-neiso-golden/bau/fc6/arms/gasup150` | 2026-2050 | `65662ca117959ee5` | 11475 | 8903 | 23.7 | 14.89 |
| NEISO | `ff-t3-neiso-golden/bau-d46/fc6/arms/carbon_plus25` | 2026-2050 | `56019f3b0850e9f9` | 11419 | 8983 | 17.9 | 14.36 |
| NEISO | `ff-t3-neiso-golden/bau-d46` | 2026-2050 | `67678e58b2d0526c` | 11209 | 8943 | 18.3 | 14.71 |
| NEISO | `ff-t3-neiso-golden/bau-d46/fc6/arms/base` | 2026-2050 | `67678e58b2d0526c` | 11209 | 8943 | 18.3 | 14.71 |
| NEISO | `ff-t3-neiso-golden/bau-d46/fc6/arms/gaspm5` | 2026-2050 | `e84079053b581a9e` | 11181 | 8914 | 18.3 | 14.68 |
| NEISO | `ff-t3-neiso-golden/bau-d60` | 2026-2050 | `f04fd06348e1623d` | 9310 | 8833 | 16.7 | 13.37 |
| NEISO | `ff-t1f-s4hydro/neiso-control` | 2026-2030 | `9a7f68fc7dcac931` | 8997 | 8997 | n/r | 14.70 |
| NEISO | `scn-ws2-ladder/neiso/CES-40` | 2026-2030 | `7d36e0b517ffb0e3` | 8997 | 8997 | 59.7 | 24.88 |
| NEISO | `scn-ws2-ladder/neiso/CES-20` | 2026-2030 | `43b921da2f0bcfc7` | 8993 | 8993 | 32.8 | 16.50 |
| NEISO | `ff-t1f-s4hydro/neiso` | 2026-2030 | `9a7f68fc7dcac931` | 8980 | 8980 | n/r | 14.72 |
| NEISO | `ff-t1f-d50/neiso` | 2026-2030 | `18515067bf4d2fbe` | 8962 | 8962 | 19.2 | 14.98 |
| NEISO | `scn-ws4-probe-t1f/neiso/REF` | 2026-2030 | `77b56ef19cb7200e` | 8957 | 8957 | 16.5 | 12.16 |
| NEISO | `scn-ws4-probe-t1f/neiso/LOAD-HI` | 2026-2030 | `6e364efaa728fc92` | 8957 | 8957 | 20.0 | 14.71 |
| NEISO | `ff-t1f-d46/neiso` | 2026-2030 | `6690e4d6d66bc819` | 8943 | 8943 | 18.3 | 14.71 |
| NEISO | `scn-campaign-load-2026-09-06/NEISO/REF` | 2026-2030 | `5e2c52ea81694c10` | 8833 | 8833 | 16.7 | 13.37 |
| NEISO | `ff-t1f-d65-a1/neiso` | 2026-2030 | `8ebed20ae90ec0e7` | 8827 | 8827 | 17.4 | 14.81 |
| NEISO | `scn-campaign-load-2026-09-06/NEISO/LOAD-HI` | 2026-2030 | `8e603f9d81b73da7` | 8803 | 8803 | 16.9 | 14.78 |
| NEISO | `scn-ws2-ladder/neiso/BAU` | 2026-2030 | `5e2c52ea81694c10` | 8803 | 8803 | 17.1 | 14.89 |
| NEISO | `ff-t1f-d65-ctl/neiso` | 2026-2030 | `18515067bf4d2fbe` | 8803 | 8803 | 17.1 | 14.89 |
| NEISO | `ff-t3-neiso-golden/bau-d46/fc6/arms/gasup150` | 2026-2050 | `96984c538320d6d6` | 6681 | 5681 | 6.2 | 14.38 |
| NYISO | `ff-t1f-d45r/nyiso` | 2026-2030 | `cc7d1050a8090c76` | 8971 | 8971 | 38.4 | 17.96 |
| NYISO | `scn-campaign-load-2026-09-06/NYISO/LOAD-HI` | 2026-2030 | `470338150a2f85a0` | 6621 | 6621 | 30.2 | 26.23 |
| NYISO | `scn-campaign-load-2026-09-06/NYISO/REF` | 2026-2030 | `aed447f88457dff7` | 6475 | 6475 | 24.4 | 20.89 |
| NYISO | `ff-t1f-d60/nyiso` | 2026-2030 | `19a9690bb12c8459` | 6475 | 6475 | 24.7 | 20.98 |
| PJM | `ff-t1f-s6-pjm/ledger` | 2026-2030 | `31a19d815fa319a7` | 8995 | 8995 | n/r | 387.58 |
| PJM | `ff-t1f-d45r/pjm` | 2026-2030 | `321f04e9060787f0` | 3585 | 3585 | 4.5 | 381.68 |
| PJM | `ff-t1f-d50/pjm` | 2026-2030 | `167e65187f32056b` | 910 | 910 | 1.1 | 383.52 |
| PJM | `ff-t1f-d60/pjm` | 2026-2030 | `09996eca71ee80fd` | 910 | 910 | 3.5 | 470.46 |

`n/r` = the bundle's summary schema predates per-fuel generation (`generation_by_fuel_mwh` empty): 10 of 45 bundles. Capacity is recorded in all of them and is the reliable signal; **`n/r` never means zero**.

Per ISO: CAISO 2, ERCOT 3, MISO 2, NEISO 30, NYISO 4, PJM 4

**Every one of these is at an unmoved cache key**, so a post-fix run of the same config will
CACHE-HIT the pre-fix bundle unless it is purged or re-solved. Purge-or-re-solve is D65-B's batch,
at one HEAD, carrying this fix. **D77 re-solved none of them.**

Direction of the correction, from this session's measurement: **CO2 falls** on every bundle that
dispatches a retrofitted unit, by roughly the CCS generation × the host rate × 0.9, plus a
second-order dispatch shift toward the now-cheaper abated fleet. In an ISO with a carbon price
(NEISO, NYISO, CAISO under CARB) the dispatch shift is large; in ERCOT/MISO (carbon 0 in these
bundles) the accounting correction still applies but the merit order barely moves, because the
mis-rated `emission_rate_co2` reaches marginal cost only through the carbon adder.

### 8.2 Which FF-2D verdict rows are mis-stated

**14 committed FF-2D verdicts are keyed to a run whose bundle carries a CCS retrofit ledger.**

| verdict id | ISO | run id | peak CCS MW | tier | determination | FC-4 | FC-5 | FC-6 |
|---|---|---|---|---|---|---|---|---|
| `caiso-t1f-pre-d60` | CAISO | `caiso-2026-2030-d46-remeasure` | 8852 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `caiso-t1f` | CAISO | `caiso-2026-2030-d60-arm` | 8622 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `ercot-t1f-pre-d60` | ERCOT | `ercot-2026-2030-d46-remeasure` | 2742 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `miso-t1f-pre-d60` | MISO | `miso-2026-2030-d45r-remeasure` | 4631 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `neiso-t3-pre-d60` | NEISO | `neiso-2026-2050-t3-golden3-bau` | 11209 | t3 | HOLD | FAIL | CAVEAT | CAVEAT |
| `neiso-t3-pre-d47` | NEISO | `neiso-2026-2050-t3-golden3-bau` | 11209 | t3 | HOLD | FAIL | CAVEAT | CAVEAT |
| `neiso-t3` | NEISO | `neiso-2026-2050-t3-golden3-d60` | 9310 | t3 | HOLD | FAIL | CAVEAT | CAVEAT |
| `neiso-t1f-pre-d60` | NEISO | `neiso-2026-2030-d46-remeasure` | 8943 | t1f | PROMOTE | n/a | SKIPPED | SKIPPED |
| `neiso-t1f` | NEISO | `neiso-2026-2030-d50-ccscapex` | 8803 | t1f | PROMOTE | n/a | SKIPPED | SKIPPED |
| `nyiso-t1f-pre-d60` | NYISO | `nyiso-2026-2030-d45r-remeasure` | 8971 | t1f | PROMOTE | n/a | SKIPPED | SKIPPED |
| `nyiso-t1f` | NYISO | `nyiso-2026-2030-d60-arm` | 6475 | t1f | PROMOTE | n/a | SKIPPED | SKIPPED |
| `pjm-t1f-pre-d60` | PJM | `pjm-2026-2030-d45r-remeasure` | 3585 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `pjm-t1f` | PJM | `pjm-2026-2030-d60-arm` | 910 | t1f | HOLD | n/a | SKIPPED | SKIPPED |
| `pjm-t1f-d50-ccscapex` | PJM | `pjm-2026-2030-d50-ccscapex` | 910 | t1f | HOLD | n/a | SKIPPED | SKIPPED |

**FC-4 / FC-5 / FC-6 rows that are actually SCORED on such a run: 3.**
- `neiso-t3-pre-d60` (NEISO): FC-4 FAIL, FC-5 CAVEAT, FC-6 CAVEAT
- `neiso-t3` (NEISO): FC-4 FAIL, FC-5 CAVEAT, FC-6 CAVEAT
- `neiso-t3-pre-d47` (NEISO): FC-4 FAIL, FC-5 CAVEAT, FC-6 CAVEAT

**Read that table carefully — the answer is narrower than the census suggests, and that is the
point:**

- **FC-4 co2 rows are NOT mis-stated.** The only scored FC-4 `dispatch skill` rows on a
  CCS-carrying run read `co2 2023 |12.8%|` and `co2 2024 |11.3%|` — crossover metric-years that
  end in 2027, before `ccs_retrofit_available_year`. The crossover bundles themselves carry no
  retrofits. FC-4 is clean.
- **FC-5 co2 rows ARE mis-stated, three of them**, on the three NEISO T3 verdicts
  (`neiso-t3`, `neiso-t3-pre-d60`, `neiso-t3-pre-d47`): the corridor row's explained-divergence
  list names **`co2@2030`, `co2@2035`, `co2@2040`**, every one on a fleet carrying 8.9–13.1 GW of
  retrofits. Each is currently an `EXPLAINED DIVERGENCE`; the repair moves the model value, so the
  explanation must be re-authored, not merely re-scored. (The same three verdicts' non-CO2 corridor
  rows — capacity and generation:gas/oil/renewables at 2030/2035/2040 — move too, since generation
  shifts between `gas_cc` and `gas_cc_ccs`.)
- **FC-6: the load-bearing row is `paired P1`, and it is a cumulative-CO2 row.** It reads
  *"P1 CO2 monotone vs carbon: cumulative CO2 base 284.42 Mt vs high 273.92 Mt"* over 25 years on
  the CCS-carrying fleet. **Both operands are mis-stated, and so is the sensitivity** — the P1
  perturbation is a carbon-price increase, and a correctly-rated captured unit pays one tenth of
  that adder, so the margin between the arms is exactly what this seam distorts. `paired P2`
  (merit-order sign, *"gas-fired 35.01→34.77 TWh"* at 2050) is likewise mis-stated in its operands.
  `paired P3` (cumulative builds) is unlikely to move — builds were identical in every year of this
  session's A/B.
- **FC-6 battery arms:** the `battery gate rows` row is already `CAVEAT` on all three, for two
  **vacuous** ladder rows — `T1.6/T1.6a` and `T1.6/T1.6b`, both flagged *all-constant series
  `[1.0, 1.0]`*. Their **status will not change** (a vacuous row stays a caveat), but the
  underlying series are drawn from a CCS-carrying fleet and would need re-running with the rest.
- **The other 11 verdicts** in the table read FC-4 `n/a` (no crossover leg), FC-5 `SKIPPED` (no
  committed benchmark-corridor table) and FC-6 `SKIPPED` (no committed driver-battery output), so
  **no scored cell moves on them.** What moves on those is FC-1/FC-2/FC-3 content and the bundles'
  own CO2 rows — reported here so the batch does not mistake `SKIPPED` for "unaffected".

**None of this is acted on here.** No `ff-verdicts.json` byte, no `program-status.json` byte, no
re-score, no GOLDEN-3 re-solve — those belong to D60-R4 / D63 / D65-B this window.

### 8.3 Routed items

1. **The parasitic-uplift question in `ccs.py`'s own capture arithmetic** (§2.2): the residual rate
   and the captured tonnage are both computed off the **unpenalized** rate while the heat rate
   rises 12 %. Physically the residual should be `old_er × (1 + pen) × (1 − capture)`, ~12 % higher,
   and the captured tonnage ~12 % higher too — which changes the §45Q stream and the transport cost
   and therefore the retrofit set. **Owner: the capx CCS lane.** Not a D77 change: it has real DOF
   consequences and belongs with the D50/D65 fixed-cost work.
2. **Same-key bundles that disagree** (§7) — the general hazard, of which D77's fix is one
   instance. Worth an owner box: the cache key hashes config only, so any behavioural code change
   silently re-uses stale bundles. The epoch ledger is the current control and it is human-read.
3. **The NEISO `federal_ces` matrix cell is now stale.** Its evidence text carries WS2b's routed
   description of this defect as an open item ("NOT fixed here … capx D50/D60/D65 owns it"). That
   routing is now discharged. The cell belongs to the scenario desk's lane, so it is **routed, not
   edited** — the same discipline WS2b applied. What a re-run would change there: the CES ladder's
   NEISO CO2 answer, which WS2b measured as sign-flipped, should be re-measured on the repair.

## 9. Rule 28 duty (b)

`ccs_retrofit_screen` is an existing matrix row; this session tested its behaviour at NEISO with a
same-HEAD A/B. **No verdict letter moves** — the mechanism's arming is unchanged and this is a
defect repair, not a lever — so the NEISO shard's cell keeps `{cell: "K", fc: "K"}` and gains an
evidence citation recording the repair and its measured effect. **Duty (c) is not engaged:** no
`ScenarioConfig` field was added, so no new matrix row is owed. Only `NEISO.js` is touched
(rule 25 `[R-ISO-SCOPE]`).

## 10. Artifacts and cleanup

**Deleted before merge (rule 29(c)):** `results/ff-t1f-d77/neiso` and
`results/ff-t1f-d77/neiso-control`. Both are rule-29 screen/control bundles, never registered, and
**this document carries every number this session will ever cite.** Git history is the record for
the bytes, exactly as rule 15 `[R-DASHBOARD]` says of pruned runs.

**Committed:** the fix (`ae8dd2a0`), the cache epoch entry, the seam test, the PRECOMMIT (pushed
before either solve), this FINDING, and the NEISO mechanism-matrix cell.

**Not touched:** any keeper, marker, shard or freeze; `ff-verdicts.json`; `program-status.json`;
the backcast registry; any other ISO's matrix shard; any other bare key.
