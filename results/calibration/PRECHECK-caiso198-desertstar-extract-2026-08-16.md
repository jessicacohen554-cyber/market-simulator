# PRECHECK — caiso-198: the Desert Star (EIA 55077) NV state-scope extract re-derive — pre-registered A/B, committed BEFORE any solve

**Committed and pushed before any LP of this session runs.** These gates are fixed
and fail-closed. This is the chartered rule-22/23 measured-input repair the
caiso-197 §6 handoff names (`FINDING-caiso197-wave2-promotion-2026-08-16.md` §6
item 1) — the deferred half of the caiso-197 NV intake, executed on the caiso-196
pattern exactly (data repair → cited re-derive → A/B on the keeper recipe → keeper
decision packaged for the owner). It is **NOT a new lever** (rule 28a): the
close-out lane inventory is CLOSED AND FULLY ADJUDICATED
(`caiso191-owner-rulings-2026-08-11.md`) and stays untouched; no new mechanism, no
ScenarioConfig field, no matrix row. Surfaced by the lane-2 G-COV measurement
(`FINDING-caiso193-wefor-residual-2026-08-15.md` §2 item 2: the state-scope gap —
the last unobserved CC_REGULAR plant).

## 0. Direction-hazard regime (adapted; binding)

The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD
measured outage removal (a plant that previously carried no overlay gains its real
windows), which lowers availability and raises price, while C3a 2024/2025 already
FAIL high (+12.1/+15.6 %). C3a movement is inadmissible as evidence for or against
acceptance in EITHER direction (rules 1, 13, 14): if the gates pass and C3a
worsens, the repair stands (caiso-183/188/196 precedent — "the accurate input
would have stayed even had the fit worsened"); if the gates fail, no C3a
improvement rescues it. C3a is reported for transparency only.

## 1. The defect, in bytes (all verified before this PRECHECK was written)

* `campd.ISO_STATES["CAISO"]` is **already `("CA", "NV")`** — committed at the
  caiso-197 session with the full NV CAMPD landing
  (`data/raw/campd-unit-level/NV_{2018..2026}.parquet`, incl. the
  quarantine-authorized 2022/H1-2026 intake under `--holdout-intake CAISO`). Only
  the **extract artifact is stale**: `data/raw/campd-unit-outages-CAISO.csv`
  (sha256 `5f3e35c5dad88da76be8f684973fd7c78009f63e84d3f5b23a609e93d45fb4ce`,
  4,561 data rows) carries **zero rows for facility 55077**, and so does the layup
  companion `campd-unit-outages-layup-CAISO.csv` (sha256
  `1475a57738c6de656938c65eebdd0f197013cac9a435cd09571a72c735b7bd43`). The
  caiso-197 G-EXTRACT proof (identical extract shas in control and keeper) is
  precisely the record that the campaign base never moved — the re-derive was
  deferred post-ladder BY CHARTER so the ladder's arms never raced their own base.
* The NV unit-level files carry facility **55077 "Desert Star Energy Center"**
  with units **EDE1 / EDE2** in every year 2018–2026 (e.g. 17,520 unit-hours in
  2023 = 2 units × 8,760).
* The CAISO fleet carries **EIA 55077 Desert Star Energy Center** as
  **CC_REGULAR** (fleet pmax 140.0 + 170.0 MW through the shipped fleet path;
  EIA-860 generators ED01/ED02/ED03, 370.1 MW nameplate — the
  FINDING-caiso193 §2 figure, 2.42 % of the class).
* `derive_campd_unit_outages.py` resolves non-ERCOT facility→group through the
  shipped fleet path (`load_fleet_from_csv`), so `group_by_code[55077] =
  "CC_REGULAR"` resolves and the facility qualifies
  (`QUALIFYING_PLANT_GROUPS`). With the CA-only state list it was skipped before
  detection — a plant whose real availability history sat unREAD not on disk but
  un-fetched; since caiso-197 it sits unread ON disk, the exact caiso-196 posture.
* **Unit-ID note, recorded ex ante:** CAMPD `EDE1`/`EDE2` vs EIA-860
  `ED01`/`ED02`/`ED03` — the normalized exact match misses and the trailing-digit
  heuristic also misses (`"1"` vs `"01"`), so unit capacity resolves through the
  recipe's documented **`observed_peak` fallback** (the unit's own CAMPD peak
  gross, steam-inclusive). This is shipped recipe behaviour, taken as-is; a
  hand-mapping entry would be new scope and is NOT taken (§2).

## 2. The repair (single data-artifact delta; zero code, zero config)

1. **No source edit of any kind.** The state list, the loader and the recipe are
   all committed; the repair is purely the deferred re-derivation of the extract
   artifact. Rule-23 citation: the caiso-197 NV data landing + this PRECHECK
   (the source data updated; no residual is consulted).
2. **BASELINE BYTE-IDENTITY PROOF FIRST** (the caiso-196 G-DELTA discipline):
   with `ISO_STATES["CAISO"]` temporarily reverted to `("CA",)` (uncommitted
   scratch edit, restored immediately after; nothing else touched), the committed
   recipe — `--iso CAISO --years 2018 2019 2020 2021 2022 2023 2024 2025 2026
   --merit-order-guard --hour-grain`, shipped constants frozen — re-derives to a
   scratch `--out` and must reproduce the committed extract **byte-identically**
   (sha256 `5f3e35c5…`) and the committed layup companion byte-identically
   (`1475a577…`). This proves the NV state addition is the ONLY free variable at
   this head. Failure ⇒ stop, own investigation, no repair lands.
3. **The real re-derive**: the identical committed recipe on the committed
   `("CA", "NV")` state list, writing `data/raw/campd-unit-outages-CAISO.csv` and
   its layup companion in place.
4. Whatever the detector emits for Desert Star — windows or none, merit-guard
   layup classifications, capacity-source fallbacks — is taken **as-is**. No
   hand-editing, no threshold movement, no per-plant exception, no unit-ID
   remap entry.

Deliberately NOT in scope (single mechanism, rule 19; flagged caiso-196 §5
item 6): `thermal_tranches_CAISO.csv` and `plant_emission_rates` v1/v2 (each
remains its OWN cited re-derive with its own A/B — they carry no 57901 rows
either and are NOT bundled into this arm); the five other ISOs' extracts (not
re-derived, byte-untouched); any change to the merit-order-guard panel
construction (NV units enter the panel through the committed recipe itself; see
G-DELTA's non-55077 kill clause).

## 3. A/B protocol

* **f0 CONTROL** — the caiso-197 keeper recipe re-solved in this environment per
  integration-protocol §3, BEFORE the repair touches the working tree:
  `python scripts/replay_keeper.py results/calibration/caiso197_w2_r5
  --out-dir results/calibration/caiso198_f0_control --set hydro_ror_split=false`
  with the capacity-deliverability partition MATERIALIZED first
  (`curate_capacity_deliverability.py --isos CAISO`; verified by the
  `seam import cap set to 16055 / 16452 / 16148 MW` log lines) and
  `hydro_ror_split` explicitly False with no hydro-plant-modes partition present —
  both disclosed (the keeper's proven-effective configuration, caiso-188/196/197
  G-CTRL). Warm-start pinned off by the replay driver
  (`MARKET_SIM_WARMSTART_XYEAR=0`).
* **f1 ARM** — the IDENTICAL invocation into `caiso198_f1_desertstar`, run after
  the §2 repair lands: same recipe, same overrides, the only tree delta being the
  re-derived extract (+ layup companion if touched).
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms
  sequential (rule 12) — the control solves on the committed extract with the
  tree clean, the baseline proof and re-derive run only after the control
  completes (the derive's temporary state-list edit must never coexist with a
  running solve). Both arms registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is
  the NV state-scope extract re-derive and the facility-55077 rows it adds; no
  ScenarioConfig field differs."

## 4. Numeric gates — fixed now, each with its anchor

| gate | bar | anchor |
|---|---|---|
| **G-CTRL** | f0 reproduces the committed keeper within the RATIFIED tolerance: per year, \|ΔC3a\| ≤ 0.1 pp and \|ΔC3b\| ≤ 0.005 against the committed keeper values (+4.0/+12.1/+15.6 %; 0.097/0.174/0.181). The control delta is quoted as the NOISE FLOOR at full precision BEFORE any treated delta is read; bit-zero is the lane norm and the primary instrument is max \|Δ\| over every zone-hour of `hourly/system_*.parquet` and every class-hour of `hourly/class_hourly_*.parquet` (probe `_caiso198_ctrl_tolerance.py`). Outside tolerance ⇒ **stop-the-line finding about the head, NO ARM SOLVES**, escalate. | Integration protocol §3, tolerance RATIFIED by caiso-191 before any campaign measurement; bit-zero observed at caiso-184/188/196/197. |
| **G-DELTA** | Three legs: (a) the §2.2 baseline byte-identity proof (NV excluded ⇒ sha `5f3e35c5…` exactly; layup `1475a577…`); (b) the repaired extract diff is STRICTLY ADDITIVE and every added row has `facility_id == 55077` (main extract and layup companion alike); every pre-existing row byte-identical and in order; (c) the f0-vs-f1 `scenario_config` diff is EMPTY over the full config. **Any non-55077 byte anywhere ⇒ void — a re-derive that moves any non-Desert-Star byte (including a merit-panel-induced reclassification of a CA facility's window) is its own investigation, not this arm.** | caiso-196 G-DELTA verbatim, one facility id substituted; caiso-192's byte-identity measurement of the recipe class at HEAD. |
| **G-ENGAGE** | f1's shipped loader (`outages.unit_outage_derate_factors`) resolves `(55077, "CC_REGULAR")` with mean multiplier < 1 in ≥ 1 solve year, and the f1 LP differs from f0. A bit-identical f1, or an extract whose added windows all fall outside 2023–2025, is an **INERT** arm — reported as such, promotion moot, the intake kept on correctness (caiso-188 §7 item 5; caiso-194 G-ENGAGE construction). Desert Star's CEMS conduct is unmeasured until the derive runs, so inertness on the solve window is a real possible outcome and is NOT a failure of the repair. | caiso-196 G-ENGAGE verbatim, facility substituted. |
| **G-SIXISO** | No other ISO's extract, config, or matrix cell is written; the NV loading filters to the CAISO fleet by construction (the NYISO NY+NJ template — `ISO_STATES` comment, `load_campd_hourly`/derive fleet filter). | Rule 25 `[R-ISO-SCOPE]`, standing. |
| **G-DOF** | Zero new parameters, zero fitted scalars, ledger unchanged at **10/7** in both bundles' attestations (the caiso-197 composed ledger; the caiso-188 import-tranche census row n_scalars 6 carries). The repair adds DATA, not freedom. | Rule 20 `[R-DOF]`; the committed 10/7 baseline (`caiso197_w2_r5/calibration_attestation.json`). |
| **G-C8** | Both bundles ship `legitimacy_diagnostics.json` and score C8 (registration duty; no attestation-less bundle — the caiso-189 E10 lesson). | Rule 21; caiso-189. |

**Post-repair no-LP obligation (the §6-handoff's own expectation, recorded as a
work item, not a gate on the arm):** G-COV re-measured on the repaired instrument
with the `_caiso193_wefor_coverage.py` construction
(probe `_caiso198_gcov_remeasure.py` → committed record
`_caiso198_gcov_remeasure.json`, both population readings). Expectation:
CC_REGULAR reaches ~100 % of the extract population — the lane-2 premise can only
STRENGTHEN (X_c can only rise; the frozen `wefor_residual = 0.0` is the caiso-187
record's arithmetic identity and is INVARIANT to this repair by construction —
`residual_c = max(0, W_c − X_c)` with X_c already ≥ 4.9× W). CC_CHP stays
excluded fail-closed (a real CEMS-exemption limit, not repairable by plumbing).
The frozen value is not recomputed; no gatespec band is touched.

## 5. Kill criteria and the criteria-flip watch

* G-CTRL outside tolerance ⇒ no arm solves; stop-the-line FINDING about the head.
* Baseline byte-identity proof fails ⇒ no repair lands; own investigation.
* Any non-55077 byte change in the re-derived extract or layup companion ⇒
  session void for this arm; the diff becomes its own investigation.
* Any `scenario_config` difference between the arms ⇒ void.
* Acceptance may not cite C3a in either direction (§0).
* **Pre-registered criteria-flip watch (integration-protocol §5 posture):
  C1-2023 CC_REGULAR sits at −4.13 TWh against a ~4.4 TWh band** — the caiso-197
  healing left ~0.3 TWh of headroom, and added measured removal at a CC_REGULAR
  plant can push the row back out of band. If a pass→fail flip occurs, the §5
  protocol runs **input-side re-examination ONLY** (mis-citation? coverage
  failure? classifier deviation?); if the input survives, the disposition is
  verbatim **"ACCEPT-WITH-FLIP, escalate to owner"** — never a silent rejection,
  and never a rescue via C3a (caiso-196 §3 precedent, adjudicated on exactly this
  class and criterion).

## 6. Promotion — explicitly NOT in-session

Both arms are registered and the FINDING packages the decision; **no keeper shard
is edited this session** (caiso-196 precedent: the session escalates, the owner
promotes). The owner package states the rule-14 posture: if the gates pass, the
accurate input is the structurally right baseline and a worsened C3a (or an
ACCEPT-WITH-FLIP C1 row) is not a rejection ground. If the owner promotes, the
standing duties fire in the promoting session: attestation generated AT promotion
(`gen_caiso198_attestation.py`, the E10 discipline) with C3c magnitudes
re-measured per caiso-189 §8.3, site-retention prune per the standing 2026-08-15
directive, keeper shard + matrix + §5.2 + status re-stamps, `audit_keepers`.
**After this repair the in-model queue is EXHAUSTED** — the only named C3a routes
remain the two standing owner objects (the walled hourly PS water-state intake,
caiso-141 / ruling 4; the 8,800 MW declared residual, caiso-191 §4), and the
alternative to further movement is the frontier/complete-readiness ASSESSMENT
(neiso-87 pattern) stating plainly that C3a genuinely fails (owner ruling 5:
NOT-YET is the honest fallback).

## 7. Required artifacts

* This PRECHECK, committed and pushed before any solve.
* Bundles `results/calibration/caiso198_f0_control`,
  `caiso198_f1_desertstar` (run ids minted by the replay driver's dating rule
  for overridden runs).
* Probes `scripts/probes/_caiso198_ctrl_tolerance.py` (G-CTRL),
  `_caiso198_ab_gates.py` (G-DELTA legs b/c + G-ENGAGE),
  `_caiso198_gcov_remeasure.py` (§4 obligation); committed records
  `results/calibration/_caiso198_ctrl_tolerance.json`, `_caiso198_ab_gates.json`,
  `_caiso198_gcov_remeasure.json`.
* `results/calibration/FINDING-caiso198-desertstar-extract-2026-08-16.md` — gate
  tally, the §0 clause quoted, the single-mechanism statement verbatim, the §5
  flip adjudication if it fires, the owner decision package, matrix duty (b)
  (`campd_outage_windows` CAISO evidence citation append — the recorded extract
  sha supersedes again).
* Calibration-log entry (`docs/calibration-log/caiso.md`) for caiso-198,
  in-session.

Holdout posture: 2023–2025 solves only; both markers and the spend freeze
untouched; the 2018–2026 derive span is data preparation, which the tier gates do
not restrict (rule 22, spend-only enforcement — the caiso-196 precedent re-derived
the identical span).
