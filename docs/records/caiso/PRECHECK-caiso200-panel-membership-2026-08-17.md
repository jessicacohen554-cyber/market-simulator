# PRECHECK — caiso-200: merit-panel MEMBERSHIP for the ISO's own out-of-state fleet — pre-registered A/B, committed BEFORE any derive or solve

**Committed and pushed before any derive or LP of this session runs.** These
gates are fixed and fail-closed. This session executes the caiso-200 handoff's
delegated adjudication of the caiso-199 §4 owner package (options A/B/C): the
adjudication taken at session start is **(C) — fund the caiso-199 §3b
panel-membership option first, then re-decide the keeper with the measurement
in hand.** Grounds, recorded before any result exists:

1. The caiso-199 C1 flip is driven by the ONE plant the layup classifier is
   structurally unable to see (FINDING-caiso199 §3 item 3, disclosed). §3b is
   the named closure of exactly that asymmetry, recorded as "a named, measured
   option, not taken" — the one remaining in-model object. Adjudicating (A) or
   (B) with a one-derive-two-solve closure available would promote or decline
   on an instrument with a known, measured, closable defect.
2. Rule 1 `[R-STRUCT]`: Desert Star is a CAISO-fleet plant — its running
   capacity DOES clear CAISO's merit order, so its panel membership is real
   market structure. Admitting it (and only it) is a **NARROWING** of the
   caiso-199 §1a exclusion: the non-CAISO NV Energy fleet that caused the
   caiso-198 275-window churn stays out.
3. Rule 14 `[R-ACCURATE]`: the flip was the signal that something else is
   miscalibrated; §3 item 3 identified exactly what. Running §3b is the
   root-cause investigation, not a fit-chasing act — see §0's admissibility
   argument for why its now-favorable expected direction does not taint it.

**Head disclosure.** This session found `main` (a4ef2a9) UNSOLVABLE — a
SyntaxError in `scripts/run_calibration.py` (duplicate
`reliability_floor_plant_exclusions` in `run_year`, the 8839960/7246272
semantic merge collision via #4036: two branches repaired the same 3febd5c gap
independently and the merge stacked both). Repaired by dedup (keep the
documented 7246272 copy) at `5148f2e`, blob-verified after push (rule 27).
G-CTRL below measures the head, this repair included.

It is **NOT a new lever** (rule 28a): like the caiso-199 pin, this is a
*derive-recipe identification scope*, the same class of object as
`campd.ISO_STATES` / `ISO_MERIT_PANEL_STATES`. It adds **no ScenarioConfig
field and no matrix row**; its effect on any solve is fully mediated by the
extract artifact whose sha is provenance-tracked through G-EXTRACT. Matrix
duty (b) = the `campd_outage_windows` CAISO cell, same as caiso-198/199.

## 0. Direction-hazard regime — REVERSED SIGN, recorded ex ante

The caiso-198/199 repairs were anti-C3a-favorable (added removal ⇒ higher
prices). **This delta points the OTHER way**: it can only MOVE windows
mechanical→layup (removing measured outage removal), which raises availability
and can lower prices — i.e. the expected sign is **C3a-favorable AND
C1-2023-favorable**, toward the two failing criteria. That makes the
anti-tuning discipline stricter, not looser:

* **C3a movement is inadmissible as evidence for or against acceptance in
  EITHER direction** (rules 1, 13, 14 — standing), and because the expected
  sign is favorable, no improvement may be cited anywhere in the acceptance
  chain. Acceptance rests SOLELY on the §4 byte-identity gates and the §1
  structural-membership argument, both fixed before any solve.
* **The object's content is not chooseable.** The entire A/B delta was fixed
  ex ante by a measurement taken at caiso-198 (run Y,
  `_caiso198_extract_delta.json`) BEFORE the C1 flip existed, and it carries
  **zero free parameters**: fleet membership is a fact of the market derived
  from the fleet registry, not a fitted value. The 9-window delta is whatever
  the instrument says it is.
* The pre-registered **C1-2023 return watch** (§5) is REPORTED, never a gate.

### 0a. Factual correction of the caiso-199 §3 item-3 record, pre-registered

FINDING-caiso199 §3 item 3 (and the matrix cell, and the caiso-200 handoff)
read run Y as reclassifying "9 of the 158" Desert Star windows. **The
committed record says otherwise**: `_caiso198_extract_delta.json`
`runY_panel_ca_plus_ds` measures `added_55077: 158, removed_from_main: 9,
entered_layup: 9` against a committed baseline that contained NO facility-55077
rows — so the 9 movers are **pre-existing CA-facility windows** (the RCC dips
when the efficient CC joins the panel), and **ALL 158 Desert Star windows are
retained as mechanical by the guard that can finally see them**. The fail-safe
default was right for 100 % of the DS windows, not ~94 %. This expectation is
GATED at G-DELTA leg (c): the mover census is measured at derive time and the
FINDING corrects the caiso-199/matrix record on that measurement.

## 1. What is being changed, and why it is a rule-23 charter not a tuning act

The caiso-199 pin scoped the panel's state list to CA, restoring instrument
stability — at the cost of a disclosed structural limit: a CAISO-fleet plant
filing CEMS out-of-state is **not a member of the panel its own spans are
scored against** (`out_of_merit_share` → `None`, `is_economic_layup` → False
fail-safe for all 158 windows). This charter admits **the ISO's own
out-of-state fleet members** — and nothing else — into the panel:

* **Membership is DERIVED, not enumerated** (rule 24 `[R-REGISTRY]` spirit):
  a facility qualifies iff it appears in an out-of-panel DETECTION state's
  CAMPD files AND its plant code resolves into the ISO's own fleet registry
  (the same `group_by_code` the detection path already filters on). Today that
  set is exactly **{NV: (55077,)}** — measured before this PRECHECK was
  written — and it regenerates for a future fleet change with no table to
  maintain.
* **The CA panel composition is untouched.** This is NOT the fleet-purity
  filter caiso-199 §1a declined: non-CAISO CA units (LADWP, municipals) stay
  in the panel the caiso-192 gates adjudicated. The change only ADDS the ISO's
  own out-of-state members; it removes nothing.
* **Rule-23 citation:** the caiso-199 §3b named option + the caiso-200 handoff
  authorizing it as the one remaining in-model object. No residual is
  consulted in the construction; the recipe scope is a committed derived rule,
  not an env var or a fallback (rule 24 satisfied through the existing
  G-EXTRACT provenance channel).

## 2. The change (one code narrowing + one data landing)

1. **`src/market_sim/data/campd.py`** — new registry
   `MERIT_PANEL_FLEET_MEMBER_ISOS` (`frozenset({"CAISO"})`) + accessor
   `merit_panel_admits_fleet_members(iso)`. Documented with the §1 rationale.
2. **`scripts/data/derive_campd_unit_outages.py`** — helper
   `_merit_member_facilities(detection_states, panel_states, years,
   group_by_code)` computing the per-state member-facility map; the panel
   build passes it through; the panel log line discloses it
   (`[scope CA +members NV:55077]`).
3. **`scripts/lib/outage_detect.py`** — `build_merit_order_panel` gains an
   optional `member_facilities` mapping: member states' unit-level parquets
   are loaded FILTERED to the listed facilities, appended after the pinned
   states. Member states join the delivered-coal-table scope (matching the
   run-Y construction, where the panel state list was CA+NV; inert here — no
   coal unit can enter this panel: CA carries no CEMS coal in any derive year
   per the caiso-199 §1b measurement, and facility 55077 is gas-fuelled).
4. **`tests/curation/test_campd.py`** — CAISO is the only member-admitting
   ISO; every other registered ISO admits none (rule 25); the detection-
   widening invariant holds (a new detection state admits only fleet members).
5. **The data landing** — the committed recipe (`--iso CAISO --years
   2018 … 2026 --merit-order-guard --hour-grain`) re-derived in place on the
   committed `("CA","NV")` detection list, panel = pinned CA + derived
   members. No hand-editing, no threshold movement, no per-plant exception;
   whatever the guard emits is taken as-is.

Deliberately **NOT** in scope (single mechanism, rule 19): fleet purity of the
CA panel (§1); any change to detection thresholds, `MERIT_RCC_PCTL`,
`MERIT_OOM_FRAC`, or the detection state lists; the five other ISOs' extracts,
configs and matrix shards (byte-untouched); `thermal_tranches_CAISO.csv` and
`plant_emission_rates` (each its own cited re-derive).

## 3. A/B protocol

* **h0 CONTROL** — the caiso-197 keeper recipe re-solved at this head with
  `data/raw` at the **committed** (caiso-199-landed) extract bytes:
  `python scripts/replay_keeper.py results/calibration/caiso197_w2_r5
  --out-dir results/calibration/caiso200_h0_control --set
  hydro_ror_split=false`, capacity-deliverability partition MATERIALIZED
  first (`curate_capacity_deliverability --isos CAISO`, seam caps
  16055/16452/16148 log-verified), no hydro-plant-modes partition present,
  warm-start pinned off by the replay driver. Compared against the committed
  **`caiso199_g1_meritpin`** sidecars — the committed baseline for the landed
  extract (the caiso-197 keeper's own sidecars predate the landing and are
  not the right identity target).
* **h1 ARM** — the IDENTICAL invocation into `caiso200_h1_memberpanel`, run
  after the §4 baseline proof lands the extract. The member-scope code is in
  the tree for BOTH arms (derive-time only, cannot reach an LP), so **the
  sole A/B delta is the extract bytes**.
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms
  sequential (rule 12) — the control solves with `data/raw` clean; the derive
  runs only after the control completes.
* Both arms registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`.
* **Single-mechanism statement, required verbatim in the FINDING:** "The A/B
  delta is the fleet-member panel-scope extract re-derive and the 9
  CA-facility windows it reclassifies mechanical→layup; no ScenarioConfig
  field differs."

## 4. Numeric gates — fixed now, each with its anchor

| gate | bar | anchor |
|---|---|---|
| **G-CTRL** | h0 reproduces `caiso199_g1_meritpin` within the RATIFIED tolerance: per year \|ΔC3a\| ≤ 0.1 pp and \|ΔC3b\| ≤ 0.005. Noise floor quoted at full precision BEFORE any treated delta; bit-zero is the lane norm; primary instrument = max \|Δ\| over every zone-hour of `hourly/system_*.parquet` and every class-hour of `hourly/class_hourly_*.parquet`. Outside tolerance ⇒ stop-the-line finding about the head, NO ARM SOLVES. | Integration protocol §3; bit-zero observed caiso-184/188/196/197/198/199. |
| **G-MEMBER** | The derived member map resolves to EXACTLY `{"NV": (55077,)}` — asserted at derive time and by test. Any other membership ⇒ **STOP**. | The §1 ex-ante measurement (15 NV facilities seen 2018–2026; 55077 the sole CAISO-fleet member). |
| **G-DELTA** | **Four legs, all pre-pinned to shas fixed in this document.** (a) **baseline inertness**: with the member scope DISABLED (in-process patch, scratch `--out`), the recipe reproduces the COMMITTED pair byte-identically — main **`da33e509465911341ba0867aefe02214f2e8ccb666ef86747e0e7ad8b47c86bb`**, layup **`1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43`**. This is the narrowing's own baseline byte-identity proof: the implementation is inert when unarmed. (b) **the landing, member scope ARMED**: reproduces the caiso-198 run-Y product byte-identically — main **`cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5`** (4,710 rows), layup **`4ccae12ebcfada3d6b716d02f25d81faaa4cfd49fedb22685449581cc6d9ed37`** (819 rows). Cross-construction check: run Y scoped the panel DIRECTORY at the caiso-198 head; this scopes MEMBERSHIP at this head. (c) the landed diff vs the committed pair is EXACTLY the §0a movement: **all 158 facility-55077 rows retained in main; exactly 9 pre-existing CA-facility rows leave main and the SAME 9 enter layup; zero additions; zero other movement; headers identical; every kept row byte-identical and in order.** Mover census (facility, year, class) recorded. (d) the h0-vs-h1 `scenario_config` diff is EMPTY over the full config. **Any other byte anywhere ⇒ STOP, own investigation, nothing lands. No sha in this document may be edited after the fact.** | `_caiso198_extract_delta.json` (`runY_panel_ca_plus_ds`); caiso-196/198/199 G-DELTA discipline. |
| **G-ENGAGE** | The h1 LP differs from h0 in ≥ 1 solve year (window movement inside 2023–2025). An arm whose 9 windows all fall outside the solve years is **INERT** — reported as such, the intake kept on correctness (caiso-188 §7 item 5; caiso-194/199 construction), and the A/B record of caiso-199 then remains the promotion basis. | caiso-199 G-ENGAGE verbatim, delta substituted. |
| **G-SIXISO** | No other ISO's extract, config, keeper shard or matrix cell written; every other registered ISO admits NO member facilities (asserted by test); the member derivation filters to the ISO's own fleet by construction. | Rule 25 `[R-ISO-SCOPE]`, standing. |
| **G-DOF** | Zero new parameters, zero fitted scalars, ledger unchanged at **10/7** in both bundles. Membership adds no freedom: it is derived from the fleet registry, and the delta content was fixed by a pre-flip measurement. | Rule 20 `[R-DOF]`; the caiso-197 composed ledger. |
| **G-C8** | Both bundles ship `legitimacy_diagnostics.json` and score C8. | Rule 21; caiso-189 E10. |
| **G-COV** (post-landing, no-LP) | Re-measured on the landed instrument: CC_REGULAR extract population expected **UNCHANGED at 1.000000** (all 158 DS rows stay in main; the 9 movers are at multi-window CA facilities). Any class-population regression ⇒ investigate before the arm solves. `wefor_residual = 0.0` NOT recomputed — invariant by construction. | `_caiso198_gcov_remeasure.py` construction; caiso-199 post-landing obligation. |

## 5. Kill criteria and the criteria-flip watches

* G-CTRL outside tolerance ⇒ no arm solves; stop-the-line FINDING about the head.
* G-MEMBER resolves to anything but `{"NV": (55077,)}` ⇒ STOP, nothing lands.
* G-DELTA leg (a) fails ⇒ the implementation is not inert unarmed; STOP.
* G-DELTA leg (b) fails ⇒ the run-Y reproduction expectation was wrong; STOP,
  own investigation, nothing lands.
* Any byte movement outside the §0a expectation (leg c) ⇒ STOP.
* Any `scenario_config` difference between the arms ⇒ void.
* Acceptance may not cite C3a in either direction (§0).
* **Pre-registered watch 1 (the return watch):** does the C1-2023 CC_REGULAR
  row (−4.25 TWh on g1, band ~4.4) return to band on h1? REPORTED at full
  magnitude either way; never a gate, never an acceptance ground.
* **Pre-registered watch 2 (flip watch, LIVE IN BOTH DIRECTIONS):** any
  criteria-panel pass→fail flip on h1 vs g1 runs the §5 input-side
  re-examination protocol (mis-citation? coverage failure? classifier
  deviation?); if the input survives, the disposition is
  **"ACCEPT-WITH-FLIP"** — never a silent rejection, never a C3a rescue — and
  the flip feeds the §6 decision tree below.

## 6. Promotion — IN-SESSION, per the delegated handoff; decision tree fixed now

Unlike caiso-196/198/199 (session escalates, owner promotes), the caiso-200
handoff delegates the keeper decision to this session ("OWNER DECISION
REQUIRED AT SESSION START", options A/B/C, standing duties firing in-session).
To keep that delegation honest, the decision tree is fixed BEFORE any solve:

1. **All gates pass, arm engaged, and h1's load-bearing FAIL set ⊆ {C1, C3a}**
   (i.e. criteria-wise no worse than g1, the run option (A) contemplated) ⇒
   **PROMOTE `2026-08-17-caiso-200-h1-memberpanel`** — the option-(A) posture
   applied to the structurally-completed chain (rule 1/14: most structurally
   faithful run, whatever the criteria read). Standing duties fire in-session:
   attestation generated AT promotion (C3c magnitudes re-measured per
   caiso-189 §8.3 — noting C3c reclassification requires guard (a): C1 must
   no longer be failing), site-retention prune per the standing 2026-08-15
   directive, keeper shard + matrix + mechanism-doc §5.2 + status re-stamps,
   `audit_keepers` via the calibration-keeper-auditor.
2. **Gates pass but the arm is INERT** (no solve-year effect) ⇒ the landing
   stands as a correctness fix with zero LP consequence; h1 is dispatch-
   identical to g1 on the landed bytes ⇒ **PROMOTE h1** (the run matching the
   committed instrument), same duties.
3. **Any STOP fires** (G-MEMBER, leg (a), leg (b), leg (c)) ⇒ nothing lands,
   the extract stays `da33e509…` ⇒ fall back to the caiso-199 §4
   recommendation: **PROMOTE `2026-08-16-caiso-199-g1-meritpin`** (option A).
   Grounds recorded now: the g1 gates are untouched by a failed §3b
   expectation; declining (option B) would leave a designated keeper that is
   not byte-reproducible at HEAD (its extract no longer exists in the tree)
   and would keep the classifier's coverage-incomplete baseline — the exact
   posture rules 1/14 reject. The failed expectation becomes an owner object.
4. **h1 carries a NEW load-bearing FAIL outside {C1, C3a}** ⇒ NO promotion
   in-session: both runs registered, keeper stays `2026-08-16-caiso-197-w2-r5`,
   and the decision goes into the owner-sitting package with the flip
   adjudication. (Conservative: the delegation covered the enumerated
   outcomes; a novel criteria regression is not one of them.)

In every branch, the frontier/complete-readiness ASSESSMENT is then written
(the handoff's closing duty): the in-model queue is exhausted, C3a genuinely
fails, `complete` is not supportable on the merits (owner ruling 5 — NOT-YET
is the honest fallback), and the two standing owner-funded objects are the
only remaining C3a axes.

## 7. Required artifacts

* This PRECHECK, committed and pushed before any derive or solve.
* Bundles `results/calibration/caiso200_h0_control`, `caiso200_h1_memberpanel`.
* Probes `scripts/probes/_caiso200_ctrl_tolerance.py` (G-CTRL),
  `_caiso200_member_panel_gates.py` (G-MEMBER + G-DELTA legs a–d + G-ENGAGE);
  committed records `results/calibration/_caiso200_ctrl_tolerance.json`,
  `_caiso200_member_panel_gates.json`, `_caiso200_gcov_landed.json`.
* `results/calibration/FINDING-caiso200-panel-membership-2026-08-17.md` —
  gate tally, §0 quoted, the single-mechanism statement verbatim, the §0a
  record correction on measurement, the watches, the §6 branch taken, and the
  promotion (or escalation) record.
* `results/calibration/ASSESSMENT-caiso200-frontier-2026-08-17.md` — the
  neiso-87-pattern frontier/complete-readiness assessment + owner sitting
  package.
* Matrix duty (b): `campd_outage_windows` CAISO cell updated in
  `docs/codebase-site/data/mechanism-matrix/CAISO.js` (superseding sha if the
  landing holds; the §0a correction either way).
* Calibration-log entry (`docs/calibration-log/caiso.md`), in-session.

Holdout posture: **2023–2025 solves ONLY**; CAISO holds NO `complete` and NO
`final` marker, the spend freeze is ACTIVE, and no out-of-training year is
solved, scored or registered. The 2018–2026 derive span is data preparation
(rule 22, spend-only enforcement — the caiso-196/198/199 precedent).
