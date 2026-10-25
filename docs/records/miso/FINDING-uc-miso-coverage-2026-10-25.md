# FINDING: UC-MISO-COVERAGE. Is there measured VLR data for 2021–2025, and what would adjudicate MISO UC-4?

```
LANE     : UC-MISO-COVERAGE (chartered by UC-DESK session_01WX9W5tgYMre3Z134LZoGF6, owner 2026-10-25 "Yes and launch anything else")
LP       : none (zero LP). Nothing built, solved, registered or promoted. No solve-path change.
DATA     : profile miso; EIA-860 generator tables (data/raw/eia-860); public filings fetched to scratch (§2, sha256 below)
READS    : RESULT-ucmilp4-miso-u4-2026-10-15 (§3, attempt_log.tsv); RESULT-ucmiso-vlr-2026-10-15; FINDING-ucmiso-vlr-phase0-2026-10-15;
           docs/uc-milp-program-plan-2026-10.md r13–r16; MISO shard cells vlr_pocket_commitment / unit_commitment_milp / uc_commitment_demand_source
```

## 0. Bottom line

1. **The gap that blocks MISO UC-4 is memory, not source data.** UC-4-MISO (#7269) and UC-MISO-VLR (#7259) held
   2021/2022–2025 because no shard container reached the 22.4 GiB gate. All 15 held attempts landed on 16.4–18.4 GiB
   containers (`attempt_log.tsv`). The requirement the owner ruled (r14: **≥ 1 committed unit per MTEP15 group**, 0 DOF)
   uses no per-year input. It is built from the MTEP15 group table plus each unit's EIA-860 retirement date, and both
   already cover 2019–2025. **The requirement can be built today for 2021–25 on sourced data.**
2. **No public source carries VLR commitment data for any year 2019–2025.** MISO's commitment guides set the MW to commit
   "based upon load forecast and calculated import capability" (MISO RSC, 2025-10-09). They name preferred and
   substitutable units by load level (ETI rebuttal, PUCT 56693). They are **CEII**, posted on MISO's Reliability-Authority
   extranet under NDA. ETI filed the SETEX guide only as a highly-sensitive attachment under protective order
   (PUCT 56693, ETI response TIEC 7-2). The IMM publishes VLR RSG dollars only. No count, MW or unit list is public.
   **Nothing quantitative exists to intake**, so no data-intake was run.
3. **The new public evidence is structural and dated.** It bears on how well the MTEP15 groups fit after 2021 (§3). It does
   not change the ruled level. Changing the groups would need an unpublished unit list, i.e. an estimate. That is a hard
   stop, so the groups stay as ruled and the misalignment is declared as a caveat.
4. **Plan (§5):** 5 shards (2021–25) on the U4 recipe at the r16 resume pin `41cd55dc`. Control: the keeper bundle. Each
   year has **one attempt left** (3 of 4 spent). At the observed pass rate (2 of 18 gate-reaching launches cleared
   22.36 GiB), the odds that 2021 plus one reserve year both land are about **3 %**. Re-running unchanged is unlikely to
   adjudicate MISO. **The owner decision is the container problem (§6), not data.**

## 1. Per-year coverage

| year | public VLR requirement data (count / MW / units) | eligible set (MTEP15 ∩ EIA-860) | 0-DOF requirement buildable? | UC-4 state |
|---|---|---|---|---|
| 2019 | none | groups A, B, D+E, F (C: Nelson 4 absent from fleet) | yes | solved `17117ee` |
| 2020 | none | same | yes | solved `52e66dc` |
| 2021 | none (SOM: Western guide stale, more units committed than needed) | same | yes | held 3/4 (memory) |
| 2022 | none (Aug 2022: Western guide → SETEX guide; WOTAB guide updated) | same | yes (caveat §3) | held 3/4 (memory) |
| 2023 | none | same | yes (caveat §3) | held 3/4 (memory) |
| 2024 | none | A loses Waterford 1 (EIA-860 retired 2024-03) | yes (caveat §3) | held 3/4 (memory) |
| 2025 | none (Sep 2025: SETEX aligned to reserve Zone 7, STR via RPE) | same as 2024 | yes (caveat §3) | held 3/4 (memory) |

EIA-860 (on-disk vintage): every other group member is operable through 2025. Sabine 1/3 plan to retire 2026-09; Little
Gypsy 2/3 plan to retire in 2029; Ninemile 4/5 in 2031/2033; Lewis Creek in 2034. All of these fall after the backcast.

## 2. Sources searched

| source | reachable | gives | class |
|---|---|---|---|
| MISO RSC, *South Load Pocket Capacity Advisory*, 2025-10-09 (`cdn.misoenergy.org/…721584.pdf`, sha256 `c5fb3036797acf67`, 174,129 B) | yes (cdn host now 200 per file) | **form:** guides fix the MW to commit from the load forecast and the calculated import capability; N1G1 for SETEX, Amite South, DSG; advisory when deficit ≥ 100 MW in any hour or ≥ 5 hours | form; no values |
| PUCT 56693, ETI rebuttal of D. Kline (`56693_335_1482692.PDF`, `7d3f85a806d46306`) | yes | the "SETEX (formerly WOTAB) Commitment Guide" names the **units to dispatch at given load levels** and the **substitutes**; binding contingencies are Rocky Creek–Grimes 345 kV and MCPS | form |
| PUCT 56693, TIEC direct of C. Griffey + Exh. CSG-2 (`56693_287_1470429.PDF`, `600345b7facf69b3`) | yes | ETI response TIEC 7-2: guides are "posted on [MISO's] Reliability Authority extranet page and protected under non-disclosure agreements"; the SETEX guide is the HSPM attachment `TP-56693-00TIE007-X002_HSPM`. Griffey pp. 34–36 quote it **redacted** | access: CEII |
| PUCT 56693 item 434 (`56693_434_1525194.PDF`, `8d749be0a45cdea7`) | yes | Lewis Creek 1/2 annual CF 2015–24 (24–61 %), "called on for transmission support" | outcome (conduct) |
| PUCT 57134, ETI fuel reconciliation, Fairclough direct, Apr 2022–Mar 2024 (`57134_6_1431742.PDF`, `f80794f9c688b3d6`) | yes | WOTAB and Western WOTAB both still require units in VLR status during 2022-04 to 2024-03 | structure (continuity) |
| Potomac MISO SOM 2021 (`abbfdb14c1d3e2a3`), 2022 (`027d01e6d1497d0f`), 2023, 2024 + appendix, 2025 (`56e1a348…`, `cfad6625…`, `6392a233…`, `a179e31a…`, matching `data/raw/MISO/SHA256SUMS.txt`) | yes | DA/RT VLR RSG $ by region per year; dated guide events (§3) | outcome ($); structure |
| LPSC Entergy Louisiana FAC audits (X-35523, X-36643, X-37898) | portal reachable; no VLR unit content located | — | — |
| `misoenergy.org` HTML | 403 | — | — |

The 2018 FERC and MTEP15/MTEP24 sources are in the phase-0 FINDING §1 and were not re-read.

## 3. Dated structural events after MTEP15 (public)

| date | event | source | bearing on the ≥1-per-group rows |
|---|---|---|---|
| 2019-05 → 2021-01 | three new CCs > 3 GW in MISO South pockets | SOM 2021 p.45; SOM 2022 p.43 | relieves need; Amite South CEMS ≥1-steam share falls to 0.32–0.71 in 2021–25 (phase-0 §4): D-4 risk already declared |
| 2021 (whole year) | Western guide not updated for the > 1 GW CC that entered the Western pocket in early 2021; summer VLR RSG ×4 | SOM 2021 pp.45–46 | real 2021 commitment ran **above** physics; group F ≥ 1 consistent with conduct (CEMS 0.97) |
| 2022-08 | Western op guide replaced by the SETEX op guide; WOTAB guide updated for the 1 GW CC | SOM 2022 p.43; SOM 2024 App. | ETI says SETEX is "formerly WOTAB" and there is no separate Western guide (Griffey p.34). Groups D, E, F sit inside one guide with substitutes. Unit list not public |
| 2024-03 | Waterford 1 retired | EIA-860 | group A shrinks; already in the table |
| 2025-09 | SETEX aligned to reserve Zone 7; local STR via RPE | SOM 2025 | part of the SETEX need is met by the reserve market from Sep 2025 (keeper 2025 carries measured reserve requirements) |

**Rule-13 / rule-14 reading.** The 0-DOF row stays admissible for every year. Its groups come from a published planning study
of the topology, and its eligible set shrinks on EIA-860 dates. Neither input is fitted or tuned to residuals.

The post-2022 SETEX regrouping does not map onto our representation. Rebuilding the rows as one SETEX set (Sabine ∪ Lewis
Creek ∪ substitutes) would need:
- the guide's unit list, which is CEII, and
- a judgment on which substitutes count.

Under rule 13 that is an estimate, so this lane does not propose it. The misalignment is declared, not repaired:
- **2022–25:** two SETEX-area rows (D+E on Sabine, F on Lewis Creek) where the real guide is one row with substitutes.
  The expected sign is over-commitment of Sabine or Lewis Creek in hours when MCPS or other substitutes carry the need.
- **Measure ex post:** V-2 (on-share vs CEMS) and V-4 (CEMS-dark binding hours). CEMS 2022–25 pocket sync is already
  tabulated (phase-0 §4): Sabine 0.83–0.90, Lewis Creek 0.82–0.95. So a ≥1 row is not grossly off where it binds.

## 4. What an owner download could and could not close

- **Could close the level, and the post-2022 groups:** the MISO commitment guides (SETEX, Amite South, DSG). The source is
  MISO's Reliability-Authority extranet, under NDA and CEII. A copy is `TP-56693-00TIE007-X002_HSPM`, under the PUCT 56693
  protective order. Neither is a public download, and neither could enter this public-data repository as-is. **No owner
  download is requested.**
- **Would not close it:** MISO `Resource_Uplift_by_Commitment_Reason` / RSG reports, and IMM tables. These are outcome
  ($, post-DA) data. As inputs they would pin commitment to observed conduct, which rule 13 forbids.

## 5. Plan to adjudicate MISO UC-4 (proposal; the desk launches)

| item | value |
|---|---|
| shards | 5: one per year 2021, 2022, 2023, 2024, 2025, launched serially, one `--years <y>` each (rule 36) |
| pin | `41cd55dc` (uc-1.8): the r16 resume ruling for held years, attempt counts carried |
| recipe | keeper `closeout_miso_nuc_span` recipe-year + `--set unit_commitment_milp=true --set st_gas_mustrun_per_plant=false --set vlr_pocket_commitment=true --set 'uc_commitment_demand_source="da_forecast"'`; per-unit `ut_h`/`mlf` as at the pin; 2023–25 keep the keeper's reserve co-opt + `miso_measured_reserve_requirements` + `miso_reserve_online_gated` (PRECOMMIT-ucmilp4 §1, recipe gate §1) |
| control | the keeper's committed bundle `closeout_miso_nuc_span` (rule 29(b)); no control solve |
| G-DRIFT | zero-LP audit `7c93273e` → `41cd55dc` on the backcast path. FIX-9 (lean preset runs LP heuristics) is LIVE on the MILP search. 2019–20 (uc-1.7) vs 2021–25 (uc-1.8) is an engine-confounded contrast, flagged as CAISO's was (#7275) |
| gate | 22.4 GiB (r16: 1.25 × 17.9 measured peak); a leg below it stops before reading data |
| attempts | 1 left per year (4th of 4); a gate stop is then a **recorded coverage gap**, not a hold |
| adjudicable when | 2021 (targets T-1 C1 CC, T-3 C4 gas) **and** ≥ 1 reserve year (2023–25) land; kill bars unchanged from PRECOMMIT-ucmilp4 |
| new PRECOMMIT? | an addendum to PRECOMMIT-ucmilp4 (pin move + §3 caveat declared ex ante), pushed before the first shard |
| keep-alive | MISO wall is ~2 h/leg (2019: 7,091 s) against a ~70–75 min background reclaim (r16 platform note) → keep-alive rule on every detached solve |

**Expected yield.** 2 of 18 gate-reaching launches cleared 22.36 GiB, a per-launch pass rate of about 0.11. Then:
- P(2021 lands) ≈ 0.11;
- P(≥ 1 of 2023–25 lands) ≈ 1 − 0.89³ ≈ 0.30;
- P(both) ≈ 0.03.

Spending the last attempts unchanged would most likely convert the holds into permanent coverage gaps.

## 6. Owner decisions (route via UC-DESK)

1. **How to get MISO a ≥ 22.4 GiB container:**
   - (a) spend the 4th attempts unchanged (~3 %);
   - (b) charter a zero-solve-surface **memory lane** for the MISO UC window. The 17.9 GiB peak, not the data, is the
     blocker. The fix must be exact (identity on 2019/2020 `uc_schedule` hash), runs on Opus/Fable, and touches `src/`;
   - (c) a gate ruling below 1.25× for MISO. Measured peaks are 16.7–17.0 GiB and containers reach 17.4–18.4. This is an
     infra-safety call the desk may not make (r15);
   - (d) close MISO UC-4 as permanently NOT ADJUDICATED.

   **Recommendation: (b), then the 5 shards.** It is the only option that raises the odds without touching the solve
   surface or the safety margin.
2. **Post-2022 SETEX regrouping:** keep the ruled MTEP15 groups with the §3 caveat declared (recommended; the alternative
   needs CEII data). There is no option to estimate the regrouping.
3. **Fleet item (carried, not new):** Nelson 4 (591.8 MW NG ST, EIA-860 operable) is still absent from the MISO fleet, so
   group C builds no row in any year (`unmatched_groups = ["WOTAB:C"]`). It stays a fleet-data item, outside this lane.

## 7. Matrix

No LP was run, so no cell changes (rule 28). `vlr_pocket_commitment` stays **R** (arm V); `unit_commitment_milp` and
`uc_commitment_demand_source` stay as on main.
