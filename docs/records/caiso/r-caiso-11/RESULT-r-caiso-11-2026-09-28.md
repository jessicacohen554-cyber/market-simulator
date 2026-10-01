# RESULT — R-CAISO-11 (2026-09-28): the evening under-price census, and the TAC-share clock fix

**Promoted:** `2026-09-28-caiso-r11-tacpst` (bundle `rcaiso11_A_span`, 2022–25), CALIBRATED with a single ledgered C3c for 2024. The 2019–21 fold is `2026-09-28-caiso-r11-tacpst-touchpoints` (bundle `rcaiso11_A_tp_2019_2021`), stamped to the keeper and still NOT-YET.

**Pruned (rule 35):** `2026-09-28-caiso-r10-nosa` and its fold. The year union 2019–2025 is unchanged.

**Owner decision cards (2026-09-28):**
- TAC clock: "Fix + solve now". Delivered in §7.
- PS wall: "Keep wall". Nothing was armed on the pumped-storage object.

**Record:** the analysis in §1–§6 is zero LP. The one solve is §7.

**Inputs:** the keeper's per-year legs, extracted locally from the R-CAISO-10 shard commits. These are gitignored under rule 31, and the SHAs below are provenance only (rule 33(d)).

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Leg SHA | `1d45e9dd` | `3598231f` | `13738fa1` | `8a16c43d` | `c6093da3` | `2ec156dc` | `7f84a4fd` |

**Probes:**
- `scripts/probes/_rcaiso11_object1_dual_census.py` → `results/calibration/_rcaiso11/object1_dual_census.json`
- `scripts/probes/_rcaiso11_ps_boundary_footprint.py` → `.../ps_boundary_footprint.json`

## 1. Where the evening gap sits

SP15_rest mean price ($/MWh) by hour of day, all days:

| hod | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2024 model | 31 | 40 | 44 | 44 | 44 | 44 | 44 | 42 |
| 2024 DAM | 39 | 57 | 67 | 57 | 51 | 48 | 44 | 42 |
| 2023 model | 58 | 67 | 70 | 71 | 70 | 69 | 67 | 65 |
| 2023 DAM | 71 | 96 | 110 | 95 | 83 | 73 | 66 | 61 |

- The gap is the **h16–19 ramp peak**. By h21–23 the model and DAM agree.
- The model prints a **flat plateau** from h18 onward. That is the signature of an intertemporal resource (storage or hydro) sitting interior across those hours.
- The daily evening/midday price ratio is 1.37–1.48 in the model against 1.75–3.0 in DAM (2022–25).

## 2. The three candidates the handoff named

| Candidate | Finding | Status |
|---|---|---|
| Evening reserve product | `reserve_price` is **$0 in every hour of every year** | Already closed: caiso-144 proved the co-opt inert (energy_reserve_coopt `I`) |
| Battery SOC dual | The fleet is interior. It is empty after the evening on only 14–30 % of days, full before it on ≤ 3.6 % of days, and at its observed power maximum in ≤ 0.5 % of evening hours | The battery never binds, so it propagates a level rather than setting it |
| Import ladder | h18–21, every year and both seasons: model imports are **0.4–4.1 GW below** EIA-930 | A symptom. Imports are priced out by a low evening |

**Battery timing against measured data** (CAISO Outlook "Total batteries", `storage-dispatch-actuals`):
- The model discharges about **1 h late**. In 2024 it is still net charging at h16 (−0.18 GW against +1.25 GW measured) and over-discharges at h20–23.
- Annual discharge is 11–13 % below measured in 2024–25 (7.49 vs 8.39 TWh; 10.82 vs 12.48 TWh).

## 3. The like-for-like hydro correction (R-CAISO-10's "shape matches" was apples to oranges)

EIA-930 CISO `NG: WAT` **folds pumped storage**: discharge adds to it and pumping subtracts. R-CAISO-10 compared **conventional hydro alone** against it. On the matched boundary (model conventional hydro + PS net):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|
| Evening h17–22, joint − WAT (GW) | **+0.47** | +0.43 | +0.47 | +0.28 | +0.47 |
| Midday h8–16, joint − WAT (GW) | −0.43 | −0.53 | −0.66 | −0.44 | −0.87 |
| Evening/mean: conventional only | 1.82 | 1.64 | 1.43 | 1.38 | 1.41 |
| Evening/mean: conventional + PS | 2.04 | 1.86 | 1.62 | 1.54 | 1.67 |
| Evening/mean: EIA-930 WAT | 1.62 | 1.55 | 1.41 | 1.36 | 1.42 |

- The model shifts **0.3–0.5 GW more** from midday into the evening than the measured water+PS object. It does so in every year, and in the price-bias direction on both ends (midday too high, evening too low).
- The monthly budget pins conventional hydro to the folded WAT, which already carries PS's shift. The explicit PS column then shifts again.
- 2021 also over-concentrates *conventional* hydro (1.82 vs 1.62), which is the R-CAISO-10 Object-2 excess. In 2023–25 conventional hydro alone matches.

**The admissible zero-parameter instrument is INERT.** It would apply the existing WAT envelope to the joint conventional + PS aggregate: no WAT split, no PS proxy.
- The joint aggregate **exceeds the envelope in 0 hours in every year 2019–25**.
- When conventional hydro is at its envelope (2024: 660 evening hours), PS discharges 7 MW on average (> 1 MW in 21 of them). The LP already substitutes the two.
- The excess lives in hours where conventional hydro is *below* its cap and PS fills in. Only a PS shape restraint reaches those hours, and that is the owner-ledgered **caiso-141/145 wall** (caiso-168 §8 item 4). **Not solved; reported.**
- Two claims in `envelopes.py`'s docstring are wrong in part and are left for the owner's ruling. It calls the PS-fold envelope "generous … only weakens the cap". It is generous in the evening, but pumping lowers WAT at midday, so there the cap is *tighter* than the conventional fleet's own.

## 4. A separate data defect found (real, small)

`scripts/data/curate_zonal_shares.py::parse_caiso_shares` maps OASIS `interval_start_gmt` to the hour of year via `tz_convert("America/Los_Angeles")`, which is **prevailing** time. The model clock and the EIA-930 system total are **PST (UTC−8)**. In DST months the zonal shares therefore land **1 h late** against the total.

This is also the runtime path: `zonal_shares._zonal_shares_from_raw` calls it whenever `data/clean` is absent, which includes every shard.

Measured effect of re-parsing on `Etc/GMT+8`, total load unchanged, Apr–Oct:

| | Mean shift h16–17 | Max single hour |
|---|---|---|
| LA_BASIN → NP15 | 0.2–0.45 GW | 1.5 GW |
| SDGE | +0.1–0.18 GW | — |

Price effect unmeasured (needs an LP). It sits well below the $10–20 evening gap, so it is not the root cause. It is still a rule 14 defect.

## 5. Dead ends checked this session (so no one re-runs them)

- **Demand clock.** Raw EIA-930 CISO `Demand` lags 1 h before 2023-11-01. The keeper already arms `caiso_demand_clock_realign` and `caiso_supply_consistent_demand`, so the model is right and the raw series is not.
- **2019-10 to 2020-08 WAT hole.** This was my own masking artifact, not a model defect. `caiso_hydro_backfill` is live: model hydro is 29.2 TWh (2019) and 16.2 TWh (2020), matching the repaired budget month by month.

## 6. What remains (for R-CAISO-12)

- **h15–17 import surplus.** In Jun–Sep 2022–25 the model imports **+1.0–2.1 GW** more than EIA-930 and runs **3–5 GW less gas**. This is where the ramp peak is lost. Check it against the DO-NOT-REDO list before proposing anything; the per-corridor firm-shape idea is excluded.
- **Owner rulings:** the TAC-share clock fix and the PS wall (decision cards, this session).

## 7. The arm: `caiso_tac_shares_standard_time` (PRECOMMIT-r-caiso-11)

**Solve.** One shard per year at pin `9005dc81`, composed at zero LP.

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Leg SHA (provenance) | `d12cd909` | `80e94bf7` | `f8519043` | `05cc2f8c` | `b719a2f3` | `e8b23b12` | `56268443` |

**Verdict.** No criterion changes status in any year, span or fold. G-DRIFT: every non-arm hunk INERT (PRECOMMIT §2).

**Span 2022–25, keeper → arm:**

| Metric | 2022 | 2023 | 2024 | 2025 | Actual (2022/23/24/25) |
|---|--:|--:|--:|--:|---|
| Mean price ($/MWh) | 91.81 → 91.77 | 57.63 → 57.62 | 36.41 → 36.41 | 36.79 → 36.78 | 84.49 / 54.17 / 34.65 / 34.42 |
| C4 gas NRMSE | 0.262 | 0.247 | 0.254 | 0.294 | — |
| CC_REGULAR (TWh) | 54.054 → 54.085 | 51.995 → 52.004 | 46.693 → 46.710 | 39.921 → 39.931 | — |
| C3c hours > $200 | 515 → 513 | 59 | 0 | 0 | RT 510 / 47 / 35 / 8 |

C4 is unchanged in every year; C3c changes only in 2022.

**SP15_rest h17–22 ($/MWh):** 109.69 → 109.54 (2022), 69.00 → 68.97 (2023), 43.42 → 43.39 (2024), 42.77 → 42.75 (2025). As §4 predicted, the fix does not close the evening gap.

**Fold 2019–21:**
- C1 CC_REGULAR 59.12 / 68.38 / 59.74 TWh against actual 36.07 / 43.14 / 49.16.
- C4 0.570 / 0.529 / 0.382.
- C3a 2021 57.09 against 50.87.
- C3c 2021 87 h.
- It stays NOT-YET and is reported only (rule 30(c)).

**Promotion basis.** A structural correctness fix (rule 1 / rule 14) that the pre-registered rule admits. It is not a residual improvement: the residual barely moves, and that is the expected size.

## Retrievability (rule 34(e))

- **On `main`:** the keeper composites `rcaiso11_A_span` and `rcaiso11_A_tp_2019_2021` in the registered keeper shape (class / class_band / storage / system hourlies, meta, metrics, attestation, legitimacy), plus the registry sidecars and run payloads.
- **Not on `main`:** the per-year legs (with dispatch / unit_hourly) are local only and gitignored. Their shard-branch SHAs are provenance only (rule 33(d)). Any unit-level question needs a re-solve (~25 min per year).
