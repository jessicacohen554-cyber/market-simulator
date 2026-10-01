# PRECOMMIT — SPP-64: arm `st_gas_mustrun_per_plant` on SPP's 100 %-regulated steam fleet. NOTHING IS SOLVED YET.

**Lane** SPP-64 · **Base** `2a267cc44f01fad85cc1be8fca329ea34d78bb53` · **Keeper / control**
`2026-09-10-spp-62-vintage-census`, bundle `results/calibration/spp62_span` (committed WITH `hourly/`
sidecars — differenced, NEVER re-solved) · **Predecessors** `FINDING-spp-64-2026-09-10.md` (this
lane's R-bb root cause), `FINDING-spp-63`, `FINDING-spp-46`, `FINDING-spp-44`.

**THIS DOCUMENT IS PUSHED BEFORE ANY LP.** Every number below is re-derived in this session from the
committed artifacts, the scorer, and two zero-LP `run_year(fleet_only=True)` rebuilds. Rule 32
`[R-SHARD]`: the parent runs **no LP** — the solves are shards.

---

## 1. THE OBJECT, AND WHY IT IS NOT THE ONE SPP-46 KILLED

**R-bc′ — SPP's gas-steam fleet is 100 % vertically-integrated regulated utility generation and is
self-committed, so it dispatches at or above its measured minimum stable level; the model gives it
no commitment structure at all and therefore runs it near-dark.**

`FINDING-spp-46` §0.2 named this object itself and left it open:

> "(4) the residual after 1–3, **the vertically-integrated steam cohort at plausible inputs
> (−5.9 TWh), whose admissible construction is a market-design (self-commitment) object**, not a
> floor and not a band."

Its items (1) and (2) — the EIA-923 gas-price plausibility screen and the simple-cycle heat-rate
floor — **both landed** and are armed in this keeper (`f923_gas_price_plausibility_screen = True`;
the SPP-49 clamp fires on 12 plants in the 2024 rebuild). Item (3), Harrington's fuel vintage, was
carried by SPP-62's census. **Item (4) is what is left, and it is this arm.**

**Why this is not the form SPP-46 declared INADMISSIBLE.** SPP-46 killed *"the measured-state form
(**CAMPD online hours as the floor window**)"* — a window that replays the meter's own on/off record
— and SPP-44 killed the **P0-anchored** form. `st_gas_mustrun_per_plant` is neither:

| | the killed forms | **this arm** |
|---|---|---|
| window source | the hours CAMPD says the unit was on / the model's own P0 run pattern | a **scalar fraction** (`online_frac`) placed in the **top system-load hours**, which the model computes itself |
| responds to changed conditions? | no — it replays a recorded outcome | **yes** — the placement follows the model's own forward load shape |
| forward regeneration | none | `online_frac` + `committed_pct` re-derive from each new multi-year CAMPD vintage, the same construction as forecast emission rates (CLAUDE.md names that family rule-13 admissible) |

SPP-44's stated re-test condition was *"a MEASURED commitment-state membership on the ST_GAS fleet …
**never this leg re-armed on the P0 pattern**"*. This is that membership, and it is not the P0
pattern. **The lane states plainly that this is a judgement at the edge of a prior adjudication**,
and it is put to the gates rather than asserted.

## 2. RULE 17 `[R-FLOOR-WINDOW]` — the triple, with the driver grounded in a PUBLISHED fact

**(a) DRIVER.** SPP's gas-steam fleet is **100.0 % EIA-860 `Sector` 1 — "Electric Utility"**,
measured this session over the reconstructed 2024 fleet: **9,515 MW of 9,515 MW**, zero IPP, zero
industrial. By owner:

| utility | MW |
|---|---|
| Oklahoma Gas & Electric | 2,887.5 |
| Public Service Co of Oklahoma (AEP) | 2,111.0 |
| Southwestern Public Service (Xcel) | 1,772.0 |
| Southwestern Electric Power (AEP) | 1,543.0 |
| Sunflower Electric Power Coop | 399.5 |
| Western Farmers Electric Coop | 322.0 |
| Omaha Public Power District | 240.0 |
| Nebraska Public Power District | 99.3 |

A vertically-integrated utility commits its own steam to serve its own native load; it does not make
a merchant start/stop decision against the LMP. **`Sector` is a published per-plant integer with an
obvious forward story** — it is the identical admissibility class the owner ruled on for PJM at
capx D53/D78 (ruling Q56: *"zero free parameters — a partition on one published per-plant
boolean"*). The contrast is the discriminating evidence, not the level: the same census reads
**CC_REGULAR 68.9 % Sector 1 / 31.1 % IPP** and **CT_PEAKER 99.7 % / 0.3 %**, so the fleet is not
uniformly utility-owned and the reading is not vacuous.

**(b) WINDOW.** Each plant's own measured synchronization fraction `online_frac`, placed in the top
`online_frac × 8760` hours **ranked by the model's own system load**. Self-limiting by construction:
a genuine cycler floors only its top-load sliver. SPP's 22 ST_GAS plants carry `online_frac` from
0.286 (Mooreland) to 0.954 (Nichols), mean 0.518.

**(c) FORWARD STORY.** `committed_pct` (P5-of-online = the LSL) and `online_frac` re-derive from each
new CAMPD vintage; a retired or deregulated plant leaves the artifact. Nothing is pinned to an
observed generation level.

**THE LEVEL IS THE PHYSICS, AND IT IS THE SMALLER OPTION — chosen ex ante, not by fit.** The floor
level is `committed_pct` (P5-of-online = the minimum stable load), which the field's own docstring
calls *"the correct min-stable-load"*. The alternative levels in the same artifact are **larger**:

| level | floored energy, all-on basis |
|---|---|
| **`committed_pct` (LSL) — CHOSEN** | **9.090 TWh** |
| `p25_cf` (`st_gas_mustrun_p25_level`) | 14.427 TWh |
| `median_cf` | 23.319 TWh |

**`st_gas_mustrun_p25_level` is NOT armed and will not be.** Its rationale is MISO's own
out-of-market VLR record (Entergy South, Amite South / DSG / WOTAB); rule 25 `[R-ISO-SCOPE]` forbids
carrying that driver to SPP, and this lane has no SPP equivalent. **The lane is taking the smallest
of the three available levels, which is the one physics names — so the level cannot have been chosen
because it closes a gap.**

## 3. PHASE 0 — ZERO LP, and the arm is MEASURED LIVE AND SURGICAL

Two on-recipe `run_year(fleet_only=True)` rebuilds of the keeper's **2023** recipe, control and arm,
in one process with `clear_fleet_caches()` between (`scripts/lib/bundle_fleet.py`):

| min_gen, TWh | CONTROL | ARM | Δ |
|---|---|---|---|
| nuclear (unclassed row) | 16.9270 | 16.9270 | **0.0000** |
| **ST_GAS** | **0.0000** | **3.8701** | **+3.8701** |
| CC_CHP | 0.6664 | 0.6664 | **0.0000** |
| CT_CHP | 0.5470 | 0.5470 | **0.0000** |
| ST_CHP | 0.0318 | 0.0318 | **0.0000** |
| **TOTAL** | 18.1721 | 22.0422 | **+3.8701** |

**The mechanism is live for SPP** (it is gated on the per-ISO artifact, not on an ISO name —
`campd_bins.py` registers `("st_gas_mustrun_per_plant", ("online_frac",), ("ST_GAS",))`, and
`thermal_tranches_SPP.csv` carries `online_frac` on all 22 ST_GAS plants), and **it touches ST_GAS
and nothing else, to the fourth decimal.**

## 4. RULE 19 `[R-ONE-MECH]` — the enumeration, MACHINE-VERIFIED

**Nothing floors or prices SPP ST_GAS today.** The keeper's own committed
`legitimacy_diagnostics.json` D-2 lists **every** forcing mechanism in the run:
`nuclear_mustrun` and `chp_steam` (on CC_CHP / CT_CHP / ST_CHP) — **ST_GAS does not appear at all**.
Corroborated independently by §3's control column (ST_GAS min_gen = 0.0000) and by SPP-44 / SPP-63's
finding, reproduced here, that `pmin_mw`, `min_run_hours`, `min_down_hours` and
`startup_cost_per_mw` are **0 on every SPP fossil unit**. The only live ST_GAS pricing channel is
`offer_curve_by_group` at a uniform 0.93, which is **untouched by this arm**.

So this adds **one** mechanism to **one** class that currently has none. Nothing is stacked, and
nothing is replaced.

## 5. THE SCREEN YEAR — 2023, NAMED ON THE MECHANISM'S OWN MEASURED FOOTPRINT

Forced increment `Σ_t max(0, floor_t − ST_GAS_model_t)`, computed model-vs-model from the keeper's
committed `class_hourly_<year>` and `system_<year>` sidecars plus the tranche artifact — **no actual,
no residual anywhere in the statistic**:

| year | floor MW (all on) | model ST_GAS TWh | **FORCED INCREMENT TWh** | C1 residual |
|---|---|---|---|---|
| **2023** | 1,690 | 7.087 | **4.894 ← LARGEST** | −8.38 |
| 2024 | 1,690 | 10.386 | 2.803 | **−9.71 ← largest residual** |
| 2025 | 1,690 | 9.206 | 3.367 | *(C1 skipped — preliminary EIA-923)* |

**The footprint choice and the residual choice DISAGREE, and the lane takes the footprint.** 2024
carries the larger C1 miss and the *smaller* footprint; 2023 is screened. That disagreement is the
demonstration that rule 29's "never the residual" clause is being honoured rather than recited.
*(The 7.087 here is the gross class series; the scorer's grid-delivered 2023 value is 6.640. The
floor acts on the gross series, which is the correct basis for this statistic.)*

## 6. THE STOP GATES — STRUCTURAL, PRE-REGISTERED, AND NONE READS THE TARGET ROW

Rule 29: a screen **may kill an arm; it may never promote one.** **`C1 ST_GAS` is the TARGET and is
NOT a gate in either direction** — no gate below improves-or-fails on it.

| gate | asks | STOP bar |
|---|---|---|
| **G-1** config identity & liveness | `st_gas_mustrun_per_plant: true`; `st_gas_mustrun_p25_level` **false**; ten fossil classes still 0.93 × 4 bands; coal supply census 32 lines / `6193,prb` present | any mismatch |
| **G-2** reach | ST_GAS **gross** dispatch rises with the direction and order of magnitude §3/§5 imply | ΔST_GAS **outside [+2.0, +7.5] TWh** |
| **G-3** the identity it asserts | the added ST_GAS energy lands **in the floored hours** (top-`online_frac` system-load hours), not spread flat | **< 0.80** of the increase inside the floored-hour set |
| **G-4** no new forcing beyond the declared mechanism | `dump` = 0; **no class other than ST_GAS acquires min_gen**; slack within the keeper's own measured envelope | dump > 0, or any non-ST_GAS class gains min_gen, or slack **> 370.102 MWh** (the keeper's own 2024 value, re-derived §7) |
| **G-5** no non-target load-bearing regression | C3a within ±10 %; C3b ≤ 0.20; C2 family volumes in band — scored by `scripts/lib/spp63_g5.py` (re-validated on keeper 7 this session: C3a 25.65 / 25.79 / 29.23, C3b 0.172 / 0.172 / 0.167, reproducing the scorer exactly) | any **PASS → FAIL** |
| **G-6** displacement cost | **no C1 class that is currently IN band is pushed OUT of band** (this reads the arm's neighbours, never ST_GAS) | any in-band class leaves the band |

**G-6 is the gate with real bite, and the lane says so before the solve.** §3's 3.87 TWh must come
from somewhere. In 2023 the only classes carrying surplus are CT_PEAKER **+2.407**, COAL_PRB
**+1.598** and CC_CHP **+0.116** — **4.121 TWh, and the arm forces 3.870**. If the displacement lands
instead on CC_REGULAR (already **−3.569**, headroom 4.431) or COAL_LIGNITE (**−2.103**, headroom
5.897) those rows worsen. On the pre-solve arithmetic no class leaves the ±8.00 TWh band, but the
allocation is exactly what the LP decides and what this screen exists to measure.

**Declared in advance so it cannot be read as a post-hoc excuse — rule 20 `[R-FORCED-BUDGET]` is a
KNOWN OPEN RISK and is deliberately NOT a screen gate** (a screen bundle cannot be scored for C8).
ST_GAS would carry roughly a third of its energy at a binding floor, against `d2_merchant_max_share`
0.30 and with ST_GAS **not** in `d2_exempt_classes`. Two things the SPAN — not this screen — must
adjudicate: (i) whether a class measured **100 % regulated-utility** is a "**merchant** class" within
the rule's own words at all; (ii) failing that, the rule's conditional pass on provenance + shape,
for which the D-4 window entry **already exists**
(`(MECH_ST_GAS_MUSTRUN_PER_PLANT, "ST_GAS"): (0, 24)`, self-windowing, so off-window binding is nil
by construction) and **D-1 `profile_r` ≥ 0.80 / `cv_ratio` ≥ 0.50 is the genuinely uncertain leg**.
**If the span lands over budget and D-1 misses, the arm is not a keeper and this lane will say so.**

## 7. G-DRIFT — the code-level audit, so no control solve is spent (rule 29(b) form 4)

The keeper's recorded `basis_sha` `67feede7…` **does not resolve** at this base (the 2026-08-16
history rewrite). The audit is therefore anchored on the commit that **added the bundle**,
`54e0c30cbfb3b368f42258221de3d0d8b1be2135` ("SPP-62 span: 2023-2025 vintage-census arm, solved and
registered"). `git diff 54e0c30c HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` returns
**13 files**, every one classified:

| file | Δ | classification |
|---|---|---|
| `data/raw/reference/spp_curtailment_share.csv` | +867 | **INERT off** — read only under `spp_curtailment_ceiling`, which this arm leaves **false** |
| `scripts/run_calibration.py` | +69/−? | **INERT off** — ceiling CLI leg, guarded `if config.spp_curtailment_ceiling and iso == "SPP"` |
| `scripts/run_calibration_full.py` | +62 | **INERT off** — ceiling CLI flags, `None`-gated |
| `src/market_sim/config/scenarios.py` | +113 | **INERT off** — ceiling fields at their declared cache-key defaults |
| `src/market_sim/data/curtailment_share.py` | +113 | **INERT off** — SPP ceiling functions, called only under the flag |
| `src/market_sim/data/renewables.py` | +19/−2 | **INERT off** — adds `and not _spp_ceiling`; identical with the flag off |
| `src/market_sim/runner.py` | +29 | **INERT twice** — forecast leg + `iso == "SPP" and flag` |
| `src/market_sim/model/interchange/spec.py` | +63/−? | **INERT** — comment-only (miso-252) |
| **`src/market_sim/pipeline/ttc.py`** | **+33/−?** | **INERT — another ISO's branch.** The entire hunk is below `if iso != "NYISO": return ttc` (nyiso-224 cutset envelope) |
| **`src/market_sim/config/constants.py`** | **+171** | **INERT — purely additive, ZERO removed lines**, one new top-level name `NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH` |
| **`src/market_sim/config/solve_surface_declared.py`** | **+4** | **INERT** — the declaration for that NYISO table, dropped at its as-committed value so every pre-existing key stays valid |
| `scripts/lib/forecast_parity_registry.py` | +70 | **INERT** — forecast parity registry; a `mode="backcast"` run never enters it |
| `scripts/lib/spp63_g5.py` | +144 | **INERT** — parent-side scorer, on no solve path |

**Machine corroboration:** the capx-D79 solve-surface fingerprint `moved_rows("SPP")` is **`{}`** —
zero rows moved at HEAD. **All hunks INERT ⇒ form 4 is valid, keeper 7's committed bundle IS the
control, and NO control solve is spent.**

## 8. DOF — rule 21 `[R-DOF]`

Ledger goes **3 entries / 2 residual → 3 entries / 2 residual. ZERO free parameters are added.**
`st_gas_mustrun_per_plant` is a boolean gate, not a parameter; the floor level (`committed_pct`) and
the window size (`online_frac`) are **each plant's own CAMPD record at the grain the floor is applied
at**, read from a rule-23-frozen artifact this lane does not regenerate or touch. No scalar is
introduced, none is tuned, and nothing is swept against any gate in §6.

## 9. THE SOLVES — rule 32 `[R-SHARD]`. The parent runs NO LP.

SPP solves ~150 s/year, ~440 s for the span.

```
SCREEN  claude/spp64-screen-2023   results/calibration/spp64_screen_2023   ~150 s
  python3 scripts/replay_keeper.py results/calibration/spp62_span \
    --years 2023 --out-dir results/calibration/spp64_screen_2023 \
    --set st_gas_mustrun_per_plant=true

SPAN    claude/spp64-span          results/calibration/spp64_span          ~440 s
  python3 scripts/replay_keeper.py results/calibration/spp62_span \
    --years 2023 2024 2025 --out-dir results/calibration/spp64_span \
    --set st_gas_mustrun_per_plant=true
```

**The SPAN is the only registerable bundle** (protocol §3). The screen is a throwaway probe — never
registered, never a keeper, never quoted as a keeper number — and its year is re-solved inside the
span. **The span runs only if the screen clears every gate in §6.**

Both bundle families are **gitignored** (`results/calibration/spp64_*/`), which is what discharges
rule 29(c). **Rule 31 `[R-RETAIN]`: nothing will be `rm`'d, and nothing is deleted before the owner
rules on promotion.**

**KNOWN TRAP, pre-declared:** `replay_keeper.py --out-dir` does not propagate
`calibration_attestation.json`, so the bundle scores **C6 UNATTESTED** unless the parent authors it.
`scripts/gen_spp63_attestation.py` is the template; the span shard re-points `attested_by` at this
lane and declares §8's zero-DOF finding. **`authorized_price_tuning`: the inherited uniform 0.93 is
declared unchanged — this arm does not touch the offer channel.**

## 10. WHAT THIS LANE PRE-COMMITS TO REPORTING, WHATEVER THE RESULT

- **The exact C1 bar, stated now so no one can re-read it later.** The band is
  `FUELMIX_VOL_CAP_TWH = 8.0` TWh, and the scorer's own text on the keeper reads
  *"2023 ST_GAS: −8.38 TWh, share −2.9pp (volume out of band)"* and *"2024 ST_GAS: −9.71 TWh, share
  −3.3pp (volume/share out of band)"*. So the bar is **+0.38 TWh (2023)** and **+1.71 TWh volume plus
  +0.3 pp share (2024)** — **not** the 8–10 TWh a reader would infer from the headline gap. That is
  why this arm is worth an LP at all, and it is stated **before** the solve.
- **What closing C1 would and would not mean.** C1 and C3c are the only failing criteria. If C1
  closes, **C3c becomes the LONE failure and rule 22 `[R-C3C]`'s standing rule can fire** — the
  scorer, not this lane, would then produce the determination. **CALIBRATED is the scorer's to
  produce**; this lane neither adds, requests nor implies a `complete` marker or a `frontier`
  declaration, both of which are OWNER acts. C3c itself is **untouched** by this arm and remains
  `FINDING-spp-64`'s R-bd.
- Every gate in §6 at full magnitude, pass or fail, and the rule-20 forced-budget outcome
  **including D-1** whatever it says.
- **Registration under rule 15 `[R-DASHBOARD]` whatever the span says** — keeper or rejection — in
  the session that produces it, plus the rule 28 matrix cell for `st_gas_mustrun_per_plant` in
  **SPP's shard only**.
- The **promotion question put explicitly in-session** (rule 31), with the statement that the
  bundles live on gitignored local disk and do not survive this container.
- `[R-HOLDOUT]` was removed 2026-09-09, so no year is protected from being iterated against. Every
  number here and in the result is model-**SELECTION** evidence, never a certified out-of-sample
  skill claim.
