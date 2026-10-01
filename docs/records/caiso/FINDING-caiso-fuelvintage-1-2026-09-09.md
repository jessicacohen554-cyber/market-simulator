# FINDING — caiso-fuelvintage-1: two phase-0 STOPs, zero LP spent

**Session** `caiso-fuelvintage-1` · **2026-09-09** · branch `claude/caiso-fuelvintage-1`
· base `b9fcb160` (tree-identical to `origin/main` `87ad084b`) · **SCOPE: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`)

**Result in one line.** Both arms this session was chartered to solve were killed by
computable pre-solve gates under rule 29 `[R-SCREEN]` clause (0), so **no LP was spent**:
the fuel seam is **provably inert** for CAISO (not near-inert), and the widened retiree
window **fails charter task 3** in 2023 — it injects **480.000 MW / 3,367,624.32 MWh** of
capacity from a unit that retired in **October 2019** into a **training** year. The second
is a located, cross-ISO defect worth **31 rows / 4,779.2 MW** across six ISOs.

**Keeper unchanged.** `2026-09-06-caiso-260-b1-demand` (bundle `caiso260_demand_vintage`),
determination **CALIBRATED**, is untouched. Nothing was promoted, registered or pruned.

---

## 0. Corrections to the handoff, established before any work

Three of the launch prompt's premises are wrong at HEAD. Each is stated here because a
later session would otherwise repeat the error.

1. **ADDITION 5's red gates are already clear.** `build_status.py --check --iso CAISO`
   reads *"status parts in sync (1 keepers: CAISO)"* and `audit_keepers.py --iso CAISO`
   reads **PASS, 0 failures / 0 warnings** (CAISO keeper, holdout, marker, status all ✓).
   caiso-267's status rebuild (`1152d593`) fixed it. **Nothing to clear; nothing written.**
2. **ADDITION 4's "CAISO's FIRST validation touchpoints" is wrong — 2022 is already SPENT,
   three times.** `caiso-262` (`150bfcef`, registered `2026-09-07-caiso-262-2022-touchpoint`,
   stamped `holdout.keeper = 2026-09-06-caiso-260-b1-demand`), `caiso-265` (`9f6b8864`, the
   2022 rung re-solved on a repaired price basis) and `caiso-267` (`9b8a9621`, the x0.92
   arm's 2022 re-test, bundle `caiso267_fossil92_2022`). **2020 and 2021 have never been
   solved.** CAISO holds `complete` (declared 2026-09-06, keeper re-keyed); `final` is
   **absent** and the locked-test freeze is ACTIVE, so 2019 stays refused.
3. **ADDITION 0's partial-plant-exit overlap concern is moot for this lane.** The keeper's
   `run_config.scenario_config` carries `partial_plant_exit_carry = False`, so
   `_partial_plant_exit_rows` never runs in any CAISO replay. Verified rather than trusted.

---

## 1. G-CTRL / G-DRIFT posture

Rule 29 (b): **no control solves.** The committed keeper bundle is the control (form 4),
and this session went further — instead of arguing hunk-inertness from a diff, it
**rebuilt the LP's own inputs** on the keeper's recipe and differenced them
(`fleet_only`, `replay_keeper.run_year_kwargs` + `derived_run_year_inputs`). That is
strictly stronger than a control solve for the questions asked: it says which array
could have moved, not merely that two numbers differ.

**A trap that invalidated the first pass, recorded so it is not repeated.**
`cod_ramp._load_cod_map` is an `@lru_cache` keyed on the **eia860 directory**, not on the
artifact's contents. Swapping a data parquet under a live interpreter therefore leaves a
**stale COD map**, and a control arm silently inherits the arm's retirement dates. The
first A/B run this way reported "48 retired unit rows are fully dispatchable, 6.6 TWh" —
**that reading was an artifact of the probe, not of the model.** Every number below comes
from arms run in **separate processes**. Measured cleanly, those 48 rows are fully masked:
availability `0.0` in all 8,760 hours, deliverable **0.0 MWh**.

---

## 2. CARD 1 — the fuel seam is PROVABLY INERT for CAISO. Arm killed, no LP.

`gas_electric_power_monthly_level`. Pre-registration (FINDING-xiso-fuelvintage §5b) said
*near*-inert by ordering, C3b unchanged to three decimals. The measurement is **exactly
inert**, on two independent legs. Probe: `scripts/probes/_caiso_fuelvintage_ep_identity.py`;
artifacts `results/calibration/_caiso_fuelvintage_ep_identity{,_2425}.json`.

### 2a. Coverage — 2019/2020/2021 refused by the admission test

`iso_electric_power_monthly_level('CAISO', y)`:

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| verdict | `None` | `None` | `None` | ADMIT | ADMIT | ADMIT | ADMIT |
| annual $/MMBtu | — | — | — | 9.4862 | 7.0329 | 3.6064 | 4.2752 |

California prints only 11 of 12 N3045 months in each of 2019-2021, so the year is refused
and the caller is byte-identical **by construction**. The four admitted annual means
reconcile the phase-0 table (9.526 / 7.038 / 3.608 / 4.273) to ≤ 0.040.

### 2b. Ordering — the admitted years cannot reach the LP either

Two `fleet_only` rebuilds per year on the keeper's own recipe, seam off vs on:

| year | n gas units | max abs Δ `fuel_prices` | max abs Δ `mc_base` | unit rows moved | gas-cell share moved |
|---|---|---|---|---|---|
| 2022 | 1,491 / 1,712 | **0.000000** | **0.000000** | 0 | 0.000000 |
| 2023 | 1,491 / 1,710 | **0.000000** | **0.000000** | 0 | 0.000000 |
| 2024 | 1,496 / 1,704 | **0.000000** | **0.000000** | 0 | 0.000000 |
| 2025 | 1,501 / 1,709 | **0.000000** | **0.000000** | 0 | 0.000000 |

Cause, from the solve log: `gas_hub_basis_overlay` reprices **1,491 / 1,496 / 1,501 gas
generators at the measured hub spot in 12/12 months** of 2022 / 2024 / 2025. A measured
constrained-hub index is the marginal unit's own opportunity cost and supersedes a state
average outright (rule 19 `[R-ONE-MECH]`, the declared level ordering).

**Dec-2022, the one month that mattered, is inert.** The pre-registered western-gas-crisis
gap (+16.058 $/MMBtu, ~120 $/MWh) is CAISO's single materially reachable ISO-month. It is
superseded exactly where it would have bitten hardest — the sharpest possible statement of
the ordering, and the reason no 2022 solve was spent chasing it.

### 2c. The one place the seam DOES write — and why it still reaches nothing

The ISO-level `_gas_series` (which keys **only** the coal passthrough sigmoid) **does move
in 2025**, by up to **0.535 $/MMBtu**, confined to **Sep / Oct / Nov**:

| month | Sep | Oct | Nov | all others |
|---|---|---|---|---|
| Δ $/MMBtu | −0.1740 | **−0.5346** | −0.3647 | 0.0000 |

**This falsifies the prompt's premise that the hub overlay covers 12/12 months of every
year.** It covers 12/12 at the **plant** layer (`apply_hub_basis_overlay`) and only **9/12**
at the **ISO** layer (`_hub_overlay_series`) in 2025 — independently corroborated by the
`gas_hub_basis_overlay` matrix cell (caiso-242, same three months). The LP reads the plant
layer, and CAISO carries no coal, so the divergence reaches nothing — confirmed empirically
by `mc_base` being bit-identical in 2025 regardless.

**Verdict — matrix cell `O` → `I` (inert).** Not refuted: **unreachable behind a strictly
better measured series.** DO-NOT-REDO for CAISO without new evidence. A CAISO arm becomes
meaningful only if the hub overlay is disarmed or its plant-layer coverage falls below 12/12.

---

## 3. CARD 3 — charter task 3 FAILS in 2023. This is the session's real finding.

Commit `7934e92c` widened `RETIREMENT_WINDOW_START` 2023 → 2019, changing exactly one
artifact (`eia860_generator_retired_within_window.parquet`, 20,185 → 35,250 B) plus its
builder; consuming code is unchanged. So the whole question is an A/B on that file.
Probes: `_caiso_retiree_window_inertness.py`, `_caiso_retiree_2023_localize.py`.

**Artifact-level, verified:** 477 → 1,094 rows, **0 removed** (additive), and **nothing
added at retirement year ≥ 2023**. CAISO gains **86 units / 1,700.6 MW summer**
(nameplate: CC 840.0, gas ST 495.0, solar-thermal 172.6, wind 166.4), matching the prompt.
All 11 shipped invariants in `tests/unit/data/test_retiree_window_extension.py` **pass**.

**Fleet-level, process-isolated, on the keeper's recipe** — the pre-registration was
*"EXACTLY ZERO change"* in 2023-2025:

| solve year | units ctl → arm | Δ `pmax` | **Δ deliverable MWh** | verdict |
|---|---|---|---|---|
| 2023 | 1,662 → 1,710 (+48) | +1,246.083 MW | **+3,367,624.320** | ***FAIL*** |
| 2024 | 1,656 → 1,704 (+48) | +1,246.083 MW | **+0.000000** | pass |
| 2025 | 1,661 → 1,709 (+48) | +1,246.083 MW | **+0.000000** | pass |

The 48 added rows are **not** the problem — they are fully COD-masked in every year and
deliver **0.000 MWh**. The 2023 move is in **8 rows that exist in both arms**, and it is
one plant:

```
ST_GAS_LA_BASIN_p356_committed   249.000 -> 393.000 MW   1,746,955 -> 2,757,242 MWh
ST_GAS_LA_BASIN_p356_peak        124.500 -> 196.500 MW     873,478 -> 1,378,621 MWh
ST_GAS_LA_BASIN_p356_econc00..05  76.083 -> 120.083 MW ea. 533,792 ->   842,491 MWh ea.
                                  mean availability 0.8009 -> 0.8009 (unchanged)
```

### 3a. Root cause — intra-plant vintage collapse in the plant-keyed COD map

**AES Redondo Beach (plant 356), generator 7** — 495 MW nameplate / **480.0 MW summer**,
gas steam turbine, **retired October 2019**. The widened window adds it. But plant 356's
other three units retire **December 2023**:

| generator | summer MW | retirement |
|---|---|---|
| 5 | 175.0 | 2023-12 |
| 6 | 175.0 | 2023-12 |
| 8 | 480.0 | 2023-12 |
| **7** | **480.0** | **2019-10** |

`cod_ramp._load_cod_map` is **plant-keyed** and records a retirement only when *every* unit
carries one, taking the **latest**: plant 356 resolves to `(1964, 7, 2023, 12)`. Generator
7's 480 MW is therefore binned into the surviving plant's tranches and carried at the
plant's full 0.8009 availability **through all of 2023** — a unit that stopped generating
in October 2019.

**This is not a builder bug and the shipped guard is not broken.** Plant 356 is genuinely
absent from the operable snapshot (verified), so `test_no_plant_overlaps_the_operable_snapshot`
correctly passes: it *is* a whole-plant exit. What the widening changed is the
**consequence** of a documented approximation — *"a scalar per-plant COD necessarily
approximates a genuinely mixed-vintage plant"* — by pulling a 2019 unit into a plant whose
collapsed date is 2023. Before `7934e92c`, generator 7 was outside the window and plant 356
carried 830 MW; after it, 1,310 MW.

Note `cod_ramp.effective_cod` **already prefers a generator's own per-unit retirement** (the
documented "Homer City seam"). It cannot fire here because the injected generators carry
`retirement_year = None` (verified on the rebuilt fleet), and because plant-level binning
merges generator 7's capacity into tranches shared with generator 8 — so a per-unit date
cannot survive the bin regardless.

### 3b. Cross-ISO census — 31 rows / 4,779.2 MW, six ISOs

Rows whose own retirement precedes their plant's latest, i.e. whose exit the plant-keyed
map discards:

| ISO | rows | summer MW | largest |
|---|---|---|---|
| PJM | 10 | **3,055.2** | Homer City 2 & 3 (648.9 + 613.3, own 2023 vs plant 2024); Conesville 5 & 6 (375.0 ea., own 2019 vs plant 2020) |
| ISNE | 4 | 614.2 | Mystic 7 (512.4, own 2021 vs plant 2024) |
| MISO | 11 | 495.8 | River Rouge 3 (272.0, own 2021 vs plant 2024) |
| **CISO** | **2** | **481.8** | **AES Redondo Beach 7 (480.0, own 2019 vs plant 2023)** |
| NYIS | 3 | 88.5 | — |
| SWPP | 1 | 43.7 | — |

**This is shared fleet infrastructure and it is deliberately NOT fixed here** (rule 25
`[R-ISO-SCOPE]`; the prompt's *"SCOPE: CAISO ONLY"*). A repair changes the artifact for every
ISO and re-keys every ISO's fleets — an owner / parent-lane decision, not a CAISO lane's.

**Candidate repairs, none armed, no threshold selected (rule 5 `[R-NO-MAGIC]`):**
(a) exclude from the whole-plant injection any retiree row whose own retirement precedes the
plant's latest — the surviving units already carry that plant's capacity, so this adds no
parameter; (b) carry the row's own `planned_retirement_*` onto the injected `Generator` and
split the bin so `effective_cod`'s existing per-unit preference can fire — correct but
touches binning; (c) bin retiree rows by (plant, retirement vintage) rather than plant.
**(a) is the session's recommendation** — smallest surface, zero free parameters.

---

## 4. Why no solve was spent, and what that costs

Rule 29 `[R-SCREEN]` clause (0): *an arm with a computable pre-solve gate does not reach a
solve until that gate passes.* Both gates were computable and both were decisive:

- **SHARD F** (2023 fuel ordering) would have cost one LP to confirm `max |Δ| = 0` on inputs
  already proven bit-identical. Pure waste.
- **SHARDS H1 / H2 / T1 / T2** (2020, 2021, 2022, 2023, 2024, 2025) would all have solved a
  fleet carrying the phantom 480 MW. It contaminates **2023 directly** (+3.37 TWh in the
  tuned window) and **2020-2022 too**, where generator 7 is likewise carried online against
  an October-2019 exit. A 2023-2025 bundle solved this way could not be a keeper — it would
  differ from `caiso260_demand_vintage` for a reason that is a **defect, not a mechanism** —
  and touchpoint rungs built on it would not be diagnosing CAISO, they would be measuring
  this seam.

The prompt's own instruction is the governing one: *"A nonzero delta means capacity-denominated
code is reading retired units — root-cause it, do not wave it through."* It has been
root-caused to a named unit, a named seam and a sized cross-ISO census. Spending ~2-4 hours
of LP across five shards before that seam is decided would have been waving it through.

**What is therefore still owed** once the seam is resolved: CAISO's 2020 and 2021 rungs
(never spent), a 2022 re-spend on the corrected fleet, and the 2023-2025 re-verification
that charter task 3 asks for.

---

## 5. Gate baselines on this tree (ADDITION 7) — all pre-existing, none added

| gate | result | vs ADDITION 7 |
|---|---|---|
| `pytest tests/scoring` | **16 failed / 1,532 passed / 12 skipped** | matches the stated 16 exactly |
| `check_cache_key_registration --base origin/main` | RED, `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` | matches; pre-existing |
| `check_mechanism_matrix --base origin/main` | **exit 0** (pre-existing anchor warnings only) | green |
| `build_status.py --check --iso CAISO` | **in sync** | already fixed by caiso-267 |
| `audit_keepers.py --iso CAISO` | **PASS, 0 / 0** | already fixed by caiso-267 |
| `tests/unit/data/test_retiree_window_extension.py` | **11 passed** | — |

## 6. Artifacts

Committed: this document; the matrix cell `O` → `I` in
`docs/codebase-site/data/mechanism-matrix/CAISO.js`; the three probes under
`scripts/probes/`. The probe JSONs under `results/calibration/_caiso_*` are gitignored
working artifacts (rule 31 `[R-RETAIN]`) — **every number this session cites is in this
document**, per rule 29 (c).

**No bundle was produced, so there is nothing to promote and nothing to prune.** The
designated keeper stands.
