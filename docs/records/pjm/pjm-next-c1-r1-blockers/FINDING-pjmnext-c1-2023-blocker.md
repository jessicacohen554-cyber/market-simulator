# FINDING — PJM-NEXT card 1, arm shard 2023: G1 hard stops (e) and (c) fail, so the bundle was not pushed (2026-09-25)

Shard of orchestrator PJM-NEXT. Pinned commit `7f0953845350089732892f83248726d4b04fb84f` (verified).
Record: `docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md` §4 G1.

The solve **completed** (exit 0, wall 678 s; phase total 657.7 s: data_prep 70.7, P0 353.3, markup 47.7,
P1 141.4, results_write 44.5). The bundle `results/calibration/pjmnext_c1_2023/` exists **on this shard's
local disk only**, complete, with `dispatch/2023_P1.parquet`. Under the shard's G1 instruction it was
**not committed**. Rule 31: it was not deleted either.

## G1 checks

| check | expected | observed | verdict |
|---|---|---|---|
| (a) keeper flags in `run_config.json` `scenario_config` | all true | eia860_vintage_tracks_solve_year, measured_{ct,coal,st,cc,chp}_heat_rates, pjm_rggi_allowance_pricing all `True` | PASS |
| (b) `campd_unit_outages.sha256` | `312a11b8…` | `312a11b84778441cdf3f4dbe580ab4941122e5e30355d7b91b9b4c56e3924312` | PASS |
| (c) solve log names EIA-860 source `vintage_2023` | named | **not named anywhere in the log.** `paths.set_active_eia860_vintage` switches to `data/raw/eia-860/vintage_2023` silently, and the directory exists on disk. The only 860 lines are `Loaded PJM fleet from EIA-860 parquet (1922 / 2024 generators)`, and `meta.json` / `run_config.json` record no 860 path | **FAIL as written.** Likely a check the runner cannot satisfy rather than a wrong vintage, but not verifiable from the log |
| (d) three arm flags true | all true | mid_vintage_exit_carry, fleet_zone_vintage_coords, benchmark_membership_vintage_union all `True` | PASS |
| (e) `mid-vintage-year exit carry (PJM 2023): injecting 45 unit(s)` | 45 | **`injecting 49 unit(s), 3707 MW — plants [384, 874, 2866, 3809, 50722, 55156, 56279, 56863, 56869, 56911, 57519, 57637, 57638, 58475]`** (printed twice, identical) | **FAIL** |
| (f) `fleet_zone_vintage_coords (PJM): …` line | may be absent | **absent**. Note that the log still shows `WARNING: 14 of 1922 PJM generators not in eGRID lookup — assigned fallback zone` with the flag on | reported |
| (g) meta `shared_inputs.eia923` 2023 total | 823.024 ± 0.001 TWh | 823.0240 TWh (`../_shared/PJM/eia923-a46506071533.parquet`) | PASS |

### On (e)

PRECOMMIT §1a's 2023 row reads 5 plants / 3,650 MW (Sammis 2866, Joliet 29 = 384, Yorktown 3809,
Joliet 9 = 874, …). The log injects **14 plants, 49 units, 3,707 MW**: 9 more plants carrying ~57 MW in
total. The phase-0 probe `scripts/probes/_pjmnext_mvx_phase0.py` counts LP units in the built fleet,
while the log line counts rows at injection, so a counting-basis difference (small non-thermal units
filtered or aggregated downstream) is a plausible explanation. It is **not verified** here: the shard does
not repair or re-derive. The same basis question would apply to the other years' 47 / 34 / 24 / 73 / 60.
In P1 dispatch the injected plants produce: 384 ST_GAS 0.628 TWh, 2866 COAL_BIT 0.518, 874 ST_GAS
0.078, 50722 CT 0.001, and the rest ≈ 0.

### Side observation — bundle is not self-contained

`meta.json` `shared_inputs.eia923` points at `../_shared/PJM/eia923-a46506071533.parquet`. That file is
**outside** the bundle dir and is gitignored (`.gitignore:2340 results/calibration/_shared/*`), so a
bundle-only push would not carry it. The parent should confirm the composer or registration regenerates
it.

## Numbers (P1, 2023, from the local bundle)

Per-class model TWh: CC_REGULAR 318.706 · nuclear 272.043 · COAL_BIT 105.035 · wind 29.628 ·
CT_PEAKER 23.195 · VIRTUAL_INC 17.573 · ST_GAS 14.295 · solar 8.976 · hydro 8.903 · CC_CHP 7.502 ·
OTHER 7.225 · biomass 5.298 · COAL_WC 4.742 · COAL_PRB 3.557 · CT_CHP 1.715 · ST_CHP 0.965 ·
oil 0.001 · VIRTUAL_DEC −11.776 · import −28.875. Net total 788.706.

Price (system.parquet P1, 9 zones): mean over zone-hours $30.142/MWh; load-weighted $30.889/MWh.

Container: `container preflight: memory ceiling 13.36 GiB …, swap 0.0 GiB, target ceiling+swap 24 GiB`;
`provisioned 3 GiB swap … ceiling 13.36 + swap 3.0 = 16.4 GiB` (WARNING: below the 24 GiB target).
`memory peak: cgroup_peak_rss_gib=13.36, cgroup_peak_rss_plus_swap_gib=15.94, process_vmhwm_gib=13.31,
process_vmswap_now_gib=0.04`. Only 0.46 GiB of headroom remained.

Setup notes: `regenerate_clean.py` finished with 2/58 datatypes failing: `emissions-unit-annual`
(exit −9, OOM-killed) and `ercot-wtx-congestion` (exit 1). The solve never named either as missing. DA
virtuals for 2023 fetched cleanly.

## Retrievability (rule 34(e))

The bundle is on ephemeral shard disk only. If the parent rules (e) and (c) as check-basis defects and
tells this shard to push, the push is cheap. If the container is reclaimed first, recovery is a re-solve
of about 11 min wall.
