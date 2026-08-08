# PREREG nyiso-133 — the NYISO market-solar in-service DATE basis

**Session nyiso-133, 2026-08-08.** Written **before** any mechanism code and
**before** any solve. Incumbent keeper `2026-08-08-nyiso-132-cf-arm` (bundle
`nyiso132_cf_arm`), determination `CALIBRATED-WITH-CAVEATS`, C3c the sole
non-passing criterion under the owner's ledgered caveat (budget 1 of 1).

Rule 22 `[R-HOLDOUT]`: **2023–2025 only.** The holdout spend freeze is ACTIVE and
outranks NYISO's `complete` marker; no out-of-training year is solved, scored or
registered here.

---

## 1. The queue item, and why it is RE-POINTED before it is tested

Lever-queue item 2 was opened by nyiso-132 and reads, verbatim:

> **THE MODEL HAS NO COMMISSIONING CURVE.** The monthly capacity ramp counts a
> plant fully from its in-service month, so one CF cannot track a fleet whose
> realized CF runs 0.1468–0.1955.
> (`FINDING-nyiso132-solar-cf-level-2026-08-07.md` §5)

**That attribution is REFUTED by measurement, ex ante, with no solve spent**
(probe `scripts/probes/_nyiso133_commissioning_ramp.py`, record
`results/calibration/_nyiso133_commissioning_ramp.json`).

Measurement (A), the **national** utility-scale PV commissioning ramp: 730
single-vintage EIA-860 `OP` PV plants ≥ 5 MW, 36.4 GW, COD years 2019–2022,
against their own EIA-923 monthly metered history, two-way normalized (a
mature-plant peer index per calendar month × each plant's own permanent quality
factor, so weather years, curtailment growth, degradation and siting cannot
contaminate it):

| age since COD | 0 mo | 1 mo | 2 mo | 3 mo | 6 mo | 11 mo | placebo 36–47 mo |
|---|--:|--:|--:|--:|--:|--:|--:|
| ratio to mature (cap-wt) | **0.723** | **0.962** | 0.995 | 1.009 | 1.046 | 1.048 | **1.0072** |

The placebo calibrates the estimator at 1.007. **A new PV plant is at mature
output from its second month**; the entire commissioning shortfall is
**0.321 month-equivalents** of one plant's nameplate — for NYISO's 2024 build
wave (399 MW) worth **≈ 18 GWh**, against a **+167 GWh** over-statement. A
commissioning curve cannot be the cause: it is ~11 % of the effect it was named
to explain.

## 2. What the measurement found instead — the DATE BASIS

Measurement (B). The keeper's armed `nyiso_solar_market_generator_basis` reads
NYISO's Gold Book Table III-2a registry and starts each plant's capacity in its
published **in-service month**. That date is a registration/interconnection
date, and it **leads** the plant's metered commercial start:

| plant | MW | Gold Book | EIA-860 `Operating` | first metered output | lead |
|---|--:|---|---|---|--:|
| Morris Ridge Solar | 179.0 | 2024-09 | 2024-11 | **2024-11** | **+2** |
| High River Solar | 90.0 | 2024-07 | 2024-08 | **2024-08** | **+1** |
| East Point Solar | 50.0 | 2024-04 | 2024-05 | **2024-05** | **+1** |
| Calverton Solar | 22.9 | 2022-06 | 2022-08 | 2022-08 | +2 |
| Puckett / Janis / Grissom | 20.0 ea | — | — | — | +1 |
| Long Island Solar Farm | 31.5 | 2011-11 | 2011-12 | (censored, E923 starts 2018) | +1 |
| Branscomb / Regan / Albany 1 / Pattersonville | 20.0 ea | — | — | — | 0 |
| Darby Solar | 20.0 | 2023-07 | 2023-06 | 2023-06 | **−1** |
| Stillwater Solar | 20.0 | 2024-02 | 2023-11 | 2023-12 | **−3** |

**EIA-860's `Operating Month` equals the first metered-output month in 11 of the
12 uncensored cases** (Branscomb and Albany County 1 are one month early; Albany
County Solar 2 has no separate EIA-860 record and is not crosswalked). The lead
is **signed both ways** — two plants run the other direction — so this is a
basis difference, not a one-directional correction toward the target.

## 3. The lever, and its rule status

Swap the **date** column only, plant by plant, to EIA-860's capacity-weighted
`Operating Year`/`Operating Month` where the plant is crosswalked; keep the Gold
Book date where it is not. **Membership and nameplate stay 100 % Gold Book** —
that identification (a NY solar plant is a NYISO grid resource *iff* NYISO
registers it in Table III-2a) has no substitute and is untouched.

* **Rule 14 `[R-ACCURATE]`** — two published registries disagree on one field
  and a third published series (EIA-923 metered output) adjudicates which is
  right. This is the rule's named *reconciled-real-data* path, not a guess.
* **Rule 13 `[R-MEASURED]`** — an INPUT (when a plant existed), never an
  outcome. EIA-860 `Operating Month` exists for forward years through EIA-860M's
  proposed→operating transition, so it regenerates and responds.
* **ZERO free parameters.** No percentile, threshold, lag or scalar. The
  crosswalk is a 15-row identity between two registries for the same physical
  plants, each row verified on nameplate agreement (±25 %) and dropped, not
  guessed, when it fails.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the re-derive trigger is the measured
  identification in §2, **not** a residual. Stated against interest: the repair
  makes 2023 **worse** (§4).
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO's own registry only. Measurement (A) is
  national and is reported as a physical fact, not transferred as a parameter.

**Construction: GATED**, `ScenarioConfig.nyiso_solar_registry_cod_dates`, default
`False` (byte-identical off). Chosen over nyiso-132's ungated `constants.py`
pattern for two reasons stated before the result is known: (i) it makes the A/B a
clean single-delta with the standard K1 gate rather than the inverted tree
harness, and (ii) it does **not** silently re-stale the NYISO forecast lane's 11
committed hindcast sidecars — the declared blast radius that nyiso-132's ungated
choice left open as a cross-lane item. The rule 26 `[R-DELETE]` tension is
acknowledged: a default-off gate whose "off" position is the less accurate date
basis is a re-armable wrong answer, so **if this is promoted the gate should be
collapsed to unconditional** — flagged here as an owner decision, not taken.

## 4. Ex-ante prediction (measurement C) — stated before the solve

Model energy at the keeper's armed CF (0.1955) against the Gold Book's own
published Net Energy:

| year | published | gold-book basis (control) | **EIA-860 basis (arm)** |
|---|--:|--:|--:|
| 2023 | 229.9 GWh | 275.8 (**+20.0 %**) | **278.7 (+21.2 %)** |
| 2024 | 503.2 GWh | 667.7 (**+32.7 %**) | **599.5 (+19.1 %)** |
| 2025 | 981.8 GWh | 982.0 (**+0.0 %**) | **982.0 (+0.0 %)** |

Mean-monthly registered capacity moves **161.07 → 162.73 MW (2023, +1.0 %)**,
**389.90 → 350.07 MW (2024, −10.2 %)**, **573.4 → 573.4 (2025, unchanged)**.

**The signature that this is a real repair and not a fit:** the implied fleet CF
the published energy demands becomes **coherent across the two ramp years** —
0.1629 / 0.1473 (incoherent, a 10 % gap between adjacent years) → **0.1613 /
0.1641** (agreeing to 1.7 %). Nothing in the construction targets that.

**ADV-1 (pre-registered, EXPECTED TO MATERIALIZE).** The 2023 advisory VRE band
gets **worse**, +20.0 % → +21.2 %. This is **not** grounds for rejection: the
band is `calibration_verdict.VRE_TOL`, explicitly report-only, D-10 classes
NYISO solar `delivered_pinned` (*"advisory-only, excluded from skill claims"*),
and rule 1 `[R-STRUCT]` forbids rejecting a structurally-correct input because a
residual moved the wrong way. It is recorded here so it cannot be presented
later as a surprise.

**ADV-2.** 2024 solar falls ≈ 68 GWh, ≈ 0.05 % of NYISO load. C3a-2024 (+0.71 %)
should move upward by well under a point; a move past +10 % would falsify the
sizing and is a kill (K5).

**ADV-3.** Less 2024 solar can only add scarcity hours, and C3c-2024 is
under-produced (3 h vs 12). A DECREASE in the 2024 tail would be unexpected.

### 4a. Construction addendum — measured after the code was built, before the solve

Three things the §4 arithmetic (flat monthly capacity) did not capture, recorded
here so they are pre-solve statements and not post-hoc explanations:

1. **The energy ratio is not the capacity ratio.** Through the actual model path
   (`load_renewable_profiles`), 2024 solar energy moves **670.2 → 586.1 GWh, a
   ratio of 0.875**, below the flat mean-monthly capacity ratio of 0.898 —
   because the re-timed months are not CF-neutral: Morris Ridge's +2-month shift
   removes 179 MW from September and October, whose solar CF sits above the
   annual mean. Measured errors against the published Net Energy are therefore
   **+20.9 → +22.3 % (2023)**, **+33.2 → +16.5 % (2024)**, **−0.1 → −0.1 %
   (2025)** — 2024 improves more than §4 predicted, 2023 worsens slightly more.
   K3 is still measured on the **capacity** ratio (1.010 / 0.898 / 1.000), which
   is the quantity the artifact controls directly.
2. **2023 year-end solar capacity RISES 174.4 → 194.4 MW.** Stillwater Solar's
   EIA-860 `Operating Month` is 2023-11 against a Gold Book 2024-02, and EIA-923
   records it metering 745 MWh in December 2023, so on the measured basis its
   20 MW belongs to the 2023 year-end fleet. `installed_mw` and the zone split
   follow. This is the mechanism working, not a leak — but it means the "year-end
   capacity is invariant" statement holds for 2024 and 2025 only, and §3's
   "membership and nameplate stay 100 % Gold Book" should be read precisely: the
   same 15 units at the same published nameplates, re-timed.
3. **The control should reproduce the keeper byte-identically, and there is no
   toolchain excuse if it does not.** Unlike nyiso-132, this session's
   environment matches the keeper bundle's recorded one exactly (Python 3.11.15,
   highspy 1.15.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.5, pyarrow 25.0.0,
   pydantic 2.13.4, same platform). A non-reproducing control is a hard failure
   here, not a drift note.

## 5. Kill gates — pre-registered, evaluated before any promotion claim

| gate | condition | disposition if it fires |
|---|---|---|
| **K1** config isolation | exactly ONE differing `scenario_config` field between arms (`nyiso_solar_registry_cod_dates`) | comparison void, re-run |
| **K2** feasibility | zero slack and zero dump, both arms, all three years | comparison void |
| **K3** liveness | arm/control registered-solar mean-monthly capacity = 1.010 / 0.898 / 1.000 (± 0.005) — the constant demonstrably reaches the LP | mechanism not wired, void |
| **K4** scope | wind energy identical (0.000 GWh) and no non-solar input moves | edit leaked, void |
| **K5** gated-criterion regression | any of C1/C2/C3a/C3b/C4/C6/C8 goes PASS → FAIL | **REJECTED AS ARMED** |
| **K6** scarcity collapse | C3c-2025 falls below 21 h, or C3c-2024 falls to 0 h | **REJECTED AS ARMED** |
| **K7** forcing budget | any material class's C8 forced share crosses its cap (30 %; peakers 15 %) | **REJECTED AS ARMED** |

K5–K7 are the substantive kills. A gate that fires is reported at full size and
the arm is rejected **as armed** — the identification in §2 survives a rejection
either way, exactly as nyiso-130's did.

**What is NOT a kill:** ADV-1, and any move in the report-only VRE advisory band
in either direction. Per rule 1 the arm is judged on whether the model's
*mechanism* is more faithful, not on whether the residual improved.

## 6. Registration duties

Rule 15: **both** arms registered on the backcast dashboard in this session,
keeper or rejected. Rule 16: **2023 2024 2025 in one bundle** per arm. Rule 28:
the new `nyiso_solar_registry_cod_dates` row is added to the mechanism matrix in
the same PR (CI `mechanism-matrix-guard` enforces this half), and the
`vre_avg_cf_level` NYISO cell's successor note is re-pointed from "no
commissioning curve" to what §1 measured.

Promotion is the **owner's call**; the keeper shard, the `complete` marker and
the matrix keeper stamp stay untouched pending it.
