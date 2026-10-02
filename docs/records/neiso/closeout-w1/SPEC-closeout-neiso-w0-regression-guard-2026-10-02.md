# SPEC — NEISO regression guard for the W0 EIA-860 settlement (closeout plan §3.2 step 4)

Author: lane `closeout-neiso-wave1`, 2026-10-02. **Runner: the W0 lane** (session_018DsgkLcN1h8NQc2yJegmdN,
branch `claude/closeout-b-w0-foundation`). NEISO is CALIBRATED on `2026-09-26-neiso-119-anchor-fuelsec`;
this guard is how W0 proves it did not move NEISO by accident. Zero LP for §2; §3 reads the W0 re-solve.

## 1. What W0 can move in NEISO (research shard §3, re-checked against the keeper `run_config.json`)

| armed path | reads | guarded by |
|---|---|---|
| `eia860_vintage_tracks_solve_year` | `vintage_<Y>`; 2025 now reads `vintage_2025` (Final) | §2 class census, 2025 |
| `mid_vintage_exit_carry` / `partial_plant_exit_carry` | retired-within-window parquet (extended by 34 pre-2023 units on 2026-10-02) | §2 watch: **Pilgrim 1590** (736 MW injected 2019, nuclear 2.18 TWh), **Mystic 1588** (7 retired 2021-06 as a zero-availability row in 2022; 8&9 carried to 2024-05-31, 1,493 MW injected 2024) |
| `cc_nameplate_summer_derate` | EIA-860 nameplate vs net summer per CC plant | §2 class capacity CC_REGULAR / CC_CHP; 2019 CC_REGULAR C1 sits at −1.8 pp of a ±3 pp band |
| CC_CHP basis | EIA-860 213/206 MW at **Kendall 1595** (CAMPD gross 278–323 MW is a metering artifact, `FINDING-neiso73`) | §2 watch 1595 |
| measured heat-rate artifacts | CAMPD unit ↔ EIA-860 generator joins | §2 watch **Canal 1599** (class-preserving `union_fleet`, neiso-118: Canal 3 files OA/DFO 2023–25 but burns gas) |
| seasonal capacity basis (W0 Q1, flat class derate deleted) | published summer/winter pair | §2 class capacity + reported available-energy move |

## 2. Zero-LP census (run before any NEISO re-key)

Scripts (committed in this record directory):

```bash
# control: the W0 base SHA (the commit W0 branched from); arm: the W0 head
git -C <control-worktree> checkout <W0_BASE_SHA>
python docs/records/neiso/closeout-w1/w0_guard_census.py --year 2019 --out /tmp/neiso_w0_control_2019.json
python docs/records/neiso/closeout-w1/w0_guard_census.py --year 2025 --out /tmp/neiso_w0_control_2025.json
git checkout <W0_HEAD_SHA>
python docs/records/neiso/closeout-w1/w0_guard_census.py --year 2019 --out /tmp/neiso_w0_arm_2019.json
python docs/records/neiso/closeout-w1/w0_guard_census.py --year 2025 --out /tmp/neiso_w0_arm_2025.json
python docs/records/neiso/closeout-w1/w0_guard_compare.py /tmp/neiso_w0_control_2019.json /tmp/neiso_w0_arm_2019.json
python docs/records/neiso/closeout-w1/w0_guard_compare.py /tmp/neiso_w0_control_2025.json /tmp/neiso_w0_arm_2025.json
```

The census rebuilds the keeper recipe (`replay_keeper.run_year_kwargs` + `derived_run_year_inputs` on
`results/calibration/neiso119_span`, `fleet_only=True`, the neiso-119 `lp_input_diff.py` pattern). Both runs need
`scripts/regenerate_clean.py --solve-profile NEISO` at their own checkout.

**Tripwires (any one fails the guard):**

| # | wire | rule |
|---|---|---|
| T1 | every LP unit of plants 1590 / 1588 / 1595 / 1599 is **byte-stable**: same unit ids, plant_group, fuel, pmax, heat rate, monthly mean availability, mean mc_base | the four known reconciliations must survive a settlement that re-maps units |
| T2 | no plant_group\|fuel class appears or disappears | class integrity (Canal 3 must not flip to oil) |
| T3 | class capacity moves ≤ 1 % | W0 census tolerance (R-2 / D-P2) |
| T4 | total capacity moves ≤ 0.5 % | W0 census tolerance |

Reported, not tripped: per-class available energy and mean mc_base moves (`MOVE` lines) and the list of LP-input
arrays whose sha256 moved. A move here is expected if W0 changes the capacity basis on purpose; it is what §3
then has to absorb.

**Known 2019 defect a W0 join may legitimately correct (T1 direction declared ex ante).** The baseline census on
main `4d459da3` (`w0_guard_baseline_2019_main-4d459da3.json`; all oil units in `oil_heat_rate_census.json`) carries
**1,711.6 MW of 2019 oil at heat rates < 9 MMBtu/MWh**: Canal 1/2 (`1599_1` 560 MW, `1599_2` 553 MW) at **4.141**
and Mystic 7 (`1588_7`, 541.8 MW) at **7.599** (Mystic's CC plant rate), so 1.1 GW of oil steam offers at
mc ≈ $85/MWh against a 2019 oil-class mean of $251. In 2022 and 2025 the same plants carry normal rates
(cap-weighted oil 13.9). Oil boilers run ≈ 10–12. A W0 vintage/heat-rate join that moves **only these rows toward
the physical range** is a rule-14 correction: T1 trips on them are expected and are reported, not escalated. Any
other T1 move escalates.

**If T1 or T2 trips:** W0 stops before any NEISO re-key and reports the unit diff to the desk; the fix lands
in W0, not in a NEISO knob (rule 19/24). **If only T3/T4 trip:** W0 states the moved classes and their
EIA-860 cause (one line per class) and proceeds to §3. A class move with no EIA-860 cause is a W0 bug.

## 3. Post-solve tripwire (the W0 NEISO re-solve, 7 legs)

| wire | threshold | source |
|---|---|---|
| **C3a move** | \|C3a(arm) − C3a(keeper)\| > **2 pp** in **2019 or 2025** | 2019 sits at +7.9 %, 2025 at +6.6 % against the ±10 % line; 2 pp is the charter's margin |
| determination | any criterion PASS → FAIL in any year | keeper status part `frontend/data/backcast/status/NEISO.js` |
| C1 CC_REGULAR 2019 | leaves the band | −1.8 pp today; neiso-118 moved it from −3.46 FAIL |

A C3a tripwire is not a veto on W0 (W0 is a structural correction; rule 1 promotes the faithful run). It obliges
W0 to decompose the move (capacity basis vs exit carry vs heat-rate join) in its RESULT before NEISO's keeper is
re-keyed, and hands NEISO's lane the residual.

## 4. Hand-off

The W0 lane runs §2 before its NEISO re-key and §3 on its NEISO re-solve, and reports the four compare outputs
and the §3 table in its RESULT. Nothing here changes a ScenarioConfig field or a registry value.
