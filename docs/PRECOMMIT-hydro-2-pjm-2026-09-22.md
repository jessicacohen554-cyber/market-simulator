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
| `2026-09-20-pjm-h15-coalwindow-span` | 2023, 2024, 2025 | keeper |
| `2026-09-20-pjm-h15-coalwindow-touchpoint` | 2020, 2021, 2022 | stamped to keeper |

**Six years, not three.** Both runs carry the identical recipe (run_config diff: `years` and the
per-year gas-price reference only; `hydro_ror_split=false`, `pjm_da_virtual_bids=true`,
`hydro_min_flow_floor=false`, `hydro_dispatch_envelope=false` in both). A promotion that covered
only 2023–2025 would leave the touchpoint stamped to a pruned keeper, which rule 35(c) forbids.

## 4. Pre-check (zero LP, this session)

`scripts/data/curate_hydro_plant_modes.py --iso PJM` → **82 plants, 57 run-of-river-class,
25 reservoir-class** (3,339 MW EHA CH). Matches the required 57. Output is under `data/clean/`
(gitignored), so each shard re-runs it.

## 5. Control and G-DRIFT (rule 29(b))

Control = the committed keeper bundles (`pjm_h15_coalwindow_span`, `pjm_h15_coalwindow_touchpoint`),
solved at `6de36475e9b89f980927fdf0fcfa196c627f2b6a`. No control solve unless a LIVE hunk is found.

G-DRIFT_PLACEHOLDER

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
| 2020, 2021, 2022 | `results/calibration/pjm_h15_coalwindow_touchpoint` |
| 2023, 2024, 2025 | `results/calibration/pjm_h15_coalwindow_span` |

**Retrievability (rule 34(e)):** the parent fetches every leg, composes, and lands the keeper
bundle on `main` before this lane's PR merges (rule 33(f)(4)(ii)). Shard SHAs are provenance only.
