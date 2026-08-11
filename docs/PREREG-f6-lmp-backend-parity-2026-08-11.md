# PREREG — F6-DIAG: the neighbour-LMP backend parity defect

**Lane:** F6-DIAG (diagnosis only). **Date:** 2026-08-11. **Branch:**
`claude/f6-lmp-backend-parity-1rc197` off `origin/main` @ `3ae7465`.

**This lane changes no production behaviour.** No tolerance edit, no backend switch, no
data-regeneration commit, no mechanism, no solve. Rule 12 and rule 22 do not bind because
nothing is solved. Rule 28 imposes no matrix row because no mechanism is added.

This file is committed **before** any measurement is taken. Predictions below are recorded
so the measurement can refute them. A refuted prediction is a successful outcome and will be
reported at full magnitude.

---

## 0. The object

`tests/curation/test_consume_lmp.py::test_clean_backed_lmp_matches_raw_loader` asserts that
the two `neighbor_lmp_hourly` backends agree within `_TOL = 1e-2` on PJM 2024 RTM:

* **raw backend** — `_neighbor_lmp_raw` reads
  `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`, built by
  `scripts/data/derive_actual_lmp.py::_hub_mean_hourly`.
* **clean backend** — `_neighbor_lmp_clean` reads the curated
  `data/clean` `lmp` partition (PJM/RTM/2024), built by `scripts/data/curate_lmp.py`,
  and reduces it to a hub mean on the 8760 calendar via `neighbor_price._hour_of_year`.

FFR-4F §6 F-6 reports the test FAILS at `max abs(raw-clean) = 408.704`. The line-35
docstring claims "float32 storage in the realized product is the only source of
disagreement".

## 1. Prerequisites (recorded, so the measurement is reproducible)

1. `uv sync` — completed, exit 0.
2. `python scripts/regenerate_clean.py lmp` — the `lmp` datatype only, not the full tree.
   **Scoping note:** the full regeneration is ~63–65 min across ~50 datatypes; this lane
   reads exactly one (`lmp`), and `regenerate_clean.py`'s datatypes are independent
   (each `curate_*.py` owns its own raw inputs and clean outputs). Building only `lmp`
   changes nothing measured here. `data/clean` and `results/` are gitignored and die with
   the container.

## 2. Pre-registered predictions

Stated before running anything, from reading the two producers and the two consumers.

**P1 (mechanism).** The two backends index the 8760 calendar on **different clocks**:

* raw — `derive_actual_lmp._std_hour_index` converts `datetime_beginning_utc` to the ISO's
  **fixed standard-time** zone (`_STD_TZ["PJM"] = "Etc/GMT+5"`, EST) and maps
  (month, day, hour) onto the non-leap 8760 calendar.
* clean — `neighbor_price._hour_of_year` maps `interval_start_local`, which
  `curate_lmp.parse_pjm_file` populates from `datetime_beginning_ept`, the **prevailing
  (DST-following)** Eastern wall clock.

During DST (2024: 10 Mar 03:00 EDT → 3 Nov 02:00 EST) EDT = EST + 1 h, so the clean series
is expected to sit **one index later** than raw: `clean[k] ≈ raw[k-1]`.

**P2 (shape).** R3 category **(b) timestamp alignment**, not (a) outliers, not (c)
units/sign, not (d) a float32 precision story the tolerance mis-sizes. Specifically:

* hours 0 … the 10-Mar-2024 02:00 EST slot: the two agree to float32 (~1e-3 or better);
* that one slot: empty in the prevailing clock (the spring-forward hour does not exist as a
  wall-clock label), so `_fill_hourly` interpolates it;
* 10 Mar → 3 Nov: offset by exactly one slot;
* the 3-Nov 01:00 slot: the prevailing clock collapses the fall-back hour's **two** real
  instances into one `_hoy`, so the clean value is their mean where raw keeps them in two
  distinct slots;
* 3 Nov → 31 Dec: agree again.

**P3 (magnitude).** `max |raw − clean|` is the largest hour-to-hour jump of the PJM 2024 RT
hub-mean series inside the DST window, not a float32 artifact. Hours exceeding `1e-2`:
predicted **> 5,000** (essentially every DST hour whose neighbour differs by more than a
cent), not a handful.

**P4 (which backend is wrong — R2).** Predicted verdict: **raw is right, the clean-backed
*read path* is wrong** — and the defect is in the **consumer reduction**, not in the curated
data product. The clean `lmp` partition carries `interval_start_utc` as the authoritative
column (`curate_lmp` docstring, "Timezone & partitioning conventions"); `_neighbor_lmp_clean`
simply reads the wrong one of the two timestamp columns. This will be tested against the
first-party source (`data/raw/lmp-data/PJM_2024_rt_da_monthly_lmps.csv`) directly, not by
assuming either derived product is correct.

**P5 (blast radius — R4).** The clean backend is env-gated `MARKET_SIM_USE_CLEAN`, default
OFF. `neighbor_lmp_hourly` *is* reachable from a production LP path
(`src/market_sim/model/interchange/nyiso.py`), so the raw side is load-bearing; the clean
side is predicted unreachable in every keeper and registered forecast run. **If any keeper
sets the flag, this lane stops and says so loudly before drawing any conclusion about that
keeper.**

**P6 (invisibility — R5).** Two independent reasons the test never fires in CI:
(i) it is marked `slow` + `integration` and CI's only general pytest tier runs
`-m "not slow and not integration and not fulldata"`; (ii) `_clean_available()` skips it
wherever `data/clean` was not built, and no CI job builds `data/clean`. Both to be
confirmed by reading `.github/workflows/ci.yml` in full.

## 3. What will be measured (R1–R5), and how

| Read | Measurement | Instrument |
|---|---|---|
| **R1 REPRODUCE** | exact `max abs(raw−clean)`, its hour index, the ISO/year/market, and the count of hours with `abs diff > 1e-2` | run the test; then recompute both arrays directly |
| **R2 WHICH IS WRONG** | for the ~10 worst hours, the published PJM value at that timestamp from `data/raw/lmp-data/PJM_2024_rt_da_monthly_lmps.csv`, compared against **both** backends | independent third-party reduction written in the probe, reading the raw CSV only |
| **R3 SHAPE** | per-segment agreement (pre-DST / DST / post-DST), the lag-1 cross-correlation inside the DST window, the spring-forward and fall-back slots | probe |
| **R4 BLAST RADIUS** | every consumer of `neighbor_lmp_hourly` and of `MARKET_SIM_USE_CLEAN`; whether any keeper `run_config.json` or registered forecast run sets the flag | grep + keeper shard / registry scan |
| **R5 INVISIBILITY** | marker exclusion + skip guard, and the age of the test | `.github/workflows/ci.yml`, `git log` |

Scope sweep for R2/R3: the same clock comparison is run for **every ISO/year the clean tree
carries**, to establish whether the defect is PJM-specific or shared curation infrastructure.
**Rule 25: no verdict is transferred between ISOs** — each ISO's number is reported as its
own.

## 4. Falsifiers

The predictions above are wrong if any of the following is measured:

* the diff is concentrated in a handful of hours with no DST structure → P1/P2 refuted, the
  shape is (a) and a different root cause is in play;
* `clean[k] ≈ raw[k-1]` does **not** hold across the DST window → P1 refuted;
* the raw product disagrees with the published PJM CSV at the worst hours while clean agrees
  → P4 refuted, verdict flips to "clean is right / raw is wrong";
* both disagree with the published CSV → P4 refuted, verdict is "both wrong";
* the max diff is O(1e-2)–O(1e-1) and traceable to float32 → P3 refuted, the docstring is
  substantially right and only the tolerance is mis-sized;
* any keeper or registered forecast run sets `MARKET_SIM_USE_CLEAN` → P5 refuted,
  **stop-the-line**.

## 5. Deliverable

`docs/FINDING-f6-lmp-backend-parity-2026-08-11.md` — the five reads at full magnitude, the
named R2 verdict, and a card-ready recommendation with the real cost of each option. The
fix is **not** implemented in this lane.
