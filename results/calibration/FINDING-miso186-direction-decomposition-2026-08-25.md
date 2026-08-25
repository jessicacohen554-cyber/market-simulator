# FINDING miso-186 — the MIDWEST-STACK SCARCE-HOUR DIRECTION DIAGNOSIS lands **V-INPUT: a CAMPD-falsified availability input** (the mothball double-count that zeroes a running 580 MW South CC through the entire 2025 scarce set), its zero-parameter repair **FLIPS THE DIRECTION GATES** (S-2: N→S binding 9/47 → 7/47; S-3: +0.286 GW toward the measured record), and the arm is **PROMOTED KEEPER** under the owner posture directive with the scored regression disclosed at full magnitude

**Session miso-186 (2026-08-25).** Executes
`PREREG-miso186-midwest-stack-direction-2026-08-25.md` (committed and pushed
at `3f0d9f0` **BEFORE any adjudicating quantity was computed**; the frozen
instrument at `bf8018d` before it ran; the disclosed fidelity corrections at
`90697e2` and after, each itemized in §7). The queue head per miso-185 §6 —
the last non-owner-decision road at C3a-2025. **LP SPENT under the frozen §4
mapping's own license (V-INPUT):** control + arm `replay_keeper` replays of
`miso177_rho_B` at HEAD, full span, both registered
(`2026-08-25-miso-186-control` / `2026-08-25-miso-186-statusscope`).
**KEEPER CHANGES: `2026-08-22-miso-177-rho-measured` →
`2026-08-25-miso-186-statusscope`** (owner posture directive, §5).
Determination of the new keeper: **NOT-YET on {C3a-2025, C1 fuelmix
CC_REGULAR 2024}**, C6 attested, C8 PASS all years, C3c the single ledgered
caveat. **Matrix cell minted: `unit_outage_fleet_status_scope` = `K`** in
MISO's shard (its new mechanism row + a cell line in every shard landed in
the same push as the field, duty 26(c)).

Instruments: `scripts/probes/_miso186_direction_decomposition.py` →
`results/calibration/_miso186_direction_decomposition.json` (the
decomposition + the §4(v) candidate static reach);
`scripts/probes/_miso186_ab_gates.py` →
`results/calibration/_miso186_ab_gates.json` (S-0…S-5 + the charter kill);
`scripts/gen_miso186_attestation.py` (the keeper attestation, ledger 34
entries / `n_residual` 2 unchanged).

## 0. The verdict

**V-INPUT(`unit_outage_fleet_status_scope`), by the pre-registered mapping**
(PREREG §4): a formation-input deviation clearing all five admissibility
clauses was found in Leg A, its offline static reach (+0.480 GW of 2025
scarce-hour South economic capacity) cleared the 0.25 GW materiality line,
and the licensed A/B passed both structural gates. Under the owner posture
directive — *"If structural integrity improves but gates regress that may
still be a keeper"* (PREREG-miso184 preamble, 2026-08-24; re-affirmed in
writing this session with *"plz promote"*) — the arm was promoted with the
scored regression reported at full magnitude (§5), never claimed as
improvement.

## 1. The decomposition (no LP; the headline table)

On the frozen 2025 scarce set (47 h; 2023/2024 concurrence 11/14), from the
committed keeper sidecars + the `model_year` input rebuild + the measured
rf_al/sr_gfm record (all footing gates passed: C3a reproduced to ±0.0001 pp,
the classifier composition 9/0/38 exact, `N_S` scarce means to ±0.001 GW):

| GW, 2025 scarce mean, surplus-positive | value |
|---|---:|
| measured South surplus `H_meas = G_S − L_S` | **+2.441** |
| model physical ceiling `H_cap` | +2.260 |
| model economic surplus at `π_MW` `H_econ` | **−1.354** |
| bridge: load leg `D_S − L_S` | −0.474 |
| bridge: generation leg `G_S − EconCap_S(π_MW)` | **+3.575** |
| bridge: reserve held (South family) | +0.694 |

The model's South is a 1.35 GW net **demander** at its own Midwest price
(π̄_MW = $73.37 scarce) where the real South was a 2.44 GW source at ~$40 —
the direction error is ~3.8 GW of South balance, and its formation is
generation-side:

* **Leg L (load) — EXONERATED.** ΔD_wiring = 0.000 exactly (the EIA-930
  sub-BA hourly share path is faithful); ΔD_source = −0.474 GW sits inside
  the ±1h alignment envelope (+0.079/−0.775) and runs the WRONG WAY for the
  object (the model already gives the South *less* load than measured). No
  candidate.
* **Leg A (availability).** Model South available capacity vs measured
  generation, scarce mean: Gas **19.34 vs 19.97** (dA +1.083), Nuclear
  **4.72 vs 5.08** (+0.441, all five reactors at a uniform 0.897), Coal
  2.85 vs 2.94 (+0.212), Solar 1.34 vs 1.52 (+0.224). Reality's fleet
  out-generated the model's *availability* — the defect class rule 14 names.
* **Leg M (mc-idled).** 3.61 GW of South capacity available but priced above
  π_MW: ST_GAS 1.39, CT_PEAKER 1.09, oil 0.74, CC 0.66 — the top offer
  tranches; attribution to multipliers is the EXHAUSTED offer family
  (miso-179/180) and is V-FORMED territory, reported not touched. Marginal
  identity: the model clears BOTH regions on CT_PEAKER at $73–75 where
  reality ran the South gas-CC-marginal at ~$40 against a $479 Midwest.
* **Legs R/S (report-only).** South zonal reserve family holds 0.694 GW
  (req 0.693, dual $1.3); the registered seam ladder implies only ~0.27 GW
  of South import at π_S offline (the LP's committed seam behaviour is the
  miso-174/184 record, unchanged). A Midwest-side observation for the
  record: the capacity-weighted delivered gas price of the MISO-Illinois
  gas fleet reads $8.22/MMBtu scarce (other Midwest zones $2.7–3.6) — an
  F923 plant-level delivered-price artifact worth a look in the Midwest
  lane; direction-irrelevant here (it *raises* π_MW).

## 2. The defect, adjudicated to its mechanism (clause (i))

`_unit_outage_factors_from_events` derates a plant's
`(plant_code, plant_group)` fleet bin by `unit_capacity_mw /
cap[fleet basis]` for EVERY detected unit window at the facility — including
units the fleet does not model because their EIA-860 operable `Status` is
non-OP (the fleet loader keeps `OP` rows only). A mothballed unit's terminal
CEMS darkness is then a **double-count**: its capacity is already absent
from the denominator AND its "outage" derates the units that remain.

**Cottonwood (55358, MISO-South), the adjudicated case.** EIA-860 2025
lists CT1/CT2/ST1/ST2 as `OA` (2023/2024 vintages: all eight `OP`) — the
model correctly carries only the OP half, 580.4 MW. The two OA trains' 2025
wind-down windows (CT1 out from mid-April, CT2 from mid-June, each 358.4 MW
CAMPD capacity) sum to 1.23 of that 580.4 MW and clip the modeled plant to
**availability 0.0 July–November** — monthly factors
`[1.0, .69, .15, .01, .11, .15, 0, 0, 0, 0, 0, .12]`. The plant's own CAMPD
record: the OP trains (CT3/CT4) generated in **47/47** of the 2025 scarce
hours, mean **525.8 MW** (min 384), 8,356 running hours in the year. The
model's input is falsified by the same source it was derived from.

The full dropped-event audit under the repair (every row's unit exactly
name-matched to a non-OP generator; unmatched rows fail open so
retired-within-window units keep their windows): Cottonwood 55358 CT1/CT2
(`OA`), Waterford 1&2 8056 unit 4 (`SB` — a year-round ~10 % South ST_GAS
derate), Valley (WI) 4042 unit 3 (`SB`, 69 MW, Midwest), Warrick 6705 unit 2
(`OS`, 2023/2024 only). Per-year availability deltas of the armed filter:
2025 South +0.480 GW scarce (Midwest +0.004); 2024 +0.184/+0.151; 2023
+0.008/+0.012.

## 3. The candidate screen (frozen §4) and the second candidate

Mechanical clause-(v) screen (2025 static reach ≥ 0.25 GW): **A_Gas 1.083**
and **A_Nuclear 0.441** cleared; L legs and A_Coal/A_Solar did not. Clause
(i)–(iv) adjudication:

* **`unit_outage_fleet_status_scope`** (the A_Gas drill's named defect):
  (i) falsified by CAMPD ✓; (ii) EIA-860 status is a forward input ✓;
  (iii) no adjudicated cell — new mechanism ✓; (iv) a load-time scope, no
  re-derivation, zero parameters ✓; (v) exact armed reach **+0.480 GW** ✓.
  **Selected** (largest reach).
* **The MISO measured-nuclear availability layer** (the A_Nuclear drill):
  the uniform 0.897 is the STATIC seasonal pattern × (1−EFORD) — MISO has
  no `NUCLEAR_MONTHLY_CF_BY_YEAR` entry, no `nuclear-availability-MISO.csv`,
  and is absent from `NRC_TO_EIA`, while PJM (pjm-nuc-1b, owner-ordered),
  NYISO (nyiso-98), CAISO (caiso-148) and NEISO (neiso-71) all carry the
  NRC-daily overlay. The NRC scarce-date record: South fleet
  capacity-weighted **0.954** vs the 0.897 smear (reach **+0.299 GW**,
  clears (v)); Midwest 0.885 vs 0.897 (−0.075 GW — the smear also
  under-derates the Midwest's real concentrated outages: Callaway 68.9 %,
  Clinton 77.2 %, Monticello 86.8 %). Clears every clause; **not armed**
  (single-delta discipline; the frozen selection rule picks the larger
  reach). **Handed to the queue as the named next arm.**
* Magnolia Power (67005): NOT a defect — EIA-860 stamps COD 12/2025 and
  CAMPD 2025 carries no rows for it; the model's December-only availability
  matches its source. Reported against the initial suspicion.

## 4. The A/B (PREREG-miso184 §6 gates verbatim; record `_miso186_ab_gates.json`)

| gate | result |
|---|---|
| S-0 control inertness | **PASS** — max\|diff\| = 0.0 on every scored sidecar of every year vs the committed keeper |
| S-1 exactness | **PASS** — single delta in `run_config`; Cottonwood 2025 scarce dispatch 0 → **448.7 MW** (CAMPD-measured 525.8) |
| **S-2 direction** | **PASS** — 2025 scarce N→S RDT binding **9/47 → 7/47** (S→N 0; unconstrained 38 → 40). 2023: 3 → 3; 2024: 1 → 1 |
| **S-3 outflow** | **PASS** — `N_S^m` +0.969 → **+0.682 GW** (move +0.286 ≥ 0.1 toward the measured −2.441; zonal balance verified, max residual 0.0012 MW) |
| charter kill | **SILENT** — C3a-2025 *worsens* while both structural gates pass: the exact opposite of the level-adder signature |
| S-4 conduct | **PASS** — zero D-4 fails, zero new; C8 PASS all years (2025 ST_GAS grounded-above-budget note carries over) |
| S-5 full magnitude | C3a: 2023 +1.28 → +1.22, 2024 −4.06 → **−4.67**, 2025 −11.75 → **−12.32 %**; ONE flip: C1 fuelmix CC_REGULAR 2024 PASS→FAIL, **+8.09 TWh vs ±8.00** (control +6.65); 2023/2024 stay inside ±10; escalation FIRED → resolved by the owner directive (§5) |

The S-3 control row is itself a new committed measurement: the keeper's 2025
scarce South boundary-complex net inflow is **+0.969 GW** exactly — inside
miso-183's declared interval [−1.508, +2.629] and 0.6 GW above its interval
mid; the direction object's model-side size is now measured, not bracketed.

## 5. The promotion (owner posture directive)

The owner's directive, in writing twice (PREREG-miso184 preamble 2026-08-24;
this session live: *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still
be a keeper."*), resolves the S-5 split. The recommendation was YES on
rules 1/14: the control **is now known to carry a CAMPD-falsified
availability input**, so it is no longer the most structurally faithful run;
the arm restores the measured record, flips the direction gates the charter
existed to flip, and adds zero degrees of freedom. The scored costs are
accepted and disclosed, never claimed as improvement:

* **C3a-2025 −11.75 → −12.32 %** — restoring 0.48 GW of real cheap South
  supply lowers prices the model already under-prices. Rule 14's own
  reading: the estimate (the phantom outage) was silently compensating for
  the adjudicated flat-stack/tail defect; the accurate input re-exposes it.
* **C1 fuelmix CC_REGULAR 2024 +8.09 vs ±8.00 TWh** — the restored real
  capacity tips a class the model already over-dispatches (+6.65 in the
  control) 0.09 TWh past the band edge.
* LOYO 2023–2025: the mechanism has **zero fitted parameters** and its
  identification (a published status sheet) is year-independent — no year's
  parameter was identified against any year's outcome; per-year effects
  are the table above.
* DOF ledger: 34 entries, `n_residual` **unchanged at 2**; the new entry is
  MEASURED with 0 lineage solves (`gen_miso186_attestation.py`).

Promotion mechanics executed: `keepers/MISO.json` re-keyed (prior note
archived as `superseded_promotion_note_miso177`), `status/MISO.js` rebuilt
(`build_status.py --iso MISO`), matrix §5.4 header + queue stamp + MISO
shard re-stamped (`check_mechanism_matrix.py` clean), calibration-log entry
appended, calibration-keeper-auditor fired on the shard edit. MISO holds no
`complete`/`final` marker, so no rule-22 D-5(b) re-key is owed.

## 6. What the direction object is after the repair

The repaired keeper still runs the wheel the wrong way in 7 of 47 scarce
hours and still holds +0.68 GW INTO the South against the measured
−2.44 GW out — the repair recovered **0.29 GW of a ~3.6 GW object**. The
remaining formation, per §1, is (a) the named nuclear-availability arm
(+0.30 GW static, both sides direction-correct), and (b) the ~3.6 GW
mc-idled block, which is the EXHAUSTED offer family and the adjudicated
flat-stack/tail model-class residual — i.e., after (a), the remainder folds
back into the standing D-4 posture question with the ~1.3 GW scarce-export
concession (miso-184 GAP), unchanged in kind but now smaller in the
direction dimension. The miso-183 falsifiable prediction stands for every
future candidate: flip the scarce-hour RDT direction toward the measured
32/47 S→N record.

## 7. Reported against interest

* **Three instrument-fidelity corrections**, each committed with its own
  disclosure before re-running (the miso-184 §1 pattern): (1) the first
  probe run gated F-2 on V2 and STOPped — the imported machinery's own
  committed usage gates V1∧V4 with V2 reported ("V2 report-only drifts with
  the keeper lineage as expected", FINDING-miso178 §6); (2) the PREREG's
  fuel-family crosswalk was spelled in the sidecar klass vocabulary and
  attributed South coal/nuclear to "Other" on the first run — re-keyed to
  the fleet's actual `fuel_type` vocabulary, same intended partition;
  (3) the S-3 balance identity initially omitted the LP's own zonal storage
  term (46 MW spurious residual) — completed from the zone-resolved root
  `storage.parquet`. No threshold moved in any of the three.
* **The PREREG §6 provisional cell name** (`miso_south_availability_repair`)
  was superseded by the code-truthful field name
  `unit_outage_fleet_status_scope` — the mechanism is not South-specific
  (its 2024 effect is half Midwest) and CI keys matrix rows to
  `ScenarioConfig` field names. Naming deviation, disclosed; no frame or
  threshold change.
* **The S-2 movement is 2 hours of 9** and S→N binding remains 0/47 — the
  direction gates are passed at their declared lines, not "solved"; §6
  states the honest remainder.
* **C3a worsens in all three years** and a load-bearing criterion-year
  flips; the promotion rests on the owner directive plus rules 1/14, not on
  any scored improvement. The determination basis of the new keeper lists
  TWO failing criteria where the old listed one.
* **The dA_Gas positive-part (1.083) over-states the repairable defect**:
  the armed repair recovers 0.480 GW; the remainder of the gas gap is
  SE-vs-fleet metering wedge (~1 % of 20 GW), real derates (WEFOR/ambient —
  rule-23-frozen against residuals), and measured output exceeding modeled
  available capacity at plants with no identified input defect. Only the
  adjudicated portion was armed.
* **dA_Nuclear (0.441) likewise over-states its candidate** (+0.299 armed
  reach): ~0.05–0.14 GW of it is the SE-vs-nameplate wedge (2023 measured
  nuclear generation exceeds nameplate by 1 %) and the NRC morning-report
  daily grain.
* **The replays carry no `calibration_attestation.json` by construction**;
  both legs scored C6-UNATTESTED until the keeper attestation was generated
  for the arm (the miso-178 §11 phenomenon, same lineage). The control
  remains unattested (a control, never a keeper candidate).
* **Registration prunes** under top-15 retention removed
  `2026-08-19-miso-169-online-gated` and `2026-08-19-miso-170-control`
  (tool-decided; committed with the registrations).
* **The branch was merged mid-session by the owner** (PR #4269, through the
  control registration); the designated branch was restarted from the
  merged main per the merged-PR rule, and later commits carry the
  post-merge lineage.

## 8. Standing OWNER items, restated not decided

(1) the C8 provenance-materiality floor (unrepaired); (2) the
committed-vs-regenerated diagnostics exposure; (3) `RHO_CLIP` 0.5 vs
measured 0.1764 (nyiso-144) — MISO now consumes the measured value, the
cross-ISO band item stands; (4) **D-4 posture — RESHAPED by this session**:
the direction object is 0.29 GW smaller with a named +0.30 GW next arm; the
~1.3 GW scarce-export model-class concession stands behind it; (5) NEW: the
C1 fuelmix CC_REGULAR band question (the keeper now carries a 0.09 TWh
band exceedance produced by restoring real capacity into an over-dispatching
class — repairing it is offer-family/flat-stack territory, adjudicated
exhausted); (6) NEW: the MISO-Illinois $8.22/MMBtu scarce delivered-gas
observation (§1 Leg S note) for the Midwest lane.

## 9. Governance

Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; MISO holds neither marker;
freeze untouched; no re-key owed. Rule 15: BOTH legs registered
(`2026-08-25-miso-186-control`, `2026-08-25-miso-186-statusscope`), the
keeper's hourly sidecars committed. Rule 16: full span, one invocation per
leg. Rule 12: years sequential; legs sequential; the miso-169 memory recipe
(8 GB swapfile, `MARKET_SIM_HIGHS_THREADS=4`). Rules 5/13/14/23/24: the
field is registered (cache-key + pinned default in the field's own commit),
measured-identified, zero fitted scalars, no derive re-run. Rule 26: §5.4
header + queue stamp + MISO shard cell/keeper/gates re-stamp +
calibration-log entry in-session; `check_mechanism_matrix.py` clean before
every matrix push. Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed
blob ≥300 lines verified on both transports. No new `.github/workflows`.
**DO-NOT-REDO honoured throughout** (miso-185 §9 carried in full): nothing
re-opened; the offer family untouched at both grains; the miso-183 basis
adjudication not re-litigated; `ba_code="SOCO"` untouched; the import-side
ladder tail reported (Leg S), not touched.

## 10. Reproduction

```
cd <repo root>
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/probes/_miso186_direction_decomposition.py --candidate-reach
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml,highspy \
  --python 3.12 python scripts/probes/_miso186_ab_gates.py
```

Reads the committed `miso177_rho_B` sidecars, the miso186_dir_A/B bundles,
`data/raw/miso-regional-balance/`, `data/raw/zone-specific-demand/MISO/`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
`data/raw/campd-unit-level/{TX,LA}_2025.parquet`,
`data/raw/campd-unit-outages*-MISO.csv`, `data/raw/eia-860/` (+ vintages),
`data/raw/nrc-reactor-status/2025PowerStatus.txt`. PREREG: `3f0d9f0`;
instrument: `bf8018d`; repair: `0001cca`; gates scorer: `127d449` +
schema-alignment commits. (Pre-merge shas cite the branch history now
reachable through PR #4269's merge.)
