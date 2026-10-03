# FINDING — NWPP-NEXT-24 phase 0 (zero LP): no forward-admissible driver of the COI economic depth

Probe: `scripts/probes/_nwppnext24_coi_depth_phase0.py` (§A–§C). Inputs: CAISO OASIS `TRNS_USAGE` DAM
(`data/raw/caiso-trns-usage`, 2023-06-19 → 2025-12-31), the measured CISO↔BPAT/PACW EIA-930 legs
(`NWPP_PRICED_SEAM_LEGS["CAISO_COI"]`), the measured MALIN LMP and the NW WEIM benchmark (validation only), keeper
`2026-10-03-nwpp-next-23-coi` committed `hourly/system_<Y>`. No LP. The DAM schedule (`ENE_IMPORT_MW`) is a market
outcome: here it is a diagnostic only (data README, rule 13).

## §A. What OASIS publishes on the CAISO side of COI (NW→CA = CAISO "I")

| year (h) | measured CISO leg MW | DAM sched Malin+Cascade MW | r | OTC MW | unsched TR MW (p10/50/90) | OTC − TR |
|---|---:|---:|---:|---:|---|---:|
| 2023 (4,705 h) | 149 | 712 | 0.774 | 2,786 | 379 (305/399/430) | 2,407 |
| 2024 | 245 | 822 | 0.792 | 2,751 | 620 (377/618/954) | 2,130 |
| 2025 | 346 | 863 | 0.770 | 2,740 | 816 (509/851/1,087) | 1,924 |

- `MKT_XFER_CAP_MW` = OTC exactly (TRM 0). `USEAGE_MW` is OASIS's "Hourly unscheduled TR capacity": the unscheduled
  part of ETC/TOR transmission rights. `ATC = OTC − schedule − unscheduled TR` to the MW.
- The DAM schedule reaches 95 % of `OTC − TR` in only 2.4 / 8.4 / 7.1 % of hours and 95 % of OTC in ≤ 0.4 %.
- NOB (PDCI, CAISO share) schedules another 370–412 MW. COTP schedules 17–52 MW.
- The CISO-leg metered flow sits 255–800 MW below the DAM schedule in every spread bin. Real-time and WEIM transfers
  (BPAT joined WEIM in May 2022) net against the day-ahead import. The midday solar export shows in the meter
  (−250 to −340 MW at hod 10–14) while the schedule stays +470 to +600 MW.

## §B. Flow vs spread on the schedule as well as the meter (validation, never a source)

Mean MW by measured MALIN − NW spread bin ($/MWh):

| | ≤ −10 | −10…−5 | −5…0 | 0…5 | 5…10 | 10…15 | 15…20 | 20…30 | > 30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024 DAM schedule | 198 | 668 | 766 | 775 | 898 | 953 | 1,022 | 998 | 1,103 |
| 2024 meter | −474 | −136 | −35 | 103 | 348 | 486 | 617 | 569 | 825 |
| 2025 DAM schedule | 281 | 574 | 685 | 809 | 988 | 1,060 | 1,007 | 963 | 822 |
| 2025 meter | −366 | −174 | −58 | 193 | 483 | 634 | 657 | 699 | 567 |

(2023 has the same shape: schedule 212 → 1,066, meter −506 → 787.)

**Reading.** The saturation is not a metering artefact. CAISO's own day-ahead book also tops out near 1,000–1,100 MW
at any spread ≥ $15, against an OTC of about 2,750. Even with the NW price $10 above MALIN, 200–700 MW is still
scheduled south. That is a spread-insensitive base (CAISO's RA/firm imports; `PNW_hydro_base` 1,072–1,566 MW on
CAISO's side) with an economic slope of only 300–500 MW above it. The depth is on the **supply** side: NW sellers did
not have the surplus. No published transmission quantity binds it.

## §C. Candidate drivers, each against rules 13, 14 and 19

| candidate | evidence | verdict |
|---|---|---|
| ETC/TOR set-aside (OTC − unscheduled TR) | Price-taker on the keeper's NW price: COI −0.40 / −2.13 / −2.06 TWh (2023–25), about 60 % of that in the LP. It leaves 1,900–2,400 MW of headroom, about 2× the measured DAM saturation. No data before 2023-06-19 (OASIS retention), so 2019–22 and 2023 H1 are untouched. The hourly value is the TR holder's scheduling choice (p10–p90 spans 2–3×), an outcome rather than a contract MW. The entitlement total, which would be the forward-admissible object, is not published. | **Not a depth driver.** Partial and admissibility-ambiguous (rule 13). Not proposed. |
| CAISO firm-import block (`CAISO_FIRM_IMPORT_TRANCHES`) | Shows as the spread-insensitive DAM base. It *adds* southbound flow and cannot limit it. On NWPP's side, a firm block would be a scheduled leg, and the priced seam would keep the economic remainder. | Not a depth limiter. Rule 19 is satisfied today: the COI seam is priced and never scheduled. |
| BPA load-service obligation / the path-vs-leg ratio | Already absorbed in NEXT-22 (CAISO's own Malin/Cascade OTC replaces 2/3 × the path). | Closed (NEXT-22). |

**Conclusion.** The residual COI over-export is not a transmission-quantity error. The model's NW has more surplus
priced below `(anchor − wheel)/(1 + loss)` than the real NW had. Gas CC fills it (C1 CC_REGULAR +8 to +15 TWh), and
the NW price is a hydro water value 27.9 % below the benchmark in 2024 (FINDING-nwppnext23 §C). The next lever is the
NW price and energy formation (C3a 2024, hydro water value), not the seam.

## Routed

- Owner card: close the seam-depth lane and pivot to C3a 2024, or solve the ETC/TOR arm as a partial.
- The data drift (#7134 coal stocks; SolveEpoch 2026-10-03b NWPP nuclear rows) needs a 7-shard replay of the keeper
  recipe at main HEAD regardless of the card. That replay is a rule-14 data re-solve and is promotable on structure.
