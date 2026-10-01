# FINDING — SOCO-31: the scoring benchmarks. **GATE G9 PASSES — the non-SOCO diff in `calibration_reference.json` is EXACTLY ZERO** (eight pre-existing regions byte-identical on both their `isos` and `egrid_benchmark` blocks; all 39 pre-existing `*_renewable_capacity.csv` byte-identical). SOCO's reference block and three capacity CSVs are landed for 2023–2025. **THE PRICE SIDE IS NOT LANDED, NOT SUBSTITUTED, AND NOT A GAP** — gate G6's skip is verified by execution and gate G17 is upheld.

**Lane** SOCO-31 · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-16 ·
**Branch** `claude/soco-31-benchmarks-b4t9` · **Base** `origin/main` `1f586ed7` ·
**Data profile** `soco` (full clone — every blob already local) ·
**Charter** plan §5 row SOCO-31 / §5 W3 bullet · **Gates** G6 (skip, verified), G9 (exit, passes),
G17 (refusal upheld) · **Solves** none (zero LP; rule 32 `[R-SHARD]` (a) is not engaged) ·
**Rules that bit** 1 `[R-STRUCT]`, 5 `[R-NO-MAGIC]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
19 `[R-ONE-MECH]`, 23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`,
28 `[R-MECH-MATRIX]`.

**Precondition.** SOCO-20 LANDED — `_ISO_BUILDERS` carries `_soco_config` at `origin/main`
(PR #6152, merged 2026-09-14), and `FINDING-soco-20-2026-09-14.md` §7 routes
`curate_demand_profile.MODEL_ISOS` to this lane. Verified at the base before any edit.

---

## 0. The benchmark table (the EXIT deliverable, reported first)

Every figure below is a MEASURED OUTCOME used only as the SCORE. Nothing here is an input to a
solve (rule 13 `[R-MEASURED]`).

### 0.1 Load, generation and the export position

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **Demand (load), TWh** — the committed `demand.total_twh` | **229.4688** | **238.6990** | **239.5576** |
| peak MW | 45,558 | **47,368** | 46,490 |
| min MW | 17,432 | 17,007 | **12,638** *(an artifact hour — §4.3)* |
| mean MW | 26,195.07 | 27,248.74 | 27,346.76 |
| **Net interchange, TWh** (positive = EXPORT) | **+10.1562** | **+10.8067** | **+13.0321** |
| **Net generation, TWh** (EIA-930) | **239.6251** | **249.5057** | **251.8847** |
| Demand + net export | 239.6250 | 249.5057 | 252.5897 |

**SOCO IS A NET EXPORTER IN EVERY YEAR AND THE BENCHMARK SHOWS IT.** The export is not a separate
field bolted onto the block — no region's block has one and this lane invented none (rule 24
`[R-REGISTRY]`). It is visible as the arithmetic: the committed `demand` is 229.5 / 238.7 / 239.6 TWh
while the committed `generation_twh` sums to a footprint that generates ~240 / ~250 / ~252 TWh, and
the difference IS the export. The identity holds exactly in 2023 and 2024
(`Net generation − Demand = Total interchange` to the MWh on the raw frame) and carries a measured
−0.6963 TWh residual in 2025 (§4.4).

The charter's reconciliation targets are met: **demand + net export = 239.63 / 249.51 / 252.59 TWh**
against the charter's 239.6 / 249.5 / 252.6, and the export is **+10.16 / +10.81 / +13.03** against
the charter's +10.16 / +10.81 / +13.03. The 2024 peak, 47,368 MW, is the same BA winter peak plan
§2.5 quotes against Georgia Power's 16,284 MW.

### 0.2 Generation by class, TWh — what is committed, and what it is measured against

`generation_twh` is EIA-923 by fuel (the repo's convention for every region), with the per-fuel
incompleteness guard applied. The EIA-930 grid-side column is the independent comparator and is the
series FINDING-soco-10 quotes.

| class | 2023 committed | (EIA-930) | 2024 committed | (EIA-930) | 2025 committed | (EIA-930) |
|---|---:|---:|---:|---:|---:|---:|
| coal | 37.2434 | 38.2520 | 40.2395 | 40.4480 | 43.2752 | 44.0825 |
| gas_cc | 117.3899 | — | 113.7601 | — | 109.7396 | — |
| gas_ct | 6.6852 | — | 6.2537 | — | 1.9659 | — |
| gas_st | 12.6350 | — | 9.4821 | — | 6.6071 | — |
| **gas, all three** | **136.7101** | **129.5924** | **129.4959** | **125.6844** | **118.3126** | **125.2752** |
| nuclear | 52.1354 | 52.4348 | 63.0598 | 62.8400 | 64.2324 | 64.2187 |
| hydro | 6.8150 | 8.4465 | 6.3014 | 7.0798 | **6.0123** *(EIA-930, swapped)* | 6.0123 |
| solar | 9.0323 | 8.3615 | 10.3849 | 10.1232 | 10.3165 | 9.9890 |
| wind | 0.0 | 0.0000 | 0.0 | 0.0000 | 0.0 | 0.0000 |
| *(not benchmarked)* oil | 0.2666 | 0.0009 | 0.2573 | 0.0017 | 0.1042 | 0.0250 |

**Against the charter's EIA-930 targets** (gas 129.6 / 126.1 / 125.4 · nuclear 52.4 / 63.0 / 64.2 ·
coal 38.3 / 40.5 / 44.0 · hydro 8.45 / 6.92 / 5.93 · solar 8.36 / 10.14 / 9.98): coal, nuclear, solar
and 2023 hydro reproduce to the third decimal. Three cells sit slightly off and each has a named
cause, not a discrepancy: **2024 gas 125.68 vs 126.1** and **2024 hydro 7.08 vs 6.92** and **2025
hydro 6.01 vs 5.93** are the loader-seam spike screen repairing the R-h hours §4.2 lists — the
charter's figures predate that screen firing on this footprint. Nothing was tuned to close them.

**The EIA-923 / EIA-930 boundary gap is normal here, checked rather than assumed.** SOCO's ratio of
EIA-923 balancing-authority total to EIA-930 net generation is **1.0454 / 1.0361 / 0.9533**, inside
the spread every other region already shows (ERCOT 1.065 / 1.062 / 0.937, MISO 1.058 / 1.048 / 0.923,
PJM 0.998 / 1.008 / 0.933, SPP 0.970 / 0.977 / 0.804, NWPP 1.076 / 1.070 / 0.788). **SOCO's 2025
vintage is the most complete of all nine regions**, which is why `eia923_incomplete` does not appear
in its block: at 0.9533 it clears the 0.90 whole-vintage bar. That bar was not moved and no SOCO-only
bar was introduced (rules 5 / 23) — see §4.5 for what the flag's absence does and does not mean.

### 0.3 Renewable capacity — EIA-860, three zones, solar only

| year | December total MW | SOCO_AL | SOCO_GA | SOCO_MS | GA share |
|---|---:|---:|---:|---:|---:|
| 2023 | 4,912.9 | 620.7 | 4,132.7 | 159.5 | 0.8412 |
| 2024 | 5,707.9 | 620.7 | 4,770.7 | 316.5 | 0.8358 |
| 2025 | 6,047.9 | 700.7 | 5,030.7 | 316.5 | 0.8318 |

**There are no wind rows because there is no wind.** `_eia860_monthly_capacity` logs
`no EIA-860 wind data for SOCO`, the block carries a `solar` key only, and each CSV is 37 lines
(header + 1 fuel × 3 zones × 12 months) rather than the 73 a two-fuel region writes. 2025 reuses the
2024 EIA-860 vintage, the standing convention for every region.

### 0.4 `egrid_benchmark.SOCO` — eGRID 2023 PLNT23, 332 rows

`generation_twh`: coal 35.9354 · gas_cc 114.1149 · gas_ct 22.4266 · hydro 6.1678 · nuclear 52.1354 ·
solar 9.0265 · **biomass 10.2547** · oil 0.4460 · other 0.0.
`co2_mt`: coal 37.0910 · gas_cc 44.5666 · gas_ct 13.3223 · biomass 0.6692 · oil 0.1100.
`source`: `EPA eGRID 2023 (PLNT23), filtered BACODE=SOCO`.

Two things a reader should know before comparing this to §0.2, both measured rather than asserted:

* **The one non-SERC row contributes nothing and is therefore not filtered.** Of 332 rows, 331 are
  NERC `SERC` and one is `NPCC` — plant **67241 "401 South" (MA)**, the same balancing-authority
  mis-entry `zone_assignment` rejects at load (SOCO-20). It reports **0.0 MWh and no CO2**, so it
  moves neither aggregate by any amount. SOCO declares no `ISO_NERC_REGION_ADMISSION` key and this
  lane added none: a registry key that changes no number would be a change made for tidiness, and
  `footprint_plant_mask` is the registry predicate either way (rule 24 `[R-REGISTRY]`).
* **eGRID `biomass` is 10.2547 TWh and it is 44 pulp-and-paper black-liquor mills**, led by Mead
  Coated Board (0.706 TWh), International Paper Savanna Mill (0.625) and IP Prattville (0.611) — all
  `PLPRMFL = BLQ`. These are behind-the-fence industrial cogeneration that files under `BACODE SOCO`;
  EIA-930 puts ~2.54 TWh in `NG: OTH` and the rest nowhere. **eGRID's SOCO footprint is not SOCO's
  dispatchable fleet**, and a C1 comparison that reads the eGRID block as one will be wrong by ~4 %
  of footprint energy. The EIA-923 block in §0.2 is the self-consistent one.

---

## 1. Gate G9 — the zero-diff proof, measured as a diff rather than asserted

`build_reference()` MERGES per `--isos`, so the exit condition is that `--isos SOCO` moves nothing
else. The committed state was snapshotted before the run and compared after it.

### 1.1 `calibration_reference.json` — per-region canonical SHA-256 (first 16 hex)

| region | `isos.<R>` before | after | verdict | `egrid_benchmark.<R>` before | after | verdict |
|---|---|---|:--:|---|---|:--:|
| CAISO | `3a5f94500e96a0e1` | `3a5f94500e96a0e1` | **IDENTICAL** | `cfd5ba5e631d18c0` | `cfd5ba5e631d18c0` | **IDENTICAL** |
| ERCOT | `0eb631c960b0b66b` | `0eb631c960b0b66b` | **IDENTICAL** | `b6457fbc9770e5f1` | `b6457fbc9770e5f1` | **IDENTICAL** |
| MISO | `64a72d874b38de15` | `64a72d874b38de15` | **IDENTICAL** | `06549624144c27bd` | `06549624144c27bd` | **IDENTICAL** |
| NEISO | `9f6b9fb3228deb87` | `9f6b9fb3228deb87` | **IDENTICAL** | `e8ef7f538d3404e6` | `e8ef7f538d3404e6` | **IDENTICAL** |
| NWPP | `70dddb92ea29601f` | `70dddb92ea29601f` | **IDENTICAL** | `f123a84d58f3d2b8` | `f123a84d58f3d2b8` | **IDENTICAL** |
| NYISO | `fcdd24a131d50317` | `fcdd24a131d50317` | **IDENTICAL** | `5adb97359267efba` | `5adb97359267efba` | **IDENTICAL** |
| PJM | `7a3d1b475704580f` | `7a3d1b475704580f` | **IDENTICAL** | `9cc2105b54801ff0` | `9cc2105b54801ff0` | **IDENTICAL** |
| SPP | `34db0db8a68487d6` | `34db0db8a68487d6` | **IDENTICAL** | `6b5586da54dea52d` | `6b5586da54dea52d` | **IDENTICAL** |
| SOCO | ABSENT | `d710e2cadc5774b7` | NEW | ABSENT | `6d5b5095b859b2cd` | NEW |

Shared top-level keys the builder rewrites unconditionally: `description`, `calibration_years`,
`henry_hub_actual` — **all three IDENTICAL**. `generated` moves `2026-09-14 → 2026-09-16`, a date
stamp, by design.

**The whole-file diff is 295 insertions, 1 deletion, and the single deleted line is
`"generated": "2026-09-14",`.** Nothing else was removed or changed.

### 1.2 The 39 pre-existing per-year capacity CSVs

`cmp` over every committed `<ISO>_<year>_renewable_capacity.csv`: **39 of 39 byte-identical**
(CAISO ×5, ERCOT ×5, MISO ×6, NEISO ×7, NWPP ×3, NYISO ×4, PJM ×6, SPP ×3). Three files are NEW:
`SOCO_{2023,2024,2025}_renewable_capacity.csv`, 37 lines each.

### 1.3 `eia923_2025.json` — the one place a non-SOCO row DOES move, and it is main's, proved

`audit_eia923_completeness.audit()` loops over `_ISO_BUILDERS` and rewrites the whole file, so unlike
`build_reference` it has no `--isos` filter to hide behind. The committed part was last written
2026-09-14 and is **stale relative to `origin/main`'s own inputs**. Rather than assert that, a
CONTROL was run: `origin/main`'s `scripts/` restored into this tree with `data/clean` removed, the
audit re-run to a separate path. **That control is BYTE-IDENTICAL to the file this branch commits**
(`cmp` clean, whole file, including the `thresholds` block). So the committed file is exactly what
`origin/main` produces today and **this branch causes none of its deltas**. They are:

| delta | what | this branch's? |
|---|---|---|
| `isos.SOCO`, `families.SOCO` | NEW — the audit enumerates registered regions | the lane's own deliverable |
| `isos.NWPP`, `families.NWPP` | NEW — NWPP registered 2026-09-14 and **NWPP-31 never ran this audit**; its charter did not list the file | **no** — reproduced by the control |
| `isos.SPP.COAL_BIT` / `COAL_PRB` | one 2024 plant moved between the two classes: `n_prior_plants` 2→1, `prior_twh` 0.079→0.033 and 56.793→56.838, `retention` 0.475→1.089 and 1.217→1.216. **`status` and `gate` unchanged in both** (IMMATERIAL / INCOMPLETE) | **no** — reproduced by the control |

Suppressing the NWPP block or hand-patching the SPP numbers back would have committed a file the
script does not produce, which is worse than disclosing two deltas that change no verdict.
**Routed to SOCO-DESK → the NWPP lane** (§6): NWPP's own completeness block now exists, and NWPP-40
should know it arrived here rather than in NWPP-31.

---

## 2. The price side: nothing built, nothing substituted, and the skip verified by execution

The price question was decided by SOCO-13 under a STOP gate pre-registered before any datum was read,
and it **read NO** — three of five criteria failed (hourly coverage 3.66 / 2.69 / 2.64 % against a
≥ 5 % bar in every year; the index +54.2 / +72.1 % above its independent public anchor in 2024/2025
against ±15 %; the 2025 shape test), and **no bar moved after the series was seen**
(`FINDING-soco-13-2026-09-13.md`). This lane re-opened none of it.

| duty | state |
|---|---|
| `data/raw/_validation-source/actual_lmp.json` | **UNTOUCHED.** `git status` shows no modification across the whole lane. **No SOCO block was written — not an empty one, not a placeholder.** Its SOCO-shaped hole is load-bearing: it is the key the scorer reads |
| `TAIL_THRESHOLD` copy 1 — `scripts/calibration_verdict.py` | **NO SOCO KEY.** Measured at HEAD: `sorted(TAIL_THRESHOLD)` is `['CAISO','ERCOT','MISO','NEISO','NYISO','PJM','SPP']`. File untouched by this lane |
| copy 2 — `scripts/data/derive_actual_tail.py` | **NO SOCO KEY.** `grep -c '"SOCO"'` = 0. SOCO-20 already documented the skip at the table itself; nothing to add |
| copy 3 — `scripts/data/derive_actual_amplitude.py` | **NO SOCO ENTRY.** `grep -c '"SOCO"'` = 0, same |
| `actual_tail.json` / `actual_amplitude.json` | **NOT regenerated as a deliverable.** Both derives were RUN as a check and both emitted **zero SOCO rows**; the outputs were then reverted to their committed bytes (`cmp` clean). The re-runs also picked up +16 and +126 lines of *other regions'* price data landed since those files were last built, and another region's rows are not this lane's to move |
| a threshold for SOCO | **NOT invented.** A tail threshold with no price distribution to measure could only be chosen, and a chosen threshold is the fitted mechanism rule 1 `[R-STRUCT]` forbids |
| a neighbouring hub | **REFUSED, and not reached for.** MISO-South, a PJM or TVA proxy and an EIA state average are each the load proxy rule 13 `[R-MEASURED]` forbids. **Gate G17 upheld**; the desk has refused this twice and this lane did not make it a third |

### 2.1 The determination-side consequence, verified

**SOCO's ABSENCE from `actual_lmp.json` is exactly what makes the PRICE-UNSCORED class fire.**
Measured at HEAD: `calibration_verdict._price_reference_absent` returns `True` for `SOCO` and `NWPP`
and `False` for ERCOT / CAISO / MISO / PJM / NYISO / NEISO / SPP. The committed `actual_lmp.json`
carries blocks for seven regions and no SOCO. So a SOCO run reads
**`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`**, never `CALIBRATED`, scored on C1/C2/C4/C6/C8, with the
price gap on its determination basis at full magnitude (card S2's ruling; rubric v3.8, lane SOCO-22).
**Adding an empty or placeholder SOCO block would break that classifier.** It was not added.

---

## 3. What was built, and the one seam it needed

Scope: the `isos.SOCO` block of `calibration_reference.json`, the `egrid_benchmark.SOCO` block, the
three `SOCO_<year>_renewable_capacity.csv` files, the regenerated `eia923_2025.json`, and two script
registrations.

### 3.1 The years are 2023–2025 because that is the whole span the DATA supports

Not a tier choice. `data/raw/eia-930-hourly/SOCO hourly.parquet` carries **26,304 rows = three
years**, so `pre_window_series("SOCO", y)` is `None` for 2019, 2020, 2021 and 2022 — measured this
lane, and printed by the curator as `[skip ] SOCO <y>: no usable per-BA hourly series`. The EIA-923
side reaches further back (SOCO rows exist from 2018), but with no demand series there is nothing to
pair them with. **Extending the span is a SOCO-11-class fetch of more EIA-930 years, not a
reference-block edit** — and it is what plan manifest row 9 (holdout years 2019–2022) buys.

### 3.2 THE SEAM: `curate_demand_profile` needed more than `MODEL_ISOS += SOCO`

The routed item was one word in a frozenset. It was not enough, and the reason is worth stating
because it will recur for the tenth region.

`load_demand_meta("SOCO", 2023)` raised `ValueError: No EIA-930 data for ISO 'SOCO'`, and that single
raise blocks `build_calibration_reference._demand_totals` and through it SOCO's whole block. The
resolution order is: the `demand-profile` clean partition first, then the legacy
`eia_demand_meta.parquet` summary. **Neither existed.** The legacy `eia_demand_profiles.parquet` is a
frozen artifact with **no live builder** — `convert_eia930.py` builds the per-BA `<BA> hourly`
extracts, not this file — and it carries rows for seven ISOs × 2021–2025 and nothing else. So
`curate_all()`, which walks *that file's* groups, wrote nothing for SOCO no matter how many
registries named it.

The repair is the F3 repair `curate_pre_window` already performs, one axis over: **pre-window closes
a missing YEAR, `curate_unextracted` closes a missing ISO.** Both take the series from the per-BA
EIA-930 hourly extract through the same `load_demand` adapter, the same physical-bounds screen and
now the same writer (`_write_per_ba_partition`, factored out of the pre-window loop). That is rule 19
`[R-ONE-MECH]` — one construction, not a second parallel reconstruction — and rule 14 `[R-ACCURATE]`:
the accurate source is the array the LP dispatches, not a legacy summary that is known corrupt where
it does exist (PJM 2021's 2.1e9 MW peak, SPP 2023's 3,621,097 MW unit slip).

`unextracted_iso_years()` is **data-driven on the raw file, never an `iso == "SOCO"` ladder**: the
candidate years are the years the extract carries for anybody, and a pair is returned only when this
ISO has no row of its own. **For the seven ISOs the extract was built around it returns EMPTY** (each
carries all of 2021–2025), which is why their committed partitions cannot move, and a tenth region
registers here with no edit.

Result, from the run:

```
registered ISOs the legacy extract omits (5 (iso, year) pair(s))
  [skip ] SOCO 2021: no usable per-BA hourly series — partition not written
  [skip ] SOCO 2022: no usable per-BA hourly series — partition not written
  [write] SOCO 2023: in-window partition ... (0 hour(s) repaired, peak 45,558 MW, total 229.5 TWh)
  [write] SOCO 2024: in-window partition ... (0 hour(s) repaired, peak 47,368 MW, total 238.7 TWh)
  [write] SOCO 2025: in-window partition ... (0 hour(s) repaired, peak 46,490 MW, total 239.6 TWh)
```

**Zero hours repaired in all three years** — the physical-bounds screen flags nothing in SOCO's
demand series. (That is not the same as the series being clean; see §4.3.) 2021 and 2022 are SKIPPED
and reported, never padded (rule 13).

### 3.3 `_EIA923_EXTRA_FUELS_BY_ISO["SOCO"] = ("hydro",)` — declared on measurement

Conventional hydro is **3.52 / 2.84 / 2.39 %** of footprint energy (EIA-930 `NG: WAT` 8.4465 / 7.0798
/ 6.0123 TWh against 239.6251 / 249.5057 / 251.8847), above the 2 % materiality floor in every year.
Declaring it also puts it in the per-fuel incompleteness candidate set, which is what 2025 needs:
**EIA-923 reports 0.3275 TWh of SOCO hydro that year, a ratio of 0.054**, by far the worst-reported
of SOCO's benchmarked classes, and the guard swapped it to EIA-930's 6.0123 rather than score a model
class against a 95 %-missing actual. The 0.80 threshold, the EIA-930 authority and the per-fuel
evaluation are all unchanged; no parameter was added (rules 5 / 21).

**Oil is deliberately omitted**, on the SPP/NWPP precedent and on its own measurement: EIA-923 oil is
0.2666 / 0.2573 / 0.1042 TWh and EIA-930 agrees it is smaller still (0.0009 / 0.0017 / 0.0250) —
**0.11 / 0.10 / 0.04 %** of footprint energy, an order of magnitude below the floor, and a
starting/backup fleet rather than the winter dual-fuel switch that makes oil first-order in
NYISO/NEISO. **Pumped storage is not a candidate and cannot become one here**: `WAT`/`PS` is storage,
excluded by prime mover — and see §4.1, which is the reason it matters.

---

## 4. WHAT CANNOT BE SCORED AND WHY

This section is the one a later lane should quote. Nothing in it is a bug to fix or a hole to fill.

### 4.1 R-i — SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in EIA-930 for 2023 and most of 2024. This is a hard constraint on the C1 `fuelmix` benchmark, and it belongs on the first keeper's determination basis.

**State it in these words.** EIA-930's storage taxonomy — `NG: PS` (pumped storage), `NG: BAT`
(battery), `NG: SNB` (solar with non-battery storage), `NG: OES` (other energy storage) — reaches the
`SOCO` frame at a **cut-over on 2024-07-15**, and before that cut-over SOCO's pumped storage is not
reported anywhere. Measured, per year, on the committed `SOCO hourly.parquet`:

| year | `NG: PS` hours reported | first reported hour (UTC) | `NG: PS` annual | `NG: WAT` minimum |
|---|---:|---|---:|---:|
| 2023 | **0 of 8,760** | — | — | **+32 MW** |
| 2024 | **24 of 8,760** (0.27 %) | **2024-07-15 06:00** | −0.0010 TWh over those 24 h | **+35 MW** |
| 2025 | 8,633 of 8,760 | 2025-01-06 07:00 | **−0.4562 TWh** | +36 MW |

**The `NG: WAT` minimum is the load-bearing number.** Conventional hydro never goes negative in 2023
or 2024 — its floor is +32 and +35 MW — so **pumped-storage charging was not folded into the hydro
series. It was NOT REPORTED.** The 24 hours that do exist in 2024 span −1,083 to +1,264 MW, which
establishes that the unit is real and cycling across the whole period while being invisible for
99.7 % of it. Because the loader drops a storage series below 50 % hourly coverage
(`_STORAGE_MIN_COVERAGE_FRAC`), `load_eia_hourly_benchmark("SOCO", 2023)` and `…, 2024)` return **no
`pumped_storage` key at all**, while 2025 returns one.

**The consequence for scoring, stated so it is not discovered later.** The model will dispatch
1,306.6 MW of pumped storage in 2023 and 2024 and **there is no measured comparator for it in those
years** — not a poor one, none. Any C1 `fuelmix` statement about SOCO storage in 2023–2024 is a
statement about a class the actuals do not contain, and the residual it creates in every other class
(the pumping load is inside the metered `Demand` while the generation side omits it) cannot be
attributed. **This is a property of the published data, not a defect in the model and not a gap for a
lane to fill.** Reconstructing the missing PS series — from unit-level CEMS, from a plant schedule,
from the 2025 profile held backwards — would be fabricating an actual, which rule 13 `[R-MEASURED]`
forbids absolutely.

### 4.2 R-h — the loader-seam fuel-spike screens fire on SOCO, exactly where FINDING-soco-10 said they would. Reported; NO new constant proposed.

| year | series | hours | max MW | vs p99.9 | against |
|---|---|---:|---:|---:|---|
| 2023 | `NG: OIL` | 1 (h 7975) | 390 | 88 | an oil fleet that essentially never runs |
| 2024 | `NG: OIL` | 7 (h 386–392) | 801 | 72 | same |
| 2025 | `NG: NG` | 4 (h 1172, 1240, 2751, 7527) | **70,683** | 26,642 | a **36,336 MW** gas fleet |

All three are repaired by `actuals._screen_fuel_spike_columns` at the loader seam, where every
consumer inherits the repair (rule 19 `[R-ONE-MECH]`). **This lane proposes no new constant and no
new threshold.** The screen that catches them already exists and its bar is two order statistics of
the series itself; setting any additional bar now, having seen these outliers, is the fitted
threshold rule 23 `[R-FROZEN-DERIVE]` forbids. The 2025 `NG: NG` hours are the striking one — 70.7 GW
from a 36.3 GW fleet is a doubled meter, not a load event — and they are the reason the charter's
2025 gas target (125.4) and the committed EIA-930 comparator (125.2752) differ at all.

### 4.3 NEW (this lane): `min_mw` for 2025 is a metering artifact, and no existing screen can catch it

The committed 2025 `demand.min_mw` is **12,638 MW**, 23 % below the next-lowest hour of that year
(16,405 MW) and 51 % below its median. It is a single hour, **2025-10-23 21:00 UTC**, in which
`Demand` falls from 23,065 to 12,638 MW and `Net generation` falls from 24,701 to 15,559 MW
**together**, and both recover in the next hour (23,653 / 26,045). A balancing authority does not shed
10.4 GW for one hour and restore it; this is a partial-hour post.

**No new constant is proposed for it, and this is not a fixable-here defect.** The curator's screen is
`≤ 0` or `> 5 ×` median — one-sided upward — and the module's own documented empirical floor is
`min/median ≥ 0.2`. This hour is **0.486 × median**, so even the documented bound would not flag it.
Inventing a downward bound now, having seen this outlier, is a fitted threshold (rule 23). Energy
effect: **~10 GWh on 251.9 TWh, 0.004 %** — negligible for `total_twh` and for every class total.
**`min_mw` for SOCO 2025 must not be read as a real minimum.** Routed §6.

### 4.4 The EIA-930 balance identity does not close in 2025, by −0.6963 TWh

`Net generation − Demand − Total interchange` is **exactly zero in every hour of 2023 and 2024**. In
2025 it is nonzero in **633 hours (7.2 %)**, from 2025-02-19 03:00 UTC to year end, summing to
**−0.6963 TWh** — 0.28 % of net generation — with a mean of −1,100 MW and a range of −13,120 to
+2,649 MW. The by-fuel `NG:` columns still sum to `Net generation` to within −0.0111 TWh, so the
residual is in the demand/interchange balance, not the fuel decomposition. It correlates −0.35 with
`NG: PS` and begins in the same year the storage series does, which is suggestive and **not a
diagnosis this lane makes**. It moves nothing committed here (the `demand` block reads the demand
partition; `generation_twh` reads EIA-923 and, for 2025 hydro, EIA-930 fuels). Routed §6.

### 4.5 2025 is not flagged `eia923_incomplete`, and the gas split is still short

The whole-vintage flag tests the balancing authority's EIA-923 total against 0.90 × EIA-930 net
generation. SOCO 2025 is **0.9533** and clears it — the most complete 2025 vintage of any registered
region. The bar was not moved. But the per-class picture the completeness audit reports is not
uniform, and SOCO-40 needs the detail rather than the flag:

| class | 2025 vs 2024 | plants reporting | status |
|---|---|---:|---|
| CC_REGULAR | 113.32 vs 114.26 | 19/19 | **COMPLETE** |
| COAL_PRB | 28.25 vs 26.82 | 3/3 | **COMPLETE** |
| COAL_BIT | 15.02 vs 13.42 | 5/6 | incomplete |
| ST_GAS | 7.61 vs 9.66 | 6/7 | incomplete |
| CT_CHP | 1.78 vs 2.08 | 5/7 | incomplete |
| CT_PEAKER | 0.68 vs 5.06 | **6/23** | incomplete |
| ST_CHP | 0.58 vs 1.87 | 9/26 | incomplete |
| CC_CHP | 0.17 vs 3.46 | **1/6** | incomplete |

Both families read incomplete, so **no SOCO (ISO, class) pair is gate-eligible for 2025**. The
consequence is visible in §0.2: SOCO's committed 2025 `gas_ct` is 1.9659 TWh against 6.2537 in 2024,
because 17 of 23 peaker plants have not filed. **A 2025 gas-split comparison must defer to EIA-930**,
exactly as it must for every other region's 2025 — the flag's absence reflects a complete *aggregate*,
not a complete *peaker* census.

### 4.6 Already on the record, and still true

* **No price, at all.** §2. Not a gap, not a lane's to close, and a neighbouring hub stays refused.
* **Southern Power (respondent 186) is excluded from the zonal load basis** — 3.211 / 3.401 / 3.084
  TWh, 1.3–1.4 % of BA demand — and card S3's re-ruling requires it named on the first keeper's
  determination basis (desk r#5). It is a SOCO-32 input, not a benchmark this lane built, and is
  repeated here only so the determination basis collects in one place.
* **The seven UTC-bounded trailing hours of 2025** are bridged by the frame fill and WARNED, never
  padded (SOCO-11 item [4]). Measured this lane: they are the last 7 hours of the year, flat-filled
  at 28,408 MW, and they move neither `peak_mw` nor `min_mw`. They add +0.1989 TWh to the committed
  2025 `total_twh` over the raw frame's 239.3587.

---

## 5. Files changed, and what was not touched

| file | change |
|---|---|
| `data/raw/_validation-source/calibration_reference.json` | **+295 / −1**; the one deletion is the `generated` date stamp |
| `data/raw/_validation-source/SOCO_{2023,2024,2025}_renewable_capacity.csv` | NEW, 37 lines each |
| `frontend/data/backcast/completeness/eia923_2025.json` | regenerated; byte-identical to an `origin/main` control (§1.3) |
| `scripts/data/build_calibration_reference.py` | SOCO in `CALIBRATION_ISOS`; `CALIBRATION_YEARS_BY_ISO["SOCO"] = (2023, 2024, 2025)` carrying the price posture in full; `_EIA923_EXTRA_FUELS_BY_ISO["SOCO"] = ("hydro",)` |
| `scripts/data/curate_demand_profile.py` | `MODEL_ISOS += SOCO` (the routed item) plus `curate_unextracted` / `unextracted_iso_years` / `_write_per_ba_partition` (§3.2) |
| `docs/multi-iso/soco-addition-plan-2026-09.md` | §5 lane-table row and §9 findings index marked LANDED |

**Not touched:** `data/raw/_validation-source/actual_lmp.json` · `scripts/calibration_verdict.py` ·
`scripts/data/derive_actual_tail.py` · `scripts/data/derive_actual_amplitude.py` · anything under
`src/` · `ScenarioConfig` · any other region's block, row or CSV · `frontend/data/backcast/**` beyond
the one completeness part the charter names (the two derive outputs were run as checks and reverted,
§2).

**Rule 27 `[R-PUSH]`.** No existing source file ≥300 lines was rewritten from regenerated content;
both script edits are in-place `Edit`-class changes to the on-disk bytes, pushed as-is.
**Rule 28 `[R-MECH-MATRIX]`.** No mechanism was tested and no `ScenarioConfig` field was added, so
duties (b) and (c) do not bite and no matrix shard is edited.

**Lint.** `ruff check` and `ruff format --check` clean on both changed scripts.

---

## 6. Routed — none applied here

| item | owner | why not here |
|---|---|---|
| **§4.3** SOCO 2025 `min_mw` = 12,638 MW, a one-hour partial post at 2025-10-23 21:00 UTC that no existing screen catches | SOCO-DESK → whoever owns `eia930.demand._screen_demand_spikes` | a downward bound chosen after seeing this outlier is a fitted threshold (rule 23). The screen lives in `src/`, outside this lane's files |
| **§4.4** the 2025 `NG − D − TI` residual, 633 hours / −0.6963 TWh, beginning with the storage series | SOCO-DESK → SOCO-33 (the seam derive) | a diagnosis of EIA-930's own accounting, not a benchmark edit |
| **§1.3** `eia923_2025.json` now carries an NWPP block and a one-plant SPP prior-year move, both reproduced by an `origin/main` control | NWPP lane / SPP lane | neither is this lane's to author, and neither changes a status or a gate |
| `data/raw/eia-930-hourly/SOCO hourly.parquet` covers 2023–2025 only, so 2019–2022 cannot be referenced | SOCO-11 successor (plan manifest row 9) | a fetch, not a reference-block edit (§3.1) |
| `scripts/data/curate_validation.py` has not been run for the new SOCO CSVs | SOCO-33 / whoever regenerates `data/clean` | its output is derived and gitignored; the committed deliverable is complete without it |

---

## 7. What SOCO-40 inherits

* A `calibration_reference.json` SOCO block for **2023, 2024 and 2025** — every year the data
  supports — so rule 16 `[R-ALLYEARS]` is satisfiable in one `--year 2023 2024 2025` invocation, and
  rule 35 `[R-PROMOTE]` (c)'s year union is those three and nothing else until manifest row 9 lands.
* **C1 `fuelmix` and C2 `sysvol` are scorable**, with three constraints carried on the determination
  basis and not fixed: **R-i** (no pumped-storage comparator in 2023–2024, §4.1), the 2025 peaker
  census (§4.5), and the eGRID black-liquor footprint (§0.4).
* **C3a / C3b / C3c are UNSCORABLE and that is the RULED outcome, not a gap.** The run reads
  `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` and may never read `CALIBRATED`; the price gap is named on
  its determination basis at full magnitude. A lane that finds the price criteria blank should read
  §2 and `FINDING-soco-13` — **not** reach for a neighbouring hub.
* **A caveat to state, not to solve:** `demand.min_mw` for 2025 is an artifact hour (§4.3).
* The demand partitions SOCO's block depends on live under `data/clean/`, which is **derived and
  gitignored**. A fresh container must run `scripts/data/curate_demand_profile.py` before
  `build_calibration_reference` will resolve SOCO — the same standing requirement PJM 2019 and
  MISO 2020 carry.

---

## Log entry

```
## 2026-09-16 — SOCO-31: the scoring benchmarks (W3, zero-LP)

GATE G9 PASSES, MEASURED AS A DIFF. build_reference --isos SOCO moved nothing else:
all EIGHT pre-existing regions byte-identical on both isos.<R> and egrid_benchmark.<R>
(CAISO/ERCOT/MISO/NEISO/NWPP/NYISO/PJM/SPP), 39 of 39 pre-existing renewable-capacity
CSVs byte-identical by cmp, whole-file diff +295/-1 with the ONE deletion being the
"generated" date stamp. description / calibration_years / henry_hub_actual unchanged.

SOCO BENCHMARK, 2023/2024/2025. Demand 229.4688 / 238.6990 / 239.5576 TWh; peak
45,558 / 47,368 / 46,490 MW. NET EXPORTER EVERY YEAR: interchange +10.1562 / +10.8067
/ +13.0321 TWh, net generation 239.6251 / 249.5057 / 251.8847 TWh, and demand + export
= 239.63 / 249.51 / 252.59 reproduces the charter's target to the 0.01 TWh. EIA-923 by
fuel: coal 37.2434 / 40.2395 / 43.2752, gas_cc 117.3899 / 113.7601 / 109.7396, gas_ct
6.6852 / 6.2537 / 1.9659, gas_st 12.6350 / 9.4821 / 6.6071, nuclear 52.1354 / 63.0598 /
64.2324, solar 9.0323 / 10.3849 / 10.3165, hydro 6.8150 / 6.3014 / 6.0123 (2025 swapped
to EIA-930, 923 ratio 0.054), wind 0.0. Three capacity CSVs, 37 lines each -- solar
only, because SOCO has no wind. egrid_benchmark: eGRID 2023 PLNT23 BACODE=SOCO, 332
rows, the one non-SERC row (67241 MA) contributing 0.0 MWh and no CO2 -- stated, not
filtered, and no NERC admission key added for a row that moves no number.

THE PRICE SIDE IS NOT LANDED AND NOT SUBSTITUTED. actual_lmp.json UNTOUCHED -- no SOCO
block, not even an empty one, because its ABSENCE is the key rubric v3.8 reads:
_price_reference_absent("SOCO") measured True at HEAD, so a SOCO run reads
PHYSICALLY-CALIBRATED (PRICE UNSCORED). TAIL_THRESHOLD skipped in all three copies
(gate G6) and VERIFIED BY EXECUTION: both derives re-run, both emitted ZERO SOCO rows,
both outputs reverted to committed bytes. Gate G17 upheld -- no neighbouring hub, no
adjusted MISO-South series, no state average; not reached for.

THE ROUTED MODEL_ISOS ITEM WAS NOT ENOUGH. The legacy eia_demand_profiles extract is
frozen, has no live builder and carries NO SOCO rows, so curate_all wrote nothing and
load_demand_meta("SOCO", 2023) still raised -- the F3 failure one axis over.
curate_unextracted() closes it as the in-window twin of curate_pre_window(): same
per-BA adapter, same screen, same writer (_write_per_ba_partition), and
unextracted_iso_years() is data-driven on the raw file -- EMPTY for the seven ISOs the
extract was built around, so their partitions cannot move. SOCO 2021/2022 SKIPPED and
reported, never padded. _EIA923_EXTRA_FUELS_BY_ISO["SOCO"] = ("hydro",) on measurement
(3.52/2.84/2.39 % of footprint energy); oil omitted at 0.11/0.10/0.04 %.

WHAT CANNOT BE SCORED. R-i: SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in
EIA-930 for 2023 (NG: PS 0 of 8,760 hours) and 99.7 % of 2024 (24 hours, all from the
2024-07-15 taxonomy cut-over), and NG: WAT never goes negative before it (min +32 and
+35 MW) -- so PS charging was NOT folded into hydro, it was NOT REPORTED. A hard
constraint on the C1 fuelmix benchmark, for the first keeper's determination basis,
never a hole to fill. R-h loader-seam spikes reported with NO new constant proposed
(rule 23): NG: OIL 1 h 2023 and 7 h 2024, and four 2025 NG: NG hours at 70,683 MW
against a 36,336 MW gas fleet. NEW THIS LANE: 2025 demand.min_mw = 12,638 MW is a
one-hour partial post (2025-10-23 21:00 UTC, D and NG both halve and both recover) that
NO existing screen catches -- 0.486x median against a documented 0.2 floor -- reported
and ROUTED, no downward bound invented. Also new: the EIA-930 balance identity
NG - D - TI is exactly zero in every hour of 2023 and 2024 and nonzero in 633 hours of
2025 (-0.6963 TWh, 0.28 % of net generation), routed to SOCO-33.

eia923_2025.json regenerated. It carries two non-SOCO deltas -- a NEW NWPP block (the
audit loops over _ISO_BUILDERS and NWPP-31 never ran it) and a one-plant SPP
COAL_BIT/COAL_PRB prior-year move with NO status and NO gate change -- and BOTH are
origin/main's own, proved by a control run of main's code with data/clean removed that
is BYTE-IDENTICAL to the committed file. Routed to the NWPP and SPP lanes. 2025 carries
no eia923_incomplete flag (ratio 0.9533, the most complete of all nine regions) but its
PEAKER census is not: 6 of 23 CT_PEAKER plants and 1 of 6 CC_CHP have filed, so no SOCO
pair is gate-eligible and a 2025 gas-split comparison must defer to EIA-930.
```
