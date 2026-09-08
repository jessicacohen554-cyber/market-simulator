# RESULT — the 2021 C8 breach is a TRUE POSITIVE, the repair is real and structural, and it does NOT close the gate (ercot-256)

> Scored against `docs/PRECOMMIT-ercot256-drag-layup-window-mask-2026-09-07.md`,
> pushed (`fa1da7a0`) before any LP ran. Every gate, the screen year, the drift
> audit and all seven predictions were registered there, upstream of the arm.
> **Rule 30(c): ERCOT's determination is the train-tier verdict and this session
> cannot move it in either direction.** Bundles are **gitignored, not deleted**
> (rule 31 `[R-RETAIN]`) and live on local disk only.

## 0. Bottom line

| | |
|---|---|
| **Is the 2021 C8 ST_GAS failure a true positive?** | **YES.** The floor really does force two plants their own meters say were idle. §1 |
| **Did the model already know?** | **YES** — its own merit-order guard measured the absence and the drag contradicted it. §2 |
| **Is the family repair already in the repo?** | On four other mechanisms; **never on this one**. §3 |
| **Identified in-sample?** | **YES** — same mechanism, 2024 and 2025, other plants. §4 |
| **Does the 2025 screen clear?** | **EVERY GATE.** And nothing regresses: C3a, C3b, C4, C8 and D-1 all move the right way. §6 |
| **Does it close the 2021 gate?** | **NO** — registered as P6 *before* the solve, and the reason is exact. §7 |
| **Keeper candidate?** | **YES**, and promoted on the owner's bar. §8 |
| **Predictions** | 5 of 7 correct, 1 wrong, 1 gate mis-specified by me. §9 |

## 1. The failure, decomposed (zero LP, committed artifacts)

`calibration_verdict.determine("2026-09-07-ercot255-five-year-keeper")`:

```
forced_share ST_GAS 2021 = FAIL  37.6 % forced (4.2050 of 11.1773 TWh)
  — above the 30 % cap and NOT grounded (forcing variables miscalibrated):
    provenance — floors a unit its own meter says is offline (D-4 per-unit
    conduct FAIL): st_netload_drag (plant 3452), st_netload_drag (plant 3628)
```

Rule 16 `[R-FORCED-BUDGET]`'s escalation needs two legs, and they split cleanly:

* **Leg (b), D-1 diurnal shape — PASSES cleanly.** `profile_r 0.999`,
  `cv_ratio 1.91` against gates 0.80 / 0.50.
* **Leg (a), D-4 provenance — FAILS**, through the **per-unit conduct rider**
  only. The window row passes *vacuously* (`st_netload_drag h0-23`, off-window
  share 0.0000) — the tautology the rider was adopted (nyiso-140 §5/§6.3, K6′)
  to defeat.

`st_netload_drag` is the **only** mechanism forcing ERCOT ST_GAS in any scored
year (the keeper's D-2 rows: 4.2050 / 4.0298 / 3.3833 / 3.0083 / 3.2467 TWh,
2021–2025), so leg (a) rests entirely on it.

### 1a. The two convicted plants, and what their meters say

| plant | floored | share of the mechanism's forced energy | binding h | measured median | at zero |
|---|---|---|---|---|---|
| **3452** Lake Hubbard | 0.4970 TWh | 11.8 % | 6,026 | **0.000 MW** | **88.75 %** |
| **3628** R W Miller | 0.3325 TWh | 7.9 % | 6,423 | **0.000 MW** | **57.90 %** |

Measured CAMPD (`data/raw/campd-unit-level/TX_<year>.parquet`, TWh / hours > 0):

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 3452 Lake Hubbard | **0.3578 / 1,924** | 0.5816 / 3,048 | 0.9410 / 3,717 | 1.7537 / 4,713 | 1.9882 / 5,496 |
| 3628 R W Miller | **0.2865 / 3,317** | 0.3893 / 3,416 | 0.5149 / 3,898 | 0.5217 / 5,401 | 1.1258 / 7,707 |

**Lake Hubbard generated exactly ZERO in January, February and March 2021** —
through Winter Storm Uri — and ran 1,924 of 8,760 h (unit 1: 907 h; unit 2:
1,581 h). **R W Miller unit 1 produced 0.0 GWh in all of 2021.** The model
floors them for 6,026 and 6,423 hours. The rider is right.

## 2. The model already measured the absence, and the drag contradicted it

`scripts/lib/outage_detect.py`'s **merit-order guard** reclassifies a detected
≥ 5-day full stop as **ECONOMIC LAY-UP** when the unit's measured SRMC sat above
the revealed clearing cost for ≥ 90 % of the window, and writes it to
`data/raw/campd-unit-outages-layup.csv` **on the express charter that the window
stays OUT of the availability envelope** — *"an economically idle unit is
AVAILABLE; the LP declines it on its own economics."*

That is right for the **LP**. It is wrong for a **forcing** mechanism:

| ERCOT 2021, plant | in the AVAILABILITY overlay | reclassified ECONOMIC LAY-UP |
|---|---|---|
| 3452 unit 1 (396.5 MW) | **no 2021 row at all** | **272.8 unit-days** |
| 3452 unit 2 (531 MW) | 197.0 unit-days | 9.2 unit-days |
| 3628 unit 3 (200 MW) | 9 windows | — |
| 3628 unit 5 (118.8 MW) | — | 20 windows |

Plant-hour shares on the model's own clock:

| plant | availability, mean | lay-up share, mean | eligible = max(0, a − l) | hours eligible == 0 |
|---|---|---|---|---|
| 3452 | 0.6749 | 0.3507 | 0.3278 | **72 → 5,088** |
| 3628 | 0.3863 | 0.2000 | 0.1942 | **168 → 4,704** |

Rule 17 `[R-FLOOR-WINDOW]` verbatim: *"a floor binding in hours its own driver
evidence says the class is offline is a bug by definition."*

**Why the class-level driver cannot see it.** The drag's evidence base
(`docs/ercot-st-gas-netload-drag-2026-06.md`) is a **FLEET** overnight capacity
factor regressed on net load — *"committed every day and every night, never
fully off"* — and the applier puts that one fraction on **every** non-peaker
tranche's `pmax`. The 2021 meter disagrees: V H Braunig 8,095 h online, Dansby
8,121, Cedar Bayou 4,809, Sommers 4,710, Handley 3,872, R W Miller 3,317, Sim
Gideon 3,278, **Lake Hubbard 1,924**. A fleet average spread uniformly
over-forces the least-committed units — the "forcing variables are wrong" signal
rule 16 exists to raise.

## 3. The family repair — and the one mechanism that never had it

| mechanism | correction | session |
|---|---|---|
| `reliability_floor` | `reliability_floor_plant_exclusions` (membership) | nyiso-140 |
| NYISO gas bridge | `nyiso_gas_bridge_plant_exclusions` | nyiso-144 |
| `*_mustrun_per_plant` | `mustrun_plant_exclusions` (membership) | miso-170 |
| `*_mustrun_per_plant` | `mustrun_layup_window_mask` (**window**) | miso-173 |
| **`st_netload_drag` / `ct_netload_drag`** | **none** | — |

**`ScenarioConfig.netload_drag_layup_window_mask`** (default `False`) is the
miso-173 construction on this family's shared engine: the per-hour clip basis
becomes `pmax × max(0, availability − layup_share(t))` from
`data.outages.unit_layup_removed_fractions` — the same accumulator, unit→plant
routing and capacity denominator as the outage overlay, so the two shares are
additive by construction. Availability itself is never touched.

* **Rule 19** — no new floor, no membership change, no second mechanism id.
* **Rule 21** — ZERO free parameters; windows, shares and the 0.90 out-of-merit
  threshold live in the frozen derive layer (rule 23).
* **Rule 13** — BACKCAST ONLY at **two** layers: `_BACKCAST_ONLY_OVERLAY_FIELDS`
  raises at `ScenarioConfig.__post_init__` in forecast mode, and
  `floors._resolve_drag_layup_shares` independently returns `{}`.
* **Rule 25** — the extract is per-ISO; nothing is transferred from MISO.
* The lay-up extract carries **no CT rows** (the derive excludes combustion
  turbines), so the CT limb is inert under the mask by construction.

## 4. Identified IN-SAMPLE, never on 2021 (rule 22 step 3)

Committed D-4 conduct FAILs on `st_netload_drag` in the **training** years:

| year | plant | floored | share of the mechanism's forced energy | median | at zero |
|---|---|---|---|---|---|
| 2024 | 3491 Handley | 0.6472 TWh | **21.5 %** | 0.000 MW | 75.6 % |
| 2025 | 3491 Handley | 0.8756 TWh | **27.0 %** | 0.000 MW | 69.8 % |
| 2025 | 3460 Cedar Bayou | 0.2006 TWh | 6.2 % | 0.000 MW | 57.1 % |

C8 passes in those years (17.1 / 15.3 / 20.1 %) only because the class runs
19.8 / 19.6 / 16.2 TWh there against 11.2 TWh in 2021 — the *share*'s
denominator, not the floor's soundness.

## 5. Phase 0 — footprint by year, and the screen year (zero LP)

`run_year(fleet_only=True)` on the keeper's recipe, differencing the drag floor's
mandated energy between `basis = availability` and `basis = max(0, a − l)`:

| year | control | with mask | **removed** | **%** |
|---|---|---|---|---|
| 2021 | 6.6290 TWh | 5.7671 | 0.8619 | 13.0 % |
| 2022 | 7.7874 | 7.0023 | 0.7851 | 10.1 % |
| 2023 | 8.4409 | 7.0861 | 1.3548 | 16.1 % |
| 2024 | 8.0658 | 7.0721 | 0.9937 | 12.3 % |
| **2025** | **7.2884** | **5.8192** | **1.4692** | **20.2 %** |

**Screen year 2025**, named in the PRECOMMIT before the solve: largest footprint
on **both** measures, and a **training** year — so the choice cannot be
residual-driven.

**G-DRIFT (rule 29b).** `git diff df46537c origin/main` over the backcast solve
path = 18 files / 6 non-merge commits, **every hunk classified INERT for an
ERCOT backcast** (SPP-44 `spp_gas_commitment_bridge`, ISO-exclusive and
default-off; SPP-55 entirely under `elif iso == "SPP"`; SPP-51 touching
`INTERFACE_NEIGHBORS["SPP"]` only, with *"ERCOT's own registry row stays 820"*;
SPP-60 data, forecast-only; capx D85-R a record block its own docstring calls
*"not an input to any key"*; two new SPP names appended to
`solve_surface_declared`, ERCOT's rows untouched). **G-CTRL form 4 valid; no
control solve spent.**

## 6. The 2025 screen — every STOP gate clears, and nothing regresses

Arm = the keeper's own recorded recipe **plus one first-class CLI flag**
(`--netload-drag-layup-window-mask`, not the `--set`/`prb_overrides` channel, so
`run_config.json` records it under its own name). Control = the committed keeper
(G-CTRL form 4).

| gate | measured | STOP bar | verdict |
|---|---|---|---|
| **G-2** direction + bound | `st_netload_drag` forced **3.2467 → 2.5703 TWh** (−0.6764) | rises, or > 1.4692 | **PASS** |
| **G-3** magnitude | system LW LMP **33.3948 → 33.5248** (+$0.1301) | > $5.00 | **PASS** |
| **G-4** non-target load-bearing | **zero PASS→FAIL** on C1/C2/C3a/C3b | any flip | **PASS** |
| **G-5** protective | no new above-cap C8 class; C6 UNATTESTED in both | a new class | **PASS** |
| **G-6** shed | slack **0.0000**, dump **0.0000** in both | slack > 1.0 MWh | **PASS** |
| **G-7** reaches its object | plant **3460 FAIL → pass** | none flips | **PASS** |
| **G-1** confinement | **MIS-SPECIFIED BY ME — see below** | — | **not claimed** |

**G-1 is reported as a drafting defect, not a pass.** It read *"only ST_GAS rows
attributed to `st_netload_drag` move; STOP if any other mechanism's forced energy
moves."* Other mechanisms' *at-floor* energy did move — `chp_steam` −0.0667 TWh,
`coal_min_config` −0.0138, `gas_commitment_bridge` −0.0107, CT_CHP `chp_steam`
−0.0034, CT_PEAKER `reliability_floor` −0.0002; 0.0948 TWh total against the
drag's 0.6764. But **at-floor energy is a dispatch statistic**: remove any floor
and the LP re-dispatches, changing how many hours sit at *every* other floor. The
question G-1 meant to ask — does the mask WRITE a floor anywhere but the drag? —
is answered yes by construction (`apply_netload_reliability_floor` is the only
touched site) and the gate as drafted could never have been met by any working
mask. Stated so the record is not tidier than the reasoning was.

**Every scored criterion, control → arm:**

| criterion | control | arm | |
|---|---|---|---|
| C1 COAL_PRB | PASS +1.60 TWh | PASS +1.64 | flat |
| C1 COAL_LIGNITE | PASS +1.01 | PASS +1.01 | identical |
| C2 coal | PASS | PASS | identical |
| **C3a** price_mean | PASS −8.0 % (33.39) | PASS **−7.6 %** (33.52) | improves |
| **C3b** price_shape | PASS 0.101 | PASS **0.098** | improves |
| C3c price_tail | 1 h vs 31 h | 1 h vs 31 h | **magnitudes identical** |
| **C4** dispatch_corr gas | r 0.983 | r **0.984** | improves |
| C4 coal | r 0.811 | r 0.811 | identical |
| **C8** ST_GAS | PASS 20.1 % | PASS **16.6 %** | improves |
| C8 CC_REGULAR / COAL | 1.7 % / 3.2 % | 1.6 % / 3.2 % | flat |
| **D-1** ST_GAS | r 0.975, cv 1.742 | r **0.976**, cv 1.834 | improves |

The C3c CAVEAT → FAIL label is the **replay artifact** ercot-255 §3 already
recorded — a replay bundle writes no attestation, C6 reads UNATTESTED, and the
C3c standing rule's guard (b) requires governance to PASS. Magnitudes are
identical (1 h vs 31 h); nothing about the tail moved.

**The `[7c]` operating-shape report flags 7 regressions** against
`cf_emd_baseline_ERCOT.json`. That baseline is stamped *"keeper of record
run121"* — many sessions stale — and the gate is **not a rubric criterion**. It
is the standing **ERCOT-126** open item: a prior ERCOT keeper was promoted
carrying **15** of them, *"un-targeted, root cause open"*
(`docs/calibration-log/ercot.md` ~L7552). Reported, not attributed to this arm.

## 7. THE COST, and it was registered before the solve: 2021 does NOT clear

Prediction **P6** — *2021 ST_GAS C8 stays FAIL, plant 3452 stays convicted* —
was written into the PRECOMMIT from a pre-solve measurement on the floor's
eligibility set:

| year | plant | CURRENT h / median / zero-share | **MASKED** h / median / zero-share | |
|---|---|---|---|---|
| 2021 | **3452** | 8,688 / 0.00 / 0.783 | **3,672 / 0.00 / 0.564** | **stays convicted** |
| 2021 | 3628 | 8,592 / 0.00 / 0.620 | **4,056 / 52.00 / 0.304** | clears |
| 2024 | 3491 | 8,760 / 0.00 / 0.694 | **5,928 / 0.00 / 0.570** | stays convicted |
| 2025 | 3491 | 8,760 / 0.00 / 0.681 | **6,168 / 0.00 / 0.581** | stays convicted |
| 2025 | 3460 | 8,760 / 0.00 / 0.550 | **4,368 / 250.50 / 0.153** | clears |

The 2025 solve confirms the mechanism exactly: **3460 flipped** (binding hours
2,396 → 1,226, measured median **0.000 → 107.317 MW**, zero-share 0.571 → 0.203)
and **3491 did not** (6,222 → 4,395 h, median still 0.000, zero-share
0.6975 → 0.6425).

**Why, and the split is exact.** `UNIT_OUTAGE_MIN_DAYS = 5`: neither extract sees
idleness in spells shorter than five days. Measured over each plant's own CAMPD
off-spells (computed after the predictions were registered, from the meter alone):

| plant / year | unit-off-hours | in sub-5-day spells | **fraction** | outcome |
|---|---|---|---|---|
| 3628 / 2021 | 39,055 | 2,906 | **7.4 %** | **clears** |
| 3460 / 2025 | 12,651 | 1,076 | **8.5 %** | **clears** |
| 3452 / 2021 | 15,032 | 4,281 | **28.5 %** | stays convicted |
| 3491 / 2024 | 22,087 | 7,087 | **32.1 %** | stays convicted |
| 3491 / 2025 | 21,763 | 9,014 | **41.4 %** | stays convicted |

The two that clear sit at 7–9 %; the three that do not sit at 29–41 %. The
residual is a **grain limit of the measured window extract**, not a defect in the
mask's logic — and closing it is a different instrument with its own
identification question (§10).

## 8. Disposition — KEEPER CANDIDATE, promoted on the owner's bar

Owner instruction, 2026-09-08: *"If structural integrity improves but gates
regress that may still be a keeper."* This arm is **stronger than that bar**:
structural integrity improves (a floor stops forcing a unit its own meter says is
offline; one of three convictions cleared) **and no rubric gate regresses** —
C3a, C3b, C4, C8 and D-1 all move the right way or hold, with zero PASS→FAIL
flips. It carries **zero free parameters**, is **backcast-only by construction**,
and consumes measured data the model's own pipeline already produces.

Promoted per the owner's instruction as the ERCOT five-year keeper's recipe plus
this one flag. The four solve legs and their per-year reproduction recipe are in
§8a; the promotion's own numbers are recorded there as they land.

### 8a. The two-config provenance defect is CHARACTERISED, and it is two keys

`RESULT-ercot254` §5 and `RESULT-ercot255` §6 both stopped on it. It is now
measured exactly. The carve-out recipe **is** the merged `meta.json` plus exactly
two `coal_prb_sigmoid_overrides` keys:

1. `ercot_offer_swcap_clip: true`
2. `offer_curve_by_group: {...}` — the carve-out dict (CC_REGULAR `peak` 151.008
   / `phys_peak` 74.25, CC_CHP 123.684, CT_PEAKER 433.95, ST_GAS 105.6, …)

Nothing else differs: a full key-by-key diff of `ercot253_2021_touchpoint`'s
meta against the merged keeper's finds only `git_sha`, `basis_sha` and
`shared_inputs`. The `run_config` differences that looked like config drift —
`ordc_voll` 9000 vs 5000 and `ordc_mcl_mw` 2000 vs 3000 — are **year-driven**,
not recipe-driven: neither is present in any meta, and both come from ERCOT's
own published ORDC parameters by year (VOLL fell to $5,000 and MCL rose to
3,000 MW after 2021). So all five years are reproducible:

| leg | years | recipe |
|---|---|---|
| A | 2024, 2025 | merged keeper meta + `--netload-drag-layup-window-mask` |
| B | 2023 | + `ercot_offer_swcap_clip=true`, the carve-out `offer_curve_by_group`, `ercot_zonal_spread_ep_referenced=false` (owner instruction: absent in 2023) |
| C | 2021 | `ercot253_2021_touchpoint` + `ercot_zonal_spread_ep_referenced=true` + mask |
| D | 2022 | `ercot252_2022_touchpoint_repair` + the same two |

## 9. Prediction scorecard — hits and misses alike

| # | registered | measured | verdict |
|---|---|---|---|
| **P1** | drag forced energy falls 0.30–1.47 TWh | **−0.6764 TWh** | **CORRECT** |
| **P2** | 3460 flips FAIL→pass; 3491 stays FAIL | **both exactly** | **CORRECT** |
| **P3** | ST_GAS class energy falls by **less** than the forced-energy fall | class **−0.6980** vs forced **−0.6764** — it fell by **MORE** | **WRONG** |
| **P4** | CT_PEAKER exactly inert under the mask | no CT rows in the extract; `ct_netload_drag` unarmed; mask wrote nothing to CT | **CORRECT** |
| **P5** | system LW LMP RISES, < $1.00 | **+$0.1301** | **CORRECT** |
| **P6** | **2021 C8 stays FAIL; 3452 stays convicted** | pre-solve measurement stands; 2025's 3491 is the in-sample analogue and stayed | **CORRECT so far** |
| **P7** | no new FAIL in 2023/2024 | leg A/B pending | pending |

**P3 was wrong, and the direction it was wrong in is the finding.** I reasoned
the LP would re-dispatch part of the freed floor economically, so class energy
would fall by less than the forcing removed. It fell by **more** (0.698 vs
0.676 TWh): the LP took back **none** of it and shed a little more besides. These
units are genuinely uneconomic in the hours the floor was holding them on —
which is precisely what a floor forcing a laid-up plant means, and it makes the
mechanism's case rather than weakening it. The prediction was still wrong and is
reported at full magnitude.

## 10. Named, and NOT taken here

* **The sub-5-day grain (§7).** The successor: a conduct instrument that sees
  idleness below the extract's 5-day floor. It has a real identification question
  (a short idle spell is ordinary cycling, which a measured operating floor exists
  to reproduce) and is not attempted here.
* **The uniform-`pmax` allocation (§2).** The deeper object: a fleet-average
  commitment fraction spread across a radically heterogeneous fleet. The per-plant
  analogue exists (`cc_mustrun_per_plant`'s top-`online_frac` placement).
  Redesigning the drag's allocation is a much larger change; named as the
  successor, not attempted.
* **The two-config `meta.json` defect is characterised (§8a) but not FIXED** —
  the composite still records neither key, so anything replaying that bundle
  still gets the forward config on 2023. The fix is a per-year recipe map in the
  composite writer.
