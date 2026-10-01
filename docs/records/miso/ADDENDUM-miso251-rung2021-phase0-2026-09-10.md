# ADDENDUM — miso-251 RUNG-2021 shard: phase-0 heartbeat (ZERO LP)

**Written and pushed BEFORE the first LP is built.** This is the shard's heartbeat under
`docs/handoffs/shard-launcher-protocol-2026-09-09.md` §4: a shard that was created is not a shard
that is working, so the branch carries evidence of a live, verified container before it spends any
solve time.

```
SHARD           : RUNG-2021 of session miso-251
ISO             : MISO      DATA PROFILE: miso      YEAR: 2021
BRANCH          : claude/miso251-tp2021
CHARTER         : docs/ADDENDUM-miso251-the-falsifiable-regime-test-2026-09-10.md  (the PREDICTION)
                  docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md              (the ladder)
                  docs/RESULT-miso251-screen2022-2026-09-10.md                     (the 2022 rung)
SIBLING         : RUNG-2020 on claude/miso251-tp2020 — never touched by this shard.
```

---

## 1. HARD STOPS — every one read from disk, quoted verbatim

### 1.1 Pinned SHA

```
$ git rev-parse HEAD
dc57d4a29b374cb7897c1503bc4d4721aa568fb0
```

Matches the pin exactly. No `git pull`, no rebase, no sync was performed or will be.

### 1.2 Keeper bundle recipe signature — `results/calibration/miso_fuelvintage_A/meta.json`

| field | required | read from disk |
|---|---|---|
| `iso` | `MISO` | **`MISO`** |
| `years` | `[2023, 2024, 2025]` | **`[2023, 2024, 2025]`** |
| `coal_prb_sigmoid_overrides.offer_curve_by_group.CC_REGULAR.committed` | `1.1055` | **`1.1055`** |
| `coal_prb_sigmoid_overrides.offer_curve_by_group.CT_PEAKER.peak` | `4.4` | **`4.4`** |
| `coal_prb_sigmoid_overrides.summer_wefor_share_override` | `1.0599` | **`1.0599`** |

All five match. This is the `2026-09-09-miso-250-ep-gas` keeper recipe, unmodified.

### 1.3 The zonal fix is live for 2021

```
$ PYTHONPATH=src:. python3 -c "... parse_miso_shares(2021, get_iso_config('MISO').zone_names) ..."
zones: ['MISO-West', 'MISO-Plains', 'MISO-Illinois', 'MISO-Indiana', 'MISO-East', 'MISO-South']
2021 shares: (6, 8760)
```

`(6, 8760)` — six MISO zones × full 8760 hours of **measured** zonal allocation, not the flat
sample-average fallback the 2022 screen repaired. Not `None`, so the hard stop passes and the rung
runs on real zonal demand.

---

## 2. Container prep — completed

* `scripts/hydrate_data.py --profile miso` — full clone, every blob already local; nothing to fetch.
* `scripts/prepare_solve_container.py` — 8 GiB swap added at `/swapfile-marketsim`
  (RAM 15.7 + swap 8.0 = **23.7 GiB**), 17.3 GiB free disk, 4 cpus.
* Solve env pins exported and verified in-shell: `MALLOC_ARENA_MAX=2`,
  `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1`. (These do not change the LP optimum.)
* Pinned deps installed: `highspy==1.14.0 numpy==2.4.6 scipy==1.17.1 pandas==3.0.3
  pyarrow==24.0.0 pydantic==2.13.4` + `pyyaml openpyxl tzdata`.
* `scripts/data/curate_capacity_deliverability.py` run — 5 partitions written (MISO 776 rows). Invoked
  with `PYTHONPATH=src:.`; the launch prompt's `PYTHONPATH=.` raises `ModuleNotFoundError:
  market_sim`. That is an invocation fix in this shell only — **no file under `scripts/` or `src/`
  was edited.**

---

## 3. What this shard will and will not do

**Will:** replay the keeper's frozen recipe on 2021 via `scripts/replay_keeper.py`, with the two
declared source-forced degradations (`miso_measured_reserve_requirements=false`,
`miso_reserve_online_gated=false`) and **nothing else**; attest recipe identity; register; score;
commit its own bundle, its own registry/run payload, `bench/MISO/2021.json.gz` **only**, and its own
two docs.

**Will not:** tune, sweep or select anything, whatever the residual says; touch `src/` or
`scripts/`; run `build_manifest.py` / `build_status.py` / `prune_iso_runs.py` /
`stamp_touchpoint_holdout.py`; touch `keepers/MISO.json`, `status/MISO.js`, the mechanism matrix or
the calibration log; open a PR; delete any result (rule 31 `[R-RETAIN]` — `.gitignore`, never `rm`);
or touch the RUNG-2020 sibling's branch, bundle or docs.

**Scope limit, stated before the numbers exist:** `actual_lmp.json` carries no MISO block before
2022, so **C3a / C3b / C3c are UNSCORABLE on 2021**. This rung reads `CALIBRATED-WITH-CAVEATS` at
best, on `unscored criteria`. That is a fact about MISO's LMP retention, **not a model result**, and
under rule 30(c) it cannot move MISO's determination in either direction.

**The pre-registered prediction this rung tests** (charter §3, H1): 2021 (Henry Hub **$3.72**, $0.20
above the training ceiling) should return a coal residual **between 2020's and 2022's and much
closer to 2020's** — a $0.20 excursion past the band-identification regime should not buy a 50 TWh
error. Reference: keeper 2023 (HH 2.54) **−5.77**, 2024 (HH 2.19) **−9.18**, 2025 (HH 3.52)
**−10.66**, 2022 (HH 6.45) **+50.46** TWh. This shard reports the number and **does not adjudicate
the hypothesis** — that is the parent's call.
