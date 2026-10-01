# PREREG nyiso-219 — is there an **admissible daily driver** for NYISO's within-month hydro allocation? The DATA question, answered with measurements

**Session:** nyiso-219, NYISO backcast calibration. **Branch:**
`claude/nyiso-hydro-within-month-cq14o1`, on `main` at `ad78cc3e`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **not touched.** Nothing is armed, screened,
solved or registered by this session, no marker moves, no cell letter changes.
**ZERO LP.** Every model-side input is a committed artifact; the only new inputs are public
hydrological records fetched read-only.

**Written and pushed BEFORE any measurement number below is read.** Section 2 discloses
everything already in hand (rule 29 step 0).

---

## 0. There are NO in-sample rubric failures, and this session targets none

NYISO's keeper reads **CALIBRATED**, grade 7/8, **zero failing criteria** across 2023–2025, with
C3c the lone ledgered caveat. The only failing rubric cells anywhere in the NYISO record are on the
**2022 validation holdout** (C3a −11.3 % / C3b 0.222 on the nyiso-218 arm; −12.5 % / 0.229 on the
keeper), and **rule 22 `[R-HOLDOUT]` forbids targeting them**: 2022 motivates, never gates, and
identifies nothing.

**This session's object is structural and is not a rubric criterion at all.** There is no hydro row
in `fuelRows` and no hydro record in any C-criterion. Nothing here is gated on a price residual
(rule 1 `[R-STRUCT]`).

**No held-out year is spent.** Sections 3–5 read **measured data only** for years outside 2023–2025
— EIA-930 `NG: WAT` actuals and public streamflow records. **No model output for any out-of-training
year is read, no score is computed for one, and nothing is solved or registered.** Rule 22 is
explicit that what is held out is the **score**, never the **data**: "Measured data inputs are
collected once and applied CONSISTENTLY ACROSS ALL YEARS." A correlation between two *measured*
series is a data property, not a score. The one place a model series enters (§5, D-C's comparison
against the model's own residual) is restricted to **2023–2025 committed keeper artifacts**.

## 1. The object, inherited and not re-derived

nyiso-218 §8 (`docs/FINDING-nyiso218-hydro-within-month-daily-allocation-2026-09-07.md`) localized
NYISO's hydro shape residual completely. Its numbers are **inherited, not re-measured**:

| year | hourly r | month energy r | **within-month day energy r** | hour-of-day r | vol err |
|---|---|---|---|---|---|
| 2022 | 0.694 | 0.949 | **0.358** | 0.988 | −2.18 % |
| 2023 | 0.677 | 0.898 | **0.392** | 0.975 | −0.82 % |
| 2024 | 0.757 | 1.000 | **0.248** | 0.987 | −0.14 % |
| 2025 | 0.723 | 0.998 | **0.207** | 0.989 | −0.19 % |

The armed mechanisms (`hydro_dispatch_envelope`, `hydro_min_flow_floor`,
`nyiso_hydro_reserve_eligible` — all **K**) constrain the month level and the diurnal shape; the
residual has retreated into the one dimension none of them touches. The model **over-swings** day to
day at **1.86 / 1.86 / 1.94 / 2.25×** the actual's within-month daily standard deviation, sits at
its own month × hour-of-day ceiling in **27–42 %** of hours delivering **32–49 %** of annual hydro
energy there, and its day residual correlates with day price at **+0.33…+0.46**.

nyiso-218 deliberately proposed **no mechanism** and named the successor as an **open data
question**: does a forward-drivable, condition-responsive daily inflow/flow driver exist for NYISO's
basins at usable quality? **This session answers that question with measurements.** It is
deliverable (a) of the handoff.

**Cells already adjudicated — not re-tested, not re-proposed:** `hydro_ror_split` **G**
(governance-refused, nyiso-111, falsified ex ante), `hydro_budget_nameplate_aware` **I** (provably
inert, nyiso-107).

## 2. Everything already in hand before these predictions were written (rule 29 step 0)

Disclosed in full, in the nyiso-218 §3 style:

* **C-1.** The §1 table, the over-swing ratios, the ceiling census and the price correlations —
  inherited from nyiso-218, all committed.
* **C-2.** NYISO's model hydro fleet: **163 plants, 4,681.0 MW nameplate** (`_load_hydro_nameplate`,
  prime mover `HY`, pumped storage excluded). Top two: **plant 2693 = 2,429.1 MW (51.89 %)** and
  **plant 2694 = 912.0 MW (19.48 %)**, both zone `Upstate_West` — **71.37 % of fleet MW in two
  plants**. Third-largest is 59.0 MW (1.26 %). *(Identified in the literature as Robert Moses
  Niagara and the St. Lawrence–FDR project; the EIA-860 attribution is measured in §3, not assumed
  here.)*
* **C-3.** EIA-930 `NYIS hourly` extract coverage: **2015 (partial, 4,416 h), 2016–2025 full,
  2026 partial (3,912 h)**. `NG: WAT` is a present column. So **ten full measured years,
  2016–2025**, are available for a climatology.
* **C-4.** **Basis re-verified by execution**, not assumed: NYISO is in neither
  `EIA930_PS_FOLDED_INTO_WAT` (MISO, PJM) nor `EIA930_PS_SPLIT_COMPLETE_FROM` (NEISO: 2025), so
  `eia930_wat_level_folded` is **False in every year** — `NG: WAT` is conventional hydro only and
  Blenheim-Gilboa pumped storage is booked under the model's `storage` klass. **Conventional-only on
  both sides.**
* **C-5.** `data/raw/eia-860/eia860_plant.parquet` exists (17,043 rows, 42 columns) and carries
  **`Name of Water Source`, `Latitude`, `Longitude`, `County`**. I have **not** read its NYISO hydro
  values. This is instrument availability, not a measurement.
* **C-6.** USGS NWIS daily-values web service is **reachable from this container**: a five-day
  `parameterCd=00060` query for site `04216000` returned **HTTP 200**. **No response body was
  read** — only the status code.
* **C-7.** Keeper `cache_key` **re-measured at this HEAD (`ad78cc3e`)**:
  **`95d4d8d167373eb7`** — identical to the value recorded at `71e62675`, `12e71b89` and
  `bfbb0b6a`. The capx D79 solve-surface fingerprint has still not moved NYISO's key.
* **C-8.** Fleet instrument validated: `scripts/probes/nyiso196_rebuild_checks.py --year 2024`
  **exit 0**, `git status --porcelain -uno` **empty** after it.
* **C-9.** The within-month statistic's exact definition, read from the committed instrument
  (`nyiso218_hydro_shape_decomposition.py`): Pearson r over the year's 365 days (Feb 29 dropped by
  the loader) of `daily_total − mean(daily_total over that day's calendar month)`, model vs actual.
  **Every r in §5 uses this identical construction**, so its values sit on the same scale as the
  0.207–0.392 above.
* **C-10.** No G-DRIFT audit is owed: **no solve is planned**, so there is no arm, no control and no
  keeper-differencing (rule 29 (b) form 4 is not invoked). The cache-key re-measurement C-7 is the
  relevant check and it is unmoved.

**My preferred answer, stated up front so the reader can discount it:** I expect the honest result
to be that a forward-drivable daily flow driver **exists** for the minority of the fleet but that
the **~71 % Great-Lakes-outflow majority is regulated, lake-buffered and not runoff-responsive at
the day grain**, so no admissible daily inflow driver carries enough of the missing signal — making
the successor object a **day-to-day transfer/shifting limit**, not a daily inflow shape. §5's P3b is
written specifically to falsify that.

## 3. M1 — the fleet → water-source census (zero external data)

Map all 163 NYISO hydro plants to their EIA-860 **`Name of Water Source`**, weight by nameplate MW,
and cross-check with `County` + lat/lon.

**Predictions:**

* **P1a** — *not a prediction, disclosed as known (C-2)*: the top two plants are 71.37 % of fleet MW.
* **P1b** — **≥ 6 distinct water sources** are needed to reach 95 % of fleet MW.
* **P1c** — **no single non-Great-Lakes water source exceeds 12 %** of fleet MW.
* **P1d** — **≥ 90 % of the 163 plants** resolve to a non-empty `Name of Water Source`.

**Exhaustive partition on P1d:** (i) ≥ 90 % resolve → the water-source field is the census basis;
(ii) 50–90 % resolve → the field is the basis for what it covers and `County`/lat-lon is the
declared fallback for the rest, **reported as a limitation, not absorbed**; (iii) < 50 % resolve →
the field is unusable and the census is county/lat-lon only, again reported; (iv) the file cannot be
joined to the hydro plant ids at all → **M1 is unmeasurable**, reported as an instrument failure and
§4–§5's MW weights fall back to the C-2 nameplate ranking with no basin labels.

## 4. M2 — the gauge availability census (USGS NWIS, read-only)

For every water source from M1 covering **≥ 3 % of fleet MW**, establish whether a daily-discharge
record exists, and characterize it: site id, **coverage** over 2016–2025, **approval status**
(approved vs provisional), **licence**, and **forward-availability route**.

**Predictions:**

* **P2a** — for the **non-Great-Lakes** basins at ≥ 3 % of fleet MW, USGS daily values (parameter
  `00060`) exist with **≥ 99 % daily coverage over 2019–2025**.
* **P2b** — the Niagara record is **not an independent runoff signal**: its **day-to-day
  coefficient of variation over 2019–2025 is < 5 %** (Lake Erie storage buffers it).
* **P2c** — the St. Lawrence record at Moses-Saunders is likewise **< 5 % day-to-day CV**, being an
  IJC Plan-2014 / ILOSLRB **regulated outflow**.
* **P2d** — a **runoff** river in the fleet (Mohawk class) shows **day-to-day CV > 40 %**, i.e. at
  least an order of magnitude more day-to-day signal than P2b/P2c.

**Exhaustive partition, applied per basin:** (i) approved daily series, ≥ 99 % coverage;
(ii) series exists at 50–99 % coverage or provisional-only; (iii) series exists but is a
**regulated-outflow** record rather than an inflow measurement — *a distinct branch, because a
regulated outflow is a decision variable of another operator, not a natural driver*; (iv) no daily
series on that water source at any gauge; (v) **the query could not be executed** (bad site code,
service error, network). Branch (v) is an **instrument failure and is reported as one** — it is
never folded into (iv).

**Note on the CV thresholds:** 5 % and 40 % are pre-registered *ex ante* as order-of-magnitude
separators, not tuned. If a basin lands between them (5–40 %) that is its own reported outcome and
neither P2b/P2c nor P2d is claimed as confirmed for it.

## 5. M3 — does ANY candidate daily driver actually carry the missing signal?

**This is the decisive measurement.** Target = the actual EIA-930 `NG: WAT` **within-month daily
energy anomaly** (C-9 construction), per year. Candidate drivers, each scored by the same statistic:

* **D-A — LOYO day-of-year climatology.** For target year *Y*, the mean `NG: WAT` daily energy by
  day-of-year over **all other** full years 2016–2025. Carries **no** information from *Y*.
  Forward-drivable by construction.
* **D-B — year-specific measured basin discharge.** The M1 MW-weighted sum of the M2 gauges' daily
  discharge, for year *Y* itself.
* **D-C — the model's own drivers.** Daily mean NYISO load, and daily mean price.
* **D-X — the FORBIDDEN pin, computed only as the scale anchor.** A daily shape pinned to year *Y*'s
  own measured `NG: WAT` daily totals reaches **r = 1.000 by construction**. It is named here so
  that the r scale has a ceiling and so the handoff's warning has a tripwire: *if any admissible
  driver returns r ≈ 0.95, check whether it has become this.* **It is never proposed, never
  built, and never entered anywhere.**

**Predictions:**

* **P3a — kills the climatology option if confirmed.** D-A reaches within-month daily
  **r ≤ 0.20 in every year**. *If it returns ≥ 0.35 in the majority of years, a purely
  climatological daily driver is viable and this session's reading is wrong.*
* **P3b — THE PREDICTION THAT HURTS MY PREFERRED ANSWER.** D-B lands in **0.20 < r < 0.55** — real
  but partial. **If D-B returns r ≥ 0.55, the daily-inflow driver is the right object, my "the
  Great-Lakes majority is unresponsive" reading is falsified, and the recommendation flips to
  "build it".** If D-B returns **r ≤ 0.20**, flow explains essentially nothing at the day grain and
  the object is definitively not an inflow driver. The three branches are exhaustive on the real
  line as written (≤ 0.20 / strictly between / ≥ 0.55); a sixth outcome — **D-B cannot be assembled
  because M2 branch (iv) or (v) fired for the material basins** — is reported as unmeasurable, not
  as a low r.
* **P3c** — the *actual* within-month daily anomaly correlates with **daily mean load at r ≥ +0.25
  in every year 2019–2025**: the real fleet **does** respond to conditions, so the model's defect is
  **over**-response, not response. *If it returns ≤ 0, the real fleet is load-indifferent at the day
  grain and the object is purely hydrological — which would strengthen the inflow-driver case
  against my reading.* Values in (0, 0.25) confirm neither limb and are reported as such.
* **P3d — the ceiling, stated in advance so it cannot be discovered conveniently.** A mechanism
  driven by a single daily series cannot exceed that series' own r with the actual. The model's
  present within-month r is **0.207–0.392**. **If the best admissible driver's r is below the
  model's current value in a year, then arming that driver would make this statistic WORSE in that
  year, and I will report that** — it is exactly the rule 14 `[R-ACCURATE]` situation, and a driver
  that is more *faithful* but scores *lower* is still the accurate input.

**Rule 14 `[R-ACCURATE]` cuts both ways and is stated before the numbers:** hydro is ~20 % of NYISO
generation, so re-timing it **will** move C3a/C3b/C3c. If a more accurate hydro shape makes the
price fit worse, **the accurate shape stays** and the worse fit is a discovered root-cause question
(rule 1 `[R-STRUCT]`, first half, untouched). nyiso-92 flagged exactly this.

## 6. M4 — rule 13 `[R-MEASURED]`, applied in writing to every surviving candidate

For each candidate that survives §5, the admissibility test is answered **in writing, explicitly**:

> *"Could this same quantity be produced for a forward year from forward drivers, and would it
> respond to changed conditions?"*

**Named forbidden, so it is not reached for:** a daily hydro shape pinned to the year's own measured
`NG: WAT` daily totals (D-X). That is an **outcome pin** — the dispatch being validated would not be
the dispatch being forecast — and it would close this residual almost exactly, which is precisely
why it must not be used.

**Boundary discipline, carried from nyiso-214 and nyiso-218:** `NG: WAT` is an **ISO aggregate**.
There is **no per-plant hourly hydro series**, which is why `allocate_min_flow_floor` splits the
fleet floor pro-rata by budget rather than inventing per-plant structure. **This session invents
none either.** Robert Moses Niagara is ~52 % of fleet MW and treaty/flow-governed; any plant-grain
claim would need a basis it does not have. The §3 census assigns **basins**, and every driver in §5
enters as a **fleet-aggregate** series.

## 7. What this session will and will not deliver

**Will:** the measured answer to the data question — whether a forward-drivable,
condition-responsive daily flow series exists for NYISO's basins at usable quality, with coverage,
vintage, licence and fleet mapping stated, rule 13's test applied in writing, and the decisive
measurement of whether any admissible driver actually carries the missing signal. If the evidence
warrants one, an owner decision card (deliverable (b)) is written **on top of** that measurement.

**Will not:** arm a mechanism, propose a cell letter change, solve anything, register anything,
spend a held-out year, open an eighth owner card unless the object genuinely is one, or re-test
`hydro_ror_split` / `hydro_budget_nameplate_aware`.

**A clean negative is a success.** If P3a and P3b both come back low, the honest deliverable is
"no admissible daily driver carries this signal", and that closes the option nyiso-218 floated
rather than leaving it open for a future session to spend LP on.

## 8. Discipline commitments (the standard the predecessors set)

* **No gate is restated after the number is seen.** A prediction that misses is reported as a miss,
  in the words it was written in. nyiso-218's S-1 failed on two `ScenarioConfig` fields that
  post-date the keeper's solve and it was **reported failed, not rewritten**; that is the standard.
* **Every partition above is exhaustive and includes an instrument-failure branch.** nyiso-215's P2
  landed in a gap between its own branches, nyiso-217's P3 declared two tests exhaustive when they
  were not, and nyiso-218's S-1 routed two different causes to one kill branch. Each reported the
  defect rather than restating the gate. Where a partition here still has a gap, **the gap is
  named** (P2's 5–40 % CV band, P3c's (0, 0.25) band).
* **The real measurement, not the cheap proxy.** nyiso-218's annual-max proxy understated envelope
  binding by three orders of magnitude and it published a conclusion from it before the proper
  census overturned it. Any proxy used here is **labelled a proxy** and the real measurement is
  taken before a conclusion is drawn.
* **Rule 31 `[R-RETAIN]`.** Nothing is deleted. No bundle is produced by this session, so there is
  nothing to retain; every fetched record is written under `results/calibration/` or
  `data/raw/` and committed or gitignored as its size warrants, never `rm`'d.
* **Rule 27 `[R-PUSH]`.** Any file ≥ 300 lines is edited locally and pushed as on-disk bytes, with
  the pushed blob verified before the next commit.

**Seven owner rulings remain pending and none is this session's:** nyiso-206 `floor_pct` basis;
nyiso-207 identification-vs-application; nyiso-203 §6; DECISION-CARD-nyiso193 §5/5.1 unit-grain;
nyiso-208 out-of-training CAMPD read; nyiso-214 §6 duct membership; nyiso-215 §6 duty-role level
basis (sharpened by nyiso-216).
