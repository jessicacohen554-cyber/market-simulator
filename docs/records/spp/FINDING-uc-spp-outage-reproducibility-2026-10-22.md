# FINDING — SPP ≥ 5-day `-netloadmask-` outage extract reproducibility (2026-10-22)

Lane UC-SPP-OUTAGE-AUDIT. Owner ruling R31 (2026-10-22): *"Zero-LP audit (Recommended)"*. Zero LP; no committed
derived file or solve input changed (rule 23). Audits RESULT-uc-spp-bench-2026-10-20 §5 / §7(d).

## 1. Result

The HEAD identity re-derive is **deterministic** and the gap has **two causes, both known**:

| Rows (committed plain only / HEAD only) | Cause | Kind | In the keeper's input? |
|---|---|---|---|
| 592 / 483 | SPP-98 split remap (`campd.CAMPD_UNIT_PLANT_REMAP`, 2026-09-28) | Deliberate code change | **No.** The keeper reads the `-splitremap-` companion, which already carries it |
| 8 / 0 | EIA-923 Early Release 2025 → Final 2025 (`36046e322`, 2026-10-02) | Source data update | **Yes**: 8 false 2025 full-year outages |

No unexplained row. No nondeterminism.

**The bench lane compared against the wrong file.** The SPP keeper (`2026-10-03-closeout-spp-nuc-keeper`) arms
`campd_split_remap_companions`. Its `run_config.json` records `data/raw/campd-unit-outages-netloadmask-splitremap-SPP.csv`
(6,472 rows), not the plain `-netloadmask-` file (6,581). The plain file is the pre-remap identity. It is not reproducible
at HEAD by design, because the remap is unconditional in the deriver.

## 2. Proof

Same invocation as the plain file's `.meta.json`: `--iso SPP --years 2019..2025 --high-load-pctl 0.85
--fullstop-override-days 5 --fullstop-override-cf 0.02 --min-outage-days 5 --min-inmerit-hours 24`.

| Code | `_processed-legacy/eia923_monthly_generation.parquet` | Rows | vs `-splitremap-` companion |
|---|---|---|---|
| HEAD `3215209d` | HEAD (Final 2025, 18,889 rows for 2025) | 6,464 | 8 rows missing, 0 extra |
| HEAD `3215209d` | as at `8289e3437` (Early Release 2025, 7,653 rows for 2025) | 6,472 | **byte-identical** (`cmp`) |

The plain file differs from the companion only in the 4 remapped facilities:
- Arsenal Hill 1416 CTG-6A/6B → J Lamar Stall 56565
- Ponca 762 → Ponca City 7546
- Anadarko 3006: plant denominators only (units 7/8 → WFEC GenCo 55655 leave the plant)

Arsenal Hill's 1416 denominators change the same way.

**Mechanism of the 8 rows.** The deriver's net-zero hook writes one full-year window (`NET0-923`, `capacity_source=eia923_netzero`)
for a plant that ran before but has **no 2025 EIA-923 filing** and no CAMPD gross. Early Release 2025 covers a sample of
respondents, so these 8 small CHP / industrial plants were simply absent from it. Final 2025 shows each one running
(5–114 GWh; table §3), which is a false positive in 2025 only.

## 3. Effect on SPP solve inputs

Consumer: the CAMPD unit-outage overlay, through `unit_outage_csv_for_iso` → per-unit hourly availability (`pmax × availability`).
The UC stage reads the same bounds. Scope: year 2025 only, and no other SPP outage layer (short, partial, shortgas) carries a
2025 window for these plants.

| EIA plant | Name | Group | NET0 MW | Final-2025 net gen (MWh) | Keeper LP 2025 cap |
|---|---|---|---|---|---|
| 10862 | ADM Lincoln | ST_CHP | 7.9 | 44,880 | **0 all year** |
| 54211 | American Crystal Sugar Moorhead | COAL_PRB | 5.0 | 37,834 | **0 all year** |
| 58192 | Arkalon Ethanol | ST_CHP | 3.0 | 14,877 | **0 all year** |
| 65367 | POET Mitchell | ST_CHP | 3.9 | 20,324 | **0 all year** |
| 52122 | Wasson CO2 Removal | CT_CHP | 23.4 | 114,005 | not derated |
| 56478 | MJMEUC GS #1 | CT_CHP | 13.3 | 90,138 | not derated |
| 60536 | UA Central Utility Plant | CT_CHP | 5.6 | 36,507 | not derated |
| 65512 | Kansas Ethanol | CT_CHP | 13.5 | 117,424 | not derated |

The four CT_CHP rows reach no LP unit: the overlay does not derate them.

**Size.** Each plant's 2024 keeper profile is the proxy for its lost 2025 availability:
- Availability: ≈ **62 GWh/yr** of LP availability removed (peak ≈ **7.5 MW**).
- Generation forgone: ≈ 53 GWh, which is **0.03 %** of the keeper's 2025 thermal generation (176.8 TWh).

LP capacities sit well below nameplate because the CHP behind-the-meter share is netted. **Immaterial to SPP price and dispatch.**
2019–2024 are unaffected: those years' NET0 rows were derived from Final 923 and reproduce.

## 4. Other ISOs (read-only, report only)

Every keeper's ≥ 5-day extract was committed before 2026-10-02, so each carries 2025 `NET0-923` rows built from Early Release 2025.
The check compares each 2025 NET0 plant against Final 2025: a filing ≥ 1 GWh means the hook would not fire at HEAD.
Per-plant list: `data/uc-spp-outage-reproducibility-xiso-2026-10-22.csv`.

| ISO | Keeper extract | 2025 NET0 rows | Now filed ≥ 1 GWh (MW) | Zeroed in keeper LP 2025 | Their 2024 gen / peak cap | Share of 2025 thermal gen |
|---|---|---|---|---|---|---|
| MISO | `unitroute-splitremap-MISO` | 57 | 51 (2,067) | 25 | 1.19 TWh / 305 MW | 0.23 % |
| PJM | `rederive-peakerkeep-exitfix-unitfuel-PJM` | 42 | 36 (795) | 14 | 1.42 TWh / 319 MW | 0.18 % |
| NWPP | `perunit-NWPP` | 9 | 8 (162) | 4 | 0.38 TWh / 67 MW | 0.17 % |
| SOCO | `perunitdark-SOCO` | 8 | 7 (333) | 4 | 0.15 TWh / 18 MW | 0.06 % |
| SPP | `netloadmask-splitremap-SPP` | 8 | 8 (76) | 4 | 0.05 TWh / 7.5 MW | 0.03 % |
| CAISO | `CAISO` | 32 | 30 (485) | 4 | 0.03 TWh / 169 MW | 0.02 % |
| NYISO | `perunitmerithour-NYISO` | 12 | 10 (226) | 1 | 0.03 TWh / 57 MW | 0.02 % |
| NEISO | `NEISO` | 23 | 22 (331) | 0 | — | — |
| ERCOT | `hourgrain` | 0 | 0 | — | — | — |

Two caveats:
- **Upper bound outside SPP.** "Zeroed" means LP cap = 0 in every 2025 hour. Only SPP was checked plant by plant to confirm the
  NET0 row is the plant's sole 2025 window. Elsewhere another window or a retirement could also zero a plant.
- **Cause-specific check only.** Full identity re-derives were not run for the other ISOs, so code drift there (e.g. the
  remap entries for MISO / CAISO / NYISO) is not covered.

## 5. Proposal (owner decision; rule 23 trigger = EIA-923 Final 2025, `36046e322`)

1. **SPP.** Re-derive the `-netloadmask-` extract and its `-splitremap-` companion at their recorded invocations.
   - Expected delta: −8 rows (2025 NET0 only).
   - Re-key: SolveEpoch, SPP backcast. G-DRIFT: LIVE for SPP 2025 only.
   - Recommendation: **fold into the next SPP promotion, not a standalone re-solve.** At 0.03 % of thermal energy it cannot move a
     determination.
   - Separately, record in RESULT-uc-spp-bench-2026-10-20 §5 that its 6,464-vs-6,581 compared against the plain file.
     The keeper's file reproduces up to the 8 data-update rows.
2. **Cross-ISO.** The same re-derive for MISO, PJM and NWPP is material enough (≈ 0.2 % of thermal energy, 67–319 MW of peak
   availability) to warrant a data lane per ISO, each in its own promotion.
3. **Guard (code, separate PR).** The net-zero hook treats "no filing" as zero output. Any Early Release year therefore produces
   false full-year outages for small respondents. Proposal: the hook requires a Final-release year, or counts an absent filing
   as zero only when the plant also files in that year's EIA-860 retired/inactive status. Propose in a PRECOMMIT; not done here.

## 6. Artifacts

- `data/uc-spp-outage-reproducibility-diff-2026-10-22.csv`: all 1,083 differing rows (plain committed vs HEAD), each with
  `side`, `cause` and `in_keeper_input_splitremap`.
- `data/uc-spp-outage-reproducibility-xiso-2026-10-22.csv`: 2025 NET0 plants now filing in Final 2025, all ISOs.

Reproduce (needs `scripts/regenerate_clean.py --solve-profile SPP` for the EIA-930 stale-snapshot repair):

```
uv run python scripts/data/derive_campd_unit_outages.py --iso SPP --years 2019 2020 2021 2022 2023 2024 2025 \
    --high-load-pctl 0.85 --fullstop-override-days 5 --fullstop-override-cf 0.02 \
    --min-outage-days 5 --min-inmerit-hours 24 --out <csv>
# old-923 control: temporarily place `git show 8289e3437:data/raw/_processed-legacy/eia923_monthly_generation.parquet`
# at that path, re-run, restore (sha256 verified), then `cmp` against the -splitremap- companion.
```
