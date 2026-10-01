# FINDING — SCN-LOAD: the six-source `load-forecast` curated intake (owner ruling S4 / card D-4)

**Lane** SCN-LOAD · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-load-forecast-intake-t17qxj` (the desk issued the stem
`…-w9tf`; the harness provisioned and binds pushes to the branch above — the same mismatch
SCN-WS4a and SCN-WS4b each recorded) · **Base** `origin/main` at `d13d1cba` ·
**Solves** none — this lane runs no LP and owed no rule-29 PRECOMMIT.
**Scope note (the prediction this is scored against):** `docs/handoffs/SCOPE-scn-load-2026-09-06.md`,
pushed before any constant was written (`b7fb4796`, now on `main`).

---

## 0. Bottom line

All six published sources were obtainable and all six are on disk. The datatype is built,
schema-validated and consumed; five of the gap list's five rows are addressed; and **three of
the four substantive rows closed further than the scope note predicted** — Table B-9b turned out
to be a downloadable workbook rather than an unread PDF table, ERCOT's own workbook carries an
hourly EV component that arms a layer, and both PJM's and NYISO's "no published low case"
limitations turned out to be publications nobody had opened.

**The intake also found that two of the numbers it replaced were wrong in ways a transcription
could not see** — a systematic era-window error in every rate, and a table that was silently
mixing peak- and energy-derived bases. Those, not the provenance upgrade, are the largest thing
this lane bought, and they move forecast demand by up to +31 % at 2030 (§4).

**What it did not buy** is in §7, stated plainly, including the one row where the ruling's cost
bought nothing.

---

## 1. The closure table (scored against the scope note's §2 prediction)

| row | predicted | **actual** | what happened |
|---|---|---|---|
| **G-D4-1** `DEMAND_GROWTH_RATES` | mid CLOSED ×6; low/high PARTIAL | **CLOSED (mid ×6, and low/high for 3 of 6); PARTIAL on the other 3** | All 36 numbers are now computed from a curated series. ERCOT gained a full published three-point band nobody had used (`base_economic` / Adjusted / TSP-Provided); NYISO's and MISO's bands are published; CAISO, PJM and NEISO publish no growth band and are re-stated as declared band-ratio constructions. **Two defects found beyond the row's scope — §3.** |
| **G-D4-2** `DATACENTER_ADDITIONS_MW` | CAISO `high := mid` CLOSED, MISO `high` CLOSED, PJM/NYISO `low := 0` PARTIAL | **CLOSED — all four named limitations, plus one not on the list** | CAISO: Form 1.1c publishes a *second* DC scenario (Local Reliability), which is the "high-DC table never read". MISO: slide 16 prints the driver's own 22–44 GW range, retiring the ratio extrapolation, **and** its `low := 0`. NYISO: **prediction wrong** — Table I-14's own footer publishes a Lower/Baseline/Higher band, so `low` is a positive published forecast. PJM: prediction correct, `low = 0` survives as a measured null, but with a much better citation. |
| **G-D4-3** `DATACENTER_ZONE_SHARE` | PJM 7 residual zones CLOSED; ERCOT reproducibility CLOSED; MISO BLOCKED | **PARTIAL — ERCOT CLOSED, MISO BLOCKED as predicted, PJM's table READ but the shares deliberately NOT rewritten** | The ERCOT `.xlsb` reproduces SCN-WS4a's aggregation to within rounding (52,304 vs 52,306 MW), so the shares are *verified*, not superseded. **Table B-9b is now on disk and curated per zone** — but see §6: rewriting the PJM shares from it is a change this lane's charter reserves, and it is routed rather than taken. MISO's per-LRZ refinement stays behind the 403 wall. |
| **G-D4-4** `ELECTRIFICATION_LAYERS` *(the priority row)* | NEISO `heat_pump` refined, NYISO `heat_pump` CLOSED, ERCOT `ev` CLOSED, three `ev` cells PARTIAL | **CLOSED as predicted, and the NEISO refinement is bigger than "a refinement"** | Armed cells go **1 → 3**. NEISO's two-anchor line was overstating 2030 heat-pump energy by ~29 % against ISO-NE's own published series. NYISO's and ERCOT's "no published component" comments were both **stale**. Three `ev` cells stay `{}` — but the blocker's identity changed from "no numbers" to "no citable 8760", and the numbers are now in the datatype. |
| **G-D4-5** `DEMAND_GROWTH_TRANSITION_YEAR` | disclosed null, unchanged | **unchanged — disclosed null** | No published basis exists and none was invented. It now stands alone as the family's one unsourced constant, and the comment says so. §7 has the one mitigating observation. |

**Scope-note accuracy:** 4 of 5 rows landed as predicted or better; the one wrong prediction
(NYISO's `low`) was wrong in the direction of *under*-promising. The two §3 findings recorded
ahead of the numbers both materialised, and the second one (mixed bases) turned out to be
larger than stated.

---

## 2. Obtainability, measured — including the flagged blocker

Every source in the scope note's §1 table was fetched. Two additions worth recording:

- **The NYISO Gold Book's sha256 verifies byte-exact** against the committed
  `data/raw/NYISO/SHA256SUMS.txt` record (`43865c1c…b908bf`) — the corpus-conversion recovery
  route works exactly as `data/raw/NYISO/README.md` claims.
- **PJM Table B-9b is not a PDF table.** It is a downloadable workbook,
  `total-load-adjustments-breakdown.xlsx` (19 KB), whose first cell literally reads
  "Table B-9b". The gap list's "never read" was accurate; "unread" turned out to mean
  "never looked for".

**THE MISO 403 WALL IS STILL UP — BLOCKED, as flagged at the gate.**
`https://www.misoenergy.org/planning/…` returns **403** for this environment, re-measured
2026-09-06; `cdn.misoenergy.org` returns 200. The driver-level per-LRZ forecast data the
2026 LTLF says it published (slide 6) is therefore still unreachable, so
`DATACENTER_ZONE_SHARE["MISO"]`'s within-region ordering remains the `load_share` default and
SCN-WS4a's published **regional** decomposition stands unchanged. No worked-around substitute
was used, and none was sought. The lane was not spent on the wall.

---

## 3. Two defects the intake found that were not on the gap list

Both were recorded in the scope note §3 **before** the numbers were written.

### 3.1 A systematic era-window error in every rate (predicted; confirmed)

The model's rate resolver is `era = "near" if year <= DEMAND_GROWTH_TRANSITION_YEAR else "long"`
(`scenario_resolvers.py:223`), and `runner._scale_demand` applies `rate(y)` to the step
`y -> y+1` over `range(weather_year, year)`. So the **near rate governs the transition from the
base level to 2031**, not to 2030. Every rate in the table was derived over `[base -> 2030]`,
leaving the 2030→2031 step covered by neither era and overshooting the era boundary by one
extra year of near growth, compounding forever after.

The intake's derivation makes the two eras tile the span — `near = CAGR(base -> 2031)`,
`long = CAGR(2031 -> min(2050, horizon))` — and the compounded level then reproduces the
publication at 2031 and at the horizon to **1e-15** on all six ISOs (asserted in the derivation).
This correction is independent of the basis question below and would apply even if nothing else
had changed. PJM is the clearest case: its `mid.near = 0.036` was the report's own headline
**ten-year summer-peak** CAGR (2026→2036) being used for a near era that ends in 2030.

### 3.2 The table was silently mixing peak- and energy-derived bases (predicted; larger than stated)

ERCOT / CAISO / PJM / MISO were derived from **peak** series, NYISO from **energy**, NEISO from a
**blend of the two**. The model applies one flat multiplicative scalar to the whole 8760, so peak
CAGR ≡ energy CAGR by construction and only one can be honoured.

**The intake declares ENERGY, uniformly**, on a structural argument rather than a fit:

1. The DC block and the electrification layers are **energy-invariant relocations** — they reshape
   the peak but cannot change the level, so a level error is unrepairable downstream while a shape
   error is exactly what they exist to fix. Rule 1 `[R-STRUCT]`: the scalar owns the level, the
   block and the layers own the shape.
2. Energy is what the LP integrates and what a CO2 answer needs — the question this whole program
   exists to answer.
3. Energy is the only metric published on the model's era resolution by all six: MISO's 2026 LTLF
   gives peak only as 2026 and 2046 endpoints, so a peak basis is not even derivable there.

The measured divergence, per ISO, mid path, near era (**reported, never used**):

| ISO | energy CAGR | peak CAGR (metric) | gap |
|---|---|---|---|
| ERCOT | 13.48 % | 9.09 % (annual peak) | **+4.4 pt** |
| PJM | 6.46 % | 4.08 % (annual peak) | +2.4 pt |
| CAISO | 3.24 % | 2.05 % (1-in-2 non-coincident) | +1.2 pt |
| NYISO | 1.18 % | 0.53 % (summer coincident) | +0.7 pt |
| NEISO | 0.74 % | 0.53 % summer / **2.9 % winter** | −2.2 pt on winter |
| MISO | 5.48 % | not derivable on the model's eras | — |

The direction is the load-factor story: in the DC-heavy ISOs energy outruns peak (ERCOT's own
forecast has the system load factor rising from ~65 % to ~81 % by 2030), and in ISO-NE winter peak
outruns energy under heating electrification. **Under the former peak basis ERCOT's modelled 2030
energy was ~19 % below ERCOT's own published figure, and no downstream mechanism could recover it.**

**This is a modelling-posture change and it is disclosed as one.** It was taken inside this lane
because the charter's own worked example — the NYISO row it names as "what every row should
become" — *is* energy-derived, so applying it uniformly is executing the charter rather than
exceeding it. If the desk disagrees, the curated datatype carries **both** metrics for all six
ISOs, so reverting the basis is a re-derivation, not a re-intake.

---

## 4. The movement, at full magnitude (rule 14 `[R-ACCURATE]`)

**Nothing here was reconciled toward the value it replaced.** No solve was run, so the movement is
reported as the closed-form change in the demand scalar the LP would see — the compounded growth
factor from the default `weather_year = 2024`, old constants vs new:

| ISO | path | 2030 factor old → new | Δ | 2050 factor old → new | Δ |
|---|---|---|---|---|---|
| **ERCOT** | low | 1.340 → 1.122 | **−16.3 %** | 1.867 → 1.459 | −21.8 % |
| | mid | 1.631 → 2.136 | **+30.9 %** | 2.830 → 3.293 | +16.4 % |
| | high | 1.922 → 3.079 | **+60.2 %** | 4.514 → 4.049 | −10.3 % |
| **PJM** | low | 1.126 → 1.236 | +9.7 % | 1.496 → 1.664 | +11.2 % |
| | mid | 1.236 → 1.456 | **+17.8 %** | 2.010 → 2.425 | +20.7 % |
| | high | 1.419 → 1.848 | +30.3 % | 3.168 → 4.290 | +35.4 % |
| **MISO** | low | 1.113 → 1.192 | +7.1 % | 1.421 → 1.430 | +0.6 % |
| | mid | 1.201 → 1.377 | **+14.7 %** | 1.804 → 1.923 | +6.6 % |
| | high | 1.302 → 1.609 | +23.6 % | 2.386 → 2.652 | +11.1 % |
| **CAISO** | mid | 1.180 → 1.211 | +2.6 % | 1.940 → 1.713 | −11.7 % |
| **NEISO** | mid | 1.081 → 1.046 | −3.2 % | 1.373 → 1.354 | −1.4 % |
| **NYISO** | mid | 1.075 → 1.073 | −0.2 % | 1.384 → 1.380 | −0.2 % |

**NYISO is the control and it passes.** Its row was already derived rather than transcribed
(FFR-SC spelled the six CAGRs out by hand in the comment block), and the curated pipeline
reproduces every one of them to 4 decimal places; the only change is the §3.1 window fix, worth
3–5 basis points. That is the strongest available evidence that the extraction is correct rather
than merely different — and it is why the large ERCOT/PJM/MISO moves should be read as
corrections, not as a new methodology producing new numbers.

**Data-centre block movement at 2030** (MW): ERCOT mid 37,000 → **38,182**, high 122,000 →
**88,603**; PJM mid 30,000 → **38,815**; CAISO mid 1,800 → 1,622 and high 1,800 → **4,240**;
NYISO mid (2031) 3,000 → **1,900** and high 10,000 → **2,842**; MISO mid 20,500 → 20,000, high
27,000 → **27,067**, low 0 → **14,111**. The MISO and CAISO mid tracks land within ~2 % and ~10 %
of the values they replace, which independently confirms the earlier hand work; the NYISO and
ERCOT-high moves are edition/basis changes and are large.

**Electrification:** NEISO `heat_pump` 2030 goes 3,184 → **2,464 GWh** (the two-anchor line was
overstating ISO-NE's own published trajectory by 29 %); NYISO `heat_pump` and ERCOT `ev` arm from
nothing.

### 4.1 One interaction with another lane's landed work — ROUTED, not resolved

SCN-WS4b declared `LOAD-HI` with the arithmetic that **ERCOT flips into the DC block's tail
regime in 2030** (`FINDING-scn-ws4b-2026-09-06.md` §3, plan §2.4 G-L3). The new constants move
that boundary a long way. Computed on each publication's own base year as a stand-in for the
model's measured 2024 8760 (the real base is lower, which is why WS-4b's own calculation crossed
where this one does not), the block's share of grown 2030 energy on the ERCOT high path falls
from **97.3 % to 44.1 %** — from hard against the threshold to a factor of ~2.3 clear of it.
NYISO high moves 34.8 % → 10.8 % the same way.

**The `LOAD-HI` case comment in `configs/scenario_campaign_matrix.yaml` is therefore stale, and
this lane may not edit that file** (it is SCN-LEVELS' this wave, and the case is SCN-WS4b's).
Routed to SCN-DESK in §6.

---

## 5. The base-year misalignment — quantified, NOT absorbed

Every edition's first forecast year is **1–2 years ahead of the model's `weather_year`** (default
2024), and `_scale_demand` compounds from the weather year. So a source CAGR applied from the
model's base reaches the era boundary having applied 1–2 extra years of growth:

| ISO | edition base | extra years | overshoot at 2031 |
|---|---|---|---|
| ERCOT | 2025 | 1 | **+13.5 %** |
| PJM | 2026 | 2 | +13.4 % |
| MISO | 2026 | 2 | +11.3 % |
| CAISO | 2026 | 2 | +6.6 % |
| NYISO | 2026 | 2 | +2.4 % |
| NEISO | 2026 | 2 | +1.5 % |

**This is not new, and it is not fixed here.** The former ERCOT row half-absorbed it (its
"6 years from the 2024 model base" construction), while the former NYISO row did not — which is
precisely the kind of hidden, per-ISO compensation rule 14 forbids burying inside an input, and
the reason the intake refused to carry it forward. A constant whose value depends on
`ScenarioConfig.weather_year` while living outside the config is also an off-registry coupling in
spirit (rule 24 `[R-REGISTRY]`).

The honest fix is a **base-year alignment or a level-index growth mechanism** — the model would
consume the published *level* trajectory rather than a two-era CAGR — and that is a mechanism
change, not an intake. **Routed to SCN-DESK (§6).** Related and worth stating with it: a two-era
constant CAGR reproduces its publication only at the era boundary and the horizon; ERCOT's
front-loaded ramp means the intermediate 2030 level sits ~7 % below the published one even with a
perfectly derived rate. That is the representation's limitation, not the derivation's.

---

## 6. Routed to SCN-DESK — not executed, outside this lane's file regions

1. **The `LOAD-HI` case comment is stale** (§4.1). `configs/scenario_campaign_matrix.yaml` is
   SCN-LEVELS' region and the case is SCN-WS4b's. The ERCOT tail-regime arithmetic in that
   comment should be recomputed against the new constants before Stage A runs.
2. **A cache-epoch ledger entry is owed and this lane may not write it.** Scope, precisely:
   **every forecast-mode bundle in ERCOT, PJM, MISO, CAISO and NEISO** solved before this commit
   is stale at the same cache key — `DEMAND_GROWTH_RATES` moves the demand array on **every**
   forecast path including the default `mid`, so unlike SCN-WS4a's zonal-only change this one
   moves system energy. **NYISO forecast bundles move only ~0.2 %** but are not byte-identical
   and should be treated as stale too. **NO BACKCAST BUNDLE IN ANY ISO IS AFFECTED**: growth
   scaling is a no-op when `year == weather_year`, and the DC block and electrification layers
   are coerced off in backcast mode by `validate_datacenter_config` /
   `validate_electrification_config`. `src/market_sim/results/cache.py` is another lane's region.
3. **The basis decision (§3.2) deserves an explicit desk record** even though it was taken inside
   the charter, because it changes forecast levels materially in four ISOs. The datatype carries
   both metrics, so it is reversible by re-derivation.
4. **The base-year misalignment (§5) needs a mechanism decision**, not a constant.
5. **`DATACENTER_ZONE_SHARE["PJM"]` can now be rewritten from Table B-9b and deliberately was
   not.** The table is on disk and curated per zone, so the DOM-anchor-plus-`load_share`-residual
   construction is superseded on the evidence — but this lane's charter says to touch that table
   *"only where a newly-read table supersedes SCN-WS4a's value"*, and SCN-WS4a's PJM shares are
   not its value (they predate it, from FF-1C). Rewriting eight anchors is a siting change with
   its own zonal-dispatch blast radius, and it belongs to whoever owns the siting row. **The data
   is ready; the edit is not this lane's to take.** Published B-9b 2030 shares for the
   record (the zone rows sum to 38,815 MW, exactly the workbook's own RTO row):
   DOM 0.358, AEP 0.223, COMED 0.133, PL 0.129, PS 0.037, APS 0.031, ATSI 0.029, DAY 0.025,
   PECO 0.021, BGE 0.005, PEPCO 0.004, rest ~0 — against the committed DOM anchor of 0.550.
   **The published table puts materially LESS in Dominion, and materially MORE in AEP, ComEd and
   PPL, than the single-anchor-plus-`load_share`-residual reconciliation does** — i.e. the
   documented limitation in that table's own comment ("ComEd, AEP and PL are the next-largest DC
   zones, so the load_share residual mildly understates them; refine all 8 anchors when Table
   B-9b is read") is confirmed, and understated.
6. **The plan §2.4 G-L2 text is now stale in this lane's favour** and is corrected in place
   (one clause), since it describes the exact gap this lane closed.

---

## 7. What the intake bought, and what it did not

**Bought — and the first item is not the one the ruling was sold on:**

- **Two real defects found and fixed**, neither of which a provenance upgrade was supposed to
  find: the era-window error in all 36 rates (§3.1) and the mixed-basis table (§3.2). These are
  worth more than the machine-verifiability the card was about, and they were only visible once
  the source series were on disk beside the constants.
- **Four stale comments corrected**, each of which had been asserting that data did not exist:
  NYISO's "no annual energy component series", ERCOT's "no published end-use decomposition",
  PJM's Table B-9b "never read", and NYISO's/MISO's "no published low case".
- **Three published low/high bands that the model was inventing**: ERCOT's three-way component
  band, NYISO's Table I-14 footer band, MISO's printed driver range.
- **The electrification row went from 1 armed cell to 3**, and the three still-empty `ev` cells
  now have their anchors curated and their blocker correctly identified as a missing hourly shape.
- **Machine-verifiability and automated vintage refresh**, which is what the card actually asked
  for: four of six ISOs are now a drop-in-the-new-workbook-and-re-run.

**Not bought:**

- **The MISO per-LRZ refinement.** Still 403-walled, exactly as flagged at the gate. An intake
  decision did not lift it and could not have.
- **G-D4-5.** `DEMAND_GROWTH_TRANSITION_YEAR` has no published source and now stands alone as the
  family's one unsourced constant. The one mitigating observation, recorded in its comment: it is
  not a free parameter in the usual sense — it says only *where* the two eras meet, and each era's
  rate is derived *against* that boundary, so moving it re-derives both rates rather than
  re-tuning the level.
- **Any reduction in modelling uncertainty.** The intake made the inputs traceable and fixed two
  derivation defects. It did not make the forecasts more likely to be right: ERCOT's 2025 LTLF
  still has ERCOT energy doubling by 2030, and that is ERCOT's judgement, now faithfully
  represented instead of faithfully mis-transcribed.
- **A CAISO growth band.** The CEC publishes load-modifier scenarios, not demand-growth ones. The
  Form 1.1c data-centre pair was tested as a band and rejected — at ~1.8 % of CAISO load it would
  have collapsed the axis, not represented it.

**The measured answer to "was it worth it", which is what the desk should carry.** The provenance
upgrade alone would have been a modest return on a large scope, and the desk's and SCN-WS4a's
recommendation to defer was reasonable on the evidence they had: **NYISO, the one row that had
already been properly derived, reproduced to four decimal places — so a lane that only re-derived
would have moved almost nothing.** What justified the ruling is what the desk could not have known
without doing it: the rows that had **not** been properly derived were wrong by up to 31 % of the
demand scalar, in a program whose headline question is what higher load does to emissions. The
owner's call was right, and it was right for a reason neither recommendation had identified.

---

## 8. Duties and deliverables

- **Matrix duty (rule 28).** No `ScenarioConfig` field added, so CI duty (c) does not fire. Duty
  (b) does not fire either: **no mechanism was tested.** `datacenter_load_block` and
  `electrification_path` are armed and adjudicated exactly as before; populating a constant that
  an already-armed mechanism reads changes no cell's verdict, evidence or posture. **No shard was
  stamped, deliberately** — the same call SCN-WS4a made and for the same reason.
- **Byte-identity.** **Every backcast keeper in every ISO is byte-identical** (growth scaling is
  a no-op at `year == weather_year`; both forecast-only axes are coerced off in backcast mode).
  Forecast-mode bundles in all six ISOs move — §6 item 2 has the exact scope for the epoch entry.
- **Tests.** `tests/curation/test_curate_load_forecast.py` (12, new — tmp-`CLEAN_DIR` fixtures,
  both intake routes, the vocabulary / metric-unit / duplicate-key guards, the registry contract);
  `tests/unit/data/test_datacenter.py` 40 passed; `tests/unit/data/test_electrification_layers.py`
  extended with the ERCOT EV profile's normalization and its rule-25 refusal for the other five
  ISOs. The full `tests/unit/config` + `tests/unit/data` + `tests/curation` surface is green
  (3,275 passed). Every re-pointed assertion now gates a **published fact** — that CAISO's high is
  a distinct higher case, that NYISO's and MISO's low cases are positive published forecasts, that
  ISO-NE's heat-pump trajectory is convex — rather than the arithmetic that produced it.
- **Rule 27 `[R-PUSH]`.** `constants.py` (5,045 lines) and `datacenter.py` (757) were edited in
  place and pushed as the exact on-disk bytes over `git push`; all eleven files ≥300 lines in the
  commit were **verified by fetch-back** against the remote blob (line count + sha256) before this
  document was written.
- **Data dictionary.** `data/dictionary/data-dictionary.md` regenerated via
  `scripts/render_data_dictionary.py`; the datatype registered in `scripts/regenerate_clean.py`
  and in the `test_clean_io` snapshot.
- **Scorecard.** Plan §5.1 Load-HI row and §2.4 G-L2 updated; ledger §3 to match.

---

## 9. Sources cited by this lane

- **ERCOT 2025 Long-Term Load Forecast** (posted 2025-04-08): `ErcotAdjustedForecast.xlsb`
  (hourly 8760 × 2025-2044 × 8 weather zones × 21 components),
  `2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx`, `Summer-and-Winter-Peaks.xlsx`,
  `ERCOT-Peak-Demand-Scenarios.xlsx`. Data-centre share of large load: ERCOT Board System
  Planning update Item 16.2 (Dec 2025), ~73 %.
- **CEC California Energy Demand 2025-2045** (2025 IEPR, adopted 2026-01-21): Forms 1.2, 1.5 for
  the Total State and the PGE/SCE/SDGE planning areas; **Form 1.1c Data Center allocations**,
  Planning Forecast and Local Reliability Scenario.
- **PJM 2026 Load Forecast Report** (posted 2026-01-14): `2026-load-report-data.xlsx` (monthly
  peak + energy per zone, 2026-2046); `total-load-adjustments-breakdown.xlsx` = **Table B-9b**.
- **NYISO 2026 Gold Book**: Table I-1a (NYCA energy/summer/winter, Lower/Baseline/Higher),
  Table I-11b (EV annual energy by zone), Table I-13a (building electrification annual energy by
  zone), Table I-14 (large load, incl. its Lower/Baseline/Higher/All-Loads footer), Table IV-7
  (load interconnection queue). Read from the existing corpus payload at
  `data/raw/NYISO/2026-Gold-Book-Public.pdf`, sha256-verified.
- **ISO-NE 2026 CELT Report** (2026-05-01): sheets 1.5.1, 1.5.2, 1.6, 1.7. Companion decks
  `heatfx2026final.pdf` and `transfx2026final.pdf` (Final 2026 Heat Pump / EV Forecasts) read for
  the EV hourly-shape question.
- **MISO 2026 Long-Term Load Forecast Results Summary** (LTLF Workshop 2026-04-13): slides 15, 16,
  18, 21, 24, 26.
