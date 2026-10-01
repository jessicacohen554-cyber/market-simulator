# FINDING nyiso-139 — the NYISO RTD interval-convention repair is LANDED. The archive is re-staged, the parquet re-derived on FULL coverage, and the keeper's determination is UNCHANGED.

**Session nyiso-139, 2026-08-16.** Owner decisions this session, via
`AskUserQuestion` on `docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md`:
**D1 GRANT** (joint Zone-K charter, write + prereg + solve), **D2 ADOPT AS
REQUESTED** (C3c reporting condition), **D3 = option (b)** — *"re-stage the
NYISO RT archive, repair first, then charter"*. This finding is the **repair**,
i.e. the first half of D3(b). No LP was solved, no year scored against model
output, and no run registered.

The repair discharges, in full, the three actions the standing NYISO-RTD-CLOCK
disclosure requested (`docs/handoffs/d32-f6fix-2026-08-13.md` §A.6 items 1-3).

---

## 1. WHAT WAS WRONG, AND WHY IT IS NOT A JUDGEMENT CALL

`scripts/data/derive_actual_lmp.py::_nyiso_wide` binned NYISO's 5-minute RT
(P-24A) zonal LBMP by plain `.floor("h")` — i.e. it read the `Time Stamp`
column as interval-**beginning**. `scripts/data/curate_lmp.py::parse_nyiso_zip`
reads the same column as interval-**ending**. Exactly one is right.

**It is adjudicated, not assumed.** NYISO publishes a second product off the
same 5-minute prices — P-4A, the *Time-Weighted / Integrated* hourly zonal LBMP
— and states in prose that it is built from them (Manual 12 p. 136; Manual 14
§4). P-4A is therefore NYISO's own published answer to "which 5-minute stamps
belong to which hour". Re-run this session
(`scripts/probes/nyiso_rtd_clock_adjudication.py --strict 202406 202312`),
restricted to zone-hours holding exactly twelve 300-second intervals, where the
Manual-14 duration weighting collapses to a plain mean and the hour assignment
is the only remaining free choice:

| convention | zone-hours | mean \|Δ\| | max \|Δ\| | n > rounding |
|---|---:|---:|---:|---:|
| BEGINNING | 14,828 | $0.476037 | **$50.0058** | **14,174** |
| **ENDING** | **14,905** | **$0.002512** | **$0.0050** | **0** |

P-4A carries two decimals, so max \|Δ\| = 0.0050 **is exact agreement**. ENDING
is exact on every one of 14,905 zone-hours; BEGINNING is wrong on 14,174 of
14,828.

**An independent corroboration found this session, from the archive's own
shape.** The monthly RT zips run from `00:05:00` on day 1 of the month to
`00:00:00` on day 1 of the *next* month (verified on 202601 and 202606) — i.e.
each file contains exactly the intervals *ending* within its month. The
publication boundary is itself in the ending convention, which no reading of the
prices was needed to see.

This is rule 14 `[R-ACCURATE]`: an accurate-vs-estimate swap on a measured
input. Per that rule a worse fit afterwards would have been a discovered bug,
not grounds to keep the mis-binned series. (In the event the fit does not
meaningfully move — §4.)

## 2. THE DATA BLOCK IS CLEARED — the archive is fully re-staged

The blocker recorded by nyiso-137 §7.5 and by decision-card option **(c)** was
that only **21** monthly RT zips were staged against a 2018-2026 series, so a
re-derivation would have been on **partial coverage**, which the standing
disclosure forbids. Option (b) was to re-stage. That is done.

New `scripts/data/fetch_nyiso_zonal_lmp.py` (idempotent, resumable, validates
each download as a readable zip before it replaces a target):

| product | months needed | staged before | fetched | staged after |
|---|---:|---:|---:|---:|
| DA `damlbmp_zone` | 102 | **0** | 102 | **102 / 102** |
| RT `realtime_zone` | 102 | 21 | 81 | **102 / 102** |

Zero failures. The **DA outer container `NYISO_zonal_hourly.zip` did not exist
at all** on a fresh clone (it is gitignored as regenerable, `.gitignore:151`),
so the DA half of the parquet had no source; it is rebuilt (12.1 MB, 102
months). The **21 already-committed RT zips were skipped, not re-downloaded**,
so their committed bytes — including the twelve 2022 rule-22 intake months —
are untouched; `git status` reports no modification to any tracked source zip.

Coverage is now **total across the parquet's committed span**, so this is
option **(b)**, not the forbidden **(c)**.

**Holdout position.** This is data intake, which the freeze file itself lists
under `not_frozen` (`"data intake (no-LP, rule 22 channel 1)"`), and which rule
22 as amended 2026-08-06 requires be *"collected once and applied CONSISTENTLY
ACROSS ALL YEARS"* — the spend being *looking at the answer*, never the data. No
model output was scored against any out-of-training year, and none was solved or
registered. The 2026 window was deliberately **not** extended past June even
though `mis.nyiso.com` now serves 2026-07: this change moves the **clock**, not
the **span**.

## 3. THE REPAIR

One behavioural change, in `_nyiso_wide`, scoped to RT:

```python
shift = pd.Timedelta(0) if kind == "da" else pd.Timedelta(seconds=1)
df = df.assign(ts=(pd.DatetimeIndex(utc) - shift).floor("h"))
```

The subtraction is done **in UTC**, after `_localize_ordered`, so the fall-back
hour's order-based disambiguation is untouched and the arithmetic crosses no DST
discontinuity. The **DA branch is deliberately exempt**: `damlbmp` is hourly and
interval-beginning, so the same shift would have moved every DA hour by one.

**That exemption is verified, not asserted: the `da` column changed in ZERO
hours in every one of the nine years.** This confirms disclosure §A.6 item 3 —
the DA block, and therefore the `spec.py` import ladder derived from it
(`derive_nyiso_import_tranches.py:169`), is untouched and **no re-derivation of
the import tranches is implied**. The NEISO proxy artifact
(`build_nyiso_proxy_lmp_neiso.py`) also reads `damlbmp` only, so no cross-ISO
artifact goes stale (rule 25 `[R-ISO-SCOPE]`).

## 4. MEASURED EFFECT ON THE SCORED SERIES

Re-derived across the full span, `--isos NYISO --parquet-only`. Shape is
unchanged at 78,840 rows / 9 years.

| year | hours moved >$0.01 | mean \|Δ\| | max \|Δ\| | Δ annual mean RT | Δ `da` hours |
|---|---:|---:|---:|---:|---:|
| 2018 | 8,386 | $1.379 | 125.33 | −0.002 % | 0 |
| 2019 | 8,271 | $0.704 | 80.46 | −0.016 % | 0 |
| 2020 | 8,212 | $0.480 | 73.05 | −0.016 % | 0 |
| 2021 | 8,459 | $0.941 | 69.34 | −0.017 % | 0 |
| 2022 | 8,570 | $1.979 | 257.21 | −0.032 % | 0 |
| **2023** | 8,306 | $0.658 | 69.08 | **−0.005 %** | 0 |
| **2024** | 8,317 | $0.635 | 72.43 | **−0.012 %** | 0 |
| **2025** | 8,484 | $1.161 | 92.16 | **−0.015 %** | 0 |
| 2026 (H1) | 4,194 | $1.507 | 161.58 | −0.012 % | 0 |

**Almost every hour moves; the level does not.** This reproduces nyiso-137 §3
(−0.0353 % pooled on its 6,018-hour staged sample) on the full population, and
it is why C3a — band ±10 %, nearest margin 1.2 pp — cannot be moved by this
defect in either direction.

**One hour changed coverage**: 2026 hour 4343, the last hour of the H1 window,
is now null. Under the ending convention that hour is priced by the intervals
stamped `23:05`…`24:00`, and its final stamp lives in the July file that the
H1-limited staging deliberately does not hold. It is an out-of-training,
frozen-year boundary artifact of the preserved span, not a data loss.

## 5. THE C3c DENOMINATOR — what actually moved

`frontend/data/backcast/tail/actual_tail.json`, re-derived
(`scripts/data/derive_actual_tail.py`). **Only two values in the entire
file changed, and both are NYISO** — every other ISO's block is byte-identical
(rule 25):

| year | `rt_gt` before | after | tier |
|---|---:|---:|---|
| 2020 | 1 | 1 | validation (unchanged) |
| 2021 | 3 | 3 | validation (unchanged) |
| 2022 | 97 | **101** | validation — **input-side only; see below** |
| **2023** | 10 | **10** | training — **unchanged** |
| **2024** | 12 | **13** | training — **+1** |
| **2025** | 42 | **42** | training — **unchanged** |

Every outcome falls inside the reachable interval nyiso-137 §5 computed ex ante
from the tail region's own measured movement — 2023 [5, 21], 2024 [10, 21], 2025
[34, 82]. The two verdict-flip edges that finding flagged **did not fire**: 2023
did not reach the 11 h that would have vacated its caveat, and 2025 did not
reach the 49 h that would have broken its PASS.

nyiso-137 §4's correction of the original adjudication stands and is now
demonstrated on the product: the claim that *"the C3c tail region moves by
cents"* is false — the tail moved enough to add an hour to 2024. The level
claim in the same passage is the half that reproduces.

**On the 2022 row.** It is recomputed because rule 22's amendment requires a
measured input be applied consistently to every year — leaving 2022's actual
count on a clock now known to be wrong, while 2023-2025 use the repaired one, is
precisely the inconsistency that amendment forbids, and it would have surfaced
as a surprise the moment the touchpoint was authorized. It is an **input-side
count derived from measured prices with no model involved**; no 2022 model
output was scored, and the year remains frozen for solve / score / registration.
The gate that permitted it is the script's own fail-closed tier check
(`scripts/lib/holdout_policy`), which NYISO clears on its `complete` marker.

## 6. THE KEEPER IS UNCHANGED

`scripts/calibration_verdict.py --run-id 2026-08-08-nyiso-133-cod-arm`, from
committed artifacts, **no solve**:

**`CALIBRATED-WITH-CAVEATS`** — unchanged. C1 / C2 / C3a / C3b / C4 / C6 / C8 all
PASS; **C3c remains the lone ledgered caveat, budget 1 of 1**. The only movement
anywhere in the verdict is 2024's C3c magnitude, `0.25× (12 h)` → `0.23× (13 h)`
— the same FAIL, the same caveat, the same determination.

Downstream artifacts refreshed so the committed set is self-consistent:

* `actual_lmp.json` — load-weighted fields via the documented `--lw-retrofit`
  path (`rt_lw` pairs each hour's price with that hour's demand, so unlike the
  raw means it *is* clock-sensitive). NYISO only; **`da_lw` / `da_lw_mon`
  unchanged**, consistent with §3. In-training annual movement: 2023 unchanged
  at 32.25, 2024 38.13 → 38.12, 2025 66.45 → 66.43 — ≤ 0.03 %, three orders
  below C3a's margin.
* `bench/NYISO/{2023,2024,2025}.json.gz` — the `avgLMP` block carries a copy of
  those fields and is what C3a/C3b actually read; retrofitted surgically
  (`retrofit_lw_price_bench.py --isos NYISO`) and verified equal to the
  reference.
* `status/NYISO.js` — rebuilt (`build_status.py --iso NYISO`); `shared.js` is
  **not** modified.

## 7. WHAT THIS DISCHARGES, AND WHAT IT DOES NOT

**Discharged.**

1. Disclosure §A.6 items 1-3 in full: the convention corrected and the parquet
   re-derived on re-staged sources (1); the keeper re-scored and its
   determination re-verified (2); the DA/import-ladder exemption confirmed
   empirically rather than by argument (3).
2. **D2's conditionality, prospectively.** D2 was adopted because C3c's
   *denominator* was untrustworthy: the arm-vs-control delta was invariant but
   absolute band membership was not. With the denominator now measured on the
   adjudicated-correct clock, **absolute C3c band membership is reliable for
   work that follows this repair** — which is exactly the ordering D3(b) bought.
   D2 still governs any C3c claim quoted from a run scored *before* it.
3. The third of the three 2022-touchpoint disclosures — the RTD-clock
   mis-binning — is now **graded for 2023-2025 (nyiso-137) and repaired for
   every year (here)**.

**NOT discharged, and still open.**

* The **holdout spend freeze is ACTIVE** and untouched. 2022 remains unspendable
  for solve/score/registration; `final` is still empty for NYISO.
* The other two 2022-touchpoint disclosures — import-tranche 719 MW duration
  RMSE, and the Transco Dec-2022 Elliott hole — remain **ungraded**.
* The `iso-model-unification-plan.md` §3 migration caveat, which §A.7 said
  *"stands until that repair lands"*, is now satisfiable; it is flagged here
  rather than edited, since it is not this lane's document.
* **The chartered joint Zone-K lever (D1) is not yet written.** D3(b) put the
  repair first; that is what this finding is.

## 8. FILES

Changed: `scripts/data/derive_actual_lmp.py` (the repair),
`data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`,
`data/raw/_validation-source/actual_lmp.json` (NYISO `rt_lw*` only),
`frontend/data/backcast/tail/actual_tail.json` (2 NYISO values),
`frontend/data/backcast/bench/NYISO/{2023,2024,2025}.json.gz`,
`frontend/data/backcast/status/NYISO.js`.
Added: `scripts/data/fetch_nyiso_zonal_lmp.py`.
The 183 fetched monthly zips and the DA container are gitignored by design
(regenerable; the committed parquet is the durable record).
