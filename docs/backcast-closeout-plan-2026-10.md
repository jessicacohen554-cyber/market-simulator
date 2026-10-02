> Status: ACTIVE — the backcast calibration close-out program (2026-10-02). Owner: jessicacohen554. Evidence: nine per-ISO research shards + one cross-ISO EIA-860 audit under `docs/records/governance/closeout-2026-10/`. Zero LP was spent building this plan; every number is read from the committed keeper status shards, keeper bundles, records, or a cited primary source.

# Backcast calibration close-out plan and roadmap — October 2026

**What this is.** One plan to take every ISO from its current determination to a defensible end state: `CALIBRATED`, `CALIBRATED-WITH-CAVEATS`, or an owner-signed frontier statement that says why the remaining miss is outside the model class. It consolidates (1) where each ISO stands against rubric v3.13, (2) the root cause behind each failing gate as the records establish it, (3) old levers whose rejection premise has changed and deserve a retest, (4) new admissible levers, (5) the free data the owner must download, (6) the EIA-860 capacity/vintage settlement, and (7) the owner decisions the program is blocked on.

**How to read it.** §1 is the board. §2 holds the cross-ISO workstreams (the 860 settlement is W0). §3 is one block per ISO with its sequence. §4 is the download list. §5 is the owner decision queue. §6 is the roadmap. Each per-ISO shard report (`SHARD-<ISO>-closeout-research-2026-10-02.md`) carries the full root-cause map, lever tables, external citations and the five owner questions; this plan keeps only what a reader needs to decide and sequence.

**Rules this plan lives under.** Rule 1 (structure before fit; the only price-tuning channel is the registered offer bands), 13/14 (measured, reproducible inputs; never an estimate because it fits), 19 (one mechanism per phenomenon), 28 (never re-test an `R`/`I`/`G` cell without new evidence — every retest below names its new evidence), 29/32/36 (phase 0 first; one shard per ISO-year; the parent never solves), 31 (never delete evidence before the owner rules).

---

## 1. The board (keeper status, rubric v3.13, worst-of across every registered year)

Rule 30: every registered year gates the ISO. A cell lists only the failing criteria; `C3c` caveats inside the one-ledgerable budget are not shown.

| ISO | Keeper (bundle) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | ISO | Residual DOF in attestation |
|---|---|---|---|---|---|---|---|---|---|---|
| **NEISO** | `2026-09-26-neiso-119-anchor-fuelsec` (`neiso119_span`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (C1/C2 unscored, prelim 923) | **CALIBRATED** | 6 of 9 |
| **NYISO** | `2026-10-01-nyisonext26p-tslprint-span` (promoted 2026-10-02 on main, NEXT-32) | — | — | ✓ | ✓ | ✓ (C3c lone-ledgered) | ✓ | ✓ (C3a −9.6 %) | **CALIBRATED** | 6 of 22 |
| **MISO** | `2026-09-28-miso-280-splitremap` (`miso280_span`) | **C1 ST_GAS −8.0** | **C3a +11.6 %** | **C3b 0.201** | ✓ | ✓ | ✓ | ✓ (prelim) | NOT-YET | 2 of 44 |
| **SPP** | `2026-09-28-spp-100-chp-scope` (`spp100_arm_span`) | **C3a +11.5 %** | **C3a +27.5 %, C3b 0.343** | **C1 CC −9.7 / PRB +13.2, C4 gas 0.307** | **C1 CC −10.8 / PRB +13.2, C4 gas 0.356** | C3c | C3c | C3c (prelim) | NOT-YET | 3 of 5 |
| **ERCOT** | `2026-10-01-r-23-swcap-hourly` (`r_ercot23_span`; 3-config partition) | **C1 CC +8.9 / PRB −10.5, C3b 0.219** | **C1 CC +10.4 / PRB −11.8, C3b 0.221** | ✓ | **C1 CC −9.9** | **C3a −24.2 %, C3b 0.380** (2023 carve-out, owner hold) | **C3a −11.1 %** | ✓ | NOT-YET | 7 of 12 |
| **PJM** | `2026-09-30-pjm-next16-ovec` (`pjmnext16_A_span`) | **C1 COAL_BIT +18.7** | **C1 COAL_BIT +11.9, CC +9.8; C3a +12.4 %** | **C1 COAL_BIT +17.1, CT −9.6** | **C1 CC +10.9; C3a −11.5 %; C3b 0.253** | **C1 CC +8.5** | ✓ | ✓ (prelim; COAL_BIT +11.3 latent) | NOT-YET | 6 of 20 |
| **CAISO** | `2026-09-30-caiso-r20-overnight` (`rcaiso20_A_span` 2022–25 + fold 2019–21) | **C1 CC +10.8, C4 gas 0.39**; C3 unscoreable | **C1 CC +17.6, C4 0.41**; C3 unscoreable | **C1 CC +10.2, C4 0.36, C3a +12.5 %** | ✓ | ✓ | ✓ | ✓ (prelim) | NOT-YET | 6 of 9 |
| **SOCO** | `2026-09-30-soco96-measured-oil-burn` (`soco96_span`; system-lambda reference) | **budget: C1 COAL_BIT −10.6 + C3a +14.3 %** | C3a +14.5 % (ledgered) | ✓ | **budget: C3a −12.0 % + C3b 0.266** | ✓ | ✓ | ✓ (prelim) | NOT-YET | 1 of 32 |
| **NWPP** | `2026-10-01-nwppnext16c-combined-vintage` (`nwppnext16c_span`; no price reference) | phys ✓ | phys ✓ | phys ✓ | phys ✓ | **C4 coal r 0.669 / 0.313** | phys ✓ | phys ✓ (prelim) | NOT-YET (price unscored) | 3 of 4 |

Units: C1 in TWh against a ±8 TWh / ±3 pp band (CAISO ±4.6–5.3 TWh); C3a % vs RT load-weighted mean; C3b NRMSE ≤ 0.20; C4 r ≥ 0.70 and NRMSE ≤ 0.30. "Residual DOF" counts attestation entries identified on a residual rather than a measurement (rule 21); the offer-band surface and `wefor_multiplier` 0.7 are the recurring ones.

**Read of the board (updated 2026-10-02 after main moved).** NYISO is now CALIBRATED (PR #6992 arm B promoted as NEXT-32). Two ISOs are one ruling away from a determination change (SOCO: a budget ruling; NWPP: a price-reference ruling). Three are blocked mainly by missing free data the owner can fetch (CAISO 2019–21 OASIS prints; ERCOT 2019–22 60-Day disclosures; SPP rail-service series). Two carry misses that the records say are commitment-state or operator-conduct phenomena the energy-only LP cannot express (PJM coal loading, SPP 2019–20 body, ERCOT 2023 ECRS era, MISO 2020 low-load margin) and need either a structural lever named below or an honest frontier statement. NEISO is closed and needs a regression guard.

---

## 2. Cross-ISO workstreams

| ID | Workstream | Why | Deliverable | LP |
|---|---|---|---|---|
| **W0** | **EIA-860 capacity / vintage / COD settlement** (§2.1) | 36 recorded 860-class defects in four months; the pattern is structural, not carelessness | a settlement spec, a committed per-ISO-year fleet census, regression tests, one default posture everywhere | zero, then one span per ISO |
| **W1** | **Scoring-reference gaps** | Gates read SKIP where the reference is missing, so an ISO cannot even fail honestly | MISO 2019–21 RT tail (derive only); CAISO 2019–20 LMP (OASIS history); NWPP C3a/C3b reference (FERC-714 lambda, STOP-gated); MISO 2022 Nov–Dec hub; EIA-923 2025 final everywhere | zero |
| **W2** | **Residual-DOF retirement** | Every keeper but SOCO still carries residual-identified free parameters; an expert reviewer will ask for each one | replace `wefor_multiplier` 0.7 with a measured wind availability input or delete (audit C-15, open since June); ledger or replace `battery_dispatch_adder` (ERCOT 10, CAISO 5), `CHP_BTM_PCT` 35 (ERCOT), `WECC_import_simultaneous.cap_mw` 7,500 (CAISO fallback), fitted import/export tranches (CAISO, NYISO), `NYISO_LOCAL_SELFSUPPLY_FRAC` 0.45, `caiso_ra_min_load_frac` 0.26 (measured 0.570) | zero-LP census first; one span per ISO |
| **W3** | **C3c tail: one classification per ISO** | NYISO and SPP read C3c `FAIL` (unledgered) in 2023–25; NEISO carries three inconsistent auto-labels; MISO/CAISO/ERCOT mix "measured-input" and "model-class" | one owner-signed `model-class` exceptions entry per ISO after a zero-LP decomposition (DA vs RT tail, reserve vs congestion component) | zero |
| **W4** | **Keeper hygiene (rule 15)** | ERCOT, MISO, NWPP keepers lack `unit_marginal_<Y>.parquet`; MISO/CAISO attestations carry a null `authorized_price_tuning` while using the rule-1 channel | re-stamp from legs or at next promotion; declare the channel | zero |
| **W5** | **Benchmark-basis rulings (ISO-agnostic)** | SPP-87/88 and PJM-NEXT-20/21 show the C1 coal/gas residual is partly EIA-923 vs EIA-930 basis (gross/net, metering coverage); zonal load-weighted C3a adopted for NYISO/MISO but not PJM | one owner ruling on the coal basis and gas-coverage alignment; one on zonal C3a for PJM | zero |

### 2.1 W0 — the EIA-860 settlement

**Verdict of the audit** (`AUDIT-eia860-capacity-vintage-settlement-2026-10-02.md`, zero LP, census CSVs beside it): the pipeline is sound in shape (vintage per solved year, month-precise COD, per-unit COD since card S12, an always-on CC phantom guard) but **not settled**, for six structural reasons. Fixing them once, everywhere, is what stops the monthly rediscovery.

| # | Why 860 keeps coming back | Evidence | Settlement rule |
|---|---|---|---|
| 1 | **The vintages are incomplete.** `vintage_2023` and `vintage_2024` carry no retired-and-canceled sheet; 2025 solves on the 2025 Early Release; the ER retired sheet is 30–95 % pruned (PJM 2019 retirements 7,579 MW in the vintage sheet vs 2,108 in the ER; NYISO 2020 2,126 vs 117). `mid_vintage_exit_carry` is reconstructing 2023/24 exits from that pruned sheet. EIA published **Final 2025** on 2026-09-10; EIA-860M is not on disk at all. | audit §A.0, §C.5 | **E.2/E.5**: solved year Y reads the Final release for Y with its full sheet set; 2025 reads `vintage_2025/`; actual `Retirement Month/Year` from the retired sheet of the first vintage listing it; `Planned Retirement` is never read in a backcast (it binds 0 MW in every ISO-year); 860M is a forecast-only layer |
| 2 | **No single capacity basis.** Loader pmax = net summer else nameplate, year-round; five flags answer "which rating in which month" and no two keepers agree (PJM/NYISO/NEISO/CAISO nameplate-basis CC; MISO/SPP/NWPP/SOCO net-summer; the flat 10/12.5 % class derate double-counts on net-summer CTs in six keepers). Measured spread: winter/summer +3–9 %, nameplate/summer +9–17 %. | audit §A.2, §A.3, §C.1 | **E.1**: the LP bound in month m is the published seasonal capability of the solved year's vintage (Summer Jun–Sep, Winter Oct–May), nameplate only where both are blank, never above max(nameplate, CAMPD p99.9); the flat class derate is deleted for plant-level fleets |
| 3 | **Correctness repairs armed in one ISO, `U` in eight** (rule 25 treats a registry-read fix like a tuning): `commission_year_cod_fallback` (MISO only; seven ISOs still age-derate off a literal 2010), `cc_block_summer_rating` (MISO), `cc_steam_part_capacity` (MISO), `retiree_vintage_status_scope` (MISO/NYISO), `admit_standby_units` (NWPP), `partial_plant_exit_carry` (4), `mid_vintage_exit_carry` (6; off in ERCOT/CAISO/SOCO). `iso_configs.py` carries none of them. | audit §A.3, §B | **E.3/E.4 + Q4**: owner declares the class "structural, default-on in backcast everywhere" (the F1 pattern: default flip + `--no-…`); per-ISO zero-LP census is the only gate |
| 4 | **Unscreened populations** (zero-LP census, 9 ISOs × 7 years): SB 1.5–2.5 GW in PJM and MISO every year; OA 2.3–3.1 GW NWPP; thermal OP rows with a blank summer rating (nameplate-filled) MISO 3,924 MW, SOCO 1,772, SPP 883, PJM 746; rows with summer > nameplate (block-on-one-row) 136–156/yr MISO, 76–100 PJM, 48–58 SOCO. Only MISO's non-NG blocks are screened. | audit §C.2, §C.3 | **E.3**: the miso-126 steam-part and miso-272 block-reallocation predicates run everywhere; **E.4**: admit OP+SB everywhere and make the EIA-923 benchmark the same population |
| 5 | **Plant grain loses unit facts, crosswalk by hand.** Eight ISOs bin per plant×class; ERCOT uses a hand CSV (Fusco 676 MW was simply absent). Every unit-grain fact (brownfield COD, single-unit retirement, GT inside a CC, coal→gas conversion) resurfaces as a phantom: Vogtle, Homer City, Sherco-2, Parish, Bridger. CEMS↔EIA splits are fixed one `CAMPD_UNIT_PLANT_REMAP` row at a time although the EPA crosswalk is on disk. | audit §B.1 | **E.3/Q5/Q7**: unit grain is the record of truth; EPA CAMD-EIA + PUDL subplant ids are the crosswalk of record (hand remaps only as cited overrides); ERCOT CSV audited per vintage now, migrated later |
| 6 | **No committed fleet census.** Only PJM's bundle carries `unit_marginal_<Y>.parquet`; `legitimacy_diagnostics` rebuilds a different fleet; nobody can diff "what the LP carried" against EIA-860 or an ISO report, so drift is found by price residuals. PJM 2023 model Σcap 175,310 MW vs vintage summer 170,912 / winter 179,922 / nameplate 186,265. | audit §C.6 | **E.7**: per ISO-year `fleet_census_<Y>.json` in every keeper bundle (class | 860 nameplate/summer/winter | model Σpmax | peak-month available | ISO report | Δ), built by one script, refused by `promote_keeper.py` preflight when absent; tolerances 1 % class / 0.5 % total vs 860, 3 % vs ISO report |

Plus **E.6** (BA membership at load time, never at derive time — SPP-40, SOCO AEC and PJM OVEC were one defect three times; ownership shares never split a unit) and **E.9** (rule-23 freeze: 860 inputs re-derive only on an EIA Final release, an 860M month in the forecast base year, a crosswalk release, or a scope change; `solve_surface.json` carries the sha256 of each vintage directory read). Eight regression tests are named in audit §E.8. The cross-check of record per ISO: ERCOT CDR unit lists; NYISO Gold Book Table III-2; ISO-NE CELT §2; CAISO NQC list; PJM IMM SOM §12; MISO PRA + OMS survey; SPP RA report; WECC L&R/WARA; **EPA NEEDS everywhere** as the unit-level independent list.

**W0 execution (one foundation lane, then one re-solve per ISO):**

| # | Step | LP |
|---|---|---|
| 0 | Owner rules on Q1–Q8 (§5); owner downloads EIA-860 Final 2025 + re-downloads the 2023/2024 zips (§4 rows 1–3) | 0 |
| 1 | Rebuild `vintage_2023/2024` with retired sheets; build `vintage_2025/`; regenerate `eia860_generators.parquet` unfiltered (E.6); intake NEEDS + PUDL crosswalk | 0 |
| 2 | Implement E.1 (seasonal basis), E.3 predicates everywhere, E.4 status admission + benchmark parity, E.5 retirement rule, `build_fleet_census.py`, the eight tests; flip the Q4 flags default-on with `--no-…` escapes | 0 |
| 3 | Per-ISO zero-LP census: vintage fleet vs model Σpmax vs ISO report, every year; ERCOT CSV audited against vintage_Y (the "DAM site with no accepted EIA plant" check); NYISO Gold Book, ISO-NE CELT, PJM IMM §12 reconciliations committed | 0 |
| 4 | G-DRIFT classification per ISO (rule 29): every hunk LIVE → one full-span re-solve per ISO, promoted on structure (rule 1) with the census in the bundle; NEISO regression tripwire (C3a > 2 pp) armed first | 9 × 7 shards |
| 5 | Freeze (E.9): the next re-derive is the Sept-2027 Final release | 0 |

Side observation for the NWPP lane, **resolved 2026-10-02 (closeout-NWPP, PR #7028)**: the 68.6/68.7 GW 2019–20 EIA-930 NWPP peak is an AVA raw-`Demand` artifact that is never on the solve path; the Adjusted-demand peaks are 46.5/43.3/49.7/49.4/49.3/52.6/51.0 GW (2019–2025), so there is no discontinuity in the pool's demand input.


---

## 3. Per-ISO close-out plans

Each block: the failing gates → the diagnosis the records settle → retests with their new evidence (rule 28) → new levers (rule 13 story stated) → the ordered sequence with the pre-fixed reading and an honest probability → what to ledger. "P" is the shard's probability that the step closes its gate, not that it improves fidelity. Full detail and citations: the ISO's `SHARD-*` report.

### 3.1 NYISO — CALIBRATED since 2026-10-02 (NEXT-32 promoted arm B); protect it and close the C3c classification

| Gate | Diagnosis (record) | Route |
|---|---|---|
| C3a 2025 −11.6 % | Transco Z6 daily print level lost to calendar renormalisation; two solved zero-DOF arms already pass: PR #6987 arm A (`nyiso_gas_daily_print_level`) → −9.6 %; PR #6992 arm B (A + `nyiso_li_tsl_all_hours`) → −9.6 % and Zone K −10.1 % | **owner ruling, 0 LP** |
| C3c 2023/2024 (0/0 h vs 10/13 h > $300) | RT-only events: DA actual tail 1 h / 0 h; all missed hours Long Island top-of-load; SOM 2024/25 attribute to RT reserve shortage, GTDC transmission-shortage steps, offline-GT pricing, TSAs | zero-LP decomposition → ledger as model-class (W3) |
| C3c 2025 (8 vs 42 h) | Jun 23–25 2025 cluster: 17.1 % of fossil unavailable vs 6.4 % EFORd (2.4 GW gap), neighbour emergency import cuts (ISO-NE OP-4 on 6/24), 213 MW unscheduled emergency capacity; model shows only NYC 10-min shortfall at the $25 cap | phase-0 availability audit; neighbour-emergency import rule (default off) if admissible |

Retests with new evidence: `nyiso_spin_reserve_online` (I) — its inertness condition ρ ≥ ρ* 0.34–0.46 no longer holds at the measured ρ 0.3014 after the RHO_CLIP ruling; `tsa_transfer_derate` (G) — SOM 2025 now publishes the 1–2 GW magnitude class (limits still need the T&D Operations Manual); `scuc_load_pocket_commitment` (G) — Potomac now publishes NYC reliability-commitment MW tables. Not re-opened: measured offer surface, CC winter capability, temp derate, firm imports, measured interface limits.

| # | Step | Gate | Pre-fixed reading | P | LP |
|---|---|---|---|---|---|
| 0 | **DONE on main 2026-10-02 (NYISO-NEXT-32):** keeper `2026-10-01-nyisonext26p-tslprint-span`, ISO CALIBRATED, C3c lone-ledgered (0.4 pt C3a-2025 margin). | C3a 2025, ISO | — | done | 0 |
| 1 | Tail decomposition on disk (RT zonal components, `rtasp`, TSA hours, DA LBMP) + free MIS intake of RT limiting constraints | C3c 2023–25 class | ≥ 80 % of 2023/24 missed hours RT-only with a reserve/congestion component → ledger | n/a | 0 |
| 2 | Jun 23–25 2025 availability audit on the keeper sidecars vs CAMPD capability | C3c 2025 | model available thermal − CAMPD max ≥ 2 GW → owner card on admissibility | low–med | 0 |
| 3 | Neighbour-emergency import curtailment phase 0 (P-32 vs ISO-NE OP-4 window) | C3c 2025 | ≥ 500 MW modelled import in cut hours → build event rule, 5 shards | low–med | 0 → 5 |
| 4 | `nyiso_spin_reserve_online` at measured ρ; `tsa_transfer_derate` coverage | C3c 2025, C3a 2025 | June hours gain reserve duals; C1/C8 unchanged | low | 0 → 5 |
| 5 | Gold Book ↔ EIA-860 per-unit reconciliation (W0 artefact; DMNC vs net summer, peaker-rule retention dates) | fleet | misalignments ≤ 1 % of NYCA ICAP | high | 0 |
| 6 | Re-score 2025 C1/C2 on EIA-923 2025 final | C1 2025 | PASS | med | 0 |

Ledger (model-class): C3c 2023/2024 (RT-only), Central-East congestion deficit on a 5-zone network, uncapped-hour Zone-K import-set congestion, DA–RT forecast-risk wedge.

### 3.2 NEISO — closed; protect it

Keeper CALIBRATED on 2019–2025 with one authorized price-tuned scalar (fossil level 0.9547, declared) and an 88-scalar band surface identified in-sample. The two neiso-119 arms are zero-DOF. Thin spot an expert will flag: C3a passes by compensation (RT ≤ $25 hours lifted +$1–5, peaks under-priced; diurnal amplitude 24–30 % of measured, unscored).

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 1 | Reconcile the three C3c caveat labels (2022 "model-class", 2023/2025 "measured-input") into one owner-signed entry; re-score 2025 on EIA-923 final | hygiene, C1/C2 2025 | determination unchanged; 2025 loses "with-caveats" | high | 0 |
| 2 | Rule-14 accuracy repairs, no gate claim: Algonquin daily is Wednesday-only prints (Elliott gas reads $12.5–15 vs IMM $35.37) — transcribe event-week dailies from FERC/NERC and EIA notes; NY Harbor ULSD daily to 2019; ISO-NE nested reserve requirements 2019–22 | inputs | input diffs cited to data (rule 23) | n/a | 0 |
| 3 | One scarcity-physics arm, 7 legs: `gas_daily_shape` on the completed AGT series + ULSD daily + response-scoped reserve eligibility (rule 18: 2,855 MW of oil steam currently counts as 10-min reserve) + measured nested requirements replacing the three static rows (rule 19) | C3c 2022/2025 fidelity | Dec 24–27 2022 model price at oil parity; no C1/C3b change; promote on rule 1 if nothing regresses | low (gates), high (fidelity) | 7 |
| 4 | Regression guard for W0: `lp_input_diff` census on 2019 and 2025 fleets; Pilgrim 1590 / Mystic 1588 carries, Kendall basis, Canal 3 class byte-stable; C3a move > 2 pp is the tripwire | W0 | — | — | 0 |

Retests with new evidence: `dynamic_reserve_requirements` (R) — 2019–22 data fetchable since rule 22 was removed and the published columns are nested (static rows overstate by 1,246 MW); `dam_availability_rebasis` (R) — the neiso-62 denominator objection is now addressable per class. Ledger: C3c 2022/2023/2025 as model-class after step 3 (2022 needs ≥ 59 h; real reserve-short hours were 1.4 h in 2022).

### 3.3 MISO — three routed misses, one derive gap, one real lever

| Gate | Diagnosis (record) | Route |
|---|---|---|
| C1 ST_GAS 2019 −8.003 TWh (band 8.00) | ~7.6 TWh of out-of-merit MISO-South steam on MTEP15 VLR-eligible plants (Ninemile, Sabine, Lewis Creek, Little Gypsy, Waterford); level unpublished → `scuc_load_pocket_commitment` G | do not build for a 3 GWh miss; closes only on an incidental rule-14 move or a published pocket limit |
| C3a 2020 +11.6 % | all-years low-load level shift: model low-load margin is gas CC 65 % + seam 28 % + coal 7 % vs IMM coal ~40 % off-peak; coal curve has a hole between the ~$9 committed band and the ~$30 econ band where the real margin (~$15) sits; ~4.4 pts is West/Plains congestion (G) | L3/L4 committed-band continuum; honest ceiling ≈ +7 % |
| C3b 2021 0.201 | Feb Uri 24 % (routed) + Sep–Nov fall coal conservation 60 % (IMM: reference-level adders on 18→8 GW of coal) | per-year transport closed (miso-299); conservation is now admissible under ruling D-P7 (measured receipts/stocks as a fuel-availability overlay) — the next MISO lever |
| C3c 2019–21 SKIP | no committed RT tail; `derive_actual_tail.py` ungated since 2026-09-09 and the hub series is on disk; zero-LP pre-read: 17/8/48 h | **derive now** → 2019 CAVEAT, 2020 PASS, 2021 CAVEAT |

Retests with new evidence: `coal_prb_committed_dispatchable` (R 07-31) and `coal_prb_committed_split` (R 08-01) — adjudicated for the retired C7 amplitude criterion on a 2023–25 keeper before measured coal HR, the yard-grain budget, the dispatched-bin denominator and the zone-resolved basis; miso-296/297's census (7 % vs 40 % low-load coal margin, "shape not level") is new evidence on exactly the committed-band question. `miso_coal_night_floor` stays I.

New levers: L1 per-year variable gas transport from own-year EIA-923 receipts (the miso-298 successor; ceiling C3b 2021 → 0.192); L2 Max Gen declaration registry 2019–21 + pre-Sep-2021 emergency floor vintage (registry has no 2019/2020 rows; VOLL was $3,500, the $500/$1,000 tiers date from Sep 2021); L3 coal econ offers at measured incremental HR (≤ ~$1 at q1–q2 alone); L4 committed-band continuum (cycling slice at incremental cost, take-or-pay sunk only to contract minimum; must replace, not stack on, the take-or-pay discount); L5 PTC-vintage wind offers (≤ +$0.25); L6 VLR pocket constraint (blocked on a published MW).

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0a | `derive_actual_tail.py`, commit the 2019–21 rows | C3c SKIP | three SKIPs scored; determination unchanged | high | 0 |
| 0b | Max Gen registry transcription (owner browser download) + floor vintage with a constants citation | inputs | windows priced only where slack binds | high (hygiene) | 0 |
| 1 | ~~L1 per-year transport table~~ **CLOSED on main 2026-10-02 (miso-299):** the pre-stated rule failed on the training tier (2023–25 CC fuel moves +0.25/−0.07/−0.12 $/MMBtu vs the frozen table; 2023 static error worsens); FINDING only, both R cells stay R. A per-year re-fit is a lag correction, not a transport measurement. | C3b 2021 | — | closed | 0 |
| 2 | L3 + L4 census: MISO incremental-HR ratio; low-load coal marginal share and q1–q4 price at the keeper quantity | C3a 2020 | ≥ −$1.0/MWh at q1–q4 with COAL_PRB 2019/21/22 in band | low–med | 0 → 7 |
| 3 | One full span carrying 0b + whatever passed; writes `unit_marginal_<y>` (rule 15, required for any promotion) | all | kill rules ex ante (PRECOMMIT-miso298 §5 pattern) | — | 7 |

Ledger: West/Plains congestion share of C3a 2020; C1 ST_GAS 2019 without a published VLR level; C3b 2021 February; fall-2021 conservation unless the owner admits measured stocks; C3c tails.

### 3.4 SPP — a scorer-basis question, one repaired lever, and a rail series

| Gate | Diagnosis (record) | Route |
|---|---|---|
| C3a 2019 +11.5 %, 2020 +27.5 %; C3b 2020 0.343 | body over-price: thermal that stays online at sub-cost prices (commitment state; SPP-74/75/79/102/103) coupled to an unexplained 2022+ upper-tercile premium, so a body fix alone breaks 2023–25; MMU: 36/31/30 % of 2020–22 energy self-committed, 2020 RT negative intervals ~11 % | commitment posture + SPP-104/106 pairing protects the train tier; 2019/20 → ledger as commitment-state |
| C1 2021/22 CC −9.7/−10.8, PRB +13.2/+13.2; C4 gas 0.307/0.356 | DA-commitment of CCs (all of 2021, ~60 % of 2022) + the 2022 coal rail/markup object (~40 %, SPP-89; ASOM 2022 names rail supply-chain problems and RR502 opportunity-cost offers); on the EIA-930-aligned gross basis coal is over by +2.0/+5.5 TWh, not +13 (SPP-87); EIA-923 carries 2.7–5.1 TWh/yr of gas outside SPP metering (SPP-88) | **W5 basis ruling first**; STB rail series re-opens SPP-44 |
| C3c 2023–25 FAIL (0/7/2 vs 42/59/68 h) | 5-minute ramp scarcity + $200+ RT markups (SPP-29); reads FAIL only because the lone-failure guard is lost while validation rows fail | W3 ledger; reverts to a caveat once validation rows close |

Retests with new evidence: `spp_commitment_posture` (R) paired with the since-solved upper-tercile movers SPP-104/106; `energy_reserve_coopt` (I) conditional on no commitment state → re-measure on a posture bundle; `coal_fuel_inventory` / deliverability (R, SPP-44) because the "different dataset" it named exists free (STB EP 724 weekly BNSF/UP coal unit-train loadings vs plan by basin). Not retests: curtailment ceiling, gas bridge, offer-band retunes.

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0a | Shadow-score C1 2021/22 on the EIA-930-aligned basis with the SPP-88 gas-coverage correction | C1 2021/22 | CC 2021 ≥ −8.0; PRB 2021/22 within ±8.0 | med (PRB) / low–med (CC 2021); needs the W5 ruling | 0 |
| 0b | CT pmax basis vs `SUMMER_CLASS_DERATE` audit (W0 double-count item) | hygiene | one-line fix or none | n/a | 0 |
| 1 | SPP-107: MMU offer-side unavailability with its two definitional repairs, 7 shards — **DONE 2026-10-02, PROMOTED** (keeper `2026-10-02-spp-107-mmu-repair`; unserved 862/136 → 443/44 MWh, C4 2021 PASS, PRB 2023/24 +1.08/+1.35, no train flip) | C4 gas 2021, PRB 2023/24, train C3a | unserved ≤ keeper; C4 2021 ≤ 0.30; no train flip | high (C4 2021) | 7 |
| 2 | Pairing span: `spp_commitment_posture` + SPP-107, one PRECOMMIT | train C3a, C3b 2020 | 2024 C3a within ±10 %; 2020 C3b falls (direction) | med / low | 7 |
| 3 | Owner downloads STB EP 724 → SPP-44 re-measure; if 2022 PRB loadings-vs-plan is anomalous, PRECOMMIT the RR502-form adder keyed to it | C1/C4 2022 | 2022 is the only anomalous year | low–med | 0 → 7 |
| 4 | West/East partition ruling (SPP-93) | zonal spread, C3b 2020 floor half | C-3 margin repaired on measured East capability | low | owner-gated |
| 5 | Ledger C3a 2019/20, C3b 2020 (commitment-state), C1 CC/C4 2022 if step 3 fails, C3c 2023–25 | — | — | — | 0 |

### 3.5 ERCOT — two admissible levers, one data decision, one 2023 ruling

Three-config partition (forward 2024–25; 2023 carve-out with peak bands × 33, owner hold; 2019–22 validation). R-ERCOT-24b (published ORDC μ/σ curve, 7 shards) is in flight with its owner card signed.

| Gate | Diagnosis (record + IMM) | Route |
|---|---|---|
| C3a 2023 −24.2 %, C3b 0.380 | Potomac SOM 2023 §II.H: ECRS sequestration and non-deployment "doubled" Jun–Dec RT prices (> $12 B through Nov; spikes "did not reflect true shortages"); whole gap is Jun–Sep; model is reserve-co-optimized (RTC+B-like), 2023 ERCOT was not; ECRS-neutral LW ≈ $35 vs actual $62–65, model $49 | **owner ruling** (hold to Door D 2026 RTC+B year, or an IMM-counterfactual band amendment); not closable structurally |
| C3a 2024 −11.1 % | hub-basis gap only −3.7 %; LZ/West congestion basis ≈ +$2.4 (West LZ premium in 2,847 h; model prints 0 because West ≡ North every hour); IMM 2024 ECRS excess ≈ $2.16/MWh of load | L2 West import-direction rating (≤ 4 pts) |
| C1 2022 CC −9.9 | coal mirror: EIA-923 identity shows Martin Lake 2022 model 16.64 TWh vs delivered fuel 12.59 (receipts 11.89 + stock draw 0.70); Coleto 4.32 vs ≈ 2.7; IMM 2022: coal fell on "fuel supply and other supply chain issues" | L1 coal fuel-delivery ceiling (ERCOT arm of `coal_fuel_inventory`, K in MISO) |
| C1 2019/20 CC +8.9/+10.4, PRB −10.5/−11.8; C3b 0.219/0.221 | keeper prices 2019–22 coal on 2024–25 SCED conduct (PRB delivered $2.55–2.66); C3b is a summer over-scarcity (Aug carries 73 %/61 % of SSE) coupled to the coal under-run | only route is the 2019–22 60-Day SCED/DAM disclosures (free, behind an ERCOT account the owner closed 2026-07-05) |

Retests: none of the R/I/G cells has genuine new evidence; `coal_offer_level_rebasis` (R) has the wrong sign (fuel-indexing raises coal offers) — recorded so nobody re-opens it; `internal_congestion_split` (G) stays closed for sub-zonal splits, but a West *import-direction* rating at the existing zonal grain is a rating repair with the ercot-234 EASTEX precedent, not a split.

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0a | Finish R-ERCOT-24b as precommitted | 2019/20 C3b, 2020 C3a | adder → 0.81–1.06× RTORPA; C3b −≤ 0.02 (still FAIL) | low (gate), structural regardless | 7 (in flight) |
| 0b | L1 census: per PRB plant-month, fuel-feasible energy = (receipts + stock_{m−1} − stock_min)/HR vs model MWh | C1 2022 | Martin Lake and Coleto bind in 2022; nothing binds 2019–21/2023–25 except Coleto Sep 2021 | n/a | 0 |
| 1 | ERCOT arm of `coal_fuel_inventory` (monthly grain, stock_min declared ex ante), full span | C1 2022 CC, PRB | CC −9.9 → −4..−6 (PASS); PRB +5.8 → ≈ +0.5; 2024 C3a unchanged | **med-high** | 7 |
| 2 | L2 census on the NP6-86 binding-constraint archive: West-import constraints' limit-at-bind vs the +$1.30 system-LW West premium | C3a 2024/25 | ≥ 70 % of > $5 premium hours coincide with a measured West-import bind → build | med | 0 |
| 3 | Asymmetric West link (import rating), full span | C3a 2024 −11.1 %, 2025 −9.2 % | 2024 → −7..−9 (PASS); 2019/20 C3a +1 pt (still PASS) | med | 7 |
| 4 | Owner re-opens the free ERCOT account → 60-Day SCED/DAM 2019–22 → per-plant coal offer tables (ercot-168 construction, zero DOF, rule 23), full span | C1 2019/20 both classes, C3b 2019/20 | PRB −10.5/−11.8 → −3..−6; Aug over-price shrinks | high if data, else not closable | 7 |
| 5 | Owner ruling on 2023 (§5 D-E1) | C3a/C3b 2023 | — | the only honest closes are (a) hold to Door D or (b) a rubric amendment | 0–1 |
| 6 | Hygiene: `unit_marginal_<Y>` into the keeper; DAM-crosswalk membership census (62/303 sites accepted; "DAM site p98 HSL with no accepted EIA plant" is the Fusco class of miss); Capacity-Changes-by-Fuel-Type COD cross-check vs EIA-860M | W0/W4 | — | — | 0 |

Ledger: 2023 C3a/C3b at the actual-RT target (operator-conduct regime); C3c 2021/22/24/25; the intra-zone LZ congestion basis (≈ +$2/MWh of C3a every year); 2019/20 coal conduct if the account stays closed.

### 3.6 PJM — the coal loading response, Elliott, and the basis ruling

| Gate | Diagnosis (record, NEXT-10..23) | Route |
|---|---|---|
| C1 COAL_BIT 2019/20/21 (+18.7/+11.9/+17.1; 2025 +11.3 latent) | the LP's in-merit loading response is steeper than real coal in every year (in-money loading 0.97 vs real 0.88); PJM-NEXT-24 (2026-10-02, main): the excess is **within-plant** loading (keeper contrast 0.56–0.69 vs real 0.19–0.30 in 2019–21), while the CT deficit is **across-plant** ordering (2–3.5× real; real CTs start about twice as often, half their energy in out-of-money shoulder hours); ~15 levers falsified | L1 coal in the per-generator reserve pool (bound 3–6 TWh/yr); otherwise frontier. Hygiene: Tait 55248→2847 one-entry CAMPD remap (NEXT-24 card 3) |
| C1 CC 2020/22/23 (+9.8/+10.9/+8.5) | 2023 = Dominion −12.7 / EMAAC +9.0 zonal offset from the unposted Peach Bottom–Conastone corridor (G) + Dominion EIA-923 gas +1.63 over eastern spot + ~10 TWh benchmark (923 vs 930) drift; 2020/22 loading-when-on, same north-over/south-under signature | W5 basis ruling; L4 only if a weekly Z5/M3 series is ruled admissible |
| C1 CT 2021 −9.6 | dear CTs (Doswell, Tait, Louisa, West Lorain) run at half their modeled offer; IMM 2021: CTs took 85.7 % of balancing credits (out-of-merit commitment) | ledger (inadmissible as a lever) |
| C3a 2020 +12.4 % | all-year bulk price floor too high (implied HR p10 6.9–8.4 vs 4.8–5.5), unmasked in 2020 with no peak-leg offset | L2 incremental-HR pricing of the price-setting CC tranche (≈ −$1/MWh; helps, does not close) |
| C3a −11.5 %, C3b 0.253, C3c 2022 | Winter Storm Elliott alone: 18 h carry 84 % of the gap; keeper max $124.9 on Dec 23–26, reserve duals 0.0; ~20 GW of published forced outage never enters the LP (CAMPD short windows recover 11–13.6 of 31–36 GW) | retest `pjm_measured_outage_event_cap` add-side; L3 event overlay; else one-event caveat |

Retests with new evidence: `pjm_measured_outage_event_cap` (R, pjm-161, tested remove-only on 2023–25) → add-side Elliott window now that 2022 is in span and `gen_outages_by_type` is on disk; `gas_offer_margin_anchor_vintage` (R, pjm-169) — killed by an S4 gate its own record calls confounded, and it moves C3a 2020 and 2022 in opposite correct directions; `winter_citygate_daily` (R) stays data-blocked. Do not retest `committed_band_measured_basis` alone. Matrix hygiene: `coal_drop_pof` is armed in the keeper but the PJM cell reads U.

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0a | Capacity reconciliation: EIA-860 vintage (+carry) vs IMM §12 installed MW by fuel at each 31 Dec 2019–25 (2020 reads 46.4 GW canonical vs IMM 52.0 GW Mar-2020; Mansfield exit + OVEC are the known movers) | W0 / COAL_BIT 2020 | class MW within ±2 % or name the units | n/a | 0 |
| 0b | Elliott census: published forced outage − model unavailable MW, hourly Dec 20–28 2022 | 2022 | gap ≥ 15 GW in ≥ 18 h confirms L3 | n/a | 0 |
| 0c | Reserve-holding census: model `reserve_family` by class vs SOM §10 synch-reserve by unit type | COAL_BIT | coal ≥ 25 % of real synch reserve and ≈ 0 in model → charter L1 | n/a | 0 |
| 0d | Incremental-HR census: CAMPD heat-input slope for CC_REGULAR vs model econ-band HR vs `pjm_midcurve_belt` floor | C3a 2020 | gap ≥ 0.8 MMBtu/MWh cap-weighted → charter L2 (rule 19 reconcile with the belt) | n/a | 0 |
| 0e | Hourly marginal-fuel bench (free PJM file) vs `unit_marginal` | C3a 2020 | model coal-set share within 1.3× of PJM's | n/a | 0 |
| 1 | L1 full span | COAL_BIT 2019/20/21/25 | 2021 ≤ +8.0 (from +17.1); 2025 preserved; C8 PASS | low–med | 7 |
| 2 | L2 full span | C3a 2020 | ≤ +10 %; 2023–25 C3a stay inside ±10 % (they pass by cancellation) | low–med | 7 |
| 3 | Retest `gas_offer_margin_anchor_vintage` with a displacement-aware S4 written ex ante | C3a 2020 + 2022 | 2022 ≥ −10 %, 2020 ≤ +10 %, COAL_BIT 2022 PASS | low–med | 7 |
| 4 | L3 Elliott overlay (event-windowed add or temperature-driven `correlated_forced_outage`) | C3a/C3b 2022 | Dec 23–24 mean ≥ $800; C3b ≤ 0.20 | low (needs ≥ $1,500 for ~18 h) | 1 → 7 |

Ledger: C3c 2021/2022; CC 2023 corridor half (no published limit); CT 2021 (out-of-merit commitment). If CC 2023 stays at +8.4 vs 8.0 on ~0.4 TWh of benchmark drift, the owner rules on the rule-14 boundary (W5).

### 3.7 CAISO — one free data fetch reverses the fold ledger

| Gate | Diagnosis (record) | Route |
|---|---|---|
| C1 CC 2019/20/21, C4 gas fold, C3a 2021 | one object: DSW/WEIM import volume the model cannot buy without a measured Palo Verde/Malin hub print; OASIS GroupZip serves nothing before 2021-04-27; after R-CAISO-20 the DSW gap is −9.3/−15.2/−10.2 TWh; the clean rungs carry 0 MW in 2019–20 | **the ledger premise is now wrong**: CAISO's Historical OASIS Data Downloader (notice 2025-11-11) serves DAM/RTM price history back to 2016 from a requester-pays S3 bucket |
| C3a/C3b/C3c 2019–20 unscoreable | no measured LMP reference on disk | same fetch |
| C3c 2021 caveat 89 vs 27 h (model over-fires 3.3×) | never censused; candidates: 2021 SDGE LCT cap, $180 placeholder hours; "measured-input limitation" label is possibly wrong | zero-LP census of the 89 hours |
| C4 2025 margin 0.288 | CT_PEAKER priced out (1.09 vs 2.34 TWh) and import diurnal | every 2022–25 lever is read against this cell first |

Retests with new evidence: `zonal_gas_basis` (R, caiso-221 on 2023–25) — the cell carves out a measured NP15-winter case; 2021 is now scored and carries the largest measured PG&E−SoCal basis (−0.902 $/MMBtu, one-signed through May–Dec) ≈ −2.5 pp on C3a 2021; `caiso_ra_min_load_frac` 0.26 → 0.570 (measured CEMS p05) — the C3a-2025 fail that blocked it is gone (+6.6 %, 3.4 pt margin) and 0.26 is neither re-solved nor ledgered; `caiso_citygate_blackout_bridge` (O) zero-LP census on the 2019–21 prints. Not re-opened: sub-zonal topology (element-outage data not public), export-sink family, DA/RT two-settlement, CC must-run floors (wrong sign), CC winter capability.

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0a | ~~Owner: fetch OASIS 2019-01-01..2021-04-26 via the Historical OASIS Data Downloader~~ **REFUSED by the owner 2026-10-02 (requester-pays AWS egress).** Verified the same day: the public OASIS `SingleZip` endpoint returns `ERR_CODE 1000 / No data returned` for `PRC_LMP` DAM on 2019-07-15 and 2020-07-15 at `TH_SP15_GEN-APND` and `PALOVRDE_ASR-APND`, so no free hourly route exists. The only free price series for 2019–20 is EIA's ICE workbook (`NP15 EZ Gen DA LMP Peak`, `SP15 EZ Gen DA LMP Peak`, daily, **peak block only**, no Palo Verde intertie row) — a labelled daily DA-peak reference that could score a C3a/C3b-class reading under an owner card but cannot arm the DSW rungs. | every fold gate | the fold's DSW residual stays data-limited; R-CAISO-20's ledger stands | — | 0 |
| 0b | PNW/DSW net import vs EIA-930 by corridor/month on the fold sidecars (DSW −9.3 vs CC +10.75 in 2019 does not close without the PNW term) | C1 fold | R-CAISO-7 Object-1 style table | — | 0 |
| 0c | `zonal_gas_basis` 2021 sizing: NP15 λ shift = basis × marginal HR × CC-marginal share by month | C3a 2021 | ≥ 2 pp projected | med | 0 |
| 0d | Census of the 89 C3c-2021 hours | caveat class | count attributable to SDGE cap / placeholder | — | 0 |
| 0e | Optional 2021 probe leg on the Jan–Apr prints (throwaway, rule 16) | C1/C4/C3a 2021 | DSW Jan–Apr ≥ +5 TWh; C3a ≤ +10 % | med-high | 1 |
| 1 | Full span: extend `caiso_intertie_partial_year_measured` to every printed hour 2019–21; the R-CAISO-20 ruling flag goes dormant → delete (rule 26); 2022–25 byte-identical expected | C1/C4 fold, C3a 2021, C3 2019–20 scored | C1 2019 ≤ ±4.64, 2021 ≤ ±4.77; C4 NRMSE ≤ 0.30 | C1 med-high; C4 low–med (printed years sit at 0.247–0.288) | 7 |
| 2 | `caiso_zonal_gas_basis` on the step-1 recipe, with 2024 (+1.5 pp) and C4-2025 tripwires pre-registered | C3a 2021 | ≤ +10 % | med | 7 |
| 3 | `caiso_ra_min_load_frac` → 0.570 (rule 14), or ledger 0.26 as residual-identified | rule 21 | gates unchanged within noise | n/a | 7 |
| 4 | Link-15 joint gas re-basis (R-CAISO-33) as its own PRECOMMIT, last | legitimacy | C3a 2022 ≤ +10 %, C4 2025 ≤ 0.30 | low (fit), high (legitimacy) | 7 |

New zero-parameter lever for later: DSW formula-hub diurnal shape from the DSW BAs' own EIA-930 net load (code proxies with CISO's). Ledger: C3c 2024 (NW import parity, export sink R/G), Path-15 midday spread (Gates–Midway element limits not public), the RT h18 body residual (≤ $5.3). Owner ruling 2026-10-02: no requester-pays AWS fetch. End state for the fold without it: 2022–25 CALIBRATED; 2019–21 reported-only NOT-YET on a data-limited ledger (plus whatever the zero-LP steps 0b–0d and the `zonal_gas_basis` 2021 retest recover).

### 3.8 SOCO — the error is in the reference; one ruling, one zero-LP hour

Zero criterion FAILs; blocked solely by the caveat budget (3 ledgered rows vs 1). Southern's IIC §3.1/§3.6 dispatches on marginal *replacement* fuel cost (spot coal), VOM, losses, and recognises purchases at energy cost; the model prices coal at EIA-923 blended receipts. 2022 coal did not surge at Southern (bench 48.8→45.5 TWh); the model surges +7.5 TWh because 2022 spot coal was $100–170/ton vs the model's $3.18/MMBtu blended.

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0 | Owner ruling: is a λ-referenced BA with three scoped ledger rows eligible for CALIBRATED-WITH-CAVEATS, or NOT-YET by design (soco-95 §4: no other ISO moves either way) | determination | — | — | 0 |
| 1 | L1 phase 0: coal econ/peak tranches at same-month EIA-923 Page-5 spot receipts (fallback EIA weekly basin spot); greedy same-setter C3a/C3b all 7 years | C3a 2022, 2022 coal/gas split | pre-register: 2022 C3a improves ≥ 2 pp and no passing year leaves ±10 %, else do not build | low–med | 0 |
| 2 | If step 1 clears: `coal_marginal_replacement_pricing` (new default-off field, matrix row + 9 cells), 7 shards | same | zero status flips; 2022 coal toward 45.5 TWh | low (ledger row flip) | 7 |
| 3 | Pool-vs-BA benchmark-scope census and "purchases at energy cost" written into the ledger rows | ledger quality | — | — | 0 |
| 4 | Owner pulls Georgia PSC FCR / Alabama Rate ECR fuel testimony; only if a plant-grain minimum-take or inventory schedule exists, a windowed floor lane for 2019 | C1 2019 | floor binds only inside the documented window | low | owner 1–2 h |

Not closable in class: Elliott 2022 (EEA purchase pricing in λ), the night CC-setter ratio (licensed SE gas), 2019 self-commitment absent a dated contractual driver, the loss penalty factor. SOCO is last in priority: C1 41/42, C2/C4/C6/C8 pass every year.

### 3.9 NWPP — a price reference first, then one coal year

NOT-YET on one record (C4 coal 2023: r 0.669, NRMSE 0.313); coal 2022 and 2025 sit at r 0.712 (fragile). Root cause settled at plant level: Jim Bridger 2023 — Feb–May fuel conservation (record-low pile, Black Butte delivery shortfall; Utah PSC 24-035-04, BHE 10-K 2023) and a Jun–Oct trough from the model's flat within-month NWPP price ($34.0 every August hour; within-day SD ~1/10 of WEIM). Even at measured prices ~half the Jun–Oct gap survives (NEXT-17 §4).

| # | Step | Gate | Reading | P | LP |
|---|---|---|---|---|---|
| 0 | **DONE on main 2026-10-02 (NWPP-NEXT-19):** Henry Hub daily explains ~0–5 % of NW within-month between-day price variance; CAISO coupling adds R² 0.11–0.43 beyond gas; the measured price lifts the 2023 Jun–Dec coal shape (+0.10 r) but not 2024/25. The interface part dominates → lever B is next. | picks A vs B | — | done | 0 |
| 1 | ~~FERC-714 Part II Sch. 6 hourly system lambda for NWPP respondents as the pool price reference~~ **FALSIFIED AT ZERO LP, 2026-10-02:** the raw extract (`data/raw/ferc-714/nwpp_hourly_system_lambda_2019_2025_raw.parquet`, every NWPP filer, 2019–2025) shows only Nevada Power and NorthWestern (2021+) file a non-zero lambda; PacifiCorp, PGE, Puget, BPA, Tacoma, EWEB and the PUDs file zeros every hour, and Idaho Power/Avista/Seattle/Chelan/Grant file no facts. A demand-weighted pool lambda cannot be built. Residual question for the owner: is a single-BA NEVP or NWMT lambda admissible as a *labelled* reference, or does NWPP stay price-unscored (then the WEIM ELAP 2023-06+ series is the only measured hourly price in the footprint). | C3a/C3b scoring | — | closed as a pool reference | 0 |
| 2 | ~~Lever A `gas_daily_shape`~~ **REJECTED on main 2026-10-02 (NWPP-NEXT-19 arm G, owner card "Reject, keep #20"):** C4 coal 2023 0.669 → 0.677 (still FAIL), C4 gas r falls in every year. Cell R. | C4 coal 2023 | — | closed | 7 (spent) |
| 3 | **SOLVED, HELD 2026-10-02 (NWPP-NEXT-21, `RESULT-nwppnext21-priced-interface-2026-10-02.md`; owner card "Hold #20, fix seam headroom"):** structural gate PASS; C4 coal 2023 0.669 → 0.781 and price 2023 −21.4 % → −0.3 % clear, but C4 gas fails 5 years and C1 CC 3 years because the seams export 17–37 TWh/yr vs 7–21 measured on full path ratings (CAISO MALIN500 import OTC ~2,730 MW vs 4,800 registered). **Next: seam headroom from measured OASIS OTC (NEXT-22, zero LP first), then re-solve.** Was: **Lever B priced seam — now the next NWPP lever** (wired default-off at NEXT-19: `NWPP_external` node, seam-limit links, empty-priced-build refusal; owner card "Fix both, then solve" = NEXT-20: the CAISO seam's gross-load shape → net load, and the WECC_CAN peak-only Mid-C anchor) — the CAISO `WECC_import` double-count ruling (card N4) still applies | C4 coal 2023 Jul/Oct level | r ≥ 0.70, NRMSE ≤ 0.30 with coal 2022/24/25 still passing | med (price shape) / low–med (C4) | 7 |
| 4 | Lever C coal commitment bridge by parameters (`min_down_hours`, startup; rules 18/19 census of existing floors first) | C4 coal 2023 Aug–Oct | same | med (matches the residual shape) | 0 → 7 |
| 5 | Retest `coal_captive_marginal_fuel_price` (R, arm D) in composition with whichever of A/B/C lands | C4 coal 2023 | same | low–med | 7 |
| 6 | If Feb–May remains: scoped C4 ledger row (v3.10 "ledger as limitation") citing the documented delivery shortfall → PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED) | determination | — | — | 0 |

Verified today: EIA's free ICE workbook carries only "Mid C Peak" (no off-peak row), so a free daily two-block benchmark does not exist; the WEIM ELAP series covers 2023-06+ only. Not closable in class: the conservation year without a public plant-level stock target (rule 13); the commitment *decision* without MIP (a P1 bridge injects a detected state, not a chosen one). Hygiene: `iso_configs.py` docstring says `use_campd_bins=False` but the keeper runs True (docs fix); keeper lacks `unit_marginal_<Y>` on main.


---

## 4. Data the owner should download (all free; one table, highest value first)

"Unblocks" names the gates or workstream the data serves. Every item lands under `data/raw/` through the data-intake skill with a licensing note; nothing here is paid. Items marked ★ are the ones on which an ISO's close-out turns.

| # | What | Unblocks | Where (URL) | Directions | Lands in | Effort |
|---|---|---|---|---|---|---|
| ★1 | **DONE 2026-10-02** — EIA-860 Final 2025 landed as `vintage_2025/`; 2023/2024 retired sheets added; retiree parquet extended by 34 pre-2023 units (the ≥ 2023 subset is test-pinned). **Top-level canonical replaced by the Final 2025 (owner ruling 2026-10-02).** | W0 (every ISO's 2023–25 fleet) | https://www.eia.gov/electricity/data/eia860/ | ZIP column → `eia8602023.zip`, `eia8602024.zip`, `eia8602025.zip`; then `scripts/data/process_eia860.py --zip … --out-dir data/raw/eia-860/vintage_<Y>` and `--rejoin-heat-rate` | `data/raw/eia-860/vintage_2023..2025/` | 30 min |
| ★2 | **DONE 2026-10-02 (data)** — EIA-923 Final 2025 rows landed in both `_processed-legacy` parquets (generation 7,653 → 18,889 rows). **Pending:** the 2025 re-bench of every keeper (restore shared inputs + regenerate the 2025 bench parts + completeness + status), an owner-visible one-pass lane. | C1/C2 2025 in every ISO | https://www.eia.gov/electricity/data/eia923/ | `f923_2025.zip`; existing `fetch_eia923_generation_fuel.py` | `data/raw/eia-923-generation-fuel/` | 15 min |
| ★3 | **ERCOT 60-Day SCED Disclosure 2019-01 → 2022-12** (NP3-965-ER; `60d_SCED_Gen_Resource_Data_*.csv`, TPO/offer-curve columns for the 10 coal resources) and **60-Day DAM Disclosure 2019-01 → 2022-10** (NP3-966-ER) | ERCOT C1 2019/20 (both classes), C3b 2019/20 | https://www.ercot.com/mp/data-products/data-product-details?id=NP3-965-ER and `…?id=NP3-966-ER` → Data Product Archive (free account at https://www.ercot.com/services/mdt/data-portal or the Public API at https://developer.ercot.com/) | Re-open the free account closed 2026-07-05; download the monthly zips; keep the on-disk parquet naming `60_DAY_*_<Y>_<Mon-Mon>.parquet` | `data/raw/ercot/` | 2 h (≈ 46 + 48 zips) |
| ★4 | **ERCOT NP6-576-ER "LOLP Distribution by Season and TOD Block"** 2018-12 → 2025 (quarterly) | replaces the ±15 MW figure digitization in the ORDC curve (rule 14) | https://www.ercot.com/mp/data-products/data-product-details?id=NP6-576-ER | every posting; one csv per season | `data/raw/ercot/ordc-lolp/` | 30 min |
| 5 | **ERCOT CDR xlsx** (May + Dec, 2019–2025) + **Capacity Changes by Fuel Type** monthly workbook + **Fuel Mix Report** + Unplanned Resource Outages report | W0 reconciliation; C1 bench cross-check | https://www.ercot.com/gridinfo/resource ; https://www.ercot.com/gridinfo/generation | one CDR per issue; the fuel-type workbook (INR, COD, IA, MW per project); Fuel Mix xlsx per year | `data/raw/ercot-cdr/`, `data/raw/ercot/fuel-mix/` | 1 h |
| ~~★6~~ | **REFUSED (owner, 2026-10-02: no requester-pays AWS).** ~~CAISO Historical OASIS Data Downloader: DAM `PRC_LMP` hourly + RTM `PRC_INTVL_LMP` 5-min, 2019-01-01 → 2021-04-26~~ Free alternative: EIA ICE daily `NP15 EZ Gen DA LMP Peak` / `SP15 EZ Gen DA LMP Peak` 2019–2022 (peak block only, no intertie) at https://www.eia.gov/electricity/wholesale/xls/archive/ice_electric-2019final.xlsx … at `TH_NP15_GEN`, `TH_SP15_GEN`, `TH_ZP26_GEN`, `DLAP_PGAE/SCE/SDGE/VEA-APND`, `MALIN_5_N101`, `CAPTJACK_5_N003`, `PALOVRDE_ASR-APND` (+ `TRNS_USAGE`, `PRC_FUEL` if the bucket holds them) | CAISO C1/C4 2019–21, C3a 2021, C3 2019–20 scoreability | https://oasis.caiso.com/ → "Historical OASIS Data Downloader" (notice 2025-11-11; AWS **requester-pays** S3, egress cost small but non-zero) | check the User Guide's report catalogue first; record the retrieval date; correct `data/raw/lmp-data/CAISO/README.md` | `data/raw/lmp-data/CAISO/`, `data/raw/caiso-trns-usage/` | 2 h + AWS account |
| 7 | **WEIM quarterly benefits reports 2019Q1–2021Q4** (Table 2 BAA-pair transfers) | CAISO fold rung-depth validation (instrument, not input) | https://www.westernenergymarkets.com/library/weim-2014-2022-reports | 12 PDFs; extend the existing `weim_benefits_appendix2_transfers.csv` builder | `data/raw/nwpp-weim/` | 1 h |
| ★8 | **STB EP 724 weekly rail service data, BNSF + UP, 2019–2025** (coal unit-train loadings vs plan by basin incl. PRB) | SPP 2022 coal object (C1/C4 2022); ERCOT/PJM 2022 coal corroboration | https://www.stb.gov/reports-data/rail-service-data/ | weekly PDF/XLS per railroad; keep the "coal unit train loadings vs plan" rows | `data/raw/rail-service/` | 1 h |
| 9 | **SPP portal**: `ver-curtailments` 5-min, `hourly-generation-capacity-by-fuel-type` 2019–2025 (browser; token-blocked from the container) | SPP C1 wind check; commitment-state comparator (never an input) | https://portal.spp.org/pages/ver-curtailments ; https://portal.spp.org/pages/hourly-gen-capacity-by-fuel-type | yearly CSV/zips | `data/raw/spp-hsl/`, `data/raw/spp-online-capacity/` | 30 min |
| 10 | **SPP MMU ASOM 2019–2025** commitment-status-by-fuel tables (§3.3 "Self-commitments") | SPP posture lane's measured driver | spp.org documents 62150 / 65161 / 67104 / 69330 / 71645 / 73953 / 76798 | transcribe the tables | `data/raw/som-competitive-conduct/` | 1 h |
| 11 | **MISO Max Gen declaration history** (OATI PDF, SSL-blocked from the container) + **MISO 2022 RT hub LMP Nov 12 → Dec 31** (Data Exchange Pricing API key, free) + **LOLE CIL/CEL for PY2019-20..2021-22** | MISO C3c 2019/21 pricing windows; C3c/C3a 2022 coverage (Elliott unscored); per-PY interface limits | https://www.oasis.oati.com/woa/docs/MISO/MISOdocs/Capacity_Emergency_Historical_Information.pdf ; https://www.misoenergy.org/markets-and-operations/rtdataapis/ ; MISO LOLE study PDFs | transcribe declarations into `maxgen-events/miso/miso.csv`; `fetch_miso_hub_lmp.py --years 2022`; transcribe CIL/CEL tables | `data/raw/maxgen-events/`, `data/raw/lmp-data/MISO/`, `data/raw/capacity-deliverability/miso/` | 1.5 h |
| 12 | **PJM**: hourly Marginal Fuel Type files 2019–2025; DataMiner `rt_hrl_lmps` (ZONE) 2019–25 → commit a derived zonal bench; `gen_outages_by_type` Dec 2022 hourly; IMM SOM §10 reserve-by-unit-type; "Capacity by Fuel Type" 31-Dec snapshots; Generation Deactivation list | PJM C3a 2020 bench, Elliott census, L1 reserve census, W0 reconciliation | https://www.pjm.com/markets-and-operations/energy/real-time/historical-bid-data/marg-fuel-type-data.aspx ; https://dataminer2.pjm.com/ (free registration) ; https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/ ; https://www.pjm.com/planning/service-requests/gen-deactivations | commit derived summaries so lanes stop re-fetching 84 throttled month-files | `data/raw/pjm-marginal-fuel/`, `_validation-source/actual_lmp_zonal_PJM.parquet`, `data/raw/pjm-deactivations/` | 2 h |
| 13 | **NYISO MIS**: RT limiting constraints 2023-01 → 2025-12 (monthly zips); RT masked generator bids 2022–25 (verify the posting path); TSA post-contingency limits (T&D Operations Manual); ISO-NE OP-4 / PJM emergency postings for Jun 2025 | NYISO C3c decomposition and the June-2025 event rule | http://mis.nyiso.com/public/ ; https://www.nyiso.com/manuals-tech-bulletins-user-guides ; https://www.pjm.com/markets-and-operations/emergency-procedures | 36 monthly zips; manual lookup of UPNY-ConEd / Dunwoodie-South TSA limits | `data/raw/lmp-data/NYISO/`, `data/raw/nyiso-bid-data/`, `data/raw/NYISO/interface-flows/` | 1 h |
| 14 | **NEISO**: NY Harbor ULSD daily 2019–2021 (EIA); ISO-NE reserve requirements 2019–2022 (ISO Express, nested); event-week Algonquin dailies transcribed from the FERC/NERC Elliott report and EIA notes; SCC monthly workbooks 2019–2025 | NEISO scarcity-physics arm; W0 reference | https://www.eia.gov/dnav/pet/hist/EER_EPD2F_PF4_Y35NY_DPGD.htm ; ISO Express (`fetch_neiso_reserve_requirements.py`); FERC/NERC Winter Storm Elliott report | extend `ny_harbor_ulsd_daily.csv` to 2019-01-01; 15-day requirement windows | `data/raw/oil-prices/`, `data/raw/NEISO-AS/requirements/`, `data/raw/capacity-market/scc/neiso/` | 1.5 h |
| ★15 | **DONE 2026-10-02 (raw) and the lever is falsified** — FERC-714 Part II Sch. 6 hourly system lambda for every NWPP-footprint filer 2019–2025 landed verbatim as `data/raw/ferc-714/nwpp_hourly_system_lambda_2019_2025_raw.parquet` (REPORTED-ONLY). Only NEVP and NWMT (2021+) report non-zero values; every thermal-following respondent the pool reference needs files zeros or nothing. No pool lambda exists to build. | NWPP price reference (C3a/C3b), STOP-gated | https://zenodo.org/api/records/21738524 (`ferc714.zip`, member "Part 2 Schedule 6 - Balancing Authority Hourly System Lambda.csv"); https://www.eia.gov/electricity/wholesale/xls/archive/ice_electric-2019final.xlsx … `-2022final.xlsx` | filter respondents to the 17 NWPP BAs; "Mid C Peak" rows only (no off-peak row exists) | `data/raw/ferc-714/`, `data/raw/nwpp-weim/midc_peak_daily.parquet` | 1 h |
| 16 | **WECC 2024 WARA appendix** subregion tables; **NWPP regional coal stocks** (EIA EPM Table 4.10, Mountain division; plant-grain stocks are not public) | W0 reconciliation; documentary evidence for the Bridger ledger row | https://feature.wecc.org/wara/ ; https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_4_10 | pull NWPP-NW/NE/Central existing-resource MW | `data/raw/nwpp-planning/` | 30 min |
| 17 | **SOCO**: EIA weekly basin spot coal prices 2019–2025; Georgia PSC FCR (dockets 42516, 44902) / Alabama Rate ECR fuel testimony (coal inventory, minimum-take); Mississippi Power 2024 IRP | SOCO L1 fallback index; 2019 COAL_BIT driver; W0 | https://www.eia.gov/coal/markets/ ; https://psc.ga.gov/facts-advanced-search/ ; https://www.psc.ms.gov/ (docket 2019-UA-231) | weekly XLS; fuel-witness testimony + "Coal Inventory" exhibits | `data/raw/coal-prices/`, `data/raw/soco-planning/` | 1–2 h |
| 18 | **Cross-check fleets (W0)** (EIA-860M August 2026 **DONE** as `data/raw/eia-860m/`; NREL ATB 2025 v1.0.0 checked — its financial-case taxonomy changed, so it is NOT landed, see `data/raw/nrel-atb/README.md`): EPA NEEDS 2025 Reference Case rev 11-28-2025; PUDL `core_eia860__scd_generators` / `scd_plants` / `scd_ownership` / `core_epa__assn_eia_epacamd_subplant_ids`; EIA-860M latest month; NYISO Gold Book 2019–2025 (Table III-2 xlsx); ISO-NE CELT 2019–2025 (§2 list); CAISO NQC lists; SPP RA reports; MISO PRA results; WECC L&R | the per-ISO reconciliation ledger | https://www.epa.gov/power-sector-modeling/national-electric-energy-data-system-needs ; https://data.catalyst.coop/ ; https://www.eia.gov/electricity/data/eia860m/ ; https://www.nyiso.com/planning ; https://www.iso-ne.com/system-planning/system-plans-studies/celt ; CAISO RA page; spp.org documents 64801/67297/69529/71804/74099 ; MISO PRA page ; wecc.org | one file per source-year | `data/raw/epa-needs/`, `data/raw/pudl/`, `data/raw/eia-860m/`, `data/raw/<iso>-capacity-report/` | 3 h total |
| 19 | **Potomac SOM figures**: ERCOT SOM 2023 Fig. 13 / SOM 2024 Fig. 11 (monthly ECRS "simulated correction to price"); NYISO 2025 SOM + Q2/Q3 2025 | ERCOT 2023 ruling evidence; NYISO tail attribution | https://www.potomaceconomics.com/ (document library) | digitize the monthly bars with the figure as provenance | `data/raw/ercot/imm-ecrs-counterfactual/`, `data/raw/NYISO/` | 1 h |

Not free, do not pursue (recorded so nobody re-asks): daily NW gas hubs (Sumas/Stanfield/Opal), Transco Z5/TETCO M3 daily, Southeast daily gas, same-day CA citygate, a full Algonquin daily index, Mid-C off-peak daily, Path-15 element outage history (CEII/NDA), GADS per-unit outages.

---

## 5. Owner decision queue

### 5.0 RULED 2026-10-02 (decision cards presented in the planning session; verbatim choices)

| # | Ruling | What it unblocks / what it requires |
|---|---|---|
| R-1 | **Merge PR #7015 now.** | Lanes clone the plan from `main`; every 2025 backcast and every forecast reads EIA-860 Final 2025 from the next launch. |
| R-2 | **W0 EIA-860 settlement: approve all eight (Q1–Q8).** | One foundation lane: seasonal capacity basis, SB admitted with benchmark parity, registry-read repairs default-on in backcast, load-time BA filtering, EPA/PUDL crosswalk, per-keeper `fleet_census_<Y>.json` with 1 % / 0.5 % / 3 % tolerances, tests, freeze; then one full-span re-solve per ISO promoted on structure. |
| R-3 | **EIA-923 monthly coal receipts and month-end stocks are admissible as a backcast fuel-availability overlay (rule 13)** — a per-plant monthly take ceiling (receipts + stock envelope with a declared `stock_min`), never the burn; forward analogue = contract delivery rate. | ERCOT 2022 L1 (first), MISO fall-2021 conservation, SPP/PJM 2022, NWPP Bridger 2023. |
| R-4 | **Coal benchmark basis (EIA-923 vs EIA-930): study across all nine ISOs first.** | One zero-LP lane produces the dual-basis C1 table for every ISO-year before any rubric ruling; SPP 0a and PJM C1 wait on it. |
| R-5 | NYISO: already promoted (NEXT-32 on main). | — |
| R-6 | **ERCOT 2023 keeps its own configuration.** Owner: *"We had it set up so 2023 was allowed to have a different config because of the ECRS; then that got eliminated. I'm comfortable with a different config for a single year we know was off."* | The 2023 carve-out config is the sanctioned 2023 recipe. Implementation needed: an owner-signed, 2023-only *configuration-exception* caveat kind in `calibration_verdict.py` / rubric §3 (non-downgrading, like C3c; cites the IMM SOM 2023 §II.H finding and this ruling), so the ECRS-era C3a/C3b residual stops gating the ISO; report the IMM counterfactual beside the actual. Rubric version bump; ERCOT lane owns it. |
| R-7 | **Re-open the free ERCOT Data Portal / Public API account for one bounded intake** (60-Day SCED/DAM 2019–22, NP6-576-ER). | ERCOT 2019/20 C1 and C3b route (per-plant coal offer tables, zero DOF). |
| R-8 | **SOCO: scope the caveat budget for a lambda-referenced BA → CALIBRATED-WITH-CAVEATS.** | Rubric amendment (§2 budgets: a BA scored on a system lambda carries its reference-definition ledger rows at full reported magnitude, determination-downgrading to WITH-CAVEATS, not NOT-YET); SOCO L1 zero-LP hour still runs for structure. |
| R-9 | **NWPP price reference: WEIM ELAP 2023-06 onward as a labelled imbalance-price benchmark**, STOP-gated like SOCO's lambda; 2019–2022 stay PHYSICALLY-CALIBRATED (price unscored). | N2 amendment card; the FERC-714 pool lambda stays falsified. |
| R-10 | **C3c: sign one owner model-class classification per ISO after each lane's zero-LP decomposition.** | W3; lanes run the decomposition first. |
| R-11 | **Retire the residual free parameters** (`wefor_multiplier` 0.7 → measured wind availability or deleted; CAISO min-load 0.26 → 0.570; battery adders and fitted import tranches ledgered or replaced), one lane per ISO, promoted only if nothing regresses. | W2. |
| R-12 | **SPP: one PRECOMMIT for SPP-107 + the commitment-posture pairing.** | 7 shards once. |
| R-13 | **PJM: re-charter the `gas_offer_margin_anchor_vintage` retest with a displacement-aware S4 written ex ante; adopt zonal load-weighted C3a for PJM.** | Every registered PJM year re-bases on the zonal basis (as NYISO/MISO). |
| R-14 | **CAISO: `zonal_gas_basis` 2021 carve-out accepted as rule-28 new evidence; re-solve `caiso_ra_min_load_frac` at the measured 0.570.** | Two sequential full-span arms with the 2024 and C4-2025 tripwires. |
| R-15 | **MISO: transcribe the Max Gen declaration history (owner downloads the OATI PDF); keep C1 ST_GAS 2019 routed.** | 0b; no lever for the 3 GWh miss. |
| R-16 | No requester-pays AWS data (CAISO OASIS history). | The 2019–21 CAISO fold stays data-limited. |
| R-17 | **No owner downloads today — proceed without them** (owner, 2026-10-02, desk session). | Deferred, not cancelled: STB EP 724 rail (SPP step 3), MISO Max Gen OATI PDF (0b), ERCOT account intake (R-7). Lanes proceed; each deferred object is written as a DRAFT data-limited ledger row whose route is the intake. |

The queue below is retained as the record of what was asked; items ruled above are marked.


Each decision is phrased so a one-word answer unblocks a lane. Recommendation in bold where the shards converge.

**Program-level**

| # | Decision | Recommendation |
|---|---|---|
| D-P1 | W0 Q1: one capacity basis everywhere (published seasonal pair of the solved year's vintage; flat class derate deleted), re-keying every keeper | **Yes** — a foundation lane; zero-LP census per ISO first, one re-solve per ISO after |
| D-P2 | W0 Q2–Q4, Q6–Q8: admit SB fleet-wide; Final 2025 + 2023/24 retired sheets as the vintage record; flip the registry-read correctness flags default-on in backcast; load-time BA filtering; EPA/PUDL crosswalk of record; census tolerances 1 % / 0.5 % / 3 % | **Yes** to all; Q5 (ERCOT CSV): audit now, migrate later |
| D-P3 | W5: rule once on the EIA-923 vs EIA-930 coal basis (gross/net) and the gas metering-coverage alignment (SPP-87/88, PJM-NEXT-20/21) — a rubric change, ISO-agnostic | rule it before any SPP/PJM C1 lane spends shards |
| D-P4 | W5: zonal load-weighted C3a basis for PJM (as NYISO/MISO 2026-10-01) | consistent basis across ISOs; re-bases every PJM year |
| D-P5 | W3: sign one `model-class` C3c classification per ISO after the zero-LP decomposition (NYISO 2023/24, SPP 2023–25, NEISO 2022/23/25, MISO, CAISO 2021 after its census) | sign after the decomposition, not before |
| D-P6 | W2: rule on the residual DOFs — replace `wefor_multiplier` 0.7 with a measured wind availability input (audit C-15) or delete; ledger or re-solve `caiso_ra_min_load_frac` 0.26 → 0.570; declare MISO's rule-1 CC exemption in `authorized_price_tuning` | replace/declare; a reviewer will ask for every one |
| D-P7 | Rule 13 scope of EIA-923 monthly coal receipts and month-end stocks as a backcast fuel-availability overlay (same form as the admitted F923 fuel price) | **Yes** — it is the admissible driver for ERCOT 2022 (L1), MISO fall-2021 conservation, SPP/PJM 2022, NWPP Bridger 2023; forward analogue = contract delivery rate; construction = receipts + stock envelope with a declared stock_min, never the burn |

**Per ISO**

| ISO | Decision | Recommendation |
|---|---|---|
| NYISO | Promote PR #6992 option 1 (NEXT-26 arm B: `nyiso_gas_daily_print_level` + `nyiso_li_tsl_all_hours`); accept the 0.4-pt C3a-2025 margin as a zero-DOF result; reinstate `complete` on promotion or hold for EIA-923 2025 final | **Promote**; hold `complete` until 2025 C1 scores |
| NYISO | Rule-13 line for a *declared-event* availability / neighbour-emergency import representation (event published, magnitude read from CAMPD / P-32) | admit the event rule with the magnitude from the ISO's own posted emergency data, not from observed output |
| ERCOT | 2023 target: hold NOT-YET until the first full RTC+B year (2026) is solved as a touchpoint, or amend the rubric with an owner-signed IMM-counterfactual band (ECRS-neutral LW ≈ $35 vs actual $62–65, model $49) | **(a) hold to Door D**, report the counterfactual alongside; (c) releasing the k=33 carve-out is reporting, not closing |
| ERCOT | Re-open the free ERCOT Data Portal / Public API account for one bounded intake (§4 rows 3–4) | **Yes** — without it 2019/20 C1 is not closable |
| ERCOT | Approve the ERCOT arm of `coal_fuel_inventory` (L1) and the West import-direction rating (L2) as a rating repair under the ercot-234 precedent, not the refused sub-zonal split | **Yes** to both; L2 only if its zero-LP census clears |
| PJM | Re-charter `gas_offer_margin_anchor_vintage` with a displacement-aware S4; treat coal-in-reserve-pool (L1) as a membership change on `pjm_reserve_pergen`; Elliott: one-event caveat vs event overlay | re-charter; membership change; run the overlay only after the 0b census shows ≥ 15 GW in ≥ 18 h |
| MISO | Max Gen registry transcription + pre-Sep-2021 floor vintage; keep C1 ST_GAS 2019 routed; per-PY LOLE CIL/CEL 2019–22 | transcribe; keep routed (do not build for 3 GWh); adopt per-PY only if the groups ever bind |
| SPP | Authorize SPP-107 + the posture pairing in one PRECOMMIT; STB rail download; West/East lane; accept ledgering C3a 2019/20 and C3b 2020 as commitment-state limits | one PRECOMMIT; download; defer West/East; accept the ledger after the pairing span |
| CAISO | Authorize the OASIS history fetch (AWS requester-pays) and the report list; delete the R-CAISO-20 ruling flag once prints exist (rule 26); accept the `zonal_gas_basis` 2021 carve-out as new evidence; min-load 0.26 re-solve or ledger; verify per-unit COD closed Redondo Beach gen 7 for CAISO | **Yes** to the fetch; delete; accept; re-solve at 0.570; verify in the W0 census |
| SOCO | Budget ruling: λ-referenced BA with three scoped ledger rows → CALIBRATED-WITH-CAVEATS, or NOT-YET by design; L1 (coal at marginal replacement cost, IIC §3.6) at zero LP; Georgia PSC / Alabama fuel testimony pull | rule on the budget; allow the one zero-LP hour; the testimony pull is optional |
| NWPP | ~~N2 amendment: FERC-714 pool lambda~~ (falsified: only NEVP/NWMT file values) → rule instead on a single-BA NEVP/NWMT lambda or the WEIM ELAP 2023-06+ series as a labelled benchmark; ask the CAISO lane to rule on the `WECC_import` double count (card N4); Bridger 2023 C4 ledger eligibility under v3.10; any licensed daily NW gas series to declare | **Yes** to the N2 card; ELAP as report-only; ask CAISO; eligible after levers A–C; none expected |
| NEISO | Sign the C3c classification; allow the scarcity-physics arm (new field `neiso_reserve_response_scoped`) on rules 14/18 alone; accept hand-transcribed event-week Algonquin dailies as provenance; keep or remove the dormant `neiso_winter_fuel_*` family; adopt ISO-NE SCC as the capacity reference with EIA-860 as the vintage/COD reference | sign; allow; accept with page citations; remove under rule 26; adopt |

---

## 6. Roadmap

Sequencing principle: **data and rulings first, zero-LP censuses second, shards last** — a shard is spent only on a lever whose census cleared its pre-fixed reading. Each wave's shards are year-isolated (rule 36), one shard per ISO-year, launched from `scripts/shard_prompt.py --all-years` by the lane's parent session; the parent never solves (rule 32).

| Wave | Content | LP | Exit criterion |
|---|---|---|---|
| **0 — rulings and downloads** (owner, days) | §5 decisions; §4 rows ★1–★4, ★6, ★8, ★15 first, the rest as lanes need them | 0 | every blocked lane has its answer or its file |
| **1 — zero-LP closes** (parallel, one session per ISO) | NYISO promotion (#6992) · MISO tail derive (C3c 2019–21 scored) · W3 tail decompositions (NYISO, SPP, NEISO, CAISO 2021) and one signed classification per ISO · W4 re-stamps (`unit_marginal`, `authorized_price_tuning`) · NEISO label reconciliation + 2025 re-score · SOCO budget ruling + L1 phase 0 · ERCOT L1/L2 censuses · PJM 0a–0e · CAISO 0b–0d · NWPP NEXT-19 · SPP 0a/0b (after D-P3) | 0 | NYISO CALIBRATED; every C3c row classified; every census has a published pass/fail reading |
| **2 — W0 foundation** (one lane, then nine re-solves) | vintages rebuilt (Final 2025, retired sheets), E.1–E.7 implemented with tests, per-ISO census ledgers, default-on flips; G-DRIFT per ISO; one full-span re-solve per ISO promoted on structure | 63 shards | every keeper carries `fleet_census_<Y>.json` inside tolerance; NEISO tripwire not tripped |
| **3 — admissible levers, full span** (per ISO, in the order each §3 block gives) | ERCOT L1 coal ceiling → L2 West rating → (if account) 2019–22 coal offer tables · CAISO L1 printed interties → zonal gas basis 2021 → min-load 0.570 · PJM L1 reserve pool → L2 incremental HR → anchor-vintage retest → Elliott overlay · MISO L1 transport table → L3/L4 coal continuum · SPP SPP-107 → posture pairing → rail-keyed SPP-44 · NWPP FERC-714 benchmark → gas daily shape → priced seam → coal bridge · NEISO scarcity-physics arm · SOCO L1 if its phase 0 clears | ≈ 7 shards per lever | each lever promoted on structure or recorded `R` with its cell updated (rule 28) |
| **4 — frontier statements** | for every miss left: an owner-signed ledger entry or frontier statement naming the mechanism the model class lacks (commitment state / MIP, operator conduct, sub-hourly scarcity, unpublished limits); the determination then reads honestly | 0 | no ISO carries an undocumented FAIL |

### 6.1 Desk log — lanes chartered 2026-10-02 (desk session `session_017wUwd6xxLRQKAYiT8G722P`)

PR #7020 (fast-tier re-vintage) merged 05:06Z; main = `4d459da3`. Desk sequencing call: wave-1 zero-LP work runs now in every lane; **every full-span solve waits for the W0 foundation lane to merge** (W0 changes every ISO-year's fleet, so a pre-W0 span would be paid twice). NYISO (PR #7022, NEXT-34) and SOCO (PR #7021, soco-100) already have live lanes and were not re-chartered.

| Lane | Session | Branch | Scope (plan ref) | LP now |
|---|---|---|---|---|
| A 2025 re-bench | `session_01AUzPizySnt65GVypU6Ji1u` | `claude/closeout-a-rebench-2025` | W1, §4 ★2 — restore shared inputs, regenerate 2025 bench, completeness, status, rescore all nine | 0 |
| B W0 foundation | `session_018DsgkLcN1h8NQc2yJegmdN` | `claude/closeout-b-w0-foundation` | §2.1 E.1–E.9 + census + NEISO tripwire + G-DRIFT; phase 3 (63 shards) after desk merge | 0 → 63 |
| C rubric amendments | `session_01WkrLoQEcAbz8a6wYs7WMnd` | `claude/closeout-c-rubric` | R-6, R-8, R-9, R-13 (zonal C3a) + MISO/CAISO `authorized_price_tuning` | 0 |
| D coal-basis study | `session_016dguTG7U2KySt1x6EhBNLk` | `claude/closeout-d-coalbasis` | R-4 dual-basis C1 table, all ISO-years, decision card | 0 |
| ERCOT | `session_014k634JEUUTjkccEd9DZCYJ` | `claude/closeout-ercot-wave1` | §3.5 0b, 2, 6 censuses; L1/L2 PRECOMMITs | 0 (held) |
| CAISO | `session_011DvUjyuLQciozV4yTe6nBG` | `claude/closeout-caiso-wave1` | §3.7 0b–0d; R-14 PRECOMMITs | 0 (held) |
| PJM | `session_015n2kdnGhbpaemCCR7dGwRs` | `claude/closeout-pjm-wave1` | §3.6 0a–0e; L1/L2/R-13/L3 PRECOMMITs | 0 (held) |
| MISO | `session_01TCpbYap2X7mfnmXQttbX13` | `claude/closeout-miso-wave1` | §3.3 0a tail derive, L3/L4 census, R-3 fall-2021 census | 0 (held) |
| SPP | `session_019jCNcHE7XghY2vUZikt262` | `claude/closeout-spp-wave1` | §3.4 0b, C3c decomposition, R-12 PRECOMMIT | 0 (held) |
| NEISO | `session_01JjVv2VJdW4E3o77vTSuwSS` | `claude/closeout-neiso-wave1` | §3.2 1, 2, 4 spec; scarcity-arm PRECOMMIT | 0 (held) |
| NWPP | `session_01UT1DSG4oaBUXDxkdvQE7bM` | `claude/closeout-nwpp-wave1` | §3.9 NEXT-20 fixes, lever C + R-3 Bridger censuses, priced-seam PRECOMMIT | 0 (held) |

Still owner-side (browser, free): STB EP 724 BNSF/UP rail files 2019–25; MISO Max Gen OATI PDF; ERCOT account re-open (60-Day SCED/DAM 2019–22 + NP6-576-ER). **Deferred under R-17** — lanes ERCOT, MISO, SPP were told to proceed without them and draft data-limited ledger rows.

**Expected end state if every recommendation is taken** (honest, not flattering): NEISO CALIBRATED (protected); NYISO CALIBRATED; CAISO CALIBRATED if the OASIS history prints the fold (else 2022–25 CALIBRATED with a reported-only fold); MISO and SPP CALIBRATED on 2022/2023–25 with 2019–21/22 validation rows closed by rulings and ledgers, several remaining NOT-YET by the "no frontier" rule unless the commitment-state misses are ledgered; ERCOT CALIBRATED on 2019–22 and 2024–25 if the account re-opens and L1/L2 land, with 2023 held to Door D; PJM remains the hardest (coal loading response is a model-class gap); SOCO and NWPP read `…-WITH-CAVEATS` on rulings, with NWPP scored on price for the first time.

---

## Appendix — evidence index

| File | What it holds |
|---|---|
| `docs/records/governance/closeout-2026-10/AUDIT-eia860-capacity-vintage-settlement-2026-10-02.md` | pipeline trace with file:line, the 36-row defect ledger, the zero-LP census (CSV beside it), external practice (EIA/NREL/EPA NEEDS/PUDL/ISO reports), the nine-part settlement spec, tests, freeze rule, Q1–Q8 |
| `…/SHARD-<ISO>-closeout-research-2026-10-02.md` (9 files) | per-ISO status table, root-cause map with record quotes, retest table with the new evidence, new-lever table with the rule-13 story, external research (primary vs inference), data gaps, capacity findings, sequence, owner questions |
| `frontend/data/backcast/status/<ISO>.js` | the scored board this plan reads (generated 2026-09-26 … 10-01) |
| `docs/codebase-site/data/mechanism-matrix/<ISO>.js` | the cells each retest must update in its own session (rule 28) |
