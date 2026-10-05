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

## Addendum A: grid visibility answered from data (desk, 02:40Z). The energy is behind the meter, so D2-c is the rule-14 correction

**Source.** EIA-923 Schedules 6/7, "Annual Source and Disposition of Electricity for Non-Utility Generators", 2019–2025
(final revisions; `eia.gov/electricity/data/eia923/[archive/]xls/f923_<y>.zip`). The rows are extracted to
`_d2_disposition_f923_sched67.csv`.

**Own generation consumed on site** = (gross − station use) − sales for resale − retail sales − tolling − outgoing.
This equals direct use minus incoming, so the two sides of the balance agree.

| Plant | Sales for resale, every year | Incoming from SCE (GWh/yr) | Own net generation consumed on site |
|---|---|---|---|
| THUMS 56051 (NAICS 211, Long Beach oil islands) | **0** (retail 0, tolling 0, outgoing 0) | 218–410 | **100 %**. THUMS is a net importer: its host buys 0.22–0.41 TWh/yr from SCE on top of its own 0.17–0.36 TWh. |
| New-Indy 10427 (NAICS 32213, paperboard mill) | 40–49 GWh (plus 8–10 GWh retail) | 0.4–6.8 | **76–80 %**. Grid-visible exports are about 0.05 TWh/yr. |

**What this means.**
- Both plants are behind-the-meter self-generators. Their own output, and the host load it serves, sit outside
  CISO-metered demand.
- The model's ≈ 0 TWh for these plants is therefore correct on the grid basis, apart from New-Indy's ≈ 0.05 TWh of
  exports.
- The 0.5–0.6 TWh "O2 gap" in the w5 FINDING is a benchmark-basis artifact. It is not missing in-market energy, and
  it cannot displace CC_REGULAR.
- **The w5 FINDING §1's O2 attribution to the CC_REGULAR excess is withdrawn.**
- D2-b (a floor) would force grid energy the data say does not exist on the grid. It is not admissible.

**Scope: the rule applies to every plant, not two.** The same Schedule 6/7 test run over every CAISO plant in the shared
EIA-923 benchmark frame finds:
- CT_PEAKER self-consumption of **0.45–0.68 TWh/yr**. THUMS and New-Indy carry 0.34–0.55 of it; the rest is small
  industrial and institutional units such as Berry NMW, Kern Oil, Blacksand and Kaweah Delta.
- CC_REGULAR ≤ 0.036 TWh and ST_GAS 0.
- CC_CHP / CT_CHP 4.4–5.0 / 2.5–3.1 TWh. These are already handled by the sector-default `chp_btm_pct` deduction. A
  measured replacement is a separate question: the `chp_btm_measured` family, which is U in CAISO.

The admissible D2-c is therefore "deduct each non-CHP-class plant's measured Schedule 6/7 self-consumption from its
class actual", applied to all plants rather than a hand-picked list.

**Census: D2-c effect on C1, zero LP, against the w3 control** (`_d2c_census.json`; TWh; miss = model − actual):

| Year | CT_PEAKER miss, w3 | Two plants only | All plants | Band | Status |
|---|--:|--:|--:|--:|---|
| 2019 | −1.531 | −1.188 | −1.074 | 4.84 | PASS → PASS |
| 2020 | −1.906 | −1.358 | −1.226 | 4.60 | PASS → PASS |
| 2021 | +1.630 | +2.114 | +2.216 | 4.83 | PASS → PASS (moves away; already WATCH) |
| 2022 | −0.634 | −0.270 | −0.153 | 5.01 | PASS → PASS |
| 2023 | −1.137 | −0.658 | −0.562 | 5.27 | PASS → PASS |
| 2024 | −1.036 | −0.504 | −0.413 | 5.29 | PASS → PASS |
| 2025 | −1.737 | −1.382 | −1.287 | 5.08 | PASS → PASS |

- CT_PEAKER moves toward actual in 6 of 7 years. 2021 moves away but stays inside its band.
- **CC_REGULAR 2020 (T1) is unchanged at +4.996 (w3) / +4.80 (w5)**, because no 2020 CC_REGULAR self-consumption
  exists. 2021–23 CC_REGULAR moves by at most 0.036.
- ST_GAS is unchanged.
- No C1 status changes in any class or year. The total-generation term in the band moves by at most 0.02 TWh.

**Nature of the change.** This is a benchmark construction: measured BTM deducted from the EIA-923 actual, the same
place `_btm_frame` already deducts CHP BTM. It is not a run flag. The shared bench part must stay run-config
independent (nyiso-149), and it moves no model quantity, so it needs no solve.

**Conclusion.** D2 is closed for T1. The CC_REGULAR 2020 residual (+0.20 TWh over band in w5) has no remaining
plant-level object in O1–O3.

**Source workbooks (SHA-256).**
```
c2fd692e7994dda8e7b04645c3cac4881c471003d417d8419da20ba015be7cce  f923_2019.zip
b8c6516cc0ae306abffc03a4af393de496d52b84b41347521f7acb184a4f7bf9  f923_2020.zip
9db69876593a669a0a02aa67ea3abaebf7dc0ea961424912c75156432851ccd8  f923_2021.zip
2f030b7da3802b9310ecd93ef98014890d3519e6d1db55e5a49173121e5e82e4  f923_2022.zip
f96326c003bcdc0534144718c96fa8c31f803190e92b936b97d210db27acc557  f923_2023.zip
272055f2d748f6486fc3076abd5a40ec736dbff45458bdb4c895761278c50f2b  f923_2024.zip
1bff7092a86f6678c069c986829da5a23104048fc1aafb65b0776e3c904284de  f923_2025.zip
```
