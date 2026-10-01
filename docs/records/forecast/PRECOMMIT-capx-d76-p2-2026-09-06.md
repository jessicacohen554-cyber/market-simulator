# PRE-COMMITMENT — capx D76 phase 2: the measured screen peak on the full span (PJM) and on the 2021-2023 window (CAISO / ERCOT / MISO)

**Pushed BEFORE any solve.** Lane capx D76 phase 2 (director's release, §0au.3). Branch
`claude/capx-d76-p2-full-span-4jkhit`, base `origin/main` **`e6a0402f`**.
Charter: pack §D76 + the phase-2 section + `FINDING-capx-d76-2026-09-06.md`
(§2 census, §3 screen years and the 2021-2023 window offer, §4 the seam and every consumer,
§6-§7 the PJM screen PASS, §8 routes).
Phase-1 record: the same FINDING, "PHASE 1" §5-§8, and
`PRECOMMIT-capx-d76-measured-screen-peak-2026-09-06.md`.

**NOTHING ARMS IN THIS LANE.** The precondition of the director's release binds: this section is the
release of **phase 2 and nothing past it** — no arming, no `ISOConfig` override, no default flip,
without a further release. The exit deliverable includes an **arming card drafted for the director**;
drafting a card is not serving it.

**NEISO and NYISO are DEFERRED** by the director's call and are not solved, not screened and not
scored here. NEISO has the smallest footprint (−1,462 MW at its screen year); NYISO is
requirement-moot at HEAD through the D52 gates `nyiso_requirement_forecast_peak` /
`nyiso_requirement_vintage_factors` (phase 0 §2.3), so its requirement delta is 0.0 MW in every year.

---

## 1. HEAD GUARD and G-DRIFT — the audit, recorded before the first LP

**HEAD = `e6a0402f`** (`origin/main` at session start; `git rev-parse HEAD == origin/main`).
The gate is on `main`: `capacity_screen_peak_measured_hindcast: bool = False`
(`scenarios.py:16429`), registered in `_CACHE_KEY_OPTIONAL_FIELDS` (1546),
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (2098) and `TIER_TAGS` (18637); the seam is
`runner.py:2078-2106` with the shared constructor `_hindcast_measured_demand` (473) that
`runner.py:2557` reuses for the LP's own `year_base_demand`.

**G-CTRL: form 4 is VOID and a control at HEAD is EARNED — pre-declared, not discovered.** The
charter states it and phase 0 §4.3 measured it: every committed T1-H bundle is **PRE-hunk** on
`DEMAND_GROWTH_RATES` (the SCN-LOAD refresh moved PJM's near rate 0.036 → 0.064645), so differencing
an arm against a committed bundle would attribute the demand-table refresh to this gate. **Both legs
of every A/B in this lane are solved at the same HEAD**, so the A/B itself carries zero code drift by
construction.

**G-DRIFT, `131291b5` (the phase-1 base) → `e6a0402f` (this base), hunk by hunk.** Three non-merge
commits touch the solve path:

| commit | change | classification for THIS lane |
|---|---|---|
| `f3d0396e` | capx D75-R step 2+3 — the PJM VRE ELCC delivery-year vintage axis, `pjm_vre_accreditation_vintage: bool = False` | **INERT** — gated default-OFF and absent from every phase-2 recipe (no leg passes the flag, no `ISOConfig` arms it) |
| `8ad280ed` | capx D76 phase 1 — this lane's own gate, default-OFF | **INERT in the control, and it IS the arm.** Not drift: it is the mechanism under test |
| `26474700` | capx D67-ARM — `capacity_adequacy_requirement_published_by_iso: {"PJM": True}` in `_pjm_config.default_scenario_overrides` (owner ruling Q52) | **LIVE for PJM. INERT for CAISO / ERCOT / MISO** — the dict is PJM-keyed, so no other ISO's requirement resolver moves |

`DEMAND_GROWTH_RATES` did **not** move between the two bases (verified: the only
`constants.py` hunk is a `RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO` import line), and the phase-0
census re-derives at THIS head with every peak delta reproducing digit for digit — §2 below.

**A matched cache key is NOT a G-DRIFT verdict**, and none is claimed as one: the audit above is a
code-level classification of every changed hunk, and the keys in §3 are recorded only to identify the
legs.

## 2. WHAT D67-ARM CHANGES FOR LEG 1 — pre-declared, because it is the whole reason PJM's numbers
   will not reproduce phase 1's

This is the single most important pre-declaration in this document, and it is made **before** the
first PJM solve.

Phase 1 screened PJM at base `131291b5`, where `capacity_adequacy_requirement_published_by_iso`
resolved `None` and the requirement was the peak-dependent `screen peak × FPR` reconstruction. There
the gate's dominant channel WAS the requirement: it moved **+14,603.770 MW** (2022) and
**+4,122.183 MW** (2023).

**At THIS head D67-ARM has landed and PJM's requirement is peak-INDEPENDENT in every in-table
delivery year.** Re-measured at HEAD with the shipped resolver (`p2_predeclare.py`,
`p2_predeclare.json`), on the identical seam and measured peaks:

| ISO | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| PJM peak Δ (seam − measured) MW | −22,702.1 | −13,437.4 | −3,781.5 | 0.0 | +2,459.5 |
| PJM **requirement Δ** MW | **0.0** | **0.0** | **0.0** | **0.0** | **0.0** |

**So LEG 1's remaining effect must run entirely through the OTHER consumers** — the accreditation
census (`accredited_firm_capacity_mw`, incl. the penetration-indexed ELCC and the D48 DR-as-supply
hold-last, both SUPPLY-side and therefore untouched by mooting the requirement), the retirement
reliability floor, the reserve-margin build backstop, and the CR-1 reserve position (phase 0 §4.2
consumers 1, 4, 5a, 5b, 5c, 5d). **Pre-declared consequence:** PJM's `screen_adequacy_requirement_mw`
is expected **identical** between control and arm in every year, and a non-zero move there would mean
the D67 arming is not doing what Q52's own evidence says it does — reported, not gated.

## 3. THE LEGS — fixed here, before the first LP

Every leg is `scripts/run_capacity_hindcast.py --vintage 2020 --entry-screen-diagnostics`, realized
variant, plain hindcast. `--entry-screen-diagnostics` is on **both** sides of every A/B (the harness
records it decision-neutral: "Byte-identical fleet outcome"), so it cancels; it is carried because it
is what makes the whole-ledger diff explicable on the entry side.

| leg | ISO | window | flag | cache key |
|---|---|---|---|---|
| 1-C | PJM | 2021-2025 | `--no-capacity-screen-peak-measured-hindcast` | `a9c66d8ea25acb9d` |
| 1-A | PJM | 2021-2025 | `--capacity-screen-peak-measured-hindcast` | `fd07e2dba50cd32b` |
| 2-C | CAISO | 2021-2023 | `--no-…` | `2184fc9c85fafd06` |
| 2-A | CAISO | 2021-2023 | `--…` | `8a7ef53c812be4e1` |
| 3-C | ERCOT | 2021-2023 | `--no-…` | `e465ee243716c86d` |
| 3-A | ERCOT | 2021-2023 | `--…` | `681b733594f4cd6b` |
| 4-C | MISO | 2021-2023 | `--no-…` | `ad3af46ecefd8941` |
| 4-A | MISO | 2021-2023 | `--…` | `ff8ef4fcb278a76d` |

Every control key **equals its bare recipe key** at this head, and every arm key is distinct
(`p2_predeclare.json`, `leg_keys[*].control_equals_bare == true`). Keys resolved from the shipped
resolver at HEAD, recorded here **before** the first solve; the phase-1 lane's transcription error is
the reason they are machine-emitted into a committed JSON rather than typed.

**All legs run SEQUENTIALLY, one LP at a time.** Rule 12 permits two concurrent per-plant multi-zone
invocations, and that allowance is deliberately **not taken**: the D67 lane measured two concurrent
PJM per-plant LPs at ~9 GB each OOM a 15 GB box and lose a leg to the kernel silently, and this box
is 15 GB / 4 cores. **Rebase BETWEEN legs, never during**; every rebase delta is re-audited hunk by
hunk before the next leg starts, and the audit is appended to this document.

### 3.1 The pre-declared peak and requirement moves, per ISO (`p2_predeclare.json`)

| ISO | year | seam peak MW | measured MW | Δ MW | Δ % | req Δ MW | binds |
|---|---|---:|---:|---:|---:|---:|---|
| PJM | 2021 | 126,887.926 | 149,590.0 | −22,702.074 | −15.18 % | 0.0 | · |
| PJM | 2022 | 135,090.596 | 148,528.0 | −13,437.404 | −9.05 % | 0.0 | Y |
| PJM | 2023 | 143,823.528 | 147,605.0 | −3,781.472 | −2.56 % | 0.0 | Y |
| PJM | 2024 | 153,121.0 | 153,121.0 | 0.0 | 0.00 % | 0.0 | Y |
| PJM | 2025 | 163,019.514 | 160,560.0 | +2,459.514 | +1.53 % | 0.0 | Y |
| CAISO | 2021 | 43,228.163 | 43,615.0 | −386.837 | −0.89 % | −444.863 | · |
| CAISO | 2022 | 44,629.849 | 51,104.0 | −6,474.151 | −12.67 % | −7,445.274 | Y |
| CAISO | 2023 | 46,077.0 | 44,007.0 | +2,070.0 | +4.70 % | +2,380.5 | Y |
| ERCOT | 2021 | 58,162.936 | 72,776.0 | −14,613.064 | −20.08 % | −15,658.264 | · |
| ERCOT | 2022 | 66,004.0 | 79,407.0 | −13,403.0 | −16.88 % | −14,361.615 | Y |
| ERCOT | 2023 | 74,902.157 | 84,617.0 | −9,714.843 | −11.48 % | −10,409.61 | Y |
| MISO | 2021 | 103,576.348 | 114,226.0 | −10,649.652 | −9.32 % | −10,725.845 | · |
| MISO | 2022 | 109,254.0 | 116,392.0 | −7,138.0 | −6.13 % | −7,189.02 | Y |
| MISO | 2023 | 115,242.842 | 120,781.0 | −5,538.158 | −4.59 % | −5,577.671 | Y |

Every non-PJM row reproduces phase 0 §2.1 digit for digit at this head; PJM's peak column likewise,
with its requirement column collapsed to 0.0 by D67-ARM (§2). "binds" is phase 0 §1(e): the
requirement/position block at `runner.py:2125` is guarded on `prior_results is not None`, so 2021
writes a `screen_peak_demand_mw` no screen consumed.

**The 2022 bridge year is exercised but never solved** (rule 22): it evolves the fleet against the
seam peak and writes its `screen_ledger_fields`, so the structural identity is checkable on the 2022
bridge ledger AND the 2023 solved ledger — which is exactly why the director offered the 2021-2023
window for the three non-PJM ISOs (phase 0 §3.1 items 1-2). CAISO's, ERCOT's and MISO's own largest
binding delta is 2022's, and it is inside this window.

## 4. STOP GATES — structural, and STOP gates ONLY (rule 29 `[R-SCREEN]`)

Pre-registered here so none can be written to fit a result. A STOP **may kill an arm; it may never
promote one**, it contributes to no determination, and **not one is gated on a residual**. Graded by
`docs/handoffs/d76/p2_gate.py`, whose partition (below) is fixed in this commit.

- **STOP 1 — no pre-existing cache key moves.** All six ISOs' bare T1-H and T1-X keys: explicit-OFF
  == bare, armed distinct. *(Already measured green at this head before this push, 12/12 —
  `p2_predeclare.json.stop1_pass`.)*
- **STOP 2 — the identity, to the MW.** The arm's `screen_peak_demand_mw` equals the year's
  PRE-DECLARED measured peak (§3.1) to the MW in every year of the window, and equals the ledger's
  own `peak_demand_mw` in every solved year. A miss of more than 0.001 MW kills the arm.
- **STOP 3 — every non-peak operand byte-identical.** The nested `scenario_config` in
  `run_config.json` differs in **exactly one field, this lane's own gate**, and in nothing else; the
  five top-level per-leg bookkeeping keys (`cache_key`, `run_dir`, `scenario_config`,
  `scenario_config_source`, `timestamp`) are not the pre-registered object and are named here so the
  grader cannot be accused of discovering them after the fact.

  > **PRE-REGISTERED CORRECTION, made before any phase-2 result exists.** Phase 1's text required the
  > 2021 pre-screen ledger to be *identical* and took a **LITERAL MISS** on `screen_peak_demand_mw`
  > — the D52 observability field `runner.py:2180` writes unconditionally in a year where no screen
  > consumes it. That pre-registration was over-broad, and phase 1 reported the miss rather than
  > editing it away. Phase 2 pre-registers the corrected text **here, before its own evidence**:
  > 2021 must be identical in every field EXCEPT `screen_peak_demand_mw`, and **any DECISION field
  > moving in 2021 kills the arm**. No STOP is weakened — the quantity that is invariant by
  > construction is still required identical to the digit.
- **STOP 4 — the footprint is confined to the rows the mechanism claims.** Every Class-A INVARIANT
  ledger key (§4.1) is identical in every year, and **no key moves that belongs to no declared
  class**.
- **STOP 5 — no non-target load-bearing criterion flips PASS → FAIL.** Graded from
  `scripts/score_capacity_hindcast.py` → `scripts/forecast_verdict.py --tier t1h` on both legs. The
  TARGET criterion is **FC-3** (the capacity-hindcast accuracy row the mechanism is expected to
  move); every other FC row is non-target and load-bearing. **Testable for LEG 1 only**: phase 1
  established that a truncated 2021-2023 window produces no scorer output at all, so for LEGS 2-4
  this STOP reads **UNTESTABLE at this configuration** and the lane will say so rather than claim it
  cleared.
- **STOP 6 — one measured load per armed year.** Already asserted by test at HEAD
  (`tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py`); re-run, not re-derived.

### 4.1 THE LEDGER PARTITION (D81 rec 4) — fixed here, before the solves

The whole-ledger diff assigns **every** moved key of **every** year to one of six pre-declared
classes. A key that moves and belongs to none is reported `UNCLASSIFIED` and **kills the arm under
STOP 4** — the partition cannot be widened after a result to absorb a surprise.

| class | keys | expectation |
|---|---|---|
| **A — INVARIANT** | `peak_demand_mw`, `adequacy_requirement_mw`, `iso`, `year`, `ledger_version`, `mode`, `hindcast`, `bridge` | identical in every year (pure functions of the measured load, or run identity). A move is a **KILL** |
| **B — SEAM** | `screen_peak_demand_mw` | moves by exactly the §3.1 Δ |
| **C — SCREEN** | `screen_adequacy_requirement_mw`, `screen_entering_firm_mw`, `screen_reserve_position`, `capacity_reserve_position`, `locality_capacity` | the rule-19 consumers of phase 0 §4.2; may move |
| **D — DECISION** | `retirements`, `thermal_additions`, `renewable_additions`, `storage_additions`, `ccs_retrofits`, `floor_retained`, `entry_pipeline`, `entry_decided_mw_by_tech`, `entry_screen_diagnostics`, `pipeline_events`, `announced_derates`, `confirmed_derates` | what the screens decided against that operand; may move |
| **E — FLEET** | `fleet_by_fuel_after`, `fleet_by_fuel_before`, `firm_clean_mw`, `firm_clean_accredited_mw`, `storage_firm_mw`, `storage_power_mw`, `wind_cap_mw`, `solar_cap_mw`, `renewable_credit_applied`, `reserve_margin` | consequent fleet state and its accreditation trail; may move (`fleet_by_fuel_before` only from the window's second year, since year Y+1's *before* is year Y's *after*) |
| **F — ACCOUNTING** | `rps_dual`, `solve_counts` | LP/solver accounting that follows the fleet; may move |

## 5. PRE-DECLARED EXPECTATIONS — reported, NOT gates

Stated before the solves so they can be graded either way. **Nothing here can kill or promote an
arm; only §4 can.**

1. **Direction, per ISO-year.** The control's screen peak is the **seam** peak and the arm's is the
   **measured** peak, so `arm − control = −Δ` where Δ is §3.1's `seam − measured` column. The sign
   table is therefore fixed as:

   | arm − control | ISO-years | expectation |
   |---|---|---|
   | **arm peak HIGHER** (Δ < 0) | PJM 2021 (+22,702), 2022 (+13,437), 2023 (+3,781); CAISO 2021 (+387), 2022 (+6,474); ERCOT 2021 (+14,613), 2022 (+13,403), 2023 (+9,715); MISO 2021 (+10,650), 2022 (+7,138), 2023 (+5,538) | a HIGHER bar ⇒ **fewer economic exits / a longer fleet** |
   | **arm peak LOWER** (Δ > 0) | **CAISO 2023 (−2,070)**, **PJM 2025 (−2,459.5)** | a LOWER bar ⇒ **more exits / a shorter fleet** |
   | no move | PJM 2024 (the weather year) | identical |

   The two reversal cells are the lane's own falsifiability: a mechanism that only ever lengthens the
   fleet would be indistinguishable from a one-way retention adder. The FINDING grades each cell
   HIT/MISS against this table.
2. **Magnitude, order of magnitude only.** For CAISO / ERCOT / MISO the requirement moves by §3.1's
   `req Δ` (the `peak × FPR` path). **For PJM it moves by 0.0** (§2) — the pre-solve arithmetic the
   dispatch response is checked against for direction and order of magnitude.
3. **PJM FC-3 at full magnitude, REPORTED and NEVER GATED** (charter). Phase 1 measured the `gas_st`
   survival channel at **+7,333.7 MW (2022)** and **+9,464.5 MW (2023)** against **2.702 GW** of
   actual steam exits — the control took PJM's entire `gas_st` fleet to 0.0 MW by 2023. That is
   D74's object seen from the demand side. On the full span the FC-3 rows (unit recall, retirement
   MW error, `false_retire`, plant-release precision) exist for 2023-2025 and are reported at full
   magnitude, **including where the arm is worse**. Phase 1's number was measured on the
   peak-DEPENDENT requirement path; at this head that channel is gone for PJM (§2), so the survival
   magnitude may differ substantially and the lane will report what it is rather than the phase-1
   figure.
4. **`reserve_margin`** is an EXITING-side quantity (`firm/peak − 1`, computed after evolution) and
   is Class E, REPORTED not gated — the phase-1 §4 correction, carried forward as written.
5. **What would surprise me.** Any movement in a Class-A key; any `UNCLASSIFIED` key moving; a
   non-zero PJM `screen_adequacy_requirement_mw` delta (which would contradict D67-ARM's own
   evidence); or a fleet that moves in the direction opposite to expectation 1's sign in an ISO-year
   with a large Δ. The first two are STOP 4 kills; the last two are findings, reported.

## 6. Delete before merge (rule 29(c))

All eight bundles are deleted from `results/hindcast/` before this PR merges. This PRECOMMIT, the
phase-2 FINDING and `docs/handoffs/d76/p2_gate_<iso>.json` + `p2_predeclare.json` carry **every
number the lane will ever cite**; git history is the record for the bytes. An unregistered bundle
directory reaching `main` is a parity-gate RED, and `KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route
for a screen or a control.

## 7. Registration and matrix duties

Registration of any arm row follows **D65-B-R's batch** (charter). Matrix duty (rule 28
`[R-MECH-MATRIX]`): the gate's base row and all six shard cells landed with phase 1; phase 2 updates
the **cell verdict + evidence citation in each tested ISO's own shard** — `PJM.js`, `CAISO.js`,
`ERCOT.js`, `MISO.js` — and touches **no other ISO's shard** (rule 25 `[R-ISO-SCOPE]`: each ISO gets
its own letter, derived from its own market's evidence; NEISO's and NYISO's cells stay as phase 1
left them because this lane did not test them).

## 8. Collisions

Audited in phase 0 §4.4 and re-checked at this base: PR #5091 (the wallclock P1 basis seed) landed
docs and golden manifests only, its code change is on `pipeline/solve.py`; `runner.py`'s year-loop
preamble carries no hunk from any commit in the `131291b5 → e6a0402f` delta other than this lane's
own phase-1 seam; and the D67 lane owns `gross_adequacy_requirement_mw`, which this lane does not
touch — the two compose exactly as phase 0 §2.3 predicted, and §2 above is that composition measured.

---

## ADDENDUM 1 — `main` moved while LEG 1's control was solving; the lane HOLDS every leg at `e6a0402f`

**Recorded 2026-09-06, while LEG 1-C was mid-LP and before any of LEGS 2-4 started** — i.e. before
the legs it governs, which is the point of writing it here rather than in the FINDING.

`origin/main` advanced `e6a0402f` → **`82a7742d`** (PR #5203, the miso-230 CT net-load-drag backcast
lane). §3's rule is "rebase BETWEEN legs, never during", and this addendum records the choice made
under it and the audit behind it.

**The audit, at file granularity and then at hunk granularity.** `git diff --stat e6a0402f
origin/main` touches **seven files and not one of them is on the hindcast solve path**:

| file | classification |
|---|---|
| `src/market_sim/**` | **no file changed at all** — the diff is empty over the whole package |
| `scripts/run_capacity_hindcast.py`, `scripts/lib/**` | **no file changed** — the diff is empty |
| `data/raw/reference/miso_ct_netload_drag.json` | new derived artifact; **no `src/` reader exists at this head**, so nothing in a solve can reach it |
| `scripts/data/derive_miso_ct_netload_drag.py`, `scripts/probes/_miso230_*.py` | derive/probe scripts, not imported by any solve |
| `scripts/legitimacy_diagnostics.py` | the BACKCAST D1/D2/D4 diagnostic; never on a hindcast solve path |
| `docs/handoffs/PRECOMMIT-miso230-…md`, `results/calibration/_miso230_…json` | documents and a backcast probe artifact |

**Verdict: the delta is INERT for every one of the eight legs**, MISO's included — it is a backcast
lane and it changed no model code.

**The choice.** All eight legs are held at **`e6a0402f`**, the base this PRECOMMIT's keys were
resolved at, and the rebase is taken **after the last leg**, with the then-current delta re-audited
hunk by hunk before merge. Two reasons, both structural rather than convenient: (a) the eight legs
then sit at ONE solve-code state, so no cross-ISO comparison in the FINDING can be contaminated by a
mid-lane code move, and every A/B keeps its own zero-drift-by-construction property; (b) §3's cache
keys were resolved at `e6a0402f` and pushed before the first LP — solving a later leg at a different
head would silently void them, which is exactly the failure mode the pre-registration exists to
prevent. Had the delta contained a LIVE hunk this choice would not have been available and the
affected legs would have been re-based and re-solved; it does not, and the audit above is what
establishes that rather than a "files changed, therefore void" heuristic in either direction.
