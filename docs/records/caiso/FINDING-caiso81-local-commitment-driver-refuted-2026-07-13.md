# FINDING (caiso-81): the approved local-commitment response curve is REFUTED at the estimation stage — the driver is not year-stable (2025 regime break), no solve run

**Session:** caiso-81, 2026-07-13.
**Adjudication script (committed, reproducible):** `scripts/derive_caiso_local_commitment.py`.
**Design under test:** `docs/handoffs/caiso-local-commitment-driver-design-2026-07.md`
(owner-APPROVED as designed, caiso-80 session) — a per-pocket HE15-23 min-gen
floor on the named LCR-area CT_PEAKER units, sized by a measured response
curve `share_committed(ramp decile, season)` estimated from CAMPD 2023-2025,
driver = the pocket's evening net-load ramp.

## 1. What was tested, and why before any solve

The design's own §4 pre-commits the curve to leave-one-year-out scoring ("the
curve is fitted, unlike the caiso-78 code fix"). That gate is checkable at the
**estimation stage**: fit the curve on two years, predict the held-out year's
pocket committed energy, compare to measured. If the curve itself mispredicts
the held-out year, no LP probe can pass — the LP dispatches *above* the
injected floor, so a floor that over-forces the held-out year is wrong before
the first simplex iteration. This is the same pre-solve honesty-gate rejection
the NYISO ST_GAS net-load drag established (2026-07-09,
`scripts/derive_nyiso_st_gas_netload_drag.py`, recorded in the
`D4_WINDOWS (MECH_RELIABILITY_FLOOR, "ST_GAS")` comment: "its level drifts
across years at equal net-load … REJECTED on its own honesty gates").

Scope: all three LCR pockets with membership crosswalks (Greater Bay inside
NP15; LA Basin and San Diego/Imperial Valley, which since the SP15 local-area
split ARE their model zones). The doc's §3 conditional for including the
southern pockets is met — the caiso-80 keeper's CT deficit GREW (model
CT_PEAKER 0.71/0.56/0.27 vs actual 4.13/4.33/2.37 TWh). Estimation panel:
one row per (pocket, day) — season, driver, measured committed MW = mean
pocket CT_PEAKER CEMS MW over HE15-23 (canonical EIA-923 dominant-class
routing). Driver basis is the model's OWN input series (honest
supply-consistent demand × zone load share − `load_renewable_profiles` VRE
potential), so estimation and any runtime application ride one basis.

## 2. Result — every candidate driver fails LOYO on 2025

Measured pocket committed-window energy (TWh, HE15-23):

| pocket | 2023 | 2024 | 2025 |
|---|---|---|---|
| Greater Bay | 0.353 | 0.287 | 0.041 |
| LA Basin | 1.215 | 0.919 | 0.171 |
| San Diego/Imperial Valley | 0.205 | 0.152 | 0.005 |

LOYO prediction error on the held-out year (curve = mean committed MW per
season × pooled-driver-decile, edges frozen on training years):

| driver | GB 2025 | LA 2025 | SD 2025 | worst in-2023/24 |
|---|---|---|---|---|
| filed: evening net-load ramp | **+761 %** | **+530 %** | **+3,619 %** | −62 % |
| ramp − zone battery MW | **+652 %** | **+439 %** | **+2,938 %** | −63 % |
| ramp ÷ zone battery MW | **+622 %** | **+375 %** | **+2,964 %** | −66 % |

The failure is not a binning artifact. Between 2024 and 2025 the driver
barely moves (LA Basin JJA mean ramp 4.93 → 4.86 GW; GB 5.72 → 5.46 GW —
2025 ramps are the *steepest* of the sample in most cells) while measured
commitment collapses ~80-97 % (LA Basin JJA mean 611 → 105 MW; GB 168 → 13
MW). Even restricted to the steepest-ramp decile days, the share of days
with any commitment falls 81/68/27 % (GB), 97/92/59 % (LA Basin),
68/62/11 % (SDGE) across 2023/24/25 — the response *at equal driver* is what
moved. Within-season Spearman ρ(ramp, committed MW) is −0.2…+0.15 pooled;
the apparent pooled-decile signal is season + year-level confounding, not a
day-level ramp response.

## 3. What broke the driver: a 2025 regime change, not a condition response

Two measured coincidences identify the break (hypothesis, not yet a wired
mechanism):

- **The pocket battery build:** EIA-860 battery power in the pocket zones
  roughly doubled over the sample — LA_BASIN 1.20 → 2.71 → 2.89 GW, SDGE
  0.79 → 1.06 → 1.81 GW, NP15 3.03 → 3.46 → 3.99 GW (system 9.57 → 13.21 →
  17.53 GW). Storage now supplies the evening-ramp local-RA capability the
  CTs were positioned for. But storage capability alone does NOT rescue the
  curve — both storage-conditioned drivers above still fail (the collapse is
  much steeper than the capability growth).
- **CAISO's 2025 slice-of-day RA reform** re-based must-offer and local
  positioning hourly, changing how much thermal local commitment the ISO
  carries at a given ramp — a market-design regime term no load/solar/storage
  driver regenerates.

The pocket fade is also steeper than the ISO-wide CT fade (pocket committed
energy −86 % vs ISO CT_PEAKER CEMS −63 % 2023→2025), i.e. commitment moved
away from the pockets specifically — consistent with in-pocket storage
displacing local commitments rather than a system-wide CT story.

## 4. Disposition (rules 12/13/26)

- **No implementation:** no `ScenarioConfig` field, no injector, no
  `D4_WINDOWS` row, no artifact under `data/raw/reference/` — a refuted
  fitted curve must not persist as a re-armable answer key (rule 26).
- **No solve, no dashboard registration:** nothing was solved; the CT
  local-commitment lane closes as REFUTED-at-estimation, the cheap
  short-circuit of the design's own §4 LOYO pre-commitment.
- **The CT_PEAKER deficit remains OPEN** (4.13/4.33/2.37 vs 0.71/0.56/0.27
  TWh) with no admissible mechanism on file. Re-opening requires a measured
  source that carries the regime term, e.g.: (a) DMM annual-report
  exceptional-dispatch / minimum-online-commitment volumes by local area and
  year (a per-year measured local-commitment series — rule-15 "needs a new
  measured source", the same status as the lane-B cogen host-load split), or
  (b) an RA-framework regime field (slice-of-day effective year is known
  market design, hence forward-native) conditioning the curve, estimated on
  data that spans the regime boundary once post-reform years accumulate.
  `scripts/derive_caiso_local_commitment.py` re-adjudicates from source when
  either lands.
- Note the design doc's own C3c caveat stands: a local commitment floor
  would not have created local prices without a binding constraint, so the
  C3c lane loses nothing that was actually promised.

## 5. Files

- `scripts/derive_caiso_local_commitment.py` — panel construction + LOYO
  adjudication, prints the §2 tables and the REFUTED verdict; re-runnable
  from committed data only.
- Design doc `docs/handoffs/caiso-local-commitment-driver-design-2026-07.md`
  carries a status addendum pointing here.
- Calibration-log entry: caiso-81 (same date).
