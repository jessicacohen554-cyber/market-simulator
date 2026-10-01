# PRECOMMIT — R-PJM-2: the h22 RGGI keeper on corrected inputs, 2019–2025 (2026-09-25)

Written and pushed **before any solve**. The seven shards pin to this commit's full SHA.

**Owner ruling (2026-09-25), verbatim: "Yes promote"**, given in answer to the R-PJM RESULT §9 question.
That question noted that the first R-PJM run was solved on the h19 recipe, and that the keeper had since
become `2026-09-24-pjm-h22-rggi-span` (RGGI allowance pricing). Promoting the h19-based run would have
dropped RGGI. **This lane therefore executes the promotion on the current keeper:** the h22 recipe plus the
four F1 flags. It solves 2019–2025 and promotes the result once it lands. Rule 1 still holds: the promotion
rests on structure (correct inputs plus the owner's ruling), not on the gates, and whatever the gates show
is reported at full magnitude.

**Incumbent / control (rule 29(b) form 4):** `2026-09-24-pjm-h22-rggi-span` (2023–25) and its folded
touchpoint `2026-09-24-pjm-h22-rggi-touchpoint` (2020–22). Both solved at `d58121c3`, and both use one
recipe (their metas differ only in years, gas prices, shared inputs, timestamp and composed_from).

## 1. Year set (rules 34(c) / 35(b))

PJM registered years at this pin: h22 span 2023–25, h22 touchpoint 2020–22, and R-PJM
`2026-09-24-pjm-r-pjm-corrected` 2019–25. **Union = 2019–2025.** This lane solves all seven.

## 2. Recipe

The incumbent h22 `meta.json` is replayed unchanged (`scripts/replay_keeper.py`), with the same six explicit
`--set` flags as R-PJM (`docs/PRECOMMIT-r-pjm-corrected-inputs-2019-2025-2026-09-24.md` §2):
`eia860_vintage_tracks_solve_year`, `measured_{ct,coal,st,cc,chp}_heat_rates` = true.
`pjm_rggi_allowance_pricing = true` is carried from the incumbent's meta. **Offer curves are unchanged**
(`authorized_price_tuning.used = false`). The outage files are identical to R-PJM's (the committed std and
short-coal extracts, and short-gas extended to 2019).

## 3. The 2019 RGGI rows (this commit, zero LP, zero free parameters)

Without these rows, the gated RGGI arm solved 2019 with **no** RGGI cost. The price lookup returned `None`,
so the adder was $0, and membership fell back to the 2025 set, which enrolls NJ one year early. That would
leave the keeper's 2019 year silently un-RGGI'd.

| table | 2019 row | source / check |
|---|---|---|
| `RGGI_MEMBER_STATES_BY_YEAR` | NY CT MA ME NH RI VT **MD DE** | Published: NJ rejoined 2020-01-01, VA joined 2021-01-01 |
| `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` | **5.97 $/t** | Mean of the four 2019 auctions [5.27, 5.62, 5.20, 5.61] = 5.42 $/short ton, ×1.10231. Equals NEISO's 2019 value; the test re-derives it from the committed CSV |
| `PJM_RGGI_ZONE_SHARE` | EMAAC **0.1716** (DE only), SWMAAC 0.9981, West_APS 0.0112, others 0 | `derive_pjm_rggi_zone_share.py --years 2019..2025`; the same run reproduces 2020–2025 **exactly** |

Solve surface: `--diff 9210075` → 4 values moved (the three PJM tables; the shared membership table
re-keys every ISO). The six pins in `test_persisted_identity.py` are advanced with a cause block. All six
**already failed at main** because pjm-h22 never advanced them; that is named in the block, not absorbed.
The 238 tests covering these tables pass.

## 4. G-DRIFT `d58121c3` → this pin (rule 29(b))

| hunk | PJM verdict |
|---|---|
| F1 (vintage eGRID join, measured per-year heat rates, backcast default flips) | **LIVE — the treatment** |
| F2 short-gas PJM +246 rows in 2019 | **LIVE for 2019 only**; 2020–25 byte-identical |
| This commit's 2019 RGGI rows | **LIVE for 2019 only**; 2020–25 rows unchanged |
| R-NEISO `outages.py` gas-only scope (`coal_scope`) | INERT: `coal_scope=True` whenever short-coal is armed (PJM arms both) |
| R-NEISO `_mid_vintage_exit_rows_from_window` | INERT: reached only under `mid_vintage_exit_carry` (default False, not in the recipe) |
| R-CAISO CC heat rate / short-gas CAISO files; CAISO / NEISO extracts | INERT: other ISOs' artifacts |
| Y-28/29/30, storage-compare, soco-61, miso-268, soco60b, `results/cache.py` epoch entries | INERT (see R-PJM PRECOMMIT §4) |

## 5. Gates and predictions (declared before any solve)

- **G1 liveness (shard hard stop):** the `run_config` shows the six flags true and
  `pjm_rggi_allowance_pricing` true. The log line `PJM <y>: partial-footprint carbon adder … (program
  RGGI, P $/t)` shows P = 5.97 / 7.07 / 10.44 / 14.84 / 14.87 / 22.83 / 24.35 for 2019–2025, with N > 0.
  The outage sha is `312a11b8…`.
- **G2 predictions:** the F1 deltas measured on h19 carry over roughly additively: 2021 coal rises
  ~+20 TWh, CC_REGULAR falls, and 2020 coal falls. The h22 keeper's own open C1 (CC_REGULAR 2024
  −13.6 TWh) is expected to persist or worsen slightly, since F1 moved 2024 CC by −0.7 TWh on h19.
  **The expected 2023–25 determination is NOT-YET on C1, like the incumbent.**
- **G3:** full C1–C8 rubric for every year, against the incumbent re-scored on the same benchmark.

## 6. Promotion mechanics (rule 35) — executed after the shards land, on the owner's ruling

The steps run in this order: compose, attest, register, then verify the incoming keeper's three stores with
`audit_keepers.py`. Then set `keepers/PJM.json`, re-key `calibration-complete.json`, run
`build_status.py --iso PJM`, and re-stamp the matrix shard. Only after that, prune the outgoing
`h22-rggi-span`, `h22-rggi-touchpoint` and `r-pjm-corrected` with `prune_iso_runs.py --iso PJM
--force-uncite`. The incoming bundle covers the full union 2019–2025, so there is no stamped touchpoint.

## 7. Shards

There are seven, one per year, pinned to this commit. Out-dirs are `results/calibration/rpjm2_<y>`, on
branch `claude/rpjm2-<y>`. The control bundle is `pjm_h22_rggi_touchpoint` for 2019–2022 and
`pjm_h22_rggi_span` for 2023–2025. The prompt uses the R-PJM shard template, with the RGGI log line added as
a hard stop. Each shard pushes its full bundle, including `dispatch/<y>_P1.parquet`. The parent lands the
composite on `main` before this lane's PR merges.
