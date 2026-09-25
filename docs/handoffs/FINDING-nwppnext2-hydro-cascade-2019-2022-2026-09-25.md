# FINDING — NWPP-NEXT-2 item 3: hydro cascade artifacts extended to 2019–2022 (2026-09-25)

**Keeper:** `2026-09-25-nwpp-next-ferc714-partial` (`results/calibration/nwppnext_span`). It arms
`hydro_cascade_coupling=True`, but the cascade was **INERT in 2019–2022**. The artifact covered
2023–2025 only, and `load_hydro_cascade` returns `None` for a year with no monthly rows. The bundle
carries `hourly/hydro_cascade_<y>.parquet` for 2023–25 only.

**Result: zero LP, no solve.** The artifact now covers 2019–2025. On the keeper's own fleet-only
rebuild, the solve path's resolver now returns the cascade in 2019, 2020, 2021 and 2022: 5 coupled
plants, 5 links, τ [0, 1, 1, 0, 0] h, the same spec shape as 2023. Every 2023–2025 artifact row is
unchanged, and the links csv is byte-identical.

## 1. Rule-23 decision (`[R-FROZEN-DERIVE]`) — recorded

- **Extended:** the MONTHLY rows only, i.e. the per plant-month η (EIA-923 net MWh per kcfs·h of
  CROHMS turbine flow), outflow and spill means, and side inflow (raw, floored, floor and STOP flag).
  Their inputs are the new 2019–22 CROHMS pull and the EIA-923 monthly series for those years.
- **Frozen:** τ per link, the pondage band (`pond_kcfsh`), the NID areas and the `coupled` / `reason`
  verdicts. They stay exactly as NWPP-36 trained them on 2023–2024 (checked on 2025).
  `nwpp_hydro_cascade_links.csv` is **byte-identical**. The links, coupled flags and gates were NOT
  re-derived.
- **Mechanics:** `--extend-years` reads τ and verdicts from the committed links csv and derives
  nothing; the default NWPP-36 derive is pinned to `DERIVE_WINDOW = 2023-01-01 → 2026-01-01`, and
  re-run on the MERGED pull it reproduces the committed links and monthly csvs **byte for byte**
  (unpinned, the 25-h anomaly, `diff()`/`shift(τ)` at 1 Jan 2023 and `measured_avg_outflow_kcfs` would read 2022).
- **η nearest-year substitution** in the extension draws only from the extension years. None was
  needed: 2019–22 have zero substituted plant-months, and McNary and Dworshak 2025 still take 2024,
  as committed.
- **A 2019–22 side-inflow STOP is REPORTED, not acted on.** It is shown in the row and the log and
  never re-opens a verdict. The one case that touches a coupled link is in §3.

## 2. What changed (rows; 2023–2025 content)

| path | before → after | 2023–25 check |
|---|---:|---|
| `data/raw/nwpp-hydro/crohms/nwpp_crohms_hourly.parquet` | 2,103,124 → 4,905,303 (+2,802,179) | value-identical row for row, same dtypes and sort (the file bytes necessarily change) |
| `data/raw/nwpp-hydro/crohms/nwpp_crohms_daily_idp.parquet` | 2,192 → 5,117 (+2,925) | value-identical |
| `data/raw/nwpp-hydro/crohms/SHA256SUMS.txt` | 2 hashes changed | catalog hash unchanged |
| `data/raw/nwpp-hydro/nwpp_hydro_monthly_923.parquet` | 7,212 → 21,036 (+13,824) | `DataFrame.equals` True |
| `data/raw/nwpp-hydro/nwpp_hydro_monthly_923_flags.csv` | 601 → 1,753 (+1,152) | lines verbatim |
| `data/raw/nwpp-hydro/nwpp_hydro_budget.parquet` | 877 → 2,056 (+1,179) | `DataFrame.equals` True |
| `data/raw/nwpp-hydro/nwpp_hydro_reconciliation.csv` | 877 → 2,056 (+1,179) | lines verbatim |
| `data/raw/nwpp-hydro/nwpp_hydro_cascade_monthly.csv` | 576 → 1,344 (+768 = 16 plants × 48 months) | lines verbatim, in order |
| `data/raw/nwpp-hydro/README.md` | new section appended | — |

**Byte-identical, NOT rewritten:** `nwpp_hydro_cascade_links.csv`, `nwpp_hydro_cascade_nid.csv`,
`nwpp_hydro_chain.csv` (per-year columns stay 2023–25 via `CHAIN_YEARS`),
`nwpp_hydro_within_month_930.csv` (`--skip-930`; `--years-930` defaults to 2023–25),
`crohms/nwpp_crohms_catalog.json` (the 2019–22 pull returned an identical catalog), pondage and PNCA files.

The 80 overlapping keys at 2023-01-01 00:00 agreed exactly. The merge refuses any disagreement.

**Scripts changed:** `fetch_nwpp_crohms_hourly.py` (`--merge-only`); `build_nwpp_hydro_budget.py`
(`--years`, default every extract year; `--years-930`; `CHAIN_YEARS`); `build_nwpp_hydro_cascade.py`
(`DERIVE_WINDOW`, `load_hourly(window)`, `measure_monthly(years, eta_years)`, `--extend-years`).
**New probe:** `scripts/probes/_nwppnext2_cascade_extension_check.py`.

## 3. Data quality, 2019–22 CROHMS (refuse, never fabricate)

- **Coverage:** 16/16 stations × 5/5 series every year; quality 0 on all 2,802,259 values; no sentinels or NaN.
- **Missing hours per series-year:** at most 80 (DWR Power 2020). Most are 0–13. The widest are
  DWR / LGS / LMN / LWG / MCN / IHR in 2020 (31–80 h) and TDA in 2022 (32–33 h). Nothing is filled.
  - η scales the turbine-flow sum to the full month, the committed construction. The worst
    plant-month is 55 missing gen-hours (2020), against 63 in committed 2025.
- **Forebay 0.0 spikes:** 19, 48, 150 and 13 hours in 2019–22, against 5, 3 and 3 in 2023–25. The
  builder's own screen (< 0.5 × median → NaN) drops them from the balance. No negative flows occur
  in 2019–22.
- **EIA-923:** 288/288/287/289 footprint hydro plants in 2019–22; Gate A **0 MISMATCH** every year;
  loader cross-check max |loader − artifact| **0.00 MWh / 0.00 MW**; η complete (12/12, all > 0) for
  every coupled and upstream plant every year.
  - The 2019–22 η ranges sit inside or near the 2023–25 ranges. Examples: CHJ 12.3–13.9 vs
    13.0–13.4; BON 3.2–4.9 vs 3.5–5.0.
- **Side-inflow STOPs in the extension:** CHJ 1, JDA 15, LGS 39, LMN 2, PRD 29, RRH 14, TDA 20.
  - Only CHJ is a coupled downstream plant. The case is **GCL→CHJ, 2019-09**: floor 1.404 kcfs =
    **2.67 %** of 52.53 kcfs arriving (gate 2 %), with zero spill that month.
  - A 2019 re-derive would STOP link 1; under rule 23 the verdict stays frozen (not a refit trigger).
    The row floors side inflow at 0 and CHJ's spill column absorbs the surplus, so it stays feasible.
- **τ diagnostic (reported only, `_nwppnext2_cascade_extension_check.py`):** 2019–22 per-year τ
  stays within **±1 h** of the frozen τ on all 5 coupled links, in all 20 link-years.

  | link | frozen τ | 2019 | 2020 | 2021 | 2022 |
  |---|---:|---:|---:|---:|---:|
  | GCL→CHJ | 0 | 0 (r 0.86) | 0 (0.74) | 0 (0.84) | 1 (0.73) |
  | CHJ→WEL | 1 | 0 (0.57) | 1 (0.44) | 2 (0.52) | 1 (0.36) |
  | RRH→RIS | 1 | 1 (0.96) | 1 (0.91) | 1 (0.93) | 1 (0.92) |
  | TDA→BON | 0 | 1 (0.45) | 1 (0.41) | 1 (0.45) | 0 (0.53) |
  | LMN→IHR | 0 | 1 (0.68) | 0 (0.82) | 0 (0.81) | 1 (0.75) |

## 4. What the LP now does in 2019–2022 (read from the code, confirmed at zero LP)

- **Gate:** `ScenarioConfig.hydro_cascade_coupling` (True in the keeper; mutually exclusive with
  `hydro_pondage_bound`, and arming both raises). Path: `pipeline.kwargs.resolve_hydro_cascade` →
  `data.hydro.load_hydro_cascade(iso, year, codes)`.
- **Columns read:** links `coupled`, `u/d_plant_id`, `tau_h`, `pond_kcfsh`; monthly
  `eta_mwh_per_kcfsh`, `side_inflow_kcfs`, `spill_mean_kcfs` (head or uncoupled upstream) and
  `outflow_mean_kcfs` (upstream that is not an LP unit).
- **Before:** the year filter emptied → `None` → `UNSET` → the unchanged LP. **Now:** a spec is
  returned in every year 2019–2025.
- **Fleet-only rebuild** of the keeper recipe (`run_year(fleet_only=True)`, `hydro_backfill_year`
  null) with the resolver called on the result:

  | year | LP hydro plants | coupled plants | links | τ |
  |---|---:|---|---:|---|
  | 2019 | 281 | CHJ 3921, WEL 3886, RIS 6200, BON 3075, IHR 3925 | 5 | [0, 1, 1, 0, 0] |
  | 2020 | 280 | same | 5 | same |
  | 2021 | 278 | same | 5 | same |
  | 2022 | 277 | same | 5 | same |
  | 2023 (control) | 285 | same | 5 | same |

- **Per year the solve adds** 5 × 8,760 = **43,800 equality rows** (water balance per coupled
  plant-hour) and **87,600 columns** (spill, pond) — the rows 2023–25 already carry. They redistribute
  *when* a coupled plant turbines its monthly EIA-923 budget, never how much (rule 19).
- **Expected 2019–22 signature:** the same as 2023–25's. CHJ locks to GCL's release shape at τ = 0,
  and within-day amplitude falls modestly. This is FINDING-nwpp-36 §5, G-A3 (xfail, strict).
- **Class TWh:** hydro class TWh cannot move by construction. Any thermal movement is second-order,
  through the hourly shape.

## 5. `hydro_backfill_year` — should 2019–22 keep `None`? **Yes.**

- **Semantics:** `load_hydro_budget(backfill_year=B)` carries plants that reported in B but not in the
  solve year, at their B-year monthly energy (built for the EIA-923 2025 early release). `None` loads
  the year exactly as reported; `2024` (keeper, 2023–25) fills 2025's 263 non-reporters and injects
  the few 2024-only reporters into 2023.
- **Why `None`:** 923 is final in 2019–22; the 5–8 EIA-860 plants with no series did not report, and a
  2024 backfill would fabricate their energy (rule 14) — the attestation already records `None`. The
  cascade does not depend on it: all 5 coupled plants are LP units in 2019–22 under `None` (table above).

## 6. The replay a span would need (not run — ZERO LP, rules 32 / 36: one shard per year, composed)

The keeper already records `hydro_cascade_coupling=True`, so **no new `--set` is needed**. The
change is purely the artifact. Per year `<Y>`:

```
python3 scripts/replay_keeper.py results/calibration/nwppnext_span \
  --out-dir results/calibration/<lane>_<Y> --years <Y> \
  [<Y> in 2019 2020 2021 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-2: keeper recipe, cascade artifact extended to 2019-2022 (monthly rows only; links frozen)"
```

- **Kwargs (run_year):** `hydro_backfill_year=None` for 2019–22, 2024 for 2023–25;
  `prb_overrides.hydro_cascade_coupling=True` as recorded. Only the 2019–22 legs move (2023–25 inputs
  unchanged; G-DRIFT still applies). Expected: new `hourly/hydro_cascade_<Y>.parquet` for 2019–22.
- **Open for the owner:** whether to solve (a structural arm, rule 1: it completes a mechanism the keeper already claims).

## 7. Tests

`tests/unit/model/test_hydro_cascade.py`, `tests/unit/pipeline/test_hydro_cascade_cli_flag.py`,
`tests/unit/data/test_hydro_pondage_bound.py` and `tests/curation/test_curate_hydro_plant_modes.py`:
**34 passed, 1 xfailed** (the strict G-A3 xfail, unchanged). `tests/unit/config/test_data_profiles_tokens.py`:
54 passed. `ruff check` and `ruff format --check` are clean on all four touched scripts.
