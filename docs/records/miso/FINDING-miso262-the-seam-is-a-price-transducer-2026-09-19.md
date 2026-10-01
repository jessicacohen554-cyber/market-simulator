# FINDING — miso-262: MISO's seam is a PRICE TRANSDUCER, not a volume defect. The 2020 COAL_BIT rung routes to the price residual, and a year-invariant coal offer multiplier cannot close it

```
SESSION : miso-262        ISO: MISO        LP SPENT: ZERO. No shard launched.
KEEPER  : 2026-09-16-miso-260-seam-ladder (bundle results/calibration/miso260_seam_span,
          span 2020-2025) — VERIFIED ON main BEFORE ANY WORK (the miso-261 §6 item 3
          duty). UNCHANGED by this session. Train tier 2023-2025 CALIBRATED.
OBJECT  : the validation rungs — C1 2020 COAL_BIT -10.29, C1 2022 CC_REGULAR -9.47,
          C3a 2020 +16.3%, C3a 2022 -14.6%, C3b 2021 0.299. I took the 2020 object.
ANSWER  : the charter's phase-0 hypothesis is CONFIRMED AS THE CHANNEL AND REFUTED AS
          THE CAUSE. The seam has NO independent volume defect: across all six years
          its volume error is an almost pure linear function of the model's own price
          bias (r = +0.957, slope 0.462 TWh per +1 pp, intercept -0.125 TWh). It
          transduces the price residual into displaced coal. The repair therefore does
          not live in the seam — where all three mechanism classes are already spent —
          and it cannot be a year-invariant coal offer multiplier either, because the
          price bias FLIPS SIGN across the scored span (+18.2 / +3.3 / -17.3 / +7.5 /
          +4.0 / -1.1 %).
PROBE   : scripts/probes/_miso262_seam_price_transducer.py (sections A-F reproduce
          every number below from committed artifacts; nothing fetched, no replay).
```

---

## 0. WHICH OBJECT I TOOK, SAID BEFORE I TOOK IT

`HANDOFF-miso262` requires the session to name its object. **I took the 2020 object —
the import/seam channel — and I did not touch the 2023/2025 intra-coal merit split.**
The charter's instruction was to reconstruct 2020's per-seam hourly net flow from the
keeper's committed sidecars and ask which hours the ladder displaces COAL_BIT in.

**One correction to the charter's mechanics, found at the first step.** It says the
keeper commits `hourly/{class_hourly,system,reserve_family,network}_<y>.parquet` and
`unit_hourly_<y>.parquet`. It commits the first three and `class_band_hourly` +
`storage`; **`network_*.parquet` and `unit_hourly_*.parquet` are gitignored**
(`.gitignore` lines 672-675) and are not in `main`. The per-seam MODEL flow therefore
does not exist outside a solve, and miso-261's per-unit `mc` quantiles are not
reproducible at HEAD either — the leg bundles they were read from were on
`claude/miso260-span-{v,t}`, and **both shard branches are now gone from `origin`**
(`git ls-remote origin | grep miso260` returns nothing), so the §1 recovery SHAs in
`RESULT-miso261` are dead. Nothing was lost that this session needed: the *aggregate*
model net-import hourly IS committed, as `class_hourly`'s `klass='import'`, whose
per-hour sum is the priced node's net injection (`run_calibration_full.py` computes net
interchange as `-(that sum)`). Every measurement below is built on that.

## 1. THE MEASUREMENT THAT DECIDES IT

Across all six years, the model's own price bias against the measured MISO hub RT, set
beside the seam's annual volume error (probe §D):

| year | model $ | RT $ | price bias | seam volume error |
|---|---:|---:|---:|---:|
| 2020 | 26.36 | 22.31 | **+18.16 %** | **+6.496 TWh** |
| 2021 | 40.75 | 39.46 | +3.28 % | +0.325 TWh |
| 2022 | 57.79 | 69.85 | **−17.27 %** | **−9.560 TWh** |
| 2023 | 34.17 | 31.79 | +7.50 % | +4.108 TWh |
| 2024 | 32.04 | 30.80 | +4.04 % | +3.382 TWh |
| 2025 | 42.37 | 42.85 | −1.11 % | +1.242 TWh |

**r = +0.9572, slope 0.4618 TWh per +1 pp of price bias, intercept −0.125 TWh.**
Against the DA price the ladder is actually coupled to: r = +0.9556, slope 0.5151,
intercept +1.044. Residuals ±2.1 TWh; leave-one-out slopes 0.298–0.648.

**Read the intercept.** At zero price bias the seam's volume error is −0.1 TWh (RT) /
+1.0 TWh (DA). The armed ladder does not over-import or under-import on its own — it
imports exactly as much as the host market's price tells it to. That is what a
price-indexed supply curve is *supposed* to do, and it is why the seam is the wrong
place to look for the repair.

**Reported against interest, three ways.** (a) Six points is a small sample and **2022
is high-leverage** — without it the slope falls to 0.298 (RT), so the relation's
strength rests partly on one extreme year. (b) The residuals carry a monotone drift
(−1.76, −1.07, −1.46, +0.77, +1.64, +1.88 TWh, 2020→2025), i.e. there is a second
~±1.8 TWh component this single regressor does not explain. (c) The direction of
causation is not established by the correlation: displacing coal with imports also
*lowers* price, so the two are jointly determined. What the intercept does establish is
the weaker and sufficient claim — **there is no volume error left to attribute to the
seam once the price residual is accounted for.**

## 2. WHAT IT DOES TO COAL, HOUR BY HOUR

Measured hourly COAL_BIT / COAL_PRB come from the committed bench part's own per-plant
`campd` blob (uint8 CF % of `npl`), so the plant set and the class map are the bench's,
not a re-derivation. CEMS is gross, so it is rescaled to the bench's grid-delivered
`classFull` level and only the SHAPE is compared (probe §C).

**2020, mean MW by decile of model load:**

| decile | BIT model | BIT meas | **BIT def** | PRB def | imp model | imp meas | **imp err** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 (low) | 4848 | 5266 | **−418** | +1175 | 5861 | 6916 | **−1055** |
| 4 | 6084 | 7340 | −1256 | −467 | 7193 | 6311 | +882 |
| 8 | 7637 | 9133 | −1497 | −907 | 7563 | 5941 | +1621 |
| 9 (peak) | 8761 | 10495 | **−1734** | −1094 | 8108 | 6713 | **+1395** |

**2023, the same table's endpoints:** BIT def −190 at the bottom decile and **+10 at the
top**; imp err +473 at the bottom and **−1600 at the top**.

Three things follow, and the third is the one that matters.

1. **The 2020 BIT deficit is in every hour of the day** (−676 MW overnight to −1419 MW
   at peak) and grows monotonically with load. It is not a peak-hour phenomenon that an
   import lever alone created.
2. **The two years differ exactly where the seam differs.** In 2020 the model
   over-imports by +1.4 to +1.6 GW in the top two load deciles and BIT is short 1.5–1.7
   GW there; in 2023 the model *under*-imports by 1.6 GW in the top decile and BIT's
   deficit closes to zero. `corr(BIT deficit, import error)` is −0.489 (2020) and −0.407
   (2023).
3. **PRB's error flips sign within the day in BOTH years** (+1175 MW at the bottom
   decile, −1094 at the top in 2020; +775 / −395 in 2023). So the intra-coal
   mis-ordering miso-261 measured in the 2023/2025 OFFER stack is visible in the 2020
   DISPATCH too. **miso-261 §4 is not contradicted** — it measured `mc` quantiles and
   correctly found no merit separation in 2020's offers. Both are true: the model has no
   BIT/PRB merit distinction in 2020, and the real market did. What is falsified is only
   the stronger reading that 2020 has no split object at all.

## 3. THE GATING BASIS CORRECTS THE 2020 FRAMING

`RESULT-miso260` reports 2020 coal moving `+7.75 → −2.83` TWh. That is the EIA-930
`fuelRows` basis, which `FINDING-miso261` ruled is **not** the C1 gating basis (the 930
MISO COL cell reads 17.5–21.1 TWh below CAMPD in every year). On the gating basis
(`classFull`, grid-delivered, per class — probe §A):

| year | COAL_BIT | COAL_PRB | COAL_LIGNITE | **coal3 total** |
|---|---:|---:|---:|---:|
| 2020 | **−10.29** | −3.33 | +0.92 | **−12.71** |
| 2021 | −7.02 | −2.03 | +1.35 | −7.70 |
| 2022 | +0.55 | +7.90 | −0.76 | +7.68 |
| 2023 | −3.32 | −1.49 | −0.71 | −5.52 |
| 2024 | −3.87 | −4.25 | −0.80 | −8.92 |
| 2025 | −4.12 | **−11.23** | −0.97 | **−16.31** |

**2020's coal family is short 12.71 TWh, not 2.83**, and BIT carries 81 % of it while
PRB carries the rest. So the 2020 rung is **not** a pure BIT-vs-PRB re-allocation — both
coal classes are short, and the seam's +6.50 TWh of excess imports covers roughly half
the family deficit.

**Also surfaced, unscored:** 2025 `COAL_PRB` reads **−11.23 TWh**, outside the ±8 TWh
band, and 2025 coal3 is the largest deficit of the span at −16.31. It does not appear in
the verdict because every 2025 coal class is SKIPPED on the preliminary EIA-923 vintage
(`COAL_PRB`: 6/40 prior plants missing, 85 % reporting). **When the 2025 vintage
finalises, MISO gains a sixth failing C1 cell unless something moves** — flagged for the
lane that re-scores after the next EIA-923 release, not acted on here.

## 4. TWO CANDIDATE CAUSES KILLED, CHEAPLY

**The load basis is clean (probe §F).** The model's annual demand reproduces MISO's own
measured EIA-930 adjusted demand to **−0.263 / −0.000 / −0.003 / +0.001 / −0.293 /
−0.003 %** across 2020–2025. The coal deficit is not a demand artefact and there is no
`td_loss_factor` / `tac_load_coverage` story here at the annual grain.

**The ladder is not setting the bulk price (probe §E).** A seam band is the marginal,
price-setting offer in **12.6 %** of 2020 internal zone-hours (9.3 / 12.4 / 6.8 / 6.3 /
4.6 % in the other years). I expected this to be the answer and it is not: in ~87 % of
2020 hours the thermal offer stack sets the price, so the seam cannot be blamed for the
price bias it transduces.

## 5. WHERE THE PRICE RESIDUAL ACTUALLY LIVES — REPORTED, NOT FIXED

The model's price distribution is **compressed in every year of the span**: too high
through the bulk, too low in the tail (probe §D).

| 2020 | p1 | p10 | p25 | p50 | p75 | p90 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| model | 17.37 | 20.67 | 22.94 | 26.74 | 29.36 | 31.33 | 36.99 |
| RT | 8.30 | 14.58 | 17.23 | 19.86 | 23.09 | 29.72 | 77.63 |

The tail half is C3c, ledgered and adjudicated as a model-class limitation. **The bulk
half is not ledgered**, it is present in all six years (model p10 runs $6–$11 above RT's
in every one), and it is what the seam converts into volume. It is the standing MISO
object behind C3a 2020 (+16.3 %) and C3a 2022 (−14.6 %) — **two of the five failing
rungs — and, through §1, behind a large part of a third.**

## 6. THE CHARTER'S OWN NAMED LEVER IS REFUSED, ON STRUCTURE, AT ZERO LP

The charter warns that *"a lever that tunes COAL_BIT's offer bands will not touch 2020
and may widen it."* The measurement says something sharper and gives the reason:

* It **would** touch 2020 — through the price→import channel of §1. Cutting BIT's
  offer bands moves BIT earlier in merit, lowers the clearing price, and the
  price-indexed seam then imports less, which raises BIT again. The channel runs the
  right way.
* It **cannot be armed anyway**, because rule 1 `[R-STRUCT]`'s authorised
  price-tuning carve-out binds on condition (b): **ONE config across EVERY scored
  year.** The price bias is **+18.2 % in 2020 and −17.3 % in 2022**. One year-invariant
  multiplier that closes 2020 deepens 2022's under-pricing and its −9.56 TWh seam
  under-import, and the reverse for a multiplier that closes 2022. A per-year value is
  per-year fitting, which condition (b) refuses outright.

**This is a structural refusal, not a residual sweep.** No multiplier was tried, no
criterion was consulted to choose it, and nothing was tuned (rule 1; rule 21
`[R-DOF]` — zero free parameters added).

## 7. THE SEAM IS SPENT AS A REPAIR SITE — AND MY HOUR-OF-DAY RESULT IS A REDO, SAID PLAINLY

The hour-of-day inversion I measured (2020 model imports peak at h13-h18 while the
measured seam peaks at h01-h04; hourly r 0.20–0.53 across the span; ordering-only
mismatch a near-constant 3.2–4.6 TWh in EVERY year including the healthy ones) is **not
new**. `miso-123` measured it at per-seam grain on 2023-2025 and closed it: the armed
availability envelope is already hod-shaped at r ≈ +0.95 while *the model's cleared flow
tracks the measured flow at −0.638 / −0.753 / −0.852*, which it attributed to the
hour-invariant `MISO_SEAM_LADDER_BY_YEAR` price ladder. `import_shape_lever` is `G`.
All three mechanism classes are spent — price (`R` ex ante, miso-114 §4), ceiling
(closed, miso-123, with the bound generalised to the whole ceiling class), floor
(`miso_firm_import_floor`, a rule-13 outcome pin, never re-licensed).

What §1 adds that miso-123 did not have is the **volume** half and the years
2020-2022: miso-123 established that the price ladder mis-orders the hours; this
establishes that the same ladder mis-*sizes* the year by exactly the price residual,
with a zero intercept. Both point away from the seam.

`miso-123`'s stated re-open condition is unchanged and unmet: *"a scheduling
representation of the firm/JOA transfer base that can raise overnight flow, on an
identification that is not the measured net interchange itself."* **Nothing here
licenses re-opening it**, and a successor should not read §2 as an invitation to.

## 8. TWO CHARTER ITEMS ADJUDICATED IN PASSING

**ST_GAS — "check the floor before the offer."** Checked, from the keeper's committed
`legitimacy_diagnostics.json` D-2 rows. `st_gas_mustrun_per_plant` forces **21.9 / 26.3
/ 22.3 / 14.4 / 15.5 / 17.7 %** of ST_GAS energy across 2020-2025 (the charter's
"31.9 %" does not reproduce on this keeper's artifact). The class is simultaneously
FLOORED and SHORT (−5.57 / −2.69 / −3.38 / +0.32 / −2.98 / −2.49 TWh), so the floor is
not what limits its volume — the economics above the floor is. Raising the floor is
forcing, and at 26.3 % it is already close to rule 18 `[R-FORCED-BUDGET]`'s 30 %
merchant cap. **The floor is not the lever; the charter's ordering instruction resolves
against it.**

**West Riverside Energy Center (EIA 64020).** Not acted on, but narrowed by one grep:
the plant is **already crosswalked in a committed reference table** —
`data/raw/reference/miso_gas_variable_transport.csv:108` carries
`64020,West Riverside Energy Center,CC_REGULAR,MISO-East,684.2` with a derived transport
adder. **That is NOT evidence about the fleet loader** — that table is derived from
EIA-923 plant prints, not from the model fleet, so its coverage says nothing about
dispatch (I checked the derive script's header before claiming otherwise). What it does
give the intake lane for free is the zone, class and nameplate, already resolved and
committed.

## 9. GATES, AS SCORED

| gate | verdict | measured |
|---|---|---|
| `calibration_verdict` on the keeper | **NOT-YET (unchanged)** | exactly the five rungs the charter names; every 2025 coal class SKIPPED on the preliminary vintage (§3) |
| `check_bench_freshness --iso MISO` | **PASS** | 6 parts, **0 STALE**; 6 carry an engine-drift WARNING (2 commits under `src/market_sim/{data,config}` since 2026-09-17) — checked, not absorbed: the parts **reproduce at HEAD**, which is the strong form, so the §A/§C bench numbers are HEAD numbers |
| `check_registry_payload_parity` | **as charted** | see the RESULT |
| `audit_keepers --iso MISO` | **PASS** | E3 warning pre-existing |
| `build_status --iso MISO --check` | **PASS** | |
| `check_mechanism_matrix --base origin/main` | **PASS** | |
| `check_cache_key_registration --base origin/main` | **PASS** | no `ScenarioConfig` field added |
| `check_gate_a_provenance` | **MISO clean** | NEISO / NYISO / SPP still fail on superseded keepers — not MISO's (rule 25) |
| `pytest tests/scoring` | **no new failures** | baseline measured in this container, both ways |
| `_miso260_bench_parity.py` / `_miso257_btm_identity.py` | **n/a** | nothing registered, nothing re-solved |

## 10. RULES

* Rule 32 `[R-SHARD]` (a) — **ZERO LP; no shard launched.** Every number is read from
  committed artifacts.
* Rule 1 `[R-STRUCT]` — no mechanism armed, no parameter tuned, no residual consulted to
  select anything. §6's refusal is on the carve-out's own condition (b), not on a sweep.
* Rule 21 `[R-DOF]` — zero free parameters added.
* Rule 28 `[R-MECH-MATRIX]` (a)/(b) — the target ISO's lever queue and cell verdicts were
  read BEFORE the object was framed; `import_shape_lever` stays **`G`** and
  `seam_neighbour_hourly_ladder` stays **`K`**, both with this session's evidence
  appended. No mechanism was tested, so no verdict moves.
* Rule 31 `[R-RETAIN]` — nothing deleted. Nothing was produced that could be promoted.
* Rule 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — every measured series used here
  (EIA-930 interchange and demand, CEMS hourly via the bench blob, the committed
  ladders) is read as a comparator, never fed back into a solve.
