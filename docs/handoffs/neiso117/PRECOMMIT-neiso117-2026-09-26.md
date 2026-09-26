# PRECOMMIT neiso-117 — NEISO coal fuel-inventory budget, per-yard ANNUAL rows only (2026-09-26)

Keeper (precondition verified): `2026-09-25-neiso114-arm-b-stgas`, bundle `results/calibration/neiso114b_span`,
years 2019–2025. Train tier 2023–2025 CALIBRATED (C3c ledgered); full span NOT-YET on C1 CC_REGULAR only
(2019 −2.87 TWh, 2022 −3.03 TWh). Phase 0: `docs/handoffs/neiso116/PRECOMMIT-neiso116-2026-09-26.md`.

## 1. Owner rulings (2026-09-26, asked before any solve — PRECOMMIT-neiso116 §5)

| # | question | ruling |
|---|---|---|
| 1 | arm the coal fuel budget for NEISO? limb shape? | **YES — per-yard ANNUAL rows only**; make them armable WITHOUT the pooled monthly limb (budget/12 is winter-hostile: it binds Merrimack in 2023/2024) |
| 1(b) | add PSEG Provport 8858 to the shared-storage crosswalk for Bridgeport 568? | **No** (census as-is) |
| 2 | Merrimack delivered price (Bailey peers + measured premium)? | **Keep the placeholder** (isolate this arm) |
| 3/4 | tranche re-derive / committed measured basis | **Defer both** (later arms, own phase 0) |

## 2. Code change (this commit)

`scripts/run_calibration.py`: new pure gate `resolve_coal_budget_arms(config, iso) -> (pooled_monthly, plant_annual)`
replaces the two inline raises. `coal_fuel_inventory` (pooled monthly limb) stays **MISO-only**;
`coal_fuel_inventory_plant_grain` (per-yard annual rows) is armable **alone**, gated to
`COAL_PLANT_GRAIN_ISOS = ("MISO", "NEISO")` (rule 25: NEISO enters on its own EIA-923 evidence); both stay
backcast-only. Rule 19: the yard rows are the annual identity's plant partition; the pooled rows add only its
month grain — separable limbs of one mechanism, not two mechanisms. MISO's two-limb recipe resolves `(True, True)`
exactly as before; every config that previously solved is byte-identical (the only behaviour change is a config
that previously RAISED now solves). No new `ScenarioConfig` field (rule 28(c) N/A). Test:
`tests/unit/pipeline/test_coal_budget_arms_gate.py` (6 cases). Zero free parameters (rule 21).

## 3. G-DRIFT (rule 29(b)) — `f30e3704` → HEAD `722b40f9`: ALL INERT

`git diff f30e3704 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` touches 5 files:

- `data/fleet/arrays.py`, `data/outages.py` — `unit_outage_window_hour_grain` routing for ERCOT's `-hourgrain`
  companions (R-ERCOT-5). INERT: keeper has `unit_outage_window_hour_grain=False`, ERCOT-only branch.
- `data/outages.py::unit_layup_csv_for_iso` new selector args (default False → same file); `run_calibration.py::
  _reliability_floor_layup_shares`, `model/interchange/core.py` `layup_removed`, `scenarios.py`
  `reliability_floor_layup_window_mask` (NYISO-NEXT). INERT: new field default-off and absent from the keeper
  recipe; returns `None` when off.

**Rebase window `722b40f9` → `cf0950dc`** (main moved before the pin): 4 files, one hunk family —
`unit_outage_unit_fuel_routing` (PJM-NEXT-3, `-memberrepair-unitfuel-` extract companion). INERT: new field,
default False, frozen cache-key drop value `"False"`, absent from the keeper recipe.

Form 4 stands for every year: the keeper's committed bundle is the control; no control solve.

## 4. Phase 0 on the ARMED code path (zero LP) — `phase0_yard_rows_probe.py` → `.json`

Keeper fleet rebuilt per year with `run_year(fleet_only=True)` on `replay_keeper.run_year_kwargs` +
`coal_fuel_inventory_plant_grain=true`; `build_coal_plant_budget` called exactly as `run_year` calls it. Every yard
row equals the neiso-116 census budget to the reported precision (TBtu):

| year | 568 Bridgeport | 2364 Merrimack | 2367 Schiller | rowed yards |
|---|---|---|---|---|
| 2019 | 3.112 | 6.354 | 3.003 | 3 |
| 2020 | 3.942 | 7.212 | 2.508 | 3 |
| 2021 | 4.093 | 9.234 | — | 2 |
| 2022 | 0.000 | 7.678 | — | 2 |
| 2023 | — | 9.645 | — | 1 |
| 2024 | — | 9.698 | — | 1 |
| 2025 | — | 4.813 | 0.000 | 2 |

All 15 rows equal the census budget exactly; the gate resolves `(False, True)` on every year's config.

**Input precondition found in phase 0:** the budget reads CURATED `data/clean/coal-{stocks,receipts}` (gitignored).
Without `scripts/data/curate_coal_stocks.py` + `curate_coal_receipts.py` the builder returns `None`, `run_year`
logs `NOT APPLIED` and the solve is silently the keeper. Every shard curates first and hard-stops unless its log
carries a `coal per-yard budget (NEISO <Y>): N yards` line (N per the table above).

## 5. Recipe — declared before any solve

Every leg: `uv run python scripts/replay_keeper.py results/calibration/neiso114b_span --years <Y>
--set coal_fuel_inventory_plant_grain=true --out-dir results/calibration/neiso117_<Y>`. One arm, no control
(form 4). Delta on the keeper: `coal_fuel_inventory_plant_grain` False → True; `coal_fuel_inventory` stays False;
offer curve byte-identical (no authorized-price-tuning change). DOF: zero new.

## 6. Gates — declared before any solve (structural; rule 1)

A passing gate does not promote and a failing one does not kill; both are reported at full magnitude.

- **G1 recipe:** `docs/handoffs/neiso117/shard_check.py` passes on every leg; log line
  `coal per-yard budget (NEISO <Y>)` present, `NOT APPLIED` absent.
- **G2 mechanism fires where predicted:** annual yard burn (Σ HR·P) ≤ budget + 1e-6 relative on every rowed yard;
  binding (burn within 0.5 % of budget) at 568 & 2364 in 2019, 2364 in 2021 and 2022, 2367 in 2025 (budget 0).
  Slack years 2020, 2023, 2024: every class TWh equal to the keeper's within 0.01 TWh (inert prediction).
- **G3 no silent breakage:** C1, C2, C3a, C3b, C4, C8 re-scored per year on one benchmark; train tier 2023–2025
  must stay CALIBRATED for a promote recommendation.
- **Predictions (stated before the solve):** 2022 C1 CC_REGULAR −3.03 → ≈ −1 TWh (inside band) if CC absorbs most
  of the 2.2 TWh Merrimack cut; 2019 volume inside ±2.81 but share leg (−4.0 pp) may stay just outside ±3 pp;
  2021 CC_REGULAR improves by ≤ 0.65 TWh; 2025 moves ≤ 0.13 TWh.

## 7. Shard plan (rule 36 — one shard per year; rule 34 — full bundle pushed)

Seven shards `neiso117_<Y>`, 2019–2025 (the keeper's whole year set, rule 34(c)), pinned to this doc's commit
SHA (§8). Branch `claude/neiso117-<Y>`. Full bundle incl. `dispatch/<Y>_P1.parquet` pushed via `.gitignore`
negation + plain `git add`. Parent composes (`docs/handoffs/neiso117/compose_span.py`), attests, registers
`--no-prune`, scores; it never solves (rule 32(a)). Per-year dirs gitignored in the parent's tree.

## 8. Launch record

All seven pinned to **`17402f351e5dc3d45126100b7839531cd21c1ca3`** (this doc's first commit, on `cf0950dc`),
created 2026-09-26 01:28 UTC, tag `neiso117`. Branch `claude/neiso117-<Y>`, out-dir `neiso117_<Y>`.

| year | shard session |
|---|---|
| 2019 | `session_01HCR54dMpxMrELwDJ3vYcF8` |
| 2020 | `session_01AnqN2uUmLU99H9dgXFWms3` |
| 2021 | `session_01CU49KTyFBepnC7eDNoMdXt` |
| 2022 | `session_01AxP61vTrmhf99qhNbzS2ka` |
| 2023 | `session_019HiqKfoVDc1a8DBVFkZwAx` |
| 2024 | `session_011W6dpXacaJVxBHZPNDuawG` |
| 2025 | `session_01MNUF1v7Zi4WWMbU84361J1` |
