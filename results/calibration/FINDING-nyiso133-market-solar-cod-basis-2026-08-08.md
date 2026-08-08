# FINDING nyiso-133 — the commissioning-curve attribution is REFUTED; the defect is the in-service DATE basis

**Session nyiso-133, 2026-08-08.** Incumbent keeper `2026-08-08-nyiso-132-cf-arm`
(bundle `nyiso132_cf_arm`). Paired single-delta A/B, 2023–2025, both arms
registered:

* `2026-08-08-nyiso-133-cod-control` — bundle `nyiso133_cod_control`
* `2026-08-08-nyiso-133-cod-arm` — bundle `nyiso133_cod_arm`

Pre-registration: `PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md`.
Identification: `scripts/probes/_nyiso133_commissioning_ramp.py` →
`_nyiso133_commissioning_ramp.json`. Gate record: `_nyiso133_ab_gates.json`.

Rule 22 `[R-HOLDOUT]`: 2023–2025 only; the ACTIVE holdout spend freeze was
checked and nothing outside the training window was solved, scored or
registered.

---

## 1. THE QUEUE ITEM IS REFUTED BEFORE IT IS BUILT — no solve spent

nyiso-132 named its successor: *"THE MODEL HAS NO COMMISSIONING CURVE. The
monthly capacity ramp counts a plant fully from its in-service month, so one CF
cannot track a fleet whose realized CF runs 0.1468–0.1955."*

**Measured, nationally, before any mechanism was written.** 730 single-vintage
EIA-860 `OP` PV plants ≥ 5 MW (36.4 GW, COD 2019–2022) against their own
EIA-923 monthly metered history, two-way normalized — a mature-plant peer index
per calendar month × each plant's own permanent quality factor — so weather
years, curtailment growth, degradation and siting cannot contaminate it:

| age since COD | 0 mo | 1 mo | 2 mo | 3 mo | 6 mo | 11 mo | **placebo 36–47 mo** |
|---|--:|--:|--:|--:|--:|--:|--:|
| ratio to mature, cap-wt | **0.723** | **0.962** | 0.995 | 1.009 | 1.046 | 1.048 | **1.0072** |

The placebo calibrates the estimator at 1.007. **A new utility PV plant is at
mature output from its second month.** The entire commissioning shortfall is
**0.321 month-equivalents** of nameplate — ≈ **18 GWh** on NYISO's 399 MW 2024
build wave against a **+167 GWh** over-statement, i.e. **~11 % of the effect it
was named to explain.**

**A commissioning curve cannot be the cause, and none is built.** This is the
durable half of the session and it survives whatever happens to §3.

## 2. WHAT THE SAME MEASUREMENT FOUND INSTEAD

The Gold Book Table III-2a **"In-Service Date"** — the date the armed
`nyiso_solar_market_generator_basis` ramps each plant on — is a
**registration / interconnection-service date** and it **leads** the plant's
metered commercial start. **EIA-860's `Operating Month` matches that start.**

| plant | MW | Gold Book | EIA-860 | first metered (EIA-923) | lead |
|---|--:|---|---|---|--:|
| Morris Ridge Solar | 179.0 | 2024-09 | 2024-11 | **2024-11** | **+2** |
| High River Solar | 90.0 | 2024-07 | 2024-08 | **2024-08** | **+1** |
| East Point Solar | 50.0 | 2024-04 | 2024-05 | **2024-05** | **+1** |
| Calverton Solar | 22.9 | 2022-06 | 2022-08 | 2022-08 | +2 |
| Puckett / Janis / Grissom | 20.0 ea | — | — | matches EIA-860 | +1 |
| Long Island Solar Farm | 31.5 | 2011-11 | 2011-12 | (censored: E923 starts 2018) | +1 |
| Branscomb / Regan / Albany 1 / Pattersonville | 20.0 ea | — | — | — | 0 |
| Darby Solar | 20.0 | 2023-07 | 2023-06 | **2023-06** | **−1** |
| Stillwater Solar | 20.0 | 2024-02 | 2023-11 | **2023-12** | **−3** |

**EIA-860's month equals the first metered-output month in 11 of the 12
uncensored plants**, and the lead is **signed both ways** — two plants run the
other direction — so this is a basis difference, not a one-directional
correction toward the residual.

## 3. The lever, and its rule status

`ScenarioConfig.nyiso_solar_registry_cod_dates` (gated, default off,
byte-identical). The derive script emits **both** published bases as parallel
columns of the same artifact (`capacity_mw` / `capacity_mw_cod`); the loader
selects. **Membership and nameplate stay 100 % Gold Book** — only the month a
unit's capacity switches on moves.

* **Rule 14 `[R-ACCURATE]`** — the reconciled-real-data path: two published
  registries disagree on one field and a third published series adjudicates.
* **Rule 13 `[R-MEASURED]`** — an INPUT (when a plant existed), never an
  outcome; regenerates forward through EIA-860M's proposed→operating
  transition.
* **ZERO free parameters.** The crosswalk is a 15-row identity between two
  registries, each row verified on nameplate agreement and **dropped** — keeping
  its Gold Book date — rather than guessed when it fails (Albany County Solar 2
  is the one unmatched unit). DOF ledger **36 → 37 entries, `n_residual`
  UNCHANGED at 6**; the new entry's identification is `published`.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the re-derive trigger is the §2
  measurement, not a residual. Stated against interest: it makes 2023 **worse**.
* **Rule 25 `[R-ISO-SCOPE]`** — a NYISO-only artifact; the loader hard-errors on
  any other ISO. §1's national ramp is reported as a physical fact, never
  transferred as a parameter.

## 4. THE CONTROL REPRODUCES THE SUPERSEDED KEEPER EXACTLY

**Max |class-year energy delta| = 0.000 GWh** across 14 classes × 3 years. And
unlike nyiso-132 there is **no toolchain-drift excuse available**: this session's
environment matches the keeper bundle's recorded one exactly (Python 3.11.15,
highspy 1.15.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.5, pyarrow 25.0.0,
pydantic 2.13.4, same platform). The arm's entire delta is attributable to the
one armed field.

## 5. ALL SEVEN PRE-REGISTERED GATES PASS

| gate | result |
|---|---|
| **K1** config isolation | **PASS** — exactly ONE differing `scenario_config` field of 701, `nyiso_solar_registry_cod_dates` False → True |
| **K2** feasibility | **PASS** — zero slack, zero dump, both arms, all three years |
| **K3** liveness | **PASS** — arm/control solar energy **1.0118 / 0.8746 / 1.0000** against the ex-ante predictions **1.0118 / 0.8746 / 1.0000**, measured through `load_renewable_profiles` before the solve |
| **K4** scope | **PASS** — wind identical, 0.000 GWh in every year |
| **K5** gated-criterion regression | **PASS** — C1/C2/C3a/C3b/C4/C6/C8 all PASS in both arms |
| **K6** scarcity collapse | **PASS** — C3c 21 / 3 / 24 h in **both** arms, bit-unchanged |
| **K7** forcing budget | **PASS** — C8 PASS both arms; no share rises |

**Determination `CALIBRATED-WITH-CAVEATS` in both arms, all 8 criterion statuses
identical** (C3c the same lone ledgered caveat, budget 1 of 1).

| criterion | actual | control | **arm** |
|---|---:|---:|---:|
| C3a 2023 | 32.25 | 35.08 (+8.8 %) | **35.08 (+8.8 %)** |
| C3a 2024 | 38.13 | 38.40 (+0.7 %) | **38.44 (+0.8 %)** |
| C3a 2025 | 66.45 | 64.16 (−3.4 %) | **64.16 (−3.4 %)** |
| C3c 2023 / 2024 / 2025 | 10 / 12 / 42 h | 21 / 3 / 24 h | **21 / 3 / 24 h** |

Hourly grain, at full size: demand-weighted ΔLMP **−0.0023 / +0.0345 / 0.0000
$/MWh**, max zonal |ΔLMP| **4.55 / 5.67 / 0.00**. **2025 is BIT-IDENTICAL — zero
hours move** — which is the construction's own prediction (the 2025 registry is
flat and the two bases coincide), and the sharpest available check that nothing
leaked.

Class energy: 2024 solar **−84.06 GWh**, taken up by CC_REGULAR +41.94, ST_GAS
+21.28, CC_CHP +14.10, CT_PEAKER +3.50, ST_CHP +1.79. C1 moves four cells, all
staying PASS; **ST_GAS-2024 moves TOWARD its actual** (10.455 → 10.476 against
11.071) and **CC_REGULAR-2024 away** (38.445 → 38.487 against 38.039). C8
ST_GAS-2024 24.5 % → **24.4 %**.

## 6. WHAT IT BUYS AND WHAT IT COSTS — reported against interest

Solar against the published Gold Book Net Energy:

| year | published | control | **arm** |
|---|---:|---:|---:|
| 2023 | 229.9 GWh | 277.9 (+20.9 %) | **281.1 (+22.3 %)** |
| 2024 | 503.2 GWh | 670.2 (+33.2 %) | **586.1 (+16.5 %)** |
| 2025 | 981.8 GWh | 981.3 (−0.1 %) | **981.3 (−0.1 %)** |

**ADV-1 materialized exactly as pre-registered: 2023 gets worse.** It was
written into the prereg before the solve and expressly ruled out as grounds for
rejection — the band is `calibration_verdict.VRE_TOL`, explicitly report-only,
and D-10 classes NYISO solar `delivered_pinned` (*"advisory-only, excluded from
skill claims"*), so no gated criterion moves on it. Rule 1 `[R-STRUCT]` is the
reason it stays: a structurally-correct input is not rejected because a residual
moved the wrong way.

**The signature that this is a repair and not a fit** is not the level at all —
it is the **coherence**. The implied fleet CF the published energy demands goes
from **0.1629 / 0.1473** (adjacent years disagreeing by 10 %) to **0.1613 /
0.1641** (agreeing to 1.7 %). Nothing in the construction targets that quantity.

**A second cost, disclosed:** 2023 year-end registered capacity rises
**174.4 → 194.4 MW**, because Stillwater's EIA-860 month is 2023-11 and EIA-923
records it metering 745 MWh that December. `installed_mw` and the zone split
follow. That is the mechanism working, but it means "year-end capacity is
invariant" holds for 2024 and 2025 only.

## 7. THE SUCCESSOR THIS OPENS (rule 19 — named, not bundled)

After the date repair, 2023 and 2024 both imply **~0.162** against 2025's
**0.1955**. What remains is a **fleet-CF COMPOSITION** object, not a ramp one:
measured mature per-plant CF is **0.174–0.182** for the 2021–22 small fixed-tilt
NY8 units and **0.198–0.221** for the 2024 tracking plants (Morris Ridge 0.1998,
High River 0.1983, East Point 0.2207). A single ISO-wide `RENEWABLE_AVG_CF`
cannot track a fleet whose technology mix goes from 100 % fixed-tilt to 56 %
large tracking across the span. **Not this run's to close**, and it replaces the
refuted commissioning-curve item in the keeper's open-items list.

## 8. Also found, and repaired: a test that has been FAILING ON MAIN

`tests/test_nyiso_market_solar.py::test_flag_off_is_byte_identical_and_on_moves_only_solar`
asserts the armed 2024 market-solar energy at `approx(0.503, rel=0.10)` — NYISO's
published Net Energy. That was right when the ISO-wide CF was 0.15. **nyiso-132's
ungated re-level to 0.1955 made the quantity 0.670 TWh and the assertion was not
updated**, so the test has been red on `main` since that promotion. Confirmed
against `origin/main`'s own artifacts, not merely inferred. Repaired here to the
level the constant actually implies, with the published figure carried as the
reference it is measured against rather than a target the model is asserted to
meet.

## 9. Recommendation

**PROMOTE.** Structure improves (a registration date is replaced by the
commissioning date three published series agree on), **zero free parameters**,
`n_residual` unchanged at 6, **no gated criterion regresses**, the control
reproduces the superseded keeper exactly, and 2025 is bit-identical. The honest
counter is §6's 2023 advisory-band worsening, pre-registered and on a
report-only band for a pinned class.

**If it is promoted, the gate should be collapsed to unconditional** (rule 26
`[R-DELETE]`: a default-off gate whose "off" position is the less accurate basis
is a re-armable wrong answer). The gate was chosen to keep this A/B a clean
single delta and to avoid silently re-staling the NYISO forecast lane's
committed hindcast sidecars — an owner decision, flagged not taken.

Promotion is the owner's call; the keeper shard, the `complete` marker and the
matrix keeper stamp are untouched, and the matrix cell reads **`O`** — built and
adjudicated, armed on no keeper.
