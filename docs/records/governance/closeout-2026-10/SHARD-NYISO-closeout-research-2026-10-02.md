# NYISO — calibration close-out research (read-only shard, 2026-10-02)

Repo state read: `origin/main` keeper `2026-10-01-nyisonext21-astoria-hr-span` + stamped `-2021`; three solved-but-unpromoted
lever PRs (#6984 closed, #6987 open, #6992 open). No solve, no edit, no commit in this shard. All parquet reads were
impossible here (no pandas/pyarrow on any interpreter; installing would write into the repo), so every number below is from
committed JSON/CSV/records or from the cited external source.

## 1. STATUS TABLE

Keeper `2026-10-01-nyisonext21-astoria-hr-span`, bundle `results/calibration/nyisonext21_span` (2022–2025), stamped
touchpoint `2026-10-01-nyisonext21-astoria-hr-2021` (`nyisonext21_2021`), pin `fdc41f36`, rubric **3.13**
(`frontend/data/backcast/status/NYISO.js`). G-DRIFT: HEAD `9209f610` is INERT on the keeper's backcast path
(`docs/records/nyiso/FINDING-nyiso-next32-gdrift-baseline-2026-10-01.md`), so no control solve is owed.

| criterion | 2021 (validation) | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C1 fuel mix | PASS (worst ST_GAS −2.99 TWh) | PASS | PASS (ST_GAS +1.92 TWh / +1.6 pp) | PASS (CC +2.44 TWh / +2.4 pp) | **SKIPPED** — preliminary EIA-923: 15–70 % of prior plants reporting |
| C2 sysvol gas | PASS | PASS | PASS | PASS | SKIPPED (−0.3 %) |
| C3a mean LMP (zone-resolved RT, LW) | PASS +2.9 % | PASS −2.4 % | PASS +1.2 % | PASS −4.0 % | **FAIL −11.6 %** (61.18 vs 69.23) |
| C3b shape NRMSE | PASS 0.108 | PASS 0.155 | PASS 0.122 | PASS 0.113 | PASS 0.181 |
| C3c tail >$300 (model max-zone dual h vs RT hub h) | PASS 0 vs 3 | CAVEAT 1 vs 101 (ledgered) | **FAIL 0 vs 10** | **FAIL 0 vs 13** | **FAIL 8 vs 42** |
| C3c DA companion (not gated) | 0 vs 0 | 1 vs 10 | 0 vs 1 | 0 vs 0 | 8 vs 12 |
| C4 gas fleet r / NRMSE | 0.918 / 0.173 | 0.821 / 0.227 | 0.917 / 0.153 | 0.898 / 0.142 | 0.854 / 0.183 (all PASS; coal SKIPPED immaterial) |
| C6 governance | PASS | PASS | PASS | PASS | PASS |
| C8 forced share (ST_GAS / CC) | 24.4 % / 1.2 % | 16.7 % / 0.7 % | 13.3 % / 1.0 % | 15.4 % / 0.6 % | 13.5 % / 0.3 % (PASS; CT_PEAKER immaterial <2 %) |
| determination | CALIBRATED | — | — | — | span **NOT-YET** |

What blocks the ISO: `reasons` = "undocumented FAIL: price_mean 2025, price_tail 2023/2024/2025". Because C3a 2025 fails, C3c is
not a *lone* failure, so rule 22's auto-ledger does not fire and three C3c FAILs stand (`status/NYISO.js`). Note the basis
asymmetry in C3c: the model count is hours the LP's **max zonal dual** > $300 (`scripts/calibration_verdict.py:2606`), the
actual is hours the **11-zone simple-mean hub** RT > $300 (`scripts/data/derive_actual_tail.py`,
`frontend/data/backcast/tail/actual_tail.json`) — the model is already given the more lenient side.

**Held arms the owner has not yet ruled on (the close-out is one ruling away):**

| PR | lever | span / 2021 / ISO | C3a 2025 | record |
|---|---|---|---|---|
| #6987 arm A (open, draft) | `nyiso_gas_daily_print_level` (zero DOF: each day priced at its own Transco Z6 print, no calendar renormalisation) | **CALIBRATED / CALIBRATED / CALIBRATED** | −9.6 % (0.4 pt margin) | `RESULT-nyiso-next25-print-level-2026-10-01.md` on `claude/nyisonext25-result` |
| #6992 arm B (open, draft) | #6987 A + `nyiso_li_tsl_all_hours` (940 MW published Zone-K security cap in all hours) | **CALIBRATED / CALIBRATED / CALIBRATED** | −9.6 %; Zone K 2025 −10.9 → −10.1 % vs DA | `RESULT-nyiso-next26-li-tsl-all-hours-2026-10-01.md` on `claude/nyisonext27-orchestrator-1xf5zi` (option 1 recommended) |
| #6984 (closed) | `nyiso_gas_flow_date` alone | NOT-YET (C3a 2025 −12.7 %) | worse alone; composes with print-level (NEXT-25 arm B: 2022–24 better, 2025 −10.3 %) | `RESULT-nyiso-next23-…` (branch) |

C3c counts are unchanged in every arm (8 vs 42 in 2025). `audit_keepers` E13 is red by design while the probe runs are registered.

## 2. ROOT-CAUSE MAP

| (year, gate) | best diagnosis (record) | tried / verdict | still open | diagnosis certainty |
|---|---|---|---|---|
| C3a 2025 −11.6 % | Not a level gap: deciles 1–8 run +$3.4 high; hours > $150 carry −$8.8 of the −$8.0 miss; two clusters — Jan–Feb (model below DA too; Jan −$2.2 of −$6.1 DA miss) and Jun 23–25/Jul RT scarcity (−$3.2 from June alone) (`FINDING-nyiso-next23-c3a-2025-phase0-2026-10-01.md` §1). Winter half: the daily-gas construction scales every ordinary day of a spike month by `c = trade_mean/calendar_mean` (Jan-2025 0.78) and 86 % of the NYC winter shortfall sits on days the oil-parity cap does **not** bind (`FINDING-nyiso-next24…` §2b, `FINDING-nyiso-next25…` §2). East-of-Central-East congestion deficit (Capital −19.1 $/MWh spread deficit, 93–96 % congestion) is the ledgered CE object (`…next25` §1, `RESULT-nyiso-next20-ce-precheck…`). | Flow-date alone: worse (−12.7). Print-level (arm A): **−9.6 PASS**. Dual-fuel measured-mix: refuted at zero LP (would double the error, `…next24` §2a). CE flowgate: FAILED pre-check, ledgered. | After arm A: Capital_Hudson still −9 % annual, NYC −7.1 %; the June RT cluster; 0.4 pt margin. | high for the winter half (bracket reproduced in LP); the June half is the C3c object |
| C3c 2023 (0 vs 10) | All 10 missed hours are Long Island at load p50 84 % of peak; Sept-led (5 of 10); model max dual p50 $85, max $172; model has NYC 10-min shortfall in 13 h but the published NYC curve is $25 (`results/phase0/nyiso/_nyiso242_tail_phase0.json`; `RESULT-nyiso249…` §6). **DA actual tail that year: 1 h.** | nyiso-242/243/244/245/246/249: DA offer level, offer shape, availability (P-27 kill test), reserve stacks — all refused or falsified at zero LP; "the instrument and the phenomenon are in different markets" (`RESULT-nyiso249…` §8). | Per-hour RT attribution (reserve vs transmission shortage) never measured in-repo. | certain that it is RT-only (DA 1 h); mechanism split uncertain |
| C3c 2024 (0 vs 13) | All 13 LI, load p50 94 % of peak, July-led; model max dual ≤ $83; **zero** reserve shortfall in the model in those hours; **DA actual tail: 0 h** (`_nyiso242_tail_phase0.json`). | as above | as above | certain RT-only |
| C3c 2025 (8 vs 42) | 39 missed: LI 38, NYC 1; Jun 15 + Jul 14 + Jan 5; model max dual p50 $159, 13 h in $200–300; model NYC 10-min short in 28 h at the $25 cap, SENY $40 in 6 h, never NYCA/East short (`_nyiso242_tail_phase0.json` 2025). On 6/24 the model tracks DA ($176–321 vs DA $189–365) while RT ran $649–2,134 (`…next23` §1). **DA tail 12 h** — so ~12 h are reachable in principle, 30 are RT-only. | nyiso-242 §: 2025's summer cluster is "the ONE window price formation could actually reach" (94.9 % utilisation, 899 MW idle sub-gate). No lever has been built for it. | June 24 availability (SOM: 4.0 GW forced outages/derates/under-performance, 2.4 GW above EFORd; ~25 % of 2.5 GW external ICAP cut) is not in the model's inputs. | high on location/timing; the availability gap is measured externally, not in-repo |
| C3c 2022 (1 vs 101, caveat) | 70 winter hours (Elliott/Jan) with all five zones > $300 at 65 % of peak load, +$251–285 additive gap; 4.4 GW offered below $300 undispatched; implied HR 23–26 MMBtu/MWh (`docs/mechanism-testing-matrix.md` §5.5 nyiso-242 paragraph); gas-input holes repaired (nyiso-235) and the oil-parity cap ($24.85) bounds the repair (nyiso-234 addendum). | availability family closed by arithmetic (nyiso-234); P-27 kill test falsified availability (nyiso-243). | ledgered | high |
| C1 2025 SKIPPED | preliminary EIA-923 vintage (data) | — | EIA-923 2025 final intake | certain |

Flag: the C3c 2023/2024 diagnosis "RT-only" rests on the DA counts and on nyiso-249's zone attribution; the split between
RT reserve-shortage pricing and RT **transmission**-shortage pricing (GTDC $200–$2,500/step, $4,000 beyond CRM; LI
transmission shortages in 12.3 % of 2025 intervals, +$6.5/MWh annual, SOM 2025 p.58) has never been measured on the missed
hours. That split decides whether anything is reachable.

## 3. RETEST CANDIDATES (rule 28: only where the premise changed)

| mechanism | prior verdict / date / evidence | what changed (new evidence) | targets | expected direction | cost |
|---|---|---|---|---|---|
| `tsa_transfer_derate` | G, nyiso-95 2026-07-28: event set published and wired, **magnitude** not identifiable (`FINDING-nyiso95-tsa-derate-not-identifiable-2026-07-28.md`) | 2025 SOM §VI.D (May 2026) publishes the magnitude class: TSAs "routinely reduce upstate-to-downstate transfer capability by approximately 1 to 2 GW relative to day-ahead scheduled levels", with TSA congestion cost by forecast-probability tranche (Fig. 25) and the recommendation to carry TSA in the DAM via modified GTDC values (`(session scratch, not committed) nyiso_2025_som.pdf` body pp. 49–50). Still a range, not a per-event limit — a phase-0 coverage test first. | C3c 2023–2025 (LI/NYC summer hours), K–J spread | raises downstate duals in TSA hours only | zero-LP coverage (TSA hours ∩ missed hours, from `data/raw/NYISO-AS/requirements/realtime-events`), then owner data ask (§6 row 4) before any solve |
| `nyiso_spin_reserve_online` | I, nyiso-110/144: inert whenever `rho ≥ rho* = 0.3426/0.3635/0.4619` (`mechanism-matrix/NYISO.js`) | RHO_CLIP floor deleted (nyiso-151, 2026-08-22): measured `online_rho` = 0.3014 for NYC (nyiso-145 card), i.e. **below** rho* in all three years — the cell's own inertness condition no longer holds. Also C3c 2025 is now load-bearing (NEXT-22). | C3c 2025 June (statewide 10-min spin was short on 6/24 per Potomac Q2-2025 slide 4/9) | raises `nyca_10min_spin` ($775) duals in tight hours → energy dual if the family binds | phase 0: recompute rho* on the keeper's `reserve_family_*` sidecars for Jun 23–25 2025; full span only if it binds there |
| `unit_outage_short_windows_gas` | I, nyiso-227 / R-NYISO 2026-09-24: sub-5-day gas windows 192–372 MW annual mean, "near-inert" on the 2022 winter tail | Never evaluated on Jun 23–25 2025, where the MMU measured 2.6 GW ST + 1.2 GW CC + 0.2 GW peaker forced outages/derates in peak hours (Q2-2025 slide 21). Honest expectation: zero-output windows capture little of "derates and under-performance". | C3c 2025 | removes availability in the window | zero-LP census of `campd-unit-outages-shortgas-NYISO.csv` rows active 6/23–6/25 2025 |
| `scuc_load_pocket_commitment` | G, nyiso-97/160/192: in-city requirement is MyNYISO-walled | Potomac publishes the reliability-commitment MW annually (SOM 2024 Table 4 p.57; SOM 2025 Table 4 p.64; Q2-2025 slide 19: 62 % "not verified", 67 % of verified MWh surplus headroom / MRT) and Rec #2024-1 "model underlying needs as local reserve requirements". A public N-1-1-0 magnitude may now be identifiable. | NYC steam over-dispatch (Ravenswood 2023 4.00 vs 0.88 TWh, NEXT-28), K–J in capped hours, C8 | shifts NYC steam from inframarginal LP loading to a committed floor | zero-LP: read Table 4 MW vs the keeper's NYC ST_GAS forced energy; design only if the identification holds |
| `nyiso_gas_flow_date` | O (NEXT-23; #6984 closed) | NEXT-25 arm B already measured it on top of print-level: better 2022–2024, 2025 −10.3 % FAIL | C3b 2022–2024 | timing | **no LP needed** — ruling on #6987/#6992 decides; keep O |
| `dual_fuel_measured_oil_burn` | U with NEXT-24 evidence | none; NEXT-24 showed measured-mix pricing doubles the error on cap days | — | — | do not solve |

Cells re-read and NOT re-opened (no new evidence): `measured_offer_surface` G (spent re-open condition), `cc_winter_capability_basis` G,
`temp_dependent_derate` G (nyiso-234 reach bar), `nyiso_fg_split` R (CE flowgate failed pre-check), `nyiso_incity_commitment_obligation`
R (nyiso-153 rejected as armed), `nyiso_hub_gap_month_level` R, `nyiso_firm_imports` R, `measured_interface_limits` G.

## 4. NEW LEVERS

| name | mechanism (LP) | measured driver | forward story (rule 13) | gate | expected effect | risk / doubts |
|---|---|---|---|---|---|---|
| Neighbour-emergency import curtailment | On a seam whose neighbour has declared a capacity emergency (ISO-NE OP-4 / CSC on 6/24/2025; PJM emergency), non-firm import upper bound → 0 for the declared hours (an availability event, same class as CAMPD outage windows) | ISO-NE OP-4 event summary (<https://www.iso-ne.com/static-assets/documents/100027/june-24-2025-coo-op-4-and-csc-summary-08072025.pdf>); PJM emergency procedures postings; NYISO SRE calls (Q2-2025 slide 23: "neighboring ISOs cut imports … on June 24") | regenerates from the neighbour's event calendar; responds to conditions | C3c 2025 (June cluster, 29 of 39 h), C3a 2025 | June 24 HB17–20 only; bounded by the model's NE/PJM import in those hours (not computable here without parquet) | few hours a year; needs the per-link schedule the landing band already carries monthly; zero-LP first |
| Graduated Transmission Demand Curve on binding links | Replace the hard `NYC>Long_Island` (and other) TTC with a soft cap: relaxation steps at the published GTDC ($200/$350/$600/$1,500/$2,500 per CRM/5; $4,000 beyond CRM, since 2023-11-14; $350/$1,175 before) | NYISO tariff / SOM 2024 p.46 fn 58; CRM 5–100 MW per facility | published market rule; regenerates for any year | C3c 2023–2025 (LI), K–J | **likely near-inert**: the LP relaxes only when LI internal supply is exhausted; the missed hours show LI duals $58–174 with LI headroom | structurally faithful but low reach; ledger-grade |
| Declared-event availability (NYISO Energy Warning windows) | In an NYISO-declared Energy Warning window, thermal availability = CAMPD-observed capability instead of the model's derived availability | NYISO operating messages (`data/raw/NYISO-AS/requirements/oper-messages`, already in-repo) + CAMPD hourly | the *event* regenerates; the *magnitude* would be read from observed output → **this is the rule-13 line** (pinning). Owner question 2. | C3c 2025 | SOM: 17.1 % unavailable vs 6.4 % EFORd on 22.3 GW → ~2.4 GW | probably inadmissible as written; an EFORd-at-high-output class slope would be a fitted parameter |
| TSA transfer limit set | During published TSA hours, the upstate→downstate link and the NYC/LI import caps take the published post-TSA limits | TSA hours in-repo; limits: NYISO Transmission & Dispatching Operations Manual (data gap row 4) | published operating rule, regenerates from TSA declarations (weather-driven) | C3c 2023–2025, C3a 2025 | SOM: 1–2 GW transfer reduction in TSA hours | identification of the limit values (the nyiso-95 objection) stands until the manual values are in hand |
| Published summer-peak unavailability by class | A class-level derate on the hottest-day hours from the MMU's measured "functionally unavailable" categories (Fig. 31: 1,480 MW in 2024; emergency MW, ambient water/tides, cogeneration steam) | SOM 2024 p.90 Fig. 31 (ISO-level, by class) | published; but it is an outcome census, not a per-unit input | C3c 2024/2025 | ≤ 1.5 GW | class-level number applied as a derate = a tuned haircut unless tied to a physical driver (water temperature); more honest as a ledger entry |

No fitted adders, haircuts or offsets are proposed. The rule-1 band channel is not invoked.

## 5. EXTERNAL RESEARCH

**Confirmed from primary sources**

- June 23–25 2025: load peaked 31.9 GW post-DR (highest since 2018); "prices were driven by lengthy shortages of statewide
  and local operating reserves"; 6/24 17:00–20:00 average RT LBMP ~$1,300 central NY, ~$1,800 eastern NY, ~$3,500 Long
  Island; NYISO Energy Warning issued. Fossil fleet: 22.3 GW evaluated, composite EFORd 6.4 % but 17.1 % unavailable
  (forced outage, derate, under-performance; 2.6 GW ST, 1.2 GW CC east NY, 0.2 GW peakers); ~25 % of ~2.5 GW external ICAP
  cut by neighbours; 213 MW emergency capacity offered but unscheduled; ~600 MW large curtailable load, ~90 % curtailed HB18
  (Potomac Q2-2025 quarterly, slides 4, 6, 7, 9, 21–24: <https://www.potomaceconomics.com/wp-content/uploads/2025/08/NYISO-Quarterly-Report_2025Q2_9-25-2025-revised.pdf>).
- Shortage pricing design: deep 30-min shortages ≈ $1,000 incl. locational adders; multiple 30/10-min shortages "can exceed
  $2,000"; MMU EVOLL ≈ $16,000 at 10-min depletion vs $1,525 combined ORDC; 30-min near-depletion ≈ $2,800 vs $750
  (SOM 2024 pp. 42–45; SOM 2025 pp. 55–57). The model's `NYISO_RCPF_PRODUCTS` / `NYISO_RCPF_LOCATIONAL`
  (`src/market_sim/model/reserves/spec.py:411–455`) carry the published levels ($775/$750/$500/$25/$40) — matches.
- Shortage frequency: 2024 system-wide 30-min shortages ~0.6 % of intervals, regulation < 3 %, shortages raised LBMPs 7–9 %
  (SOM 2024 p.42). 2025: regulation 7 %, system-wide and SENY 30-min 2–3 %, **NYC reserve shortages 7 % of intervals**,
  LBMP impact 10–15 % (SOM 2025 p.54). Model: NYC 10-min short in 28 of the 39 missed 2025 hours — direction consistent.
- Transmission shortages: GTDC five steps $200/$350/$600/$1,500/$2,500 (each CRM/5), $4,000 beyond CRM, since 2023-11-14;
  2024: 9 % of 5-min intervals (5 % in 2023); 2025: ~20 % of intervals, LI 12.3 %, LI annual LBMP impact ≈ +$6.5/MWh;
  "offline GT pricing" depresses recognised shortages (SOM 2024 pp. 46–47; SOM 2025 p.58).
- DA–RT: 2025 RT premium NYC +4.7 %, LI +5.6 % "due to real-time reserve shortages … during extended heat waves … and
  real-time congestion"; LI more susceptible (old slow-ramping steam, LDC gas intraday inflexibility, weak HV ties);
  TSAs reduce upstate→downstate transfer by ~1–2 GW vs DA and are RT-only (SOM 2025 pp. 46, 49–50).
- NYC reserve requirement: the as-enforced series in-repo is 500/1,000 MW with TSA zero-hours 137/184/92 (2023/24/25)
  (`data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_<y>.csv`); the raise to 625/1,250 is posting v2.0 dated
  2026-05-13 (README) — **outside the backcast span**. Dynamic Reserves: FERC approved July 2025, deployment targeted 2028
  (NYSRC markets reports: <https://www.nysrc.org/wp-content/uploads/2026/04/8.2-2026.04.10-NYISO-Markets-Report-Attachment-8.2.pdf>).
- Peaker Rule: ~800 MW NYC peaking exited between summers 2022 and 2023 (SOM 2025 p.48); ~590 MW more from 2025-05-01;
  Gowanus 2&3 + Narrows 1&2 retained to 2027-05-01 then to 2029-05-01; Danskammer (G) and Far Rockaway/Pinelawn (K) retained
  on reliability (<https://www.utilitydive.com/news/nyc-peakers-planned-2025-retirement-remain-online-reliability-must-run-nyiso/700417/>,
  <https://www.rtoinsider.com/130378-nyiso-proposes-keeping-old-generators-nyc-reliability/>). The in-repo schedule
  (`data/raw/reference/nysdec-227-3-peaker-compliance.csv`, 23 rows) carries Gowanus/Narrows as STAR-designated, not
  restricted — consistent.
- Winter 2025 gas: eastern NY $5–6.24/MMBtu average with "considerable price volatility in the winter because of
  west-to-east congestion on gas pipelines" (SOM 2025 p.i); the MLK-weekend $97.90 Z6 print is in the committed series
  (`FINDING-nyiso-next23…` §2a).

**How established models treat the phenomena (confirmed)**: the MMU itself attributes the RT premia to reserve shortages,
RT congestion and TSAs that the DAM does not carry (SOM 2025 pp. 46–50); the rubric already classes the DA–RT wedge as
out-of-representation (`docs/calibration-determination-rubric.md:208`) and the C3c band note records that commercial practice
excludes spike hours or tunes hurdle rates (line 1272). A realized-weather LP with energy+reserve co-optimisation reproduces
DA-like outcomes; the DA tail counts (1/0/12 h) are the honest ceiling of what this model class can reach without an RT
mechanism.

**My inference (not sourced)**: (i) C3c 2023 and 2024 are unreachable by any admissible mechanism in this class — the DA
market, with the real fleet and real offers, produced 1 h and 0 h. (ii) 2025's reachable share is ≤ 12 h (DA count) vs the
21 h the band needs, unless an availability/import event representation for June 24 is admitted. (iii) The Zone-K summer
miss is the RT transmission-shortage (GTDC) and offline-GT-pricing object, not a reserve object.

## 6. DATA GAPS (free sources only)

| what | why (gate) | source | directions | lands in | effort |
|---|---|---|---|---|---|
| EIA-923 2025 **final** annual | C1/C2 2025 SKIPPED (15–70 % reporting) | <https://www.eia.gov/electricity/data/eia923/> | "EIA-923 2025 Final" zip (released ~Sep–Oct 2026; check the page); replace the preliminary vintage | `data/raw/eia-923-generation-fuel/` via the existing fetch | low (existing path) |
| NYISO RT **limiting constraints** (shadow prices, per 5-min) | per-hour attribution of the 65 missed tail hours to transmission vs reserve shortage | MIS public: `http://mis.nyiso.com/public/` → "Real-Time Market → Limiting Constraints" (monthly CSV zips, pattern `…/csv/rtlimit…`; the DA sibling is already fetched by `scripts/data/fetch_nyiso_zonal_lmp.py --kind dlc`) | 2023-01…2025-12, 36 monthly zips | `data/raw/lmp-data/NYISO/` (gitignored, regenerable) | low: extend `--kind` to the RT posting |
| NYISO RT ancillary prices | same decomposition (reserve-shortage components) | already in-repo `data/raw/NYISO-AS/NYISO_as_rt_<y>.csv` | none | — | zero |
| NYISO TSA post-contingency transfer limits | identifies `tsa_transfer_derate` magnitude (nyiso-95's blocker) | NYISO Manuals → "Transmission and Dispatching Operations Manual" (<https://www.nyiso.com/manuals-tech-bulletins-user-guides>) and "Thunderstorm Alert" procedures; also NYISO "Operating Limits" posting on OASIS | find the UPNY-ConEd / Dunwoodie-South / Sprain Brook–Dunwoodie-South limits under TSA; note the vintage | `data/raw/NYISO/interface-flows/` (new file, transcribed with page cites) | medium (PDF transcription) |
| NYISO RT masked generator bids (`rtgenbids`) | the RT instrument nyiso-249 §10 says any successor to the DA-only P-27 needs | MIS public "Market Bid Data: Generator (Real-Time)" — same P-27 family as the DA archive already fetched by `scripts/data/fetch_nyiso_bid_data.py`; **verify the exact path on mis.nyiso.com/public** (not confirmed in this shard) | 2022–2025 monthly | `data/raw/nyiso-bid-data/` | low if the posting exists |
| Potomac 2025 SOM (May 2026) + Q2/Q3-2025 quarterlies | tail attribution, June-24 availability facts, LI congestion drivers | <https://www.potomaceconomics.com/wp-content/uploads/2026/05/NYISO-2025-SOM-Report__5-19-2026-final.pdf> (14 MB; copy in `(session scratch, not committed) nyiso_2025_som.pdf`), Q2 link above | store as publication PDFs per `data/raw/NYISO/README.md` (gitignored class) | `data/raw/NYISO/` | low |
| ISO-NE June 24 2025 OP-4 / CSC summary; PJM emergency postings | neighbour-emergency curtailment lever (§4 row 1) | ISO-NE link in §4; PJM "Emergency Procedures" postings (<https://www.pjm.com/markets-and-operations/emergency-procedures>) | event windows 2023–2025 | `data/raw/seam-neighbour-price/` or a new `neighbour-events/` | low |
| NYISO 2026 Gold Book | forecast-side retained-unit dates (Gowanus/Narrows to 2029, Danskammer, Far Rockaway) | <https://www.nyiso.com/documents/20142/2226333/2026-Gold-Book-Public.pdf> | README says already fetched (gitignored); verify Table IV-4/IV-5 vintages carry the retention dates | `data/raw/NYISO/` | zero–low |

No paywalled data is required for any item above. GADS per-unit outages (the MMU's Rec 2025-1b object) are not public.

## 7. CAPACITY / VINTAGE (EIA-860)

- Fleet basis: year-matched EIA-860 vintage per solved year (`eia860_vintage_tracks_solve_year = true` in the keeper
  `run_config.json`), per-unit COD, mid-year retiree carry (`mid_vintage_exit_carry`, `fleet_zone_vintage_coords`,
  `retiree_vintage_status_scope` armed since NEXT-18 — Indian Point 3, 1,039 MW, retired 2021-04-30, was missing Jan–Apr
  2021 and held 88 % of the 2021 over-pricing). Vintage snapshots `vintage_2018…2024` plus the 2025 Early Release;
  `vintage_2023/2024` carry the operable sheet only (`data/raw/eia-860/README.md:68–80`). No 860M in-year layer exists.
- Gold Book role: transcription source, not a machine input (`data/raw/NYISO/README.md:21–31`); 2018–2022 PDFs committed,
  2023–2026 gitignored; `2023/2024-NYCA-Generators.xlsx`, `2025-NYCA-Existing-Generating-Facilities.xlsx` present. Records
  settled that Gold Book Table III-2a "In-Service Date" is a registration date that leads EIA-860 `Operating Month`
  (records grep, §M). A Gold-Book-vs-EIA-860 unit-by-unit reconciliation (summer DMNC vs net summer capacity) has **not**
  been done as a standing artifact; the xlsx files make it a zero-LP task.
- Peaker Rule schedule (`data/raw/reference/nysdec-227-3-peaker-compliance.csv`): 2023-05-01 ozone OOS — Coxsackie GT1,
  South Cairo GT1 (retired 2024-03-31), Northport GT, Port Jefferson GT, Shoreham, Glenwood (55 MW), 74th Street;
  2025-05-01 — Astoria GS (15 MW), Arthur Kill (16 MW), 59th Street; Gowanus/Narrows STAR-designated (not restricted);
  Ravenswood GT retired 2023-10-14; 2030 statutory rows Vernon Blvd, Seymour, Brentwood, Hell Gate, Harlem River Yard.
  Published totals to reconcile against: ~800 MW exited 2022→2023 (SOM 2025 p.48) and ~590 MW unavailable from 2025-05-01
  (Utility Dive) — most CSV rows carry a null `restricted_mw` (whole unit), so the MW sum needs the EIA-860 join.
- Available-capacity overstatement, measured by the MMU: 2024 hottest days ~1,480 MW "functionally unavailable" (emergency
  MW, ambient water/tides, cogeneration steam, barometric pressure; SOM 2024 Fig. 31 p.90); June 24 2025 17.1 % of 22.3 GW
  unavailable vs 6.4 % EFORd; ~8 GW in zones G–K are tidal/barometric-sensitive. The model's EIA-860 net summer capacity ≈
  DMNC, which the MMU says is itself over-stated on peak days. This is the single biggest *input-side* fact behind the
  2025 June tail and it has no admissible per-unit source.
- Retained retirements (forecast side): Gowanus 2&3, Narrows 1&2 (to 2029-05-01), Danskammer 1–4 (G), Far Rockaway /
  Pinelawn (K) — EIA-860 planned retirement dates for these must not fire in the forecast fleet (reversal registry under
  `fossil_announced_exits_enabled`). CHPE 1,250 MW HVDC into NYC enters 2026 (SOM 2025 p.v) — forecast only.
- Capacity market facts for the forecast arm: NYC LCR 80.4 → 78.5 % (2025/26), IRM 122 → 124.4 %, NYC capacity $132/kW-yr
  2025/26, ROS $51/kW-yr; 2026/27 LCRs rise sharply (SOM 2025 p.v); non-firm winter CAFs from May 2026 (−42 % in NYC).

## 8. RECOMMENDED CLOSE-OUT SEQUENCE

| # | step | gate | pre-fixed pass reading | P(closes) | cost |
|---|---|---|---|---|---|
| 0 | **Owner rules on #6992 option 1** (promote NEXT-26 arm B = print-level + all-hours Zone-K TSL; decline #6984 standalone; close #6987 with docs). `promote_keeper.py` one command; prunes NEXT-21/25/26-A stores. | C3a 2025, ISO determination | already read: span/2021/ISO **CALIBRATED**, C3c lone → auto-ledgered caveat | **high** (solved, gates passed) | 0 LP |
| 1 | Zero-LP tail decomposition: for the 10+13+39 missed hours, join RT zonal LBMP components (congestion/loss, on disk), `rtasp` reserve prices (on disk), TSA hours (on disk), DA LBMP; add RT limiting constraints after the §6 intake. Reading: share of missed hours with DA < $300 and (RT reserve price > 0 or RT congestion > $100). | C3c 2023/2024/2025 classification | if ≥ 80 % of 2023/2024 missed hours are RT-only (DA < $300) with an RT reserve/congestion component → ledger C3c 2023/2024 as model-class with the SOM citations | high that the reading holds (DA tail 1/0 h) | 0 LP |
| 2 | Zero-LP June 23–25 2025 availability audit: keeper availability vs CAMPD-observed capability by class in HB15–20 (needs `unit_hourly` / `unit_marginal_2025` sidecars — parquet). Reading: model available thermal minus CAMPD max output ≥ 2 GW ⇒ availability object confirmed; write the owner card on admissibility (§9 Q2). | C3c 2025 | an admissible driver found → PRECOMMIT; else ledger 2025 with the measured gap | low–med that an admissible driver exists | 0 LP |
| 3 | Neighbour-emergency import curtailment, phase 0: model NE/PJM import on 6/24 HB17–20 vs P-32 measured and the ISO-NE OP-4 window. Reading: ≥ 500 MW of modelled import in cut hours → build the event rule (default off), 5 shards. | C3c 2025 (needs ≥ 21 h; model 8; June cluster 29) | arm reaches ≥ 21 h without inventing hours elsewhere (2021–2024 counts unchanged) | low–med | 0 LP, then 5 shards |
| 4 | `nyiso_spin_reserve_online` at measured rho: phase 0 rho* on the keeper's reserve sidecars for the June 2025 hours; full span only if rho 0.3014 < rho* there. | C3c 2025, C3a 2025 | June hours gain reserve duals; C1/C8 unchanged | low | 0 LP → 5 shards |
| 5 | TSA: phase-0 coverage (TSA hours ∩ missed hours) + §6 data ask; design only if the manual limits are published. | C3c 2023–2025 | coverage ≥ 50 % of summer missed hours and limits in hand | low (identification) | 0 LP |
| 6 | Gold Book ↔ EIA-860 per-unit reconciliation (summer DMNC vs net summer, retention dates, peaker-rule MW sums vs 800/590 MW) as a standing artifact. | C1/fleet audit, forecast gate | documented misalignments ≤ 1 % of NYCA ICAP | high (bookkeeping) | 0 LP |
| 7 | After step 0: re-score when EIA-923 2025 final lands (C1 2025 SKIPPED → scored). C3a is unaffected; C1 2025 may move the span if a class misses. | C1 2025 | C1 2025 PASS | med | 0 LP |

**Likely not closable under this model class; ledger instead**: C3c 2023 and 2024 (RT-only: DA tail 1 h / 0 h; RT transmission-
shortage/GTDC and offline-GT pricing on Long Island, RT reserve shortages, TSAs — SOM 2025 pp. 46–58); the Central-East
congestion deficit on a 5-zone network (NEXT-20, ledgered); the uncapped-hour Zone-K import-set congestion (NEXT-29/30,
owner card pending); the DA–RT forecast-risk wedge (rubric line 208); sub-hourly transients. C3c 2025 is partially
reachable only if an availability/import event representation for June 24 is ruled admissible.

## 9. OPEN QUESTIONS FOR THE OWNER

1. Rule on #6992 option 1 (promote NEXT-26 arm B; subsumes #6987 option 1; decline #6984 standalone). This single ruling takes
   NYISO to CALIBRATED with C3c as the ledgered caveat. Accept the 0.4-pt C3a-2025 margin as a structural (zero-DOF) result?
2. Rule 13 line: is a **declared-event** availability representation (NYISO Energy Warning windows; neighbour OP-4/emergency
   import cuts) admissible when the event is published but the magnitude is read from observed output (CAMPD / P-32)? If
   only the event is admissible, what magnitude source do you accept (EFORd-at-high-output class slope = fitted; MMU's
   17.1 % = outcome)?
3. Accept ledgering C3c 2023/2024 as RT-only model-class limitations on the DA-tail evidence (1 h / 0 h) plus the SOM
   attribution, after the step-1 decomposition confirms it?
4. Authorise the two free MIS intakes (RT limiting constraints; RT masked genbids) for the tail decomposition — no LP.
5. Should the `complete` marker (withdrawn 2026-09-25, Y-31) be reinstated on promotion, or held until EIA-923 2025 final
   scores C1 2025?
