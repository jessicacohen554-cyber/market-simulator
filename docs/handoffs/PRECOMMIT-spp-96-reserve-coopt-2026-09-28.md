# PRECOMMIT — SPP-96: queue item 6 (SPP-56, reserve co-optimisation M2), non-inertness proof at zero LP

**Lane** SPP-96 · keeper `2026-09-28-spp-94-curtail-rows` (bundle `results/calibration/spp94_arm_span`, `git_sha`
`020bb1c5`) is the control (rule 29(b) form 4) · written **before** any measurement below was run.

## 1. Why this lever (rule 28(a))

The §5.7 queue, item by item:

| item | state |
|---|---|
| 1 SPP-51 priced seams | R (killed at phase 0, 2026-09-07) |
| 2 SPP-52 curtailment | done as input: `vre_reference_rate_year_own` K, rows complete 2019–25 (SPP-67/94/95) |
| 3 SPP-53 N↔S TTC | out of scope (re-rating the link); SPP-92 closed the width question |
| 4 SPP-54/57 pockets | topology; West/East stays O pending a ruling (SPP-93); out of scope |
| 5 SPP-55 scarcity | I (killed at zero LP) |
| **6 SPP-56 reserve co-opt (M2)** | **U — the only queue item never adjudicated.** Its charter gate is a *measured non-inertness proof before any LP*. SPP-merit-order also names it as the prerequisite for the top-of-stack leg SPP-79 says any body lever must be paired with. |

Off-queue O cells were considered and not taken: `chp_steam_following` is R (owner "Don't promote"; re-open only as the
scoped non-cycling form, and the solved arm moved CC_REGULAR the wrong way for 2021–22); `dam_availability_rebasis` is
owner-gated and would add coal, the wrong direction for the 2021–22 swap.

Scope: this lane measures. It does not touch ramp limits (PARKED), SPP-91's coal-headroom question, gas price, the
N↔S rating, or the partition.

## 2. The object and the tests (zero LP)

A reserve row in an hourly LP can move an energy dual only in an hour where the reserve-eligible headroom
(available − dispatched) is below the requirement. SPP-55 measured this for the contingency family alone (1.5 GW) on
2023–25 of an older keeper: 0 / 1 / 0 hours. M2 adds Regulation and the 2022+ Ramp / Uncertainty products, and the
failing years are 2019–22, so the test is repeated on the current keeper for every year with the full up-requirement.

- **T1 — market-side weight.** From `data/raw/spp-or-mcp/RTBM_MCP_<Y>.csv.zip` (5-min, per Reserve Zone): hourly
  mean over intervals of the zone-mean RegUp, Spin and Supp MCP, against the keeper's actual-LMP benchmark
  (the scorer's own RT series). Reported per year: mean MCP by product, and `mean(Spin MCP) / mean(RT LMP)`.
- **T2 — model-side bindability.** Rebuild the keeper fleet per year with `run_year(fleet_only=True)` through
  `replay_keeper.run_year_kwargs` + `derived_run_year_inputs` (the SPP-55 construction, no LP). Headroom_t =
  Σ(pmax × availability) over `_reserve_eligible` − Σ P1 dispatch of the eligible classes (`class_hourly_<Y>`).
  Requirement_t = SPP's **measured cleared** up-reserve MW, `regup + spin + supp (+ rampup + uncup where posted)`,
  from `data/raw/_validation-source/spp_rtbm_or_cleared_hourly.parquet` — a deliberate over-statement of what a
  requirement would be (cleared ≥ requirement), so the test is biased *toward* finding bind hours.
  Count hours with headroom < requirement, per year.
- **T3 — sign.** Declared, not measured: a reserve row only adds a non-negative term to the energy dual. It cannot
  lower a price.

## 3. Expectations, fixed now

| # | expectation |
|---|---|
| E1 | T2 bind hours **≤ 20 in every year 2019–2025** (SPP-55 found 0–1 at 1.5 GW; the full up-requirement is larger, ~2–3 GW, but keeper headroom p1 was 6.3–7.0 GW). |
| E2 | T2 median headroom ≥ 5 × median requirement in every year. |
| E3 | T1 is reported, not predicted. It is a necessary leg, not a sufficient one. |
| E4 | T3: in 2019 and 2020 (C3a over-price +11.5 % / +27.8 %) the lever is wrong-signed by construction. |

## 4. Recommendation rule, fixed now

- **Earns a solve** only if **both** (a) T2 bind hours ≥ 88 (1 % of hours) in at least one failing validation year
  2019–22, **and** (b) in that year T1 `mean(Spin)/mean(LMP)` ≥ 5 %. Even then the solve is not this lane's: SPP has
  no Reg/Spin/Supp design (`_spp_design` builds the contingency family only), so the result is a design charter put
  to the owner, not seven shards.
- **Otherwise: INERT.** No shard is launched. `energy_reserve_coopt` stays **I** (evidence extended to M2 and to
  2019–25); `reserve_pergen` and `reserve_deliverability_scoping` stay **U** with the measurement attached (the only
  way to make the row bind is to shrink eligible headroom to what can deliver in 5–10 minutes, which is the ramp
  family — PARKED). SPP-56 is closed as a queue item.

No number below is used to choose a threshold; the thresholds above are final.

## 5. G-DRIFT, keeper `020bb1c5` → HEAD `6ca311d4` (rule 29(b), form 4)

`git diff 020bb1c5 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` touches 7 files. Every hunk:

| file | hunk | class | reason |
|---|---|---|---|
| `data/raw/reference/custom-bin-assignments.csv` | W A Parish capacity split (3470 / 34702) | INERT | ERCOT sheet; no SPP plant |
| `scripts/run_calibration.py`, `runner.py` | `sd_floor_static` arg to `apply_caiso_local_import_limits` | INERT | CAISO branch only |
| `model/interchange/caiso.py` | same | INERT | CAISO only |
| `config/scenarios.py` | `campd_st_gas_span_coverage`, `caiso_import_cap_floor_static` fields + cache-key defaults | INERT | default off, absent from the keeper recipe |
| `data/resolved_inputs.py` | `_fuel_split_companion(base, fuel_split)` | INERT | reached only under `campd_unit_fuel_split`, off in the keeper |
| `data/fleet/campd_bins.py` | `split_child_parent_codes` (R-ERCOT-11) | INERT | fires only on `[TAG]`-suffixed rows of `custom-bin-assignments.csv` (ERCOT's sheet; 4 tagged rows, no SPP plant) |
| `data/fleet/campd_bins.py` | `campd_fuel_split_selector` returns a tag under the stcov sub-gate | INERT | sub-gate of a flag that is off in the keeper; the unarmed return is unchanged |

**All hunks INERT.** Form 4 is valid; the keeper is the control. (This lane expects to spend no LP either way.)
