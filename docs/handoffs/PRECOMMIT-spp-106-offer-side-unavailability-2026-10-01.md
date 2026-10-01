# PRECOMMIT — SPP-106: MMU offer-side unavailability carrier EX

Lane: SPP-106. Owner card **"Build EX anyway"** (2026-10-01), over the DESIGN's recommendation to
record a model-class limit.
Design and phase 0: `docs/handoffs/DESIGN-spp-106-offer-side-unavailability-2026-10-01.md` (§4–§5).
Keeper / control: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (git `11b72265`).
**Written before any solve. Nothing below is chosen from a solved number.**

## 1. What is solved: one arm, the keeper plus exactly one field

| arm | set on the keeper recipe | what it does |
|---|---|---|
| **EX** | `spp_mmu_offer_unavailability = true` (new field, default off) | on every SPP gas / coal / oil row, the flat GADS performance derate and the flat summer class derate (CC 10 %, CT 12.5 %) are replaced by the SPP MMU's measured bands: above-emergency-max share + economic-to-emergency-max share all year, plus ambient MW-days on Jun–Sep |

- **Zero free parameters.** Every value is read from `data/raw/spp-mmu-unavailable-capacity` (MMU Dec 2025,
  digitized ±~100 MW; Fig 12 exact). 2019 holds 2020 and 2025 holds 2024. That hold rule is the
  DESIGN's, fixed before any number was computed.
- **Rule 14, the structural case.** The replaced `SUMMER_CLASS_DERATE` is recorded in code as an "UNCITED
  FLAT APPROXIMATION". The arm swaps it for SPP's own measured classes.
- **Declared at the gate.** The inputs are digitized annual figures from a one-off white paper. The
  recurring ASOM gives only a combined figure, ~16 % lower for 2024. Reliability-status capacity is
  deliberately not carried (rule 21).

## 2. Prediction (zero LP; DESIGN §4; the built path reproduces the instrument: 2024 upper +0.434 vs +0.433)

Re-clear instrument, Δ$/MWh all hours / upper tercile, against the keeper:

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| +0.53 / +0.81 | +0.41 / +0.61 | +1.47 / +0.70 | +1.28 / +1.26 | +0.45 / +0.58 | +0.32 / +0.43 | +0.65 / +0.74 |

- No short hours in any year. The 2024 minimum fossil margin is +1.17 GW (keeper +0.61).
- **Direction of the train-tier C3a** (keeper −6.7 / −8.6 / −5.4 %): it should improve slightly, with
  ~+1–2 % of the RT mean at most. The over-priced validation years 2019–20 (C3a +11.5 / +27.5 %) should
  worsen by a similar amount.

## 3. G-DRIFT (rule 29(b), form 4): keeper `11b72265` → this PR's base `e7fd8931`

- **Up to SPP-105's merge (`190af2c0`):** audited all INERT by SPP-104 and SPP-105 (their PRECOMMITs §3 and
  addenda).
- **`190af2c0 → e7fd8931`,** over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/replay_keeper.py`,
  `scripts/lib`, `data/raw/_validation-source` and `data/raw/reference`:

| commit(s) | files | verdict | reason |
|---|---|---|---|
| SPP-105 `7105f162`, `400d7bd6` | `paths.py`, `scenarios.py`, `fleet/arrays.py`, `spp_gas_outage.py`, `data/raw/spp-gen-outage/` | INERT | `spp_gas_crow_residual_outage`: default False, absent from the keeper recipe; `crow_rate_out=None` on every unarmed call |
| R-ERCOT-19 `41e0f242` | `run_calibration.py`, `scenarios.py`, `commitment_profile.py`, `fleet/floors.py`, `offer_curves.py`, `reference/ercot_prior_year_commitment_profile.*` | INERT | two sub-gates, default False. `load_prior_year_commitment_profile` returns None when its flag is off, and `cc_committed_offer_margin` is off in SPP's recipe. The new `year` argument is pass-through only |
| NWPP-NEXT-14 `dd40dac5`, `1d83b224` | `run_calibration.py`, `constants.py`, `scenarios.py`, `solve_surface_declared.py`, `fleet/assembly.py`, `fleet/eia860.py`, `fleet/campd_bins.py` | INERT | `cc_subfloor_eia923_heat_rates` and `campd_per_unit_vintage_denominator`: default False, absent from SPP's recipe; every new branch is behind its flag |
| R-CAISO-20 `cd589798` | `scenarios.py`, `eia930/envelopes.py`, `interchange/caiso.py`, `interchange/spec.py` | INERT | `caiso_dsw_overnight_clean_unprinted_arm`: default False, CAISO intertie path only |
| **this lane** | `paths.py`, `scenarios.py`, `fleet/arrays.py`, `spp_mmu_unavailability.py`, `data/raw/spp-mmu-unavailable-capacity/` | **LIVE only under `spp_mmu_offer_unavailability`** | Default off. `_spp_mmu_armed` is False on every unarmed call, so no derate is skipped and no band is removed. `check_cache_key_registration --base origin/main`: "1 new field(s), all registered" |

All rows are INERT for the keeper recipe, so **the committed keeper is the control** and no control solve
is spent.

## 4. Solve plan (rule 36)

- **Seven shards, one year per shard, 2019–2025.** All are pinned to this PR's merge SHA and launched in
  one message. A shard stuck PENDING for more than 15 min is archived and relaunched.
- Each shard runs `replay_keeper.py results/calibration/spp100_arm_span --years <Y> --set
  spp_mmu_offer_unavailability=true --out-dir results/calibration/spp106EX_<Y>`.
- It then runs `scripts/probes/_spp106_shard_check.py --arm EX` and pushes its full bundle, including
  `dispatch/<Y>_P1.parquet`, to `claude/spp106ex-<Y>`.
- **The parent solves nothing.** It composes the seven legs, regenerates the legitimacy diagnostics,
  attests, registers locally and scores.

## 5. Expectations (fixed before any solve)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all 7 legs |
| E2 | Every year solves Optimal within the shard budget |
| E3 | No year's unserved energy rises by more than 500 MWh over the keeper |
| E4 | D-4: no FAIL row the keeper does not carry (keeper: 7) |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1/C3a/C3b/C4 status flip in 2023–25 |
| E6 | Direction: the upper-tercile mean price rises in each of 2023–25 (the DESIGN's prediction) |

**Reported, not gated:** per-year ΔC3a, ΔC3b, ΔC3c, class TWh (CT_PEAKER, CC_REGULAR, ST_GAS, coal),
Δprice, and the carrier's logged bands per year.

## 6. Recommendation rule (fixed)

- **RECOMMEND PROMOTE iff E1–E5 hold.** The basis is rule 14: an uncited flat approximation is replaced by
  SPP's own measured classes, with zero free parameters.
- **E6 failing** is reported and does not change the recommendation, since a residual is never the basis
  (rule 1). A failing E6 would, however, mean the DESIGN's instrument is wrong, and that gets said.
- **Otherwise RECOMMEND AGAINST.**
- The owner decides (rule 31). 2019–22 movement is reported at full magnitude and is never the basis.

## 7. Year set (rule 35(b))

SPP's registered years are 2019–2025, all on keeper `2026-09-28-spp-100-chp-scope`. All seven are solved.

## 8. Shard check, tested before launch

`scripts/probes/_spp106_shard_check.py` was run on four synthetic 2021 legs built from the keeper (hourly
sidecars copied, recipe edited, a placeholder `dispatch/2021_P1.parquet`):

| synthetic leg | expected | result |
|---|---|---|
| EX recipe, price +0.5 | PASS | **PASS** (DATA CHECK passes on the MMU CSV sha `37ce73e9`) |
| EX recipe + stray `hydro_pondage_bound` | FAIL | **FAIL** (RECIPE) |
| EX recipe, leg identical to the keeper | FAIL | **FAIL** (ARMED) |
| keeper recipe (field not armed), price +0.5 | FAIL | **FAIL** (RECIPE) |

Prompt: `docs/handoffs/spp106/shard_prompt_template.txt`.
