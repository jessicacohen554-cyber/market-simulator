# RESULT — miso-278: unit-fuel split of the thermal-tranche family. Zero status flips; ST_GAS closer every year; PROMOTED.

```
LANE     : miso-278 (owner charter 2026-09-26, docs/handoffs/CHARTER-miso-stgas-unit-fuel-attribution-2026-09-26.md)
PREREG   : docs/PRECOMMIT-miso278-unit-fuel-split-2026-09-27.md (pin 257d3c6f)
OUTGOING : 2026-09-26-miso-277-d1-as (miso277_span) — pruned (rule 35)
KEEPER   : 2026-09-27-miso-278-fuelsplit (results/calibration/miso278_span, 2019-2025)
DELTA    : campd_unit_fuel_split = true. DOF +0
CONTROL  : keeper bundle (G-DRIFT bd0329ed..257d3c6f: all non-delta hunks INERT; rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape — same three as the keeper); train 2023-2025 CALIBRATED
```

## 1. Legs

Seven single-year shards pinned to `257d3c6f`. Every leg verified in the parent: recipe = keeper + exactly
`campd_unit_fuel_split`; the solve read the four pinned `-fuelsplit-` companions. 17 files each including
`dispatch/<Y>_P1.parquet`. All 7 shard sessions archived.

| year | leg commit (provenance) | ST_GAS Δ TWh | coal Δ TWh (BIT+PRB) | LW internal price keeper → arm $/MWh |
|---|---|---:|---:|---|
| 2019 | `0602ad4e` | +0.366 | −0.028 | 27.911 → 27.929 |
| 2020 | `96a6cd01` | +0.300 | −0.611 | 24.546 → 24.585 |
| 2021 | `d4c3f4fa` | +0.194 | −0.483 | 37.079 → 37.144 |
| 2022 | `c6c39219` | +0.157 | −0.448 | 58.399 → 58.507 |
| 2023 | `c66fae8d` | +0.179 | −0.515 | 32.675 → 32.716 |
| 2024 | `7839973c` | +0.232 | −0.613 | 30.730 → 30.759 |
| 2025 | `c372a490` | +0.087 | +0.354 | 41.670 → 41.633 |

## 2. Gates (live scorer, rubric 3.9) — zero criterion-year status flips

| criterion-year | keeper miso-277 | miso-278 |
|---|---|---|
| **C1 ST_GAS 2019** | −8.56 TWh FAIL | **−8.20 TWh FAIL** |
| C1 ST_GAS 2020 / 2021 / 2022 / 2023 / 2024 | −6.90 / −5.68 / −5.51 / −0.61 / −2.16 | −6.62 / −5.49 / −5.36 / −0.44 / −1.94 |
| C3a 2022 | −15.8 % FAIL | −15.7 % FAIL |
| C3b 2021 | 0.254 FAIL | 0.254 FAIL |
| C3a other years | within ±0.1 pp | |
| legitimacy D-1/D-2/D-4 findings | 12 | **11** (2023 COAL_BIT D-1 clears; none new) |
| determination | NOT-YET (3) | NOT-YET (3) |

## 3. Reading

- A correct structural repair (rule 14): coal and gas boilers at one facility are no longer described by one row. It
  moves ST_GAS the right way in every scored year and the legitimacy count down by one, with no gate regressing.
- As predicted, it closes ~4 % of the 2019 ST_GAS gap. The remaining −8.20 TWh is (i) Entergy/Cleco South steam
  committed for local reliability (VLR) the model does not represent (`scuc_load_pocket_commitment` = `·`), and
  (ii) units that retired before the 2023–2025 tranche window (Baxter Wilson 2050, Teche 3, Houma, Meramec) and so
  can never get a measured row from it.
- **Held out, still owed:** the Riverside remap (55641 CT-03/CT-04 → EIA 64020). It is not solve-inert (benchmark
  activity gate and `bench_multiclass` read raw CAMPD through the remap table), so it lands as its own lane, LIVE in
  that lane's G-DRIFT. Patch text is in the charter's scope item 2.

## 4. Where the bytes are

The composite `miso278_span` (slim bundle incl. `hourly/`, attestation with a `miso278` block, regenerated
diagnostics, stamped partition that passes `--check`), its registry sidecar and payload are on `main` with this
lane's PR. Per-year leg dirs are parent-local and gitignored; the SHAs above are provenance only (rule 33(d)).

## 5. Promotion

Promoted on the owner's standing instruction (*"Is this a recommended keeper candidate? If so plz promote"*).
Year set (rule 35(b)): outgoing {2019–2025}, incoming {2019–2025}, covered. `audit_keepers --iso MISO` passes.
