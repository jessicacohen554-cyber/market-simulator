# ADDENDUM — miso-251 SCREEN shard, phase 0 (pre-LP heartbeat)

```
SHARD           : SCREEN (re-solve of held-out 2022 on REPAIRED MISO zonal demand)
SESSION         : miso-251
BRANCH          : claude/miso251-screen2022
PINNED SHA      : 34b0e557440b5ce956c73c75889f07a17761ac92
KEEPER REPLAYED : 2026-09-09-miso-250-ep-gas  (results/calibration/miso_fuelvintage_A)
SUPERSEDES      : 2026-09-10-miso-251-tp2022  (docs/RESULT-miso251-span-tp2022-2026-09-10.md)
CHARTER         : docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md
STATUS          : phase 0 complete, all hard stops PASS, LP not yet started
```

This is the pre-LP heartbeat required by the charter step 2 and by
`docs/handoffs/shard-launcher-protocol-2026-09-09.md`. It records the values the
three hard stops actually read, **before** any solve, so the record cannot be
written to fit a result.

## 1. Hard stops — all three PASS

### Hard stop 1 — pinned SHA

```
$ git rev-parse HEAD
34b0e557440b5ce956c73c75889f07a17761ac92
```

Equals the pinned SHA exactly. The clone is a detached HEAD at that commit;
`git status --short` is clean. **No `git pull`, no rebase, no sync was performed
and none will be** (rule 32 `[R-SHARD]` (c) 1).

### Hard stop 2 — the keeper bundle is the recipe it claims to be

From `results/calibration/miso_fuelvintage_A/meta.json`:

| field | value read | required | verdict |
|---|---|---|---|
| `iso` | `MISO` | `MISO` | **PASS** |
| `years` | `[2023, 2024, 2025]` | `[2023, 2024, 2025]` | **PASS** |
| `coal_prb_sigmoid_overrides.offer_curve_by_group.CC_REGULAR.committed` | `1.1055` | `1.1055` | **PASS** |
| `coal_prb_sigmoid_overrides.offer_curve_by_group.CT_PEAKER.peak` | `4.4` | `4.4` | **PASS** |
| `coal_prb_sigmoid_overrides.summer_wefor_share_override` | `1.0599` | `1.0599` | **PASS** |

Full bands as read (unchanged, quoted so the post-solve config check has an
ex-ante referent):

```
CC_REGULAR : committed 1.1055 · econ_low 1.045 · econ_high 1.188 · peak 2.475
             econ_low_share 0.5   · pct_peaking 8.0
             phys_committed 1.005 · phys_econ_low 0.887 · phys_econ_high 1.008 · phys_peak 2.25
CT_PEAKER  : committed 1.1275 · econ_low 1.1 · econ_high 1.1 · peak 4.4
             econ_low_share 0.526 · pct_peaking 7.0
             phys_committed 1.025 · phys_econ_low 0.687 · phys_econ_high 0.691 · phys_peak 1.0
```

### Hard stop 3 — THE ZONAL FIX IS LIVE

This is the shard's entire reason for existing, so it is the check that matters.

```
$ PYTHONPATH=src:. python3 -c "... parse_miso_shares(2022, zone_names) ..."
zones: ['MISO-West', 'MISO-Plains', 'MISO-Illinois', 'MISO-Indiana', 'MISO-East', 'MISO-South']
2022 shares: (6, 8760)
```

**A real `(6, 8760)` array, not `None`.** Two further self-checks, neither
required by the charter, both clean:

- **the shares are a partition** — the six zone shares sum to `1.000000` in every
  sampled hour, so nothing is double-counted or dropped by the repair;
- **they are hourly-varying, not flat** — each zone's share moves materially
  across the year, which is precisely the signal the first solve did not have.

| zone | 2022 mean share | 2022 min | 2022 max | 2023 mean (context) |
|---|---:|---:|---:|---:|
| MISO-West | 0.144729 | 0.101859 | 0.184224 | 0.148932 |
| MISO-Plains | 0.137616 | 0.111578 | 0.163681 | 0.137847 |
| MISO-Illinois | 0.071276 | 0.059329 | 0.084045 | 0.068688 |
| MISO-Indiana | 0.135303 | 0.110552 | 0.163584 | 0.131161 |
| MISO-East | 0.244772 | 0.181812 | 0.287071 | 0.243492 |
| MISO-South | 0.266305 | 0.212930 | 0.360016 | 0.269879 |

The within-year range is the whole point: MISO-South alone swings from 21.3 % to
36.0 % of MISO load hour to hour. A flat sample average erases that, and with it
every hour in which a zone's own load — not the RTO total — is what a link,
a floor or a locational reserve family actually sees. The 2023 column is shown
only as a sanity referent (the repaired 2022 profile sits in the same family as
the year the keeper was calibrated on, so the fix has not produced something
structurally alien).

Had this printed `None`, the charter directs the shard to STOP.

## 2. Container prep — done

- `scripts/hydrate_data.py --profile miso` → this is a **full** clone, so every
  blob is already local and hydration is a no-op by design (the script says so
  itself); `data/raw/zone-specific-demand/MISO/miso_subba_demand_2022.csv` is
  present on disk, which is the file the repaired loader now reads.
- `scripts/prepare_solve_container.py` → 8 GiB swap added at
  `/swapfile-marketsim`; **15.7 GiB RAM + 8.0 GiB swap = 23.7 GiB** total, 17.3
  GiB free disk, 4 cpus. Env pins exported for the solve
  (`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1`) —
  these do not change the LP optimum.
- Pinned deps installed: `highspy 1.14.0`, `numpy 2.4.6`, `scipy 1.17.1`,
  `pandas 3.0.3`, `pyarrow 24.0.0`, `pydantic 2.13.4`, `pyyaml`, `openpyxl`,
  `tzdata`.
- `scripts/data/curate_capacity_deliverability.py` → 5 partitions written
  (CAISO 386 · ISONE 15 · **MISO 776** · NYISO 35 · PJM 155 rows).

## 3. What this shard will and will not do

**Will:** solve 2022 once, on the keeper's frozen recipe, with exactly the two
mandated `--set` flags (`miso_measured_reserve_requirements=false`,
`miso_reserve_online_gated=false`) and nothing else; attest via
`gen_touchpoint_attestation.py`'s declared-degradation channel; register; score;
commit the slim bundle set; push to this branch; report every number side by side
against the first solve.

**Will not:** tune anything, whatever the numbers say (no offer-curve change, no
additional flag); edit anything under `src/` or `scripts/`; touch
`build_manifest.py` / `build_status.py` / `prune_iso_runs.py` /
`stamp_touchpoint_holdout.py` / `keepers/MISO.json` / `status/MISO.js` / the
mechanism matrix / the calibration log; open a PR; delete any result (rule 31
`[R-RETAIN]` — `.gitignore`, never `rm`); or propose a config change, which is
the parent's and the owner's call.

A shard that stops with a clear report is a SUCCESS; a shard that repairs
infrastructure is a FAILURE.
