# PRECOMMIT — SPP-100: the CHP steam-level swap, scoped to hosts whose meter supports an all-hours floor

**Lane** SPP-100 · control = keeper `2026-09-28-spp-99-remap-rederive`, bundle `results/calibration/spp99_remap_span`
(rule 29(b) form 4, no control solve) · written before any shard launched and merged to `main` before launch.

## 1. Why this lever (off-queue, stated)

The §5.7 queue is exhausted (SPP-96). The one SPP cell with a **named re-open route** is `chp_steam_following`
(R, owner ruling 2026-09-24 *"Don't promote"*): *"Re-open ONLY as the scoped form (the level swap restricted to
non-cycling hosts)."*

- SPP-75 armed `chp_steam_floor_p25` alone. It lifted SPP's two flat metered steam hosts (Eastman 55176 CC_CHP,
  Black Hawk 55064 CT_CHP) toward their measured level, passed its over-forcing gate, and moved every 2020 price
  row the right way.
- It was declined for one structural defect: a 4.4–4.6 MW **24/7** floor at **Lake Road (MO) 2098 ST_CHP**, a
  cycler metered on only 5.5–27.7 % of hours. That is a rule-17 D-4 unit-conduct FAIL in all seven years.

This lane builds the scoped form and tests it. Basis: rule 17 `[R-FLOOR-WINDOW]` and rule 14 `[R-ACCURATE]`
(the two hosts' measured flat conduct), never the residual.

## 2. Phase 0 (zero LP)

### 2a. The existing duty window does not fix Lake Road

`chp_steam_duty_window` (caiso-293) holds the floor at the undiluted level in the top `on_frac` of live hours by
system load. Replayed on the keeper's own demand against Lake Road's CAMPD meter
(`scripts/probes/_spp100_chp_duty_phase0.py`), using D-4's test (median metered MW over the floor hours == 0):

| year | Lake Road metered on | zero share in window | D-4 (whole window / low half) |
|---|---:|---:|---|
| 2019 | 12.7 % | 66.9 % | FAIL / FAIL |
| 2020 | 5.5 % | 89.2 % | FAIL / FAIL |
| 2021 | 7.8 % | 78.5 % | FAIL / FAIL |
| 2022 | 15.7 % | 59.7 % | FAIL / FAIL |
| 2023 | 27.7 % | 38.1 % | pass / FAIL |
| 2024 | 25.1 % | 51.2 % | FAIL / FAIL |
| 2025 | 25.7 % | 53.7 % | FAIL / FAIL |

Eastman and Black Hawk pass in every year (window median 206–402 MW and 208–221 MW).

### 2b. The mechanism: `chp_steam_floor_conduct_scope` (new, default off)

- A **metered** CHP row (`status == ok`) takes the swapped level only if its pooled on-frequency
  `steam_level_cf / median_cf` (an exact identity over committed artifact columns) is **> 0.5**. Otherwise it keeps
  its p2 floor.
- **0.5 is D-4's own conduct test** (median metered output over an all-hours floor is zero iff the plant is off in at
  least half its hours), applied ex ante to pooled data: `constants.CHP_STEAM_ALLHOURS_MIN_ON_FRAC`, with citation.
  **Not a free parameter** (rule 21). On SPP the partition is identical for any bar in (0.25, 0.98):
  Lake Road 0.246 · Eastman 0.989 · Black Hawk 0.995.
- CEMS-invisible `eia923_cf` rows have no on-frequency and keep the swap (never fail a mechanism for a missing meter).
- Rule 19: no new floor, no second level source; the one `MECH_CHP_STEAM` swap's eligibility. Rule 13: pooled
  multi-year CEMS, regenerates forward. Rule 25: per-ISO artifact. Registered: `_CACHE_KEY_OPTIONAL_FIELDS`,
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, `TIER_TAGS` = 1, solve surface (0 values moved, 1 row added),
  matrix row + a cell in all nine shards.

### 2c. Fleet delta (`fleet_only` rebuild, `scripts/probes/_spp100_chp_floor_delta.py`)

| year | CHP floor mean MW: keeper | SPP-75 arm | **this arm** | Lake Road floor (this arm) |
|---|---:|---:|---:|---|
| 2020 | 142.5 | 328.1 | **323.6** | none (was 4.4 MW × 8760 h) |
| 2024 | 141.8 | 331.5 | **327.0** | none |

Every non-CHP plant is byte-identical. The only other differences are two small EIA-923 ST_CHP plants (58192, 58193)
re-banded by the swap, exactly as in SPP-75's arm.

**Arm = keeper + `chp_steam_floor_p25=true` + `chp_steam_floor_conduct_scope=true`.** Nothing else.

## 3. G-DRIFT (rule 29(b), form 4) — keeper `289d4baf` → `aab6d815` (origin/main at writing)

| hunk family | verdict | reason |
|---|---|---|
| PJM-NEXT-8 exit-cohort repair (`arrays.py`, `outages.py`, `resolved_inputs.py`, `scenarios.py`) | INERT | `unit_outage_exit_cohort_repair` default off, absent from SPP's recipe; every new branch is gated on it |
| NWPP-NEXT-8 coal monthly pile (`coal_fuel_inventory.py`, `rows.py`, `run_calibration.py`, `scenarios.py`, `forecast_parity_registry.py`) | INERT | `coal_fuel_inventory_monthly_pile` default off and gated to `COAL_TAKE_FLOOR_ISOS`; the `rows.py` refactor is algebraically identical at one month column and only reached when yard rows exist |
| This lane's own hunks | LIVE only under the new field | default off; byte-identical off |

All INERT for the keeper recipe → **the committed keeper is the control**. The shard check's recipe test enforces
that the leg differs from the keeper by exactly the two fields.

## 4. Solve plan (rule 36)

Seven shards, one per year 2019–2025, pinned to this PRECOMMIT's merge SHA. Each runs
`replay_keeper.py results/calibration/spp99_remap_span --years <Y> --set chp_steam_floor_p25=true --set
chp_steam_floor_conduct_scope=true`, then `scripts/probes/_spp100_shard_check.py`, and pushes its full bundle
(incl. `dispatch/<Y>_P1.parquet`) to `claude/spp100-<Y>`. The parent solves nothing, composes with
`_rspp_compose.py --side arm` (+ `--require chp_steam_floor_p25=true --require chp_steam_floor_conduct_scope=true`),
regenerates legitimacy diagnostics, attests, registers and scores.

## 5. Expectations (fixed before any solve)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all 7 legs (recipe = keeper + exactly the two fields; scope partition as §2b) |
| E2 | CHP class TWh rises in every year, +0.15 to +1.6 TWh (SPP-75: +0.22 to +1.33); \|ΔCC_REGULAR\| ≤ 0.8 and \|ΔCOAL_PRB\| ≤ 0.6 TWh per year |
| E3 | Demand-weighted mean price falls or holds in every year; \|Δ\| ≤ $0.60/MWh |
| E4 | **D-4: no unit-conduct row FAILs at 2098 in any year; no D-4 FAIL row that the keeper does not carry** (keeper: 8 D-4 FAIL rows, all ST_GAS/coal); Eastman and Black Hawk pass |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1/C3a/C3b/C4 status flip in 2023–25 |

Predicted, not gated: 2020 C3a +28.0 % falls by ~1–1.5 pp and stays FAIL (SPP-75: −1.37 pp). SPP-75's one
validation flip (2022 C1 CC_REGULAR PASS → FAIL) is already FAIL on this keeper (−10.46 TWh), so it cannot recur.

## 6. Recommendation rule (fixed)

- **RECOMMEND PROMOTE** iff E1, E4 and E5 hold and no year's unserved energy rises by more than 500 MWh over the
  keeper. That is the structural test: the two flat hosts at their measured level, with no new rule-17 defect.
- E2/E3 misses are reported at full magnitude and do not change the recommendation (rule 1: never judged by the
  residual). Validation-tier movement is reported, never the basis.
- Otherwise **RECOMMEND AGAINST**, naming the failed item.
- The owner decides (rule 31). Bundles are pushed to shard branches and the composite lands on `main` (rule 34).

## 7. Year set (rule 35(b))

SPP's registered years: 2019–2025, all on keeper `2026-09-28-spp-99-remap-rederive`. This lane solves all seven.

## Addendum A (2026-09-28, before any number was read) — shard-check repair

The first seven shards (pinned `2e1f387d`) solved, then stopped at hard stop 3. The recipe test in
`_spp100_shard_check.py` had a bug: `chp_steam_floor_p25` already sits in the keeper's recorded recipe at its
default (`false`), so the shared `_diff` helper reports it as CHANGED rather than NEW, and the check required
CHANGED to be empty. It now requires the effective delta (changed-to values plus new values) to be exactly the two
fields, with every change starting from the field's default. Verified on a synthetic leg: exact recipe → PASS, recipe
plus a stray field → FAIL. Nothing in §2–§6 changes. The shards are relaunched on the repair's merge SHA. The first
round's bundles never left their containers (the shards correctly refused to push), and no number from them was seen.
