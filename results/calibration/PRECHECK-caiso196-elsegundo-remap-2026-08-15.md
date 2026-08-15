# PRECHECK — caiso-196: the El Segundo (ORIS 330 → EIA 57901) CEMS-history remap repair — pre-registered A/B, committed BEFORE any solve

**Committed and pushed before any LP of this session runs.** These gates are fixed
and fail-closed. This is rule-14 `[R-ACCURATE]` / rule-20 `[R-DOF]` input-integrity
work in the caiso-180/183/184 lineage (a measured-input defect found → repaired →
A/B'd on pre-registered structural gates), surfaced by the lane-2 G-COV measurement
(`FINDING-caiso193-wefor-residual-2026-08-15.md` §2). It is **off-queue by design**
like caiso-190: a data-plumbing repair, not a lever — no new mechanism, no
ScenarioConfig field, no matrix row.

## 0. Direction-hazard regime (adapted; binding)

The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD measured
outage removal (a plant that previously carried no overlay gains its real windows),
which lowers availability and raises price, while C3a 2024/2025 already FAIL high.
C3a movement is inadmissible as evidence for or against acceptance in EITHER
direction (rules 1, 13, 14): if the gates pass and C3a worsens, the repair stands
(caiso-183/188 precedent — "the accurate input would have stayed even had the fit
worsened"); if the gates fail, no C3a improvement rescues it. C3a is reported for
transparency only.

## 1. The defect, in bytes (all verified before this PRECHECK was written)

* `campd.CAMPD_UNIT_PLANT_REMAP` = {(315, CT1/CT2) → 62115, (335, CT1/CT2) → 62116}
  — the Alamitos and Huntington Beach repowers — with **no (330, ·) → 57901 entry**.
* CAMPD CA unit-level files carry facility **330 "El Segundo"** with units **"5"**
  and **"7"** in every year 2018–2025 (581.4/560.2 GWh gross in 2018;
  66.7/101.9 (2023), 103.2/88.5 (2024), 30.3/22.9 (2025) GWh).
* The CAISO fleet carries **EIA 57901 El Segundo Energy Center** (CC_REGULAR,
  537.4 MW; EIA-860 generator IDs "5"/"6"/"7"/"8", CTs at "5" and "7" — exact unit-ID
  match). EIA plant 330's own units retired 2015, so ORIS 330's live rows are the
  Energy Center CTs and nothing else — no split remains at this facility.
* `derive_campd_unit_outages.py` applies the remap BEFORE its group lookup; with no
  entry, facility 330 matches no fleet plant and is skipped before detection. The
  committed extract `data/raw/campd-unit-outages-CAISO.csv` (sha256
  `25360e90…1166c6`) therefore has **zero rows for 57901**, and the keeper's LP
  applies only the statistical WEFOR to a 537 MW CC whose measured windows sit
  unread on disk.

## 2. The repair (single data-plumbing delta)

1. Add `(330, "5") → 57901` and `(330, "7") → 57901` to
   `campd.CAMPD_UNIT_PLANT_REMAP` with a citation comment; extend the pinned unit
   test (`tests/iso/caiso/test_caiso_bins.py::TestCaisoSplitPlantRemap`) to require
   57901 in the extract facilities.
2. Re-derive `data/raw/campd-unit-outages-CAISO.csv` over the full committed span
   (2018–2026) with the committed recipe — `--merit-order-guard`, shipped constants
   frozen (caiso-192 proved this recipe reproduces the committed extract
   byte-identically at HEAD, so the re-derive's diff is attributable to the remap
   alone). Rule-23 citation: this PRECHECK §1 (a detector-input keying defect; the
   CAMPD source bytes themselves are unchanged).
3. Whatever the detector emits for El Segundo — windows, merit-guard layup
   classifications, `eia923_netzero` interactions — is taken **as-is**. No
   hand-editing, no threshold movement, no per-plant exception.

Deliberately NOT in scope (single mechanism, rule 19): the Desert Star NV intake
(filed, needs the CAMPD fetch queue); any emission-rate artifact re-derivation
(plant_emission_rates v1/v2 were derived with facility 330 orphaned — flagged for
their own cited re-derive, since touching them moves the LP's CO2-cost basis, a
separate input); the five other ISOs' extracts (not re-derived, byte-untouched).

## 3. A/B protocol

* **e0 CONTROL** — the caiso-188 keeper recipe re-solved in this environment per
  integration-protocol §3, BEFORE the repair touches the working tree:
  `python scripts/replay_keeper.py results/calibration/caiso188_d1_micseam
  --out-dir results/calibration/caiso196_e0_control --set hydro_ror_split=false`
  with the capacity-deliverability partition MATERIALIZED (verified by the
  `seam import cap set to 16055 / 16452 / 16148 MW` log lines) and
  `hydro_ror_split` explicitly False with no hydro-plant-modes partition present —
  both disclosed (the keeper's proven-effective configuration, caiso-188 G-CTRL).
  Warm-start pinned off by the replay driver (`MARKET_SIM_WARMSTART_XYEAR=0`).
* **e1 ARM** — the IDENTICAL invocation into `caiso196_e1_elsegundo`, run after the
  §2 repair lands: same recipe, same overrides, the only tree delta being the
  remap entries + the re-derived extract.
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms sequential
  (rule 12); both registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is
  the (330 → 57901) CEMS-history remap and the extract rows it adds; no
  ScenarioConfig field differs."

## 4. Numeric gates — fixed now, each with its anchor

| gate | bar | anchor |
|---|---|---|
| **G-CTRL** | e0 reproduces the committed keeper within the RATIFIED tolerance: per year, \|ΔC3a\| ≤ 0.1 pp and \|ΔC3b\| ≤ 0.005 against the committed keeper values. The control delta is quoted as the NOISE FLOOR at full precision BEFORE any treated delta is read. Outside tolerance ⇒ **stop-the-line finding about the head, NO ARM SOLVES**, escalate. | Integration protocol §3, tolerance RATIFIED by caiso-191 before any campaign measurement; bit-zero is the observed CAISO norm (caiso-184/188 G-CTRL). |
| **G-DELTA** | The extract diff is STRICTLY ADDITIVE and every added row has `facility_id == 57901` (main extract and, if touched, the layup companion alike); every pre-existing row byte-identical. The e0-vs-e1 `scenario_config` diff is EMPTY over the full config. Any other change ⇒ void (a re-derive that moves any non-El-Segundo byte is its own investigation, not this arm). | caiso-192's byte-identity measurement of the same recipe at HEAD — the committed extract reproduces exactly, so the remap is the only free variable. |
| **G-ENGAGE** | e1's shipped loader (`outages.unit_outage_derate_factors`) resolves `(57901, "CC_REGULAR")` with mean multiplier < 1 in ≥ 1 solve year, and the e1 LP differs from e0. A bit-identical e1 ⇒ the repair is INERT on the solve window (possible if every detected span classifies as layup under the shipped guard) — reported as such, promotion moot, the remap kept on correctness (caiso-188 §7 item 5: check the data the gate resolves through). | caiso-194's G-ENGAGE construction; the caiso-192 finding that the guard's layup classification is live at this plant class. |
| **G-SIXISO** | No other ISO's extract, config, or matrix cell is written; the remap keys are CA facilities by construction. | Rule 25 `[R-ISO-SCOPE]`, standing. |
| **G-DOF** | Zero new parameters, zero fitted scalars, ledger unchanged at 11/8 in both bundles' attestations. The repair adds DATA, not freedom. | Rule 20 `[R-DOF]`; the committed 11/8 baseline. |
| **G-C8** | Both bundles ship `legitimacy_diagnostics.json` and score C8 (registration duty; no attestation-less bundle — the caiso-189 E10 lesson). | Rule 21; caiso-189. |

## 5. Kill criteria

* G-CTRL outside tolerance ⇒ no arm solves; stop-the-line FINDING about the head.
* Any non-57901 byte change in the re-derived extract ⇒ session void for this arm;
  the diff becomes its own investigation.
* Any `scenario_config` difference between the arms ⇒ void.
* Acceptance may not cite C3a in either direction (§0).

## 6. Promotion — explicitly NOT in-session

Both arms are registered and the FINDING packages the decision, but **no keeper
shard is edited this session**. Three owner calls are bundled for one sitting:
(1) whether e1 becomes the keeper (rule-14 posture stated: if the gates pass, the
accurate input is the structurally right baseline and a worsened C3a is not a
rejection ground); (2) whether the close-out campaign's remaining lanes (3, 5)
re-anchor their control onto the repaired-extract base — integration protocol §1/§3
name the caiso-188 recipe and its committed inputs, and the protocol's own amendment
clause reserves deviations to "a fresh adjudication session and explicit owner
authorization"; (3) whether lane 2 re-runs on the repaired instrument scoped
`{CC_REGULAR}` (its G-COV passes there under both population readings —
`FINDING-caiso193-wefor-residual-2026-08-15.md` §3 — and the owner-granted value
0.0 is invariant to the repair by the frozen formula's own arithmetic).

## 7. Required artifacts

* This PRECHECK, committed before any solve.
* Bundles `results/calibration/caiso196_e0_control`, `caiso196_e1_elsegundo`
  (run ids minted by the replay driver's own dating rule for overridden runs).
* `results/calibration/_caiso196_gcov_remeasure.json` — the no-LP G-COV re-measure
  on the repaired instrument (both population readings).
* `results/calibration/FINDING-caiso196-elsegundo-remap-2026-08-15.md` — gate tally,
  the §0 clause quoted, the single-mechanism statement verbatim, the owner decision
  package, matrix duty (b) (`campd_outage_windows` CAISO evidence citation append —
  the recorded extract sha changes with the re-derive).
* Calibration-log entries (`docs/calibration-log/caiso.md`) for caiso-193 (lane 2)
  and caiso-196, in-session.
