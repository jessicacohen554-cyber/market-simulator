# SHARD REPORT — nyiso-228 ARM B (SEAM-R)

**Session:** nyiso-228 shard B · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/nyiso228-seamr-span` · **Bundle:** `results/calibration/nyiso228_seamr_span`
**Charter:** `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` §3.2 (DIAGNOSTIC, not a promotion
candidate) and §4 (STOP gates).

**Variable — ONE flag:** `nyiso_import_reconciliation` **True → False**.
(`--set nyiso_hub_gap_month_level=false` is the PRECOMMIT §3 base restoration shared by all three
arms — it returns the `nyiso223_gapfill_span` base to the keeper recipe exactly — not a second
delta.)

**Purpose:** falsify nyiso-99's standing caveat that the reconciled monthly import quota is met at
the **wrong hours**. No session has ever measured that claim by removing the band.

---

## 1. HARD STOPS — all three observed and PASSED

| # | requirement | observed | verdict |
|---|---|---|---|
| **1** | `git rev-parse HEAD` == `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | **PASS** |
| **2** | config signature (below) | all six fields as required at the base | **PASS (pre-solve); re-verified post-solve in §2** |
| **3** | exactly ONE flag moves | `nyiso_import_reconciliation` only | **PASS** |

**HARD STOP 2 — base config signature**, read from
`results/calibration/nyiso223_gapfill_span/run_config.json` (pre-solve):

| field | required | base value | where it lives |
|---|---|---|---|
| `nyiso_import_reconciliation` | **false** (my delta) | `True` → set `false` | `scenario_config` |
| `nyiso_hub_gap_month_level` | **false** | `True` → set `false` (base restoration) | `scenario_config` |
| `priced_interchange` | **true** | `True` | `calibration_flags` (top-level; it is not a `ScenarioConfig` field — `model/interchange/spec.py::resolve_priced_interchange` is a tri-state CLI flag, persisted by `pipeline/persist.py`) |
| `nyiso_import_hub_prices` | **true** | `True` | `scenario_config` |
| `nyiso_seam_par_attribution` | **true** | `True` | `scenario_config` |
| `offer_curve_by_group["CT_PEAKER"]["peak"]` | **4.0** (unmoved) | `4.0` | `scenario_config` |

`CT_PEAKER.peak` is **4.0 and stays 4.0** — the offer surface is arm A's variable, not mine.

---

## 2. CONTAINER PREP LOG

| step | result |
|---|---|
| `hydrate_data.py --profile nyiso` | no-op — **this is a FULL clone**, every blob already local |
| `prepare_solve_container.py` | 8 GiB swap added at `/swapfile-marketsim`; RAM 15.7 + swap 8.0 = **23.7 GiB** |
| env pins | `MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` exported |
| pip pins | PyYAML, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, openpyxl, tzdata — all exit 0 |
| `regenerate_clean.py` (27 datatypes) | `data/clean/` started **EMPTY**; see note below |
| `curate_lmp.py` | **NOT run**, per charter (known pre-existing `KeyError: 'MGHG'`) |

**One prep finding, recorded rather than repaired (rule 32: a shard that repairs infrastructure is a
FAILURE).** `market_sim` lives under `src/`, so the charter's `PYTHONPATH=.` does not import it in a
*subprocess* that `regenerate_clean.py` launches from a different cwd. `curate_fleet.py` and most
others insert their own `sys.path` and are unaffected; `curate_fuel_prices.py` and
`curate_reference.py` do not, and failed `ModuleNotFoundError: No module named 'market_sim'`.
**Fixed in my shell only** — `PYTHONPATH=/home/user/market-simulator/src:/home/user/market-simulator`.
**No file under `scripts/` or `src/` was edited.** Flagged for the parent; not my scope to fix.

All 27 datatype names verified present in `regenerate_clean.py --list` — none dropped.

---

## 3. KEEPER 2023 COMPARATOR — recomputed here from the committed sidecar (zero-LP)

`results/calibration/nyiso_fuelvintage_A/hourly/class_hourly_2023.parquet`, P1, klass `import`:

**Annual: 23.3357 TWh** (charter quotes 23.33 — reproduced; measured EIA-930 target 23.45).

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2423.5 | 1995.4 | 2742.8 | 2183.8 | 1614.3 | 1641.2 | 2170.0 | 2131.0 | 2017.2 | 1706.3 | 1063.8 | 1646.3 |

(GWh.) This is the G-LIVE baseline.

---

## 4. THE SCREEN — 2023, and BOTH GATES CLEARED

**Screen year 2023**, named in the PRECOMMIT §4 on the band's **own measured footprint** (the
un-banded priced node clears a near-flat 18.5–21.6 TWh against a 2023 measured schedule of
23.45 TWh, the widest of the four years) — **never** on the residual.

`replay_keeper.py` exit **0**, wall **247 s**. Config signature **re-verified post-solve** from the
written `run_config.json`: `nyiso_import_reconciliation` **False**, `nyiso_hub_gap_month_level`
**False**, `priced_interchange` **True**, `nyiso_import_hub_prices` **True**,
`nyiso_seam_par_attribution` **True**, `CT_PEAKER.peak` **4.0**. HARD STOP 2 holds on the artifact,
not just on the intent.

### 4.1 G-LIVE — **FIRES**. The band is live, and it binds on MONTHLY SHAPE, not on the annual level.

Priced import node, P1, monthly net interchange (GWh):

| month | keeper | arm | delta | delta % |
|---|---|---|---|---|
| Jan | 2423.5 | 2102.3 | **−321.3** | **−13.3 %** |
| Feb | 1995.4 | 1955.3 | −40.1 | −2.0 % |
| Mar | 2742.8 | 2665.0 | −77.8 | −2.8 % |
| Apr | 2183.8 | 2108.9 | −74.9 | −3.4 % |
| May | 1614.3 | 1335.0 | **−279.3** | **−17.3 %** |
| Jun | 1641.2 | 1905.9 | **+264.7** | **+16.1 %** |
| Jul | 2170.0 | 2360.6 | +190.6 | +8.8 % |
| Aug | 2131.0 | 1994.7 | −136.2 | −6.4 % |
| Sep | 2017.2 | 2019.1 | +1.8 | +0.1 % |
| Oct | 1706.3 | 1861.5 | +155.2 | +9.1 % |
| Nov | 1063.8 | 1417.0 | **+353.2** | **+33.2 %** |
| Dec | 1646.3 | 2241.8 | **+595.5** | **+36.2 %** |

**Annual: keeper 23.3357 TWh → arm 23.9671 TWh, +0.6314 TWh (+2.71 %).**
Against the measured EIA-930 2023 target of 23.45 TWh: keeper **−0.49 %**, arm **+2.21 %**.

**G-LIVE verdict: FIRES — the arm is NOT inert.** Five months depart by more than 13 %
(Dec +36.2 %, Nov +33.2 %, May −17.3 %, Jun +16.1 %, Jan −13.3 %), far beyond any band width.
Per the charter this authorizes the remaining three years.

**The shape of the result is itself the finding, and it is directly on nyiso-99's caveat.** The
annual total moves only **+2.71 %** while individual months move as much as **±36 %**. That is the
signature of a constraint that was binding on *monthly allocation* rather than on *annual volume*:
with the band removed, the model's own economics redistribute ~0.6 TWh out of winter/spring
(Jan, May) into late autumn/early winter (Nov, Dec) and midsummer (Jun, Jul) — while the annual
level stays close to measured on its own. The band was therefore doing real work on **when** the
imports arrive, which is exactly the object nyiso-99 flagged. **Whether the unbanded timing is
BETTER is not this gate's question and is not claimed here** — that is leg (i) of §3.2's two-legged
bar (interchange hourly `r`), which is the parent's scoring call across all four years.

### 4.2 G-ENERGY — **PASS**

| | keeper | arm | delta |
|---|---|---|---|
| ISO total model energy (P1) | 148.3100 TWh | 148.3297 TWh | **+0.0197 TWh** |

Within the 0.05 TWh tolerance. **PASS.**

### 4.3 Class energy, 2023 (P1, TWh) — where the displaced energy went

| klass | keeper | arm | delta |
|---|---|---|---|
| import | 23.3357 | 23.9671 | **+0.6314** |
| CC_REGULAR | 33.7987 | 33.2586 | **−0.5400** |
| ST_GAS | 9.8097 | 9.5018 | **−0.3079** |
| hydro | 26.6158 | 26.8327 | +0.2169 |
| CC_CHP | 15.9057 | 16.0158 | +0.1101 |
| CT_CHP | 1.5350 | 1.4761 | −0.0589 |
| ST_CHP | 1.3686 | 1.3443 | −0.0244 |
| CT_PEAKER | 0.3967 | 0.3882 | −0.0084 |
| solar | 0.2798 | 0.2806 | +0.0007 |
| oil | 0.1497 | 0.1498 | +0.0001 |
| nuclear / wind / biomass / OTHER / COAL_BIT / COAL_PRB | — | — | **0.0000** |
| **ISO TOTAL** | **148.3100** | **148.3297** | **+0.0197** |

The extra import displaces **gas** (CC_REGULAR −0.540, ST_GAS −0.308) — the merit-order response the
mechanism's own arithmetic implies. Nuclear, wind, biomass and OTHER are untouched to 4 dp, as
must-run/zero-MC classes should be. §3.2 predicted "C1/C2 gas volume moves 1–3 TWh"; the measured
2023 move is **0.85 TWh** across both gas classes — **below the predicted range**, and recorded here
as landed rather than re-framed.

### 4.4 Price and reserves, 2023 (P1, load-weighted over the five load zones)

| | keeper | arm |
|---|---|---|
| mean | 32.356 | **32.591** |
| p95 | 48.138 | 47.759 |
| p99 | 63.228 | **63.243** |
| max | 213.860 | **213.862** |
| hours >$150 | 8 | 8 |
| hours >$200 | 1 | 1 |
| hours >$300 | 0 | 0 |

The upper tail is **untouched** (p99 +0.015, max +0.002, h>150/200/300 identical). That is the
expected and correct result for this arm: SEAM-R moves *when* imports arrive, not the offer stack
that sets the ceiling. **Arm A owns the tail; this arm does not and does not pretend to.**

Reserve families, 2023 (P1):

| family | hours dual>0 | max dual | hours shortfall>0 | max shortfall MW |
|---|---|---|---|---|
| `nyca_30min_total` | 0 | 0.00 | 0 | 0.0 |
| `nyca_10min_total` | 0 | 0.00 | 0 | 0.0 |
| `nyca_10min_spin` | 0 | 0.00 | 0 | 0.0 |
| `east_10min_total` | 0 | 0.00 | 0 | 0.0 |
| `seny_30min_total` | 4 | 40.00 | 3 | 205.6 |
| `nyc_10min_total` | 21 | 25.00 | 20 | 342.7 |
| `nyc_30min_total` | 16 | 25.00 | 13 | 416.3 |
| `li_10min_total` | 0 | 0.00 | 0 | 0.0 |
| `li_30min_total` | 0 | 0.00 | 0 | 0.0 |

Unchanged in character from the keeper (PRECOMMIT §1.3): the three NYCA-wide families never bind,
and the ceiling is a $25–40 locational adder. This arm does not touch that.

`legitimacy_diagnostics.json` **regenerated** (22,309 bytes, `gates` block present).
`metrics.json` / `calibration_attestation.json` are **not yet written** — the replay driver emits
them at the end of the full span, so they arrive with the remaining three years.

---

## 5. PREP — two partitions the charter's list did not cover

Following the parent's steer, speculative curation was **stopped** and only what the solve itself
named was regenerated. `pip install -e .` was run (the repo is a `src/` layout, which is the real
fix for the import failure recorded in §2 — better than my in-shell `PYTHONPATH` workaround).

| attempt | solve failed on | regenerated | wall |
|---|---|---|---|
| 1 | `nyiso_li_lcr_tsl=True` but no published Long Island `transfer_security_limit` for DY 2023/2024 | **`capacity-deliverability`** only (NYISO 35 rows) — **absent from the charter's 27-name list** | 29 s to fail |
| 2 | `nyiso_seam_par_attribution 2023` could not read the `nyiso-interface-flows` clean partition | **`nyiso-interface-flows`** only | 2 s to fail |
| 3 | — | — | **247 s, exit 0** |

Neither failure was a config problem: attempt 1 reached fleet construction (460 generators), 2023
TTC resolution and the year loop before raising. **`data/clean/` was never fully rebuilt** and did
not need to be — 12 datatypes total.

---

## 6. THE FULL SPAN — and the answer to nyiso-99

`--reuse-solved` against the shard's **own** out-dir fails (`shutil.SameFileError` on
`dispatch/2023_P1.parquet` — `_copy_reused_year` copies the reused year onto itself). Rather than
drop it and re-solve 2023 (~18 min total, at rule 32(b)'s ceiling), the 2023 bundle was copied
**out of the repo** to the scratchpad and `--reuse-solved` pointed at the copy: 2023 byte-copies
forward, only 2022/2024/2025 solve. Driver confirmed `reusing years [2023], solving fresh
[2022, 2024, 2025]`. Nothing deleted (rule 31 `[R-RETAIN]`); the copy never touches the repo.

| year | wall | exit |
|---|---|---|
| 2023 (screen) | **247 s** | **0** |
| 2022 + 2024 + 2025 (one invocation, sequential per rule 12) | **721 s** | **0** |

### 6.1 THE HEADLINE — BOTH legs of §3.2's promotion bar FAIL, and the caveat is falsified **against** the arm

§3.2 makes the arm a promotion candidate only if **both** hold. Measured over all four years:

**Leg (ii) — annual net interchange within ±5 % of measured EIA-930, EVERY year.** Measured is
computed here from `data/raw/eia-930-hourly/NYIS hourly.parquet` (`−Total interchange`); it
reproduces the PRECOMMIT's stated values (2023 23.45, 2024 20.35, 2025 19.09) and supplies 2022.

| year | measured TWh | keeper TWh | keeper % | **arm TWh** | **arm %** | leg (ii) |
|---|---|---|---|---|---|---|
| 2022 | 28.3102 | 27.8487 | −1.63 % | **24.1639** | **−14.65 %** | **FAIL** |
| 2023 | 23.4532 | 23.3357 | −0.50 % | **23.9671** | **+2.19 %** | PASS |
| 2024 | 20.3913 | 20.7057 | +1.54 % | **25.3148** | **+24.15 %** | **FAIL** |
| 2025 | 19.0853 | 19.3577 | +1.43 % | **22.8626** | **+19.79 %** | **FAIL** |

**FAILS in 3 of 4 years.** The keeper sits within ±1.7 % of measured in every year; the unbanded
arm swings from −14.7 % to +24.2 %.

**Leg (i) — interchange hourly `r` improves in ≥3 of 4 years.** Model `import` against measured
hourly, aligned on local time (8,759 overlapping hours/yr):

| year | keeper `r` | **arm `r`** | delta | |
|---|---|---|---|---|
| 2022 | 0.7933 | 0.7730 | **−0.0203** | worse |
| 2023 | 0.6561 | 0.5146 | **−0.1414** | worse |
| 2024 | 0.6571 | 0.5296 | **−0.1275** | worse |
| 2025 | 0.4567 | 0.3940 | **−0.0627** | worse |

**Improves in 0 of 4 years.** *(Method validation: my keeper `r` — 0.793 / 0.656 / 0.657 / 0.457 —
reproduces the committed payload's `fuelRows` 0.794 / 0.660 / 0.679 / 0.473, so the comparison is
on the same object the dashboard reports.)*

### 6.2 WHAT THIS ANSWERS — nyiso-99's caveat is FALSIFIED, in the direction of the band being GOOD

The matrix row's standing caveat is: *"the reconciled monthly quota is met at the WRONG HOURS."*
The implied claim is that `nyiso_import_reconciliation` buys an annual level at the cost of hourly
timing. **Removing the band tests that claim directly, and the claim does not survive:** hourly `r`
falls in **all four years**, by as much as **−0.14**. The band is therefore **not** merely an
annual-level pin — it is also *improving* the hour-to-hour allocation relative to an unbanded
priced node, while simultaneously holding the annual level within ±1.7 % of measured.

So the §1.4 chain in the PRECOMMIT — that interchange `r` is a symptom of the missing price tail
(§1.2), not of the band — **survives this test**. The too-flat internal price cannot allocate
imports to the right hours, and taking the band off does not fix that; it makes it worse, because
the flat internal price is then the *only* thing allocating them. **This closes the question, and it
is the shard's result.** Per rule 29 `[R-SCREEN]`, a gate may kill an arm and never promote one —
here the arm is killed by its own pre-registered bar, not by a residual.

### 6.3 Import footprint — annual TWh + 12 monthly GWh, every year, beside the keeper

**2022** — keeper 27.8487 → arm 24.1639 TWh (**−3.6848**, −13.23 %)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 2627.1 | 2223.2 | 2687.3 | 1273.7 | 1159.2 | 2194.7 | 2945.7 | 3423.7 | 3223.6 | 2060.3 | 1641.1 | 2389.1 |
| arm | 2640.5 | 1846.3 | 2263.4 | 1129.9 | 1090.1 | 1777.0 | 2547.8 | 2959.3 | 2667.1 | 1645.2 | 1537.9 | 2059.3 |
| delta | +13.4 | −376.9 | −423.9 | −143.9 | −69.1 | −417.7 | −397.9 | −464.4 | −556.5 | −415.1 | −103.2 | −329.7 |
| delta % | +0.5 | −17.0 | −15.8 | −11.3 | −6.0 | −19.0 | −13.5 | −13.6 | −17.3 | −20.1 | −6.3 | −13.8 |

**2023** — keeper 23.3357 → arm 23.9671 TWh (**+0.6314**, +2.71 %)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 2423.5 | 1995.4 | 2742.8 | 2183.8 | 1614.3 | 1641.2 | 2170.0 | 2131.0 | 2017.2 | 1706.3 | 1063.8 | 1646.3 |
| arm | 2102.3 | 1955.3 | 2665.0 | 2108.9 | 1335.0 | 1905.9 | 2360.6 | 1994.7 | 2019.1 | 1861.5 | 1417.0 | 2241.8 |
| delta | −321.3 | −40.1 | −77.8 | −74.9 | −279.3 | +264.7 | +190.6 | −136.2 | +1.8 | +155.2 | +353.2 | +595.5 |
| delta % | −13.3 | −2.0 | −2.8 | −3.4 | −17.3 | +16.1 | +8.8 | −6.4 | +0.1 | +9.1 | +33.2 | +36.2 |

**2024** — keeper 20.7057 → arm 25.3148 TWh (**+4.6091**, +22.26 %)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 2017.5 | 1381.2 | 1765.6 | 1054.2 | 1243.6 | 2255.5 | 2617.4 | 2477.1 | 1862.0 | 1282.4 | 1185.6 | 1563.5 |
| arm | 2322.5 | 1772.9 | 2554.8 | 1669.1 | 1704.5 | 2404.6 | 2621.2 | 2655.9 | 2283.8 | 1722.7 | 1403.0 | 2199.9 |
| delta | +305.0 | +391.6 | +789.2 | +614.9 | +460.9 | +149.1 | +3.9 | +178.7 | +421.8 | +440.3 | +217.3 | +636.4 |
| delta % | +15.1 | +28.4 | +44.7 | +58.3 | +37.1 | +6.6 | +0.1 | +7.2 | +22.7 | +34.3 | +18.3 | +40.7 |

**2025** — keeper 19.3577 → arm 22.8626 TWh (**+3.5050**, +18.11 %)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 2259.8 | 1894.6 | 1480.9 | 1298.2 | 1280.1 | 1798.0 | 2180.3 | 1504.6 | 1597.3 | 1454.4 | 1269.3 | 1340.2 |
| arm | 2213.1 | 1893.5 | 1882.9 | 1439.7 | 1281.2 | 1975.7 | 2517.6 | 2105.7 | 1929.6 | 1900.6 | 1618.3 | 2104.8 |
| delta | −46.7 | −1.2 | +402.0 | +141.5 | +1.1 | +177.8 | +337.3 | +601.1 | +332.3 | +446.2 | +349.0 | +764.6 |
| delta % | −2.1 | −0.1 | +27.1 | +10.9 | +0.1 | +9.9 | +15.5 | +40.0 | +20.8 | +30.7 | +27.5 | +57.1 |

**2022 goes the OTHER WAY from 2024/2025** (−13 % vs +20 %), and that asymmetry matters: 2022 is the
high-gas year (Henry Hub $6.45 vs $2.19/$3.52). With expensive domestic gas the unbanded node
*under*-imports; with cheap gas it *over*-imports. The band was absorbing a fuel-price-conditioned
seam error, which is the substantive thing this diagnostic exposes and hands to the parent.

### 6.4 Class energy TWh (P1), arm vs keeper — top movers

| year | ISO total keeper → arm (delta) | import | CC_REGULAR | CC_CHP | ST_GAS | hydro | CT_PEAKER |
|---|---|---|---|---|---|---|---|
| 2022 | 154.1908 → 154.1514 (**−0.0394**) | **−3.6848** | +0.4754 | +2.3405 | +0.2026 | +0.2980 | +0.0973 |
| 2023 | 148.3100 → 148.3297 (**+0.0197**) | **+0.6314** | −0.5400 | +0.1101 | −0.3079 | +0.2169 | −0.0084 |
| 2024 | 152.1795 → 152.3508 (**+0.1713**) | **+4.6091** | −1.5944 | −1.6376 | −0.7171 | 0.0000 | −0.0374 |
| 2025 | 153.2063 → 153.3013 (**+0.0950**) | **+3.5050** | −0.9765 | −0.8665 | −0.9223 | 0.0000 | −0.2409 |

(2022 also: COAL_PRB +0.1631.) Nuclear, wind, biomass and OTHER move **0.0000** in every year.

**Reported against the pre-registered tolerance rather than quietly:** G-ENERGY was pre-registered
on the **screen year**, where it passed (+0.0197 ≤ 0.05). Carried to the other three years it would
**FAIL 2024 (+0.1713)** and **FAIL 2025 (+0.0950)**, and pass 2022 (−0.0394). The gate's own text
scopes it to the screen, so this is **not** a gate trip — but a ±0.17 TWh energy-balance drift on a
one-flag arm is a real observation and is the parent's to weigh, not mine to explain away.

§3.2 predicted gas moving 1–3 TWh: measured **0.68 (2022, and the wrong sign) / 0.85 (2023) /
3.95 (2024) / 2.77 (2025)**. Two years inside, 2023 below, 2022 inverted. Recorded as landed.

### 6.5 LW price, all four years (P1, five load zones, `NYISO_external` excluded)

| year | | mean | p95 | p99 | max | >$150 | >$200 | >$300 |
|---|---|---|---|---|---|---|---|---|
| 2022 | keeper | 65.282 | 122.398 | 170.319 | 1429.988 | 198 | 30 | 8 |
| | **arm** | **71.098** | 125.824 | 175.486 | 1429.988 | 233 | 36 | **8** |
| 2023 | keeper | 32.356 | 48.138 | 63.228 | 213.860 | 8 | 1 | 0 |
| | **arm** | **32.591** | 47.759 | 63.243 | 213.862 | 8 | 1 | **0** |
| 2024 | keeper | 38.633 | 60.636 | 115.919 | 203.639 | 44 | 7 | 0 |
| | **arm** | **36.324** | 56.645 | 115.758 | 203.983 | 41 | 6 | **0** |
| 2025 | keeper | 58.357 | 124.736 | 177.200 | 313.944 | 220 | 43 | 3 |
| | **arm** | **55.930** | 123.001 | 178.524 | 313.944 | 198 | 44 | **3** |

**The upper tail is untouched in every year** — hours >$300 identical (8 / 0 / 0 / 3) and the maxima
move by ≤ $0.35. Mean moves +5.8 (2022) and −2.3 / −2.4 (2024/2025), tracking the import direction.
**This arm does not build a tail and never claimed to; that is arm A's object.** PRECOMMIT §1.2's
finding — the model's ceiling is ~$200–315 and no seam lever reaches it — is untouched.

### 6.6 Reserve families (P1), arm, all four years

| year | family | h dual>0 | max dual | h short>0 | max short MW |
|---|---|---|---|---|---|
| **2022** | `east_10min_total` | 9 | **775.000** | 8 | 1200.000 |
| | `seny_30min_total` | 12 | **500.000** | 12 | 1800.000 |
| | `nyc_30min_total` | 74 | 49.418 | 51 | 1000.000 |
| | `nyc_10min_total` | 154 | 25.000 | 95 | 500.000 |
| | `li_30min_total` | 4 | 25.000 | 4 | 540.000 |
| | `li_10min_total` | 3 | 25.000 | 3 | 120.000 |
| | `nyca_30min` / `nyca_10min` / `nyca_10min_spin` | **0** | **0.000** | 0 | 0.000 |
| **2023** | `nyc_10min_total` | 21 | 25.000 | 20 | 342.715 |
| | `nyc_30min_total` | 16 | 25.000 | 13 | 416.315 |
| | `seny_30min_total` | 4 | 40.000 | 3 | 205.636 |
| | all six others incl. every `nyca_*` | **0** | **0.000** | 0 | 0.000 |
| **2024** | `nyc_10min_total` | 23 | 25.000 | 15 | 342.715 |
| | `nyc_30min_total` | 9 | 25.000 | 9 | 388.715 |
| | `east_10min_total` | 3 | 32.694 | 0 | 0.000 |
| | `seny_30min_total` | 1 | 40.000 | 1 | 2.477 |
| | `li_*` and every `nyca_*` | **0** | **0.000** | 0 | 0.000 |
| **2025** | `nyc_10min_total` | 38 | 25.000 | 33 | 460.515 |
| | `nyc_30min_total` | 24 | 25.000 | 23 | 481.115 |
| | `seny_30min_total` | 8 | 40.000 | 7 | 424.354 |
| | `east_10min_total` | 1 | 1.949 | 0 | 0.000 |
| | `li_*` and every `nyca_*` | **0** | **0.000** | 0 | 0.000 |

**The three NYCA-wide families never bind in any hour of any year** — 0 h, max dual 0.000, in
2022–2025 alike. This independently reconfirms PRECOMMIT §1.3 on a *fourth* year (2022) and on a
different recipe, and it is the structural fact behind the missing tail. **2022 is the exception
that proves the point**: `east_10min_total` reaches its full **$775** published penalty and
`seny_30min_total` its **$500** in Elliott-class hours — the *locational* families can reach real
scarcity prices, while the NYCA-wide ones never do.

### 6.7 Artifacts

`legitimacy_diagnostics.json` **regenerated** for the full span (`gates` block present) — the
rule 20 `[R-DOF]` / C8 artifact the replay path owes.
**`metrics.json` and `calibration_attestation.json` are absent, and that is correct, not a gap:**
both are written by `scripts/calibration_verdict.py` / `scripts/dashboard_add_run.py`, which are the
**parent's** scoring-and-registration path and are named on this shard's forbidden list. There are
therefore no `metrics.json` headline rows for me to quote; the parent produces them when it scores
C3a/C3b.

---

## 7. PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — the bundle is on LOCAL DISK ONLY

**Recommendation: do NOT promote.** The arm fails **both** legs of its own pre-registered §3.2 bar —
leg (ii) in 3 of 4 years, leg (i) in 4 of 4 — and it degrades the object it was built to improve.
It is a **successful diagnostic**: it closes nyiso-99's caveat, which was the point.

**But that recommendation is mine, and the decision is the owner's** — rule 31 exists precisely
because a session's "not a keeper in my judgement" is not a licence to act. So, stated plainly:

* The bundle `results/calibration/nyiso228_seamr_span` is **committed to this branch** (slim set) and
  is **also on local disk in full**, including the heavy `dispatch/`, `floors/`, `unit_hourly` and
  `network` intermediates that are **not** committed.
* **This container is ephemeral. The uncommitted intermediates will NOT survive it.** If the owner
  wants a unit-level look at why `r` falls, that must be said before this session ends; otherwise
  reproducing it costs **~16 min of LP** (247 s + 721 s).
* **Nothing has been deleted** (rule 31). No registration, no dashboard write, no matrix edit — all
  the parent's (rule 32(d)).

---

## 8. STATUS

**Status: 1** — solved, committed and **pushed** to `claude/nyiso228-seamr-span`.

All four years solved into ONE bundle on ONE recipe with ONE flag moved. Screen gates cleared;
full-span promotion bar failed on both legs; the caveat that motivated the arm is falsified against
it. Every number this shard will ever cite is in this document.
