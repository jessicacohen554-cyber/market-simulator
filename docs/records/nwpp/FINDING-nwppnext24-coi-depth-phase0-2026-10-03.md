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

## §D. C3a pivot (zero LP, desk ruling "pivot C3a"): the price-mean miss is in the tail days, not the water value

Inputs: keeper `nwppnext23_span` `hourly/system_<Y>` (demand-weighted P1 price over the five `NWPP-*` zones) and
`class_hourly_<Y>`; the WEIM benchmark `actual_lmp_hourly_NWPP` rt (the C3a reference); EIA-930 NWPP footprint
frame; EIA-923 Schedule 2 zone-month delivered gas (`derive_nwpp_zonal_gas_hub.load_zone_months`); and
`gas-prices/sumas_weekly.csv`.

| year | C3a (bench hours) | share of the gap in the top 10 days | C3a without them | the days |
|---|---:|---:|---:|---|
| 2023 (Jun–Dec) | −11.1 % | 0.52 (top 20: 0.79) | **−6.0 %** | Oct 25–31 (cold, Sumas print 6.04 on 10-25), Jul 25–26 and Aug 16 (heat) |
| 2024 | −26.2 % | **0.80** | **−7.0 %** (no January: −6.9 %) | **Jan 12–17**, the MLK arctic event: bench daily $236 / 709 / 782 / 634 / 478 / 185, model $48–54 |

- **Physics matches during the event (Jan 12–17, 2024).** Model vs EIA-930, mean MW: hydro 14,789 / 13,997;
  gas 10,644 / 10,114; coal 6,322 / 6,043. Slack is 0. The model dispatches the cold snap correctly and prices it at
  the marginal offer ($50), while the WEIM benchmark priced scarcity ($700–1,270 peaks).
- **Not fuel.** EIA-923 January 2024 zone delivered gas is $3.98–6.42/MMBtu, against Henry Hub at about $3.2. The
  weekly Sumas prints are 6.46 (01-10) and 3.99 (01-17). A monthly zonal basis, which `gas_electric_power_monthly_level`
  would need an NWPP state-weight row to supply (none exists, so that key is inert for NWPP), moves January by only
  $1–2/MMBtu. It would matter for January 2023 (zone deliveries $15–40), but that month is outside the benchmark.
- **Not the water value.** Outside the tail days, both years sit inside the ±10 % band. The hydro-marginal price
  level (FINDING-nwppnext23 §C) is not the binding error.

**Routed (not solved; a lever arm needs a desk slot).** The open C3a records are a **scarcity-pricing** gap. In NWPP's
model, nothing prices a tight-but-served hour above the marginal offer. In the real market, WEIM's
resource-sufficiency failures and power-balance penalty pricing did. A structural candidate needs a measured,
forward-reproducible driver (rule 13), for example WEIM RSE-failure intervals or a reserve requirement with a
demand curve, plus a rule-19 census of what already prices NWPP's tail. Free daily NW gas hubs do not exist
(plan §4), so a daily-fuel route is closed. C3b 2023/24 (shape) shares the same days.
