# FINDING — miso-266: regenerating MISO's bench parts at HEAD moves the actuals, and one of them goes negative

**Session** miso-266 · **Date** 2026-09-23 · **Lane** MISO calibration
**Instrument** `scripts/probes/_miso257_bench_gate.py` (dry run — **nothing was
written**) over `results/calibration/miso266_arm_span` after
`run_calibration_full.py --rebuild-benchmark`.
**Zero LP.**

## 1. WHY THIS WAS MEASURED

`dashboard_add_run.py` writes
`frontend/data/backcast/bench/<ISO>/<year>.json.gz` for every year its bundle
covers — "newest run covering a year supplies it". Those parts are the
**actuals every registered run of that ISO is scored against**, the designated
keeper included. So registering a six-year MISO run necessarily re-bases MISO's
whole scoring basis, and the size of that move decides whether a registration is
a formality or the NYISO incident (`FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md`:
a regenerated part moved a metered actual ~4 TWh and flipped every registered
NYISO run to NOT-YET, the keeper included).

miso-266's PRECOMMIT required the move be measured **before** registering. This
is that measurement.

## 2. THE MOVE, PER YEAR (TWh, committed part → HEAD rebuild)

| class | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| CC_REGULAR | +0.174 | +0.647 | +0.347 | +0.644 | **+2.651** | −0.143 |
| COAL_BIT | +0.094 | +0.110 | +0.087 | +0.070 | +0.376 | −0.237 |
| COAL_PRB | +0.199 | +0.247 | +0.266 | +0.234 | +0.214 | −0.216 |
| COAL_LIGNITE | +0.015 | +0.019 | +0.014 | +0.036 | +0.027 | −0.022 |
| CT_PEAKER | +0.022 | +0.229 | +0.083 | +0.079 | +0.075 | −0.072 |
| ST_GAS | +0.004 | +0.007 | +0.017 | +0.005 | +0.013 | +0.221 |
| OTHER_FOSSIL | +0.001 | +0.431 | +0.006 | +0.002 | +0.003 | +0.617 |
| CC_CHP | +0.008 | +0.005 | +0.002 | +0.000 | +0.001 | −0.101 |
| **`oil`** | **0.346→0.005** | **0.724→0.081** | **0.384→−0.073** | **0.462→0.030** | **0.397→0.023** | **0.353→−0.012** |

`e930.coal_cems` moves +0.004 to +0.016 in every year.

## 3. THE DISPOSITIVE OBSERVATION — A NEGATIVE MEASURED ACTUAL

**`classFull.oil` regenerates NEGATIVE in 2022 (−0.0731 TWh) and 2025
(−0.0124 TWh).** Measured generation cannot be negative. The `oil` class is
drained in every one of the six years (−0.34 to −0.64 TWh, i.e. 86–100 % of the
class) and in two of them it overshoots past zero.

The visible operand is the builder's dual-fuel re-attribution, which logs
e.g. for 2025: *"EIA-923 dual-fuel oil re-attribution: 0.365 TWh across 50
modelled plant(s) moved from the `oil` class into the classes their units
dispatch in."* It is subtracting more oil than the class holds.

**This one observation needs no controls.** Whatever else differs between the
committed part and this rebuild, no difference of bundle, year span or dispatch
can make a *measured* quantity negative. It is a defect in the benchmark builder
at HEAD.

## 4. WHAT THIS MEASUREMENT CANNOT SEPARATE, STATED RATHER THAN GLOSSED

`_miso257_bench_gate.py`'s admissibility condition is that the rebuilt part's
plant key set and every **dispatch-scoped** field (`name / zone / group / npl /
nodata / campd / c_ann / c_mon`) come back byte-identical, which is what would
license attributing everything else to the builder alone.

**The gate FAILED in all six years** — 6 to 12 fields moved, on two plants:

* `1393` R S Nelson (COAL_PRB, ST_CHP) — `campd`, `c_ann`, `c_mon` in every year;
  `nodata` also in 2024 and 2025.
* `1743` (COAL_BIT, CT_PEAKER) — `campd`, `c_ann`, `c_mon` in 2020–2022 only.

So the §2 table is **not** cleanly attributable to the builder: it mixes builder
drift with whatever those two plants' CAMPD records contribute. The table is
reported as *"what registering this run would do to MISO's actuals"*, which is
exactly the decision-relevant quantity, and **not** as *"how far the builder has
drifted"*, which this instrument did not isolate.

## 5. WHAT WAS DONE WITH IT

**The move was NOT adopted, by two independent lanes on the same day.**

`miso266_arm_span` was registered with the committed `bench/MISO/*.json.gz`
**restored byte-for-byte** afterwards, verified by sha256 against the
pre-registration snapshot, so the arm and the then-incumbent keeper were scored
against **the same numbers**. That promotion was later **withdrawn** (a sibling
arm, hydro-5's `hydro_ror_split`, landed on the same `miso-264` base first and
promoting this one would have reverted it) — but the bench decision stands on its
own and is why this finding exists.

**Independently, `hydro-5` hit the same wall and made the same call**, in its own
commit message: *"MISO's regenerated parts moved content (miso266 builder drift)
and were NOT committed."* Two lanes, two registrations, one conclusion.

**The one cost of that choice, stated.** A run payload's `volErr` field (the Run
Explorer's volume-error heatmap) is computed inside `build_payload` against the
regenerated frames, so it is inconsistent with the restored bench part by the §2
magnitudes. `volErr` appears **nowhere** in `scripts/calibration_verdict.py` —
C1 reads `ybench["classFull"]` from the bench part and the model side from the
payload — so **no scored criterion is affected**. The defect is confined to one
display surface. It does not apply to any currently registered MISO run, because
the only run that carried it was withdrawn.

## 6. WHAT THIS IS ROUTED TO, AND WHY NOT HERE

This is **not** a MISO-lane-local problem.
`tests/scoring/test_bench_stamp_payload.py::test_d_every_committed_part_resolves_to_a_known_builder_state`
fails on **44 committed parts across all nine ISOs** — CAISO, ERCOT, MISO, NEISO,
NWPP, NYISO, PJM, SOCO, SPP — every one carrying aggregate `64b6829fb757`, which
`PAYLOAD_FINGERPRINT_BY_BUILDER` cannot resolve. That failure arrived with `main`;
this branch touches no bench part, no `bench_stamp.py` and no payload source.

Refreshing MISO's six parts in isolation would re-score every registered MISO run
against a builder that §3 shows is defective, while the other eight ISOs stayed on
the old one. The correct order is: **fix the `oil` re-attribution → refresh the
parts → re-score each ISO's keeper → then promote anything that was waiting.**

**ROUTED: this is `miso-267` STEP 1.** Bisect which builder commit moved the
parts, classify each moved field as a real data correction or a regression, and
only if it is a correction regenerate once, re-score the keeper and every stamped
run, and report every determination that moves at full magnitude. The benign
precedent to aim at is hydro-5's SPP case, where the regenerated parts came back
**byte-identical** to the pre-spp-71 content — that is what a clean refresh looks
like, and MISO's is not one.

## 7. THE PRIOR CLAIM THIS CORRECTS

`RESULT-miso266-dispatched-bin-denominator-2026-09-22.md` §5 said
`--rebuild-benchmark` "would regenerate the committed `bench/MISO/*.json.gz`
parts". **It does not.** `rebuild_benchmark()` writes only to the *gitignored*
shared store `results/calibration/_shared/<ISO>/` and re-points that one bundle's
`meta.json`; its trailing `report_run()` is a printer. The re-base happens one
step later, in `dashboard_add_run.py`. The hazard was correctly identified and the
mechanism was named wrong — which matters, because the wrong mechanism made the
hazard look unavoidable when in fact it is separable, and §5's separation is what
allowed this run to be registered at all.
