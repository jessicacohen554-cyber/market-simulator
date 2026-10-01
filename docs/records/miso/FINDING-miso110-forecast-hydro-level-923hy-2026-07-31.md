# FINDING (miso-110): the FORECAST hydro level at a PS-folding BA now comes from
# EIA-923 `HY` too — the forward half of the miso-109 fix, closed with NO solve

**Session:** miso-110 (the miso-109 §7(e) hand-back)
**Date:** 2026-07-31
**Verdict:** FORWARD LEVEL FIX **landed** (rule 14 `[R-ACCURATE]`).
`hydro_level_923_hy` goes **`mode: "B"` → `"BF"`**; MISO stays **`O`** in both
lanes. **No LP was solved** — the level is a 12-vector, so every claim below is
assertable directly, and nothing in the repo needed re-solving.
**Rule 25:** registry-scoped to MISO; PJM enters when its own session lists it.
**Runs:** none, and none was warranted — see §6.

---

## 1. The defect, and why miso-109 left it open

miso-109 established that MISO files **no EIA-930 `NG: PS` column**, so its
`NG: WAT` is a conventional-hydro **plus pumped-storage-discharge** series,
while the LP's hydro units are EIA-923 prime mover `HY` alone. It refused the
`NG: WAT` **backcast** level pin for any BA in
`constants.EIA930_PS_FOLDED_INTO_WAT`.

It deliberately did **not** fix the forward analogue, and said so. The forecast
level is built by `hydro.forecast_monthly_hydro` →
`eia930.climatological_monthly_hydro`, which is the **mean of that same
`NG: WAT` series** over `constants.HYDRO_CLIMATOLOGY_YEARS`. Averaging
contaminated years yields a contaminated climatology: the forward level carried
pumped-storage discharge exactly as the backcast level had. `build_hydro_fleet`
emitted a **WARNING** on that path — loud rather than silently wrong, but still
wrong. This session replaces the warning with a correct level.

## 2. The fix

A BA in the registry now takes its forward level from
**`data/hydro.py::climatological_monthly_hydro_923`** — the mean of the ISO's
EIA-923 `HY` monthly totals over the same window constant. The plant population
is exactly `_load_hydro_generation`'s, i.e. the one `load_hydro_budget` already
builds the per-plant shares from, so **level and units are one population** in
the forecast lane just as they now are in the backcast lane.

Everything else is held identical on purpose: the same `(12,)` MWh contract, the
same `HYDRO_CLIMATOLOGY_YEARS` window constant, the same wet/dry `hydro_year`
lever applied afterwards, the same `monthly_target_mwh` seam into
`load_hydro_budget`. **Zero new free parameters**, and — as in miso-109 — **no
reconciliation factor** between the two series, because none is identifiable
(miso-109 §2: MISO's conventional share of `NG: WAT` drifts 0.9937 → 0.8442 over
2019–2024 and the monthly gap changes sign by month in 4 of 5 complete years).
A fitted constant would be a free parameter with no forward story
(rules 5 `[R-NO-MAGIC]` / 13 `[R-MEASURED]` / 22 `[R-DOF]`).

Rule 13 admissibility is unchanged from miso-109's argument: EIA-923 `HY`
regenerates every year and responds to hydrology, so it is the same
admissibility class the per-plant budget already relies on.

**MISO forward level: 10.244 TWh → 9.3116 TWh.**

## 3. THE TRAP — the number that must not be quoted as the inflation

The naive comparison is **930 climatology 10.244 TWh vs 923 climatology
9.3116 TWh, +10.0 %**. That is **not** the fold and is not quotable as it,
because the two sides realise **different year sets**:

| side | realised window | why |
|---|---|---|
| EIA-930 `NG: WAT` | 2021, **2023, 2024, 2025** | no usable 2022 extract |
| EIA-923 `HY` | **2021, 2022, 2023, 2024** | 2025 is an early release (14 plants vs ~163) |

So +10.0 % mixes the pumped-storage fold with a **window mismatch**, and part of
it is just hydrology. The defensible inflation numbers remain the
**coverage-gated per-year backcast** ones:

> **+13.5 % (2023)** and **+18.5 % (2024)**.

**CAISO is the control that proves the trap is real.** On the same naive
climatology comparison CAISO reads **+15.5 %** — larger than MISO's — and
**+5.1 %** window-matched. Yet CAISO screens **CLEAN** on the three-signature PS
test: **zero** nameplate-breach hours in every year, and 1–121 **negative**
`NG: WAT` hours a year, which prove pumping **is** netted into its series. A
climatology gap is therefore **never on its own evidence of a fold**. The full
six-ISO table is §5.

Consequently the code **logs the realised window** rather than assuming it
equals the constant, and both the constant's citation and the matrix row carry
this warning.

## 4. The design decisions, made and documented

**(1) Which years enter the 923 mean — option (a), intersect and log.** The
window constant stays `HYDRO_CLIMATOLOGY_YEARS`; a **coverage gate**
(`complete_923_hydro_years`) removes years whose filing is incomplete, and the
**realised** window is emitted in an INFO line. No second window constant: a
separate `HYDRO_CLIMATOLOGY_YEARS_923` would be a second thing to keep in sync
and would silently diverge, whereas a gate can only ever *remove* an
unusable year and self-heals when the 2025 final vintage lands. Realised window
for MISO today: **2021, 2022, 2023, 2024**.

The gate admits a year iff **both** hold:

* `year <= EIA923_LATEST_FINAL_VINTAGE` (2024) — vintages past the latest final
  release are monthly early releases by construction; and
* census ≥ `EIA923_COMPLETE_FILING_CENSUS_FRACTION` (**0.50**) × the ISO's modal
  census over the window — a per-ISO check that also catches a partial filing
  *inside* a nominally final vintage.

*Census bookkeeping, so this doesn't read as contradicting miso-109.* The counts
here are the **LP-visible** census — `_load_hydro_generation`'s, which drops
plants with zero annual generation — giving MISO **163 / 161 / 163 / 160** for
2021–2024 and **14** for 2025. miso-109 quoted **165**, the raw distinct
`plant_id` count for 2023/2024. Same population, two counting conventions; the
energy totals agree exactly (2023 **8.7894** TWh, 2024 **9.0420** TWh), and the
gate uses the LP-visible one because that is what the budget is built from. The
realised window's mean is
(10.1740 + 9.2411 + 8.7894 + 9.0420) / 4 = **9.3116 TWh**.

0.50 is **not a tuned edge**. Measured over all six ISOs × 2018–2026 (probe §A),
the two populations are separated by a wide empty band: the **largest**
early-release census ratio is **0.157** (CAISO 2025, 26/166) and the
**smallest** final-vintage ratio is **0.800** (ERCOT 2024, 12/15 — genuine
attrition of very small hydro, not coverage loss). 0.50 sits mid-band, 3.2×
above the largest early release and 1.6× below the smallest complete filing.
(Note the 0.800 figure: a naive 0.8 threshold would sit exactly on a real year's
value and misfire on ERCOT.)

**(2) Fallback when a registry ISO has no complete filing in the window —
`None`, i.e. the shape-year 923 level, and that is intended.**
`climatological_monthly_hydro_923` returns `None`, `forecast_monthly_hydro`
returns `None`, and `build_hydro_fleet` leaves the budget at the (clamped)
shape-year EIA-923 level. This is the right fallback because it is **still the
same population** — a single water year instead of a climatology, not a
different series. Two consequences are stated rather than hidden: the level
loses its normal-water-year averaging, and **the wet/dry `hydro_year` lever goes
inert** because there is no target to scale. Both are logged at WARNING. This
path is unreachable for MISO today (four complete years); it exists so a future
registry entry with thin coverage degrades to something coherent rather than to
the contaminated series.

**(3) `HYDRO_CLIMATOLOGY_YEARS` is NOT extended.** Rule 23
`[R-FROZEN-DERIVE]` requires a **source-data** justification for a window
change, and there is none — the 2022 hole is not missing source data. MISO's and
CAISO's wide per-BA extracts `data/raw/eia-930-hourly/{MISO,CISO} hourly.parquet`
carry **7 and 9 rows** for 2022 against 8760, while the per-year long-form
`data/raw/eia-930/{MISO,CISO}_fueltype_2022.parquet` files are **present and
complete** (61,320 / 70,080 rows). That is an **extract-build gap**, and its
remedy is rebuilding those two extracts in a data-intake session. Extending the
window instead would move the forward level of **every** ISO to work around two
files, and would cross ISO boundaries this session has no mandate over
(rule 25). After this fix MISO no longer reads the 930 side at all, so the gap
stops affecting MISO's forward level entirely; CAISO's exposure is CAISO's lane.
Recorded as an open data-intake item, not actioned.

**(4) No scale factor**, per the charter and miso-109 §2. None was introduced,
and the monthly deltas in §5 show why one could not be: the gap is **+38.2 %**
in July and **−12.0 %** in December.

## 5. Measurements (probe `scripts/probes/_miso110_forward_level_audit.py`)

**§C, all six ISOs — naive vs window-matched, with the realised windows shown.**
Rule 25: each row is evidence for that ISO's own lane.

| ISO | naive (different windows) | window-matched | three-signature verdict |
|---|---:|---:|---|
| ERCOT | +0.2 % | −10.8 % | clean (no PS fleet) |
| CAISO | **+15.5 %** | +5.1 % | **CLEAN** — 0 breach hours, negative `WAT` hours prove pumping is netted |
| PJM | +71.5 % | +72.5 % | DEFECT, the largest — its own lane |
| MISO | **+10.0 %** | +11.1 % | **DEFECT — fixed here** (per-year 2023 +13.5 %, 2024 +18.5 %) |
| NYISO | −6.8 % | −4.8 % | clean — bias runs the opposite way |
| NEISO | +0.2 % | +7.0 % | time split from Nov 2024, not a standing fold |

CAISO's row is the point: **the largest naive delta of any clean ISO.**

**§D, MISO's corrected forward level** (GWh/month, realised 923 window
2021–2024 vs realised 930 window 2021+2023–2025):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **923 `HY`** (new) | 804.9 | 769.9 | 841.8 | 902.1 | 1042.6 | 932.1 | 807.9 | 705.5 | 549.1 | 541.2 | 675.5 | 738.9 |
| 930 `NG: WAT` (old) | 853.1 | 815.8 | 914.2 | 984.0 | 1058.0 | 1035.7 | 1116.2 | 947.3 | 700.6 | 536.6 | 632.3 | 650.4 |
| delta % | +6.0 | +6.0 | +8.6 | +9.1 | +1.5 | +11.1 | **+38.2** | **+34.3** | **+27.6** | −0.8 | −6.4 | −12.0 |

The monthly signature is the fold, not a level offset: **Jul/Aug/Sep +38/+34/+28 %**
— summer pumped-storage cycling, the same Jun–Sep signature miso-109 measured
per-year — while Oct–Dec go **negative**. A single scale factor cannot represent
a discrepancy that changes sign by month, which is the measured reason there
isn't one.

## 6. Verification is NO-LP, and that is the point

The forecast level is a 12-vector, so every claim is assertable without a solve.
Tests land in `tests/unit/data/test_hydro.py::TestPumpedStorageFoldedForecastLevel`,
beside `TestPumpedStorageFoldedLevelGuard`. All 106 tests in the module pass.

| # | assertion | result |
|---|---|---|
| 1 | MISO's forecast level equals the coverage-gated 923 `HY` mean **exactly** (`assert_array_equal`, not a tolerance) | PASS — 9.3116 TWh |
| 2 | **Every** non-registry ISO's `forecast_monthly_hydro` is **byte-unchanged** — asserted for ERCOT/CAISO/PJM/NYISO/NEISO × dry/normal/wet, not assumed | PASS, 15/15 exact |
| 3 | wet/dry lever still multiplies cleanly (0.85 / 1.00 / 1.15, exact) | PASS |
| 4 | **Regression guard** — `build_hydro_fleet(forecast_budget=True)` returns a FULL plant census past the EIA-923 vintage horizon (the `shape_year` clamp; nyiso-forecast-2035 finding 1) | PASS at **2026 and 2035**, 160 units both |
| 5 | realised window is a subset of the requested one and gates 2025 out | PASS — (2021, 2022, 2023, 2024) |
| 6 | fallback returns `None` and WARNs when no complete filing exists | PASS |
| 7 | forward and corrected-backcast levels are now the same population | PASS — 9.3116 TWh sits between the 2023 (8.789) and 2024 (9.042) backcast levels ×1.05 |

**No solve was spent, and none was owed.** Blast radius is zero:
`frontend/data/forecast/registry/` does not exist (no MISO forecast run is
registered anywhere), and `program-status.json` records that **no ISO clears the
T1→T2 rubric gate or the §2.1b full-solve authorization gate**. Nothing needs
re-solving and no keeper is at risk. Rule 22 was not engaged: no year was solved
or scored in either mode.

## 7. Rule 19 `[R-ONE-MECH]` — what else acts on this phenomenon

Unchanged from miso-109's enumeration, re-checked on the forecast path. The
monthly level is the **only** mechanism acting on MISO hydro energy placement:
`hydro_dispatch_envelope`, `hydro_min_flow_floor`, `hydro_ror_split` and
`hydro_budget_nameplate_aware` are all default-off and off in MISO's keeper. The
fix **replaces** the level in place; nothing is stacked on another mechanism's
residual.

**Standing hazard, recorded and again NOT actioned.** `HYDRO_ENVELOPE_PERCENTILE`
and `HYDRO_MIN_FLOW_PERCENTILE` are built from **hourly** `NG: WAT` and inherit
the same contamination. Both are default-off and off in MISO's keeper, so
nothing is stacked today — but arming either at a registry ISO needs its own
source fix first, and EIA-923 is monthly so there is no hourly substitute. That
is a separate charter, flagged in the constant's citation and the matrix row.

## 8. Governance

* **Rule 5 `[R-NO-MAGIC]`** — the one new scalar,
  `EIA923_COMPLETE_FILING_CENSUS_FRACTION = 0.50`, carries a measured citation
  and sits mid-empty-band (§4.1). No new `ScenarioConfig` field.
* **Rule 12 / 16 / 22** — not engaged; no solve, no scoring, no year touched.
* **Rule 14 `[R-ACCURATE]`** — the accurate input is kept regardless of effect
  on any residual; no residual was consulted, and none could be (no run).
* **Rule 15 `[R-DASHBOARD]`** — nothing to register: no run was produced. Had
  one been, it would go on the **forecast** dashboard via
  `scripts/register_forecast_run.py`, never the backcast registry.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the window is unchanged; the one derived
  threshold cites source data (census counts), never a residual.
* **Rule 25 `[R-ISO-SCOPE]`** — registry-scoped to MISO. PJM's larger defect
  (+71.5 % naive / +72.5 % matched) is measured here and **left for PJM's own
  lane**; NEISO still needs a per-window treatment, not this switch.
* **Rule 26 `[R-MECH-MATRIX]`** duty (b) — `hydro_level_923_hy` re-stamped
  `B` → `BF` with the forecast-lane outcome, and the MISO lever-queue item 6
  extended, both in this session. Duty (c) does not bite: no new
  `ScenarioConfig` field. `scripts/check_mechanism_matrix.py` passes.
* **Rule 27 `[R-PUSH]`** — Opus session (scope writes `src/market_sim/`); edits
  made locally with the Edit tool, blob-verified after push.

## 9. Open, not actioned

1. **KEEPER PROMOTION of `2026-07-31-miso-109b-hy-level` is an owner call** and
   is untouched here. If promoted, flip `hydro_level_923_hy`'s MISO cell `O` →
   `K` and run the keeper auditor scoped `--iso MISO`.
2. **PJM's forward level carries the same defect, larger.** PJM's forecast
   climatology is 15.875 TWh against a 9.254 TWh 923 `HY` climatology. Adding
   `"PJM"` to the registry is a one-line change that fixes both lanes at once —
   but it moves PJM's keeper and owes PJM's own A/B (rule 25).
3. **Data-intake item (new, from §4.3):** rebuild
   `data/raw/eia-930-hourly/{MISO,CISO} hourly.parquet` to cover 2022. The
   source files are already on disk. This would restore 2022 to CAISO's 930
   climatology and close the window mismatch that makes the naive comparison
   misleading in the first place.
4. **Hazard (§7):** the hourly envelope / min-flow floor remain `NG: WAT`-derived
   at registry ISOs. Separate charter.
