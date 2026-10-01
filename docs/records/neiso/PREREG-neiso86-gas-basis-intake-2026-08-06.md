# PREREG — neiso-86: NEISO gas-basis intake, repairing the inverted pre-2023 hub basis

**Session:** neiso-86, 2026-08-06
**Type:** DATA INTAKE (rule 22 channel 1). **NO LP. NO SOLVE. NOTHING SCORED OR REGISTERED.**
**Status of this document:** written and committed **BEFORE** any data byte is edited. The gates
below are pre-registered, not chosen after seeing the corrected numbers.
**Keeper:** UNCHANGED (`2026-08-05-neiso-83-ca1-reclass`).
**Mechanism cells:** UNCHANGED. No mechanism is tested, proposed, or armed (rule 28(d)).
**New DOF:** ZERO. No `ScenarioConfig` field is added or changed.

---

## 1. The object

`data/raw/gas_basis_by_iso_month.csv` sources NEISO's `basis_usd_mmbtu` from the **EIA `N3050MA3`
proxy** for 2015–2022 and 2026, and from the **measured ISO-NE Massachusetts gas index** for
2023–2025. `N3050MA3` is an LDC city-gate **purchase-portfolio average**: New England LDC summer
throughput collapses, fixed pipeline reservation charges spread over a small volume, and the average
$/Mcf balloons. Subtract Henry Hub and the resulting "basis" is **seasonally inverted** relative to
the *marginal* Algonquin basis a gas unit's offer actually tracks.

Measured `winter(Jan,Feb,Dec) − summer(Jun,Jul,Aug)` basis, NEISO:

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|
| −0.58 | −2.29 | −4.37 | −4.79 | −6.71 | −7.18 | −8.56 | −7.84 | **+2.83** | **+4.54** | **+10.97** |

The proxy years are inverted; the measured years are correct. Full diagnosis:
`results/calibration/FINDING-neiso85-2022-seasonal-inversion-2026-08-05.md`.

This is rule 14 `[R-ACCURATE]`'s misalignment clause exactly — **a real measured series used on the
wrong boundary**. The remedy is a correctly-bounded measured series, not a model parameter. The repo
has already adjudicated this failure mode twice: the `NEISO,2025,8` row's own `source` field records
the proxy being **rejected** for that month, and CAISO retired the same EIA N3050 family on a
different leg at caiso-84 (`caiso_citygate_spot_level`).

## 2. Scope — exactly what changes

**Two files, both under `data/raw/`.**

1. `data/raw/gas_basis_by_iso_month.csv` — NEISO rows only, for the authorized years, replacing the
   `EIA N3050MA3` proxy with the measured ISO-NE MA gas index, `basis = MA index − Henry Hub monthly
   mean`, one cited source URL per row (matching the 2023–2025 provenance style).
2. `data/raw/gas-prices/algonquin_citygate_daily.csv` — extended to the same years via the existing
   committed scraper `scripts/data/fetch_algonquin_daily_spot.py --merge`, whose `--merge` mode
   seeds from the committed CSV, adds only newly scraped dates, and **asserts every pre-existing row
   survives byte-identical**.

**Nothing else.** No source file under `src/market_sim/`, no `ScenarioConfig` field, no mechanism, no
cell verdict, no keeper, no dashboard registration.

### 2.1 The transformation, verified against a committed row before adoption

The stored quantity is `basis = (ISO-NE MA gas index) − (Henry Hub monthly mean)`. Verified against
an existing committed row and **its own cited source URL**, not assumed:

| check | value |
|---|---|
| Jan-2023 ISO-NE recap, "average natural gas price during January" | **$4.73/MMBtu** |
| Henry Hub Jan-2023 monthly mean, `data/raw/gas-prices/henry_hub_monthly.csv` | **3.273** |
| implied basis | **1.457 → 1.46** |
| committed `NEISO,2023,1,…,1.46` | **match** |

The index is defined in the recaps as "a volume-weighted average of trades at four natural gas
delivery points in Massachusetts, including two Algonquin points, the Tennessee Gas Pipeline, and
the Dracut Interconnect" — identical wording and units ($/MMBtu, monthly) in the 2018, 2020 and 2022
posts as in the 2023–2025 posts. **Same quantity, same boundary, same convention.**

## 3. Owner authorization (rule 22 channel 1)

Requested and granted in-session, 2026-08-06, naming the exact years:

- **Authorized window: NEISO 2018, 2019, 2020, 2021, 2022, 2026.**
- 2019 is the **SPENT** locked-test year. The owner authorized repairing its **DATA** with an
  explicit note. **The spent one-shot is NOT re-opened, NOT re-scored, and NOT re-interpreted.** It
  stands exactly as scored, on the proxy input it consumed.
- **2015–2017 are NOT authorized and are NOT touched.** They remain on the defective proxy. This is
  a declared, deliberate residual, recorded in §6.

The **holdout spend freeze** (`frontend/data/backcast/holdout-freeze.json`) is ACTIVE and is
respected in full. It freezes SOLVE / SCORE / REGISTRATION; it does **not** freeze data intake
(its own `scope.not_frozen` says so, as does rule 22 channel 1). **No year is solved, scored or
registered in this session** — before or after the intake. A corrected 2022 re-solve requires a
separate owner lift and is **not requested here**.

## 4. Pre-registered no-LP gates

All five are evaluated from committed artifacts and pure data inspection. **No dispatch solve is
run to evaluate any of them.** Evaluability scope is fixed *here*, in advance, so a gate cannot be
quietly declared N/A after the fact.

### V1 — SEASONALITY SIGN
Every corrected NEISO year must satisfy `winter(Jan,Feb,Dec) − summer(Jun,Jul,Aug) > 0`, matching
the measured years (+2.83 / +4.54 / +10.97) and reversing the proxy years (−0.58 … −8.56).

- **Evaluable:** 2018, 2019, 2020, 2021, 2022 (complete years).
- **NOT evaluable: 2026** — the ISO-NE recaps are published only through **May 2026** (June not yet
  posted, verified 2026-08-06), so no Jun/Jul/Aug exists. Declared in advance, not discovered later.
- **Substitute for 2026 (V1b):** the winter months present must exceed the shoulder months present,
  `mean(Jan,Feb) > mean(Apr,May)`. This is a weaker check and is reported as such; it is **not**
  presented as V1 having passed.

### V2 — IN-SAMPLE INVARIANCE  *(the gate that protects the keeper)*
NEISO's **2023, 2024, 2025** rows must be **byte-identical** before and after, and so must every
pre-existing row of `algonquin_citygate_daily.csv`. Verified by direct byte comparison against
`git show HEAD:<path>`, not by eyeballing values. Any movement is a stop-the-line event.

### V3 — LEVEL PLAUSIBILITY against an independent measured series
The corrected hub-month level (`HH month + corrected basis`) must **not sit below** the measured
EIA-923 ISO-month delivered gas cost in **Jan, Feb, Dec** — the months where the pipeline-constrained
hub is by construction the dearer *marginal* source relative to a contract-laden plant-average
delivered receipt.

- **Evaluable:** 2018, 2019, 2020, 2021, 2022 — EIA-923 has **12/12 reporting months** in each
  (verified 2026-08-06 via `iso_monthly_gas_prices`).
- **NOT evaluable: 2026** — no EIA-923 receipts exist for 2026. Declared in advance.
- 2022 reference values: Jan **16.27**, Feb **14.60**, Dec **15.38**.
- **A V3 miss is reported as a FAIL, not silently reconciled.** V3 is a falsification check on the
  intaken series, so no adjustment, shift or blend may be applied to make it pass — that would be
  precisely the fitted correction this lane exists to avoid.

### V4 — NO RESIDUAL FITTING
The intake commits cite the **data change only** (rule 23 `[R-FROZEN-DERIVE]`). No commit message,
and no field of the corrected rows, may reference a price residual, MAE, gate score, or the
neiso-85 attribution figures (77.3 %, corr 0.978, +14.7 %, +23.1 %) as a target. **Source selection
is decided by boundary correctness alone** — the ISO-NE MA index is chosen because it is the
marginal hub the offer tracks, and that choice was fixed in §2.1 before any corrected value was
computed. If a choice between candidate sources ever turns on which improves a score, the correct
action is to STOP.

### V5 — CROSS-ISO NON-INTERFERENCE
No non-NEISO row changes, byte-for-byte: CAISO, ERCOT, MISO, NYISO, PJM, SPP. In particular **CAISO
is left alone** — it arms the same overlay and is 100 % proxy in all years including its tuned
window, which is flagged for the CAISO lane under rule 25 `[R-ISO-SCOPE]` and is not this session's
to fix. Verified by byte comparison of every non-NEISO row against `git show HEAD:`.

## 5. Baseline reproduced before the change (rule 22 discipline)

Both neiso-85 probes were re-run **before** any edit and reproduce the committed baseline, emitting
artifacts **byte-identical** to the committed ones (`git diff` empty on
`results/calibration/_neiso85_gas_chain.json` and `_neiso85_attribution.json`):

- 2022 resolved gas winter/summer = **0.397** (INVERTED); 2023/2024/2025 = 2.390 / 3.778 / 4.608.
- Stage-4 hub overlay 2022: Jan **6.738**, Aug **19.199**; overlay covers **8760/8760 hours**.
- EIA-923 stage 2022: Jan **16.270**, Feb **14.604**, Dec **15.376**.
- Oil transposition Jun–Sep **2.2983 TWh** vs Jan/Feb/Dec **0.0012 TWh**.

Neither probe builds an LP.

## 6. Declared residuals — stated in advance, not discovered later

1. **2015–2017 remain on the defective proxy** (not authorized). Any future use of those years must
   treat their NEISO basis as known-inverted.
2. **2026 is partial**: Jan–May only, and both V1 and V3 are **not evaluable** there (§4). June-2026
   onward has no published recap as of 2026-08-06.
3. **The 2019 spent locked-test one-shot was scored on the proxy input.** After this intake the
   committed input no longer byte-matches what that one-shot consumed. The one-shot **stands as
   scored** and is not re-opened; this note is the load-bearing record of that discontinuity.
4. **If the Algonquin daily extension proves unobtainable for any authorized year**, the residual
   monthly-plateau parity gap is declared explicitly in the FINDING and in
   `calibration-complete.json` — never left silent. (The daily leg is what the overlay docstring
   says "trips the dual-fuel switch"; without it a covered month keeps the flat monthly plateau.
   For 2022 specifically the daily leg currently falls through to the **Transco Z6 NY shape borrow**,
   so the pre-intake state is an inverted level *and* a borrowed within-month shape.)

## 7. What this session explicitly will NOT do

- No solve, score or registration of **any** year, in or out of training. No LP is constructed.
- No re-opening, re-scoring or re-interpretation of the SPENT 2019 / H1-2026 locked-test one-shot.
- No request for a freeze lift.
- No `ScenarioConfig` field, no mechanism armed, no cell verdict moved.
- No edit to NEISO 2023–2025 basis rows (V2).
- No edit to any other ISO's rows (V5).
- No tuning of anything against the 2022 residual, and no quotation of 2022 figures as a skill
  number. 2022 is **iterable validation evidence** (rule 22).
