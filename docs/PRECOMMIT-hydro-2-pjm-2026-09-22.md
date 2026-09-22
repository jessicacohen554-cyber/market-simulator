# PRECOMMIT — hydro-2: PJM `hydro_ror_split`, full year set (2026-09-22)

Continues `docs/RESULT-hydro-1-2026-09-22.md` (§A). Written and pushed **before** any solve;
the shards are pinned to this commit's SHA.

## 1. What this lane does

Re-solves PJM's designated keeper recipe with **exactly one delta**, `hydro_ror_split=true`, on
**every year PJM has registered**, one shard per year (rule 36 `[R-YEAR-ISOLATION]`), each
pushing its full bundle (rule 34(a)). Parent composes, scores, registers, and puts promotion to
the owner.

## 2. The 2023 blocker — resolved by re-fetch, not by changing the recipe

hydro-1's 2023 leg stalled because `data/raw/pjm-da-virtuals/` held only `README.md` (payload is
gitignored under PJM's DataMiner2 redistribution restriction) while the keeper arms
`pjm_da_virtual_bids=true`. Measured this session: `scripts/data/fetch_pjm_da_virtuals.py
--years 2023 --feeds hrl_da_incs_decs` wrote all 12 months (138–149 k rows/month, ~4 min), and
January 2020 / 2021 / 2022 return 81,067 / 114,092 / 212,350 rows. **`pjm_da_virtual_bids` stays
`true`** — the A/B is not confounded. Because the payload cannot be committed, **each shard
fetches its own year** before solving.

Disclosed: the corpus carries no `SHA256SUMS.txt`, so byte-identity of a re-fetch to what the
keeper solved on cannot be proven. DataMiner2 retention is indefinite and these are posted
historical bid curves; G-DRIFT below is the check on whether the keeper remains a valid control.

## 3. Year set (rule 34(c) / 35(b))

Union of `years` over every PJM sidecar in `frontend/data/backcast/registry/`:

| registered run | years | role |
|---|---|---|
| `2026-09-22-pjm-h16-coalgrain-span` | 2023, 2024, 2025 | keeper (promoted by pjm-h16, `49c237e90`) |
| `2026-09-22-pjm-h16-coalgrain-touchpoint` | 2020, 2021, 2022 | stamped to keeper |

**Six years, not three.** Both runs carry the identical recipe (run_config diff: `years` and the
per-year gas-price reference only; `coal_sync_window_commitment_grain=true`, `hydro_ror_split=false`, `pjm_da_virtual_bids=true`,
`hydro_min_flow_floor=false`, `hydro_dispatch_envelope=false` in both). A promotion that covered
only 2023–2025 would leave the touchpoint stamped to a pruned keeper, which rule 35(c) forbids.

## 4. Pre-check (zero LP, this session)

`scripts/data/curate_hydro_plant_modes.py --iso PJM` → **82 plants, 57 run-of-river-class,
25 reservoir-class** (3,339 MW EHA CH). Matches the required 57. Output is under `data/clean/`
(gitignored), so each shard re-runs it.

## 5. Control and G-DRIFT (rule 29(b))

**Re-based 2026-09-22 onto the new keeper** (the owner promoted pjm-h16 while this lane was in phase 0; no shard had launched).
Control = the committed keeper bundles (`pjm_h16_coalgrain_span`, `pjm_h16_coalgrain_touchpoint`),
all six legs solved at `c25d7e500238a953c241271ed91f7c01835f41b5` (an ancestor of HEAD). No control solve unless a LIVE hunk is found.

**G-DRIFT, `c25d7e50` → HEAD: ALL INERT — form 4 valid.** The solve-path commits in this window are a subset of the audited `6de36475` → `7c1fed78` set below, plus `3c5a8967b` (soco59: `EIA930_PS_SPLIT_COMPLETE_FROM` gains `"SOCO": 2025` — another ISO's entry, INERT for PJM). Independently, pjm-h16 spent six same-HEAD control legs and measured PJM drift bit-identical across `6de36475` → `c25d7e50` (`ffbd2426a`). Original audit table:

| commit | what | verdict | reason |
|---|---|---|---|
| `188c30e42` | pjm-h15 coal-sync per-year window | INERT | same `git patch-id --stable` as `6de36475` — the keeper already carries it (`coal_sync_online_frac_per_year: true`) |
| `cc5b886f5` | content-addressed P0 cold-solve cache | INERT | requires `MARKET_SIM_P0_CACHE` truthy (default off); shards must leave it unset |
| `c1116c86b`, `4dfe9d298` | miso-266 outage-derate denominator | INERT | `unit_outage_dispatched_bin_denominator` default False, absent from keeper |
| `6edc996d1` | SPP-71 coal-sync ensemble placement | INERT | `coal_sync_ensemble_level` default False, absent |
| `c25d7e500` | pjm-h16 coal whole-operating-day grain | INERT | `coal_sync_window_commitment_grain` default False, absent; off-path returns the prior `load_rank[:k]` |
| `bdd69194a` | soco-57 `measured_cc_heat_rates` | INERT | default False, absent; data file SOCO-only |
| `da38d1086` | hydro-1 forebay bound, RoR hybrid-label repair | INERT for control | pondage resolver `UNSET` unless `hydro_pondage_bound`/`hydro_cascade_coupling`; the mode partition is read only under `hydro_ror_split` (`data/hydro.py:1769`) |
| `e107949df` | PERF-C S2 row-bound collection; P0 slim extraction | INERT | same vectors/order/dtype; extraction skip is post-solve only |
| `5cb658922` | PERF-C memo add/drop | INERT | pure derivation |
| `d45d57f97` | P1 basis-seed un-nest | INERT | keeper legs ran seedless (x-year off); `replay_keeper` pins both env vars to 0 |
| `7fd12b91e` | registration IO | INERT | post-solve |

Five new `ScenarioConfig` fields, all default False and on `_CACHE_KEY_OPTIONAL_FIELDS` with drop value `"False"`; new CLI tri-states default `None` and are filtered. **The arm's one moving input is the HEAD classifier** (the hydro-1 repair adds 1–2 shapeable PJM plants vs hydro-1's pre-repair classifier — immaterial here since hydro-1's 2024/25 legs were also solved at a HEAD carrying it). Partition this session: 82 plants, 57 RoR-class; content hash (`hash_pandas_object`, sorted) `223845be42b5cfdf`. Each shard reports its own hash; a mismatch is a STOP.

## 6. Gates, declared before the solves (carried from hydro-1 §4)

Decided on structure (rule 1). A failed gate does not kill the arm; a passed one does not promote.

- **G1 liveness** — ≥ 1,000 MW-avg flat class stamped; model zero-hours < 500/yr.
- **G2 invariant** — annual hydro TWh moves < 0.1 % vs control, every year.
- **G3 targeted statistic** — zero-hours fall, p05 rises, p95 and top-decile share fall.
- **G4 no silent breakage** — full rubric (C1–C8) re-scored on every year and reported at full
  magnitude vs the keeper.

**Rule 1, restated before any number arrives:** if the faithful representation moves scored
criteria the wrong way, **it stays**, and the regression is a root-cause question. The owner has
ruled structural integrity can outweigh gate regression here.

**Not armed, on purpose:** `hydro_min_flow_floor`, `hydro_dispatch_envelope`. Both read EIA-930
`NG: WAT`, which folds 5,046 MW of PJM pumped storage (`EIA930_PS_FOLDED_INTO_WAT`); the level pin
refuses for this BA, those two readers do not. Live code gap, recorded, not worked around (rule 14).

## 7. Shards

Six, one per year, pinned to this commit. Each: fetch its year's virtual bids → curate hydro modes
(must print 57) → `replay_keeper.py <control bundle> --years <y> --set hydro_ror_split=true
--out-dir results/calibration/hydro2_pjm_ror_<y> --note ...` → commit the full bundle (including
`dispatch/<y>_P1.parquet`) via `.gitignore` negation + plain `git add` → push to
`claude/hydro2-pjm-ror-<y>`.

| year | control bundle |
|---|---|
| 2020, 2021, 2022 | `results/calibration/pjm_h16_coalgrain_touchpoint` |
| 2023, 2024, 2025 | `results/calibration/pjm_h16_coalgrain_span` |

**Retrievability (rule 34(e)):** the parent fetches every leg, composes, and lands the keeper
bundle on `main` before this lane's PR merges (rule 33(f)(4)(ii)). Shard SHAs are provenance only.
