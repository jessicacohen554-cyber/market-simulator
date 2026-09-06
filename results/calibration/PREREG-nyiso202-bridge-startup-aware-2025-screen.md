# PREREG nyiso-202 — `nyiso_gas_bridge_startup_aware` **ALONE**, screened on **2025**, under nyiso-201's CORRECTED gates with S-1 re-pointed to this arm's own arithmetic

**Session:** nyiso-202 (`claude/nyiso-202-backcast-calibration-3xdzby`), 2026-09-06.
**Keeper:** `2026-09-06-nyiso-196-extract-basis` (CALIBRATED, grade 7 of 8, fails 0, C3c the lone
ledgered caveat; unchanged by nyiso-197 … nyiso-201).
**Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §3, re-validated empirically
at THIS HEAD, **before** this document was pushed).
**SOLVES AT TIME OF PUSH: ZERO.** This document is pushed before the arm is solved.
**Owner ruling carried forward** (2026-09-06, recorded in PREREG-nyiso200 before its first solve,
verbatim): *"Is this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."* — permissive ("may"), not automatic;
§6 states how it is applied and names the class that moves away **before** the span is solved.

---

## §0 — Phase 0 (zero LP). §0.1 is inherited and NOT re-derived; §0.4–§0.7 are stated here before the solve.

**0.1 Inherited, not re-measured** (rule 29's DO-NOT-REDO discipline). Established in
`docs/FINDING-nyiso200-bridge-run-screen-2026-09-06.md`,
`docs/FINDING-nyiso201-threeway-2025-screen-2026-09-06.md` and their machine records
(`_nyiso200_bridge_phase0.json`, `_nyiso200_screen_gates_{a1,a3}_2023.json`,
`_nyiso201_screen_gates_a3_2025.json`):

* the nyiso-199 7314 / 50978 stop was a one-year `ct_only` union artifact, since repaired
  scorer-side (`legitimacy_diagnostics.ct_only_guard_years` unions over the training span);
* the bridge's P0-pattern dependence is real and is the **detector's**, not the band's;
* the measured-conduct eligibility gate is **REFUSED** under rule 13 (nyiso-144 7314 ruling) and is
  not proposed here;
* **A1 on 2023 is already spent (nyiso-200) and is NOT re-solved or re-scored.** Its numbers stand:
  census 1,173 of 1,576 CC runs, 122 of 228 state-cohort runs, 351 of 422 steam runs dropped;
  bridge forced volume **1.0034 → 0.3439 TWh**; **zero C1 flips**; C8 clean; C3a **+4.6 % → +5.7 %**
  (both PASS); C3b 0.119 unchanged; `CC_REGULAR` +0.83 → **+0.37 TWh**;
* **the nyiso-200 A1 stop is RETIRED and is not re-litigated.** It fired on a D-4 **failure-row
  COUNT**, which nyiso-201 §7(4) established is not a forcing measure where two mechanisms floor one
  plant and compose by maximum. Under gate (a) as corrected, A1-2023's own reading — 8906 total
  forcing **0.2501 → 0.2282 TWh, a FALL** — **passes**.

**0.2 The arm's own 2025 reachability bound — the S-1 bound, meter-free and residual-free**
(`_nyiso200_bridge_phase0.json`, `keeper_bridge_footprint.2025`). The run screen can only *remove*
bridge anchors, so the keeper's own bridge volume is the whole of what this arm can move:

| class | forced TWh | share of class | **bound** |
|---|---|---|---|
| `CC_REGULAR` | 0.4080 | 1.21 % | |
| `ST_GAS` | 0.1621 | 1.34 % | |
| **total** | | | **0.5701 TWh** |

**0.3 There is no CT bound in this arm, and that is why S-1 must be re-pointed** (§5). nyiso-201's
S-1 reads *"`CT_PEAKER` must RISE, inside the CT band's newly-in-the-money bound (2.1417 TWh)"* —
that is `nyiso_ct_peaker_bands_measured`'s arithmetic, and this arm does not contain that field.
Applying it here would gate this arm on a mechanism it does not arm. **The re-point is a narrowing,
not a loosening:** S-1 becomes *"the bridge's D-2 forced volume must NOT RISE, and its fall must sit
inside §0.2's 0.5701 TWh"* — nyiso-200's own A1 gate (`S1_direction_bound`), reused verbatim.

**0.4 The keeper's 2025 D-4 dark-meter baseline, gate (a)'s own function** (inherited from
PREREG-nyiso201 §0.4, which verified the function reproduces nyiso-200 §5.1's published 2023
number, 0.2515 TWh, exactly):

| year | dark plants (keeper) | **keeper dark total** |
|---|---|---|
| 2025 | **8006 0.0010 TWh** (17 h, median 0.0 MW, zero-share 0.588) | **0.0010 TWh** |

**Astoria 8906 is NOT dark in 2025** — its keeper bridge row reads median **80.976 MW**, zero-share
0.4475, verdict `pass` (`_nyiso200_bridge_phase0.json`, 2025 `unit_conduct_rows`) — so the 2023
attribution migration that stopped nyiso-200's A1 **cannot recur in this screen year in that form**.

**0.5 Declared BEFORE the solve so it cannot be read as a discovered escape: the 8906 composition is
REPORTED, not gated.** nyiso-201 §5.4 measured that on 2025, under the three-way arm, the run screen
removes 8906's bridge row entirely (686 → 0 binding hours) while the reliability floor beneath it
grows (3,512 → 4,834 h, 0.2520 → 0.3061 TWh), so the plant's **total** forced energy RISES
0.2725 → 0.3061 TWh. A1 alone contains the same run screen, so the same composition is expected
here. It does **not** enter gate (a), because gate (a)'s subject is forcing at plants the meter says
are **dark** and 8906 is not dark in 2025 (§0.4). That is the gate as nyiso-201 corrected it and this
session does not widen it mid-lane. **The 8906 keeper-vs-screen composition will be reported at full
magnitude in the FINDING whatever it is**, from the two bundles' D-4 unit-conduct rows.

**0.6 How 2025 is SCORED, stated before the solve because it decides which gates have teeth**
(PREREG-nyiso201 §0.5, re-declared here as the handoff requires):

* **C1 is SKIPPED in every class cell in 2025** — preliminary EIA-923 vintage, incomplete plant data
  (`CC_REGULAR` 11/20 plants missing, `CC_CHP` 12/17, `CT_PEAKER` 17/20, `ST_GAS` 3/10, `ST_CHP` 2/6).
* **C2 gas is ALSO SKIPPED in 2025** (`-1.0%`); C2 coal is skipped as immaterial in every year.
* Therefore **no volume criterion is gateable in 2025**, and gate (d) is **vacuous on volume** there.
  The class deltas are the arm's structural evidence, reported at full magnitude, and no gate fires
  on them.
* **What binds in 2025 is C3a and C3b**, plus the protective C6/C8:

  | criterion | keeper 2025 | band | room |
  |---|---|---|---|
  | **C3a** mean LMP | **61.84 vs 66.43 = −6.9 %** | ±10 % | 3.1 pp **down**, 16.9 pp **up** |
  | C3b price shape | NRMSE **0.154** | ≤0.20 | 0.046 |
  | C3c price tail | 4 h vs 42 h | — | ledgered caveat, non-downgrading (rubric v3.3/v3.6) |

  **The asymmetry is the point and it is stated ex ante, not as a prediction of success.** This arm
  is the only one of the three with no price-lowering signature — on 2023 it read C3a +4.6 → +5.7 %,
  i.e. it RAISES price — and the keeper's 2025 exposure is on the **downward** side. That is *why*
  this arm is the live candidate, and it is **not** a gate: rule 1 `[R-STRUCT]` forbids judging the
  arm by whether the residual moved, in either direction. §5(c) is a do-no-harm flip test and
  nothing more.

**0.7 Why the screen year is 2025, and why that is not residual-driven year selection.** Rule 29
names the screen year by the mechanism's own measured footprint. The footprint-largest year is
**2023** (bridge bound 1.0034 TWh, 1.8× either other year) and **nyiso-200 already spent it on this
exact arm**; its verdict stands and is not re-read. 2025 is the *other* year nyiso-200 §4
pre-registered before any solve, it is the year nyiso-201 §7(2) handed forward for this arm
specifically, and it is the harder of the two: least C3a room, no C1 evidence. This session inherits
that pre-registration rather than choosing a year. **2023's A1 screen is not re-run.**

## §1 — The arm: exactly ONE registered, default-off field

```
scripts/replay_keeper.py results/calibration/nyiso196_extract_basis --years 2025 \
  --out-dir results/calibration/nyiso202_screen_a1_2025 \
  --set nyiso_gas_bridge_startup_aware=true \
  --note "nyiso-202 rule-29 screen: nyiso_gas_bridge_startup_aware ALONE on 2025"
```

**G-DOF +0**: no free parameter is selected anywhere. The run screen's bar is the bridge's own
registered startup constant ($50/MW CC, $35/MW ST — `_ra_bridge_unit_params`, the constant the
economic leg already prices), not a value chosen here.

**Neither partner is armed.** `nyiso_ct_peaker_bands_measured` and `cc_duct_peaking_row_scoped` both
sit at cell **R**; their joint re-test with this arm is now **spent on both pre-registered screen
years** (2023 nyiso-200, 2025 nyiso-201 → C3a −11.7 %, out of band) and is REFUTED. Re-arming either
alone is refused without an owner ruling.

**Not done and not proposed:** no new `offer_curve_by_group` band multiplier, no adder/offset/
haircut/proxy, no per-plant list, no cross-ISO change, no out-of-training year, no control solve, no
re-derived measured parameter.

## §2 — Pre-solve F-gates (zero LP). ALL passed before this document was pushed.

* **F-1 THIS SESSION CHANGES NO SOLVE-PATH CODE AT ALL.** The per-unit / per-plant run census that
  makes gate (b)'s identity leg falsifiable landed at HEAD in nyiso-201 and is untouched here
  (`src/market_sim/pipeline/commitment.py`, the `run screen, leg …` and `run screen per-plant
  census: …` lines). The only file this session adds to the solve tree is a probe
  (`scripts/probes/nyiso202_screen_gates.py`), which reads bundles and never runs.
* **F-2 THE GATE SCRIPT IS nyiso-201's, REUSED AS IS, WITH EXACTLY ONE BLOCK CHANGED.**
  `scripts/probes/nyiso202_screen_gates.py` is a copy of `nyiso201_screen_gates.py`; `diff` over the
  code body shows **only** the S-block (§0.3, §5) plus the session/output labels. Gate (a), gate (b),
  the load-bearing companions and G-ENGAGE are byte-identical, so the corrected constructions are
  the ones that run. `ruff check` and `ruff format --check` both clean.
* **F-3 PLUMBING.** `--set nyiso_gas_bridge_startup_aware=true` reaches the registered
  `ScenarioConfig` field (`config/scenarios.py:7079`), which the bridge consumes at
  `pipeline/commitment.py:914`. **The fail-loud signal is the census log line**: a screen log with no
  `run screen, leg …` line did not arm the leg, and gate **G-ENGAGE** STOPs on its absence.
* **F-4 PRE-EXISTING TEST FAILURES, declared so they are not read as this session's.** At clean HEAD
  `tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py::test_default_cache_key_unmoved` and
  four `tests/scoring/test_ff_readiness_battery.py` tests already fail. They are untouched by this
  arm and unrelated to it.

## §3 — G-DRIFT (rule 29(b)): the keeper's committed bundle is the control, re-validated at THIS HEAD

Validated **empirically**, not by reading hunks, exactly as the handoff directs. The committed
keeper-sha probe record `_nyiso198_rebuild_checks_2024.json` (the keeper recipe's per-plant /
per-band LP `pmax`, **42 leaves**) re-run at this HEAD reproduces **0 of 42 differing leaves,
max |Δ| 0.0**, including the record's own `VERDICT` field — the regenerated file is **byte-identical
to the committed one** (`git status` clean after the re-run). The fleet's capacity basis at HEAD is
the keeper's. **Form 4 is valid: no control solve is spent.**

## §4 — The screen. ONE year, ONE LP. It may KILL the arm; it may never promote it; no gate reads the target residual.

Screen year **2025** (§0.7). One LP at a time. The bundle is a rule-29 throwaway probe: never
registered, never a keeper, never quoted as a keeper number, and **deleted before merge** (29(c)).
Every number it produces lands in `_nyiso202_screen_gates_a1_2025.json` and in this session's
FINDING; git history is the record for the bytes.

## §5 — Gates, as written. S-1 is re-pointed to this arm; NOTHING ELSE is changed and nothing is loosened.

**S-1 DIRECTION AND BOUND — RE-POINTED (meter-free).** The bridge's D-2 forced volume must **NOT
RISE**, and its fall must sit inside the keeper's own 2025 bridge volume, **≤ 0.5701 TWh** (§0.2).
A rise, or a fall exceeding the bound, ⇒ **STOP**. *(This replaces nyiso-201's `CT_PEAKER`-rises
gate, which has no subject in this arm — §0.3.)*

**S-2 CENSUS IDENTITY.** The census's own per-leg and per-plant rows are recorded and the screen's
bridge-floored plants listed. **Reported, not gated**: the committed keeper bundle is slim (no
`floors/` sidecar), so a keeper-vs-screen per-plant floor differencing is unavailable; the
falsifiable per-plant leg is carried by gate (b) via the F-1 census. STOP only in the degenerate
case (floors moved while the census dropped zero runs).

**S-3 CONFINEMENT.** No non-gas, non-import class may move by more than the lane's own registered
tolerance, **0.05 TWh** (`nyiso200_screen_gates.NON_GAS_TOL_TWH`). Otherwise ⇒ **STOP**.

**(a) C8 / D-4 COMPANION — forced energy at DARK-METER plants, like-for-like. NEVER a failure-row
COUNT.** *(nyiso-200 FINDING §7(a), as nyiso-201 implemented it — unchanged.)* Compute, per side,
the total D-4 unit-conduct `floored_twh` over **every mechanism** at plants whose measured median
over their own binding hours is 0.0 MW. Keeper 2025 = **0.0010 TWh** (plant 8006). **STOP** if the
screen's total rises by **> 0.05 TWh**, or if any single plant's rises by **> 0.05 TWh**, or if
**D-2** adds a failure. The 0.05 TWh tolerance is the lane's own registered confinement tolerance,
declared before this solve and not chosen against a result; its effect in both directions is stated
in PREREG-nyiso201 §5(a) and is unchanged. The D-4 failure ROWS are recorded on both sides and
reported at full magnitude — **reported, not gated**.

**(b) NAMED PLANTS 7314 / 50978 — anchored on a DROPPED run, or a new D-4 conviction. NEVER "zero
floor".** *(nyiso-200 FINDING §7(b), as nyiso-201 implemented it — unchanged.)* **STOP** if either
plant carries bridge floor while its run census reads **zero kept runs**; **STOP** on a **new D-4
conviction** at either plant at the span guard. Stated honestly ex ante: both are `ct_only` reporters
the span guard restores, so this leg is **expected to be vacuous**; the fleet-wide teeth are gate (a).
Bridge floor hours and GWh at both plants are **REPORTED at full magnitude whatever they are** — a
floor on a run that repaid its start is the mechanism working, not a stop.

**(c) C3a / C3b DO-NO-HARM — a PASS → FAIL flip is a STOP, full stop.** Keeper 2025 C3a −6.9 %
against ±10 %; C3b 0.154 against ≤0.20. This is a flip test, **not** a residual test: an arm that
moves C3a toward zero is not thereby a better arm, and one that moves it away while staying in band
is not thereby stopped (§0.6).

**(d) NO LOAD-BEARING FLIP.** No C1 cell, no C2 family, no C3a, no C3b may flip PASS → FAIL.
**Declared ex ante (§0.6): in 2025 every C1 cell and the C2 gas family are SKIPPED, so this gate is
vacuous on volume in this year.** It is retained because it is the gate the span will be judged on,
and the class deltas are reported at full magnitude regardless.

**G-ENGAGE.** The census log line must be present. Its absence means the leg did not arm ⇒ **STOP**.

**WHAT IS NOT A GATE:** "did `CT_PEAKER` / `ST_GAS` / `CC_REGULAR` / the price residual improve".
S-1 is a bound from the arm's own arithmetic, S-3 is conservation, (a)/(b) are the defect's own
identity, (c)/(d) are do-no-harm. Rule 1 `[R-STRUCT]`: the arm is never judged by whether a residual
moved, **in either direction**. A screen that kills the arm is reported as this session's result and
the remaining years are never spent.

## §6 — If it clears: the span, and the promotion question put at full magnitude BEFORE the span is solved

The span, `--year 2023 2024 2025` in **ONE** invocation and **ONE** bundle (rule 16), registered in
this session (rule 15) with a computed attestation — **G-DELTA exactly the one field
`nyiso_gas_bridge_startup_aware`, G-DOF +0**, G-CONTROL the keeper's committed bundle, G-INPUTS
pinning the `phys_*` values and the startup table, G-ENGAGE the census logged in every year — and the
NYISO matrix shard re-stamped (rule 26(b)).

**Promotion is a SEPARATE question, and the class that moves AWAY is named here, before the span, so
that no post-hoc reading can present it as a discovered detail.** From A1-2023's own committed
numbers (`_nyiso200_screen_gates_a1_2023.json`; actual → keeper → arm, TWh):

| class | actual 2023 | keeper | arm | keeper err | arm err | |
|---|---|---|---|---|---|---|
| `CC_REGULAR` | 33.012 | 33.840 | 33.378 | +0.828 | **+0.366** | toward |
| `CT_PEAKER` | 2.114 | 0.421 | 0.440 | −1.693 | −1.674 | toward (trivially) |
| **`CC_CHP`** | 14.802 | 15.751 | 15.981 | +0.949 | **+1.179** | **AWAY — the largest** |
| **`ST_GAS`** | 8.141 | 9.952 | 10.061 | +1.811 | **+1.920** | **AWAY** |
| `ST_CHP` | 1.169 | 1.340 | 1.382 | +0.171 | +0.213 | away (trivially) |

**`CC_CHP` is the class that moves away** (+0.230 TWh of movement, the largest single move in the
table), with **`ST_GAS`** second (+0.109). All five cells were PASS on both sides in 2023; the arm's
2023 structural gain is that it removes two-thirds of a bridge whose own census says 1,173 of 1,576
CC runs could never have repaid a start, and its price effect is +1.1 pp of C3a.

Applied as nyiso-198 §9.4 / nyiso-199 §8.4 / nyiso-201 §4 applied it — **the structural half first,
then the gates at full magnitude**: a determination that regresses on a load-bearing family with the
structure intact is a candidate the owner's formula admits; one that **collapses**, or that a
protective gate refuses on a defect the arm itself creates, is not. **And the hard boundary
nyiso-201 established stands: a span carrying a load-bearing FAIL (C1, C2, C3a or C3b) reads
`NOT-YET` — the C3c standing rule needs a LONE C3c and the v3.0 fail-closed guard refuses
`model-class` on the load-bearing tier — so promoting such a span would DECERTIFY NYISO. The owner's
formula admits gates regressing; it does not reach a decertification.** The recommendation is
written in the FINDING before the disposition is chosen, and the owner's formula decides.

## §7 — Governance

* Rule 29 `[R-SCREEN]`: phase 0 (§0, zero LP) → F-gates (§2, zero LP) → the ONE named screen year
  (§4) → the span only if it clears (§6). Screen bundle **deleted before merge** (29(c)).
* Rule 29(b): no control solve; G-DRIFT §3, empirical at this HEAD.
* Rule 1 `[R-STRUCT]`: no gate reads the target residual, in either direction; §0.6 says so of the
  price direction explicitly.
* Rule 13 `[R-MEASURED]`: no measured outcome is fed back; the refused measured-conduct eligibility
  gate is not built (nyiso-144 7314 ruling).
* Rules 21 / 23 / 24: **zero free parameters, no DOF entry**, no derive re-run, no off-registry
  channel. The one declared threshold (gate (a)'s / S-3's 0.05 TWh) is a *screen-gate* materiality
  bound in a diagnostic probe — it touches no solve and is not a model parameter.
* Rule 25 `[R-ISO-SCOPE]`: NYISO-only; CAISO's own `startup_aware` leg and cell untouched.
* Rule 22 `[R-HOLDOUT]`: 2023–2025 only. No marker requested; `complete` remains WITHDRAWN.
* Rule 26 `[R-MECH-MATRIX]`: NYISO's `gas_commitment_bridge` cell is re-stamped in THIS session,
  whatever the verdict.
* Rule 15 `[R-DASHBOARD]`: a span run, if one is earned, is registered in this session.
* Rule 27 `[R-PUSH]`: no existing ≥300-line source file is rewritten; the one new probe is pushed as
  its on-disk bytes.

---

*(nyiso-202, 2026-09-06. Pushed before the arm was solved. Zero solves at time of push.)*
