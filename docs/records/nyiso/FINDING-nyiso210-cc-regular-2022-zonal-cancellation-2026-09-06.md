# FINDING nyiso-210 — the 2022 touchpoint's CC_REGULAR over-run is **NOT a new object and NOT an amplification**: it is the keeper's **persistent NYC over-run made visible** when the **Capital_Hudson under-run that cancels it in-sample flips sign**. The in-sample C1 PASS rests on two ~1 TWh opposite-signed zonal errors that both **grow** across 2023-2025.

**Session:** nyiso-210, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-3znirv`, off `main` `9a67ecb6`. **Date:** 2026-09-06.
**Keeper: `2026-09-06-nyiso-202-startup-aware` — UNCHANGED.** No `ScenarioConfig` field, no
coefficient, no offer curve, no derive script, no scorer, no marker, no keeper, no gate moved.

**ZERO LP SPENT.** Rule 29 phase 0 in full: every number below is read from artifacts already
committed to `main`. No solve, no screen, no arm, no bundle, no registration — so rule 29(c) has
nothing to delete and rule 15 has nothing to register.

**Pre-registration:** `results/calibration/PREREG-nyiso210-cc-regular-2022-overrun-attribution.md`
(committed and pushed at `f520bd1f` **before the probe was written**), plus
`results/calibration/ADDENDUM-nyiso210-band-vocabulary-2026-09-06.md` (`c30612c5`, a construction
repair to the band partition, **written before any P1/P2/P3 verdict value was read**).
**Machine record:** `results/calibration/_nyiso210_cc_overrun_attribution.json`.
**Reproduce:** `uv run python scripts/probes/nyiso210_cc_overrun_attribution.py`.

**THERE ARE STILL NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads **CALIBRATED,
grade 7 of 8, fails 0**, C3c the lone ledgered non-downgrading caveat. Nothing below was selected
because a residual moved (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`).

**Rule 22:** the 2022 rung was **already SPENT** by nyiso-209. This session re-reads that run's
committed sidecars and payload — touchpoint-loop **step 2**, not a new spend. **Nothing is
identified against 2022.** The object below is measurable, and repairable, **entirely within
2023-2025**, which is what makes step 3 possible without ever fitting to the held-out year.
2020, 2021 and the locked test are untouched; no marker byte moved.

---

## 0. The result in one paragraph

The 2022 C1 CC_REGULAR over-run has never been decomposed; nyiso-209 §2.4 read it as *"the same
cell-G sign the keeper carries in-sample, scaled by the 2022 fuel regime"*. **That reading is
half right and it hides the load-bearing half.** On a CAMPD-consistent basis the class gap
deteriorates **+2.136 TWh** from its in-sample mean to 2022, and the deterioration splits by
**zone**: **Capital_Hudson +1.592 TWh (74.5 %) — a SIGN FLIP**, from −1.104 TWh in-sample to
**+0.488 TWh**; NYC +1.032 TWh (48.3 %) — an amplification of a gap that is **positive in all
four years**; Upstate_West −0.623 TWh (−29.2 %); Long_Island +0.135 TWh (6.3 %). In-sample the
**class** gap is ≈ 0 (+0.223 TWh mean) **because NYC's persistent +0.884 TWh over-run is
cancelled by Capital_Hudson's persistent −1.104 TWh under-run.** 2022 does not create a new
error — **it removes the cancellation.** And the cancellation is not stable: both legs **grow**
across the training window (NYC +0.945 → +1.296 TWh, Capital_Hudson −0.641 → −1.564 TWh), so the
in-sample C1 pass depends on an increasingly large offset. Three named plants over-run in
**every** year (Bethlehem, Zeltmann, Astoria Energy) and two under-run in **every** year (Cricket
Valley, CPV Valley) — **no new plant object exists.** Availability is refuted independently
(2022 carries *more* overlay derate at two of the three over-runners), and forcing is refuted by
the bundles' own D-2 (2022's CC_REGULAR forced energy is the **lowest of the four years**).

## 1. Pre-registered verdicts, as declared

| prediction | declared bar | measured | fires |
|---|---|---:|:--:|
| **P2** (M1 forcing) — *the one declared to hurt the preferred answer* | `committed` band > +0.5 TWh vs in-sample mean | **+0.855 TWh** | **YES** |
| **P1** (M2 merit position) — *the preferred answer* | economic **share** ≥ +3.0 pp | **+1.05 pp** | no |
| **P3** (M3 availability) | CV of band % changes < 0.35 | **1.832** | no |
| **P4** (plant grain) | ≥ 2 of top-3 by \|gap\| shared with in-sample | overlap **1 of 3** | no |
| **P4 falsifier** | a non-in-sample-top-3 plant > 30 % of the gap | **two** fire (37.3 %, 30.1 %) | **YES** |
| **P5** (dual fuel, reported only) | CC_REGULAR oil ≤ 0.05 TWh | **0.353 TWh** | falsified |
| **I1** (instrument identity) | payload plant sum vs `class_hourly` within 5 % | 0.92 / 0.05 / 0.37 / 0.00 % | **PASS** |

**The pre-registered verdict is P2, and this session reports that P2's own mechanism is REFUTED
on the same committed artifacts.** Both halves are stated at full strength in §2.

## 2. P2 fired, and the mechanism it was declared to indicate did not happen

PREREG §2 mapped **M1 (forcing)** onto the `committed` band. P2 fires: `committed` is
**+0.855 TWh** above its in-sample mean (net-of-oil basis; **+0.870** gross — the verdict is
identical on both, §6.2). **But forcing went DOWN.** From the bundles' own
`legitimacy_diagnostics.json` D-2 rows, CC_REGULAR forced energy:

| | 2022 | 2023 | 2024 | 2025 | in-sample mean |
|---|---:|---:|---:|---:|---:|
| `nyiso_gas_commitment_bridge` forced TWh | **0.0774** | 0.3373 | 0.0962 | 0.1304 | **0.1880** |
| share of class | 0.22 % | 1.07 % | 0.28 % | 0.39 % | 0.58 % |

**2022 is the LOWEST of the four years**, −0.111 TWh below the in-sample mean. A channel that
delivers 0.077 TWh cannot carry a 0.855 TWh band rise, and it moved in the **opposite** direction.

**The defect is in my own pre-registration, and it is a construction error, not a threshold
one.** `committed` is an **offer** band — the low-priced committed tranche of the rising
per-plant offer curve (`docs/binning-methodology.md`) — not a forcing channel. Energy lands in it
whenever a unit is on and its committed tranche clears, whatever put the unit on. So the band
axis localizes the over-run to that tranche without identifying **why** the tranche ran, and
PREREG §2's *"M1 owns the `committed` band"* was wrong as stated.

**A second, larger limitation of the band axis, discovered in execution:**
`class_band_hourly` carries **no measured side and no zone**. A band comparison is therefore
model-2022 against model-in-sample — it measures how the **model's own composition** moved, never
what carries the **model-minus-measured** over-run. The band axis could not have answered the
PREREG's question at any threshold. **P1, P2 and P3 are reported exactly as declared and none of
them is the finding**; the finding is §3, on the axis that does carry a measured side.

## 3. The answer: a zonal cancellation, not a 2022 object

Model-minus-CAMPD CC_REGULAR gap, TWh, from the committed bench (`c_ann`/`c_mon`) and the
committed run payloads (`m_ann`/`m_mon`) — the same instrument in all four years:

| zone | 2022 | 2023 | 2024 | 2025 | in-sample mean | **2022 − mean** | share of deterioration |
|---|---:|---:|---:|---:|---:|---:|---:|
| **NYC** | **+1.916** | +0.945 | +0.411 | +1.296 | **+0.884** | **+1.032** | **48.3 %** |
| **Capital_Hudson** | **+0.488** | −0.641 | −1.106 | −1.564 | **−1.104** | **+1.592** | **74.5 %** |
| Upstate_West | −0.078 | −0.101 | +0.561 | +1.175 | +0.545 | −0.623 | −29.2 % |
| Long_Island | +0.033 | −0.297 | +0.014 | −0.024 | −0.102 | +0.135 | 6.3 % |
| **class** | **+2.359** | −0.094 | −0.119 | +0.883 | **+0.223** | **+2.136** | 100 % |

The zonal terms sum to the class deterioration exactly (2.1360 vs 2.1362, rounding).

**Three statements, in order of load-bearing:**

1. **NYC over-runs in every year, and in every winter.** NYC's gap is positive in all four
   years, and its winter (Jan/Feb/Mar/Dec) half is positive in all four: **+1,062 / +795 / +294 /
   +479 GWh**. This is a **standing keeper property**, fully visible in-sample. 2022 is its
   largest instance, not its first.
2. **The in-sample C1 PASS is a cancellation.** NYC's +0.884 TWh mean over-run is offset by
   Capital_Hudson's −1.104 TWh mean under-run, leaving a class gap of +0.223 TWh that comfortably
   passes C1. **Two errors of ~1 TWh each, of opposite sign, are netting to zero at class grain**
   — which is precisely the condition under which a class-level criterion certifies a model whose
   zonal dispatch is wrong in both directions (rule 1 `[R-STRUCT]`).
3. **The cancellation is DRIFTING, and 2022 is simply where it had not yet formed.** Both legs
   grow monotonically in magnitude across the training window — NYC +0.945 → +0.411 → +1.296 and
   Capital_Hudson −0.641 → −1.106 → **−1.564** — so the offset the class-level pass depends on is
   getting larger every year. In 2022 Capital_Hudson is **+0.488**, i.e. the offset has the
   *opposite* sign, and the NYC over-run stands exposed. **That, not a fuel regime, is why 2022
   fails C1.**

### 3.1 Plant grain — the same five plants in every year

| plant | code | zone | npl MW | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|---:|---:|
| Bethlehem Energy Center | 2539 | Capital_Hudson | 893 | **+1.622** | +0.569 | +0.396 | +0.441 |
| Zeltmann | 56196 | NYC | 528 | **+0.880** | +0.556 | +0.264 | +0.439 |
| Astoria Energy | 55375 | NYC | 595 | **+0.710** | +0.294 | +0.238 | +0.057 |
| Astoria Energy II | 57664 | NYC | 650 | +0.253 | +0.128 | −0.069 | +0.779 |
| Athens Generating Plant | 55405 | Capital_Hudson | 1,222 | +0.249 | +0.036 | −0.136 | −0.099 |
| Cricket Valley Energy | 57185 | Capital_Hudson | 1,312 | **−0.648** | −0.441 | −0.608 | **−1.010** |
| CPV Valley Energy Center | 56940 | Capital_Hudson | 770 | **−0.595** | −0.717 | −0.741 | −0.841 |

*(TWh, model − CAMPD. Full 21-plant table in the machine record; every other plant is
|gap| ≤ 0.073 TWh in 2022.)*

**Every plant in the 2022 top-3 over-runs in all four years. No new plant object exists.** The
over-runners are the older CCs (Bethlehem 2005, Astoria Energy 2006, Zeltmann 2011); the
under-runners are the two newest H-class units (CPV Valley 2018, Cricket Valley 2020) — i.e. the
model carries a **merit-order inversion inside CC_REGULAR**, running the older Capital_Hudson and
NYC units ahead of the newer ones, and that inversion is **worsening** at Cricket Valley
(−0.441 → −0.608 → −1.010).

**P4's declared verdict is FALSE, and the reason is a defect in my own statistic — disclosed, not
repaired into a pass.** P4 ranked by **|gap|**, which mixes over- and under-dispatch, so the
in-sample top-3 is dominated by the two big *under*-runners (CPV −0.766, Cricket −0.686) and the
overlap reads 1 of 3, firing the "new plant" falsifier on Zeltmann and Astoria Energy. Ranked by
**over-run** — which is what C1's over-shoot actually is — the 2022 top-3 is
{2539, 56196, 55375} against an in-sample top-3 of {2539, 56196, 57664}, an overlap of 2 of 3,
and the new-plant reading dissolves. **I report P4 as declared (does not fire) and do not claim
the alternative ranking as its verdict**; the substantive conclusion — no new plant object — rests
on the full seven-plant table above, which is sign-consistent across all four years and needs no
ranking at all.

## 4. Two competing mechanisms, independently refuted

### 4.1 Availability (M3) — REFUTED by the overlay's own coverage

CC_REGULAR windows in the committed `campd-unit-outages-perunitmerit-NYISO.csv`:

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| class windows | 161 | 182 | 148 | 182 |
| class GW-days out | **654.2** | 698.3 | 645.0 | 721.0 |

2022's coverage is **ordinary**, not thin — it sits between 2024 and 2023. And at the plants that
matter, GW-days out in 2022 vs the in-sample mean: **Bethlehem 40.1 vs 21.1** and **Zeltmann 52.1
vs 29.4** — the two largest over-runners carry **nearly double** the derate in 2022 and over-run
anyway. (Astoria Energy is 11.0 vs 16.7, i.e. less; Cricket Valley 40.9 vs 59.5 and CPV Valley
23.1 vs 39.8 both carry less derate in 2022, which is *why* their under-run is smallest that
year.) **A thinner 2022 input is not the story** — this is the neiso-85/86 hypothesis the
touchpoint loop exists to test, and here it returns a clean negative.

### 4.2 Merit position as a *fuel-level* effect (M2) — NOT SUPPORTED at band grain

The economic share moves **+1.05 pp** against a declared 3.0 pp bar. A fuel-regime story in which
$6.45 Henry Hub widens the CC-vs-ST_GAS spread and pushes CC up the economic bands predicts a
much larger share move than that. **The merit problem this session did find is
LOCATIONAL and INTRA-CLASS** (§3.1: older downstate/Capital_Hudson CCs ahead of newer ones), not
a fleet-wide fuel-level effect — and it is present in every training year, so it does not need
2022 to be identified.

## 5. What this hands forward (all of it in-sample, none of it against 2022)

The correctly-specified object is: **NYISO CC_REGULAR carries two persistent, opposite-signed,
growing zonal errors — NYC over, Capital_Hudson under — that cancel at class grain in
2023-2025.** Consequences for the standing queue:

- **It re-ranks the named objects.** Object 3 of the session charter (the winter downstate
  locational premium, `INTAKE-SPEC-nyiso156` Leg 2, blocked on identification) is the one this
  measurement most directly implicates: NYC's over-run is positive in all four years and
  **winter-loaded in all four**. Objects 1 and 2 (the NYC persistent-base limb's basis, the
  unit-grain D-2/C8 re-base) are **not reached** by this: both are `ST_GAS` mechanisms, and
  CC_REGULAR's D-2 forced energy is 0.077-0.337 TWh — an order of magnitude too small to move a
  ~1 TWh zonal gap. **Neither is re-tested or re-adjudicated here** (DO-NOT-REDO respected).
- **A class-grain C1 pass is not evidence of zonal correctness, and this ISO now has a measured
  instance.** Whether C1 should see a zonal decomposition is a **rubric question and therefore an
  owner question**; this session neither proposes nor prejudges it, and no gate moved.
- **The Cricket Valley / CPV Valley deficit is the sharper end.** It is monotone
  (−0.441 → −0.608 → −1.010 at Cricket) and it is the *growing* half of the offset. nyiso-186's
  plant-grain pass (`_nyiso186_cc_attribution.json`, on the superseded nyiso-186 control) recorded
  Cricket Valley as the **largest positive** excess of 2023 (+1.24 TWh on its own basis); on the
  current keeper it is a **deficit**. Whatever moved it between those keepers over-corrected, and
  that is an in-sample, committed-artifact question a next session can take with zero LP.
- **Not an arm.** Nothing here is a mechanism, a parameter or a candidate. No screen is
  pre-registered, because phase 0 returned a diagnosis rather than a lever.

## 6. Reported at full magnitude — things measured that are not the finding

### 6.1 P5 — the model **does** burn CC_REGULAR oil, and 2022 is not its largest year

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| CC_REGULAR `mw_oil` energy, TWh | **0.353** | 0.082 | 0.259 | 0.673 |

The prediction (≤ 0.05 TWh) is **falsified**, and the shape refutes a 2022-specific dual-fuel
story outright: 2025 carries nearly twice 2022's oil. `dual_fuel_switching` needs no attention
from this result.

### 6.2 A sidecar-basis note (documented behaviour, confirmed by measurement)

`class_band_hourly.mw` **includes** the re-attributed oil MW while `class_hourly.mw` does not:
`Σ_band mw − class_hourly = mw_oil` to four decimals in **all four years** (0.3531 / 0.0819 /
0.2587 / 0.6725 against oil 0.3531 / 0.0818 / 0.2587 / 0.6725). This is exactly what
`scripts/run_calibration_full.py` L680-682 documents (*"the class_hourly view is mw − mw_oil"*).
The band table in §2 is therefore built **net of oil**, on `class_hourly`'s own basis; the gross
basis is in the machine record and **changes no verdict** (P2 +0.870 gross vs +0.855 net; P1
+1.00 pp gross vs +1.05 pp net).

### 6.3 The C1 benchmark basis is NOT the CAMPD plant sum, and its offset is unstable

C1 scores against the bench `classFull` series, which sits **below** the CAMPD plant sum in every
year, by an amount that swings by a factor of five:

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `classFull` TWh | 31.564 | 33.012 | 34.060 | 33.544 |
| CAMPD plant sum TWh | 33.551 | 33.455 | 36.440 | 33.880 |
| difference | **−1.987** | −0.443 | **−2.380** | −0.336 |

**This is why §3's numbers are not C1's numbers.** C1 reads **+4.35 TWh** for 2022; this session
reads **+2.36 TWh** against CAMPD. Both are correct on their own basis, and **this session uses
CAMPD consistently on both sides in all four years**, which is what makes the cross-year and
cross-zone comparisons in §3 sound. The `classFull`-minus-CAMPD swing (−2.0 / −0.4 / −2.4 / −0.3)
is itself an odd bimodal pattern in a benchmark series, **reported here and claimed as nothing** —
it is not this session's object and no conclusion above depends on it.

### 6.4 Pre-existing failures at HEAD — re-measured, not repaired (rule 25)

Unchanged from nyiso-209's report, re-measured on this branch: the six charter-named files read
**36 failed / 69 passed**, and `tests/scoring/test_gate_a_provenance.py::test_live_board_passes`
fails on **MISO's** stale gate-(a) stamp (miso-232 promoted on `main` without the board re-key).
**Neither is this lane's to fix.** `scripts/probes/nyiso198_rebuild_checks.py --year 2024` was run
as the environment check: it reproduces its committed record and `git status --porcelain -uno` is
**empty** (its own "VERDICT: STOP" is the nyiso-198 gate, not drift). **G-DRIFT is not owed** —
no arm reached a solve, so there is no control to validate.

## 7. Governance

| item | state |
|---|---|
| **Rule 1 `[R-STRUCT]`** | a structural mis-specification named; no residual optimized, no mechanism proposed |
| **Rule 22** | 2022 already spent by nyiso-209; committed artifacts re-read only; **nothing identified against 2022**; the object is in-sample and step 3 is unblocked |
| **Rule 29** | phase 0 only; no screen, no arm, no solve, no bundle — (c) has nothing to delete |
| **Rule 15** | no run produced, so nothing to register |
| **Rule 28(b)** | NYISO matrix shard stamped in this session; **no cell verdict letter moves** |
| **Rule 25** | NYISO only; MISO's gate-(a) failure reported, not touched |
| **Rule 27** | no source file ≥ 300 lines pushed |
| **Markers / keeper / gates** | untouched; D-5(b) does not attach (no candidate) |
| **Owner cards** | all five stay UNRULED; per card (v), the 2022 CAMPD conduct was read only through the committed bench of an already-scored year, never to identify a coefficient |

---

*(nyiso-210, 2026-09-06. The pre-registered verdict fired and the session reports its mechanism
refuted on the same artifacts; the answer came from the axis the pre-registration had ranked
third. A clean negative on three named mechanisms, and one structural finding that needs no
held-out year to be true.)*
