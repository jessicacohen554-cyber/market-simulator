# PRECOMMIT — UC-SPP-CONTROL: the SPP keeper recipe re-solved on the R22/R23 data (2026-10-19)

Lane UC-SPP-CONTROL, chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) under owner ruling **R25**. Branch `claude/uc-spp-control`
from `main` `c92e40270b500d06887c9ad49e6059182195b0a8` (#7287, SolveEpoch `2026-10-18b`). DATA PROFILE: spp.
**Written and pushed before any shard exists.** Nothing here is registered or promoted; promotion is a separate owner decision.

## 0. What and why

- **Recipe:** keeper `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span`, replayed **unchanged**
  (`replay_keeper.py … --years <y>`, no `--set`). Seven legs, 2019–2025, one shard each (rule 36).
- **Purpose:** the control for every later SPP arm. The keeper bundle can no longer serve as the control (rule 29(b)) because the
  datafix is LIVE on its inputs (§1).
- **DOF (rule 21):** zero parameters added or moved. The authorized price tuning (`offer_curve_by_group`, all bands 0.93) rides unchanged.
  The new bundle's ledger gains the `SPP_STALE_SNAPSHOT_REPAIR` data-QA note (`build_dof_ledger.py::data_qa_entries`), not a free parameter.

## 1. G-DRIFT `8c3ea461` (keeper solve) → `c92e4027` (zero LP; backcast path only)

`8c3ea461…` is not in `main`'s history (shard SHA). Its drift to `60e7c6fa` is already classified, hunk by hunk, all **INERT** for the
keeper recipe (UC off):

| span | classified in |
|---|---|
| `ae224faf → 6cf95135 → 9cb0eecb → 580c4fbf → 2dd69d5a` | `ucmilp/PRECOMMIT-ucmilp-spp-b-2026-10-09.md` §8 + Add. C; `ucmilp/PRECOMMIT-ucmilp3-spp-2026-10-14.md` §1.1 + Add. A |
| `2dd69d5a → 7dbfe20f` | `ucmilp/PRECOMMIT-ucmilp4-spp-2026-10-15.md` §1.1 |
| `7dbfe20f → 41cd55dc → 60e7c6fa` | `ucmilp/PRECOMMIT-ucmilp5-spp-2026-10-18.md` §1.4 |

**New here: `60e7c6fa → c92e4027`** (6 commits). Five (#7282–#7286) touch only `docs/`. The sixth, #7287, changes:

| file(s) | hunk | control |
|---|---|---|
| `data/stale_runs.py`, `data/stale_snapshot.py` (new); `constants.py` `SPP_STALE_*` | detector + SPP repair registry; declared gaps | **LIVE** (the datafix) |
| `data/eia930/demand.py` `_load_spp_hourly_demand`, `load_zone_weights` | masked hours ← SPP HOURLY_LOAD (load, zonal shares) | **LIVE** |
| `data/eia930/envelopes.py` `spp_net_interchange` | masked hours ← measured seam legs | **LIVE** |
| `data/eia930/actuals.py` `load_eia_hourly_renewable_gen` | frozen `NG: WND`/`NG: SUN` hours ← SPP GenMix | **LIVE** (wind/solar input) |
| `data/commitment_demand.py` | UC actual repaired | **INERT** (read only by the UC stage; UC off) |
| `solve_surface.py` / `_declared.py` epoch `2026-10-18b`, `results/cache.py` comment | re-key | re-keys (expected) |
| `data/raw/reference/spp_curtailment_share.csv` (rule-23 re-derive) | ceiling shape | **INERT**: read only under `spp_curtailment_ceiling`, which the keeper leaves `false` |
| `scripts/build_dof_ledger.py` | data-QA note | scoring/attestation only |
| curate/fetch scripts, `scripts/lib/{iso_area_load,iso_genmix,counterparty_interchange,curate_local_year}`, `clean_profiles.py`, `regenerate_clean.py`, schemas, raw intake | the three new datatypes | LIVE via the data they produce (rows above) |
| `render_data_dictionary.py`, `data-dictionary.md`, READMEs, `scripts/probes/spp_stale_snapshot_effect.py` | docs / probe | off-path |

No `iso_configs.py`, `scenarios.py`, `model/*`, `pipeline/*`, fleet/offer `data/*` or orchestrator hunk. **The only LIVE delta is the
R22/R23 input repair.** Every control-vs-keeper difference is attributed to it.

## 2. Input deltas (zero LP; `RESULT-uc-spp-datafix-2026-10-18.md` §2, before = keeper inputs)

Net-load Δ = Δdemand − Δwind − Δsolar (GWh). Masked months from the committed provenance CSV.

| year | masked h (demand) | months | Δdemand N+S | Δwind | Δsolar | **Δnet load** | mean \|Δdemand\| in masked h (MW, N / S) |
|---|---|---|---|---|---|---|---|
| 2019 | 828 | Mar–Jun, Nov, **Dec 480** | +356 | −2,503 | −43 | **+2,902** | 1,286 / 1,186 |
| 2020 | 47 | Feb, Apr | +93 | −74 | +3 | +164 | 1,144 / 1,280 |
| 2021 | 142 | Mar, **Aug 132** | +691 | +613 | 0 | +78 | 4,071 / 3,150 |
| 2022 | 9 | Dec | +7 | 0 | 0 | +7 | 532 / 744 |
| 2023 | 36 | Jul, Aug, Dec | +29 | +64 | −2 | −33 | 1,472 / 1,433 |
| 2024 | 510 | Jan–Apr, Oct, Dec | +235 | +191 | −1 | +45 | 991 / 1,125 |
| 2025 | 698 | Feb–Jul, Oct, Dec | −622 | +167 | −250 | **−539** | 1,549 / 1,925 |

No zone-year peak moves. 2021's masked hours are August, not Winter Storm Uri.

## 3. Expectations (ex ante, from §2; not bars)

1. **2019:** +2.9 TWh net load, mostly December → thermal output up, mean LMP up. C3a 2019 (keeper +12.3 %, FAIL) is expected to rise.
2. **2025:** −0.54 TWh net load → mean LMP down slightly. C3a 2025 (keeper inside band) may move toward the lower edge.
3. **2020, 2022, 2023:** ≤ 47 masked hours, |Δnet| ≤ 0.17 TWh → |ΔC3a| ≤ 2 pp, |ΔC3b| ≤ 0.02, C1 verdicts unchanged.
4. **2021, 2024:** net-annual ≈ 0 but 132 / 510 h of 1–4 GW hourly error removed → hourly redistribution; C3b and C4 may move,
   annual C1/C3a ≈ unchanged. No sign predicted.
5. **Unserved:** keeper 0 MWh in every year. Expected 0.
6. **Determination:** NOT-YET, as the keeper (C1 2021/22, C3a, C3b, C3c, C4 2022 failures are not data-hour driven).

## 4. Readings (fixed ex ante)

Per year, **keeper → control**, from `calibration_verdict.py` (rubric as on `main`, unchanged) over the composed span
`results/calibration/uc_spp_control_span`, plus `legitimacy_diagnostics.py`:

- C1 per class (CC_REGULAR, COAL_PRB, COAL_LIGNITE, ST_GAS, CT_PEAKER), C2, C3a, C3b, C3c, C4, C5a, C6, C8, determination;
- unserved MWh and slack hours; Σ dump MWh;
- LMP MAE and bias ($/MWh) vs the rubric's RT benchmark, annual and in masked vs unmasked hours;
- attribution: Δ in masked hours vs Δ in unmasked hours (a non-trivial unmasked-hour Δ in a year with ≤ 47 masked hours is
  reported as unexplained and sent to UC-DESK, since the drift audit predicts none).

## 5. Gates, kills, hard stops

- **Gates = the rubric as is** (rule 37). No bar is set on the control: it is a measurement, not a candidate. Every year is scored.
- **Hard stops (any ⇒ stop, report to UC-DESK, no repair):** a config change vs the keeper recipe in any leg's `run_config.json`;
  a shard OOM, or > 20 min with no artifact; a leg whose printed ceiling + swap is < **10.6 GiB** (SPP memory gate, r16 ruling 1) or whose
  cgroup peak exceeds it; any data that reads stale/estimated beyond the declared gaps (`SPP_STALE_OMITTED_LEGS`,
  `SPP_STALE_KEPT_INTERCHANGE_HOURS_UTC`, `SPP_STALE_KEPT_RENEWABLE_WINDOWS_UTC`).
- **Shards:** `scripts/shard_prompt.py --iso SPP --all-years --sha <this commit> --lane uc-spp-control --bundle
  results/calibration/closeout_spp_nuc_span --budget 20`, plus a memory-gate appendix. Legs `results/calibration/uc_spp_control_<y>`,
  branches `claude/uc-spp-control-<y>`; composed span `results/calibration/uc_spp_control_span`. Full bundles pushed (rule 34),
  incl. `dispatch/<y>_P1.parquet` and `hourly/unit_marginal_<y>.parquet`.

## 6. Outputs

`RESULT-uc-spp-control-2026-10-19.md` beside this file; the composed span on `main` via a `.gitignore` negation (rule 34). **No**
dashboard registration, keeper designation, `keepers/SPP.json` or `calibration-complete.json` edit. Mechanism-matrix SPP shard touched
only if a verdict changes.
