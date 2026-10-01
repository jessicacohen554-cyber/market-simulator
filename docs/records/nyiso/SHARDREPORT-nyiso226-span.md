# SHARDREPORT — nyiso-226 span shard: 2023–2025 arm numbers

**Shard for session:** nyiso-226 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Rule 32 `[R-SHARD]`.** This document carries every number this shard will ever cite; the
bundle `results/calibration/nyiso226_span/` is **gitignored** (rule 29(c) / rule 31
`[R-RETAIN]`), stays on the shard's local disk, and is **not deleted**.

**This shard scores nothing, compares nothing and recommends nothing.** Every verdict is the
parent's (rule 32(d)).

---

## 0. Hard stops — all passed

| stop | required | observed |
|---|---|---|
| 1 | `HEAD` = `ec3374d2ed7e8e9721e58b0d65c913656373341e` | matched exactly; no rebase, no pull, no sync |
| 2 | `nyiso_fuelvintage_A/meta.json` `git_sha` = `da2e7076` | `da2e7076`, `iso NYISO`, `years [2023, 2024, 2025]`; bundle not modified |
| 3 | PRECOMMIT §1 + span ADDENDUM read | both read before any action |

## 1. The arm as applied

One cell of `data/raw/reference/reliability_floor_coeffs_NYISO.csv`, line 6
(`NYISO,NYC,ST_GAS,tmax,-50.0`): `floor_pct` **0.175 → 0.16629202320362052**. Nothing else in
the file changed — `git diff --stat` reads `1 insertion(+), 1 deletion(-)`.

**One process note, so the parent can audit the bytes.** The CSV has **CRLF** line endings. A
first edit made in Python text mode silently rewrote every line ending to LF (`47 insertions,
47 deletions`). That was reverted with `git checkout --` and the edit redone in **binary mode**,
which preserves the CRLF and touches exactly one line. The committed diff is the binary one.

Mandated verification, verbatim:

```
ARM floor_pct = 0.16629202320362052 enabled= True distribution= pro_rata
rows total 46
```

No `ScenarioConfig` delta, no cache-key delta, no `src/` or `scripts/` edit.

## 2. Timing — inside the 20-minute ceiling

Single invocation, `--years 2023 2024 2025`, years sequential (rule 12 `[R-PARALLEL]`).

| leg | wall clock |
|---|---|
| fleet build + 2023 | start → 17:15:45 |
| 2024 | 17:15:45 → 17:22:06 (**6 min 21 s**) |
| 2025 | 17:22:06 → 17:27:53 (**5 min 47 s**) |
| **total (`real`)** | **18 m 20.834 s** (`user` 14 m 02.499 s, `sys` 4 m 30.112 s) |

Exit code **0**. The 20-minute stop condition did **not** fire; all three years completed, so no
continuation shard is owed.

## 3. Scorer — **ALL FIVE INVOCATIONS FAILED, IDENTICALLY**

Run read-only, `--write-metrics` never passed. Every one of the five returned, verbatim:

```
could not resolve a registered run from 'results/calibration/nyiso226_span' (no registry sidecar and no bundle match).
```

— for the bare call, `--json`, `--years 2023`, `--years 2024` and `--years 2025` alike.

**This is structural, not a transient error, and it is NOT the `metrics.json` absence the
addendum anticipated.** `calibration_verdict.py --help` states it "reads a run's COMMITTED
artifacts only — the registry sidecar, the run payload, the per-(ISO, year) benchmark parts…".
Those artifacts are created by **registration**, which rule 32(c) item 6 forbids this shard from
performing (`dashboard_add_run.py` and everything under `frontend/data/backcast/**` are the
parent's, once, at the end). So **an unregistered bundle cannot be scored by any flag
combination available to a shard.**

Consequence for the parent, stated plainly: **C3a / C3b are again unmeasured**, and the `S4` gap
that `ADDENDUM …-span-authorized` §2 set out to close is **not closed** by instructing the shard
to run the scorer — the missing precondition was registration, not the invocation. The scorer
was **not repaired and not worked around** (rule 32(c) item 6; a shard that repairs
infrastructure is a failure). §4 and §5 below are the raw numbers the parent can score from.

## 4. Class energy and system, per year

### 2023 — class TWh
```
      COAL_PRB  0.000000
      COAL_BIT  0.000000
           oil  0.149817
         solar  0.279821
     CT_PEAKER  0.398197
       biomass  0.839526
        ST_CHP  1.372494
        CT_CHP  1.543037
         OTHER  2.197331
          wind  4.590724
        ST_GAS  9.731508
        CC_CHP  15.926029
        import  23.336016
         hydro  26.615767
       nuclear  27.487143
    CC_REGULAR  33.843945
         TOTAL  148.311356
  load-weighted mean LMP 33.675992 | unweighted 33.043276 | p95 50.6789 | max 326.4235
  demand TWh 147.048845 | slack max 0.000000 | dump max 0.000000
```

### 2024 — class TWh
```
      COAL_PRB  0.000000
      COAL_BIT  0.000000
     CT_PEAKER  0.371614
           oil  0.443568
         solar  0.586129
       biomass  0.759742
        ST_CHP  1.131514
        CT_CHP  1.200273
         OTHER  2.201389
          wind  6.011645
        ST_GAS  8.503434
        CC_CHP  19.587124
        import  20.707304
         hydro  26.739035
       nuclear  26.953211
    CC_REGULAR  36.984173
         TOTAL  152.180145
  load-weighted mean LMP 40.178154 | unweighted 38.747417 | p95 60.1522 | max 217.8642
  demand TWh 150.516661 | slack max 0.000000 | dump max 0.000000
```

### 2025 — class TWh
```
      COAL_PRB  0.000000
      COAL_BIT  0.000000
       biomass  0.672388
         solar  0.981276
           oil  1.284010
     CT_PEAKER  1.319794
        ST_CHP  1.449799
        CT_CHP  1.685867
         OTHER  1.948275
          wind  7.048691
        ST_GAS  9.304146
        import  19.357996
        CC_CHP  20.405596
         hydro  24.058859
       nuclear  28.341602
    CC_REGULAR  35.348652
         TOTAL  153.206955
  load-weighted mean LMP 61.623478 | unweighted 58.770121 | p95 122.2831 | max 323.5304
  demand TWh 151.589750 | slack max 0.000000 | dump max 0.000000
```

**`slack max` and `dump max` are 0.000000 in all three years** — no unserved energy, no dumping.

## 5. Legitimacy diagnostics

`years [2023, 2024, 2025]`

| diagnostic | passed |
|---|---|
| D1 | True |
| D2 | True |
| D4 | **False** |
| D5 | True |
| D9 | True |
| D10 | True |

The solve emitted, verbatim:
`WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8 score from its contents — see the report above)`

D-9 overlay quarantine **PASS** (all five checks). D-10 free-class-only rescore **PASS** — all
6 wind/solar (year, fuel) rows `delivered_pinned`, advisory-only.

### D2 rows (all, verbatim)
```
{'year': 2023, 'class': '', 'mechanism': 'nuclear_mustrun', 'forced_twh': 27.4871, 'class_total_twh': 35.3716, 'share_of_class': 0.7771}
{'year': 2023, 'class': '', 'mechanism': 'firm_import', 'forced_twh': 7.884, 'class_total_twh': 35.3716, 'share_of_class': 0.2229}
{'year': 2023, 'class': 'CC_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.013, 'class_total_twh': 15.9532, 'share_of_class': 0.0008}
{'year': 2023, 'class': 'CC_REGULAR', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.3574, 'class_total_twh': 31.9738, 'share_of_class': 0.0112}
{'year': 2023, 'class': 'CT_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0002, 'class_total_twh': 2.855, 'share_of_class': 0.0001}
{'year': 2023, 'class': 'ST_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0078, 'class_total_twh': 0.0676, 'share_of_class': 0.1147}
{'year': 2023, 'class': 'ST_GAS', 'mechanism': 'reliability_floor', 'forced_twh': 1.8716, 'class_total_twh': 11.773, 'share_of_class': 0.159}
{'year': 2023, 'class': 'ST_GAS', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.007, 'class_total_twh': 11.773, 'share_of_class': 0.0006}
{'year': 2023, 'class': 'hydro', 'mechanism': 'hydro_min_flow', 'forced_twh': 7.7249, 'class_total_twh': 26.6158, 'share_of_class': 0.2902}
{'year': 2024, 'class': '', 'mechanism': 'nuclear_mustrun', 'forced_twh': 26.9532, 'class_total_twh': 34.8381, 'share_of_class': 0.7737}
{'year': 2024, 'class': '', 'mechanism': 'firm_import', 'forced_twh': 7.884, 'class_total_twh': 34.8381, 'share_of_class': 0.2263}
{'year': 2024, 'class': 'CC_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0581, 'class_total_twh': 19.6738, 'share_of_class': 0.003}
{'year': 2024, 'class': 'CC_REGULAR', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.1134, 'class_total_twh': 35.2778, 'share_of_class': 0.0032}
{'year': 2024, 'class': 'CT_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0023, 'class_total_twh': 2.2658, 'share_of_class': 0.001}
{'year': 2024, 'class': 'ST_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0251, 'class_total_twh': 0.0889, 'share_of_class': 0.2823}
{'year': 2024, 'class': 'ST_GAS', 'mechanism': 'reliability_floor', 'forced_twh': 2.1733, 'class_total_twh': 10.6008, 'share_of_class': 0.205}
{'year': 2024, 'class': 'ST_GAS', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.022, 'class_total_twh': 10.6008, 'share_of_class': 0.0021}
{'year': 2024, 'class': 'hydro', 'mechanism': 'hydro_min_flow', 'forced_twh': 7.6756, 'class_total_twh': 26.739, 'share_of_class': 0.2871}
{'year': 2025, 'class': '', 'mechanism': 'nuclear_mustrun', 'forced_twh': 28.3416, 'class_total_twh': 36.2308, 'share_of_class': 0.7823}
{'year': 2025, 'class': '', 'mechanism': 'firm_import', 'forced_twh': 7.884, 'class_total_twh': 36.2308, 'share_of_class': 0.2176}
{'year': 2025, 'class': 'CC_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0473, 'class_total_twh': 20.6512, 'share_of_class': 0.0023}
{'year': 2025, 'class': 'CC_REGULAR', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.1543, 'class_total_twh': 34.0546, 'share_of_class': 0.0045}
{'year': 2025, 'class': 'CT_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.003, 'class_total_twh': 3.1154, 'share_of_class': 0.001}
{'year': 2025, 'class': 'ST_CHP', 'mechanism': 'chp_steam', 'forced_twh': 0.0119, 'class_total_twh': 0.0902, 'share_of_class': 0.1319}
{'year': 2025, 'class': 'ST_GAS', 'mechanism': 'reliability_floor', 'forced_twh': 2.0983, 'class_total_twh': 11.7553, 'share_of_class': 0.1785}
{'year': 2025, 'class': 'ST_GAS', 'mechanism': 'nyiso_gas_commitment_bridge', 'forced_twh': 0.0128, 'class_total_twh': 11.7553, 'share_of_class': 0.0011}
{'year': 2025, 'class': 'hydro', 'mechanism': 'hydro_min_flow', 'forced_twh': 6.5982, 'class_total_twh': 24.0589, 'share_of_class': 0.2743}
```

The arm's own row, `ST_GAS × reliability_floor`, isolated for convenience (still the shard's
numbers, no comparison drawn):

| year | forced TWh | class total TWh | share of class |
|---|---|---|---|
| 2023 | 1.8716 | 11.7730 | 0.1590 |
| 2024 | 2.1733 | 10.6008 | 0.2050 |
| 2025 | 2.0983 | 11.7553 | 0.1785 |

### D4 `reliability_floor` rows (all, verbatim)
```
{'year': 2023, 'check': 'window', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '', 'floored_twh': 1.8716, 'offwindow_twh': 0.0, 'offwindow_share': 0.0, 'binding_hours': '', 'measured_median_mw': '', 'measured_zero_share': '', 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2480', 'floored_twh': 0.0015, 'offwindow_twh': '', 'offwindow_share': 0.0008, 'binding_hours': 157, 'measured_median_mw': 0.0, 'measured_zero_share': 1.0, 'verdict': 'FAIL'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2490', 'floored_twh': 0.3101, 'offwindow_twh': '', 'offwindow_share': 0.1657, 'binding_hours': 3227, 'measured_median_mw': 96.634, 'measured_zero_share': 0.3812, 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2511', 'floored_twh': 0.4028, 'offwindow_twh': '', 'offwindow_share': 0.2152, 'binding_hours': 7685, 'measured_median_mw': 135.391, 'measured_zero_share': 0.0513, 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2516', 'floored_twh': 0.9082, 'offwindow_twh': '', 'offwindow_share': 0.4853, 'binding_hours': 7819, 'measured_median_mw': 218.974, 'measured_zero_share': 0.1219, 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2625', 'floored_twh': 0.0197, 'offwindow_twh': '', 'offwindow_share': 0.0105, 'binding_hours': 165, 'measured_median_mw': 521.382, 'measured_zero_share': 0.0788, 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '8006', 'floored_twh': 0.0009, 'offwindow_twh': '', 'offwindow_share': 0.0005, 'binding_hours': 18, 'measured_median_mw': 254.649, 'measured_zero_share': 0.0, 'verdict': 'pass'}
{'year': 2023, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '8906', 'floored_twh': 0.2283, 'offwindow_twh': '', 'offwindow_share': 0.122, 'binding_hours': 5546, 'measured_median_mw': 0.0, 'measured_zero_share': 0.511, 'verdict': 'FAIL'}
{'year': 2024, 'check': 'window', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '', 'floored_twh': 2.1733, 'offwindow_twh': 0.0, 'offwindow_share': 0.0, 'binding_hours': '', 'measured_median_mw': '', 'measured_zero_share': '', 'verdict': 'pass'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2480', 'floored_twh': 0.0002, 'offwindow_twh': '', 'offwindow_share': 0.0001, 'binding_hours': 23, 'measured_median_mw': 0.0, 'measured_zero_share': 1.0, 'verdict': 'FAIL'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2490', 'floored_twh': 0.2, 'offwindow_twh': '', 'offwindow_share': 0.092, 'binding_hours': 3435, 'measured_median_mw': 96.617, 'measured_zero_share': 0.1249, 'verdict': 'pass'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2511', 'floored_twh': 0.4641, 'offwindow_twh': '', 'offwindow_share': 0.2135, 'binding_hours': 6889, 'measured_median_mw': 101.554, 'measured_zero_share': 0.0793, 'verdict': 'pass'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2516', 'floored_twh': 1.1692, 'offwindow_twh': '', 'offwindow_share': 0.538, 'binding_hours': 7064, 'measured_median_mw': 312.712, 'measured_zero_share': 0.0011, 'verdict': 'pass'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2625', 'floored_twh': 0.0345, 'offwindow_twh': '', 'offwindow_share': 0.0159, 'binding_hours': 191, 'measured_median_mw': 384.767, 'measured_zero_share': 0.1623, 'verdict': 'pass'}
{'year': 2024, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '8906', 'floored_twh': 0.3054, 'offwindow_twh': '', 'offwindow_share': 0.1405, 'binding_hours': 5561, 'measured_median_mw': 81.217, 'measured_zero_share': 0.4147, 'verdict': 'pass'}
{'year': 2025, 'check': 'window', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '', 'floored_twh': 2.0983, 'offwindow_twh': 0.0, 'offwindow_share': 0.0, 'binding_hours': '', 'measured_median_mw': '', 'measured_zero_share': '', 'verdict': 'pass'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2490', 'floored_twh': 0.2028, 'offwindow_twh': '', 'offwindow_share': 0.0966, 'binding_hours': 3257, 'measured_median_mw': 158.05, 'measured_zero_share': 0.062, 'verdict': 'pass'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2511', 'floored_twh': 0.4496, 'offwindow_twh': '', 'offwindow_share': 0.2143, 'binding_hours': 6775, 'measured_median_mw': 109.096, 'measured_zero_share': 0.022, 'verdict': 'pass'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2516', 'floored_twh': 1.1546, 'offwindow_twh': '', 'offwindow_share': 0.5503, 'binding_hours': 6787, 'measured_median_mw': 328.443, 'measured_zero_share': 0.0043, 'verdict': 'pass'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '2625', 'floored_twh': 0.0337, 'offwindow_twh': '', 'offwindow_share': 0.016, 'binding_hours': 235, 'measured_median_mw': 509.27, 'measured_zero_share': 0.0, 'verdict': 'pass'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '8006', 'floored_twh': 0.001, 'offwindow_twh': '', 'offwindow_share': 0.0005, 'binding_hours': 17, 'measured_median_mw': 0.0, 'measured_zero_share': 0.5882, 'verdict': 'FAIL'}
{'year': 2025, 'check': 'unit-conduct', 'floor': 'reliability_floor × ST_GAS', 'window': 'h0-23', 'plant': '8906', 'floored_twh': 0.2567, 'offwindow_twh': '', 'offwindow_share': 0.1223, 'binding_hours': 4225, 'measured_median_mw': 80.976, 'measured_zero_share': 0.1917, 'verdict': 'pass'}
```

**Every `check: window` row passes** — `offwindow_twh 0.0`, `offwindow_share 0.0` in all three
years, as a `-50.0 °C` threshold limb binding h0-23 must.

### The complete D4 FAIL set (whole artifact, not only `reliability_floor`)

5 FAIL rows in total, all `unit-conduct`; `D4.gates` is `null`.

| year | floor | check | plant |
|---|---|---|---|
| 2023 | `reliability_floor × ST_GAS` | unit-conduct | 2480 |
| 2023 | `reliability_floor × ST_GAS` | unit-conduct | 8906 |
| 2024 | `nyiso_gas_commitment_bridge × CC_REGULAR` | unit-conduct | 54574 |
| 2024 | `reliability_floor × ST_GAS` | unit-conduct | 2480 |
| 2025 | `reliability_floor × ST_GAS` | unit-conduct | 8006 |

Plant **8906 (Astoria)** fails 2023 only (`measured_median_mw 0.0`, `measured_zero_share 0.511`,
5,546 binding hours, 0.2283 floored TWh) and **passes** 2024 and 2025. Plant 2480 fails on
0.0015 / 0.0002 TWh and 8006 on 0.0010 TWh.

## 6. Warnings and errors observed

- The five scorer failures in §3 (verbatim above).
- `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8 score from its contents — see the report above)`.
- Routine fleet-build reconciliation warnings, unchanged from the keeper's own path and
  **not** introduced by the arm: eGRID plant `55641` heat-rate boundary reconciliation
  (14.964 → 6.880); SPP-49 simple-cycle floor clamps on `2681`, `57186`, `59453`; NYISO CC
  pmax reconciliations on `7314` (−29.5 MW), `10190` (−20.0 MW), `56196` (−102.0 MW);
  `18 of 45 NYISO generators not in eGRID lookup — assigned fallback zone`.
- No `Traceback`, no `MemoryError`, no OOM, no killed process. Solve exit code 0.

## 7. Retention and scope — what this shard did NOT do

- **Nothing deleted** (rule 31 `[R-RETAIN]`). `results/calibration/nyiso226_span/` — all three
  years' `class_hourly`, `class_band_hourly`, `system`, `reserve_family`, `network`, `storage`
  and `unit_hourly` sidecars plus `legitimacy_diagnostics.json` — is intact on the shard's local
  disk and gitignored (`.gitignore:1913`, `results/calibration/nyiso226_*/`). **The container is
  ephemeral: these bundles do not survive it.**
- **No registration.** `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
  `prune_iso_runs.py` and `frontend/data/backcast/**` untouched.
- **No `src/` or `scripts/` edit** — `curate_lmp.py` and its owner-deferred `KeyError: 'MGHG'`
  left exactly as found, per the span addendum §1(b).
- **No `--write-metrics`, no PR, no `git add -A`/`git add .`** — only the two intended paths were
  ever staged, `git status --short` confirmed clean of anything else before each commit.
- **No judgement.** This shard states no verdict on the arm and draws no comparison to the
  control. That is the parent's, under rule 32(d), and the promotion call is the owner's under
  rule 31.
