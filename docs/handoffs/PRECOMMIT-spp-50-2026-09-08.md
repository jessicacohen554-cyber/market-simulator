# PRECOMMIT — SPP-50: the batched re-baseline (SPP-48's wind LEVEL repair + SPP-49's two input seams), keeper-3's recipe otherwise unchanged, full span in ONE invocation

**Lane** SPP-50 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-08 ·
**Branch** `claude/spp-50-rebaseline-eeys8j` · **Base** `cbf9be9f` (`origin/main` at launch) ·
**Data profile** `spp` · **Owner sequencing ruling** P19b (SPP desk r#13) — the two re-baselines are
**ONE** full-span solve, so the keeper that emerges is identified against the FINAL input surface.
**Control** keeper-3 `2026-09-07-spp-3-screened-input` / `results/calibration/spp43_screened_B`,
rule 29(b) **form 4** (the committed bundle IS the control; no control solve is spent).

**This document is pushed BEFORE the LP starts.** Every bar below is declared here and is not re-cut
after the result is seen — the discipline that made SPP-43's promotion clean and that rules 1
`[R-STRUCT]` / 29 `[R-SCREEN]` exist to enforce.

---

## 1. What moved since keeper-3 was solved — all of it INPUT, none of it mechanism

Keeper-3 (`git_sha 623184f3`, basis `dcb609f4`) is re-solved on its **own recipe, byte for byte**. No
new flag, no band, no floor, no bridge, no scarcity overlay, no offer-curve change; every offer band
stays 1.0 and `authorized_price_tuning` stays **NONE**. Three inputs beneath it have moved, plus one
scorer-side reference cell:

| # | mover | what | source |
|---|---|---|---|
| **(a)** | **SPP-48 R-LEVEL wind** | each zone's shape is now the capacity-weighted mean over its WHOLE operable fleet, not the six largest plants; `_SAMPLES_PER_ZONE` deleted (net **−1** free parameter). The solve-path parquets carried the retired rule until this lane regenerated them — SPP-48 deliberately did not. Declared magnitude: North **+1.915 / +2.304 / +2.131 TWh** (South equal and opposite), up to **9.0 GW** in a zone-hour | `FINDING-spp-48-2026-09-07.md` §0 |
| **(b)** | **SPP-49 seam 1** | `f923_gas_price_plausibility_screen`, a registered `ScenarioConfig` gate, **default ON**, declared at `("2026-09-08", "f923_gas_price_plausibility_screen", "True")`. SPP's keeper key moves **by design**. 2024: 60 low / 11 negative / 25 high plant-months across 19 plants — **90 rows, 10,409 MW, 31.9 %** of the gas fleet (2023: 66 / 5,865 MW; 2025: 48 / 5,445 MW) | `FINDING-spp-49-2026-09-08.md` §0.3 |
| **(c)** | **SPP-49 seam 2** | the simple-cycle heat-rate floor — an unconditional construction, non-CHP only: **21 SPP rows / 1,142 MW** clamped each year, Pioneer 57881 from **3.43 → 9.00** | `FINDING-spp-49` §0.3 |
| **(d)** | **scorer-side only** | `calibration_reference.json` `isos.SPP.2025.generation_twh.hydro` **0.0233 → 8.8299** — the EIA-923-preliminary vintage repair SPP-43 §6 (R-15) reported and routed. It is **NOT an LP input**: it must not appear anywhere in the array census of §3 leg (i), and it reaches only the determination | `git diff 623184f3 HEAD` |

## 2. G-DRIFT — the code-level drift audit (rule 29(b); zero LP)

`git diff 623184f3 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` → **34 files, +4,094 / −108**. Every hunk on
SPP's backcast path is classified below. **Form 4 is valid**: the only LIVE hunks are the two seams this
lane is deliberately re-baselining on, so the keeper's committed numbers are the control and **no control
solve is spent**.

| classification | files / hunks | reason |
|---|---|---|
| **LIVE — the declared movers** | `data/fuel/plant_prices.py` (+228), `data/fleet/eia860.py` (+114), `config/constants.py` `EGRID_CT_HR_PHYSICAL_FLOOR` + `F923_GAS_PRICE_PLAUSIBILITY_BAND`, `config/scenarios.py`'s gate + (b′-1) landing | seams 1 and 2 — §1 (b) / (c) |
| **LIVE — scorer only, never an LP array** | `data/raw/_validation-source/calibration_reference.json` SPP-2025 hydro | §1 (d) |
| INERT — default-off gate absent from keeper-3's recipe | `spp_gas_commitment_bridge` (`= False`) and everything it gates: `pipeline/commitment.py::build_spp_gas_bridge_p1_prep` (`if not (… and iso == "SPP")`), `floor_mechanisms.py` `MECH_SPP_GAS_COMMITMENT_BRIDGE`, `constants.SPP_GAS_BRIDGE_{MIN_LOAD_FRAC,MIN_RUN_HOURS}`, the `run_calibration*.py` threading | the ONLY new SPP-named mechanism since keeper-3; it is not in the recipe, so it never constructs |
| INERT — default-off gate | `netload_drag_layup_window_mask` (`= False`) → `data/fleet/floors.py`'s `layup_removed` clip basis (`None` ⇒ byte-identical, by its own docstring) | ercot-256's; absent from the recipe |
| INERT — default-off gate, other ISO | `ercot_zonal_spread_ep_referenced` (`= False`) → `data/fuel/basis/ercot.py`'s new `ercot_zonal_gas_basis_source_group`; the single removed line is inside an ERCOT-only branch | rule 25; ERCOT-only |
| INERT — forecast path a `mode="backcast"` run never enters | `config/iso_configs.py` (+68, PJM capacity-market overrides), `config/capacity_market.py`, `model/capacity_evolution/*`, `retirements.py`, `runner.py`'s ELCC/NQC hunks, `scripts/lib/confirmed_retirements/spp.py` (step 0), `data/raw/_validation-source/capacity_actuals_spp.csv` | keeper-3 is `mode="backcast"`, `hindcast=False` |
| INERT — gated on a flag absent from the recipe | `model/interchange/spec.py` (+274, SPP's `hr_by_year` filled by SPP-51) — reached only under priced interchange, which keeper-3 does not run (it uses served EIA-930 interchange); `model/reserves/spec.py` (+268, SPP's Contingency Reserve design) — gated `config.energy_reserve_coopt`, which is `False` | SPP-51 / SPP-55 landed their registries un-armed |
| INERT — hindcast-only branch | `data/neighbor_price.py`'s `_measured_henry_hub_annual` / `_HINDCAST_ASKNOWN_PREFIX` — fires only for a `hindcast_asknown_*` trajectory; keeper-3 runs `hindcast_fuel_variant="realized"`, `hindcast=False` | |
| INERT — not on the solve path | `scripts/lib/wind_shape.py` (build-time, produces (a)'s parquets), `scripts/lib/key_provenance.py` (instrument), `config/solve_surface_declared.py`, `pipeline/{kwargs,persist,year}.py` plumbing for the gated fields above | |
| INERT — other ISOs / other years | the CAISO LMP parquets; `calibration_reference.json`'s MISO / NEISO / NYISO cells; `actual_lmp.json`'s 2022 block | rule 25 |

**The `ScenarioConfig` delta since keeper-3 is five fields**, and exactly one defaults ON:
`f923_gas_price_plausibility_screen: bool = True` (the intended seam). The other four —
`spp_gas_commitment_bridge`, `netload_drag_layup_window_mask`, `ercot_zonal_spread_ep_referenced`,
`pjm_thermal_accreditation_vintage` — default `False` and are absent from keeper-3's recipe.

## 3. THE PRE-DECLARED PROMOTION RULE

Four legs. **All four must be MET.** If ANY leg fails or is ambiguous: **register the run** (rule 15 —
a rejected probe registers too), do **NOT** touch `keepers/SPP.json`, and **STOP** with the table, serving
the promotion question to the owner as **P15**. The rule is not re-cut after the result is seen.

### Leg (i) — IDENTITY, on the P0 objective and the LP INPUT ARRAYS, **never** a warm-started P1 objective

Desk error **E-8**: `P1 basis seed: ON` carries an earlier year's basis across years, so a degenerate
8760-hour LP lands a **different vertex of the same optimal face** and a bit-identity leg on P1 is not a
valid test — that is exactly what stopped keeper-3's own promotion (`FINDING-spp-43` §1). So this leg is
measured on (1) the P0 objective and (2) the LP input arrays, and P1 objectives are **reported, never
gated**.

The instrument is `docs/handoffs/spp50/array_census.py` (zero LP): keeper-3's fleet rebuilt with
`run_year(fleet_only=True)` on its own recipe (`scripts.replay_keeper.run_year_kwargs` +
`derived_run_year_inputs` — the sanctioned reconstruction, the seam SPP-49's census used), run **twice**:
`pre` in a code-only sparse git worktree at keeper-3's own `git_sha 623184f3` with the as-built wind
parquets in place, and `post` at HEAD with the regenerated ones. **The bar:**

| array | declared expectation |
|---|---|
| `wind_cf` | **MOVES**, all three years — mover (a). SPP-48's two-zone delta: ±3.5 % of each zone's annual energy, up to 9.0 GW in a zone-hour |
| `fuel_prices` | **MOVES** — mover (b). The own-reported flagged rows PLUS the nearby-plant pool that reads the screened frame; SPP-49 §0.4's realised row counts are 2023 **484** / 2024 **499** / 2025 **482** fleet rows across the six gas groups |
| `heat_rate` | **MOVES** — mover (c), **21 rows / 1,142 MW**, identically in each year |
| `mc_base` | **MOVES** — the union of (b) and (c) and nothing else |
| **everything else** | **IDENTICAL, bit for bit**: `pmax` `pmin` `vom` `emission_rate` `nox_rate` `so2_rate` `zone_idx` `fuel_type_idx` `plant_code` `availability` `min_gen` `wind_cap` `solar_cf` `solar_cap` `wind_mc` `solar_mc` `demand` `storage_power_cap` |
| **fleet shape** | unit count and `unit_id` order **identical** in every year. A clamped heat rate that re-binned a plant would change the fleet, and that would be a finding about seam 2, not a detail |
| P0 objective | **REPORTED** at full precision beside keeper-3's. All three years are expected to move — the inputs moved — so this is not a bar; a year whose P0 did **not** move would mean a repair failed to reach it |
| P1 objective | **REPORTED ONLY, never gated** (E-8) |

**Leg (i) is MET iff** the moved set is exactly `{wind_cf, fuel_prices, heat_rate, mc_base}`, the fleet
shape is unchanged, and mover (d) appears nowhere in it. Anything else that moves is named at full
magnitude and the leg FAILS.

### Leg (ii) — the wind identity holds in all three years

Keeper-3's defining structural identity: SPP's wind bound is the delivered EIA-930 series grossed up by
the SPP-32 **measured** reference curtailment rate 0.096501 — a year-invariant factor
**1.106808** — with **0.0 %** LP re-curtailment, so `model_wind / delivered_wind` **must** equal
**1.10681** in every year. It did, to five decimals, in all three years under keeper-3.

**Bar: |model/delivered − 1.106808| < 1e-5 in 2023, 2024 and 2025.**

This is a **real** test, not a tautology. R-LEVEL is a pure re-split — SPP-48 proved the system total
`M(t)` moves 0.000 MW in every hour — but it moves up to 9.0 GW of wind *across a seam served by a single
3,400 MW link*. If the LP can no longer deliver the re-split energy it will **re-curtail**, the identity
will break, and per the charter that is **a finding about the repair and this lane STOPs rather than
promotes**. Reported either way: the LP re-curtailment percentage per year.

### Leg (iii) — the attribution moves as SPP-49 §0.5 measured

Same rows, same direction, same order — or the solve is not carrying the repairs it is supposed to.
Measured with SPP-49's own instrument (`docs/handoffs/spp49/attribution.py`; 2024, GWh, model in-merit at
keeper-3's P1 prices minus CAMPD) on **this lane's** arrays. Because the wind parquets do not touch any
thermal marginal cost, this lane's thermal arrays should reproduce SPP-49's `post` arrays, so the bar is
tight:

| cohort | SPP-49 §0.5 "moved by" | bar |
|---|---:|---|
| CT_PEAKER — Pioneer 57881 (HR) | **−3,362** GWh | same sign, within ±10 % |
| CT_PEAKER — `fuel_low` (Elk, Mustang 4, Jones, Cunningham, Maddox …) | **−5,739** GWh | same sign, within ±10 % |
| ST_GAS — `fuel_low` (Harrington 6193) | **−4,643** GWh | same sign, within ±10 % |
| ST_GAS — **clean** cohort | **+6** GWh | stays put: \|Δ\| < 100 GWh |
| CC_REGULAR — `fuel_low` (Mustang CC, Redbud) | −698 GWh | same sign |

### Leg (iv) — the promotion bar, the desk's standing form (SPP-42's)

**No load-bearing criterion may go PASS → FAIL.** Keeper-3's scorecard is C1 FAIL · C2 PASS · C3a FAIL ·
C3b FAIL · C3c FAIL (ledgered caveat, rubric v3.3/v3.6) · C4 PASS · C6 PASS · C8 PASS. So the bar is:
**C2 and C4 stay PASS, and the protective criteria C6 and C8 stay PASS.** The DOF ledger must stay at
keeper-3's 3 entries / 0 tuned scalars / `authorized_price_tuning` **NONE** — with the arithmetic
adjustment that SPP-48 **deletes** `_SAMPLES_PER_ZONE`, so this run carries **one fewer** free parameter
than keeper-3, never one more.

**C1-2024's gas split is the criterion these repairs target** (keeper-3: CC_REGULAR −8.60 TWh / −3.0 pp,
CT_PEAKER +9.94 TWh / +3.4 pp) and it is **REPORTED AT FULL MAGNITUDE**, whichever way it goes.

**And, stated ex ante so it cannot be read as a rationalisation afterwards:** per rule 1 `[R-STRUCT]` the
promotion rests on this run being **the most structurally faithful** — two proven input repairs, net **−1**
free parameter, nothing tuned, no mechanism added — and **NOT** on whether C1 improved. A structurally
correct input repair stays in even if the residual worsens (rules 1 / 14), and a residual improvement is
not by itself a reason to promote. If C1-2024 gets worse, that is reported and the recommendation is
unchanged in its reasoning.

## 4. The solve — ONE invocation, full span, years sequential

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 2024 2025 \
    --out-dir results/calibration/spp50_rebaseline --hydro-backfill-year 2024 --hydro-eia930-monthly
```

Rules 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]`: one invocation, all three years, sequential within it.
Estimated ~7 min of LP for the span (SPP-46's figure). **Rule-12 concurrency check, before launch:**
`ListAgents` reports no other Claude session on this host and `ps` shows no `run_calibration*` process, so
this is the **only** per-plant SPP solve running (cap: 2). SPP-DESK is not reachable from this container to
be asked; the check that the ask exists to make is recorded here instead.

**Rule 22 `[R-HOLDOUT]`: no holdout year.** SPP holds no `complete` marker and 2023 / 2024 / 2025 are its
entire span. Nothing outside the training tier is solved, scored or registered.

## 5. Rule 31 `[R-RETAIN]` — the bundle-retention posture, declared before the bundle exists

`results/calibration/spp50_rebaseline/` is added to `.gitignore` **the moment it is written**, in the
shape the `miso243`/`ercot255` entries already use: gitignoring is what discharges rule 29 `[R-SCREEN]`
(c)'s delete-before-merge duty and keeps the parity gate green, and it is **NOT** a licence to delete.

**Nothing is deleted for any reason.** If the owner promotes, the ignore is **narrowed** — rule 15
`[R-DASHBOARD]` then requires the slim files plus the `hourly/` sidecars (`class_hourly_<year>.parquet`,
`system_<year>.parquet`, `reserve_family_<year>.parquet`) to be committed, exactly as the `miso243_sppair_K`
entry does. This container is ephemeral, so the FINDING will state plainly that the bundle lives on local
disk, will not survive the session, and that the promotion question is open.

## 6. What this lane will NOT do

- No new `ScenarioConfig` field, flag, band, floor, bridge, adder or scarcity overlay. If the result
  argues for one, that is a different lane and this FINDING says so instead of taking it.
- No edit to `scripts/lib/wind_shape.py` or to either SPP-49 seam file — they are LANDED and this lane
  **consumes** them. If one looks wrong, STOP and route to SPP-DESK.
- No shared record (§8.0 collision rule 1): not the plan, the ledger, `docs/calibration-log/spp.md` or
  `CHANGELOG.md`. The FINDING carries a `## Log entry` block for the desk to append.
- No other ISO's keeper shard, status, bench, sidecar, log or matrix shard; nothing under
  `frontend/data/forecast/`.
- **`keepers/SPP.json` is untouched unless the owner rules the promotion in-session.**
