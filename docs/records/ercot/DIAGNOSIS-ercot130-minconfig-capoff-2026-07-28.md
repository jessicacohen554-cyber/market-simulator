# DIAGNOSIS — ERCOT-130: the min-config UPPER bound (cap a coal plant OFF when it cannot reach its minimum online configuration) is REFUTED — not because the residual leg is too small, but because it is not what the charter assumed. In 99.8 / 99.0 / 100.0 % of the plant-hours the cap-off would zero, the real plant was **running**, and in 71 / 39 / 86 % of them it was running at or **above** its own minimum online configuration. The defect is the model's coal AVAILABILITY, not its min-config bound

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot130-capoff ·
**Keeper under audit** `2026-07-28-ercot129-conditional-coal-min` (bundle
`results/calibration/ercot129_conditional`) — **unchanged by this session** ·
**Chartered by** `PRECOMMIT-ercot129-coal-minconfig-conditional-2026-07-28.md`
§3's last bullet, which named the category-B hours and explicitly did **not**
fix them ·
**Method** Phase 1 only — the keeper's committed dashboard run payload, the
keeper's own fleet-array availability captured at the exact point the
ERCOT-129 conditional consults it, the frozen EIA-860 min-config artifact and
CAMPD unit-level operation, through
`scripts/probes/ercot130_capoff_phase1.py`.
**No LP was solved. No year was registered. No `ScenarioConfig` field was
added, no cache-key surface and no solve path was touched. No keeper file was
touched.** Default cache key verified `603c2498bf71d21d` at session start and
at session end.

**Outcome: ABSTAIN — the eighth consecutive abstention on the coal residual,
and the first that dies on CORRECTNESS rather than on an ex-ante size bound.**

The charter's Phase-1 gate (a) was a size test: *"if it is small (< ~2 % of
online coal hours), the fix is COSMETIC — say so and STOP."* **That gate
PASSES** — category B is 2.17 / 4.22 / 1.70 % of online coal plant-hours, above
the bar in two years of three, and it is **100 %** of the keeper's residual
physically-impossible operation (§2). On the charter's own written test this
lane would have proceeded to a solve.

It does not proceed, because a check the charter implies but does not name
refutes the mechanism's premise outright. The charter states the physical
story as *"Reality would show it OFF."* Measured against CAMPD, reality shows
it **ON** in 99–100 % of those hours (§3). The cap-off would force off a fleet
that demonstrably ran — the precise inversion of the ERCOT-128 §1.3 safety
argument, which licensed the plant-grain interval because a relaxation "never
forbids something the real plant did". An upper bound is the unsafe direction,
and here it is unsafe in almost every hour it would touch.

§4 locates the actual root cause, and it is already a named, owner-gated lane.

---

## 0. What is inherited, re-verified rather than assumed

| claim | source, verified this session |
|---|---|
| keeper is `2026-07-28-ercot129-conditional-coal-min` | `frontend/data/backcast/keepers/ERCOT.json` |
| default `ScenarioConfig().cache_key() == 603c2498bf71d21d` | reproduced; **unmoved** at session end (no config field added) |
| `coal_min_config_ERCOT.csv` — 10 plants, 2,164 MW, cap-weighted 0.1590 | reproduced; sum of `min_config_mw` = 2,164 MW |
| the floor arms and bites under the keeper recipe | live log: `coal_min_config floor ARMED (availability-conditional): 10 plants, 2164 MW … across 78 tranches` |
| `2026-07-28-ercot128-unit-grain-coal` is the rejected availability-SCALED control | dashboard registry, unchanged |
| `ercot_thermal_dam_availability_coal = False` in the keeper | `run_config.json:666`; the DAM water-fill logs `CC_REGULAR / CT_PEAKER / ST_GAS` only — **coal is not in the water-fill's class set** |
| derive script untouched (rule 23) | `scripts/data/derive_eia860_coal_min_config.py` not run, not edited |

**Environment parity with the ercot115–129 baseline, recorded:** the gtc-limits
clean partition is absent, so `ercot_gtc_limits_measured` falls back to
**"static TTC kept" 3/3** — matching every ERCOT-115…129 baseline. The
`hydro-plant-modes` WARNING and the benign replay-path
`ercot_wtx_curtailment_driver … stomped by prb_overrides` WARNING both appear as
expected. **Test state (empty `src/` diff):** `test_persisted_identity` 11/11,
`test_flag_registry` 12/12, `test_coal_min_config_floor` 18/18 — all as
inherited; no pin was updated.

## 1. Method, and the one measurement correction it forced

**Availability is captured, not reconstructed.** Category B is *defined* by the
array the ERCOT-129 conditional consults —
`total[p,t] = Σ_k availability[k,t] × pmax[k]` over the plant's COAL rows — so
the probe monkeypatches the live fleet-array constructor
(`scripts/run_calibration.py:76`, **not** `market_sim.runner`: the runner's copy
is not the one the calibration path calls) under the keeper's own replayed
kwargs, records that array, and aborts before any LP is built. The measurement
is therefore exact for the gate rather than a proxy for it.

**Per-plant dispatch comes from the keeper's committed run payload**, the
ERCOT-128 sections A–G basis (rule 15 `[R-DASHBOARD]`: the payload, not a
replay), so the counts are directly comparable to that lane's.

**Correction — the payload is uint8-quantized, and it matters here.** The
payload stores each plant-hour as an integer percent of the bench nameplate, so
its resolution is `npl/100` — **3.5 to 24.4 MW** depending on plant. Scoring
"below `min_config_mw`" at exact equality therefore counts every hour a plant
sits *pinned at its floor* and rounds down. That artifact is large enough to
invert the headline result, so it is stated explicitly and both bases are
reported in §2. Any successor reading this payload for a threshold comparison
must carry the same half-step tolerance.

## 2. Leg (a) — the residual leg, measured on the CURRENT keeper

The keeper's residual physically-impossible operation splits exactly two ways:

* **category A** — plant online, its available capacity *can* reach
  `min_config_mw`, yet it dispatches below it. This would be a **failure of the
  ERCOT-129 floor itself**.
* **category B** — plant online while `Σ_k avail[k,t]×pmax[k] < min_config_mw`.
  ERCOT-129 correctly drops the floor to zero here (a floor above available
  capacity is infeasible) and nothing then stops the LP running the plant below
  its minimum configuration. **This lane's target.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| online coal plant-hours | 77,986 | 77,374 | 73,737 |
| **category A**, exact comparison | 6,532 | 6,082 | 3,350 |
| **category A**, half-quantization-step tolerance | **0** | **0** | **0** |
| **category B** | **1,690** | **3,262** | **1,257** |
| category B, share of online plant-hours | **2.17 %** | **4.22 %** | **1.70 %** |
| category B energy | 0.1341 TWh | 0.2699 TWh | 0.1148 TWh |
| … share of model coal energy | 0.221 % | 0.462 % | 0.188 % |

**Two results, and the first is a clean finding for ERCOT-129.** Category A is
**exactly zero** in all three years once the payload's own resolution is
respected — not "small", zero. The availability-conditional floor is airtight
wherever it applies: whenever a plant *can* reach its minimum online
configuration, it does. The apparent 3,350–6,532 hours are entirely the uint8
artifact of §1.

**Therefore category B is 100 % of the keeper's remaining physically-impossible
coal operation.** That is what makes the charter's size gate pass: this is not a
partial polish on a partly-fixed defect, it is the whole of what ERCOT-129 left
behind, and no other mechanism in the model addresses it.

Where it lives (plant-hours):

| plant | 2023 | 2024 | 2025 | `min_config` MW |
|---|---|---|---|---|
| Major Oak Power (7030) | 892 | 946 | 1,089 | 95 |
| San Miguel (6183) | 336 | 1,488 | 0 | 250 |
| W A Parish (3470) | 347 | 636 | 24 | 175 |
| Sandy Creek (56611) | 115 | 0 | 0 | 360 |
| J K Spruce (7097) | 0 | 192 | 0 | 130 |
| Limestone (298) | 0 | 0 | 144 | 300 |

Note that **Major Oak is the single plant whose unit feasible set is NOT
connected** (ERCOT-128 §1.3 — `[95,153] ∪ [190,305]`, a 17.6 % gap), and it is
the largest category-B contributor in all three years.

## 3. The refutation — what the real plants did in exactly those hours

The charter's physical premise is one sentence: *"Reality would show it OFF."*
It is testable directly, and it is a legitimate ex-ante diagnostic rather than a
model input (rule 13 `[R-MEASURED]`: this is used to adjudicate a proposed
mechanism, never fed to the LP). CAMPD gross load, scaled to the bench net total
by the per-year factor 0.8972 / 0.9051 / 0.9069 — applied to one side only:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| category-B plant-hours | 1,690 | 3,262 | 1,257 |
| real plant **RUNNING** in them | **99.8 %** | **99.0 %** | **100.0 %** |
| real plant at or **ABOVE** its own `min_config_mw` | **71.1 %** | **38.6 %** | **86.4 %** |

Per plant, median actual output in its own category-B hours against the model's
median available capacity in the same hours:

| plant · year | model avail (MW) | `min_config` (MW) | **median ACTUAL (MW)** |
|---|---|---|---|
| W A Parish · 2023 | 59 | 175 | **342** |
| W A Parish · 2024 | 110 | 175 | **310** |
| W A Parish · 2025 | 127 | 175 | **473** |
| Major Oak · 2023 | 77 | 95 | **155** |
| Major Oak · 2025 | 77 | 95 | **157** |
| Limestone · 2025 | 289 | 300 | **377** |
| J K Spruce · 2024 | 104 | 130 | **209** |
| Sandy Creek · 2023 | 342 | 360 | **356** |
| San Miguel · 2024 | 216 | 250 | **226** |

**The cap-off is refuted.** It would zero a plant in hours when the real plant
was not merely synchronised but, in most of them, loaded *above* the minimum
configuration the model claims it cannot reach. W A Parish is the extreme case:
the model says 59 MW of coal is available and the plant delivered 342 MW — a
factor of six. This is the direction ERCOT-128 §1.3 expressly guarded against:
the plant-grain interval was licensed as a **relaxation**, safe because it
"never forbids something the real plant did". An upper bound has no such
protection, and here it forbids exactly that, in ~99 % of the hours it touches.

Removing 0.134 / 0.270 / 0.115 TWh of measurably-real generation to enforce an
internal consistency property is a worse model, not a more structural one. Rule
1 `[R-STRUCT]` protects a real market behaviour that hurts the fit; it does not
protect a mechanism whose own physical premise is contradicted by measurement.

## 4. Root cause — this is the coal AVAILABILITY defect, and it is ERCOT-116's

Category B is not a min-config phenomenon. It is the narrow, visible tip of a
systematic under-estimate of ERCOT coal availability. Counting hours in which
the *actual* plant output exceeds the model's entire available coal capacity for
that plant:

| plant | 2023 | 2024 | 2025 | model mean avail (2023) |
|---|---|---|---|---|
| Major Oak (7030) | 5,393 | 5,323 | **6,727** | 77.3 % |
| W A Parish (3470) | 3,509 | 4,276 | 4,444 | 53.5 % |
| J K Spruce (7097) | 2,365 | 2,131 | 3,480 | 47.3 % |
| Martin Lake (6146) | 2,517 | 2,837 | 2,832 | 74.5 % |
| Limestone (298) | 1,732 | 2,415 | 3,351 | 56.9 % |
| Oak Grove (6180) | 1,444 | 1,697 | 3,488 | 86.7 % |

The model's availability ceiling is below what the fleet measurably delivered in
**1,200–6,700 hours per plant-year** — 14 % to 77 % of the year. Category B is
just the sliver of that error where the shortfall happens to cross a
`min_config_mw` line.

**This is ERCOT-116, already measured and already on the owner's desk** (one of
the four decisions this session inherits, §7 item 1):
`2026-07-26-ercot116-coal-avail-probe` is measured-correct and halves the
ceiling pin 43/41/50 → 20/16/17 %, at a C1 cost of +5.7/+8.9/+11.0 TWh. It is
the coal lane's only live instrument, and the owner has not ruled. **It is not
armed here.**

Rule 14 `[R-ACCURATE]` is the governing rule and it points one way: the input is
inaccurate, and the response is to fix the input, not to add a second mechanism
that hides the consequence. The cap-off would do exactly the latter — it would
convert "the model thinks too little coal is available" into "the model turns
the plant off", burying the error one layer deeper and making the ERCOT-116
correction *harder* to see when it is eventually adjudicated.

**One plant is a different problem, and it is also already named.** San Miguel
(6183) contributes 336 / 1,488 / 0 category-B hours, and there the real plant
clears its own `min_config_mw` in only **1.5 % / 2.5 %** of them (median actual
226 MW against a registered 250 MW minimum). That is not an availability error —
it is the open **registration** question recorded in the ERCOT-129 promotion
note: San Miguel's EIA-860 registered minimum load is genuinely 0.639 of its
capacity and the real plant sometimes runs below its own filed LSL. Capping it
OFF is the worst available response to that, and lowering the measured value is
forbidden (rule 21). It stays open, untouched.

## 5. Legs (b) and (c) — reported as chartered, for the record

**Leg (b), the C1 cost bound — would have passed.** The category-B energy is
removed outright (there is no floor to replace it), so the lift-in-place bound
is a hard upper bound on the loss; the LP would recover part of it by
substituting other coal:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| keeper C1 (TWh vs actual) | +0.371 | +0.797 | −1.167 |
| energy removed (upper bound) | −0.134 | −0.270 | −0.115 |
| **projected C1, worst case** | **+0.237** | **+0.527** | **−1.282** |

All three inside G2's ±2.0. The risk year 2025 lands at −1.282 against the −2.0
bound with 0.7 TWh of room. **The charter's cost gate does not refute this lane
either** — §3 does, alone.

**Leg (c), rule 19 `[R-ONE-MECH]` — and this is where the design fails a second
time.** The narrow reading holds: an availability change creates no `min_gen`,
so D-2/D-4 attribution would be literally unchanged and no new mechanism id
would appear. But rule 19 asks what *else* already addresses the phenomenon, and
the answer is now unambiguous: the phenomenon is coal availability being wrong
(§4), and the mechanism that owns it is the availability layer itself — the
ERCOT-116 lane. The cap-off would be a second mechanism stacked on the
unexplained residual of an existing one, which is the exact pattern rule 19
forbids. **A design that produced no D-2 row would not have made it legitimate;
it would only have made it invisible.**

**The seam question, answered even though the design is refuted.** Had it been
built, the change belonged immediately **before** `_compose_min_gen_floors`
(`src/market_sim/data/fleet/arrays.py:2306`) and **after** every availability
layer — the CAMPD outage overlays, the ERCOT DAM class-hour water-fill, the
NEISO block and the hydro-ROR cap. Before the compose call, because `min_gen`
must never exceed `pmax × availability` or the LP is infeasible; after the
water-fill, because that overlay *sets a cap-weighted class-hour mean to a
measured fraction* and would have redistributed any zeroed coal capacity across
the rest of the class, silently moving coal availability fleet-wide and
invalidating the A/B. In this keeper the hazard is latent rather than live —
`ercot_thermal_dam_availability_coal=False`, so COAL_PRB/COAL_LIGNITE are
dropped from the overlay's class dicts and the water-fill provably cannot reach
coal (verified in the live log: `CC_REGULAR`, `CT_PEAKER`, `ST_GAS` only). It
would have become live the moment ERCOT-116 or ERCOT-110's coal scope is armed.
Recorded so a successor does not have to rediscover it.

## 6. Incidental finding, outside this lane — Sandy Creek is dark for all of 2025

Not part of the charter and **not fixed here**, but surfaced because it is
larger than the entire quantity this lane was chartered to remove:

| Sandy Creek Energy Station (56611), 2025 | |
|---|---|
| model available capacity | **0.0 MW in all 8,760 hours** |
| model dispatch | **0.000 TWh** |
| CAMPD (net-equivalent) | **1,300 running hours, 0.697 TWh, peak 895 MW** |

The plant carries its 936 MW of `pmax` in the 2025 fleet, so this is an
availability overlay zeroing it for the full year, not a retirement. For
contrast, 2023 and 2024 carry 7,152 and 6,720 non-zero availability hours and
the model *over*-produces there (4.51 / 4.56 TWh model against 3.19 / 2.97 TWh
CAMPD). The 0.697 TWh of missing 2025 generation is ~5× the category-B energy
this lane targeted, and it is the phantom-outage signature ERCOT-79 diagnosed
for the cycling classes. **Recommend a dedicated look; it is not this lane's to
fix and no attempt was made.**

## 7. Recommendation

1. **Do NOT build the min-config upper bound.** No `ScenarioConfig` field, no
   solve, no bundle, no dashboard registration — there is no run to register
   (rule 15 `[R-DASHBOARD]` binds completed runs; this lane produced none, as
   ERCOT-124/125/127 and ERCOT-128 Phase 1 also did not).
2. **The reason is correctness, not size.** The charter's size gate (a) PASSES
   at 2.17 / 4.22 / 1.70 % of online plant-hours and 100 % of the residual
   defect, and its cost gate (b) passes with 0.7 TWh of room. The lane dies
   because reality ran those plants in 99–100 % of the target hours (§3).
3. **`ercot129`'s floor is vindicated on a point it never claimed.** Category A
   is exactly zero: wherever the conditional floor can apply, it binds
   correctly. The residual is not a gap in the mechanism.
4. **Route the residual to ERCOT-116** (§4). Every category-B hour is a coal
   availability shortfall; the correct repair is the accurate availability
   input, which is measured, built, and awaiting an owner ruling — **not armed
   here**.
5. **Reopening condition, stated so it is testable.** If ERCOT-116 (or any
   successor availability correction) is armed and category B *survives* on the
   corrected availability — i.e. plant-hours where the model cannot reach
   `min_config` **and CAMPD agrees the plant was off or below it** — then an
   upper bound becomes the right instrument for that residue, and this
   document's §5 seam analysis applies unchanged. On today's availability it is
   not.
6. **Four inherited owner decisions, surfaced not decided:** (1) ERCOT-116 coal
   availability — measured-correct, halves the ceiling pin, C1 +5.7/+8.9/+11.0
   TWh, the coal lane's only live instrument, **now also the named root cause of
   this lane's residual**; not armed. (2) `BIN_FORCED_DERATE_BY_YEAR`
   (`eia860.py:2392-2404`, applied `arrays.py:619-624`) — a live rule 26
   `[R-REGISTRY]` breach sitting in the same availability path this lane
   inspected; **read, not touched**, and §4's availability gap is consistent
   with it contributing. (3) The ramp-envelope GROSS/NET basis error
   (ERCOT-127 §1). (4) The ERCOT-122 offer-LEVEL controlled refutation. Plus
   the San Miguel registration question (§4) and the new Sandy Creek 2025
   finding (§6).

## 8. Scope, closed items honoured, artifacts

Holdout years 2022 / 2019 / ≤2021 / H1-2026 untouched (rule 22) — only 2023,
2024, 2025 were read, and none was solved. No GitHub Actions workflow was
created (the fleet-array capture ran in-session).
`scripts/data/derive_eia860_coal_min_config.py` was neither run nor edited (rule
23). `frontend/data/backcast/keepers/ERCOT.json` untouched. Every CLOSED lane
stayed closed: the four coal offer-surface lanes, the coal availability
ENVELOPE layer (ERCOT-126 §§2-3), coal ramp trajectory bounds, the plant-grain
fractional min-load floor, unit-grain commitment STATE and its detectors,
the availability-SCALED min-config floor, age/temp coal derates, the EP-rebasis
C3c lane, the pooled HH-0.50 artifacts, `ercot_zonal_gas_basis` ablations and
the West/Panhandle topology split. ERCOT-116 was neither armed nor promoted.

**Artifact:** `scripts/probes/ercot130_capoff_phase1.py` — `--capture` rebuilds
the keeper's coal availability from the live fleet-array path (~90 s/year, no
LP); the default mode scores legs (a) and (b). The cached availability
(`results/calibration/_ercot130_avail_cache/avail_<year>.npz`, 4 KB/year) is
gitignored and regenerable from the committed tree.
