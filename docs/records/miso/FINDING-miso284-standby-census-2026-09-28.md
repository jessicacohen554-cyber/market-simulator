# FINDING miso-284: MISO `SB` units' measured conduct, and why a faithful `admit_standby_units` arm cannot be built from existing extracts (ZERO LP)

**Session:** miso-284 (2026-09-28). **Keeper:** `2026-09-28-miso-280-splitremap` (unchanged). **Solves:** none.
**Lane:** owner ruling on the miso-283 card: *"Do standby units and un route ro2 before going after night overshoot"*.
**Evidence:**
- `scripts/probes/_miso284_standby_conduct.py` → `results/phase0/miso/_miso284_standby_conduct.json` (unit conduct)
- `scripts/probes/_miso282_standby_delta.py` (fleet delta, re-run for 2019–2025 this session; numbers match `results/phase0/miso/_miso282_standby_delta.json`)

## 1. Answer

`admit_standby_units` admits five material plants in MISO. Only **two** have measured output in the years they would be admitted. The largest remaining envelope sits on units with **no measured conduct** that any existing outage construction can reach.

| Plant (class) | SB MW | Years admitted | Measured conduct in those years | Covered by an outage extract? |
|---|---:|---|---|---|
| Baxter Wilson 2050 unit 1 (ST_GAS) | 494 | 2021–22 | **Real.** CEMS 771 / 318 GWh (2,466 / 1,403 op-h); EIA-923 751 / 309 GWh | yes (plant is in the extracts) |
| Marion 976 GT 5/6 (CT_PEAKER) | 140 | 2019–24 | **Real.** CEMS 2–61 GWh per unit per year | yes |
| Taconite Harbor 10075 (COAL_PRB) | 155 | 2019–22 | **None.** CEMS units 1/2: 0 op-hours in every year 2019–23. EIA-923: 0 MWh filed every year 2018–23 | **no** |
| Louisiana 2 1392 (ST_GAS) | 138 | 2023–25 | **No record.** No CEMS rows; no EIA-923 row in any year 2018–26 (and `OS` status in the 2021 vintage) | **no** |
| Wyandotte 1866 units 4/7 (ST_GAS) | 42 | 2023–25 | **None.** CEMS unit 7: 0 op-hours 2023–25; EIA-923 ST: 0 GWh 2023–25 (27–30 GWh in 2020–21) | **no** |
| Midland Cogen 10745 ST2 (CC_CHP) | 380 (+247 LP MW) | 2019–25 | **Not observable at unit grain.** ST2 has no CEMS id; EIA-923 is plant × prime mover. Plant CA output 1.26–2.45 TWh/yr = 35–68 % CF on the OP ST1 (410 MW) alone | yes (plant), but not ST2 itself |

The ~800 MW/yr of SB oil / IC units add ~0 TWh of envelope and are not material.

## 2. What the arm would do to the rubric

The failing criteria are C1 ST_GAS 2019, C3a 2022 and C3b 2021.
- **ST_GAS 2019:** the flag admits **0 MW** of ST_GAS in 2019. It cannot reach this miss.
- **C3a 2022 / C3b 2021** are price objects (West→East congestion; South storm gas). +0.08–0.38 TWh of South steam does not address either.
- **Where the envelope lands instead:**
  - 2019–22: COAL_PRB, already **+3.6 to +6.4 TWh** over actual. Taconite adds 0.57–1.01 TWh there.
  - 2023–25: ST_GAS, which **passes today**. Louisiana 2 + Wyandotte add 0.37–0.48 TWh with zero measured output.

Not a criterion either way (rule 1): stated so the owner sees the cost/benefit at full magnitude.

## 3. Phase 0 (b): what a faithful outage companion needs

None of the three plants with zero conduct has a row in any MISO outage extract (`campd-unit-outages*-MISO.csv`, `campd-partial-outages-MISO.csv`). The extracts were derived on the `OP` population. Re-running the deriver on the `OP + SB` population (rule 23: a population change is a legitimate re-derive trigger) **does not reach them either**, because every existing zero-output construction guards on evidence of earlier output:

| Construction | Guard | Taconite | Louisiana 2 | Wyandotte |
|---|---|---|---|---|
| Standard CAMPD detector (≥5-day windows) | needs a producing CEMS series | fails (dark all years) | fails (no CEMS) | fails (dark) |
| `eia923_netzero` full-year hook (`derive_campd_unit_outages.py:2604–2677`) | `ran_before`: >10 GWh in an earlier EIA-923 year **on disk (2018+)** | **fails** (idle since 2016) | **fails** (no filing ever) | **passes** (27–30 GWh in 2020–21) |
| SOCO-61 dark-unit-year windows | output in an adjacent year + a peer that ran + per-unit crosswalk | fails | fails | fails (per-unit family not armed in MISO) |

So a faithful arm is a **build with two parts**:
1. `-standby-` companion extracts, re-derived on `OP + SB` and read only when the flag is armed (separate files, never an overwrite).
2. **A longer EIA-923 history.** An intake of EIA-923 2014–2017 (eia.gov is reachable from this container) lets the **unchanged** `ran_before` test see Taconite's pre-2016 output. That is a source-data update (rule 23), not a new threshold. The same widened lookback can also move the netzero windows of `OP` plants that ran in 2014–17 and are dark in 2019+. That footprint is unmeasured until the data lands.

Even with both parts, two units stay unresolved without a new admission rule:
- **Louisiana 2** has no EIA-923 or CEMS record at all. Admitted, it is 138 MW the C1 benchmark can never see.
- **Midland ST2**'s conduct is not observable at unit grain. The plant's CA output fits ST1 alone.

## 4. Phase 0 (c): should an SB unit with no conduct be admitted at all?

Answered from the data only:
- The admission rule under test is **status alone**. That is its rule-13 basis.
- Filtering admission by same-year output is the variant NWPP-NEXT-5 **refused** as outcome selection (`scenarios.py`, the `admit_standby_units` comment).
- Idle units therefore have to be handled on the availability side, where an event construction exists. For Taconite and Louisiana 2, none does (§3).

**Conclusion:** no structural, admissible build results from existing constructions. A build would need a data intake plus a companion re-derive, and it would still leave 518 MW (Louisiana 2 + Midland ST2) admitted on status alone with no unit-grain evidence. That is the owner's call, not this session's (rule 31 has nothing to retain: no solve was run).

## 5. Matrix

MISO `admit_standby_units` **stays `U`**, with this census cited. No mechanism was tested in an LP, so no verdict is minted.

## 6. Owner ruling (2026-09-29, miso-284 card)

**"Park, go to RO-2 (Recommended)"**. The cell stays `U` with this census cited, and no solve is run. The same session opens queue item 2: RO-2 `scuc_load_pocket_commitment`, the South out-of-merit steam commitment. That work needs a rule-17 window, a driver and a forward story, and must use no own-year floors (rule 13).

The queue is unchanged after that. The system night overshoot (`diurnal_price_amplitude`, G) waits until RO-2 is done.
