# FINDING — caiso-199: the merit-order panel SCOPE PIN lands the Desert Star extract — **every pre-registered gate PASSES**, the classifier's instrument stability is restored, and the pre-registered **C1 flip FIRES**: disposition **ACCEPT-WITH-FLIP, escalate to owner**

**Pre-registration:** `PRECHECK-caiso199-merit-panel-scope-2026-08-16.md`, committed
and pushed at `a4205d1` **BEFORE any derive or solve of this session ran**. Both
baseline shas were fixed in that document before the recipe was executed; neither
was edited afterwards. Gates applied as written.

**Owner ruling executed:** caiso-198 §5 **option 1** (taken at session start on the
FINDING-caiso198 escalation package) — pin the panel's identification scope
independently of the detection state list, then land the strictly-additive
candidate and A/B it.

**Registered runs:** `2026-08-16-caiso-199-g0-control` (bundle
`caiso199_g0_control`) and `2026-08-16-caiso-199-g1-meritpin` (bundle
`caiso199_g1_meritpin`). 2023–2025 only, one bundle per arm, years sequential,
arms sequential (rules 12/16). **Keeper UNCHANGED** at `2026-08-16-caiso-197-w2-r5`
— no keeper shard is edited this session (PRECHECK §6; the caiso-196/198 precedent:
the session escalates, the owner promotes).

**The extract LANDED**: `data/raw/campd-unit-outages-CAISO.csv` `5f3e35c5…` →
`da33e509…`; layup companion **byte-unchanged** at `1475a577…`. Unlike caiso-198,
where nothing landed, the committed extract sha now **supersedes**.

## 0. Direction-hazard regime (verbatim from the PRECHECK, binding — and it bound)

> The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD
> measured outage removal (a plant that previously carried no overlay gains its
> real windows), which lowers availability and raises price, while C3a 2024/2025
> already FAIL high (+12.1/+15.6 %). C3a movement is inadmissible as evidence for
> or against acceptance in EITHER direction (rules 1, 13, 14): if the gates pass
> and C3a worsens, the repair stands (caiso-183/188/196 precedent — "the accurate
> input would have stayed even had the fit worsened"); if the gates fail, no C3a
> improvement rescues it. C3a is reported for transparency only.

C3a moved exactly as predicted (**+12.1/+15.6 → +12.8/+15.7 %**) and **was not
consulted in any acceptance decision.** It is reported here and nowhere used.

## 1. Gate tally — 10 of 10 PASS

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-CTRL** | g0 within \|ΔC3a\| ≤ 0.1 pp/yr, \|ΔC3b\| ≤ 0.005/yr of the committed keeper | **BIT-ZERO**: max \|Δ\| = 0.0 over every zone-hour of `hourly/system_*.parquet` (prices included) AND every class-hour of `hourly/class_hourly_*.parquet`, all three years (`_caiso199_ctrl_tolerance.json`). Noise floor exactly 0.0 pp / 0.000, quoted before any treated delta. Seam caps 16055/16452/16148 log-verified; MIC partition materialized in-session (386 rows); `hydro_ror_split=false` disclosed; warm-start pinned off; stack = the keeper's recorded one (python 3.11.15, highspy 1.14.0, numpy 2.4.6, pandas 3.0.3). | **PASS** |
| **G-DELTA (a)** | pinned recipe, NV EXCLUDED ⇒ committed bytes | main `5f3e35c5…`, layup `1475a577…` reproduced **byte-identically**; 4,561/810 rows. **The pin is INERT when the two scopes coincide** — it changes nothing about the baseline it restores. | **PASS** |
| **G-DELTA (b)** | pinned recipe, NV INCLUDED ⇒ the caiso-198 candidate | main **`da33e509…`**, layup **`1475a577…`** reproduced **byte-identically**; 4,719/810 rows. | **PASS** |
| **G-DELTA (c)** | landed diff strictly additive | 4,561 → 4,719 rows; **all 158 added rows are facility 55077**; **zero** removals; every pre-existing row byte-identical **and in order**; header unchanged; layup companion byte-identical. Verified twice — by the probe and by an independent row-level check against the committed blob. | **PASS** |
| **G-DELTA (d)** | g0-vs-g1 `scenario_config` diff EMPTY | `{}` over the full config. | **PASS** |
| **G-ENGAGE** | loader resolves (55077, CC_REGULAR) < 1 in ≥1 solve year AND the LP differs | **NOT INERT.** Mean multiplier **0.702/0.345/0.607** (2023/24/25) with **2,789/7,197/5,468** derated hours of 8,760. LP differs in **14,966/26,930/18,697** price zone-hours of 61,320 and **4,032/9,594/4,575** class-hours; max \|Δprice\| 79.5/539.5/59.7 $/MWh. | **PASS** |
| **G-SIXISO** | no other ISO's extract, config, shard or cell written | Only CAISO's extract landed; `ISO_MERIT_PANEL_STATES` pins **CAISO alone** and every unpinned ISO resolves exactly to its detection list — asserted by test over every ISO in the registry, not by inspection. | **PASS** |
| **G-DOF** | ledger unchanged at 10/7 | 10/7 in both bundles, the caiso-197 composed ledger carried **byte-identically**. The pin adds no parameter and no fitted scalar; the landing adds DATA, not freedom. | **PASS** |
| **G-C8** | both bundles ship and score `legitimacy_diagnostics.json` | shipped and scored; C8 PASS in both. | **PASS** |
| **G-COV** (post-landing, no-LP) | re-measured on the LANDED instrument | CC_REGULAR **population 1.000000, uncovered list EMPTY**; strict CEMS **0.990880** (residual: Harbor + Agnews, the known `eia923_netzero` blind spot). Reproduces the caiso-198 candidate measurement exactly — **confirming the landed instrument IS that candidate**. CC_CHP unchanged at 0.678/0.636, stays excluded fail-closed. `wefor_residual = 0.0` **NOT recomputed** — invariant by construction (`residual_c = max(0, W_c − X_c)`, X_c can only rise). | **PASS** |

**Single-mechanism statement (PRECHECK §3, verbatim):** "The A/B delta is the
merit-panel-scope-pinned extract re-derive and the facility-55077 rows it adds; no
ScenarioConfig field differs."

### 1a. Head drift, disclosed against interest

The control's `scenario_config` differs from the **committed keeper's** at exactly
**2 of 716 keys** — `commission_year_cod_fallback` and
`ercot_reserve_supply_cap_net_credits` — both absent from the keeper's
`run_config` (which predates them) and both default-**off** in the tree, one
ERCOT-scoped by name and by rule 25. They arrived on `main` from other lanes
between the caiso-197 promotion and this session. Their inertness on CAISO is not
asserted but **measured**: G-CTRL came back bit-zero against the committed
keeper's own sidecars. G-DELTA leg (d) compares control against arm at the **same**
head and is `{}`, so the A/B itself is unaffected. **No rebase was taken between
the two arms** — `main` gained solve-path changes mid-session
(`iso_configs.py`, `scenarios.py`, `interchange/core.py`) and rebasing would have
left control and arm on different code, voiding the single-mechanism guarantee.

## 2. What the pin actually fixed

`build_merit_order_panel` is fleet-blind by design; the deriver handed it the
**detection** state list, so the two scopes were silently coupled. The measured
consequence (caiso-198): adding NV for the ONE CAISO-fleet plant that files CEMS
there put **59–64 units of 13–14 non-CAISO NV Energy facilities** into CAISO's
revealed-clearing-cost panel, lifted the RCC in **87–97 % of hours** (mean
**+3.45 $/MWh** in 2024) and reclassified **275 CA-facility windows at 15
facilities**.

Under the pin, the same recipe on the same committed detection list produces the
Desert Star rows **and nothing else**. The classifier is no longer a function of a
coverage decision — which is the whole of rule 23 `[R-FROZEN-DERIVE]`. The panel's
scope is now disclosed in the deriver's own log line (`[scope CA]`, 231–238 priced
units/yr), so a future re-derive records which scope produced it.

**The pin is a STATE-LIST pin, not a fleet filter** (PRECHECK §1a, held to): the
committed CA panel still contains non-CAISO **CA** units (LADWP, municipals),
which is the panel the caiso-192 gates adjudicated the guard on. Fleet purity would
move the committed extract and needs its own baseline; it was not taken.

**A pre-registered claim that could have failed and didn't.** The caiso-198
candidate was produced by scoping the panel's **directory**; this pin scopes its
**state list**, which *also* narrows `_delivered_coal_price_tables` from
`{CA, NV}` to `{CA}`. PRECHECK §1b pre-registered that as a provable no-op — no CA
CEMS unit is coal-fuelled in **any** year of the 2018–2026 derive span (CA fuels ∈
{natural gas, other gas, pipeline natural gas, wood}), and the gas leg keys on
`iso` rather than the state list — with an explicit STOP if it were wrong. Leg (b)
confirms it by byte identity rather than by argument. (NV *does* carry coal — North
Valmy — one of the units that drove the measured RCC rise; under the pin those
units are out of the panel entirely.)

## 3. The criteria-flip watch FIRED — §5 protocol run in full

**The flip.** C1 fuel-mix **PASS → FAIL**, the single failing row being **2023
CC_REGULAR −4.25 TWh, share −1.8 pp** against the keeper's in-band **−4.13**;
C1 **12/12 → 11/12**, free **8/8 → 7/8**. The control passes C1 identically to the
keeper, so the flip is attributable **solely to the landing**. CC_REGULAR volume
moves **−0.112 / −0.283 / −0.101 TWh** (2023/24/25); the 2023 leg is exactly the
−0.12 that carries the row across its band. This is the direction §0 predicted:
added measured removal at a CC_REGULAR plant, spending the ~0.3 TWh of headroom the
caiso-197 healing had left.

The pre-registered protocol admits **input-side re-examination ONLY**. All three
questions, answered on measurement:

1. **Mis-citation?** **No.** EIA 55077 Desert Star Energy Center is a CAISO-fleet
   plant carried as `CC_REGULAR`; CAMPD units EDE1/EDE2; `group_by_code[55077]`
   resolves through the shipped fleet path. Capacity basis is the recipe's
   documented `observed_peak` fallback (CAMPD `EDE1`/`EDE2` vs EIA-860
   `ED01`/`ED02`/`ED03` misses both id heuristics) — shipped behaviour, recorded
   ex ante in PRECHECK-caiso198 §1 and taken as-is. The derate enters as a
   **fraction** (`unit_pct_of_plant` = 50 %), so the `observed_peak` denominator
   never injects capacity.
2. **Coverage failure?** **No — the opposite.** G-COV on the landed instrument puts
   CC_REGULAR extract population at **1.000000 with an EMPTY uncovered list**: the
   FINDING-caiso193 §2 state-scope arc closes completely. The class is now fully
   observed for the first time.
3. **Classifier deviation?** **No deviation — but a real structural limit, measured
   and disclosed.** Desert Star sits in NV and the pinned panel is CA-only, so it
   is **not a member of the panel its own spans are scored against**:
   `out_of_merit_share((55077, ·))` returns `None` and `is_economic_layup` returns
   `False` in all three years (verified directly). **All 158 windows are therefore
   retained as mechanical by the fail-safe, without ever being tested against the
   merit order.** That matters because the windows do not look like classic
   mechanical outages — 16–24 per year, e.g. 2018 Jan 1–7 (6.6 d), Jan 9–23
   (14.6 d), Jan 28–Feb 6 (9.4 d) — a mid-winter cycling signature, and a mean
   availability of **0.345 in 2024** is a strong claim for a 2006-vintage CC.
   **Bound on the exposure, from caiso-198's own run Y** (panel = CA + facility
   55077, the only variant in which the guard *can* see this plant): it reclassifies
   **9 of the 158** windows to layup — **5.7 %** — leaving **149 mechanical**. So
   the fail-safe's default is what the guard itself would have concluded for ~94 %
   of these windows, and the un-adjudicated remainder is small and quantified.

**The input survives re-examination.** Disposition, verbatim as pre-registered:
**"ACCEPT-WITH-FLIP, escalate to owner"** — never a silent rejection, and never a
rescue via C3a.

### 3a. C3c is not a substantive regression

C3c reads FAIL on the arm where the keeper carries a CAVEAT, purely because a
non-keeper A/B arm has **no governance attestation**: the C3c standing rule
requires governance PASS (guard b) *and* lone-failure (guard a), and neither holds
here (C1 also fails). That is the guard operating exactly as written, not a tail
regression. On a promoted keeper with an attestation generated at promotion, C3c
would be re-measured per caiso-189 §8.3 and its classification re-decided then.

### 3b. A third option the caiso-198 package did not enumerate — for the owner

caiso-198's run Y is neither of the two options the §5 package put to the owner: a
panel scoped to **CA + the ISO's own out-of-state fleet members** (here, facility
55077 alone). It would give Desert Star membership in the panel that judges it —
closing the §3 item-3 asymmetry — **without** admitting the non-CAISO NV fleet that
caused the 275-window churn. It is a fleet-scoped panel in miniature, and it is
**out of scope here** (PRECHECK §1a excludes fleet purity): it moves the committed
extract by 9 windows and needs its own baseline proof and pre-registration. It is
recorded as a named, measured option, not taken.

## 4. The keeper decision, packaged for the owner (NOT taken in-session)

**What the arm is.** A run in which the ISO's economic-layup classifier no longer
moves when its detection coverage changes; the last unobserved CC_REGULAR plant is
covered, taking the class to 100 % population coverage; the committed extract is a
strict superset of its predecessor; and every one of the ten pre-registered gates
passes on measurement taken in the pre-registered order.

**What it costs.** One load-bearing criterion flips: C1 12/12 → 11/12 on a single
row (2023 CC_REGULAR, −4.13 → −4.25 TWh). The arm therefore carries **two**
load-bearing FAILs (C1, C3a) against the keeper's **one** (C3a). C3a itself
worsened slightly and is inadmissible in either direction.

**The rule-14 posture, which is the owner's to apply.** The landed input is the
more accurate representation — measured CEMS conduct for a plant that previously
carried no overlay at all — and rule 14 `[R-ACCURATE]` says a worse fit from a more
accurate input is a signal that something *else* is miscalibrated, not a reason to
revert to the estimate. Rule 1 `[R-STRUCT]` says a structurally-correct mechanism
is not judged by whether it improves the residual. Both point at promotion.

**The honest counterweight, stated plainly.** The C1 flip is not merely a residual
moving: it is a **load-bearing criterion crossing its band**, and the mechanism that
pushed it there is a set of windows that the guard was **structurally unable to
adjudicate** (§3 item 3). That un-adjudicated fraction is bounded at ~5.7 % by the
guard's own run-Y measurement, so it cannot account for the whole flip — but the
owner should weigh that the plant driving the flip is the one plant the classifier
cannot see.

**Recommendation.** Promote, on the rule-1/rule-14 posture: the arm is the more
structurally faithful run, the flip is disclosed and bounded, and the alternative is
to keep a keeper whose classifier is coverage-dependent and whose CC_REGULAR class
is knowingly missing a plant. If the owner promotes, the standing duties fire in the
promoting session: attestation generated AT promotion with C3c magnitudes
re-measured per caiso-189 §8.3, site-retention prune per the standing 2026-08-15
directive, keeper shard + matrix + §5.2 + status re-stamps, `audit_keepers`. If the
owner instead judges a load-bearing flip too high a price, the extract still stands
as landed (it is a correctness fix to a committed instrument, not a candidate), and
the keeper simply remains caiso-197.

**Queue posture:** with this landing the **in-model queue is EXHAUSTED**. The only
named C3a routes remain the two standing owner objects — the walled hourly PS
water-state intake (caiso-141 / ruling 4) and the 8,800 MW declared residual
(caiso-191 §4) — plus the §3b panel-membership option above. **No new lane is
improvised.** The frontier/`complete`-readiness ASSESSMENT route remains available
and its answer is unchanged: C3a genuinely fails, so a `complete` declaration is
**not** supportable on the merits (owner ruling 5 — NOT-YET is the honest fallback).

## 5. Holdout posture

**2023–2025 solves ONLY.** CAISO holds NO `complete` and NO `final` marker; the
spend freeze is ACTIVE; no out-of-training year was solved, scored or registered.
The 2018–2026 derive span is **data preparation**, which the tier gates do not
restrict (rule 22, spend-only enforcement — the caiso-196/198 precedent re-derived
the identical span).

## 6. Artifacts

Runs `2026-08-16-caiso-199-g0-control`, `2026-08-16-caiso-199-g1-meritpin` (slim
files + hourly sidecars + `legitimacy_diagnostics.json` + `free_parameters` 10/7).
Records: `_caiso199_ctrl_tolerance.json` (G-CTRL bit-zero),
`_caiso199_panel_pin_gates.json` (G-DELTA legs a–d + G-ENGAGE),
`_caiso199_gcov_landed.json` (G-COV on the landed instrument). Probes:
`scripts/probes/_caiso199_ctrl_tolerance.py`, `_caiso199_panel_pin_gates.py`,
`_caiso199_carry_dof_ledger.py`. Code: `campd.ISO_MERIT_PANEL_STATES` +
`merit_panel_states_for_iso`, the deriver wiring, and
`tests/curation/test_campd.py::TestMeritPanelStatePin` (7 tests incl. the
detection-widening invariant, the per-ISO fallback over every registered ISO, and a
wiring guard against reverting the call site). PRECHECK @ `a4205d1`.
`_caiso198_gcov_remeasure.json` was briefly overwritten by a re-run of the
caiso-198 probe and **restored byte-identical** — disclosed. Matrix duty (b):
`campd_outage_windows` CAISO cell updated, the extract sha **superseding** to
`da33e509…`. Calibration-log entry in `docs/calibration-log/caiso.md`.
