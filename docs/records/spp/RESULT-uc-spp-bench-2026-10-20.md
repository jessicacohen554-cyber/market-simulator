# RESULT — UC-SPP-BENCH: SPP scoring benchmark and outage net-load mask on the stale-snapshot repair (2026-10-20)

Owner ruling **R27** (2026-10-19, decision card, verbatim: "Re-base, separate PR (Recommended)"). Desk UC-DESK
`session_01WX9W5tgYMre3Z134LZoGF6`. Base `main` `583ff0d5`. **Zero LP.** DATA PROFILE: spp.
Follows `RESULT-uc-spp-datafix-2026-10-18.md` (#7287, its §4 residue) and `RESULT-uc-spp-control-2026-10-19.md` §4.

## 0. Answer

- **One code path.** `stale_snapshot.repair_eia930_frame` serves a raw SWPP frame's stale hours from the values the LP-input
  repair already produces (rule 19: same detector, same masks, same sources). Two readers now use it: the EIA-930 scoring
  benchmark (`load_eia_hourly_benchmark`) and the outage net-load mask (`outage_detect.high_load_mask`).
- **No determination changes. No criterion changes status in any year, for either bundle.** Keeper NOT-YET → NOT-YET; control
  NOT-YET → NOT-YET (§4).
- **The C4 artefact UC-SPP-CONTROL found closes.** Scored on the repaired benchmark, the control's 2025 gas r goes 0.930 → 0.960 and
  coal r 0.882 → 0.920; 2019 gas 0.938 → 0.966. The keeper, solved on the stale inputs, moves the other way (2025 gas 0.954 → 0.916).
  Both still PASS.
- **No estimate anywhere.** Two columns have no basis-matched SPP series (`NG: OIL`, `NG: OTH`): EIA's own value is kept and flagged,
  bounded at ≤ 0.02 / ≤ 0.21 TWh/yr of masked-hour energy (§2). They are not hourly-scored; see desk question (a).
- **Rule 23 derives.** The 1–5-day outage extract (`-short-netloadmask-`, read by the SPP keeper) is re-derived: 10 coal windows
  added, 11 dropped. The ≥ 5-day and partial companions re-derive unchanged. SPP 2023–25 `*_lw` price weights are re-derived on the
  #7287 demand (C3a actual moves ≤ 0.06 $/MWh).
- **Re-key.** SolveEpoch `2026-10-20a` (SPP backcast arming `unit_outage_netload_mask_repair`). G-DRIFT: the SPP keeper and the
  control being promoted are LIVE on the short-window extract (§5).

## 1. What changed

| Piece | Where |
|---|---|
| Frame repair, matched to the repair clock by each row's own UTC stamp | `src/market_sim/data/stale_snapshot.py::repair_eia930_frame` |
| Per-column provenance | `stale_snapshot.benchmark_stale_provenance` |
| Spec fields | `genmix_columns`, `kept_stale_genmix_hours`, `kept_stale_columns` on `StaleSnapshotSpec` |
| Declared gaps (iv), (v) | `constants.SPP_STALE_KEPT_BENCHMARK_COLUMNS`, `SPP_STALE_KEPT_NUCLEAR_HOURS_UTC` (declared at landing hash; move no key) |
| Hooks | `eia930/actuals.load_eia_hourly_benchmark` (after the spike screen, before gap-fill); `scripts/lib/outage_detect.high_load_mask` |
| Re-derived data | `data/raw/campd-unit-outages-short-netloadmask-SPP.csv` (+ meta); SPP 2023–25 `*_lw` in `actual_lmp.json` |
| Probe | `scripts/probes/spp_bench_stale_rescore.py` |

Per column, in the column's own stale hours:

| Column | Source | Mask |
|---|---|---|
| `Demand`, `Total interchange` | `repair_system_demand`, `repair_net_interchange` (#7287) | demand mask |
| `Net generation` | repaired demand + repaired interchange (EIA-930's identity D = NG − TI) | demand mask |
| `NG: COL / NG / NUC / WAT / WND / SUN` | SPP GenMix coal / gas / nuclear / hydro / wind / solar | `fuel_stale_mask` (the #7287 rule) |
| `NG: OIL`, `NG: OTH` | EIA's value kept, flagged | `fuel_stale_mask` |
| any other `NG:` column with a stale hour | raises | — |

Wind / solar are asserted bit-identical to `repair_renewable_gen` (the LP input) in every year.

## 2. Masks, basis and declared gaps

Hours repaired (iso_measured) / kept stale, per year. Provenance (run-length encoded): `data/uc_spp_bench_2026_10_20/benchmark_stale_provenance_runs.csv`.

| Column | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Demand / TI / Net gen | 828 (TI 1 kept) | 47 | 142 | 9 | 36 | 510 | 698 |
| NG: COL | 905 + 8 kept | 46 | 143 | 0 | 33 | 257 | 670 |
| NG: NG | 817 + 8 kept | 46 | 143 | 0 | 33 | 257 | 672 |
| NG: WND | 820 + 8 kept | 46 | 142 | 0 | 33 | 261 | 671 |
| NG: WAT | 852 + 8 kept | 50 | 151 | 57 | 95 | 326 | 688 |
| NG: NUC | 5,089 + 11 kept | 4,320 + 1 | 4,385 + 1 | 2,035 | 3,558 | 3,880 | 1,810 + 4 |
| NG: OIL (kept) | 1,180 | 478 | 1,241 | 319 | 352 | 797 | 1,493 |
| NG: OTH (kept) | 5,403 | 3,463 | 2,096 | 1,681 | 1,829 | 1,569 | 2,016 |

2024: 253 of the 510 demand-mask hours are sub-BA-only freezes; the BA fuel columns are live there and are not touched.

**Basis (rule 14), GenMix / EIA-930 outside the mask, 2019–2025.**

| Column | Ratio | r | Treatment |
|---|---|---|---|
| coal | 0.98–1.00 | 0.99–1.00 | GenMix |
| gas | 1.00–1.01 | 0.99–1.00 | GenMix |
| nuclear | 0.99–1.01 | 0.90–1.00 | GenMix |
| hydro | 0.99–1.02 | 0.97–1.00 | GenMix |
| wind / solar | 1.00–1.01 / 1.02–1.10 | ≥ 0.97 | GenMix (datafix §3) |
| oil | **0.28–2.53** | 0.66–0.95 | kept, flagged (iv) |
| other (+ waste, waste heat) | **0.79–1.00** | 0.62–0.99 | kept, flagged (iv) |

**Declared gaps** (constants.py; every other gap raises):

- **(iv) `NG: OIL`, `NG: OTH` kept.** A different aggregate, not the same quantity. Masked-hour EIA energy ≤ 0.019 TWh/yr (oil),
  ≤ 0.21 TWh/yr (other); GenMix differs from it by ≤ 0.023 TWh/yr. Neither is hourly-scored. Their only scored use is the annual
  fossil-reconcile target and the gas fold-in, where these bounds are ≤ 0.15 % of the target.
- **(v) 9 nuclear hours kept** (2019 ×3, 2020, 2021, 2025 ×4). GenMix nuclear is blank there.
- **Ruling (iii) window applied to every GenMix column.** 2019-03-29 09:00–16:00Z: GenMix is blank for all fuels; EIA's stale value
  is kept, as (iii) already does for wind and solar.

**Nuclear is a screen false positive outside the record freeze.** The fleet holds exact MW for days. The one screen flags it
(1,810–5,089 h/yr), and GenMix serves it, agreeing within a median 1–5 MW. Net effect ≤ 44 GWh/yr. This is stated, not tuned
around (rule 19: no second screen).

## 3. Benchmark effect (annual TWh, before → after, ΔGWh)

| Year | coal | gas | wind | solar | hydro | nuclear | net gen | interchange |
|---|---|---|---|---|---|---|---|---|
| 2019 | 94.12 → 95.57 (+1,446) | 69.18 → 70.53 (+1,353) | 77.03 → 74.53 (−2,503) | −43 | −312 | −9 | +353 | −56 |
| 2020 | +66 | +81 | −74 | +3 | +15 | −26 | +95 | −7 |
| 2021 | +46 | +40 | +613 | 0 | +4 | −35 | +690 | +83 |
| 2022 | 0 | 0 | 0 | 0 | 0 | +5 | +7 | +1 |
| 2023 | −4 | −21 | +64 | −2 | −5 | +6 | +29 | +18 |
| 2024 | −132 | −229 | +191 | −1 | +20 | −44 | −176 | +116 |
| 2025 | 87.70 → 87.18 (−524) | 75.95 → 75.68 (−265) | +167 | 2.35 → 2.10 (−250) | −94 | −12 | −880 | +143 |

Oil and other: 0 by construction. 2019 is the November–December freeze. The benchmark now carries the +2.8 TWh of thermal energy that
UC-SPP-CONTROL §4 found the model dispatching against SPP's own load and wind.

## 4. Re-score (zero LP, `calibration_verdict.determine_from_artifacts`, rubric unchanged)

**Method.**
- **Keeper** (`2026-10-03-closeout-spp-nuc-keeper`, the designated keeper at scoring time):
  - before = committed artifacts;
  - after = bench parts re-rendered under the repair, plus payload `fuelRows` recomputed from the committed `class_hourly` /
    `unit_marginal` sidecars.
  - The recompute reproduces every committed keeper fuelRow exactly on the unrepaired benchmark (asserted).
- **Control** (`uc_spp_control_span`, PR #7290, root frames from its legs): a full local re-registration before and after. Not
  committed.
- **Cross-check:** the patch method applied to the control's "before" render gives the full "after" render exactly (0 of all
  records differ).
- **Bench parts:** the "before" render reproduces every committed SPP bench part byte-for-byte.

**C4 hourly dispatch r (gas / coal), before → after.** All PASS before and after (floor r ≥ 0.85).

| Year | keeper gas | keeper coal | control gas | control coal |
|---|---|---|---|---|
| 2019 | 0.966 → 0.937 | 0.953 → 0.917 | 0.938 → **0.966** | 0.919 → **0.954** |
| 2020 | 0.942 → 0.942 | 0.946 → 0.945 | 0.940 → 0.942 | 0.946 → 0.946 |
| 2021 | 0.957 → 0.946 | 0.929 → 0.925 | 0.947 → 0.957 | 0.923 → 0.928 |
| 2022 | 0.962 → 0.962 | 0.928 → 0.928 | 0.962 → 0.962 | 0.928 → 0.928 |
| 2023 | 0.962 → 0.962 | 0.951 → 0.951 | 0.962 → 0.962 | 0.951 → 0.951 |
| 2024 | 0.954 → 0.944 | 0.916 → 0.909 | 0.945 → 0.957 | 0.912 → 0.917 |
| 2025 | 0.954 → 0.916 | 0.919 → 0.890 | 0.930 → **0.960** | 0.882 → **0.920** |

2022 gas stays FAIL in both bundles (NRMSE 0.313, unchanged).

**Other criteria.**
- **C1 (fuel-mix).** Magnitudes only. Largest move: 2025 COAL_PRB +7.39 → +7.75 TWh (keeper), still PASS. The 2023–25 actuals move
  ≤ 0.5 % because the fossil reconcile still fires against the repaired e930 target.
- **C1 FAIL set unchanged.** 2021/2022 CC_REGULAR and COAL_PRB.
- **C3a.** 2024 −11.2 → −11.3 % (FAIL → FAIL); 2025 −4.3 → −4.5 % (PASS).
- **C3b.** 2024 0.216 → 0.217 (FAIL → FAIL).
- **C2, C3c, C6, C8:** unchanged.

Full records: `data/uc_spp_bench_2026_10_20/rescore.json` (keeper, probe output) and `rescore_full_render_control_and_keeper.json`.

**Not committed:**
- **Bench parts and the keeper payload.** `frontend/data/backcast/bench/SPP/*` and `runs/<keeper>.js` are dashboard artifacts, and
  UC-SPP-PROMOTE owns them now. They refresh at the next SPP registration, to the "after" numbers above.
- **Scoring the new keeper.** UC-SPP-PROMOTE had not landed when this was scored. The control column above is that bundle.

## 5. Rule 23 derives that read the frame, and re-key

| Artifact | Reads | Action |
|---|---|---|
| `campd-unit-outages-short-netloadmask-SPP.csv` (1–5 day, read by the SPP keeper) | `high_load_mask` | **Re-derived** at its recorded invocation. The identity path reproduces the committed bytes. Repaired: 460 → 459 rows; 10 coal windows added, 11 dropped (2019 ×6, 2020, 2021, 2023 ×2, 2024 ×5, 2025 ×6) |
| `campd-unit-outages-netloadmask-SPP.csv` (≥ 5 day) | `high_load_mask` | Not re-derived: repaired = identity at HEAD (0 rows differ) |
| `campd-partial-outages-netloadmask-SPP.csv` | `high_load_mask` | Unchanged (0 rows, reproduces) |
| `actual_lmp.json` SPP 2023–25 `*_lw` | `load_demand` (#7287) | **Re-derived** (`--lw-retrofit --isos SPP`). rt_lw 25.13 → 25.14 / 25.45 → 25.47 / 28.60 → 28.66. 2019–22 carry no `*_lw` by design; none added |
| `derive_import_tranches` (reads benchmark interchange) | benchmark | No SPP output on disk; nothing to re-derive |

**High-net-load hours flipped by the repaired mask:** 246 / 29 / 11 / 0 / 22 / 116 / 206 (2019–2025).

**FINDING (not repaired; report, don't repair).** At HEAD, the identity re-derive of the **≥ 5-day** `-netloadmask-` extract does not
reproduce the committed file: 6,464 vs 6,581 rows (483 / 600 rows unmatched). The cause predates this lane and is independent of the
repair: repaired = identity at HEAD. The file was not touched.

**Re-key.**
- SolveEpoch `2026-10-20a`: SPP, backcast, `requires="unit_outage_netload_mask_repair"`. Ledger entry in `results/cache.py`.
- The benchmark and `*_lw` are scoring-only and in no solve key.
- **G-DRIFT:**
  - SPP keeper: LIVE.
  - UC-SPP-CONTROL bundle: LIVE (its outage input moves in 21 short coal windows).
  - Every other ISO: INERT (the registry holds SPP only; `repair_eia930_frame` returns the same object for any other ISO, tested).

## 6. Tests

`tests/unit/data/test_stale_snapshot_frame.py` (12 tests, tmp CLEAN_DIR, synthetic ISO):
- identity for an unregistered ISO, for a frame without a clock, and with no mutation of the input;
- fuel / demand / interchange / net-generation repair;
- wind bit-identical to the LP-input repair;
- a flat column screened and served measured;
- a kept-stale column flagged;
- an undeclared stale column raises;
- a blank mix raises unless the hour is ruled;
- rows matched by UTC stamp, not position;
- tz-aware stamps.

Fast lane: 11,883 passed.

## 7. Desk questions (none blocks the merge; no determination changes)

- **(a)** `NG: OIL` / `NG: OTH`: keep EIA's stale value, flagged (done; measured > stale), or drop the masked hours from the reconcile
  target? Dropping them would itself be an estimate of the annual, and the bound is ≤ 0.15 % of the target.
- **(b)** Confirm extending ruling (iii)'s 2019-03-29 window to every GenMix column, and the 9 GenMix-blank nuclear hours (v).
- **(c)** Sequencing with UC-SPP-PROMOTE. The SPP bench parts and the keeper payload need one zero-LP re-render (`dashboard_add_run`
  on the designated keeper) to adopt this benchmark. The promoted control is LIVE on epoch `2026-10-20a` (short outage windows).
- **(d)** The ≥ 5-day `-netloadmask-` reproducibility drift (§5) needs an owner. It is outside this lane.

## 8. Reproduce

```
PYTHONPATH=.:src uv run python scripts/probes/spp_bench_stale_rescore.py --out /tmp/r.json \
    --provenance /tmp/prov.csv --after-bench <re-rendered bench/SPP dir> --run-id 2026-10-03-closeout-spp-nuc-keeper
uv run python scripts/data/derive_campd_unit_outages.py --iso SPP --years 2019 2020 2021 2022 2023 2024 2025 \
    --high-load-pctl 0.85 --fullstop-override-days 5 --fullstop-override-cf 0.02 \
    --short-windows --min-outage-days 1 --min-inmerit-hours 6 --out <csv>
PYTHONPATH=.:src uv run python scripts/data/derive_actual_lmp.py --lw-retrofit --isos SPP --years 2023 2024 2025
```
