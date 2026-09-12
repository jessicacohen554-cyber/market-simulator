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

## 4. STATUS

**HEARTBEAT COMMIT — proof of life before the first LP.** Hard stops cleared, prep complete,
baseline captured. The 2023 SCREEN solve is next; §5–§8 (gate table, per-year numbers) are appended
in the following commits.

Status: **2** (in progress — screen solve not yet launched).
