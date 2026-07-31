# FINDING — nyiso-106: NYISO solar 2025 is scored against an 8-plant partial vintage, and the two guards built to stop that both miss it

**Session:** nyiso-106. **Keeper under test:** `2026-07-31-nyiso105-chp-heat-rates`
(bundle `results/calibration/nyiso105_chpheatrate_B`, CALIBRATED-WITH-CAVEATS,
0 FAILs, 1 ledgered caveat C3c). **Frozen HEAD:** `a209836`.
**Solves run: ZERO.** Both scoped no-solve items closed on measurement alone —
the nyiso-93/94/95/97/99/101/105 pattern.

Scope items A and B. Item A's stated premise did not survive contact
(§A.1), and what replaced it is a larger and more precise defect (§A.2–§A.5).
Item B's prerequisite turned out to be live in the **committed** artifacts, not
only the refreshed one (§C).

---

## §A — Item A: the 2025 solar "actual" is a survey-coverage artifact

### A.1 The scoped premise is moot: `NG: SUN` is not the benchmark, and it is not gappy

The scope asked to "gap-audit `NG: SUN` the nyiso-98 way (zero-block census, then
falsify the gap days)". There are no gap days to falsify. On the model's
8760-hour clock, EIA-930 `NYIS` `NG: SUN` is **identically zero**:

| year | NaN | zero hours | zero blocks | longest block | midday (h10–15) zeros | max MW |
|---|---|---|---|---|---|---|
| 2023 | 0 | **8,760 / 8,760** | 1 | 8,760 | 2,190 / 2,190 | 0 |
| 2024 | 14 | **8,746 / 8,746** | 3 | 6,351 | 2,190 / 2,190 | 0 |
| 2025 | 14 | **8,746 / 8,746** | 3 | 8,375 | 2,190 / 2,190 | 0 |

This is not a reporting gap in the nyiso-98 sense (a real series with zero-coded
holes). NY grid solar is overwhelmingly distribution-connected / net-metered and
invisible to the NYIS balancing-area telemetry, so the series is structurally
absent. **The codebase already knows this** — it is the stated reason
`results.calibration._EIA923_OVERRIDE` routes NYISO solar's scoring to **EIA-923**
instead (`calibration.py:110-118`). So the audit's real target is EIA-923.

### A.2 The real defect: the 2025 EIA-923 vintage carries 8 of 565 solar plants

`data/raw/_processed-legacy/eia923_monthly_generation.parquet`, `ba_code == NYIS`,
`fuel_type == SUN`:

| year | plants | TWh | months reporting |
|---|---|---|---|
| 2022 | 371 | 1.6295 | 12 |
| 2023 | 441 | 2.0479 | 12 |
| 2024 | 565 | 2.9008 | 12 |
| **2025** | **8** | **0.6617** | 12 |

It is a **plant**-coverage collapse, not a month-coverage one: all 8 report all
12 months. The whole 2025 vintage is a preliminary monthly survey — nationally
**13,210 → 3,427 plants** — and NYIS is hit across the board (`WAT` 152 → 6,
`WND` 34 → 15, `NG` 128 → 31, `LFG` 17 → 1, `MWH` 46 → 0).

**The 8 plants are a strict subset of 2024's 565, and on a like-for-like basis
they GREW:**

| basis | 2024 | 2025 |
|---|---|---|
| all plants | 2.9008 TWh | — |
| restricted to the 8 that report in 2025 | **0.2527 TWh** | **0.6617 TWh** |

(Morris Ridge Solar 20,861 → 313,307 MWh, High River 67,754 → 156,395 MWh.)
NY utility-scale solar did not fall. **557 plants stopped being counted.**

### A.3 Independent falsification: NYISO's own telemetry says solar GREW

NYISO MIS **P-63 Real-Time Fuel Mix** publishes **no** separate solar category —
verified live against the source this session (`20250701rtfuelmix_csv.zip`: seven
categories, Dual Fuel / Hydro / Natural Gas / Nuclear / Other Fossil Fuels /
Other Renewables / Wind). Grid solar sits inside **Other Renewables**, whose
flat biomass/refuse/LFG baseline and solar bulge separate cleanly (2025:
~233 MW overnight → ~550 MW at noon). Decomposing per day (baseline = the
night-hour median, bulge = Σ max(0, MW − baseline)):

| year | Other Renewables total | night baseline | **solar bulge** |
|---|---|---|---|
| 2023 | 2.226 TWh | 231 MW | **0.212 TWh** |
| 2024 | 2.745 TWh | 248 MW | **0.577 TWh** |
| 2025 | 3.022 TWh | 233 MW | **0.994 TWh** |

Monotonic growth, ~4.7× over three years, against an EIA-923 series that claims
a 77 % collapse. **The 2025 actual is falsified.** (The bulge is a *lower bound*
on the EIA-923 population — NYISO meters only market-participating solar, EIA-923
counts every plant ≥ 1 MW — so it establishes the direction and the falsification,
not the level.)

### A.4 The scored consequence, reproduced exactly from the committed keeper

Decoded from `frontend/data/backcast/runs/2026-07-31-nyiso105-chp-heat-rates.js`:

| year | model TWh | actual TWh | error | source |
|---|---|---|---|---|
| 2023 | 1.938 | 2.0479 | −5.37 % | eia923 |
| 2024 | 2.644 | 2.9008 | −8.85 % | eia923 |
| **2025** | **3.554** | **0.6617** | **+437.1 %** | eia923 |

The model's solar is *fine* — it grows 1.94 → 2.64 → 3.55 TWh, tracking the same
fleet build-out NYISO's telemetry shows. **The benchmark broke, not the model.**

### A.5 Two purpose-built guards exist and NYISO solar falls through BOTH

1. **`scripts/audit_eia923_completeness.py`** exists precisely to stop a class
   being scored against a half-reported vintage. It audits **GAS + COAL only** —
   its own docstring: *"Non-fossil/renewable classes are scored on EIA-930, so
   923 completeness does not gate them."* That is true for every ISO **except the
   one `(ISO, class)` pair in `_EIA923_OVERRIDE`**. The committed
   `frontend/data/backcast/completeness/eia923_2025.json` audits exactly
   `[CC_CHP, CC_REGULAR, COAL_BIT, COAL_PRB, CT_CHP, CT_PEAKER, ST_CHP, ST_GAS]`
   for NYISO — **`solar` is absent**. (It correctly flags all six gas classes
   `incomplete`.)

2. **`run_calibration_full._backfill_renewables_eia930`** repairs wind / solar /
   hydro by swapping in the EIA-930 grid total when the 923 class total falls
   below 90 % of it. Its first act is:

   ```python
   ann930, mon930 = _e930_series_annual_monthly(e930, klass, year)
   if ann930 <= 0.0:
       continue          # <-- NYISO solar: the repair bails here
   ```

   The repair keys on the very series that is identically zero. **It cannot fire
   for exactly the cell that motivated `_EIA923_OVERRIDE`.**

Everything else in NYISO 2025 *was* repaired — the committed bench part carries
wind 7.049 (930 swap), hydro 24.104 (930 swap), biomass 0.672 (prior-year
carry-forward) — reproduced bit-for-bit this session. **Solar 0.662 is the single
unrepaired cell.**

### A.6 Blast radius, measured

Solar is **not** a C1-gated row (`score_fuelmix` scores only `GAS_CLASSES +
COAL_CLASSES`), so the +437 % never fired a FAIL. It is not harmless either: it
enters `_gen_totals`' `a_gen`, the shared share denominator. Correcting 2025 solar
0.662 → 2.901 moves `a_gen` 133.953 → 136.192 TWh (+1.67 %) and every fossil
class's `share_pp` — CC_REGULAR −0.43 pp, ST_GAS −0.20 pp, CC_CHP −0.16 pp
(band ±3.0 pp). Material, not decisive. The headline damage is the dashboard
reporting a 5.4× over-generation that does not exist.

**Rule-14 verdict: the 2025 solar statistic must not size or judge any mechanism** —
which is what Item A was for.

---

## §B — The fix: route a class with no EIA-930 authority to the carry-forward

A class that is absent from CAMPD **and** absent from EIA-930 **and** truncated by
a partial vintage is in precisely `biomass`'s position, and the repo already has
the right repair for that: the prior complete year's class total scaled by the
vintage completeness, reusing that year's monthly shape
(`_reconciled_mustrun_class`). NYISO solar was excluded from it only because it
sits in `_EIA930_RENEWABLE_CLASSES`.

`_backfill_renewables_eia930` now falls through to that carry-forward instead of
`continue`-ing when `ann930 <= 0.0`. **No new parameter, no new threshold**, and
the existing `_EIA923_VINTAGE_COMPLETENESS_FRACTION` (0.90) gates it.

Verified on the real committed data, all three years:

| year | vintage completeness | solar raw | solar repaired |
|---|---|---|---|
| 2023 | 1.0495 (complete) | 2.0479 | **2.0479** (exact no-op) |
| 2024 | 1.0370 (complete) | 2.9008 | **2.9008** (exact no-op) |
| 2025 | **0.8850 (partial)** | 0.6617 | **2.5673** |

`2.9008 × 0.8850 = 2.5673`. The scored 2025 statistic becomes **+38.5 %** instead
of +437.1 %.

**Blast radius, measured across 6 ISOs × {wind, solar, hydro} × 2023–2025: NYISO
solar is the ONLY cell with a zero EIA-930 authority.** Every other ISO-class has
a nonzero series and takes the pre-existing swap branch, unchanged (spot-checked
live: NEISO 2025 solar 1.021 → 1.577, PJM 13.364 → 24.674 — both the old path,
both identical to before).

**Direction, stated plainly (rules 1 / 13 / 21).** The repair makes the model look
*better*. That is not why it is being made: it introduces no free parameter, it is
the byte-identical formula biomass already uses, it is gated on a pre-existing
threshold, and an independent instrument (§A.3) establishes the old number was
wrong before the new one was computed. It is also **conservative** — a
carry-forward under-states a growing class rather than fitting it.

**No committed keeper changes.** Bench parts are built from the bundle's own
`eia923` input, written at solve time, so the correction is **forward-acting**: it
applies to the next NYISO solve. The nyiso-105 keeper's committed scorecard still
carries +437.1 % until it is re-solved.

Tests: 4 added to `tests/curation/test_eia923_renewable_backfill.py` (synthetic
zero-930 carry-forward; synthetic complete-vintage no-op; live NYISO 2025 lands in
2.0–3.0 TWh; live 2023/2024 byte-identical). 10 pass.

---

## §C — Item B: the `p25_cf` clamp, and a correction to nyiso-105's account of it

nyiso-105 reported the above-nameplate `p25_cf` defect as a property of the
**refreshed** NYISO artifact (S A Carlson 142.2 %, Astoria 101.7 %). It is
**already live in every committed artifact**:

| ISO | rows > 100 % | max | breaching groups | **ST_GAS breaches** |
|---|---|---|---|---|
| MISO | **17** | 150.0 | CC_REGULAR 5, CT_CHP 4, CC_CHP 3, COAL 2, CT_PEAKER 2, ST_CHP 1 | 0 |
| NEISO | 3 | 150.0 | CC_CHP 1, COAL 1, **ST_GAS 1** | **1** |
| NYISO | 2 | 150.0 | CC_REGULAR 1, CT_CHP 1 | 0 |
| PJM | 3 | 130.6 | CC_REGULAR 2, COAL 1 | 0 |
| CAISO | 0 | 95.0 | — | 0 |

Source: `derive_thermal_tranches.py:555` clips available-CF at **1.5**, a
multi-unit CEMS-noise guard, and `p25_cf` inherits that ceiling while
`committed_pct` / `mustrun_pct` are separately capped at 0.70 / 0.60.

**Clamped at 1.0 (nameplate)** in both places — the deriver (`_P25_CAP`, so the
artifact never carries an impossible value) and the accessor
(`campd_bins.thermal_tranche_p25_level`, so the *stale* committed artifacts —
which is all of them — cannot inject one without a re-derivation). The ceiling is
1.0 and **not** `_COMMITTED_CAP`: the defect is physical impossibility, not a
large share. p25 ≥ p5 by construction, so a 0.70 cap would collapse p25 onto the
committed level and destroy the mechanism it refines.

**Measured inert on every live keeper.** The only consumer is the ST_GAS
per-plant floor, gated on `level > 0 AND online_frac > 0`. The sole breaching
ST_GAS row anywhere (NEISO Merrimack 150.0) sits in an artifact with **no
`online_frac` column**, so no NEISO plant is armable. MISO — the one ISO that
arms the `st_gas_mustrun_p25_level` + `st_gas_mustrun_per_plant` pair — has 16
armable ST_GAS rows topping out at **67.4 %**. After the clamp, **0 levels above
nameplate in any ISO** (was: MISO 17 / NEISO 3 / NYISO 2 / PJM 3 across all
groups). 149 tranche/binning tests pass.

Rule 23 `[R-FROZEN-DERIVE]`: this is a **physical-admissibility bug fix**, not a
residual-driven re-derivation — nothing here responds to a backcast miss.

**The artifact refresh itself is NOT done and stays chartered.** nyiso-105's §A.3
measurement stands (refreshing moves `p25_cf` on 32/78 rows, `committed_pct`
36/78, `median_cf` 37/78 — the tranche shares the whole NYISO offer curve is
built from). Its prerequisite is now met; it still needs its own control arm and
a solve.

---

## §D — What this changes on the record

* **Scope Item A — CLOSED, no solve.** The 2025 `solar` statistic (+437.2 %) is a
  survey-coverage artifact, falsified against NYISO's own telemetry. It is
  **barred from sizing or judging any mechanism**. Root cause found and fixed
  forward.
* **ST_CHP 2025 (+85.0 %) is already handled.** It is audited `incomplete`
  (plant retention 0.667) in the committed completeness part and is therefore
  C1-**SKIPPED**, not gated. No new defect.
* **OTHER 2025 (+11.4 %) is a THIRD instance of the same family — reported, NOT
  fixed here (see §E).** It is not, as first drafted, already carried forward.
* **Lever 2 (`hydro_budget_nameplate_aware`) is re-framed before it was ever
  sized.** NYISO hydro's 2025 actual (24.104 TWh) comes from the **EIA-930 swap**;
  2023's (28.031) and 2024's (27.465) come from **EIA-923**. The scope's
  "+1.3 / +1.3 / −12.7 %, a miss ENTIRELY in 2025" is measured **across a
  benchmark-basis switch**, not on one basis. Any hydro lever must first
  establish how much of the −12.7 % survives putting all three years on one
  basis. This is exactly the artifact shape the scope warned about — and it was
  found before a solve was spent.
* **Scope Item B / §5.5 item 6's successor charter — prerequisite DONE, refresh
  still chartered.** Clamp landed in deriver + accessor, measured inert.
* **No mechanism was tested.** No matrix verdict flips; no `ScenarioConfig` field
  added; no keeper changed; **zero fitted parameters**; C3c untouched and its
  closed queue stays closed.

---

## §E — Found in passing: `OTHER` is injected on one basis and scored on another (REPORTED, NOT FIXED)

`_reconciled_mustrun_class`'s own docstring states its contract: it is *"the
single source of truth for 'how much' of an injected residual class (`biomass` /
`OTHER`) **both the benchmark and the must-run injection** consume, so the
model's injected energy is pinned to the exact value it is scored against."*

**The benchmark half only implements `biomass`.** `_backfill_renewables_eia930`'s
carry-forward block is hard-coded to `biomass`; `OTHER` never gets it. So the
model injects OTHER at the carried-forward level while the scorecard compares it
against the raw truncated vintage.

NYISO 2025, decisive:

| quantity | TWh |
|---|---|
| model OTHER dispatch (committed keeper sidecar) | **1.9483** |
| `_reconciled_mustrun_class("OTHER")` carry: 2.2014 × 0.8850 | **1.9483** |
| benchmark `classFull` OTHER (raw 2025 vintage, 10 plants vs 76) | **1.7487** |
| scored error | **+11.4 %** |

The model's value **is** the carry-forward, to four decimals. **On a consistent
basis the error is exactly 0.0 %** — the entire +11.4 % is the basis asymmetry.

Blast radius, measured (the carry fires only below 0.90 completeness):

| ISO | 2025 completeness | OTHER raw | OTHER carried | Δ TWh |
|---|---|---|---|---|
| CAISO | 0.7331 | 5.5034 | 5.9206 | **+0.4173** |
| NEISO | 0.8278 | 2.6130 | 2.7748 | **+0.1618** |
| NYISO | 0.8850 | 1.7487 | 1.9483 | **+0.1996** |
| ERCOT | 0.9372 | 0.8746 | 0.8746 | 0.0000 |
| PJM | 0.9233 | 4.7776 | 4.7776 | 0.0000 |
| MISO | 0.9230 | 5.8328 | 5.8328 | 0.0000 |

**Not fixed in this session, deliberately.** Unlike the solar repair — measured to
a **one-cell** blast radius — this one demonstrably moves **three ISOs'** 2025
benchmark, so it changes CAISO and NEISO scoring from a NYISO session. It is a
one-line change in shape (route the carry-forward block through
`_reconciled_mustrun_class` for `("biomass", "OTHER")`, which also gets the
pumped-storage holdout right for free, rather than hand-rolling it for biomass),
but it needs its own charter and per-ISO verification. **Named successor.**

Until then: **NYISO's OTHER 2025 +11.4 % is a benchmark artifact and must not
size or judge a mechanism either.**

---

Evidence in-repo: `scripts/probes/_nyiso106_solar_benchmark_audit.py`;
`results/calibration/_nyiso106_solar_benchmark_audit.json`.
