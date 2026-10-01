# DIAGNOSIS — ERCOT-142 Phase 1: the C7 2023 COAL_LIGNITE diurnal-shape miss

**Date** 2026-07-30 · **ISO** ERCOT · **Lane** ercot142-coal-lignite-shape ·
**Phase 1 only — NO LP built, NO year solved, NO parameter changed** ·
**Keeper under test** `2026-07-30-ercot140-coal-peak-offer`
(bundle `results/calibration/ercot140_coal_peak_arm`) — **UNCHANGED** ·
**Queue item** `docs/mechanism-testing-matrix.md` §5.1 #3 (the coal dispatch-band
mechanism, ERCOT-117 §5.3's named successor: "→ C7 COAL_LIGNITE-2023 + the
±1.5 GW coal seasonal split. Needs a measured band identification (CAMPD
loading distributions), not a floor. Charter it on C7, never as an over-run
fix.") · **Reproduce** `scripts/probes/ercot142_lignite_shape_probe.py`

---

## 0. Result in one paragraph

C7's ERCOT failure is **one cell**, and it is **not** what the handoff's summary
line said. The keeper's own committed `legitimacy_diagnostics.json` records
exactly one D-1 failure — **`2023 COAL_LIGNITE: profile r 0.769 < 0.8`**. The
`cv_ratio` leg **passes** (0.535 against a 0.50 gate), and 2024/2025 pass both
legs comfortably (0.973/1.147 and 0.964/1.277). The miss is carried by **one
plant**, Oak Grove (EIA 6180, 1,795 MW = 70 % of the 2,554 MW lignite class),
in **one season** (fall 2023). The named "coal seasonal split" companion is
**refuted in its level form**. What the model actually gets wrong is the
**amplitude of lignite's price response**: Oak Grove's whole modelled offer
curve tops out at **$21.19/MWh**, *below* the ~$24 overnight clearing price, so
every MW of the plant is inframarginal in every night hour and it physically
cannot back down. The real plant, whose measured curve puts ~36 pp of capacity
in the **$17.5–$25** band, backs 700+ MW off overnight. **No mechanism is
promoted and no solve was spent**; Phase 2 is chartered and pre-registered
in §8.

---

## 1. The gate, read off the keeper's own artifact (not from the handoff)

D-1 gates (`legitimacy_diagnostics.json` → `gates`): `d1_min_profile_r` 0.80,
`d1_min_cv_ratio` 0.50, `d1_offpeak_last_hour` 14. `profile_r` is the Pearson
correlation of the **24-point hour-of-day mean profile**, model vs measured,
pooled over the whole year; `cv_ratio` is model/actual CV of that profile over
h0–h14.

| year | profile_r | model off-pk CV | actual off-pk CV | cv_ratio | verdict |
|---|---|---|---|---|---|
| 2023 | **0.769** | 0.031 | 0.057 | 0.535 | **FAIL** |
| 2024 | 0.973 | 0.020 | 0.018 | 1.147 | pass |
| 2025 | 0.964 | 0.030 | 0.023 | 1.277 | pass |

`failures` contains exactly one string: `2023 COAL_LIGNITE: profile r 0.769 <
0.8`. **Correction to the handoff brief**, which said C7 "fails on BOTH legs
(profile r 0.761, off-peak cv 0.561)": those figures are not in the keeper's
artifact, and `cv_ratio` 0.535 **clears** its gate — "far from 1.0" is not the
test. Only `profile_r` fails, and it fails by **0.031**.

**Basis check.** The class-aggregate reproduction used throughout this document
returns 0.769 / 0.973 / 0.964 — **exact** to the committed artifact — so the
miss is a class-shape property, not an artifact of D-1's per-plant pairing.

## 2. Where the miss lives: one season, then one plant

### 2.1 Seasonal decomposition (2023)

| season | r | cv_ratio | model CV | actual CV | model MW | actual MW | m/a |
|---|---|---|---|---|---|---|---|
| winter | 0.879 | 2.707 | 0.080 | 0.030 | 1,810 | 1,941 | 0.93 |
| spring | 0.932 | 1.740 | 0.054 | 0.031 | 1,694 | 1,595 | 1.06 |
| summer | 0.913 | 0.428 | 0.031 | 0.074 | 2,260 | 1,929 | 1.17 |
| **fall** | **0.745** | **0.110** | **0.014** | **0.128** | 2,002 | 1,699 | 1.18 |

Fall 2023 is the outlier on both legs: the model is nearly **dead flat**
(CV 0.014) against the year's **most** variable measured season (CV 0.128).

### 2.2 The "coal seasonal split" companion — REFUTED in its level form

The named hypothesis was that one annual coal passthrough/margin basis is being
asked to carry two seasonal regimes, distorting the pooled annual profile
through the seasonal **level** mix (model/actual 0.93 winter → 1.18 fall).
Tested directly by re-weighting each model season to the measured season's own
level and recomputing the annual profile correlation:

* baseline annual r **0.769**
* r after neutralising the seasonal LEVEL mix, shapes untouched → **0.738**

Neutralising the composition makes the gate **worse**, not better. The pooled
annual r is also *below* three of the four individual season r's, but that is a
shape effect, not a level-mix effect. **The seasonal-level split is not the
cause and is not a lever here.** (The *within*-season shape miss is real and is
what §3 onward pursues.)

### 2.3 One plant

Lignite is three plants: Oak Grove (6180, 1,795 MW), San Miguel (6183, 410 MW),
Major Oak / Twin Oaks (7030, 349 MW). Fall-2023 means:

| plant | model night h0-8 | actual night | model day h10-22 | actual day |
|---|---|---|---|---|
| **Oak Grove** | 1,541 (0.859 CF) | **1,022 (0.569 CF)** | 1,578 (0.879) | 1,468 (0.818) |
| San Miguel | 118 (0.288) | 117 (0.286) | 131 (0.320) | 131 (0.319) |
| Major Oak | 311 (0.890) | 290 (0.831) | 318 (0.912) | 293 (0.839) |

San Miguel matches to 1 MW; Major Oak to ~25 MW. **Oak Grove misses by 519 MW
at night** and is the entire defect.

The hourly trace is unambiguous — the model holds Oak Grove at a *constant*
1,508 MW for days on end while the real plant cycles:

```
2023-10-10  h00  model 1,508   actual   844
            h04  model 1,508   actual   808
            h08  model 1,508   actual   808
            h12  model 1,508   actual 1,490
            h18  model 1,508   actual 1,526
```

Value histograms confirm the regime difference: the model spends **30.7 %** of
2023 at a single value (1,706 MW = 0.950 CF); the measured plant is **bimodal**,
spending 5.6 % of hours at exactly **808 MW** with the rest at 0.86–0.94 CF.

## 3. Rule 19 [R-ONE-MECH] enumeration — everything that already floors or
prices COAL_LIGNITE is MEASURED-CORRECT

Taken from the keeper's own committed artifacts, not from memory.

**(a) The floor is right, and is not binding.** D-2 attributes exactly one
mechanism to class COAL: `coal_min_config`, 3.95/3.77/2.13 TWh
(6.35/6.07/3.20 % of class energy). `COAL_MUSTRUN_BY_PLANT[6180] = 45.0` ⇒
808 MW — **exactly the measured overnight floor the real plant sits on**
(808 MW appears 493 times in 2023). The constant is *correct*. It is also **not
the pin**: the model sits at 1,541 MW at night, ~730 MW *above* it, and is
at/below it in only **0.9 %** of fall-2023 night hours against the real plant's
**40.5 %**. The model's problem is that it never *descends* to a floor that is
already correctly placed. **A floor cannot fix this** — ERCOT-128 established
the same result for the min-load family ("the defect is over-flatness … a
uniform lower bound can only flatten further"), and ERCOT-130 refuted the
matching upper bound.

**(b) The fuel price is right.** Oak Grove and Major Oak carry **zero** EIA-923
Schedule-5 delivered-cost rows in any year — both are mine-mouth lignite
(captive adjacent mine, no arms-length receipts), so they fall back to
`LIGNITE_PRICE_2023_25 = 1.45 $/MMBtu`. That constant checks out against the
**EIA Annual Coal Report** f.o.b.-mine series already in-repo
(`data/raw/coal-prices/eia_coal_price_by_rank.part*.csv`): Texas lignite 2023 =
**$18.76/ton ÷ 13.30 MMBtu/ton = $1.411/MMBtu**, i.e. the model is **+2.8 %**,
and mine-mouth means no transport to add (`COAL_TRANSPORT` lignite share 1.00 =
commodity). West-South-Central corroborates at 1.432 (2023) / 1.498 (2024).
**Rule 14 [R-ACCURATE] licenses no change here.** San Miguel's F923 cost
($3.51/3.56/3.97) is **not** a valid donor — it is a small, old, captive-lignite
unit with its own coal quality and economics, and using it would be exactly the
cross-plant misalignment rule 14's exception clause warns about.

**(c) The offer LEVEL is right.** ERCOT-138 measured the model's coal
committed/econ bands at **−1.6…+3.9 $/MWh** against the fleet's own SCED TPO
conduct through the crossing band, and closed further coal offer levers *for the
gas residual*. ERCOT-137 put the must-run block on its measured net-margin form;
ERCOT-140 put the `_peak` tranche on its measured top-decile level. Nothing in
this lane re-opens any of those.

## 4. Two hypotheses tested and REFUTED along the way (recorded so they are not
re-run)

**(i) Daily unit-commitment (one of two units off overnight).** 808 MW ≈ one of
Oak Grove's two ~915 MW units, which made a one-unit-off cycle the obvious
reading. **Refuted at unit grain** (`data/raw/campd-unit-level/TX_2023.parquet`):
in fall 2023 *both* units stay online — online share 95.2 %/95.1 % (unit 1,
night/day) and 94.6 %/95.6 % (unit 2) — and *both back down together*
(unit 1 845→561 MW, unit 2 819→598 MW). This is **continuous turndown, not
commitment**, which matters because it is squarely LP-expressible: the
ERCOT-127/128 "commitment state is unavailable in pure LP" blocker **does not
apply** to this defect.

**(ii) "The real plant isn't price-following."** A first pass compared the price
in the plant's floor hours against its high hours and found almost no separation
(model $24.34 vs $24.74; real RT HB_NORTH $19.13 vs $21.52) — which reads as a
non-price driver. **That test was wrong**: Pearson-on-levels against an ERCOT
price series that swings 0.35→3.48 within a day and spikes past $1,000 is
outlier-dominated. The robust re-test (Spearman, within-day so the day-level
effect is removed) reverses it:

| fall | REAL within-day ρ | MODEL within-day ρ |
|---|---|---|
| 2023 | **0.446** | 0.568 |
| 2024 | 0.208 | 0.700 |
| 2025 | 0.217 | 0.484 |

The real plant **is** price-following, and it follows *twice as strongly* in
2023 as in 2024/2025. So the mechanism class is price response after all — the
model's failure is one of **amplitude**, not direction or presence.

## 5. Why the three years look like different regimes — and why that does NOT
need a year-specific driver

Measured Oak Grove day-minus-night CF gap:

| year | winter | spring | summer | fall | annual |
|---|---|---|---|---|---|
| 2023 | 0.018 | 0.052 | 0.144 | **0.248** | +0.117 |
| 2024 | −0.019 | 0.060 | 0.072 | 0.008 | +0.029 |
| 2025 | −0.018 | −0.012 | 0.010 | −0.008 | −0.007 |

This looked like a rule-13 trap: a behaviour present in 2023 and absent (even
inverted) later, with every obvious driver pointing the wrong way — delivered
lignite cost is flat/falling into 2023, gas was **cheapest** in 2024 ($2.19 vs
$2.54/$3.52) when cycling *stopped*, and solar/wind growth is monotone. The
plant's at-floor share is also **higher** in the flat years (11.7 % in 2023 vs
17.4 %/16.6 %), so it is not a level effect.

**The resolution is that the driver is the price shape itself**, which the model
already carries. Measured HB_NORTH fall hour-of-day price profile, normalised:

| year | mean | trough | peak | peak/trough |
|---|---|---|---|---|
| 2023 | $47.10 | 0.35 | 3.48 | **9.9×** |
| 2024 | $26.00 | 0.54 | 2.55 | 4.7× |
| 2025 | $30.94 | 0.56 | 2.04 | 3.6× |

Fall 2023's diurnal price swing is **2–3× wider** than 2024/2025's. A single,
year-invariant offer curve with the correct slope therefore produces a **large**
turndown in 2023 and a **small** one in 2025 — reproducing both regimes from
each year's own prices, with **no year-specific parameter**. That is what makes
a Phase-2 arm rule-13 admissible; it is also the reason the model, whose curve
has no slope in the relevant band, is flat in *all* three years.

## 6. The mechanism, identified from measured conduct

**The model's Oak Grove offer curve does not reach the overnight price.**
From `results/calibration/ercot135_coal_merit_order.json` (`A_model_offer`;
ercot135-vintage, so pre-ercot137/140 in *level* — cited for **structure**, and
Phase 2 must re-measure it on the current keeper):

| plant | bottom | cap-wtd | **top** | spread | fuel | HR |
|---|---|---|---|---|---|---|
| Oak Grove | $4.50 | $11.32 | **$21.19** | $16.69 | 1.450 | 10.283 |
| Major Oak | $4.50 | $11.80 | $22.37 | $17.87 | 1.450 | 11.009 |
| San Miguel | $4.50 | $20.41 | $52.24 | $47.74 | 3.473 | 11.999 |

The model's fall-2023 overnight North-zone price is **$24.34** (p50). Oak
Grove's **entire** curve — every tranche — sits below it. No LP can back the
plant down, and this is exactly why San Miguel (whose curve spans $4.50–$52.24
and straddles the price) tracks its measured shape to 1 MW while Oak Grove does
not.

**The measured target.** The `ercot136_coal_headroom_conduct.json` `B2_supply_grid`
(SCED TPO, floored convention, 2024 control) gives the real coal fleet's own
offered supply curve:

| ≤$0 | ≤$10 | ≤$15 | ≤$17.5 | ≤$20 | ≤$25 | ≤$30 | ≤$40 |
|---|---|---|---|---|---|---|---|
| 0.430 | 0.487 | 0.507 | 0.563 | 0.673 | 0.920 | 0.929 | 0.949 |

~43 % at ≤$0 (the min-load block), then flat to ~$17.5, then a **steep segment
carrying 35.7 pp of capacity between $17.5 and $25** — straddling precisely the
overnight clearing price. **This is the "measured band identification (CAMPD
loading distributions), not a floor" that queue item 3 asked for**, and it is
the slope the model's lignite lacks. It is a *shape* object: ERCOT-138
exonerated the committed/econ bands on **level** at p10–p75 quantiles, which a
curve can pass while still having the wrong slope.

## 7. Feasibility bounds — what any such mechanism could buy (ex ante, no solve)

Energy-preserving reshaping of the keeper's own Oak Grove series, one shared
parameter across all three years, class `profile_r` recomputed on the gate's
basis. Nothing here is adopted; it bounds Phase 2 and pre-registers its risk.

*Price-keyed form* (back toward the 0.45 floor in the k cheapest hours of each
day, by the model's own North price):

| k | depth | 2023 | 2024 | 2025 | all pass |
|---|---|---|---|---|---|
| 6 | 0.25 | 0.841 | 0.976 | 0.933 | **YES** |
| 8 | 0.25 | 0.885 | 0.973 | 0.916 | **YES** |
| 8 | 0.50 | 0.912 | 0.959 | 0.859 | **YES** |
| 10 | 0.50 | 0.944 | 0.961 | 0.834 | **YES** |
| 10 | 1.00 | 0.958 | 0.941 | 0.769 | no |

**A feasible window exists and it is wide.** But it is bounded on both sides:
too little does nothing, and **too much breaks 2025** (which currently passes at
0.964). 2025 is the binding guard, because its measured plant barely cycles at
all — that is the single most important pre-registered risk for Phase 2.

## 8. Phase 2 — chartered, pre-registered, NOT executed here

Phase 2 is a separate session (this is the ERCOT-138 → ERCOT-139 split, the
lane's own established pattern). It must:

1. **Re-measure** Oak Grove's / lignite's offer curve **on the current ercot140
   keeper** — the §6 table is ercot135-vintage and is structure-only evidence.
2. **Identify the slope from `B2_supply_grid`**, expressed at the shared gas
   anchor, exactly as ERCOT-137/140 identified their levels. **Zero swept
   parameters** — the §7 sweep is a feasibility bound, and adopting any of its
   (k, depth) values would be rule-13 residual tuning and a rule-21 DOF
   addition. If no non-fitted identification survives, the lane closes.
3. Land as a **rule-19 REPLACEMENT** of whatever prices the lignite mid-band
   today, never a fourth surface stacked on it.
4. Pre-register **2025 `profile_r` ≥ 0.80 as a hard kill** (§7), plus the
   standing zero-spurious / C3c-no-drain / C1-C2-held guards, and score the
   mechanism leave-one-year-out within 2023–2025.
5. Carry its `ScenarioConfig` field with `_CACHE_KEY_OPTIONAL_FIELDS`
   registration, all six wiring seams, and its matrix row in the same PR
   (rules 24/26c).

**Expected value, stated honestly.** The prize is one C7 cell, 0.031 short of
its gate. It does **not** touch C3a/C3b/C3c, which are the keeper's other three
fails and are a different (gas-side/tail) object. A Phase 2 that clears C7 takes
the ERCOT fail set from **{C3a, C3b, C3c, C7} → {C3a, C3b, C3c}** and does not
by itself produce a determination (C6 remains UNATTESTED on 8
residual-identified DOF entries). It should be sequenced accordingly.

## 9. Governance

* **No LP built, no year solved, no parameter changed, keeper UNCHANGED**
  (`2026-07-30-ercot140-coal-peak-offer`). No dashboard run registered because
  no run was produced — the ERCOT-117 / ERCOT-130 / miso-107 / caiso-140
  precedent for a Phase-1 adjudication.
* **Holdouts (rule 22 [R-HOLDOUT])** — 2023/2024/2025 only. No 2022, 2019,
  ≤2021 or H1-2026 data was solved, scored or read.
* **ERCOT-scoped (rule 25 [R-ISO-SCOPE])** — no other ISO's files touched.
* **Rules 13/14 [R-MEASURED]/[R-ACCURATE]** — all measured conduct here is read
  as driver evidence and diagnosis. Nothing is fed back as an answer key; no
  offer curve, sigmoid, derive value or measured parameter was changed
  (rules 21/23 [R-FROZEN-DERIVE]).
* **Matrix (rule 26b)** — the `coal_min_load_floor` row's ERCOT cell carries
  this adjudication (it is the coal dispatch-band/min-load family's row);
  §5.1 queue item 3 is re-stamped with the Phase-1 result and the Phase-2
  charter. No new `ScenarioConfig` field, so no new row (rule 26c n/a).
* **CLOSED, not re-opened** — the C3a trough lane (ERCOT-141, closed
  end-to-end), the CC committed band, the coal side of the coal-vs-gas ranking
  (ERCOT-138), the reserve-side scarcity family (ERCOT-107/108), the
  West/Panhandle topology split (ERCOT-117). P2 is ARCHIVED and unused.
* **Pre-existing conditions matched, NOT fixed** — `audit_keepers` reports
  `status/NEISO.js` stale (another ISO's lane); the `nyiso_import_sil_retire`
  `_CACHE_KEY_OPTIONAL_FIELDS` gap on `main` (NYISO's lane; default key verified
  unmoved at `2c8098e8e1684c7d` for this session's preconditions).

## 10. Open owner rulings carried forward (surfaced, not decided)

1. **Carried from ERCOT-137/138/139/141, still open:** delete outright vs leave
   inert the retired `coal_tranche_1_fuel_passthrough` pricing path and the
   legacy non-CAMPD `split_coal_tranches` `_t1/_t2/_t3` path (rule 26
   [R-DELETE]).
2. **Carried from ERCOT-138 §7.2, still open:** `ercot_offer_hrmult_ep_rebasis`
   and `_bands` are solve-affecting `ScenarioConfig` fields with **no
   mechanism-matrix row** — a rule-26(c) gap now predating six lanes.
3. **Carried from ERCOT-141, still open, NYISO's lane:**
   `nyiso_import_sil_retire` (PR #3136) is missing from
   `_CACHE_KEY_OPTIONAL_FIELDS`, which moved the default cache key
   `603c2498bf71d21d → 2c8098e8e1684c7d`, orphaning on-disk caches and failing
   5 pinned tests on a clean `main`. Needs an owner-assigned NYISO session;
   `scripts/check_cache_key_registration.py` warns that re-pinning the test
   literal is the WRONG fix.
