# FINDING — SPP-93: West/East re-partition. It is admissible on measured prices and the link rates cleanly, but the pre-solve feasibility leg C-3 STOPS it. No shard launched.

**Lane** SPP-93 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`) ·
**PRECOMMIT** `PRECOMMIT-spp-93-west-east-2026-09-27.md`, on `main` at `599f45a6` (PR #6804) **before any model output
existed** · records `docs/handoffs/spp93/` · keeper unchanged, nothing solved or registered, no promotion question (rule 31).

## 0. Bottom line: the STOP-leg table

| leg (PRECOMMIT §) | test | result | verdict |
|---|---|---|---|
| A1 (§1.4) | actual mean (East − West) > 0 in every year 2019–25 | +3.66 / +3.82 / +10.70 / +15.99 / +2.84 / +4.79 / +3.05 $/MWh | **PASS** 7/7 |
| A2 (§1.4) | actual mean \|E − W\| > mean \|S − N\| in ≥ 5 of 7 years | 5.92 vs 5.02 · 6.71 vs 5.54 · 15.32 vs 13.85 · 19.66 vs 14.84 · 9.79 vs 9.28 · 15.08 vs 12.02 · 15.11 vs 12.59 | **PASS** 7/7 (2023 margin thin) |
| R1 (§2) | ≥ 3 identified constituents with L_f | 18 of 37 identified (ψ > 0, t ≥ 2), all 18 carry an L_f | **PASS** |
| R4 (§2) | hours-weighted p75/p25 ≤ 10 | 8,044 / 2,275 = 3.5 | **PASS** |
| R2 / R3 (§2) | TTC < B_plaus / B_hard | 4,000 < 20,889 < 33,293 MW | **PASS** |
| C-0 (§3) | every unit in one bubble; the two fleets are the same units | identical pmax and availability in all 7 years; 850 SWPP plants mapped, 0 unmapped | **PASS** |
| C-1 (§4.1) | Σ_z cap·cf = the N/S total, every hour | max rel. error 6.8e-16 to 8.2e-16 | **PASS** |
| C-2 (§4.1) | cf ≤ 1, no lost overflow | max cf 1.000 (2024: 0.989) | **PASS** |
| **C-3 (§4.1)** | no hour with min W/E bubble margin < 0 while min N/S margin ≥ 0 (keeper-slack hours exempt) | **14 hours**: 2019 3 · 2023 4 · 2024 6 · 2025 1 | **STOP** |

**The lane stops there, as declared.** No G-DRIFT-gated shard was launched and nothing was solved. The partition, the
link and the gate were not re-cut after the result (rules 1, 23).

## 1. The partition, and what the measured prices say about it

**Rule (PRECOMMIT §1, registry data only):** SPP's own reserve zones. West = RZ {1, 2, 3, 5}, East = RZ 4.

**Load side:** each sub-BA goes to the majority RESZONE of its LOAD settlement locations. West = LES, NPPD, OPPD, SECI, SPS,
WAUE, which is 37.9–39.7 % of energy (0.3954 pooled 2023–25).

**Plant side:** each EIA-860 generator's LMP node is matched to SPP's registry RESZONE, else placed by 1-NN on
coordinates (`data/raw/reference/spp_plant_reserve_zone.csv`, `scripts/data/derive_spp_plant_reserve_zone.py`). Coverage:
- 587 of 1,804 SWPP generators across the 2018–2025 vintages carry a node;
- 451 of those match the registry and 449 resolve to a bubble;
- that gives 162 plants node-labelled and 688 placed by 1-NN.

Named placements (SPP's own registry decides):

| plant | bubble | basis |
|---|---|---|
| Tolk, Harrington, Holcomb | West | node |
| Cooper, Nebraska City, Gerald Gentleman | West | node |
| **Iatan (MO)** | **West** | KCPL node in RZ 1 |
| Jeffrey, La Cygne, Sooner, Muskogee | East | node |
| Wolf Creek, Welsh, Flint Creek | East | 1-NN |

**Price admissibility (A1/A2), actual RTBM LMP** at all 112 load SLs, sub-BA-energy weighted, GMT − 7 h clock
(`_spp93_we_spread.py` → `spp93/we_spread.json`):
- West is the cheap side in every year: East is dearer in 70–85 % of hours.
- The new cut separates more than N/S in all seven years.
- For information only (P3, which selects nothing): the SW bubble (SECI + SPS) and the NW bubble (Nebraska + Dakotas) differ
  by $9–26/MWh mean |spread|, larger than either's spread to East. The West bubble is not homogeneous either.

## 2. The link: 4,000 MW (ψ₁), with ψ₂ ≈ 10,400 as a cross-check

**Construction:** SPP-53's FCITC on the ACTUAL E − W spread, 2023–25, OLS with HC1, 26,280 h, R² 0.312. The constituents
are `n_s_corridor` ∪ `sps_tie` (`_spp93_psi_we.py` → `spp93/psi_we.json`, `tstar_we.csv`).

**Result:**
- 18 constituents identified W→E, 12 loaded E→W.
- **TTC = 4,000 MW** (weighted median 3,967 at the Sibley 345/161 xfmr; p25 2,275 at Franklin 161/69; p75 8,044).
- No `sps_tie` constituent identifies W→E.

**ψ₂ (SPP-58's HIFLD DC-PTDF with a West→East pair added; informational, not a gate)**
(`_spp93_psi2_we.py` → `spp93/psi2_we.json`, `psi2_we_crosscheck.csv`):
- 8 of the 18 are loaded ≥ 0.005, carrying 3,694 of 11,951 identified binding hours.
- **T*₂ weighted median 10,449** (p25 9,570, p75 18,613).
- Franklin, Nashua, First Creek–Roanridge, Mullergren–Ellsworth and N345–Blackberry are unresolved.
- Sibley 345/161 (the ψ₁ median) reads 0.0021 and −0.0156, i.e. not loaded.
- This is the same pattern SPP-58 found for N↔S (3,400 vs 11,022): the price-based rating rests on sub-transmission elements
  the public line data cannot see.

**Rule-14 misalignment**, carried in the `_spp_config` comment:
- 2026 limits are applied to 2019–25;
- an element-under-contingency rating is not a corridor capability;
- ψ is identified on 2023–25 and applied to 2019–22.

## 3. The census (zero LP, the keeper recipe with the partition armed; `spp93/census.csv`)

| year | bubble | plants | thermal + hydro MW (coal / CC) | wind MW / TWh | demand TWh (min–max MW) | net position TWh |
|---|---|---:|---|---|---|---:|
| 2019 | West | 155 | 22,291 (9,478 / 1,734) | 12,431 / 48.2 | 102.9 (8,421–17,838) | +97.0 |
| 2019 | East | 143 | 36,917 (12,346 / 8,479) | 8,274 / 30.0 | 168.9 (12,279–33,886) | +61.7 |
| 2023 | West | 153 | 22,443 (9,433 / 1,746) | 17,944 / 65.5 | 111.8 (9,223–18,968) | +104.2 |
| 2023 | East | 142 | 35,958 (11,253 / 8,583) | 14,911 / 47.2 | 172.7 (13,153–35,672) | +70.6 |
| 2025 | West | 160 | 23,541 (8,423 / 1,749) | 18,696 / 69.8 | 119.9 (10,208–20,470) | +100.8 |
| 2025 | East | 153 | 36,922 (12,272 / 8,570) | 16,768 / 52.8 | 181.9 (13,567–37,224) | +71.6 |

- Every year is in `census.csv`.
- **West is the long, cheap side:** 40 % of load, but about 54 % of wind and 40 % of coal.
- **East holds about 60 % of load and nearly all the gas.** Net position = available energy − demand, before dispatch; it is
  reported, not gated.
- The wind shapes were rebuilt under SPP-48's whole-fleet level rule (`build_spp_wind_shape.py --zone-partition west_east`,
  suffixed files; the keeper's own parquets are untouched). GenMix hourly r is 0.84–0.88, the same as the N/S build.
- Whole-fleet CF: West 0.335 vs East 0.302 (2025).

## 4. Why C-3 stops it (`spp93/c3_hours.csv`, `presolve_legs.json`)

**The test (PRECOMMIT §4.1):** margin_z = available thermal + hydro + wind + solar + the link as import − demand_z, on the
keeper's own inputs. There is no storage and no seam interchange, and SPP-54's convention is identical.

| year | local | bubble | W/E margin MW | East demand | East thermal avail. | wind | N/S min margin (zone) |
|---|---|---|---:|---:|---:|---:|---:|
| 2019 | 09-03 14–16 h | East | −647 / −798 / −477 | ~30,400 | 24,963 | 612–967 | +230 to +692 (South) |
| 2023 | 02-17 07 h | East | −149 | 23,705 | 18,292 | 1,264 | +818 (South) |
| 2023 | 08-25 13–15 h | East | −68 / −177 / −275 | ~35,300 | 30,130 | 861–1,036 | +4,561 to +4,865 (South) |
| 2024 | 06-22 15–16 h | East | −46 / −58 | ~31,800 | 26,084 | 1,196–1,648 | +2,707 / +2,870 (South) |
| 2024 | 10-03 14–17 h | East | −246 / −637 / −645 / −170 | ~25,000 | 20,011 | 256–457 | +1,054 to +1,317 (South) |
| 2025 | 07-30 14 h | East | −46 | 35,016 | 29,881 | 840 | +1,076 (South) |

**What it says, structurally:**
- Every new-negative hour is **East**, on a hot or low-wind afternoon with outage-derated thermal. The keeper's 3,400 MW
  N→S link fed a South holding ~40 % of load.
- Under West/East, the 4,000 MW W→E link has to feed an East holding ~60 % of load and the gas fleet.
- The West's surplus is exactly the energy this partition traps (+97 to +109 TWh net position).
- So C-3 is the **link rating** biting on the side that now carries most of the load. It is not a data defect: C-0 and C-1
  prove the inputs are the keeper's own, only relabelled.
- It also improves the Dec-21-2025 window SPP-54 stopped on: min margin W/E +1,251 vs N/S −796 MW.

**What the arithmetic leaves out, stated and NOT used to re-grade it:**
- East storage (~444 MW of batteries at HEAD);
- scheduled seam imports (MISO/AECI);
- any LP re-dispatch.

Those could close some or all of the 46–798 MW gaps, but that is a post-hoc argument. The gate was declared without them,
and the owner's direction for this lane is "do not re-cut after the result".

## 5. What landed, and the proofs

- **The mechanism, GATED:**
  - `ScenarioConfig.spp_zone_partition`, default `"north_south"` = the keeper, byte-identical;
  - `topology_variant.set_spp_zone_partition` at all three config seams;
  - `_spp_config`'s W/E branch;
  - the plant map and zone-assignment carve;
  - the sub-BA grouping, the suffixed wind shapes and the allocation fallback;
  - the cache-key drop at its frozen default, and TIER 1;
  - a matrix row plus a cell in all nine shards (rule 28(c)).
- **Proofs:**
  - `solve_surface_register --diff origin/main HEAD`: **317 → 317, 0 moved**;
  - 8/8 new tests (`tests/iso/spp/test_spp_west_east_partition.py`);
  - 265 related SPP / zone / zonal-share / cache-key / facade tests green;
  - the six fast-tier failures in `tests/unit/config` + `test_persisted_identity` **reproduce identically on `main`**, so they
    are not this change;
  - `check_mechanism_matrix --base origin/main` clean.
- **G-DRIFT** `d72e5f10` → `325674da` (47 files): **ALL INERT for SPP** (`spp93/gdrift_d72e5f10_to_325674da.md`). If a lane
  solves it, the keeper bundle remains a valid form-4 control.
- The shard self-check `_spp93_shard_check.py` is ready: recipe = keeper + exactly the one field, the extract and plant-map
  sha256 are pinned, and the topology is checked.
- **DOF:** zero tuned scalars. The partition is a registry rule, 1-NN has no parameter, and the TTC is a measured
  construction. The 0.93 multipliers are untouched.

## 6. Status and routing

- **Cell `spp_zone_partition` = O** (open). The design is built and measured-admissible, and blocked at its own pre-solve
  leg. It is not refuted by an LP: no LP ran.
- `internal_congestion_split` stays U, and `measured_interface_limits` stays O; evidence is appended to both.
- **Owner card (decision cards, not decided here):**
  - (a) hold the STOP and route;
  - (b) authorize a solve despite C-3, graded post-solve by L3 (unserved ⊆ keeper's).
- `complete` / `frontier`: unchanged. The train tier 2023–25 is CALIBRATED (lone ledgered C3c); the validation tier 2019–22
  is NOT-YET (reported, not gating, rule 30(c)). **`frontier` is NOT reached.**

## 7. Owner ruling (decision card, 2026-09-27)

**"Hold STOP, next lever (Recommended)."**
- The C-3 STOP stands.
- `spp_zone_partition` stays built and default-off, and its cell stays **O**.
- SPP-94 moves to the next SPP rubric failure.
- A West/East solve is NOT authorized; a later lane re-opens it only with a new ruling.
