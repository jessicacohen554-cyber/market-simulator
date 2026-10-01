# ADDENDUM — miso-251 SPAN shard: phase-0 hard stops PASSED (2026-09-10)

Shard: **SPAN** of session `miso-251`. Branch `claude/miso251-tp2022`.
Charter: `docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md`.
Job: replay the MISO keeper's frozen recipe on held-out **2022** and register it.

This addendum is the heartbeat required before the first LP. It records the three
hard stops with the values actually read off disk, not asserted.

## Hard stop 1 — pinned SHA

```
$ git rev-parse HEAD
b69062657498097f1bfb7ed264d77d95403f65e9
```

Equals the pinned `source_revision`. **PASS.** No pull, no rebase, no sync was
performed and none will be (rule 32 `[R-SHARD]` (c) 1).

## Hard stop 2 — the keeper bundle is the MISO 3-year keeper

`results/calibration/miso_fuelvintage_A/meta.json`:

```
iso   : MISO
years : [2023, 2024, 2025]
```

**PASS.**

## Hard stop 3 — the offer-curve / WEFOR signature

Read from `meta.json` → `coal_prb_sigmoid_overrides`:

```
offer_curve_by_group.CC_REGULAR.committed = 1.1055
offer_curve_by_group.CT_PEAKER.peak       = 4.4
summer_wefor_share_override               = 1.0599
```

All three match the charter exactly. **PASS — this is the right keeper.**

## Container prep (front-loaded, complete)

* `hydrate_data.py --profile miso` — full clone, every blob already local; nothing to hydrate.
* `prepare_solve_container.py` — 8 GiB swap added at `/swapfile-marketsim`
  (15.7 GiB RAM + 8.0 GiB swap = 23.7 GiB); `MALLOC_ARENA_MAX=2`,
  `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` exported.
* Pinned environment installed from the keeper `meta.json` `environment` block:
  highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0,
  pydantic 2.13.4, pyyaml, openpyxl, tzdata.
* `curate_capacity_deliverability.py` — `data/clean` is gitignored and was empty
  in this fresh container; rebuilt 5 partitions (MISO 776 rows). Note: the script
  needs `PYTHONPATH=.:src`, not `PYTHONPATH=.` — recorded here as an observation
  only; **no edit was made under `scripts/` or `src/`** (rule 32 (c) 6).

## Next

The single LP: `replay_keeper.py results/calibration/miso_fuelvintage_A --years 2022`
with the two mandatory `--set` flags of PRECOMMIT §3 (`miso_measured_reserve_requirements=false`,
`miso_reserve_online_gated=false`) and no other delta.
