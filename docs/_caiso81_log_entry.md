### 2026-07-13 — CAISO — caiso-81 (local-commitment driver adjudication): the approved response curve is REFUTED at the estimation stage — its own §4 LOYO gate fails before any LP (held-out 2025 overpredicted +375 % to +3,600 % by every candidate driver); no solve, no registration; the CT_PEAKER deficit stays OPEN pending a measured regime source

Lane C of the caiso-80 handoff (the owner-approved
`docs/handoffs/caiso-local-commitment-driver-design-2026-07.md`, sized against
the caiso-80 payload's GROWN CT deficit — model 0.71/0.56/0.27 vs actual
4.13/4.33/2.37 TWh). The design's §4 pre-commits the fitted response curve
`share_committed(ramp decile, season)` to LOYO within 2023-2025; that gate is
checkable at the ESTIMATION stage, before any solve — the NYISO ST_GAS
netload-drag precedent (2026-07-09, rejected on its own honesty gates from
the derive script). It fails decisively
(`scripts/derive_caiso_local_commitment.py`, committed + reproducible;
`results/calibration/FINDING-caiso81-local-commitment-driver-refuted-2026-07-13.md`):

- **Panel:** per-(pocket, day) measured committed MW (CAMPD CT_PEAKER via the
  canonical 923 dominant-class routing, HE15-23 mean) vs the filed driver
  (pocket-zone evening net-load ramp on the model's OWN input basis — honest
  supply-consistent demand × zone share − VRE potential), all three LCR
  pockets (GB inside NP15; LA_BASIN/SDGE are their zones since the SP15
  split; the doc's §3 southern-pocket conditional is met, the deficit grew).
- **Measured committed-window energy collapsed in 2025 at equal-or-steeper
  ramps:** GB 0.353/0.287/0.041 TWh, LA Basin 1.215/0.919/0.171, SDGE
  0.205/0.152/0.005 (2023/24/25), while LA-Basin JJA mean ramp went 3.5 →
  4.9 → 4.9 GW. Steepest-ramp-decile days committed: GB 81/68/27 %, LA
  97/92/59 %, SDGE 68/62/11 %. Within-season day-level ρ(ramp, MW) is
  −0.2…+0.15 — the pooled decile signal was season/year confounding.
- **LOYO on the curve itself:** held-out-2025 prediction error — filed
  driver +761/+530/+3,619 % (GB/LA/SD); the storage-conditioned rescue
  variants (ramp − zone battery MW, ramp ÷ battery) still +375 % to
  +2,964 %. In-window years also miss up to −66 %. No driver in the
  admissible family survives; a floor that over-forces the held-out year is
  wrong before the first simplex iteration (the LP only dispatches above it).
- **Diagnosis (hypothesis, measured coincidences):** a 2025 regime break —
  pocket batteries doubled (LA_BASIN 1.20→2.89 GW, SDGE 0.79→1.81, system
  9.57→17.53 GW; EIA-860 via the model loader) and CAISO's slice-of-day RA
  reform re-based local positioning hourly. The pocket fade (−86 %) is
  steeper than the ISO-wide CT fade (−63 %): commitment moved away from the
  pockets specifically. A load/solar/storage-capability driver cannot
  regenerate a market-design regime term (rule 13's "would it respond to
  changed conditions" cuts both ways).
- **Disposition (rules 12/13/26):** no `ScenarioConfig` field, no injector,
  no D4_WINDOWS row, no reference artifact — a refuted fitted curve must not
  persist re-armable. Design doc carries a REFUTED status banner. Re-open
  requires a measured per-year local-commitment series (DMM
  exceptional-dispatch / minimum-online volumes by local area) or an
  RA-regime field estimated across the regime boundary; the committed derive
  script re-adjudicates from source when either lands.
- **Open after caiso-81** (rule-1 order, unchanged otherwise): (i) the C3a
  2024/25 body overprice (soft-month margin composition), (ii) ~~CT
  local-commitment driver~~ CLOSED-REFUTED (this entry — the CT deficit
  itself stays open, mechanism-less), (iii) the 2023 flat-wedge split
  (needs a new measured source), (iv) C3c local-tail formation + the 2023
  spurious-tail regression, (v) PJM/NYISO/NEISO re-gate on the fixed
  `fleet_to_bins`.
