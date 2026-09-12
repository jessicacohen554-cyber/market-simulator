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

## 6. STATUS

Screen **PASSED both STOP gates**; the remaining three years (2022, 2024, 2025) are authorized and
are being solved into the **same** bundle. §7–§8 (per-year footprint, prices, classes, reserves for
all four years) follow in the next commit.

Status: **2** (screen committed and pushed; full span in flight).
