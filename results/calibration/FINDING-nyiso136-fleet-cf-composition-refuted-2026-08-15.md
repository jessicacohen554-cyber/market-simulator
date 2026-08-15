# FINDING nyiso-136 — the FLEET-CF COMPOSITION object is REFUTED on its own premises, ex ante, with NO SOLVE SPENT

**Session nyiso-136, 2026-08-15.** The owner chose lever (a), the **fleet-CF
composition object** — nyiso-133's named successor, carried in the lever queue by
`ASSESSMENT-nyiso135-promotion-2026-08-15.md` §2. Rule 19 `[R-ONE-MECH]` requires
a pre-registration before any solve; the identification work that a
pre-registration must rest on was done **first**, and it **refuted the object**.
No arm was written, no pre-registration was filed for a mechanism that cannot be
identified, and **no LP was solved**. This is the nyiso-133 pattern applied to
nyiso-133's own successor.

Probe `scripts/probes/_nyiso136_fleet_cf_composition.py`, record
`results/calibration/_nyiso136_fleet_cf_composition.json`. Both published inputs
were already committed: EIA-860 `eia860_solar_operable` (per-plant
`Single-Axis Tracking?` / `Fixed Tilt?` / `Tilt Angle`, `Operating Year/Month`)
and EIA-923 monthly net generation, joined on the **same** 15-row registry
crosswalk the keeper's capacity ramp uses
(`derive_nyiso_market_solar.PTID_TO_EIA`), so this measures the keeper's own
fleet and nothing else (rule 25 `[R-ISO-SCOPE]`).

---

## 1. THE OBJECT, AS NAMED

> *"After the date repair 2023 and 2024 both imply fleet CF ~0.162 vs 2025's
> 0.1955; measured mature per-plant CF is 0.174–0.182 (2021–22 small fixed-tilt
> NY8) vs 0.198–0.221 (2024 tracking: Morris Ridge 0.1998, High River 0.1983,
> East Point 0.2207). One ISO-wide `RENEWABLE_AVG_CF` cannot track 100 %
> fixed-tilt → 56 % tracking."*

Three factual premises: **P1** the 2024 wave is tracking; **P2** the fleet spans
100 % fixed-tilt → 56 % tracking; **P3** tracking runs at a materially higher CF
than fixed tilt. The quoted CF *levels* all reproduce. The **technology labels
attached to them do not.**

## 2. P1 — FALSIFIED IN PART: High River is FIXED TILT

| plant | MW | COD | `Single-Axis Tracking?` | `Fixed Tilt?` | Tilt Angle |
|---|---:|---|---|---|---:|
| Morris Ridge | 177.0 | 2024-11 | **Y** | — | 0° |
| East Point | 50.0 | 2024-05 | **Y** | — | (blank) |
| **High River** | **90.0** | **2024-08** | **—** | **Y** | **18°** |

**High River is the second-largest plant in the registry and ~16 % of the 2025
fleet**, and it is fixed tilt on EIA-860's own flags, corroborated by a
non-zero tilt angle (every tracking plant in the fleet reads 0° or blank). The
object names it as one of the three plants that establish "2024 tracking".

## 3. P2 — FALSIFIED: the span is ~35 % → ~56 % tracking, not 0 % → 56 %

Two of the units the object calls *"2021–22 small fixed-tilt NY8"* are
single-axis tracking: **Branscomb** (COD 2021-12) and **Regan** (COD 2022-12).
On capacity-months online (COD basis):

| year | tracking share | mean online MW |
|---|---:|---:|
| 2023 | **34.8 %** | 163.0 |
| 2024 | 41.7 % | 295.3 |
| 2025 | **56.1 %** | 511.4 |

The 56 % end point is right. The 100 % fixed-tilt start point — the half that
makes the composition swing large — is not.

## 4. P3 — FALSIFIED: the tracking flag has no explanatory power here

Capacity factors measured over **mature** months (age ≥ 2, the threshold
nyiso-133 established nationally at 0.723 / 0.962 / 0.995 against a 1.0072
placebo) and **non-zero** months, because a full-month zero at a mature solar
plant in a New York summer is an **outage**, not a capacity factor.

| technology | n | range | simple mean | capacity-weighted |
|---|---:|---|---:|---:|
| FIXED | 7 | 0.1639 – 0.2170 | **0.1854** | 0.1862 |
| TRACKING | 5 | 0.1515 – 0.2091 | **0.1856** | 0.1971 |

**The two simple means differ by 0.0002.** The ranges overlap almost entirely.
**The highest-CF plant in the whole fleet is fixed tilt** (Calverton, 0.2170) and
**the lowest is tracking** (Regan, 0.1515). The capacity-weighted gap is not a
technology effect either — it is carried entirely by Morris Ridge (177 MW) and
East Point (50 MW), i.e. by *being large and recent*, which is a vintage
covariate, not a mounting one.

**What the object actually grouped was COD VINTAGE, and then labelled the
vintages by an assumed technology that EIA-860 contradicts.**

## 5. THE CEILING — even the most generous version reaches 38 %

Grant the mechanism strictly more than it asks for: let **every plant carry its
own measured mature CF** (per-plant, not merely per-technology — a strict
superset of any composition weighting), weighted by capacity-months on the COD
basis.

| year | composite CF | implied by published energy |
|---|---:|---:|
| 2023 | 0.1794 | 0.1613 |
| 2024 | 0.1869 | 0.1641 |
| 2025 | 0.1923 | 0.1955 |

Composite swing **+0.0129** against an implied swing of **+0.0342** — the
mechanism reaches **38 % of the effect it was named to explain**, and it
*over-states* 2023 and 2024 by +11 % and +14 % while landing 2025 nearly right.
For scale, this is the same test that retired nyiso-132's commissioning-curve
object at ~11 %. A mechanism that cannot reach the majority of its own named
effect, on premises its own data falsifies, is not built (rule 26 `[R-DELETE]`,
rule 1 `[R-STRUCT]`).

## 6. A HYPOTHESIS THIS SESSION RAISED AND THEN KILLED ITSELF

Because the mature-CF composite (0.1794) sits ~11 % above the CF the Gold Book's
published energy implies (0.1613), the obvious next thought is that the two
published series disagree — the benchmark-basis defect already chartered for
hydro at §5.5 item 11b. **Measured, and false.** Over the same crosswalked
plants:

| year | Gold Book Net Energy | EIA-923 metered | ratio | plants reporting |
|---|---:|---:|---:|---:|
| 2023 | 229.9 GWh | 230.2 | **1.001×** | 9 of 9 online |
| 2024 | 503.2 GWh | 517.3 | **1.028×** | 14 of 14 |
| 2025 | 981.8 GWh | 609.1 | 0.620× | **4 of 12 — preliminary** |

The two published series **agree** where both are complete. 2025's EIA-923 is a
preliminary vintage and is excluded, not averaged in. Recorded because it was
tested, not because it survived.

## 7. WHAT THE SAME MEASUREMENT FOUND INSTEAD — the successor, NAMED AND NOT BUILT

Against each plant's own mature CF, in the two years with whole EIA-923 coverage:

| year | expected at own mature CF | actual | shortfall | of which FULL-MONTH ZERO at a MATURE plant |
|---|---:|---:|---:|---:|
| 2023 | 256.1 GWh | 230.0 | 26.1 (10.2 %) | **11.1 GWh = 43 %** (Regan, Mar–Jul, 5 consecutive months) |
| 2024 | 483.4 GWh | 457.1 | 26.4 (5.5 %) | **7.9 GWh = 30 %** (Grissom, Mar–May, 3 consecutive months) |

**The largest single identified component of the residual is plant OUTAGE, and
the model cannot represent it at all.** `derive_cf_profile` normalizes the
EIA-930 shape so its hourly mean equals a flat annual `RENEWABLE_AVG_CF`, then
applies it to the **full registered nameplate in every hour**. There is no
availability derate anywhere on the VRE path — the thermal fleet has
`THERMAL_AVAILABILITY` / WEFOR and a measured CAMPD outage layer; solar has
**nothing**.

**This is a rule 1 `[R-STRUCT]` structural-fidelity item, NOT a gate
instrument, and it is deliberately not bundled here (rule 19).** Three things a
pre-registration must settle before it is worth a solve, all of which cut
against it:

1. **It is small and it is advisory.** ~11 GWh on a 230 GWh fleet, on a band
   `calibration_verdict.VRE_TOL` marks **report-only** for a class D-10 marks
   `delivered_pinned` ("advisory-only, excluded from skill claims"). No gated
   criterion can move on it.
2. **Two plant-years is not a rate.** Deriving a solar EFOR from two observed
   outages would be fitting a parameter to two events — rule 21 territory. An
   admissible construction needs a *published* solar availability series, and
   whether one exists for NY is unestablished.
3. **It does not close the gap either.** 43 % and 30 % of a 10.2 % and 5.5 %
   residual leaves most of both unexplained.

## 8. WHAT THIS SESSION DID **NOT** DO

No LP solved, no run registered, no keeper moved, **no cell verdict moved**, no
pre-registration filed. The keeper remains `2026-08-08-nyiso-133-cod-arm` at
`CALIBRATED-WITH-CAVEATS` with C3c the lone ledgered caveat at 21 / 3 / 24 h.
Frontier stays **CLEARED** (2026-08-06) and is **not** re-asserted — the queue is
not cleared, and this session **opened** an object while retiring another.
`RENEWABLE_AVG_CF["NYISO"]["solar"]` is **untouched at 0.1955**: it is the
measured **mature-fleet** CF and this finding gives no admissible basis to move
it. Holdout posture unchanged — the ACTIVE spend freeze was re-confirmed **HELD**
by the owner in this session, and 2022 was not solved, scored or registered.

**Lever queue after this session.** (1) the chartered **JOINT Zone-K
transfer-bound + downstate ST_GAS `min_gen` reconciliation** (rule 19) — still
open, still needs its own owner charter **and** pre-registration; do **not**
re-test the bare number swap (`nyiso_li_tsl_n11_security` is `R`, killed on K6 at
nyiso-130). (2) **VRE availability / forced-outage representation** — newly
named here, sized, and flagged as low-value on a report-only band. (3) The
FLEET-CF COMPOSITION object is **RETIRED**, joining the commissioning curve.

* Next number: **nyiso-137**.
