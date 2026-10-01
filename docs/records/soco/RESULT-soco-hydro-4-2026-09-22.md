# RESULT — SOCO hydro-4: hydro dispatch physics (2026-09-22)

Pre-registration: `PRECOMMIT-soco-hydro-4-2026-09-22.md` (+ addendum A), pushed before any solve at
`a5e5f237` / `4b6c6d96` (since merged to `main`; SHAs are provenance, rule 33(d)). Control: keeper
`2026-09-22-soco58-warm-committed`, form 4 — no control solve for 2023/2024; for 2025 the control is
the repair-only leg `soco_h4_fix_2025` (addendum A). Parent LP cost: zero. 7 shards, ~9 min each.

**Registered PROBES** (rule 15): `2026-09-22-soco-h4-hydro-min` (ARM 1) and
`2026-09-22-soco-h4-hydro-ror` (ARM 2). Both NOT-YET on C1 — the keeper's own 2024 CC_REGULAR
over-dispatch, unchanged in status.

## 1. Gates

| | ARM 1 `hydro_min_flow_floor` | ARM 2 `hydro_ror_split` |
|---|---|---|
| **G1 liveness** | PASS all 3 yrs — floor 266 / 197 / 213 MW-avg, every month's min ≥ its floor | PASS all 3 yrs — 277 / 250 / 250 MW-avg flat |
| **G2 invariant** | 0.0000 % all 3 yrs | 0.0000 % all 3 yrs |
| **G3 zero-MW hours** (control → arm; measured 0) | 1,674 → **0**; 1,962 → **162** ‡; 1,949 → **0** | → **0 / 0 / 0** |
| **G3 top-decile share** (control → arm; measured) | 0.342 → 0.323 (0.176); 0.303 → 0.286 (0.171); 0.364 → 0.328 (0.140) | 0.342 → **0.275**; 0.303 → **0.246**; 0.364 → **0.291** |
| share of the gap to measured closed | 11 / 13 / 16 % | **40 / 43 / 33 %** |
| **p95 MW** (control → arm; measured) | 3,268 → 3,068 (2,357); 3,128 → 3,082 (2,257); 3,198 → 3,072 (1,675) | → **2,581 / 2,508 / 2,486** |
| **G4** C1 / C2 / C4 / C8 | no status flip; gas r +0.005–0.009 | no status flip; gas r +0.006–0.012 |
| 2025 model mean price (repair-only control $38.88) | $38.93 | $53.08 — 2 h scarcity, §3 |

‡ Dec 2024: EIA-930 SOCO `NG: WAT` is missing 2024-11-25 → 12-31 (1,343 h), so
`measured_hydro_min_flow_level` returns 0 for the empty month and December carries no floor. The
pooled fallback only triggers for a wholly-empty YEAR. Recorded, not repaired.

C3a/C3b are SKIPPED by the rubric: SOCO has no price benchmark. 2025 C1/C2 are data-blocked
(preliminary EIA-923) in every SOCO run.

## 2. Which arm — on the driver, not the criterion (rule 1)

**Recommendation: ARM 2.** Its driver is per-plant and external: 17 of 45 SOCO plants carry an ORNL
EHA `Mode` of Run-of-river or Canal/Conduit (Alabama Power's lower Coosa dams — Lay, Mitchell,
Jordan, Walter Bouldin — plus Corps Millers Ferry and Holt, and others), 94 % of energy is classified
by direct label. Those plants physically cannot shape output within a month, and the model was
letting them. ARM 1's driver is a fleet aggregate — the monthly Q05 of an EIA-930 series that is
pumped-storage-folded before 2024-07-15 and has a 5-week gap — which bounds the bottom of the fleet
but says nothing about *which* plants can move water in time.

The measured data backs this reading without being the reason for it: ARM 2 moves p95 and top-decile
share much closer to measured; ARM 1 removes the zeros and leaves the peaking almost untouched.

**Neither arm closes the defect.** Even under ARM 2, top-decile share is 0.25–0.29 against 0.14–0.18
measured. The remaining 65 % of energy (reservoir class) still carries month-long perfect foresight.
The two mechanisms are one family and `build_hydro_fleet` already reconciles them (the floor is
reduced by the RoR base and put on the reservoir class). A reconciled ARM 1 + 2 arm is a real
follow-up. It was not run here because this lane's brief forbade stacking.

## 3. ARM 2's 2025 scarcity is a demand finding, not an arm defect

Hours 5030–5031 (2025-07-29 afternoon): 287 MWh unserved at $61,900. Every thermal class is at its
ceiling in both the control and the arm. The control covered the gap with **3,258 MW** of hydro,
98 % of the fleet's nameplate. SOCO's measured hydro that hour was **762 MW**, and its 2025 maximum
over the year was **2,204 MW**. ARM 2's ceiling (2,469 MW) is still above anything measured.

What is actually short is supply against demand. **Model demand is 51.3 GW that hour vs EIA-930's
46.2 GW (+11 %); 2025 annual model/930 = 1.055 and peak 51.3 vs 46.5 GW (+10.3 %)**, against
1.044 / 1.045 annual and +1.6–3.5 % at the top-100 hours in 2023/2024. The faithful hydro
representation exposes the 2025 demand excess; the unconstrained one had been absorbing it.
**Routed** as a SOCO demand-basis question.

## 4. Other findings, routed

1. **SOCO-53b is owned by SOCO-59**, which merged a PRECOMMIT the same day with the better instrument
   (`hydro_backfill_year=2024` + `hydro_eia930_monthly`, 5.93 TWh measured, plus
   `EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025`). This lane's 2025 legs use backfill only
   (6.33 TWh, +6.8 %) as a stand-in so the arms were testable. **If SOCO-59 lands first, the 2025 arm
   legs should re-solve on its repair before any promotion.** The zero-MW numbers above for 2025 do
   not depend on which repair is used. The top-decile share will move slightly.
2. **SOCO's committed bench parts carry a pumped-storage-folded hydro actual.** A fresh
   `--rebuild-benchmark` at HEAD writes 2023/2024 `classFull.hydro` = 6.815 / 6.301 TWh (EIA-923 HY);
   the committed `bench/SOCO/{2023,2024}.json.gz` carry 8.4465 / 7.0798 (the EIA-930 `WAT` values).
   The lane did **not** commit the rebuilt parts, because they are shared by every SOCO run. Scored
   records were verified identical with and without them.
3. **C8/D-2 reports 0.0 % forced for hydro in both arms**, even though G1 shows the floor and the flat
   levels binding. D-2 does not currently attribute the hydro `min_gen` stamps. The forced share is
   ~27–36 % of hydro energy by construction. Hydro is < 2 % of load, so it is ungated either way,
   but the diagnostic under-reports it.

## 5. Retrievability (rule 34(e))

The registered composites `results/calibration/soco_h4_{mff,ror}_span` (slim set, committed with this
RESULT) carry every hourly sidecar. The per-year legs are gitignored on the parent's disk (rule 31),
and their full bundles came from the shard branches:

| leg | commit |
|---|---|
| mff 2023 | `5a85c8b8730c699fbe94d186fe57950152f780ad` |
| mff 2024 | `67e2232073c8d5d5ec4b537e59181eac2a198070` |
| mff 2025 | `e12a8d9dbb27bcf045ebab94f5b206c1c1caf5a6` |
| ror 2023 | `ba61f3135a4407243054ede9530690401d1b7ce9` |
| ror 2024 | `f2511588a57dbdd97a960c2c010ed6a7478cac8f` |
| ror 2025 | `9d113ba2a8784321edae35d59b2605d0be80b616` |
| fix 2025 | `95d058b30a9d59f8be35efca0b6f95761245ecf4` |

These are provenance only: shard branches are transport (rule 33(f)). Promoting either arm needs a
re-solve of the leg's full `dispatch/` layer only if this session's disk is gone (~9 min per leg,
3 legs). The 2025 legs likely re-solve anyway, per §4.1.
