# PRECHECK — caiso-199: the merit-order panel SCOPE PIN + the Desert Star (EIA 55077) landing — pre-registered A/B, committed BEFORE any solve

**Committed and pushed before any LP of this session runs.** These gates are fixed
and fail-closed. This session executes **owner ruling caiso-199 §5 option 1**
(taken at session start on the `FINDING-caiso198-desertstar-extract-2026-08-16.md`
§5 escalation package): *pin the merit-order panel's identification scope
independently of the detection state list, then land the strictly-additive Desert
Star candidate and A/B it.*

It is **NOT a new lever** (rule 28a): the close-out lane inventory is CLOSED AND
FULLY ADJUDICATED (`caiso191-owner-rulings-2026-08-11.md`) and stays untouched.
It adds **no ScenarioConfig field and no matrix row** — the pin is a *derive-recipe
identification scope*, the same class of object as `campd.ISO_STATES` itself,
whose effect on any solve is fully mediated by the extract artifact whose sha is
already provenance-tracked through G-EXTRACT. (Rule 24 `[R-REGISTRY]` is
satisfied by that existing channel, not bypassed: no solve-time knob is created,
and the recipe scope is a committed literal, not an env var or a fallback.)

## 0. Direction-hazard regime (verbatim from PRECHECK-caiso198 §0, binding)

> The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD
> measured outage removal (a plant that previously carried no overlay gains its
> real windows), which lowers availability and raises price, while C3a 2024/2025
> already FAIL high (+12.1/+15.6 %). C3a movement is inadmissible as evidence for
> or against acceptance in EITHER direction (rules 1, 13, 14): if the gates pass
> and C3a worsens, the repair stands (caiso-183/188/196 precedent — "the accurate
> input would have stayed even had the fit worsened"); if the gates fail, no C3a
> improvement rescues it. C3a is reported for transparency only.

## 1. What is being pinned, and why it is a rule-23 charter not a tuning act

`scripts.lib.outage_detect.build_merit_order_panel` is **fleet-blind by design**
("self-contained", no EIA-860 join): it re-reads the CAMPD unit-level parquets for
whatever state list it is handed. Before this pin the deriver handed it the
**detection** list `campd.ISO_STATES[iso]`, so the two scopes were silently
coupled and a *coverage* widening re-identified the *classifier*:

* **`ISO_STATES` = detection coverage** — "which state files must be READ so every
  plant in the ISO's fleet is observable?" Widening it is purely additive: the
  loaders and the derivation filter every loaded state back to the ISO's own
  fleet, so a new state adds plants and removes nothing.
* **the panel's list = identification scope** — "whose running capacity SETS the
  revealed clearing cost (RCC) each window is scored against?" That object is the
  ISO's **own market**; NV Energy's fleet does not clear CAISO's merit order.

Measured coupling (caiso-198, `_caiso198_extract_delta.json`): adding NV for the
ONE CAISO-fleet plant that files CEMS there put **59–64 units of 13–14 NON-CAISO
NV Energy facilities** (Fort Churchill, Clark, Harry Allen, Tracy, North Valmy,
Chuck Lenzie, Silverhawk, Higgins…) into CAISO's panel, moved the RCC in **87–97 %
of hours** (mean **+3.45 $/MWh** in 2024, +2.41 in 2025) and reclassified **275
CA-facility windows at 15 facilities** (188 layup→mechanical, 87 reverse,
concentrated in the solve years). That is exactly the instrument instability rule
23 `[R-FROZEN-DERIVE]` exists to prevent — the classifier moved with **no change
to its own source data**, driven by an unrelated coverage decision.

**Rule-23 citation for this re-derivation:** the *recipe charter* granted by the
owner ruling above, plus the caiso-197 NV data landing. **No residual is
consulted anywhere in the pin's construction**, and the pin's value is not a
fitted quantity — it is the restoration of the scope every committed CAISO
extract through sha `5f3e35c5…` was already identified on.

### 1a. Scope of the pin — recorded ex ante, deliberately narrow

* It is a **STATE-LIST pin, not a fleet filter.** The committed CA-only panel
  already contains non-CAISO **CA** units (LADWP and municipal utilities file CEMS
  under CA), and that is the panel the caiso-192 gates adjudicated the guard on.
  Making the panel fleet-PURE would move the committed extract and needs its own
  baseline measurement; it is **NOT done here** (FINDING-caiso198 §5 "evidence
  AGAINST / scope caution", taken as written).
* **CAISO is the only ISO pinned.** Every other ISO falls back to its detection
  list — the pre-pin behaviour — so no other ISO's committed extract can move
  (rule 25 `[R-ISO-SCOPE]`; asserted by a test, §2.3). The same fleet-blindness at
  NYISO (NY+NJ), PJM and MISO (shared states) is **flagged and adjudicated NOT AT
  ALL** by this session; each is its own lane's measurement, and no verdict
  transfers.

### 1b. Construction difference from the caiso-198 candidate — recorded ex ante

The caiso-198 run-X candidate was produced by scoping the panel's **directory**
(`_MERIT_UNIT_LEVEL_DIR` symlinked to CA-only files) while the state list stayed
CA+NV. This pin scopes the **state list**, which ALSO narrows
`_delivered_coal_price_tables(frozenset(states), year)` from `{CA, NV}` to `{CA}`.
Pre-registered claim that this is a **provable no-op**, measured on the input data
before this PRECHECK was written and BEFORE any derive was run:

* **No CA CEMS unit is coal-fuelled in ANY year of the 2018–2026 derive span** —
  CA `primaryFuelInfo` ∈ {natural gas, other gas, pipeline natural gas, wood};
  `_MERIT_COAL_FUELS` = {coal, coal refuse} matches NOTHING in CA in any year. The
  coal ladder is therefore never consulted for any unit that can enter the pinned
  panel. (NV *does* carry coal — North Valmy — which is one of the units driving
  the measured RCC rise; under the pin those units are out of the panel entirely.)
* The gas leg `delivered_gas_price_hourly(iso, year, n_hours)` keys on **`iso`**,
  not on the state list, so it is unaffected by construction.

Consequently the pin is expected to reproduce the run-X candidate **byte-for-byte**
(sha `da33e509…`). **If it does not, that expectation was wrong and the session
STOPS** (§5) — the ex-ante claim above is falsifiable and is gated as such.

## 2. The change (one code pin + one data landing)

1. **`src/market_sim/data/campd.py`** — new registry `ISO_MERIT_PANEL_STATES`
   (`{"CAISO": ("CA",)}`) + accessor `merit_panel_states_for_iso(iso)` that falls
   back to `ISO_STATES` for any unpinned ISO. Documented with the two-question
   distinction and the caiso-198 measurement.
2. **`scripts/data/derive_campd_unit_outages.py`** — the panel is built from
   `campd.merit_panel_states_for_iso(iso)` instead of the detection `states`; the
   panel log line discloses its scope (`[scope CA]`).
3. **`tests/curation/test_campd.py`** — `TestMeritPanelStatePin`, 7 tests: CAISO
   pinned to `("CA",)`; NV still in the DETECTION scope; **the pin survives a
   detection widening** (the invariant itself); every unpinned ISO resolves
   exactly to its detection list (rule 25); CAISO is the only pinned ISO; unknown
   ISO → `()`; and a **wiring guard** that the deriver feeds the panel the pinned
   scope and not `states` (reverting the call site is the exact regression the pin
   exists to prevent).
4. **The data landing** — the committed recipe (`--iso CAISO --years 2018 … 2026
   --merit-order-guard --hour-grain`) re-derived in place on the **committed**
   `("CA","NV")` detection list, under the pin. No hand-editing, no threshold
   movement, no per-plant exception, no unit-ID remap entry; whatever the detector
   emits is taken as-is.

Deliberately **NOT** in scope (single mechanism, rule 19): a fleet-purity filter
on the panel (§1a); `thermal_tranches_CAISO.csv` and `plant_emission_rates`
v1/v2 (each its own cited re-derive with its own A/B); the five other ISOs'
extracts, configs and matrix shards (byte-untouched); any change to the guard's
detection thresholds, `MERIT_RCC_PCTL` or `MERIT_OOM_FRAC`.

## 3. A/B protocol

* **g0 CONTROL** — the caiso-197 keeper recipe re-solved in this environment per
  integration-protocol §3, with `data/raw` at the **committed** extract bytes:
  `python scripts/replay_keeper.py results/calibration/caiso197_w2_r5
  --out-dir results/calibration/caiso199_g0_control --set hydro_ror_split=false`
  with the capacity-deliverability partition MATERIALIZED first
  (`curate_capacity_deliverability.py --isos CAISO`; verified by the
  `seam import cap set to 16055 / 16452 / 16148 MW` log lines) and
  `hydro_ror_split` explicitly False with no hydro-plant-modes partition present —
  both disclosed (the keeper's proven-effective configuration, caiso-188/196/197
  G-CTRL). Warm-start pinned off by the replay driver
  (`MARKET_SIM_WARMSTART_XYEAR=0`).
* **g1 ARM** — the IDENTICAL invocation into `caiso199_g1_meritpin`, run after the
  §4 baseline proof lands the extract. The panel-scope pin is present in the tree
  for BOTH arms (it cannot affect an LP — it is derive-time only), so **the sole
  A/B delta is the extract bytes**.
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms sequential
  (rule 12) — the control solves with the tree's `data/raw` clean, and the derive
  runs only after the control completes (a derive must never coexist with a
  running solve).
* Both arms registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`.
* **Single-mechanism statement, required verbatim in the FINDING:** "The A/B delta
  is the merit-panel-scope-pinned extract re-derive and the facility-55077 rows it
  adds; no ScenarioConfig field differs."

## 4. Numeric gates — fixed now, each with its anchor

| gate | bar | anchor |
|---|---|---|
| **G-CTRL** | g0 reproduces the committed keeper within the RATIFIED tolerance: per year, \|ΔC3a\| ≤ 0.1 pp and \|ΔC3b\| ≤ 0.005 against the committed keeper values (+4.0/+12.1/+15.6 %; 0.097/0.174/0.181). The control delta is quoted as the NOISE FLOOR at full precision BEFORE any treated delta is read; bit-zero is the lane norm and the primary instrument is max \|Δ\| over every zone-hour of `hourly/system_*.parquet` and every class-hour of `hourly/class_hourly_*.parquet`. Outside tolerance ⇒ **stop-the-line finding about the head, NO ARM SOLVES**, escalate. | Integration protocol §3, tolerance RATIFIED by caiso-191 before any campaign measurement; bit-zero observed at caiso-184/188/196/197/198. |
| **G-DELTA** | **Four legs, all pre-pinned to shas fixed in this document.** (a) **baseline, NV excluded**: with `ISO_STATES["CAISO"]` temporarily `("CA",)` (scratch `--out`, restored immediately), the PINNED recipe reproduces the committed extract byte-identically — main `5f3e35c5…`, layup `1475a577…`. This proves the pin is inert when the two scopes coincide, i.e. it changes nothing about the committed baseline. (b) **the landing, NV included**: with the committed `("CA","NV")` detection list, the PINNED recipe reproduces the caiso-198 strictly-additive candidate byte-identically — main **`da33e509…`**, layup **`1475a577…` (BYTE-IDENTICAL to the committed companion)**. (c) the landed diff is **STRICTLY ADDITIVE**: exactly **158** added rows, every one `facility_id == 55077`, zero removals, zero non-55077 additions, every pre-existing row byte-identical and in order, layup companion byte-identical. (d) the g0-vs-g1 `scenario_config` diff is EMPTY over the full config. **Any other byte anywhere ⇒ STOP, own investigation, nothing lands.** | caiso-196/198 G-DELTA discipline; shas from `_caiso198_extract_delta.json` (`runX_panel_ca_only`, reproducible via `scripts/probes/_caiso198_extract_delta.py`). |
| **G-ENGAGE** | g1's shipped loader (`outages.unit_outage_derate_factors`) resolves `(55077, "CC_REGULAR")` with mean multiplier < 1 in ≥ 1 solve year, **and** the g1 LP differs from g0. A bit-identical g1, or an extract whose added windows all fall outside 2023–2025, is an **INERT** arm — reported as such, promotion moot, **the intake kept on correctness** (caiso-188 §7 item 5; caiso-194 G-ENGAGE construction). Inertness is a real possible outcome and is NOT a failure of the repair. | caiso-196/198 G-ENGAGE verbatim, facility substituted. |
| **G-SIXISO** | No other ISO's extract, config, keeper shard or matrix cell is written; the pin leaves every unpinned ISO resolving exactly to its detection list (asserted by test, §2.3); the NV loading filters to the CAISO fleet by construction. | Rule 25 `[R-ISO-SCOPE]`, standing. |
| **G-DOF** | Zero new parameters, zero fitted scalars, ledger unchanged at **10/7** in both bundles' attestations (the caiso-197 composed ledger; the caiso-188 import-tranche census row n_scalars 6 carries). The pin adds no freedom: it REMOVES an unintended dependence of the classifier on an unrelated coverage choice, and its value is the scope the committed extract already had. | Rule 20 `[R-DOF]`; the committed 10/7 baseline (`caiso197_w2_r5/calibration_attestation.json`). |
| **G-C8** | Both bundles ship `legitimacy_diagnostics.json` and score C8 (registration duty; no attestation-less bundle — the caiso-189 E10 lesson). | Rule 21; caiso-189. |

**Post-landing no-LP obligation** (carried from PRECHECK-caiso198 §4, now measured
on the LANDED instrument): G-COV re-measured with
`scripts/probes/_caiso198_gcov_remeasure.py` run with **NO `--extract`** (reading
`data/raw` itself) → committed record. Expectation, already measured on the
candidate (`_caiso198_gcov_remeasure.json`): CC_REGULAR extract population
**1.000000** / strict CEMS **0.990880**; CC_CHP unchanged at 0.678/0.636 and stays
excluded fail-closed. The lane-2 premise can only STRENGTHEN and the frozen
`wefor_residual = 0.0` is INVARIANT by construction (`residual_c = max(0, W_c −
X_c)` with X_c already ≥ 4.9× W). **The frozen value is not recomputed; no
gatespec band is touched.**

## 5. Kill criteria and the criteria-flip watch

* G-CTRL outside tolerance ⇒ no arm solves; stop-the-line FINDING about the head.
* **G-DELTA leg (a) fails** (pinned recipe does not reproduce `5f3e35c5…` with NV
  excluded) ⇒ the pin is not inert on the baseline; STOP, nothing lands.
* **G-DELTA leg (b) fails** (pinned recipe does not reproduce `da33e509…` with NV
  included) ⇒ the §1b ex-ante no-op claim was wrong, or the pin differs from the
  run-X construction in some unaccounted way; **STOP, own investigation, nothing
  lands.** No sha in this document may be edited after the fact.
* Any non-55077 byte change in the landed extract or layup companion ⇒ STOP.
* Any `scenario_config` difference between the arms ⇒ void.
* Acceptance may not cite C3a in either direction (§0).
* **Pre-registered criteria-flip watch (integration-protocol §5 posture, LIVE IN
  BOTH DIRECTIONS): C1-2023 CC_REGULAR sits at −4.13 TWh against a ~4.4 TWh
  band** — the caiso-197 healing left ~0.3 TWh of headroom, and added measured
  removal at a CC_REGULAR plant can push the row back out of band. If a pass→fail
  flip occurs, the §5 protocol runs **input-side re-examination ONLY**
  (mis-citation? coverage failure? classifier deviation?); if the input survives,
  the disposition is verbatim **"ACCEPT-WITH-FLIP, escalate to owner"** — never a
  silent rejection, and never a rescue via C3a (caiso-196 §3 precedent,
  adjudicated on exactly this class and criterion).

## 6. Promotion — explicitly NOT in-session

Both arms are registered and the FINDING packages the decision; **no keeper shard
is edited this session** (caiso-196/198 precedent: the session escalates, the owner
promotes). The owner package states the rule-14 posture: if the gates pass, the
accurate input is the structurally right baseline and a worsened C3a (or an
ACCEPT-WITH-FLIP C1 row) is not a rejection ground. If the owner promotes, the
standing duties fire in the promoting session: attestation generated AT promotion
with C3c magnitudes re-measured per caiso-189 §8.3, site-retention prune per the
standing 2026-08-15 directive, keeper shard + matrix + §5.2 + status re-stamps,
`audit_keepers`.

**After this landing the in-model queue is EXHAUSTED.** The only named C3a routes
remain the two standing owner objects (the walled hourly PS water-state intake,
caiso-141 / ruling 4; the 8,800 MW declared residual, caiso-191 §4); the
alternative to further movement is the frontier/complete-readiness ASSESSMENT
(neiso-87 pattern) stating plainly that C3a genuinely fails (owner ruling 5:
NOT-YET is the honest fallback). **No new lane is improvised.**

## 7. Required artifacts

* This PRECHECK, committed and pushed before any solve.
* Bundles `results/calibration/caiso199_g0_control`, `caiso199_g1_meritpin`.
* Probes `scripts/probes/_caiso199_ctrl_tolerance.py` (G-CTRL),
  `_caiso199_panel_pin_gates.py` (G-DELTA legs a–d + G-ENGAGE); committed records
  `results/calibration/_caiso199_ctrl_tolerance.json`,
  `_caiso199_panel_pin_gates.json`, and the re-measured
  `_caiso199_gcov_landed.json`.
* `results/calibration/FINDING-caiso199-merit-panel-scope-2026-08-16.md` — gate
  tally, the §0 clause quoted, the single-mechanism statement verbatim, the §5
  flip adjudication if it fires, and the owner decision package.
* Matrix duty (b): `campd_outage_windows` CAISO cell updated in
  `docs/codebase-site/data/mechanism-matrix/CAISO.js` — the landed extract sha
  **supersedes** (unlike caiso-198, where nothing landed).
* Calibration-log entry (`docs/calibration-log/caiso.md`) for caiso-199,
  in-session.

Holdout posture: **2023–2025 solves ONLY**; CAISO holds NO `complete` and NO
`final` marker, the spend freeze is ACTIVE, and no out-of-training year is solved,
scored or registered. The 2018–2026 derive span is **data preparation**, which the
tier gates do not restrict (rule 22, spend-only enforcement — the caiso-196/198
precedent re-derived the identical span).
