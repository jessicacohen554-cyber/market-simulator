# SHARDREPORT — nyiso-228 SHARD A (TAIL)

**Session:** nyiso-228 · **Shard:** A (TAIL) · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/nyiso228-tail-span` · **Bundle:** `results/calibration/nyiso228_tail_span`
**Charter:** `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` §3.1 (authorized channel), §4 (STOP gates)
**Arm variable:** `offer_curve_by_group[*].peak` **×1.50**, frozen ex ante, one config all years, never swept.

> Status of this revision: **HEARTBEAT** — hard stops cleared, container prep logged, no LP started yet.

---

## 1. HARD STOPS

| # | stop | required | observed | verdict |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | **PASS** |
| 1b | no rebase / pull / sync | — | none performed; branch `claude/nyiso228-tail-span` at pinned SHA | **PASS** |
| 2 | `results/calibration/nyiso228_peak_x150.json` exists, exactly 10 classes, each exactly one key `peak` | 10 / 1 | 10 classes, every one carrying exactly `{"peak": …}` | **PASS** |
| 3 | config signature in the written `run_config.json` | see below | evaluated after the screen solve writes it | pending |
| 4 | factor frozen at ×1.50, no re-cut / sweep | — | acknowledged; a second value would be a shard FAILURE | **held** |

### 1.2 — the ×1.50 file as read from disk

```
CC_CHP 3.375 · CC_REGULAR 3.375 · COAL 2.175 · COAL_BIT 2.175 · COAL_LIGNITE 2.325
COAL_PRB 2.22 · COAL_WC 1.8 · CT_CHP 1.5 · CT_PEAKER 6.0 · ST_GAS 6.3
```
n_classes 10 · n_bands 10 · every entry a `peak` and nothing else.

### 1.3 — zero-LP precondition for HARD STOP 3

Base bundle `nyiso223_gapfill_span` vs keeper `nyiso_fuelvintage_A`, `offer_curve_by_group`:
**byte-identical** on the three signature classes, so the ×1.50 file lands on the keeper's own values.

| class | base/keeper `peak` | ×1.50 expected | required by HARD STOP 3 |
|---|---|---|---|
| `CT_PEAKER` | 4.0 | 6.0 | 6.0 ✓ |
| `ST_GAS` | 4.2 | 6.3 | 6.3 ✓ |
| `CC_REGULAR` | 2.25 | 3.375 | 3.375 ✓ |
| `CT_PEAKER.committed` | 1.35 | **untouched** 1.35 | 1.35 ✓ |
| `ST_GAS.committed` | 1.05 | **untouched** 1.05 | 1.05 ✓ |

`nyiso_import_reconciliation` is `True` in both base and keeper and this arm does not touch it.
`nyiso_hub_gap_month_level` is `True` in the gapfill base and is disarmed to `false` by `--set`,
which returns the recipe to the keeper exactly (PRECOMMIT §3).

---

## 2. CONTAINER PREP LOG

| step | result |
|---|---|
| `hydrate_data.py --profile nyiso` | no-op — **this is a FULL clone**, every blob already local |
| `prepare_solve_container.py` | 8 GiB swap added at `/swapfile-marketsim`; RAM 15.7 + swap 8.0 = **23.7 GiB**; 16.9 GiB free disk, 4 cpus |
| `--emit-exports` | `MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` exported into every solve shell |
| pip pins | PyYAML, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, openpyxl, tzdata — all exit 0 |
| `regenerate_clean.py` | see §2.1 |
| `curate_lmp.py` | **NOT run** (charter: known pre-existing `KeyError: 'MGHG'`, out of scope) |

### 2.1 — `regenerate_clean.py` notes

* `chp-btm-price` is **not** a datatype in `regenerate_clean.py --list`; dropped per charter
  ("if a datatype name is not in `--list`, drop it and continue — do not fix the script").
  The 26 remaining names all resolve.
* First invocation failed 20/27 with `ModuleNotFoundError: No module named 'market_sim'` —
  `PYTHONPATH=.` as a command prefix does not reach the curate subprocesses `regenerate_clean.py`
  spawns, and `market_sim` lives under `src/`. Repaired **by environment only**, not by editing the
  script (forbidden): `export PYTHONPATH="$PWD:$PWD/src"`.

---

## 3. GATE TABLE (PRECOMMIT §4)

Pending the screen solve on **2025**.

## 4. SOLVE LOG

Pending.
