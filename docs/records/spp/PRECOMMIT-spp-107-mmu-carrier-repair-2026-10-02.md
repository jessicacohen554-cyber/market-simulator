# PRECOMMIT — SPP-107: the repaired MMU offer-side carrier (arm EXR)

- **Lane:** SPP-107, on the owner card **"Build + solve EXR (Rec.)"** (2026-10-02).
- **Design and phase 0:** `docs/records/spp/DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md`.
- **Keeper / control:** `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (git `11b72265`).
- **Written before any solve. Nothing below is chosen from a solved number.**

## 1. What is solved: the keeper plus exactly two fields

| arm | set on the keeper recipe | what it does |
|---|---|---|
| **EXR** | `spp_mmu_offer_unavailability = true` (SPP-106) + `spp_mmu_offer_repair = true` (new, default off) | EX's MMU bands, built on the MMU's own definitions: (1) every band multiplies the row's post-outage availability, `a × (1 − share)`; (2) the economic → emergency slice is a per-zone `emergency_band` pool offered at `shed price − ε` ($1,999.999), so it clears only where the zone would otherwise shed load |

- **Zero free parameters.** The shares come from `data/raw/spp-mmu-unavailable-capacity` (unchanged, sha
  `37ce73e9`). The pool price is the LP's registered shed price minus rule 9's ε.
- **The built path reproduces the instrument.** On the 2024 `fleet_only` rebuild, the fossil rows match the
  probe's arm M to < 1e-4 MW and the South pool to < 1e-4 MW.

## 2. Prediction (zero LP; DESIGN §3)

| year | Δ all / Δ upper, $/MWh (re-clear, vs keeper) | C3a: keeper → predicted | South capacity vs keeper in EX's short hours |
|---|---|---|---|
| 2019 | +0.33 / +0.46 | +11.5 → ≈ +13.1 % | — |
| 2020 | +0.26 / +0.34 | +27.5 → ≈ +29.3 % | — |
| 2021 | +0.93 / +0.19 | +6.5 → ≈ +9.5 % | — |
| 2022 | +0.83 / +0.67 | −5.8 → ≈ −3.1 % | +148 MW |
| 2023 | +0.26 / +0.28 | −6.7 → ≈ −5.3 % | — |
| 2024 | +0.11 / +0.06 | −8.6 → ≈ −7.7 % | +115 MW |
| 2025 | +0.35 / +0.27 | −5.4 → ≈ −3.3 % | +93 MW |

- **Unserved energy:** at or below the keeper's in 2022 / 24 / 25 (0 / 862 / 136 MWh).
- **Pool energy:** a few hundred MWh to ~1 GWh/yr, all of it in hours that would otherwise be short.

## 3. G-DRIFT (rule 29(b), form 4)

- **Keeper `11b72265` → SPP-106 pin `392633a1`:** audited all INERT by SPP-104, SPP-105 and SPP-106 (their
  PRECOMMITs §3 and addenda).
- **`392633a1` → this branch's base `a6f554f3`:** 26 commits on the rule-29(b) path set (`src/market_sim`,
  `scripts/run_calibration*.py`, `scripts/replay_keeper.py`, `scripts/lib`, `data/raw/_validation-source`,
  `data/raw/reference`). Every flag cited was checked in all seven keeper `run_config_<Y>.json`:

| commit(s) | verdict | reason |
|---|---|---|
| cleanup-C `64f27f3c` (144 files) | INERT | docstring-masked ASTs identical apart from `docs/` / `results/` path strings in help text, errors and citations; the one code change (`topscoped_encode.py`) is ERCOT-only and off the solve path |
| R-ERCOT-24 `58d9ce36`, `02f67d13`; R-ERCOT-23 `651723e3`; R-ERCOT-22 `f4d29d72` | INERT | `ercot_ordc_published_curve` / `ercot_swcap_effective_hourly` absent (default False) and ERCOT-gated; the off-path cost broadcast is numerically identical; the LOLP vintage is ERCOT-only. (`02f67d13` is labelled AST-identical but rewrites an ERCOT-only call; behaviour-preserving) |
| NWPP-NEXT-16 `91141abf` | INERT | deleted code reachable only under `campd_per_unit_attribution` and `campd_unit_fuel_split`, both False in every SPP year |
| `cc_mustrun_conduct_window` `082c8315`, `073e6669` | INERT | absent (default False); off path unchanged |
| NYISO-NEXT-23 / 25 / 26 `05a136d5`, `b6e8ffe5`, `9d288842` | INERT | default-off flags inside NYISO-only blocks |
| soco-97 / 98 `2eac46ec`, `03a1903e`, `b499b7b1`, `b01b0a9e`, `7ca4fd04` | INERT | SOCO interface entries, comments, and a FERC-714 lambda loader the solve does not call |
| R-ERCOT-21 `8f4121a3` | INERT | one ERCOT plant (55154) in ERCOT-only reference files |
| nyiso-next22 `5b93b84d` | INERT | `actual_lmp.json` diff touches only `/NYISO/*` keys; SPP actuals unchanged |
| `d5e04018` (unit_marginal) | INERT | output-only sidecar written after the solve |
| `163db323`, `908d67c1`, `d3e16f23`, `3fa42239`, `f46350d5`, `171e8ff3`, `e9b06eac` | INERT | build tooling, CAISO data-curation libraries, bench / governance metadata; none on the solve path |

- **This lane:**

| files | verdict | reason |
|---|---|---|
| `scenarios.py`, `fleet/models.py` (fuel code 17), `fleet/arrays.py`, `spp_mmu_unavailability.py`, `results/export.py`, `run_calibration.py`, `run_calibration_full.py`, `runner.py` | **LIVE only under `spp_mmu_offer_repair`** | Default off, and the field requires its parent. Unarmed, `_spp_mmu_repair_armed` is False: the bands keep the additive path (`multiplicative=False`), no pool row is built, and `_apply_spp_mmu_pool` does not run. The export exclusion and the sidecar class label match a fuel no unarmed fleet carries. `check_cache_key_registration --base origin/main`: "1 new field(s), all registered" |

**All drift rows are INERT for the keeper recipe, so the committed keeper is the control** and no control
solve is spent.

**Fast tier at this commit:** 11,141 passed, 2 failed, both in
`tests/unit/data/test_gas_offer_zonal_anchor_vintage.py` (NYISO; open on `main` at lane start, other lane).
`tests/iso/spp` passes, matrix guard and cache-key registration (`--base origin/main`) are ok.

## 4. Solve plan (rule 36)

- **Seven shards, one year per shard, 2019–2025.** All are pinned to one full SHA on this branch and launched
  in one message. A shard stuck PENDING for more than 15 min is archived and relaunched.
- **Each shard:**
  1. runs `replay_keeper.py results/calibration/spp100_arm_span --years <Y> --set
     spp_mmu_offer_unavailability=true --set spp_mmu_offer_repair=true --out-dir
     results/calibration/spp107EXR_<Y>`;
  2. runs `scripts/probes/_spp107_shard_check.py`, which is the SPP-106 checks with the arm swapped, plus pool
     present, pool offer = $1,999.999, and pool clearing in scarcity hours only;
  3. pushes its full bundle, including `dispatch/<Y>_P1.parquet`, to `claude/spp107exr-<Y>`.
- **The parent solves nothing.** It composes the seven legs, regenerates the legitimacy diagnostics, attests,
  registers locally and scores.

## 5. Expectations (fixed before any solve)

| # | expectation |
|---|---|
| E1 | `SPP-107 SHARD CHECK: PASS` on all 7 legs (this includes pool present, pool offer and scarcity-only) |
| E2 | Every year solves Optimal within the shard budget |
| E3 | No year's unserved energy rises by more than 500 MWh over the keeper |
| E4 | D-4: no FAIL row the keeper does not carry (keeper: 7) |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1 / C3a / C3b / C4 status flip in 2023–25 |
| E6 | Instrument check: in each of 2023–25, train C3a moves toward zero by less than EX's solved move (EX: +2.3 / +2.6 / +3.8 points) |

**Reported, not gated:**
- per-year ΔC3a, ΔC3b, ΔC3c and class TWh (CT_PEAKER, CC_REGULAR, ST_GAS, COAL_PRB);
- Δprice (all hours and upper tercile);
- pool MWh and hours by zone;
- validation 2019–22 at full magnitude, 2021 C3a included (predicted ≈ +9.5 %, at the ±10 % edge).

## 6. Recommendation rule (fixed)

- **RECOMMEND PROMOTE iff E1–E5 hold.** The basis is rules 1 and 14: the flat uncited derates are replaced by
  SPP's own measured classes, built on the source's own definitions, with zero free parameters.
- **E6 failing** is reported and does not change the recommendation (rule 1), but it means the DESIGN's
  instrument mis-sized the repair, and that gets said.
- **Otherwise RECOMMEND AGAINST.**
- The owner decides (rule 31). Validation-year movement is reported at full magnitude and is never the basis.

## 7. Year set (rule 35(b))

SPP's registered years are 2019–2025, all on keeper `2026-09-28-spp-100-chp-scope`. All seven are solved.

## 8. Shard check, tested before launch

`scripts/probes/_spp107_shard_check.py` was run on three synthetic 2024 legs built from the keeper (hourly
sidecars copied, recipe edited, a placeholder `dispatch/2024_P1.parquet`, a synthetic `unit_marginal` with
two pool rows):

| synthetic leg | expected | result |
|---|---|---|
| EXR recipe, South pool 120 MW in an hour priced $1,999.999 | PASS | **PASS** |
| EXR recipe, the same pool hour priced $35 | FAIL | **FAIL** (SCARCITY-ONLY) |
| EX recipe only (repair field not armed) | FAIL | **FAIL** (RECIPE) |

Prompt: `docs/records/spp/spp107/shard_prompt_template.txt`.
