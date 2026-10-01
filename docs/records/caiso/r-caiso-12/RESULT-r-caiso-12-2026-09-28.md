# RESULT — R-CAISO-12 (2026-09-28): the "h15–17 import surplus" was two benchmark artifacts; no admissible lever

**Keeper unchanged:** `2026-09-28-caiso-r11-tacpst` (CALIBRATED, single ledgered C3c 2024). Fold
`2026-09-28-caiso-r11-tacpst-touchpoints` stays NOT-YET, reported only (rule 30(c)).
**Zero LP.** No shard was launched, nothing was armed or registered, and no matrix cell verdict moved.

**Probe:** `scripts/probes/_rcaiso12_import_census.py` → `results/calibration/_rcaiso12/import_census.json`.
Every number below comes from that JSON. The legs were read from the R-CAISO-11 shard commits (SHAs in
RESULT-r-caiso-11 §7, provenance only per rule 33(d)).

## 1. The handoff premise does not survive re-measurement

R-CAISO-11 §6 stated two things. Both came from mismatched benchmarks:
- "h15–17 the model imports +1.0–2.1 GW more than EIA-930."
- "and runs 3–5 GW less gas."

| Claim | What was wrong | Re-measured (Jun–Sep, 2022–25) |
|---|---|---|
| Import surplus at **h15–17** | EIA-930 interchange is hour-ending **prevailing** time; the model clock is fixed-PST hour-beginning. That is a 1–2 h offset in summer. | On the model clock (`_caiso_interchange_model_clock`), the surplus is **h8–16** (+0.4 to +2.5 GW) and turns negative from h17–18 |
| **3–5 GW less gas** | Compared against the EIA-930 CISO `NG` cell, which is **registered corrupt** (`EIA930_NG_CELL_CORRUPT`, onset 2023). The scorer does not use it. The 2025 cell reads 79.0 TWh against CEMS grid gas 44.4 + cogen 6.4 TWh. | Against CEMS (C4's basis), model gas is **−0.4 to −1.5 GW at h8–16** and **+0.2 to +1.9 GW at h19–21** |

Model minus EIA-930 net import, GW, on the model clock:

| hod | 8 | 12 | 14 | 16 | 17 | 18 | 20 | 22 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2022 | +1.3 | +1.5 | +0.8 | +0.4 | −0.4 | −2.1 | −3.3 | −2.6 |
| 2023 | +2.1 | +2.5 | +2.3 | +1.9 | +0.8 | −0.7 | −1.7 | −1.9 |
| 2024 | +1.4 | +1.6 | +1.3 | +0.9 | +0.1 | −0.4 | −0.7 | −0.7 |
| 2025 | +1.2 | +1.7 | +1.8 | +1.2 | +0.6 | −0.5 | −0.8 | −1.0 |

**Consequence:** the evening under-price is not a gas shortfall. The model runs **more** CEMS gas than measured in
the evening and still prices below DAM. That points at price formation, not at imports displacing gas.

## 2. Which tranche carries the midday surplus

Per-tranche P1 dispatch, Jun–Sep mean GW (2024; the other years have the same pattern):

| Tranche | h8 | h12 | h16 | h18 | h20 | h22 |
|---|--:|--:|--:|--:|--:|--:|
| `DSW_daytime_clean` (caiso-94, window 6–21) | 1.38 | 1.14 | 0.86 | 0.12 | 0.03 | 0 |
| `DSW_surplus_clean` (caiso-87) | 0.51 | 0.30 | 0.12 | 0 | 0 | 0 |
| `DSW_solar_PV` + `PNW_hydro_base` (firm, measured shape) | 2.52 | 0.78 | 2.10 | 3.38 | 4.29 | 4.46 |
| `DSW_lateevening_clean` (caiso-269, hod 22–23) | 0 | 0 | 0 | 0 | 0 | 0.43 |
| `PNW_midC`, `DSW_CCGT`, `DSW_CT`, scarcity | 0.09 | 0.43 | 0.33 | 0.09 | 0.01 | 0 |
| **Export legs (MALIN, PALOVRDE)** | **0** | **0** | **0** | **0** | **0** | **0** |

- The midday surplus sits in the two **at-hub WEIM clean rungs**, both cell `K`. Their depth is a p95 capability,
  priced at the measured Palo Verde DAM + wheel.
- The export legs clear **0 MW in every hour of every year**. Measured PNW runs net **export** at midday
  (−1.2 GW at h12 in 2023, −0.7 GW in 2025). The model cannot reproduce that.

**Import volume mirrors the model-vs-DAM price error.** Import offers are the measured intertie DAM LMP + wheel, so
imports rise where the model price sits above that LMP (midday) and fall where it sits below (evening). The
correlation between the two hour-of-day profiles is r = 0.85 / 0.40 / 0.65 / 0.81 (2022–25). Hourly it is weak
(0.04–0.32), because the firm blocks are floored.

## 3. Lever check against DO-NOT-REDO

| Candidate | Verdict |
|---|---|
| Let the model export at midday | Adjudicated: `caiso_p1_export_sink_seam` R, `caiso_corridor_export_path` R, `caiso_node_export_constraint` G |
| Re-size the clean-rung depth (p95 → another percentile) | Picking a percentile by fit is rule 1 fitted selection. The rungs are `K` and their p95 identification is cited. Refused |
| Reshape firm imports per corridor | Excluded by the handoff |
| Evening offer levels | Already measured from CAISO public bids (caiso-283 closed the offer-basis route) |

**No admissible lever on Object 1.** The residual is the model's diurnal price compression, seen through
price-elastic imports. It is not an import-model defect.

## 4. Object 2 — the fold

Model vs EIA-930 annual corridor net import, TWh:

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW model / EIA-930 | 21.3 / 44.7 | 17.4 / 42.0 | 29.7 / 40.9 |
| DSW deficit | −23.4 | −24.6 | −11.2 |
| PNW model / EIA-930 | 16.8 / 9.2 | 21.5 / 17.4 | 16.6 / 13.6 |
| C1 CC_REGULAR excess | +23.0 | +25.2 | +10.6 |

- Object 1 does **not** explain the fold. It has the opposite sign: a midday surplus in 2022–25 versus an all-hour
  DSW **deficit** in 2019–21.
- The DSW deficit matches the CC excess almost one for one. The clean rungs cannot arm in 2019–20 without a
  measured hub price. That is the standing STOP (R-CAISO-7), and it stands.

**New evidence on the STOP.** The only non-OASIS measured source for 2019–20 found is the ICE daily on-peak index
(EIA wholesale archive). It fails as a reconciled substitute (rule 14):

| Palo Verde (ICE vs OASIS DAM on-peak) | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|
| r | 0.49 | 0.85 | 0.88 | 0.86 | 0.74 |
| ICE − OASIS ($/MWh) | +17.1 | +11.9 | +18.0 | +7.9 | +6.8 |

- It covers about 180 on-peak days a year, with no hours and no off-peak.
- The bias against the intertie LMP drifts by year: +7 to +18 $/MWh at Palo Verde, and −0.7 to +28 at Mid-C.
- Using it would need a per-year fitted basis, which rules 1 and 13 forbid. **The 2019–20 STOP stands.**

## 5. What remains open

- **Evening price formation.** Model gas exceeds CEMS at h19–21, yet the price is below DAM. Battery discharge
  timing (about 1 h late vs the CAISO Outlook series, R-CAISO-11 §2) and caiso-253's re-point of the 22–23 gap at
  storage are the only un-adjudicated leads.
- **Fold 2019–20:** data-blocked, no route found. 2021: the DSW deficit remains after R-CAISO-8's partial-year
  pricing.

## Retrievability (rule 34(e))

Nothing was solved. The census JSON and the probe are on this branch. The legs it reads are local-only, gitignored
extracts of the R-CAISO-11 shard commits. Their SHAs are provenance, not a recovery route (rule 33(d)).
