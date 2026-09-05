# PRECOMMIT — caiso-250: WHAT SETS λ WHEN NO THERMAL UNIT IS MARGINAL

**Session caiso-250, 2026-09-05.** Branch
`claude/caiso-250-backcast-calibration-7tci3e` off `main` `182aa74a`. Keeper
**`2026-09-05-caiso-246-b1-spot`** (`caiso246_b1_spot_coverage`, `git_sha`
`900402b`), **NOT-YET**, C3a the sole load-bearing FAIL at **+3.9 / +12.3 /
+11.4 %**.

**Pushed to `origin` BEFORE the estimator is coded and BEFORE any cell of the
object is computed.** Nothing is armed: no `ScenarioConfig` field, no CLI flag,
no derive, **no LP, no solve, no run registration, no promotion.** Rule 22
`[R-HOLDOUT]`: 2023–2025 only, hard-filtered and fail-closed; CAISO holds no
`complete` and no `final` marker and the holdout freeze is ACTIVE.

---

## §0 — THE OBJECT, AND WHAT IS ALREADY DECIDED ABOUT IT

**The object is caiso-249 §6 item 1, taken as ranked**: in the zone-hours
caiso-249 labels `STORAGE` — a **residual** label, assigned when no own-zone or
delivery-factor-reachable domestic unit price-matched and storage happened to
be cycling — **43.4 % (2024) / 55.0 % (2025) of the C3a gap** sits with no
identified price-setter. No DOM_GAS number is quotable until it resolves
(caiso-249 P-9: the tol-0.75 variant moves the DOM_GAS share **+31.7 / +32.7
points**).

### §0.1 — What the code says the candidate carriers can be, read BEFORE measuring

Read off the shipped LP builder and the keeper's own `run_config.json`, not off
a residual. A column strictly between its bounds has zero reduced cost, so its
stationarity is an EXACT identity for λ:

| column | rc = 0 gives | reachable on this keeper? |
|---|---|---|
| thermal `P[g,t]`, own zone | `λ_z = mc_g` | YES — and **already tested**: this is exactly caiso-249's own-zone pass, so by construction it FAILED in every `STORAGE` zone-hour |
| storage `Chg[s,t]` | `λ_z = −ε − η_c·ν_s` | YES (`ν` = the SOC-row dual) |
| storage `Dis[s,t]` | `λ_z = ε + vom_s − ν_s/η_d` | YES (`battery_dispatch_adder = 5.0`; PS per-plant adders) |
| hydro `P[g,t]` | `λ_z = mc_g + w_{g,m}` | **YES — and INVISIBLE to every price-match instrument this lane has run.** `hydro_dispatch_envelope`/`hydro_budget_nameplate_aware`/`hydro_min_flow_floor` are all ARMED, so `_build_hydro_rows` puts a **monthly energy-budget row per (hydro unit, month)** in the LP. Its dual `w` is the water value; it is NOT in `mc`, so an `mc = λ` test can never see a marginal hydro unit. 160 CAISO hydro units across all five CA zones |
| W/S | `λ_z = mc_ren` (≈ 0 or the REC floor) | YES, but those hours are the `SURPLUS` label, which is assigned ahead of `STORAGE` |
| import rows | the caiso-244 complementarity | YES — **already tested** as the `HUB` pass (acquitted, 5.1 / 7.8 % of the gap) |
| ramp rows | — | **NO**: `ramp_limits = False`, no ramp rows exist |
| reserve co-opt rows | — | **NO**: `caiso_reserve_coopt = False`, `energy_reserve_coopt = False` — reserves are not in the energy balance |

**The falsifier the handoff names — "the carrier is a CONSTRAINT (reserve
co-optimisation, ramp, the RA must-offer floor, or the ORDC scarcity adder)" —
is therefore already half-decided by the recipe, and is registered here as a
decision made from the code before measurement:** the reserve co-opt and the
ramp rows **do not exist in this LP**, and the RA must-offer floor is a *bound*,
not a row — a unit at a min-gen floor has `mc ≥ λ` and cannot set the price
(it explains why the thermal stack sits ABOVE λ; it does not say what sets λ).

### §0.2 — The ORDC scarcity adder is NOT re-measured. It is cited and bounded out.

`caiso_scarcity_pricing = True` on this keeper, and the adder is **folded into
the persisted price** (`runner.py`: `result.prices = result.prices + caiso_adder`,
written by `run_calibration_full._system_frame`) — so the committed
`system_<year>.parquet` `price` is `λ_LP + A(t)`, not the raw dual. That matters
for every price-match instrument in this lane, and it is **already adjudicated**:
**caiso-229 bounded `A(t)` arithmetically on CAISO's own constants (VOLL 2000,
MCL 1400 MW, σ 2500 MW, shift 0) against caiso-131 §4's committed
MINIMUM-headroom hour — LOLP is monotone decreasing in reserves, so the year's
minimum headroom gives the year's MAXIMUM adder: `$0.017 / $0.006 / $0.003` per
MWh (2023/24/25).** Matrix cell `ordc_scarcity_overlay` = `K`; "inert on C3a and
on C3c; cite the bound, never the absence".

**This session cites that bound and does not re-derive it.** Consequence,
registered in advance: the adder is **12× to 150× smaller** than caiso-249's
median STORAGE-cell wedge (+0.21 / +0.44 $/MWh), so it cannot be the carrier and
the committed price is the LP dual for every purpose here. **The overlay is
excluded from this session's candidate list by citation, not by measurement.**

### §0.3 — What is already adjudicated and is NOT re-opened

* **caiso-168 §8 item 2** — *"do not re-measure whether a storage charge column
  sets the belly dual"*. It is measured, on the same reduced-cost argument, for
  the **belly-surplus** mask (Pacific `[09,16)`, measured CA day-ahead hub
  ≤ $20). This session does **not** re-measure it. It measures ONE new thing
  about it: **how much of the caiso-249 `STORAGE` cell lies inside that mask**,
  i.e. how much of the ranked-first object is already-adjudicated ground whose
  instrument channel is armed (`caiso_storage_shape_anchor`) or walled (the
  pumped-storage limb, caiso-141/145). That is a *reach* question about a new
  cell, not a re-litigation of caiso-168's verdict, and caiso-168's verdict is
  carried verbatim for whatever overlap is found.
* **caiso-168 §8 items 1, 3, 4** — no new charge-side cap/floor/adder/hurdle is
  proposed here; no PS envelope is approximated; caiso-121's +1967/+2049/+2244
  is not re-quoted.
* **caiso-169** — `storage_daily_cycling` is refused ex ante; not re-opened.
* **caiso-248 §8 / caiso-249 §7 entire**, and every earlier DO-NOT-REDO.

### §0.4 — Admissibility and the direction hazard

Nothing is armed, so **no direction is claimed and there is no promotion basis
to exclude C3a from.** The lane has run **five consecutive favourable
directions** (caiso-246 §5.2); a sixth would be the next. This session cannot
produce one — it registers no arm — and if its result points at a mechanism, the
successor session must declare the sixth-favourable-direction hazard and exclude
C3a's verdict from its promotion basis before it builds anything.

**G-CTRL: not applicable.** No arm, no delta, no solve, so neither form 2 nor
form 4 is engaged. (Form 4 is VOID at HEAD in any case — solve-path files have
changed since `900402b`.)

---

## §1 — THE ESTIMATOR, NAMED, WITH ITS FALSIFIERS

`scripts/probes/_caiso250_lambda_carrier_anatomy.py`, zero LP. It **extends**
the committed instruments rather than rewriting them: `C247.rebuild_full`
(fleet, splatting `derived_run_year_inputs` per caiso-248), `C249.own_zone_matches`
/ `C249.delivery_ratio`, `C244.reconstruct`/`sidecars`, and
`caiso168_storage_bid_phase0`'s `_hub` / `_envelope` / `_monthly_power_cap` /
`_model_hour` with its module `BUNDLE` re-pointed at the current keeper. The
caiso-249 labelling is REPRODUCED (not re-derived) and gated against the
committed `_caiso249_ownzone_attribution.json`.

**Stage 1 — the interior-column census.** In `STORAGE`-labelled zone-hours,
which candidate family CAN carry rc = 0, from committed sidecars + the rebuild:

* `HYDRO_INTERIOR` — ISO hydro dispatch (`class_hourly` `hydro`) strictly
  between `Σ min_gen(hydro)·avail>0` and `Σ pmax·avail`;
* `BATT_CHG` / `BATT_DIS` — li_ion strictly between 0 and the armed shape-anchor
  bound `env_p95[hod] × cap[m]`, `cap[m]` recovered by caiso-168's inversion;
* `PS_CHG` / `PS_DIS` — pumped storage against its nameplate / per-plant caps;
* `NONE` — no candidate interior.

**Stage 2 — the dual signature (G-FLAT).** A budget/SOC dual is CONSTANT over
the hours it governs: hydro's `w_{g,m}` is constant over a MONTH, storage's
`ν_s` over an SOC-interior episode. So `λ_z` must take **exactly repeated
values** within a (zone, month) wherever such a column is the setter. Measured
as the load-weighted share of the cell sitting on λ values recurring ≥ 5 and
≥ 10 times within their own (zone, month), at 1e-6 relative rounding, in
`STORAGE` cells against `DOM_GAS` cells and against all hours.

**Stage 3 — the caiso-168 overlap** (weight and gap share inside
belly-surplus), carried, not re-adjudicated.

**Stage 4 — the wedge, re-read.** caiso-249's headline characterisation
("the nearest available own-zone thermal offer sits ABOVE λ … λ sits JUST UNDER
the thermal stack") is MINE and may be an artifact of LP optimality: every
available unit at its lower bound has `mc ≥ λ` at ANY optimum, so a positive
nearest-offer wedge is mechanical. Stage 4 measures the distance to the nearest
offer **strictly below** λ alongside the one above. If the two are of the same
order, the wedge measures **stack density**, not a carrier, and the caiso-249
sentence must be qualified.

**Stage 5 — the hydro water-value candidate.** Within (zone, month), the λ
spread (IQR) in `STORAGE ∧ HYDRO_INTERIOR` hours, and the implied
`w = λ − mc_hydro` band.

### §1.1 — Gates, registered

| gate | passes iff |
|---|---|
| **G-REPRO** | the reproduced caiso-249 regime gap shares match the committed `_caiso249_ownzone_attribution.json` to ≤ 0.001 in all three years |
| **G-FLEET′** | the caiso-248 phantom check, **RE-KEYED on the solver's authoritative `_INJECTED_MUSTRUN_CLASSES` tuple** rather than the shape heuristic (caiso-249 §6 item 3, registered here IN ADVANCE as the queue asks). Passes iff no rebuilt family's fuel is in that tuple and no sidecar klass lacks its LP twin, in all three years |
| **G-CONSERVE** | cells sum to `gap_hourly`, and `gap_hourly` = caiso-248's 1.3071 / 3.7812 / 3.1507 to 5e-4 |
| **G-BENCH** | recomputed `rt_lw` matches the committed `bench/CAISO/<y>.json.gz` to 0.01 |
| **G-CAP** | the recovered monthly battery cap staircase matches `load_eia860_storage`'s monthly battery fleet to ≤ 1 % in all 36 months, and December meets the next January across independent solves (caiso-168's own validation, re-run on THIS keeper) |
| **G-HOLDOUT** | every year read ∈ {2023, 2024, 2025}, fail-closed |

A failed gate is **reported as failed**. caiso-249 did not re-run its own failed
G-FLEET to a pass and that discipline holds here.

---

## §2 — PREDICTIONS, WRITTEN TO BE UNCOMFORTABLE

Three consecutive sessions have each falsified 5 of 10 and one withdrew its own
headline. These are registered wide and against interest.

| # | prediction | why it is uncomfortable |
|---|---|---|
| **P-1** | G-REPRO passes: reproduced regime gap shares within 0.001 of the committed caiso-249 JSON in all three years | if it fails, this session cannot speak about the cell at all |
| **P-2** | **G-FLEET′ passes in ALL THREE years**, including 2023 — i.e. caiso-249's 2023 failure really was the documented `oil` false positive and nothing else | if 2023 still fails on the authoritative tuple, caiso-248's diagnosis of its own gate was wrong |
| **P-3** | at least one STORAGE column (batt or PS, charge or discharge) is interior in **≥ 70 %** of the `STORAGE`-cell load-weight | the label is named STORAGE; < 70 % means the name is largely coincidental |
| **P-4** | hydro is interior in **≥ 60 %** of the `STORAGE`-cell load-weight | if hydro is rarely interior, the invisible-water-value reading in §0.1 is dead |
| **P-5** | **BOTH** hydro and a storage column are interior in **≥ 40 %** of the cell, so the census alone CANNOT name a winner and the session must report a JOINT cell | predicts my own instrument's failure to separate; registered so a joint result cannot be spun as an identification |
| **P-6** | G-FLAT: **≥ 25 %** of `STORAGE`-cell load-weight sits on λ values recurring **≥ 5×** exactly within their own (zone, month), against **< 10 %** in `DOM_GAS` zone-hours | floating-point duals rarely repeat exactly; this is the prediction most likely to fail outright |
| **P-7** | in `STORAGE ∧ HYDRO_INTERIOR` hours the within-(zone, month) λ IQR is **≤ $3.00** | a water value is one number per unit-month; a wide IQR refutes hydro as the dominant setter |
| **P-8** | **≥ 35 %** of the 2025 `STORAGE`-cell GAP contribution falls inside caiso-168's belly-surplus mask — the ranked-first object is substantially **already-adjudicated ground** whose channel is armed or walled | this is the prediction that would make the whole ranked-first item much less valuable than the handoff assumes, and it is registered as expected |
| **P-9** | the median distance from λ to the nearest available own-zone offer **below** is within **3×** of the distance to the nearest offer **above**, in `STORAGE` zone-hours | if it holds, caiso-249's published "λ sits JUST UNDER the thermal stack" is a statement about stack density and MY OWN characterisation must be qualified in this session's finding |
| **P-10** | **no single named carrier** (hydro-only, storage-only, both, neither) exceeds **60 %** of the cell's gap contribution | predicts that the ranked-first object does not resolve to one answer |

---

## §3 — STOP RULE

1. **If P-5 holds** (a large joint hydro∧storage cell), the session **STOPS** at
   "the carrier is jointly identified and cannot be separated from committed
   artifacts", files the missing artifact (a **per-zone** storage sidecar and a
   per-zone hydro dispatch sidecar; both are ISO-aggregate today) as the
   successor, and **does not reach for a third labelling rule** — the caiso-249
   §4.4 discipline.
2. **No mechanism is proposed from a falsified prediction.** If P-3/P-4/P-6 fail,
   the result is the negative, reported at full size.
3. **No gate is re-run to a pass**, and no gate is redefined after seeing its
   result.
4. **Nothing is armed in this session under any outcome.** A carrier, if found,
   is handed forward as a named object with its admissibility question stated,
   not as a lever.
5. **caiso-168's belly verdict is carried, never re-derived**, for whatever
   overlap Stage 3 finds.

---

## §4 — DELIVERABLES

This PRECOMMIT (pushed first); `scripts/probes/_caiso250_lambda_carrier_anatomy.py`
+ `results/calibration/_caiso250_lambda_carrier_anatomy.json`;
`FINDING-caiso250-lambda-carrier-2026-09-05.md`; the `docs/calibration-log/caiso.md`
entry; an **evidence-only** append on the CAISO matrix shard (no cell verdict
moves — no mechanism is tested). **No run is registered** (none is produced) and
the keeper is unchanged.
