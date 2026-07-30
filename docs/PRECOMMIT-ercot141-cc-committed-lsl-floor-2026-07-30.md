# PRE-COMMIT — ERCOT-141: the CC committed-block commitment STATE (LSL floor beyond bridged gap hours)

**Date** 2026-07-30 · **ISO** ERCOT · **Lane** ercot141-cc-committed-lsl-floor ·
**Phase** mechanism + full-span arm ·
**Keeper under test** `2026-07-30-ercot140-coal-peak-offer`
(bundle `results/calibration/ercot140_coal_peak_arm`) ·
**Chartered by** `docs/PRECOMMIT-ercot139-cc-committed-offer-2026-07-30.md` §4.1
(the named successor: "the successor is then the **commitment STATE** (the
bridge's floor coverage outside gap hours), **NOT** another price lever") ·
**Arm** `ercot_gas_bridge_online_hours` (new gate, default off, requires the
bridge) · **Precommit pushed BEFORE any solve** (rule 15/26b discipline).

This document is fixed before the LP runs. Its predictions and decision rule
are the falsifier; the run is scored against what is written here.

---

## 0. The mechanism question — DECIDED with measurement, before code

ERCOT-139 put the CC_REGULAR `_committed` tranche on its measured $10.354 SCED
TPO level and **the trough flooded**: hours <$15 went 206→400, 741→1147,
194→290 and hours <$10 went 66→139, 158→318, 159→241, while C3a fell
−35.2/−14.5/−12.1 → −36.8/−16.7/−14.6 %. The level is measured and is keeper;
the defect is therefore not the price but **what the LP is allowed to do with a
row carrying that price**.

**The diagnosis was already fixed by ERCOT-64, and this lane's job was to
confirm its arithmetic still holds and then widen the window.** Both done
before writing any code:

1. **The block is a FREE LP variable outside bridged gap hours.** The bridge
   (`ercot_gas_commitment_bridge`) floors the committed band **only inside idle
   gaps between two P0-detected runs**. Inside a *run* there is no floor, so
   whenever the plant's own output sits below the committed tranche's capacity
   the band is partly loaded — i.e. **marginal** — and sets the clearing price
   at its own bid. Cheapening that bid (ERCOT-139) therefore prices the trough.
2. **The real market's inflexibility is carried by the STATE, not the price.**
   ERCOT-64 built the price-side twin (`ercot_offer_surface_lowcurve_floorscoped`
   — the measured LSL bid applied exactly on the bridge's floored hours) and
   measured it **PROVABLY INERT**: byte-identical to the keeper, price max
   |Δ| = 0.0, because in that window the tranche is **already exactly pinned**
   (`min_gen = pmax × availability`, max `P − floor` = 0.0 across all 37,788
   floored gen-hours). A pinned variable's objective coefficient cannot move the
   LP or its duals. **The window where the band plays its LSL role is precisely
   the window where its bid cannot price** — so the fix is the floor's
   **COVERAGE**, never a price on the floored rows.
3. **The pinning arithmetic re-measured ex ante for this leg** (no solve;
   `bins_to_fleet` on the 2024 ERCOT fleet). Floor target is
   `min(0.574 × plant_pmax, tranche_pmax)`; the gas-CC `_committed` share is
   **p50 0.250, max 0.550, cap-weighted 0.319, and below 0.574 on 41 of 41
   non-CHP gas-CC plants**. So the target **clips to the tranche bound on every
   plant** and the band is exactly pinned wherever this leg binds — the ERCOT-64
   property, now extended to the run hours. Reproduce:
   `scratchpad/probe_shares.py` (committed shares + `_ra_bridge_unit_params`
   acceptance).
4. **Scope needs no class tuple (rule 18 [R-PHYSICS]).** The detector's
   `_ra_bridge_unit_params` accepts **only** the base committed tranche
   (measured: 40 accepted) and rejects every incremental `_econ`/`_peak` tranche
   (startup 0, measured: 41/41 rejected each). The leg inherits that eligibility
   unchanged — merchant `gas_cc`, non-CHP, base band only.

**Decision: extend the WINDOW of the existing mechanism, change nothing else.**

## 1. The arm — ONE change, one bundle, one mechanism

`ercot_gas_bridge_online_hours` (new `ScenarioConfig` gate, default off,
ERCOT-gated, **requires** `ercot_gas_commitment_bridge` and fails loud without
it): the bridge's min-load floor covers **every hour the P0 pattern has the
plant ONLINE**, not only the idle gaps between runs.

* **Same detector** — `model/commitment.py::caiso_ra_mustoffer_min_gen`, the
  shared ISO-neutral body, via the single shared
  `pipeline/commitment.py::_ercot_gas_bridge_floor` (so both the P1 fleet hook
  and the bid hook and the `runner.py` forecast path see one floor — the
  ERCOT-64 charter wiring trap #2 cannot recur).
* **Same measured level** — `ercot_gas_bridge_min_load_frac` = 0.574, the
  committed-CC LSL/HSL capacity-weighted p50 (60-Day DAM disclosure Gen
  Resource data, ERCOT-62 derive). **This arm adds ZERO new scalars** and
  re-derives nothing (rules 13/21/23 [R-FROZEN-DERIVE]).
* **Same D-2 id** — `MECH_GAS_COMMITMENT_BRIDGE`. A wider **window** on one
  mechanism, so it **EXTENDS rather than stacks** (rule 19 [R-ONE-MECH]),
  exactly as the `min_run` (nyiso-87) and `startup_trajectory` (caiso-96) legs
  extend the same detector.
* **Composes by maximum**, never by addition; it never lowers a floor another
  leg wrote, and the bridged-gap floors are unchanged.

**Rule 19 enumeration of what else floors CC_REGULAR** — taken from the
keeper's own committed `legitimacy_diagnostics.json`, not from memory:
`gas_commitment_bridge` (1.38/1.07/1.51 % of class energy) and
`reliability_floor` (0.79/0.07/0.05 %), composing by maximum. Class forced
share today: **2.17 / 1.14 / 1.56 %** against the 30 % merchant cap.
`ercot_commitment_posture` is default-off and is not a floor by construction
(it forces no exogenous energy). Nothing is stacked on an unexplained residual.

**Rule 12 [R-FLOOR-WINDOW] declaration** (also written into
`scripts/legitimacy_diagnostics.py`, whose prior text declared the floor
gap-only and is amended in this PR):

* **(a) DRIVER** — minimum-stable-load inflexibility of a *synchronized*
  thermal unit: a CC that is online cannot operate below its LSL, so its LSL
  block is must-take. Level = the measured 0.574 LSL/HSL p50.
* **(b) WINDOW** — every hour the model's own P0 pattern has the plant online.
  **ALL 24 hours by driver, and it binds nowhere off-window BY CONSTRUCTION
  rather than by measurement**: the leg only floors hours the P0 pattern
  already has the plant running, and `min_gen` is clipped to
  `pmax × availability`, so an offline or outaged plant carries a zero floor.
  **It cannot force a start.** (Same rationale shape as
  `MECH_COAL_MIN_CONFIG` — a standing physical property, not an event. This is
  the opposite of the rule-12 failure mode: no clock-hour boxcar is asserted,
  so there is no hour in which the class's own driver evidence says it is
  offline while the floor binds.)
* **(c) FORWARD STORY** — regenerates in any forecast year from the model's own
  P0 run pattern plus the frozen measured constant, exactly as the gap legs do.
  No measured generation enters (rules 13/14 [R-MEASURED]).

**Bounded above by measurement, stated as the honesty argument:** because the
committed share (p50 0.250) is *below* the measured LSL fraction (0.574), the
floor **never holds more than the unit's real minimum stable load**. It is
conservative by construction, not a tuning surface.

## 2. What must happen for the mechanism to be real (live verification FIRST)

Before any gate is read, the run must show the leg actually fired, and fired
with the pinning property the whole story rests on. The bridge's log line is
instrumented for this (`[+online-hours leg]`, floored unit-hours, floor TWh,
and the segment-length buckets relabelled to "committed blocks"). Required:

1. floored unit-hours and floor TWh **materially above** the keeper's, and
2. the floored segments **fuse** — the length distribution moves out of the
   ≤24 h gap buckets toward whole committed blocks, and
3. the floored rows are **pinned** (`max(P − floor) ≈ 0` on floored gen-hours).

If (1)–(3) do not hold the arm is **not a test of this hypothesis** and is
reported as a wiring failure, not as evidence about the trough.

## 3. Pre-registered predictions (the falsifiers)

1. **C3a rises (trough lifts) in all three years.** The pinned block cannot set
   the margin, so the next-dearer rung (the `_econ` tranche) becomes marginal in
   the part-load hours ERCOT-139 flooded. Direction is the prediction; magnitude
   is not pre-committed beyond guard 2's ceiling.
2. **Trough counts fall toward actual.** Hours <$15 and <$10 move DOWN from the
   keeper's, i.e. back toward the pre-ercot139 levels and beyond.
3. **C3c is ≈unchanged.** The leg touches no offer and adds no scarcity
   capability; a pinned band is deep inframarginal in every scarcity hour. This
   is guard 4's structural premise and is a genuine test of it.
4. **CC_REGULAR volume RISES and coal FALLS further.** Forced min-load is
   must-take energy, so it displaces marginal supply — the same direction
   ERCOT-139 moved (CC +5.2/+5.1/+4.5 TWh, coal −3.8/−3.5/−3.0), and the same
   direction the ERCOT-138 ranking defect wants. This is what puts guard 3
   (C1/C2) genuinely at risk.

## 4. MANDATORY PRE-REGISTERED GUARDS — fixed now

### Guard 1 — C8 forced-energy budget (rule 20 [R-FORCED-BUDGET])

CC_REGULAR is a **material** merchant class, so the cap is **30 %** of class
energy at binding non-exempt floors. Today: 2.17/1.14/1.56 %.

**The risk is real and is quantified ex ante, not hand-waved.** Absolute
ceiling if every `_committed` tranche were pinned in every hour of the year:
committed capacity 10.52 GW × 8760 h = 92.19 TWh = **63.2/63.6/63.7 %** of
CC_REGULAR energy — well over the cap. The realised number will be far lower
because D-2 aggregates **per plant** and counts forced energy only in
plant-hours where *total plant output sits at the plant floor* (a plant online
above its committed block is not at floor and contributes zero), and the class
runs at only ~0.50 of capacity on average. But it cannot be pinned without the
solve, so both outcomes are pre-registered:

* **Under 30 % ⇒ C8 PASS**, reported plainly.
* **Over 30 % ⇒ NOT an automatic fail** — rule 20's escalation to a conditional
  pass on **provenance + shape**: (a) every binding non-exempt mechanism must
  clear **D-4 off-window binding**, and (b) the class's **D-1** diurnal profile
  must clear `profile_r`/`cv_ratio`. The `D4_WINDOWS` entry for the extended
  mechanism **is written in this same PR** (amending the prior gap-only text),
  and the leg binds nowhere off-window by construction, so the escalation
  reduces to the D-1 shape test. **A grounded pass is a clean PASS surfaced as
  a report note, never a caveat; a D-1 miss FAILs as a forcing-shape
  mismatch.** No parameter is re-tuned to land under the cap (rule 13).

### Guard 2 — zero-spurious + C3a no-overshoot (the ercot89/91 gate)

Scored with `scripts/probes/ercot140_guard_probe.py --arm <new bundle>`:

* **Zero spurious scarcity**: no new model >$200 hour where RT actual ≤$200.
* **C3a no-overshoot**: C3a must **not cross +0 %** in any year. This arm
  pushes C3a UP, so this is its natural failure mode: overshooting is
  over-correction and the arm is rejected on it.

### Guard 3 — C1/C2 held

Forcing min-gen ON adds must-take energy (prediction 4). **If CC_REGULAR or
coal C1 cells flip FAIL, the arm is an ORDINARY REJECTION** — declared now.
C1 today is 16/16 free 12/12 PASS and C2 PASS; both must survive.

### Guard 4 — C3c no-drain vs 47/6/0

The ERCOT-118/119 drain channel was cheap-CC-in-merit. **This arm PINS the
cheap block**, so a C3c drain falsifies the §4.1 story outright. Concretely: if
the model's >$200 count falls materially below the keeper's 47/6/0 (RT actual
181/53/31), the arm is an **ORDINARY REJECTION** — declared now, before the
solve.

## 5. The decision rule — fixed now

1. Live verification §2 fails ⇒ **wiring failure**, reported as such; no gate
   conclusions drawn.
2. Any of guards 2/3/4 breached ⇒ **ORDINARY REJECTION**, registered as a
   rejected probe with its matrix cell stamped; not promoted.
3. Guards 2/3/4 intact **and** C3a improves in all three years ⇒ **KEEPER
   CANDIDATE**, surfaced to the owner (promotion is the owner's call, not this
   session's).
4. Guards intact but C3a does **not** improve ⇒ the committed band's *state* is
   not what carries the trough residual; registered as a rejected probe, and
   the finding retires the ERCOT-139 §4.1 hypothesis and hands the trough back
   to the D-2/G1 enumeration. **This closes the last live lever on C3a**, which
   is stated here so the negative result is a real deliverable, not a
   disappointment.
5. A result outside all four is reported as it falls. **Nothing is re-tuned to
   land inside one; no parameter in this arm is swept** (there is no new
   parameter to sweep — the level is the frozen measured 0.574).

## 6. Governance

* **Holdouts (rule 22 [R-HOLDOUT])** — 2023/2024/2025 only, full span in ONE
  bundle (rule 16 [R-ALLYEARS]). No 2022, 2019, ≤2021 or H1-2026 solve, score
  or intake.
* **ERCOT-scoped (rule 25 [R-ISO-SCOPE])** — the flag gates on
  `iso == "ERCOT"`; the CAISO / NYISO / legacy-P2 detector call sites keep the
  `False` default and are byte-identical (verified by test).
* **Registry (rule 24 [R-REGISTRY])** — the gate is a `ScenarioConfig` field,
  recorded in `run_config.json`; registered in `_CACHE_KEY_OPTIONAL_FIELDS` so
  the default cache key is byte-stable while an armed run gets a distinct key
  (verified: default `2c8098e8e1684c7d` unmoved, armed `d1b1651372aba2e8`).
* **Matrix (rule 26 [R-MECH-MATRIX])** — the field is registered on the
  existing `gas_commitment_bridge` row in the same PR (duty c), correctly so
  under rule 19: it is a wider window on that mechanism, not a new one. The
  cell verdict is stamped in this same session once the run is scored (duty b).
* **CLOSED, not reopened** — `ercot_offer_surface_lowcurve_floorscoped`
  (provably inert for this exact purpose), the CC committed offer LEVEL
  (ercot139, measured, keeper), the coal offer curve end-to-end
  (ercot137/138/140), the reserve-side scarcity family (ercot107/108), gas econ
  rebasis (ercot118/119). P2 is ARCHIVED and is not used.

## 7. Honest limits, stated before it runs

1. **The 0.574 identification is per-train, and the floor is applied per
   plant.** The 60-Day-DAM LSL/HSL pairs are per-train (the caiso-135 finding
   that the same 0.57 value is a per-TURBINE turndown). Applied to a whole
   plant this would be too high — but it never binds at that level here,
   because the target clips to the committed tranche's own capacity (p50 0.250)
   on 41/41 plants. The clip is what makes the per-plant application admissible,
   and it is why the leg is conservative rather than aggressive. Any future
   change that raised the committed share above 0.574 would re-expose this and
   must revisit the basis.
2. **The window is the MODEL's online pattern, not the measured one.** That is
   deliberate (it is what makes the leg forward-native and rule-13-clean), but
   it means the leg inherits any error in the model's own commitment pattern: if
   P0 has a plant online when reality has it off, the leg floors a wrong hour.
   The D-1 diurnal gate is the check on that, and guard 1's escalation path rests
   on it.
3. **This lifts the trough by making a DEARER unit marginal, which is a real
   mechanism but not the only possible one.** If C3a improves, that is evidence
   the committed band's freedom was mispricing the trough — it is *not* evidence
   that the remaining C3a residual is all of the same kind. ERCOT-138 §5.6's
   opposite-sign p90 finding (the model's coal curve runs $9.6–15.5 UNDER
   measured at p90) still stands and still belongs to the near-tail/C3c lane.
   Reading a tail movement here as evidence about the crossing band, or vice
   versa, is a category error and is refused in advance.
4. **C6 stays UNATTESTED.** It is blocked on 8 residual-identified DOF entries
   and will not be attested to buy a determination while C3a/C3b fail as model
   misses.

## 8. Open owner rulings surfaced (NOT decided here)

1. **Carried from ERCOT-137/138/139, still open:** delete outright vs leave
   inert the retired `coal_tranche_1_fuel_passthrough` pricing path and the
   legacy non-CAMPD `split_coal_tranches` `_t1/_t2/_t3` path (rule 26
   [R-DELETE]).
2. **Carried from ERCOT-138 §7.2, still open:** `ercot_offer_hrmult_ep_rebasis`
   and `_bands` are solve-affecting `ScenarioConfig` fields with **no
   mechanism-matrix row** — a rule-26(c) gap predating five lanes. The CI guard
   passes because it only checks fields new against base. Recorded, not fixed.
3. **NEW — a defect on `main`, in NYISO's lane, found by this session's
   preconditions:** `nyiso_import_sil_retire` (PR #3136) is **not registered in
   `_CACHE_KEY_OPTIONAL_FIELDS`**, so the default `ScenarioConfig` cache key
   moved `603c2498bf71d21d → 2c8098e8e1684c7d`. This **orphans every on-disk
   cache** and fails **5 pinned tests** on a clean checkout of `main`
   (`test_persisted_identity` ×2, `test_cc_committed_offer_margin`,
   `test_ramp_envelope_basis`, `test_forecast_xyear_warmstart_flag`). The
   one-line remedy is registering that field in NYISO's lane;
   `scripts/check_cache_key_registration.py` explicitly warns that re-pinning
   the test literal instead is the WRONG fix. **Not touched here (rule 25).**
