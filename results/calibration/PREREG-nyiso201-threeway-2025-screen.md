# PREREG nyiso-201 — the THREE-WAY arm (`nyiso_gas_bridge_startup_aware` + `nyiso_ct_peaker_bands_measured` + `cc_duct_peaking_row_scoped`) screened on **2025**, under the two gate constructions nyiso-200's own FINDING §7 handed forward CORRECTED

**Session:** nyiso-201 (`claude/nyiso-201-backcast-calibration-dqn95r`), 2026-09-06.
**Keeper:** `2026-09-06-nyiso-196-extract-basis` (CALIBRATED, grade 7 of 8, fails 0, C3c the lone
ledgered caveat; unchanged by nyiso-197 … -200).
**Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §3, re-validated
empirically at THIS HEAD).
**SOLVES AT TIME OF PUSH: ZERO.** This document is pushed before the arm is solved.
**Owner ruling carried forward** (2026-09-06, recorded in PREREG-nyiso200 before its first solve,
verbatim): *"Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."* — permissive ("may"), not automatic;
§6 states how it is applied.

---

## §0 — Phase 0 (zero LP). The nyiso-200 records ARE this session's phase 0; §0.4–§0.6 are new and measured here.

**0.1 Inherited, not re-derived** (rule 29's DO-NOT-REDO discipline). The following are established
in `docs/FINDING-nyiso200-bridge-run-screen-2026-09-06.md` and its machine records
(`_nyiso200_bridge_phase0.json`, `_nyiso200_screen_gates_{a1,a3}_2023.json`) and are **not
re-measured**: the nyiso-199 7314/50978 stop was a one-year `ct_only` union artifact, since
repaired scorer-side (`legitimacy_diagnostics.ct_only_guard_years` unions over the training span);
the bridge's P0-pattern dependence is real and is the detector's; the run screen drops **1,173 of
1,576 CC runs and 351 of 422 steam runs** on the keeper's own 2023 P0 pattern; the measured-conduct
eligibility gate is REFUSED under rule 13 (nyiso-144 7314 ruling) and is not proposed here.

**0.2 The keeper's own 2025 bridge footprint** — the repair can only REMOVE floor, so this is its
pre-solve reachability bound, meter-free and residual-free
(`_nyiso200_bridge_phase0.json`, `keeper_bridge_footprint.2025`):

| class | forced TWh | share of class | **bound** |
|---|---|---|---|
| `CC_REGULAR` | 0.4080 | 1.21 % | |
| `ST_GAS` | 0.1621 | 1.34 % | |
| **total** | | | **0.5701 TWh** |

**0.3 The CT arm's own 2025 bound** (`_nyiso199_ct_band_basis_phase0.json`): newly in-the-money
**2.1417 TWh** (mean 244.5 MW). This is S-1's upper bound and it is the CT arm's own arithmetic,
not a residual.

**0.4 NEW — the keeper's 2025 D-4 dark-meter baseline, computed with gate (a)'s OWN function.**
A plant is *dark* when its measured median output over the hours its floor actually binds is
0.0 MW — the D-4 rider's own definition. Summing `floored_twh` over EVERY mechanism at those
plants gives the like-for-like measure nyiso-200 §5.1 used. The function reproduces that section's
published 2023 number exactly, which is the check that the construction is §5.1's and not a new one:

| year | dark plants (keeper) | **keeper dark total** | nyiso-200 §5.1 published |
|---|---|---|---|
| 2023 | 2480 0.0014 · **8906 0.2501** | **0.2515 TWh** | 0.2515 → 0.2296 ✓ |
| **2025** | **8006 0.0010** (17 h, median 0.0 MW, zero-share 0.588) | **0.0010 TWh** | — |

Two facts this fixes ex ante: **Astoria 8906 is NOT dark in 2025** (its reliability row reads median
80.976 MW / zero-share 0.143, its bridge row 80.976 / 0.448 — both pass), so the 2023 attribution
migration that stopped A1 cannot recur in this screen year in the same form; and **neither 7314 nor
50978 carries any keeper D-4 row in any year**, so the keeper's per-plant bridge baseline at both is
0, as nyiso-200 §0.3 states.

**0.5 NEW — how 2025 is SCORED, stated before the solve because it changes which gates have teeth.**
The keeper's own committed determination, re-run at this HEAD:

* **C1 is SKIPPED in every class cell in 2025** — preliminary EIA-923 vintage, incomplete plant data
  (`CC_REGULAR` 11/20 plants missing, `CC_CHP` 12/17, `CT_PEAKER` 17/20, `ST_GAS` 3/10,
  `ST_CHP` 2/6, `COAL_BIT` immaterial). *"not gated — C2 family grid reconcile covers this class."*
* **C2 gas is ALSO SKIPPED in 2025** (`-1.0%`); C2 coal is skipped as immaterial in every year.
* Therefore **no volume criterion is gateable in 2025.** The class deltas are the arm's structural
  evidence and are reported at full magnitude, but a "no C1 flip" gate is **vacuous** there and this
  document does not pretend otherwise.
* **What binds in 2025 is C3a and C3b**, plus the protective C6/C8:

  | criterion | keeper 2025 | band | room |
  |---|---|---|---|
  | **C3a** mean LMP | **61.84 vs 66.43 = −6.9 %** | ±10 % | **3.1 pp down** |
  | C3b price shape | NRMSE **0.154** | ≤0.20 | 0.046 |
  | C3c price tail | 4 h vs 42 h | — | ledgered caveat, non-downgrading (rubric v3.3/v3.6) |

**0.6 NEW — why the screen year is 2025, and why that is not residual-driven year selection.**
Rule 29 names the screen year by the mechanism's own measured footprint. The footprint-largest year
is **2023** (bridge bound 1.0034 TWh, 1.8× either other year) and **nyiso-200 already spent it** —
its numbers stand and are not re-solved. 2025 is the *other* year nyiso-200 §4 named **before any
solve** ("the exposed year"), and it is the harder of the two: it is the year with the least C3a
room and the year whose C1 evidence is unavailable. This session inherits that pre-registration
rather than choosing a year, and it chooses the more adverse one, which is the opposite of the
hazard rule 29 guards against. **2023's screen is not re-run and its verdict is not re-read.**

## §1 — The arm

Exactly three fields, all registered, all default-off, over the keeper recipe:

```
scripts/replay_keeper.py results/calibration/nyiso196_extract_basis --years 2025 \
  --out-dir results/calibration/nyiso201_screen_a3_2025 \
  --set nyiso_gas_bridge_startup_aware=true \
  --set nyiso_ct_peaker_bands_measured=true \
  --set cc_duct_peaking_row_scoped=true \
  --note "nyiso-201 rule-29 screen: three-way arm on 2025 under corrected gates"
```

Neither partner field is armed ALONE anywhere in this session — both sit at cell **R** with the
identical re-test condition ("re-arm only paired, with the bridge repair"), and re-arming either
alone is refused without an owner ruling. **G-DOF +0**: no free parameter is selected; the run
screen's bar is the bridge's own registered startup constant, and both partner fields carry their
own measured bases (nyiso-198 EIA-860 duct sheet, nyiso-199 CT band basis).

**Not done and not proposed:** no new `offer_curve_by_group` band multiplier, no adder/offset/
haircut, no per-plant list, no cross-ISO change, no out-of-training year, no control solve.

## §2 — Pre-solve gates (zero LP). ALL passed before this document was pushed.

* **F-1 THE ONE CODE CHANGE IS DIAGNOSTICS-ONLY.** To make gate (b)'s identity leg *falsifiable*
  rather than asserted from the code path, the detector now records a **per-unit** run census
  (`detected` / `kept` / `dropped` / `dropped_hours`) and the NYISO consumer rolls it up **per
  plant** into one log line. The floor arithmetic never reads the census — `runs` is rebound to
  `kept_runs` before every leg, exactly as before. Guarded by two new tests:
  `test_per_unit_census_makes_the_identity_falsifiable` (a dropped-run unit reads `kept: 0` and
  floors nothing; a kept-run unit reads `kept: 1` and floors) and `test_census_is_diagnostics_only`
  (a supplied stats dict changes no floor, byte-identical). **52 pass** in
  `tests/iso/nyiso/test_nyiso_gas_commitment_bridge.py`; **76 pass** in
  `tests/unit/model/test_commitment.py`.
* **F-2 THE SCREEN'S ARITHMETIC IS UNCHANGED** from nyiso-200: a 2 h P0 fragment at $10/MW margin
  is not extended; the same fragment at $60/MW still is.
* **F-3 PLUMBING.** `--set` reaches all three fields (the bridge fields are consumed after
  `prb_overrides` applies). **The fail-loud signal is the census log line**: a screen log with no
  `"run screen, leg …"` line did not arm the leg, and gate **G-ENGAGE** STOPs on its absence.
* **F-4 PRE-EXISTING TEST FAILURES, declared so they are not read as this session's.** At clean
  HEAD, before any edit of this session, `tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py
  ::test_default_cache_key_unmoved` and four `tests/scoring/test_ff_readiness_battery.py` tests
  already fail (verified by `git stash`). They are untouched by this arm and unrelated to it.

## §3 — G-DRIFT (rule 29(b)): the keeper's committed bundle is the control, re-validated at THIS HEAD

Validated **empirically**, not by reading hunks, exactly as the handoff directs: the committed
keeper-sha probe record `_nyiso198_rebuild_checks_2024.json` (the keeper recipe's per-plant /
per-band LP `pmax`, 42 leaves) re-run at this HEAD reproduces **0 of 42 differing leaves, max
|Δ| 0.0** — including the record's own `VERDICT` field, which is unchanged. The fleet's capacity
basis at HEAD is the keeper's. **Form 4 is valid: no control solve is spent.**

## §4 — The screen. ONE year, ONE LP. It may KILL the arm; it may never promote it; no gate reads the target residual.

Screen year **2025** (§0.6). One LP at a time. The bundle is a rule-29 throwaway probe: never
registered, never a keeper, never quoted as a keeper number, and **deleted before merge** (29(c)).
Every number it produces lands in `_nyiso201_screen_gates_a3_2025.json` and in this session's
FINDING; git history is the record for the bytes.

## §5 — Gates, as written, with the two nyiso-200 corrections and NOTHING loosened

**S-1 DIRECTION AND BOUND (meter-free).** `CT_PEAKER` must RISE and stay inside the CT arm's own
pre-solve bound, **≤ 2.1417 TWh** (§0.3). Outside ⇒ STOP.

**S-2 CONFINEMENT.** |gas-family total Δ| ≤ |the CT gain|; the energy comes from inside the gas
family, not from a non-gas source. Otherwise ⇒ STOP.

**(a) C8 / D-4 COMPANION — forced energy at DARK-METER plants, like-for-like. NEVER a failure-row
COUNT.** *(nyiso-200 FINDING §7(a).)* The retired construction counted this year's D-4 failure
rows, and nyiso-200 §5.1 showed that count RISES whenever the higher of two composed floors is
removed at a plant the lower one also floors — at Astoria 8906 the bridge floor fell 1,400 → 34 h,
the reliability floor beneath absorbed the dark hours, the row count went 1 → 2, and the plant's own
forced energy **FELL** 0.2501 → 0.2282 TWh. The count was measuring attribution, not forcing. The
gate is now §5.1's own table:

* Compute, per side, the total D-4 unit-conduct `floored_twh` over **every mechanism** at plants
  whose measured median over their own binding hours is 0.0 MW. Keeper 2025 = **0.0010 TWh**
  (plant 8006). **STOP** if the screen's total rises by **> 0.05 TWh**, or if any single plant's
  rises by **> 0.05 TWh**.
* **The 0.05 TWh tolerance is declared here, before the solve, and its source is named:** it is the
  lane's own registered confinement tolerance (`nyiso200_screen_gates.NON_GAS_TOL_TWH`), reused on
  both legs — not a number invented for this screen and not one chosen against a result. Its effect
  is stated in both directions so it cannot be read as a convenience: it lets a sub-materiality
  reshuffle of a 17-hour row pass (reported at full magnitude), and it fires HARD if a plant with
  real forced energy becomes dark-median under the arm — which is the defect the gate is for.
* **D-2** must add no failure (unchanged; D-2 is the production C8 path).
* The D-4 failure ROWS are still recorded on both sides and reported at full magnitude — **reported,
  not gated.**

**(b) NAMED PLANTS 7314 / 50978 — anchored on a DROPPED run, or a new D-4 conviction. NEVER "zero
floor".** *(nyiso-200 FINDING §7(b).)* The retired construction demanded ZERO bridge floor at both
plants and fired on 542 h / 153 h that were **anchored on P0 runs which REPAID their start** — the
mechanism working, not the defect. The defect nyiso-199 found is a floor anchored on a run the
unit's own economics say it would never have started. So:

* **STOP** if either plant carries bridge floor while its run census reads **zero kept runs** — the
  screen's by-construction claim, made falsifiable at plant grain by the F-1 census rather than
  asserted from the code path.
* **STOP** on a **new D-4 conviction** at either plant at the span guard. Stated honestly ex ante:
  both plants are `ct_only` reporters that the span guard restores, so the rider skips them and this
  leg is **expected to be vacuous**; the fleet-wide teeth are gate (a), not this leg.
* Bridge floor hours and GWh at both plants are **REPORTED at full magnitude whatever they are**,
  as nyiso-200 §7(b) requires. A floor on a run that repaid its start is not a stop.

**(c) C3a-2025 IS THE NAMED RISK AND A FAIL IS A STOP, FULL STOP.** Keeper **−6.9 %** against
±10 %: **3.1 pp of downward room**. The three fields push the same way on price and the sign of
their sum is not knowable from this session's records — the CT arm alone read **−9.1 %** on 2025
(nyiso-199), the duct arm alone **−10.3 %** on the span (nyiso-198), and the run screen alone
**RAISES** price (+1.1 pp C3a in 2023, the CAISO de-anchoring signature). **C3b** likewise: keeper
0.154 against ≤0.20, a PASS → FAIL flip is a STOP.

**(d) NO LOAD-BEARING FLIP.** No C1 cell, no C2 family, no C3a, no C3b may flip PASS → FAIL —
`CC_REGULAR` **included**, not exempted. **Declared ex ante (§0.5): in 2025 every C1 cell and the
C2 gas family are SKIPPED, so this gate is vacuous on volume in this year.** It is retained because
it is the gate the span will be judged on, and the class deltas are reported at full magnitude
regardless.

**G-ENGAGE.** The census log line must be present. Its absence means the leg did not arm ⇒ STOP.

**WHAT IS NOT A GATE:** "did `CT_PEAKER` / `ST_GAS` / `CC_REGULAR` / the price residual improve".
S-1 is a bound from the arm's own arithmetic, S-2 is conservation, (a)/(b) are the defect's own
identity, (c)/(d) are do-no-harm. Rule 1 `[R-STRUCT]`: the arm is never judged by whether a residual
moved, **in either direction**. A screen that kills the arm is reported as this session's result and
the remaining years are never spent.

## §6 — If it clears

The span, `--year 2023 2024 2025` in ONE invocation and ONE bundle (rule 16), registered the same
session (rule 15) with a computed attestation — **G-DELTA exactly the three fields, G-DOF +0**,
G-CONTROL the keeper's committed bundle, G-INPUTS pinning the `phys_*` values, the EIA-860 duct
sheet and the startup table, G-ENGAGE the census logged in every year — and the NYISO matrix shard
re-stamped (rule 26(b)).

**Promotion is a SEPARATE question and it is put at full magnitude, with the class that moves away
named BEFORE the span is solved.** Under the owner's standing formula (*"if structural integrity
improves but gates regress that may still be a keeper"*), applied as nyiso-198 §9.4 / nyiso-199
§8.4 applied it — the structural half first, then the gates at full magnitude:

* **The class that moves AWAY from its actual is `CC_REGULAR`**: +0.83 → **+1.43 TWh** in 2023
  (share +1.2 → +1.6 pp), still PASS. It is named here, before the span, so that no post-hoc
  reading can present it as a discovered detail.
* The classes that move toward theirs in 2023 are `ST_GAS` (+1.81 → +0.46 TWh), `CT_PEAKER`
  (−1.69 → −0.99) and price (C3a +4.6 → +0.9 %).
* A determination that regresses on a load-bearing family with the structure intact is a candidate
  the formula admits; one that collapses, or that a protective gate refuses on a defect the arm
  itself creates, is not. The recommendation is written in the FINDING before the disposition is
  chosen, and the owner's formula decides.

## §7 — Governance

* Rule 29 `[R-SCREEN]`: phase 0 (§0, zero LP) → F-gates (§2, zero LP) → the ONE named screen year
  (§4) → the span only if it clears (§6). Screen bundle deleted before merge (29(c)).
* Rule 29(b): no control solve; G-DRIFT §3, empirical at this HEAD.
* Rule 1 `[R-STRUCT]`: no gate reads the target residual, in either direction.
* Rule 13 `[R-MEASURED]`: no measured outcome is fed back; the refused measured-conduct eligibility
  gate is not built (nyiso-144 7314 ruling).
* Rules 21 / 23 / 24: **zero free parameters, no DOF entry**, no derive re-run, no off-registry
  channel. The one declared threshold (gate (a)'s 0.05 TWh) is a *screen-gate* materiality bound
  in a diagnostic probe — it touches no solve and is not a model parameter.
* Rule 25 `[R-ISO-SCOPE]`: NYISO-only; CAISO's own `startup_aware` leg and cell untouched.
* Rule 22 `[R-HOLDOUT]`: 2023–2025 only. No marker requested; `complete` remains WITHDRAWN.
* Rule 26 `[R-MECH-MATRIX]`: NYISO's shard cells (`gas_commitment_bridge` leg,
  `nyiso_ct_peaker_bands_measured`, `cc_duct_peaking_row_scoped`) are re-stamped in THIS session,
  whatever the verdict.
* Rule 15 `[R-DASHBOARD]`: a span run, if one is earned, is registered in this session.

---

*(nyiso-201, 2026-09-06. Pushed before the arm was solved. Zero solves at time of push.)*
