# PRECOMMIT — soco-71: the SOCO coal heat-rate artifact, re-derived over the window it declares

Lane soco-71, 2026-09-26. Written and pushed **before any shard was launched**. The parent solves nothing
(rule 32(a)). Each year is solved in its own shard (rule 36) and each shard pushes its full bundle (rule 34).

Control: the keeper `2026-09-26-soco70-coal-rows-measured` (bundle `results/calibration/soco70_span`, legs solved at
`e3cea99b74a21838853d233ace8f17afce308852`). Its committed numbers are the control (rule 29(b) form 4). No control
solve is spent.

## 0. G-DRIFT (rule 29(b)), keeper sha → HEAD `9149be2c`

- **Measured.** `scripts/probes/_soco71_gdrift_identity.py` rebuilds the keeper recipe's `fleet_only` arrays at both
  shas on one shared `data/` tree: **ALL LP INPUTS BIT-IDENTICAL**, all seven years, all 14 arrays (labels included).
  Record: `results/calibration/_soco71/gdrift_input_identity.json` (gitignored).
- **Read by hand (code).** Every hunk on the backcast path is a new default-off `ScenarioConfig` field absent from the
  recipe (`admit_standby_units`, `unit_outage_netload_mask_repair`, `miso_winter_gas_daily_delivered`), or the
  neiso-117 coal-yard reconcile, which runs only under `coal_fuel_inventory*` (both `False` in the recipe).
  Changed path defaults (`campd_bins_path` etc.) are settled by the measurement. **INERT.**
- **Read by hand (data).** Every `data/raw` change since `e3cea99b` is another ISO's own artifact: NEISO CT heat rates,
  SPP net-load-mask outage layers, NYISO merit-hour outages, CAISO supply-consistent demand. **INERT for SOCO.**

**Form 4 is valid. The keeper is the control.**

## 1. Why the 2019 cyclers under-run: the decomposition (zero LP)

`scripts/probes/_soco71_phase0.py decompose --years 2019`, on the soco-70 2019 leg. 2019 system price: p50 $33.19,
mean $32.53.

| plant | EIA-923 TWh | CEMS gross TWh | model TWh | CEMS synced h | model on h | synced, model off h | CEMS TWh in those h | model unavailable, synced h |
|---|---|---|---|---|---|---|---|---|
| Barry 3 | 4.175 | 4.634 | 0.145 | 8,307 | 405 | 7,933 | 4.399 | 108 |
| Crist 641 | 2.668 | 3.079 | 1.181 | 7,618 | 1,964 | 5,989 | 2.368 | 0 |
| Wansley 6052 | 1.816 | 2.275 | 0.127 | 3,774 | 144 | 3,673 | 2.198 | 0 |
| Gaston 26 (check) | 2.789 | 3.348 | 1.701 | 4,739 | 4,656 | 151 | 0.079 | 151 |

**Availability is not the cause.** 108 / 0 / 0 synced hours are unavailable in the model. The deficit is merit order.

**The offer, per tranche, over the plant's CEMS-synced hours:**

| plant | tranche | base $/MWh (P0) | P1 median | start markup median / max | base − price, median | share of synced h with base ≤ price |
|---|---|---|---|---|---|---|
| Barry | `_committed` | 37.61 | 66.09 | +28.57 / +100.00 | +4.43 | 4.7 % |
| Barry | econ / peak | 37.61 | 37.61 | 0 | +4.43 | 4.7 % |
| Crist | `_committed` | 37.86 | 65.87 | +29.52 / +100.00 | +3.47 | 22.1 % |
| Crist | econ / peak | 37.86 | 37.86 | 0 | +3.47 | 22.1 % |
| Wansley | `_committed` | 42.37 | 142.37 | +100.00 / +100.00 | +8.60 | 2.8 % |
| Wansley | econ / peak | 42.37 | 42.37 | 0 | +8.60 | 2.8 % |

1. **The start markup is real, but it is not what binds.** Only the `_committed` tranche carries it. The econ tranches
   carry none, and they still clear in only 4.7 / 22.1 / 2.8 % of the synced hours, because the **base** offer sits
   above the price.
2. **The measured-run basis would make the markup small.** CEMS median start-to-stop runs are 283 / 88.5 / 143.5 h.
   $100/MW over those horizons is $0.35 / $1.13 / $0.70 per MWh, against a markup of up to $100 today.
3. **Levers (i) and (ii) have a ceiling, and it is too low.** Stripping the markup from these plants' `_committed`
   tranche entirely, net of the greedy's own bias (§5), adds +0.42 TWh COAL_BIT in 2019 (≈ +0.15 pp) and +0.10 TWh in
   2020. The row needs roughly +1.7 TWh.
   - (i), a measured coal start basis, is bounded by this ceiling, so it is not taken.
   - (ii), a physics-keyed `coal_warm_committed` exemption, is bounded by it too. It also has no zero-parameter warm
     predicate for a unit that is dark 57 % of hours (Wansley).
   - Neither is armed. Both are recorded as the named next object (§8).
4. **Fuel is measured and right.** The model's implied delivered coal is $3.083 / $2.968 / $2.970 per MMBtu. Each
   plant's own 2019 EIA-923 receipts, volume-weighted, are $3.160 / $2.901 / $3.083. The gap is within 3 %, so there is
   no fuel-vintage repair (lever iii, fuel half).
5. **The heat rate in use is NOT measured for two of the three plants.**

   | plant | model HR 2019 | source | CEMS 2019 gross → net (÷ 0.93) |
   |---|---|---|---|
   | Barry | 10.739 | pooled artifact row (2023–25 hours only) | 9.905 → 10.65 |
   | Crist | 11.241 | **eGRID** (no artifact row) | 9.736 → 10.47 |
   | Wansley | 12.751 | **eGRID** (no artifact row) | 10.159 → 10.92 |

## 2. The defect: `campd_coal_heat_rates_SOCO.csv` never measured 2019–2022 for AL / FL / GA

The artifact declares `years = 2019-2020-…-2025`, and F1 (2026-09-24) flipped `measured_coal_heat_rates` on for every
backcast on the premise that every artifact carries a pooled 2019–2025 row plus per-year rows. For SOCO that is false:

- **Every pooled row except Daniel's (MS) equals the sum of its 2023–2025 per-year rows exactly.** Scherer:
  16,680 + 20,340 + 18,145 = 55,165 steady hours, which is the pooled row. Barry: 3,930 + 1,778 + 2,081 = 7,789.
- **No AL or GA plant has a 2019–2022 per-year row. Daniel (MS) has all seven.**
- The derive skips an absent state-year extract with `(skip …: not on disk)`. The AL / FL / GA 2019–2022 CAMPD
  extracts were not in the tree the artifact was derived from. They are now.

**Re-derived at HEAD, unchanged code, over the same declared window (`--egrid-family-heat-rates
--measured-ct-heat-rates --measured-st-heat-rates`, the artifact's recorded recipe):**

- **Every one of the 30 committed rows reproduces byte-for-byte.** That is every 2023–2025 row and all of Daniel's.
- The new rows are exactly the AL / GA 2019–2022 hours, plus Wansley (6052), whose coal units ran only in 2019–2022.
- **Pooled rows move** (the pooled estimator now sees its whole window): Barry 10.739 → 10.618, Gaston 11.051 →
  11.216, Bowen 10.244 → 10.382, Miller 10.794 → 10.845, Scherer 11.417 → 11.398.

**Second defect, same artifact: the population.** Crist (641) is COAL in the 2019 backcast fleet and gas-steam after
its 2020 conversion. `union_fleet(fleets)` keeps each unit's LATEST record, so Crist fell out of the coal derive's
population. That is the neiso-118 defect the CT sibling already guards with `klass=TARGET_CLASS`, and the coal derive
did not pass it.

- The fix is `union_fleet(fleets, klass=TARGET_CLASS)` in `scripts/data/derive_campd_coal_heat_rates.py`, with a test
  in `tests/curation/test_heat_rate_years_union.py`.
- **It only adds plants.** A plant whose latest record is coal reads the same record. Measured on SOCO, it adds
  Crist's three rows (pooled, 2019, 2020) and moves nothing else.
- Other ISOs' committed artifacts are untouched. They re-derive in their own lanes (rule 25).

**Rule 23 citation.** This re-derivation is triggered by the **source data** the artifact declares, not by a residual:
the CAMPD 2019–2022 AL / FL / GA extracts it never read, and the population rule it mis-applied. The committed rows it
did measure reproduce exactly. It is found by the decomposition of a residual, and the rule forbids exactly one thing
here: re-deriving because the residual moved. **The re-derived values are fixed by the estimator, not chosen.**

- Artifact sha256: `369a58ba7d8948bcfff2dcc72a819eec2ed2e8e935166833620e6b6c6ef2f948` →
  **`a55796376ce68c0b5004165084ad45eed650f293f7bccbfac491005d176d9d47`**.
- `thermal_tranches_SOCO.csv` is unchanged (`ab5ec265…22ad7`). There is no `ScenarioConfig` change. The recipe is
  the keeper's eight `--set` fields.
- **Zero free parameters.** The mechanism is `measured_coal_heat_rates` (SOCO cell `K`), a change to its INPUT
  coverage only.

Matrix check (rule 28(a)):

| cell | verdict | how this lane treats it |
|---|---|---|
| `coal_warm_committed` | armed (`K` since SOCO-58) | not re-tested |
| `thermal_tranche_artifact_coverage` | `K` | untouched |
| `coal_mustrun_requires_measured_row` | `K` | untouched |
| `tranche_startup_amortization` | `G` | **not armed**; the owner question stays open |
| `coal_plant_monthly_pricing` | shard reads `U`, but the keeper arms it | fuel verified, unchanged |
| `coal_sync_*` | `U` | not a lever: the keeper does not arm the sync floor |
| `measured_coal_heat_rates` | `K` | **this lane: input-coverage repair** |

**Not levers** (declared): `offer_curve_by_group` bands, any adder or offset, and re-deriving the thermal-tranche
rows against the residual.

## 3. Census (zero LP): the lever in the fleet

`_soco71_phase0.py fleet`, keeper recipe, incumbent vs re-derived artifact. **Every non-coal unit is byte-identical
in every year** (pmax, mc, min_gen, availability, asserted). Coal econ `mc` medians, $/MWh:

| year | Barry 3 | Gaston 26 | Crist 641 | Wansley 6052 | Bowen 703 | Miller 6002 | Scherer 6257 | Daniel 6073 |
|---|---|---|---|---|---|---|---|---|
| 2019 | 37.61 → 37.31 | 49.86 → 50.39 | 37.86 → 35.82 | 42.37 → 36.93 | 34.08 → 35.30 | 23.01 → 23.24 | 32.93 → 32.80 | = |
| 2020 | 38.66 → 36.98 | 48.64 → 48.48 | 44.54 → 38.61 | 49.14 → 34.12 | 33.89 → 34.24 | 23.06 → 23.38 | 33.06 → 34.27 | = |
| 2021 | 40.98 → 40.24 | 49.51 → 51.29 | — | 36.28 → 33.97 | 33.13 → 33.88 | 24.34 → 24.29 | 34.94 → 34.62 | = |
| 2022 | 45.34 → 46.05 | 73.26 → 76.06 | — | — | 43.55 → 44.21 | 28.88 → 29.06 | 42.48 → 41.51 | = |
| 2023 | = | = | — | — | = | = | = | = |
| 2024 | = | = | — | — | = | = | = | = |
| 2025 | = | = | — | 45.46 → 41.81 (avail 0) | = | = | = | = |

- **2023 and 2024 LP inputs are bit-identical to the keeper's.**
- **2025 differs only in the `mc` of four Wansley columns whose availability is 0** (upper bound 0).
- **The move is two-sided.** Wansley and Crist fall by up to $15/MWh. Bowen and Gaston rise.

## 4. Greedy estimate, NET of the instrument's own bias

The price-taker greedy on the **unchanged** fleet already moves 2019 COAL_BIT +0.60 TWh against the LP. Every number
below is therefore arm minus that baseline, both computed through the identical instrument. C1 is
`calibration_verdict.score_fuelmix` on the keeper's committed payload (scorer-exact; it reproduces the keeper's rows).
C4 is the scorer's own construction.

| year | COAL_BIT pp | COAL_PRB pp | ST_GAS pp | CC_REGULAR pp | CT_PEAKER pp | C4 coal NRMSE |
|---|---|---|---|---|---|---|
| 2019 | −3.45 → **−2.93** (still FAIL: −8.03 TWh vs ±7.64) | +2.71 → +2.66 | −2.63 → −2.72 | +2.40 → +2.19 | +0.96 → +0.80 | 0.159 → 0.171 |
| 2020 | −2.31 → −1.80 | +0.55 → −0.35 | −2.11 → −2.16 | +1.91 → +2.21 | +1.78 → +1.90 | **0.285 → 0.330 (FAIL risk)** |
| 2021 | +0.60 → +1.19 | +1.82 → +1.85 | **−2.75 → −2.76** | +1.86 → +1.31 | −0.61 | 0.203 → 0.236 |
| 2022 | +1.01 → +0.84 | **+2.67 → +2.67** | −2.29 → −2.26 | −0.49 → −0.42 | −0.85 → −0.78 | 0.238 → 0.268 |
| 2023 | = | = | = | = | = (+2.40) | = 0.268 |
| 2024 | = | = | = | = | = | = 0.256 |
| 2025 | C1 SKIPPED | | | | | = 0.184 |

2019 plant deltas (TWh): Wansley +1.72, Crist +0.52, Barry +0.03, Bowen −0.99, Miller −0.15.

## 5. Recipe and hard stops

Each shard runs one year `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document, which it pins
itself as step 0:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. python3 scripts/data/curate_demand_profile.py
python3 scripts/replay_keeper.py results/calibration/soco70_span --years <Y> \
  --out-dir results/calibration/soco71_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --note "soco-71 <Y>: soco-70 keeper recipe on campd_coal_heat_rates_SOCO.csv re-derived over its declared 2019-2025 window + coal-family population (rule 14/23 source coverage)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- `git rev-parse HEAD` equals the pinned SHA.
- `sha256sum data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv` equals `a55796…9d47`.
- `thermal_tranches_SOCO.csv` equals `ab5ec265…22ad7`, and so does `resolved_inputs.thermal_tranches.sha256`.
- `scenario_config` shows all eight `--set` fields true and `measured_coal_heat_rates` true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log carries `container preflight:` and `memory peak:`.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (identity).**
  - **2023 and 2024:** the leg's `class_hourly` and `unit_hourly` `mw` are byte-identical to soco-70's legs, because
    the inputs are bit-identical and the year is isolated.
  - **2025:** dispatch is identical up to degenerate ties. The only change is `mc` on zero-availability columns.
  - **A 2023 or 2024 difference is a stop-the-line finding**, not a result.
- **E2 (direction, 2019–2022).**
  - Wansley and Crist coal rise in every year they exist.
  - Bowen coal falls in 2019–2022.
  - COAL_BIT rises in 2019, 2020 and 2021.
  - Nuclear, hydro, wind and solar: |Δ| ≤ 0.1 TWh.
- **E3 (the failing row).**
  - **2019 COAL_BIT:** −3.45 pp / −9.31 TWh → ≈ −2.9 pp / −8.0 TWh. **Expected to STILL FAIL**, on volume, against a
    ±7.64 TWh band. A PASS needs the LP to refill ~0.4 TWh more than the net greedy, and that is declared a coin
    flip, not the expectation.
- **E4 (side-effect risks, declared now).**
  - **2020 C4 coal** may cross 0.30 (greedy 0.330). This is the most likely new FAIL.
  - 2021 ST_GAS −2.76 and 2022 COAL_PRB +2.67 stay thin PASSes.
  - 2019 COAL_PRB, ST_GAS and CC_REGULAR move ≤ 0.25 pp.
  - **Expected determination: NOT-YET.** One or two failing rows: 2019 COAL_BIT, and possibly 2020 C4.
- **E5 (unserved).** 0 MWh in every year. No capacity changes.
- **E6.** C2, C6 and C8 PASS. C3 is UNSCORABLE. D-2 and D-4 are unchanged in kind, because no floor is added.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all four of these hold:

1. All seven legs solve cleanly with the §5 hard stops met.
2. **The mechanism fires exactly as censused.**
   - In every leg, every non-coal unit's hourly `cap_mw` is byte-identical to soco-70's leg.
   - Every coal econ tranche's median solved `mc` matches §3 to ±$0.01.
   - E1's 2023/2024 identity holds.
3. No year's unserved energy increases.
4. C6 and C8 PASS, and `legitimacy_diagnostics` records no new D-4 FAIL.

**This holds whatever C1 and C4 do.** The lever replaces eGRID and a truncated pool with the plant's own metered rate
for the year (rules 14 / 23). If it opens a 2020 C4 FAIL, that is reported at full magnitude as a root-cause lead: a
measured input exposing what the stale one was compensating for. It is **never** a reason to keep the stale input.

The owner's standing ruling covers promotion. If it lands:

- Rule 35 enumerates the year union from every SOCO sidecar, then runs `audit_keepers` E1.
- Then `prune_iso_runs --iso SOCO --force-uncite` removes `2026-09-26-soco70-coal-rows-measured`.

## 8. Named next object (not armed here)

**The coal start markup on no-must-run cyclers** — `coal_warm_committed`'s must-run predicate against a measured start
basis. It is real (up to +$100/MWh on Wansley in 2019) and the fix is small (§1.3). It rides with the SOCO-64/65 owner
question on cost-based starts, and it is not decided here.

## 9. Retrievability (rule 34(e))

- Each shard pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco71-<Y>` through a
  `.gitignore` negation and a plain `git add`.
- The parent fetches each leg, verifies it, and composes `soco71_span`. It lands the composite (slim set + `hourly/`),
  the sidecar and the payload on `main` with this lane's PR.
- A leg not landed on `main` is costed as a re-solve, ~2 min of LP.
