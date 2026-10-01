# PRECOMMIT — R-SPP: SPP 2019–2025 re-solved on corrected backcast inputs

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.9. Owner instruction
2026-09-24: every backcast year 2019–2025 runs on the year-correct EIA-860 vintage, plant-specific heat rates
(never the asset-class table) and granular CAMPD outage data.

**Precondition met.** F1 (#6572) and F2 (#6569) are merged; this lane is cut from `9210075392a128d14a5efb168ab1f9955a9b6946`.
**Phase 0 is zero LP.** Numbers: `results/calibration/_rspp_phase0.json`. Instrument:
`scripts/probes/_rspp_phase0_census.py`, a `run_year(..., fleet_only=True)` rebuild from each incumbent
bundle's own `meta.json`, one interpreter per (year, variant). This doc is pushed before any shard launches.

## 1. Incumbent and SPP-78

- **Incumbent keeper:** `2026-09-22-hydro-5-spp-floor` (bundle `hydro5_spp_floor_span`, 2023–25, CALIBRATED),
  with the rung `2026-09-22-hydro-5-spp-rung` (`hydro5_spp_floor_rung`, 2019–22, NOT-YET) stamped to it.
  Both were solved at `fda9ece3`.
- **The rung is invalid as an input record.** Audit D1: it priced 100 % of SPP thermal nameplate at
  `HEAT_RATE_BINS` bin centres. This re-solve replaces it.
- **SPP-78 (measured CC / ST / coal)** merged as a record but was **not promoted**; `keepers/SPP.json` still
  names hydro-5. SPP-78 solved on the pre-F1 2023–25 artifacts and the pre-F1 heat-rate-less 2019–22
  vintages. F1 has since flipped all five `measured_*_heat_rates` fields on by default in backcast and
  re-derived every artifact over 2019–2025 (a pooled row plus per-year rows). **This run subsumes SPP-78.**
  SPP-78's three fields are a subset of the arm set below, and they read different, corrected artifacts.
  SPP-78's numbers are not a control for this run, and its matrix `O` cells are superseded by this lane's
  cells (§8).

## 2. Registered years (rules 34(c) / 35(b))

The union of `years` over every SPP sidecar (`frontend/data/backcast/registry/2026-09-22-hydro-5-spp-floor.json`
plus `…-rung.json`) is **{2019, 2020, 2021, 2022, 2023, 2024, 2025}**.

**Benchmarks.** Every year is scorable. Both incumbent `metrics.json` list 2019–2025 as `scorable_years`,
with no `data_blocked_years` and no `price_reference_blocked_years`.

## 3. Census (zero LP)

Variants:
- `ctl` is the incumbent recipe at HEAD with the five measured flags and `unit_partial_outage_windows`
  forced False. That is the F1 eGRID-year-matched layer alone.
- `arm` is this run's recipe (§5).

"Class-table MW" uses the EXACT measure: the plant's active EIA-860 row carries no joined eGRID heat rate,
**and** no measured artifact row covers it that year.

HR is the capacity-weighted loaded heat rate (MMBtu/MWh). "COAL avail" is the Σ pmax × mean availability,
in TWh-equivalent.

| year | EIA-860 source | thermal MW | class-table MW (ctl→arm) | COAL HR | CC_REG HR | ST_GAS HR | CT_PEAKER HR | CC_CHP HR | COAL avail TWh (ctl→arm) |
|---|---|---:|---:|---|---|---|---|---|---:|
| 2019 | `eia-860/vintage_2019` | 52,404 | 836.8→836.8 | 10.279→10.231 | 7.313→7.202 | 11.109→10.931 | 12.075→11.064 | 5.344→9.464 | 125.274→124.196 |
| 2020 | `eia-860/vintage_2020` | 52,177 | 831.2→831.2 | 10.248→10.281 | 7.330→7.200 | 11.177→10.912 | 12.251→11.101 | 5.370→9.444 | 110.868→110.345 |
| 2021 | `eia-860/vintage_2021` | 51,226 | 830.1→830.1 | 10.152→10.107 | 7.534→7.266 | 11.224→11.103 | 11.693→10.892 | 5.393→9.586 | 113.358→112.761 |
| 2022 | `eia-860/vintage_2022` | 51,489 | 833.8→833.8 | 10.201→10.125 | 7.510→7.248 | 11.017→10.838 | 12.213→11.194 | 5.392→9.661 | 117.395→116.120 |
| 2023 | `eia-860/vintage_2023` | 50,907 | 833.8→833.8 | 10.318→10.159 | 7.394→7.223 | 10.887→10.717 | 12.089→11.173 | 5.400→9.274 | 100.500→99.772 |
| 2024 | `eia-860/vintage_2024` | 50,488 | 845.3→845.3 | 10.283→10.187 | 7.266→7.128 | 10.668→10.624 | 11.672→10.970 | 5.443→8.963 | 96.572→95.320 |
| 2025 | `eia-860` (canonical 2025ER; no `vintage_2025`) | 53,647 | 1,426.9→984.7 | 10.281→10.141 | 7.276→7.166 | 10.773→10.762 | 11.320→10.762 | 5.443→8.963 | 105.773→104.824 |

**(a) Vintage.** The resolved vintage equals the solve year in 2019–2024. For 2025 it is the canonical
snapshot.

**(b) Class-table MW.**
- **The incumbent's own solve:** 100 % of thermal nameplate in 2019–22 (audit §3a) and 2.9 / 3.1 / 4.1 %
  in 2023–25.
- **This arm:** 830–845 MW (1.6–1.7 %) in 2019–24 and 985 MW (1.8 %) in 2025.
- **The residual** is every plant absent from every eGRID vintage 2018–2024 and from CAMPD. These are the
  F1 residual list, reproduced exactly by this rebuild:

| plant | class | MW |
|---|---|---:|
| 56565 | CC_REGULAR | 507–511 |
| 2098 Lake Road | ST_CHP + CT_CHP | 112–131 |
| 7546 | CC_REGULAR + CT_PEAKER | 107 |
| 2255, 2120, 1280, 1328, 7555, 1327, 1320, 2256, 1324, 2217 | CT_PEAKER | ≤ 22 each, ~93 total |
| 64548 | CT_PEAKER | 151 (2025 only) |

  - 64547 (442 MW, 2025) is on the class table under `ctl` and is covered by the measured CT artifact under
    `arm`.
  - Lake Road's CHP rows are `basis_mismatch` in the CHP artifact every year, so they are correctly not
    applied.

**Heat-rate moves the arm makes, beyond SPP-78's three classes:**
- **CT_PEAKER** falls 5–9 % (−0.56 to −1.15 MMBtu/MWh). CAMPD loaded-hour rates replace eGRID, including the
  SPP-49 simple-cycle floor clamp on Pioneer 57881 (measured 10.25 vs the clamped value).
- **CC_CHP** (Eastman 55176, 271 MW) rises from eGRID's thermal-credited 5.34–5.44 to the measured power-only
  8.96–9.66. That is +65 to +79 %. The same field is armed K in the CAISO, MISO, NYISO and PJM keepers.
  This is the largest proportional move in the census. It is reported at full magnitude and is not netted.

**(c) Outage windows per family.** Windows starting that year / TWh of removed capability, from the committed
extracts (F2 coverage, 2019–2025 everywhere):

| family | armed | file sha256 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| std ≥5-day | ✔ (incumbent) | `05aced4ff69f` | 943 / 135.93 | 932 / 141.79 | 982 / 136.61 | 946 / 127.09 | 912 / 135.14 | 939 / 131.46 | 973 / 122.43 |
| short coal | ✔ (incumbent) | `82fca832aeec` | 181 / 5.04 | 239 / 6.51 | 379 / 10.69 | 270 / 8.17 | 163 / 5.33 | 211 / 6.43 | 246 / 6.94 |
| short gas | ✗ (matrix R) | `cbf85409c43a` | 906 / 9.40 | 934 / 10.81 | 1160 / 14.83 | 1071 / 14.36 | 935 / 11.82 | 840 / 10.18 | 1063 / 12.55 |
| unit partial derate | **✔ (new arm)** | `7acc39f6e21d` | 36 / 1.27 | 29 / 0.67 | 17 / 0.68 | 37 / 1.47 | 18 / 1.02 | 41 / 1.51 | 26 / 1.22 |

**Partial-derate footprint in the fleet rebuild.** COAL availability falls by 0.52–1.28 TWh/yr. Every other
class is unmoved (the family is coal-scoped). This is the unit-grain detector, not ERCOT's plant-grain path.

**Short-gas stays OFF.** Its R (SPP-32) was a **2025** screen. 2025 was solved on eGRID heat rates, not the
D1 bin centres, so D1 did not contaminate it. The kill was physical:
- G4 identity failed: 10.9 GWh of VOLL slack in 12 SPP-South hours.
- C3a and C3b flipped to FAIL on pure scarcity.

Nothing in F1 or F2 changes the 2025 gas windows (F2 §3: SPP short-gas 2023–25 is byte-identical after the
merit-panel pin). By the charter's own test, it is not re-opened.

## 4. G-DRIFT (rule 29(b)) — `fda9ece3` → `9210075`

Scope: `git diff` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source` and `data/raw/reference`.

**LIVE by design (the F1 / F2 hunks):**
- **`59ba7ca9` (F1):**
  - `egrid.py` resolver
  - vintage-aware `_join_egrid_heat_rate` plus the regenerated `vintage_2018…2024`, canonical and retiree
    parquets
  - boundary repair reads the active vintage
  - per-year measured-rate loader `campd_bins._measured_rate_map`
  - `_rows_to_generators(heat_rate_year=…)`
  - `chp.py` year threading
  - `heat_rate_years.py`
  - the six backcast default flips plus the `__post_init__` coercion
  - `results/cache.py` epoch
- **`4efebee0` (F2):** the SPP / SOCO merit-panel pin. This is deriver-only and not on the solve path. The
  F2 extract extensions (SPP partial, short-coal, short-gas 2019–22 rows) are data under `data/raw/`.
  SPP's std and short-coal extracts are byte-untouched (F2 §3).

**INERT for SPP backcast:**

| commit | what it changes | why inert for SPP |
|---|---|---|
| `bb749a94` / `9c99bd47` / `68f84c5c` / `12161857` / `79fc1436` (Y-28/29/30) | cache-key registration, pins, lint, import cycle | no solve arithmetic |
| `da9fc148` (pjm-h22) | RGGI 2020–22 membership, zone share and price; `capacity_market.py` / `fuel_trajectories.py` | no SPP state is a RGGI member; capacity market is forecast-only |
| `4263d602` (soco-61) | `campd_dark_unit_year_windows` | default False, absent from recipe |
| `79aa52c5` (miso-268) | `coal_fuel_inventory_plant_grain` (lp rows / model / spec) | default False, absent |
| `4b66bc2d` | `demand_balance_screen` (eia930 demand, runner) | default False, absent |
| `329e2026` | `nwpp_grid_carried_wind_served` (envelopes, runner) | default False, NWPP branch |
| `f560408f` / `2a20e9d9` (soco-60b / 59) | SOCO-only constants (PS split, BA recode) | other ISO's keys |
| `6831b110` | storage dispatch/SOC comparison | report-only payload |

**Scorer-side, not solve:** `ad42fe43` repairs the EIA-923 benchmark builder's dual-fuel oil re-attribution.
It reaches SPP's benchmark frame, so the incumbent is **re-scored at HEAD** beside the new run. The
comparison is on one benchmark frame; the incumbent's committed metrics are not used.

**No control solve** (rule 29(b)). The only LIVE hunks are the intended input correction, so the committed
incumbent is the control. It carries the rule-36(f) warm-start artifact as well; both are reported as one
"old keeper → re-solve" delta and not attributed to any single arm. A per-arm attribution would need
controls this charter does not ask for.

## 5. Recipe (fixed now)

Every year runs from **its own incumbent bundle's `meta.json`**: the rung for 2019–22, the span for 2023–25.
The recipe adds exactly these `--set` values, and nothing else changes:

```
--set measured_ct_heat_rates=true   --set measured_coal_heat_rates=true
--set measured_st_heat_rates=true   --set measured_cc_heat_rates=true
--set measured_chp_heat_rates=true  --set unit_partial_outage_windows=true
--set mid_vintage_exit_carry=true   --set eia860_vintage_tracks_solve_year=true
```

- **The five measured flags and the vintage flag** are F1's backcast defaults. They are passed explicitly so
  the recipe is self-documenting and does not depend on a default.
- **`unit_partial_outage_windows`** is the charter's "ARM unit partial-derate (U)".
- **`mid_vintage_exit_carry`** is already True on the rung (matrix K, SPP-48). Setting it on 2023–25 unifies
  the recipe so all seven years compose into **ONE bundle**, as the charter asks. The incumbent split into
  span and rung on this field alone (plus the per-year gas price and weather year). Phase 0 measured it
  **fleet-inert in 2023–25**: rows, heat rate, pmax and per-row mean availability are identical to 0.0 in
  2023, 2024 and 2025, arm with vs arm without. It adds no DOF (a K mechanism, one published field).
- **Offer-curve multipliers are UNCHANGED.** The `offer_curve_overrides` block is the incumbent's 0.93 across
  every class, byte-identical in every leg. This is an input correction (rule 1(c)): nothing is re-tuned,
  swept, or selected against a gate.
- **Short-gas stays off.** Every other incumbent flag is untouched.
- **Gas price hard stops:** 2019 2.57 / 2020 2.03 / 2021 3.72 / 2022 6.45 / 2023 2.54 / 2024 2.19 /
  2025 3.52.

## 6. Solve plan (rules 32 / 34 / 36)

**Seven shards, one per year**, all pinned to this commit's full SHA. Each shard runs:

```
uv run python scripts/replay_keeper.py results/calibration/<hydro5_spp_floor_rung|hydro5_spp_floor_span> \
  --years <Y> --out-dir results/calibration/rspp_<Y> --note "R-SPP <Y>: corrected backcast inputs" <the 8 --set above>
uv run python scripts/probes/_rspp_shard_check.py --year <Y> --keeper results/calibration/<bundle> --leg results/calibration/rspp_<Y>
```

- **Push:** each shard pushes its full bundle, including `dispatch/<Y>_P1.parquet`, to `claude/rspp-<Y>`. It
  uses a `.gitignore` negation plus a plain `git add` (rule 34(a)).
- **Parent composes** with `scripts/probes/_rspp_compose.py`. That script refuses any leg missing the arm
  signature or disagreeing on a shared field.
- **Parent scores** the composite and the incumbent at HEAD, then registers the composite (rule 15).

## 7. Expectations (directional; declared so they cannot be fitted)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all seven legs: the recipe diff is exactly the arm set; the nine input sha256 match. |
| E2 | CT_PEAKER TWh rises in every year vs the incumbent (5–9 % cheaper CT). CC_CHP TWh falls in every year (Eastman +65–79 % HR). |
| E3 | 2019–22: offer HR rises in CC / ST vs the incumbent's bin centres (SPP-78 ADDENDUM direction). Demand-weighted mean price rises in 2019–22 by ≤ $2/MWh. 2023–25 moves by ≤ $1.5/MWh. |
| E4 | COAL TWh changes by ≤ 2 TWh in any year. The partial family removes ≤ 1.3 TWh of coal availability. |
| E5 | C1 COAL_PRB 2022 stays out of band (the crossover object, SPP-69 / 75 / 77). No arm here addresses it. |
| E6 | C8 / D-4 stay clean. No arm touches a floor (rule 19); a forced-share move is a denominator effect. |

## 7a. Recommendation rule (fixed now)

**Recommend PROMOTE iff all hold:**
- (a) E1 holds on every leg.
- (b) C8 / D-4 are clean with no new forced share (rule 20).
- (c) `build_dof_ledger --check` shows zero new free parameters.
- (d) The composite registers and `audit_keepers` reads 0 failures once it is stamped as keeper.

**Gate outcomes are not a criterion in either direction** (rules 1 / 14). This is the owner-mandated
accurate-input posture. A regression is reported with its owning object and root-caused, never re-tuned.
The owner rules on promotion (rule 31); this lane recommends and does not act.

## 8. Standing duties

1. SPP matrix cells updated in `mechanism-matrix/SPP.js` (rule 28(b)):
   - `measured_{ct,coal,st,cc,chp}_heat_rates`
   - `unit_outage_short_windows` (its partial shape)
   - `eia860_vintage_tracks_solve_year`
   - `mid_vintage_exit_carry`
2. Nothing is deleted (rule 31).
3. Shards are archived once their bytes are fetched and verified (rule 33).
4. If promoted, follow the rule 35 order:
   1. Record the year union {2019..2025} (done: §2).
   2. Promote.
   3. `audit_keepers`.
   4. Prune the hydro-5 floor and rung.
   5. Rebuild status.
   6. Re-key `calibration-complete.json`.
   7. Run the keeper auditor.
