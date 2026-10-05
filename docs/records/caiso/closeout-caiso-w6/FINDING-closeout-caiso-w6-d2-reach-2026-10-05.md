# FINDING closeout-CAISO-w6: D2 (industrial self-generation reclass) has zero reach as specified (2026-10-05)

**Charter (desk, 2026-10-05 02:30Z).** Build D2 as its own default-off flag that reclassifies only THUMS (EIA 56051)
and New-Indy Ontario Mill (EIA 10427), with source citations, stacked on w3 + D1. T1 = C1 CC_REGULAR 2020 ≤ 4.60.
Declare the benchmark class-map side effect. Run 7 legs.

**Status.** Zero LP. Nothing is built and nothing is solved. Code read at `935a3142`.

## 1. What a reclass would do: nothing to the scored quantities

**Model side.**
- The class is set in `eia860._rows_to_generators` → `plant_taxonomy.classify_plant` (NG GT → `CT_CHP if chp else
  CT_PEAKER`). The CHP flag comes from `eia860_chp_by_year.parquet`. 56051 has chp = N in every year 2018–2025. 10427
  has chp = Y only for GEN1, which retired 2019-11; GEN2/GEN3 (2 × 16.5 MW, from 2019) are chp = N. Both are sector 6
  "Industrial Non-CHP" in EIA-860; NAICS 211 (oil and gas extraction) and 32213 (paperboard mill).
- A plant moved to CT_CHP gets a floor only from a `thermal_tranches_CAISO.csv` level row (`chp_pmin_cf`,
  `steam_level_cf`). Neither plant has one. WP-3 scope (b) (`derive_thermal_tranches._chp_f923_floor_cf`) needs
  EIA-923 energy in the same class as the fleet group, and both plants are CT_PEAKER in EIA-923 from 2020 on. A
  re-derive is a frozen-derive question (rule 23), and the CAISO artifact is already non-reproducible at HEAD
  (caiso-294).
- Without a level row, a reclass only:
  - moves the plants to the CT_CHP offer curve, which is near-identical to CT_PEAKER;
  - drops the measured CT heat-rate gate, which is moot because neither plant files CAMPD;
  - takes the default merchant 35 % `chp_btm_pct` out of their LP capacity.
- Both plants dispatch ≈ 0 TWh in the w3 control in every year. Re-labelling ≈ 0 TWh moves ≈ 0 TWh.

**Benchmark side.**
- `run_calibration_full._eia923_frame` classifies each EIA-923 row on its own `chp` flag. The fleet `plant_group` is
  used only in the CEMS and missing-month backfills, which neither plant reaches.
- So a model reclass does not move the benchmark. The "class-map side effect" the charter asked me to declare does not
  occur. Making it occur would need a benchmark construction that depends on run config, which nyiso-149 forbids for
  the shared bench part.
- The one exception is 10427 in 2019, which is split in EIA-923: 190 GWh CT_CHP plus 41 GWh CT_PEAKER.

**Scoring.**
- CT_CHP is in `FUELMIX_EXCLUDED` (`calibration_verdict.py:808`), so it is not C1-gated.
- Even if the plants were floored, the floored energy would land in an ungated model class while the gated CT_PEAKER
  actual keeps it.

**Conclusion.** D2 as chartered is inert on T1 (ΔCC_REGULAR ≈ 0) and on every C1 cell. Seven legs would buy a known
null.

## 2. The physical question the w5 FINDING skipped: is this energy in CAISO's demand at all?

- Both plants are industrial non-CHP self-generators: an oil-island operation and a paper mill.
- If their output serves on-site host load, both that output and that load are outside CAISO-metered demand
  (EIA-930 CISO). They then displace nothing in the model's energy balance, and the 0.54–0.61 TWh "gap" is a
  benchmark-basis artifact. The correct treatment would be a BTM deduction from the CT_PEAKER actual, which leaves
  CC_REGULAR untouched.
- If instead they export to the grid, a host-driven floor would displace in-market gas. Most of that displacement
  would fall on CC_REGULAR and close part of T1.
- Neither plant appears by name in the CAISO ATL pnode map. That is inconclusive: pnode names are electrical nodes,
  and Carlsbad is not found by name either.
- What would settle it zero-LP: the EIA-923 Schedule 6 disposition (sales for resale vs. facility use) or a CAISO
  Master File resource ID.

## 3. Admissible variants (desk / owner choice)

| Variant | What it is | Rule exposure | Reach on T1 |
|---|---|---|---|
| D2-a (as chartered) | Class relabel only | none | ≈ 0, proven above |
| D2-b | Relabel plus a plant-keyed host level: a multi-year pooled EIA-923 CF, never same-year, through the existing CHP floor (`chp_pmin_cf`), with `chp_btm_pct` set explicitly | rule 17 floor (driver: host process; window: all hours; forward story: re-derive from EIA-923 history); rule 20 budget; rule 23 (new artifact rows); benchmark mismatch (model CT_CHP vs actual CT_PEAKER) unless the benchmark also moves | up to −0.4…−0.6 TWh, only if the energy is grid-visible |
| D2-c | Keep CT_PEAKER; benchmark-side BTM deduction for the two plants | benchmark construction (a shared-bench change, not a run flag); a rubric-adjacent change, so rule 37 caution | 0 on CC_REGULAR; CT_PEAKER actual −0.5 TWh |

`ct_mustrun_per_plant` (a same-year EIA-923 pin) is the quarantined actuals crutch and is not a candidate (rule 13).
