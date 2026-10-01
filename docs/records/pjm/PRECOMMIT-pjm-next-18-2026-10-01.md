# PRECOMMIT — PJM-NEXT-18: seven year-isolated keeper replays to read the LP's own low-end marginal units

**Keeper:** `2026-09-30-pjm-next16-ovec` (bundle `results/calibration/pjmnext16_A_span`, 2019–2025). **No arm.**
- Each shard replays ONE year of the keeper, byte-faithfully. These are diagnostic replays: never registered as runs, never promotion candidates (each IS the keeper).
- **Owner card** (decision card, this session): *"All 7 years"*.

## 1. Why

- The owner card *"Both, sequenced"* asks for card 1: the low-price-hour price floor, all seven years.
- NEXT-14 named the keeper's low-end price-setters for **2020 only**, and against an older keeper: CC econ/committed plus coal econ, at about 7.8 × delivered gas, against the actual 5.5 ×.
- NEXT-17's own-offer audit puts the model's price level in hours under $25 behind +5 to +47 TWh of the COAL_BIT over-run. That term is large in 2023/24 too.
- The marginal unit can be read only from `hourly/unit_hourly_<y>.parquet`: per LP unit-hour `mw`, `cap_mw`, the P1 offer `mc` and HiGHS `red_cost`. The keeper bundle does not carry it.

**Comparator.** The IMM State of the Market reports PJM RT marginal-resource shares, transcribed in `data/raw/som-competitive-conduct` for 2019–2025, all intervals:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CC | .621 | .643 | .598 | .617 | .692 | .608 | .632 |
| coal | .244 | .175 | .142 | .100 | .091 | .103 | .079 |
| CT | .060 | .059 | .101 | .113 | .110 | .097 | .099 |
| wind | .038 | .068 | .110 | .111 | .055 | .136 | .111 |

The IMM publishes no low-price-hour split. The low-end comparison against actuals is therefore the price ratio (RT ÷ delivered gas), as in NEXT-14.

## 2. Owner instruction attached to this lane (2026-10-01)

*"Make sure this is captured in the keeper bundle moving forward"* / *"Moving forward for all ISOs. Add as rule or something to code."* Executed in this PR:

- **CLAUDE.md rule 15 `[R-DASHBOARD]`:** keeper bundles commit `hourly/unit_hourly_<year>.parquet` for every year, in every ISO.
- **`.gitignore`:** `unit_hourly_*` is no longer ignored. `network_*` stays opt-in.
- **`scripts/check_promotion_completeness.py` leg (e):** a promoting PR whose new keeper bundle lacks the layer for any year FAILS. The leg is prospective: it is armed only for a keeper that changed against `--base`.
- **This keeper:** each replay's `unit_hourly_<y>.parquet` is copied into `pjmnext16_A_span/hourly/` **only if** that year reproduces the keeper exactly. The test is §4 G-REPRO at Δ = 0.000 TWh for every class. A year that drifts at all is not attached, and the drift is reported.

## 3. G-DRIFT (rule 29(b)), keeper pin → this branch

- **Up to `cc3e160b5`:** the NEXT-17 audit (`PRECOMMIT-pjm-next-17-2026-10-01.md` §4) applies unchanged. That runs from the keeper pin's rebased equivalent `2f4af3b07` to the NEXT-17 head, and every non-lane hunk is INERT.
- **`cc3e160b5` → this branch:** an AST diff of `src/market_sim`, `scripts/run_calibration*.py`, `scripts/replay_keeper.py` and `scripts/lib`, with docstrings neutralized.
  - The only AST-changed solve-path files are `run_calibration.py`, `run_calibration_full.py`, `config/scenarios.py`, `data/reserve_requirements.py` and `model/interchange/import_nodes.py`. In every one, the changed hunks are doc-path strings rewritten by cleanup-C (`docs/…` → `docs/records/<lane>/…`) in help, error and comment text. INERT.
  - `scripts/lib/topscoped_encode.py` is ERCOT-only and INERT.
  - `scripts/lib/clean_profiles.py` and `record_lanes.py` are new: data-prep tooling (`regenerate_clean --solve-profile`) and docs routing. Neither is on the LP path.
  - **Data-prep risk is caught by G-REPRO**, not by the audit. A clean partition the profile might omit would show up as a non-zero class delta.
- **Conclusion:** form 4 is valid. The keeper's committed `class_hourly_<y>.parquet` is the control. The rule-36(d) warm-start knobs are pinned off by `replay_keeper.py`.

## 4. Gates and predictions (fixed before any replay)

`low` = hours with actual RT < 6.5 × delivered gas (NEXT-12/14 definition). Marginal = interior (> 0.5 MW off both bounds) with `|red_cost| ≤ 0.01`, pooled per hour, weight 1/n.

| id | statement | falsified if |
|---|---|---|
| G-REPRO | Every class's P1 TWh equals the keeper's `class_hourly` to Δ = 0.000 in every year | any \|Δ\| > 0.000 (≤ 0.05 is reported and the census still stands; > 0.05 voids that year) |
| P1 | In every year, ≤ 5 % of `low` hour-weight has a marginal offer < 6.5 × delivered gas | > 0.05 in any year |
| P2 | Median marginal offer ÷ delivered gas in `low` hours exceeds the median actual RT ÷ delivered gas by ≥ 1.5 in every year | < 1.5 in any year |
| P3 | That P2 gap is **not** year-discriminating: the 2019–2021 mean exceeds the 2023–2024 mean by < 0.5 | ≥ 0.5, which would make it a C1/C3a-ordering candidate |
| P4 | The thermal-marginal hour share in `low` hours is ≥ 0.75 in every year | < 0.75 (network, storage or imports set the low end) |
| P5 | Renormalized over thermal classes, the model's all-hours CC marginal share is below the IMM CC share in every year | ≥ IMM in any year |
| P6 | The COAL_BIT econ share of `low` marginal weight is higher in 2019–2021 than in 2023–2024 (means) | not higher |

**What each outcome means:**
- **P3 holds:** the price floor is an all-year level object. It is the shared root of the C3a level and the coal price-level term, but it does not order the failing years. It is then a level lever and no answer to C1 by itself.
- **P3 fails:** a year-discriminating price-floor term exists. Card 3 then designs against its named units.
- **P4 fails:** the low end is set by network, storage or imports, and the lane turns to the interchange and transfer surfaces.

## 5. Execution

- One shard per year (rule 36), pinned to this commit's full SHA.
- Each shard runs `python3 scripts/replay_keeper.py results/calibration/pjmnext16_A_span --years <y> --out-dir results/calibration/pjmnext18_rp_<y> --note "PJM-NEXT-18 card 1 diagnostic replay"`.
- Setup: `pip install -e .`, `hydrate_data.py --profile pjm`, `fetch_pjm_da_virtuals`, `regenerate_clean.py --solve-profile PJM` (which includes `transfer-interface-limits`).
- Each shard pushes its full bundle (with `dispatch/` via a `.gitignore` negation, and `hourly/unit_hourly_<y>.parquet`) to its own branch `claude/pjm-next-18-rp-<y>` (rule 34).
- The parent fetches, runs G-REPRO and the census (`scripts/probes/_pjmnext18_lowend_census.py`), attaches `unit_hourly` to the keeper bundle where G-REPRO is exact, and records every number in the RESULT.
- The per-year replay dirs never reach `main`. They are gitignored in the parent (rule 29(c) / 32(d)).

**Retrievability (rule 34(e)).** These are keeper replays, so a promotion never needs them. The durable output is the keeper bundle's `unit_hourly` layer on `main`, plus the census JSON.
