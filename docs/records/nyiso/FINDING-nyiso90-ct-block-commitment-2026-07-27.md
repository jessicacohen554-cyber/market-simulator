# NYISO CT_PEAKER: block commitment is eliminated — the runs are the right length, there are too few of them

**Session:** nyiso-90 (CT day-ahead block commitment) · **Date:** 2026-07-27
**Premise:** `docs/FINDING-nyiso89-ct-heat-rate-2026-07-27.md` §5
**Mode:** characterization + one registered arm against a same-HEAD zero-delta control
**Pre-registration:** `docs/handoffs/nyiso90-preregistration.md` (written before the
parameter was derived or any arm was solved)

---

## 0. Summary

The charter named day-ahead **block commitment** as the last standing candidate
for CT_PEAKER's 1.8–2.1 TWh level gap, on the reasoning that "the real fleet
runs several times more hours than any hourly SRMC screen implies — the ordinary
signature of multi-hour DA commitment," and instructed that it be judged against
the **measured run-length distribution** rather than the volume gap.

Measured against exactly that, it is **eliminated**, and the premise it rested on
does not survive the measurement.

1. **The model already reproduces the measured run-length distribution.** The
   brief anticipated that "the model's starts are single-hour-ish." They are not.
   Mean model run length is **6.18 / 6.02 / 8.15 h** against a measured
   **6.61 / 6.31 / 7.92 h**, with matching quartiles — and in 2025 the model's
   runs are *longer* than reality's (§1). This holds at **both** defensible
   online thresholds, so it is not a threshold artifact.

2. **What is missing is STARTS, not duration.** At a common physical bar the
   model synchronizes the CT fleet **1,138 / 937 / 2,061** times a year against a
   measured **4,790 / 4,694 / 4,521** — a factor of 2.2–5.0 too few — at
   essentially unchanged run length (§2).

3. **A minimum-run constraint cannot create a start.** It can only refuse to stop
   a unit the model already started. Applied to a fleet whose runs are already
   the right length, it has nothing to bite on — which the arm measures directly:
   the CT leg floors **12 unit-hours (0.0001 TWh)** in 2023 against the CC leg's
   16,698 unit-hours (1.289 TWh) in the same solve (§3).

The mechanism was built anyway, is committed default-off, and is registered as a
**PROBE**. It is not a keeper candidate and should not be armed.

**The lane's question changes.** "Why are the runs too short?" is answered — they
are not. The open question is now **"why does the model start the CT fleet 2–5×
less often?"**, which converges with nyiso-88 §3's measurement that the real
fleet is *at the money* (margin within ±$6/MWh, roughly half its energy below its
own SRMC). A fleet sitting on the margin has its **start** decisions flipped by
small cost or price errors while its run *durations*, once started, stay right.
That is precisely the signature measured here (§5).

---

## 1. The characterization: run lengths already match

Both sides are compared at **plant level** — the only apples-to-apples unit
available, since the measured artifact counts physical CAMPD turbines while the
model carries one LP row per plant *tranche* of the same iron. A plant is online
when any of its tranches (model) or any of its CT units (CAMPD) is loaded, the
convention `_pjm_plant_online_pattern` already uses. Measured side restricted to
CAMPD `unitType == "Combustion turbine"`, so mixed steam/turbine facilities
(Barrett, Gowanus, Narrows) contribute only their turbines.

`scripts/probes/nyiso90_ct_run_lengths.py`, control bundle
`results/calibration/nyiso90_ctrl_zerodelta`:

| year | series | n_runs | mean | p10 | p25 | p50 | p75 | p90 | frac 1 h |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | **measured** | 4,790 | 6.61 | 2 | 3 | 5 | 8 | 14 | 5.4 % |
| 2023 | control | 2,533 | 6.37 | 2 | 3 | 6 | 8 | 11 | 7.4 % |
| 2024 | **measured** | 4,694 | 6.31 | 2 | 3 | 5 | 8 | 13 | 4.5 % |
| 2024 | control | 2,440 | 7.43 | 2 | 3 | 6 | 8 | 12 | 8.2 % |
| 2025 | **measured** | 4,521 | 7.92 | 2 | 3 | 5 | 9 | 15 | 4.8 % |
| 2025 | control | 4,951 | 12.81 | 1 | 3 | 6 | 11 | 17 | 11.6 % |

The whole interior of the distribution coincides: p25 = 3 h and p50 = 5–6 h on
both sides in every year. The model's p90 is *shorter* in 2023–24 (11–12 h vs
13–14 h) and *longer* in 2025 (17 h vs 15 h).

**Threshold robustness.** The table above thresholds each plant against its own
observed maximum, which is generous to the model (its plants never reach their
real capacity, so its bar is lower). Re-thresholding **both** sides at the same
physical MW — `max(1 MW, 0.05 × the plant's measured CAMPD HSL)` — moves the
counts but not the conclusion:

| year | model runs @ common bar | mean | measured runs | mean |
|---|--:|--:|--:|--:|
| 2023 | 1,138 | 6.18 | 4,790 | 6.61 |
| 2024 | 937 | 6.02 | 4,694 | 6.31 |
| 2025 | 2,061 | 8.15 | 4,521 | 7.92 |

Mean run length agrees within 7 % in every year at the strict bar, and the model
is *longer* in 2025. Whichever bar is used, **the model's CT runs are not short.**

For reference, the committed measured artifacts the charter cites agree with this
picture and with each other: `campd_ct_run_lengths_NYISO.csv` gives a per-unit
class-fallback median of 4.0 h / mean 6.85 h, and the CT class row derived this
session (§3.1) independently gives an equally-weighted p50 of exactly 4.0 h.

---

## 2. Where the energy actually goes

`scripts/probes/nyiso90_ct_gap_decomposition.py` splits the gap on the identity
`energy = online_plant_hours × mean_MW_when_online`, both sides at the same
physical bar, measured converted gross→net with the benchmark's own parasitic
factors (nyiso-89 §1: mixing those bases was worth 2.5× on that session's
headline). Residual on the identity is exactly 0.

| year | plants | measured online h | model online h | **online ratio** | measured MW when on | model MW when on | **loading ratio** | measured TWh | model TWh | energy ratio |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 22 | 31,682 | 7,037 | **0.222** | 72.3 | 50.6 | **0.700** | 2.291 | 0.356 | 0.155 |
| 2024 | 20 | 29,629 | 5,639 | **0.190** | 70.5 | 52.1 | **0.740** | 2.089 | 0.294 | 0.141 |
| 2025 | 19 | 35,802 | 16,789 | **0.469** | 75.9 | 58.5 | **0.771** | 2.718 | 0.983 | 0.361 |

*Scope note.* Both sides are restricted to the **22 / 20 / 19 plants present in
both** the model's CT_PEAKER class and the CAMPD CT-unit record, so the measured
TWh column (2.291 / 2.089 / 2.718) is a subset of the benchmark's full class
actual (2.260 / 2.134 / 3.011) and the two are not directly comparable. The
ratios are what this table is for, and they are computed within the matched set.

Two things follow.

* **The commitment term dominates.** Online hours run 0.19–0.47 of measured;
  loading-when-on runs 0.70–0.77. The fleet is not mainly mis-loaded, it is
  mainly **not synchronized**.
* **That shortfall is entirely a shortfall in starts.** Online hours = starts ×
  mean run length, and §1 shows mean run length is right to within 7 %. So the
  0.19–0.47 online ratio is carried almost wholly by the 0.20–0.46 ratio in run
  *count*.

---

## 3. The mechanism, and the arm that measures it

### 3.1 What was built

`ScenarioConfig.nyiso_gas_bridge_ct` (default **off**) admits the CT class to the
existing P1-native gas commitment bridge, where it can reach the `min_run_hours`
extension leg **and nothing else**.

**This does not widen the fast-start physics gate, and does not re-open
nyiso-87's exclusion.** In `caiso_ra_mustoffer_min_gen`, a unit with min-down 1 h:

* can never trip the *physical* bridge — `gap < min_down` is unreachable when
  `min_down = 1` and every gap is ≥ 1 h;
* is blocked from the *economic* bridge by `RA_BRIDGE_ECON_MIN_DOWN_HOURS`, which
  stays at **4.0** and is untouched.

Minimum-**down** governs how fast a unit can come back — nyiso-87's reasoning that
a fast-start CT is never *held across a gap* is preserved exactly, and pinned by
`TestCTBlockCommitment::test_long_idle_gap_is_never_bridged`. Minimum-**run**
governs how long a started unit must stay on. They are independent physical
properties; the NREL class tables carry both separately for every other fuel.

Nor is it the windowed CT floor the **G-20 probe rejected** on 2026-07-11 (12.8 %
overnight binding against the class's own overnight-offline evidence). That floor
placed CT capacity by an exogenous clock. This one has no clock: it can only
extend a run the model itself started in P0, so an overnight-floored hour is
always the tail of a model-chosen evening start. Declared in `D4_WINDOWS` with
that reasoning.

**Parameters, both measured, both pre-registered before derivation.**
`scripts/data/derive_campd_gas_commitment_params.py --ct` extends the frozen
artifact to the CT class (new output `campd_ct_commitment_params_NYISO.csv`;
80 units, 2,454 MW, 34,024 runs). The default invocation is **byte-identical** —
verified by md5 before and after — because adding CT to the default target set
would have made every mixed steam/turbine plant ambiguous and silently changed
the committed CC/ST rows the keeper's own bridge reads.

* `nyiso_gas_bridge_ct_min_load_frac = 0.238` — cap-weighted p50 of the CT
  loading-when-on ratio, the same statistic and construction as the CC (0.523)
  and ST_GAS (0.239) legs.
* `nyiso_gas_bridge_ct_min_run_hours = 2.0` — cap-weighted **p25** of the measured
  run distribution (cap-weighted p25/p50/p75 = 2 / 4 / 8 h). p25 rather than p50
  because an observed run bounds a min-run **constraint** from *above* (every
  observed run ≥ the constraint), so a low order statistic is the correct
  estimator — the artifact's own docstring says so, and the charter repeats it.
  p25 rather than p10 because runs are computed within a year, so year-boundary
  runs split into two spurious short ones.

*Recorded inconsistency, deliberately not folded in:* the keeper's CC/ST legs use
`p50_capwtd` (21 h / 13 h). Reconciling the conventions would change those legs'
floors — a second delta and a keeper regression risk — so it is a named follow-up.

### 3.2 What the arm measured

`2026-07-27-nyiso-90-ctblock-minrun` (`results/calibration/nyiso90_ctblock_minrun`)
against `2026-07-27-nyiso-90-control-zerodelta`
(`results/calibration/nyiso90_ctrl_zerodelta`), same HEAD, one ScenarioConfig
field apart.

The per-leg trace added this session (so an inert leg can never again be mistaken
for a structural finding — nyiso-89 §4a) reports for 2023:

```
NYISO gas bridge leg gas_cc (min_load_frac 0.523, min_run 21h): 16698 unit-hours, 1.2890 TWh
NYISO gas bridge leg gas_st (min_load_frac 0.239, min_run 13h):  3242 unit-hours, 0.0816 TWh
NYISO gas bridge leg gas_ct (min_load_frac 0.238, min_run  2h):    12 unit-hours, 0.0001 TWh
```

**12 unit-hours.** The leg is demonstrably *live* — a wiring failure would show
exactly 0, and this session went looking for that failure mode first — and it has
essentially nothing to extend, because the model's runs are already at or above
2 h almost everywhere. This is the direct measurement of §1's conclusion, taken
inside the solve rather than inferred from it.

Across the three years the CT leg floors **12 / 28 / 74 unit-hours**
(0.0001 / 0.0002 / 0.0007 TWh) against the CC leg's 16,698 / 18,374 / 11,973.

### 3.3 The arm is live and moves nothing

**Exact-equality check first** (nyiso-89 §4a): merged on
`(year, pass, klass, hour)`, the arm differs from its control by up to
**346.4 / 275.2 / 103.7 MW** in a single hour, with 2.3 / 1.8 / 2.1 GWh of
absolute hourly reshuffling. The mechanism is unambiguously live, so what
follows is a result and not a wiring failure.

**Class level — the gap does not move.**

| year | CT_PEAKER control | arm | delta | gap to actual | **gap closed** |
|---|--:|--:|--:|--:|--:|
| 2023 | 0.4429 | 0.4430 | +0.00011 | 1.817 | **+0.01 %** |
| 2024 | 0.3941 | 0.3942 | +0.00009 | 1.740 | **+0.01 %** |
| 2025 | 1.4069 | 1.4074 | +0.00051 | 1.604 | **+0.03 %** |

The offsetting energy comes from ST_GAS (−0.00006 / −0.00008 / −0.00040) and
CC_REGULAR; system totals are unchanged to five decimals in all three years.

**Run lengths and online hours — unchanged at plant level.** The arm's
plant-level distribution is identical to the control's (2,533 / 2,440 / 4,951
runs, mean 6.373 / 7.432 / 12.811), and online hours move 7,037 → 7,037,
5,639 → 5,639, 16,789 → 16,792. Only the per-*tranche* distribution moves at all
(4,029 → 4,038 runs in 2023), which is the extension acting on individual
tranches and vanishing into the plant envelope.

### 3.4 Gate re-score — every criterion identical

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 / C3a / C3b / C4 / C7 / C8 | PASS | PASS |
| C3c price tail | FAIL | FAIL |
| C5a CO2 | CAVEAT 2025 +7.6 % | CAVEAT 2025 +7.6 % |
| C6 governance | UNATTESTED (probe) | UNATTESTED (probe) |

Determination **NOT-YET** for both, governance UNATTESTED — correct for probes.

**The two flagged guardrail cells are unchanged**, and both were measured rather
than assumed:

* **C1's knife edge.** 2023 CC_REGULAR is **32.513 vs 35.297 = −2.784 TWh** in
  *both* runs, against a ±2.94 band — the 0.156 TWh headroom is untouched. The
  arm's total CC_REGULAR movement is 0.00005 TWh, about 0.03 % of that headroom.
* **C5a.** 2025 system CO2 is **31.390 Mt vs 29.167 actual = +7.6 % in both**
  (2023 +0.5 %, 2024 +1.1 %). The charter warned not to assume the sign of a CO2
  move from added peaker volume at 10–16 MMBtu/MWh; the added volume is 0.0005
  TWh, so there is no move to sign.

**C7/C8 do not gate this class.** CT_PEAKER is 1.5 / 1.4 / 2.0 % of ISO load —
below the 2 % materiality floor — so both are reported-not-gated. D-2 reads
0.0 / 0.0 / 0.01 % forced share against the 15 % peaker cap, and the new
**D-4 row is exercised and PASSES**: `nyiso_gas_commitment_bridge × CT_PEAKER`,
window h0–23, off-window binding 0.0.

### 3.5 Verdict: PROBE — REJECTED as a mechanism, kept default-off

The leg is structurally sound and correctly parameterized, and it is *not*
withdrawn for making the fit worse — it does not make the fit anything. It is
rejected because the phenomenon it models is **already present in the model**.
Arming it would add a mechanism, a D-2 row and two parameters to buy 0.01–0.03 %
of the residual, which rule 19 [R-ONE-MECH] and rule 21 [R-DOF] both argue
against. It stays committed and default-off so the measurement is reproducible
and the CT class row is available to the next session.

---

## 4. Governance

* **Rule 1 [R-STRUCT] / rule 24 [R-FROZEN-DERIVE].** The parameter was fixed by a
  written pre-registration before the CT class row was derived, so it cannot have
  been chosen from what it does.
* **Rule 13 [R-MEASURED].** Both parameters are unit-conduct statistics that
  regenerate for a forward year from the same pipeline and respond to changed
  conditions; neither is a measured outcome fed back to close a residual.
* **Rule 17 [R-FLOOR-WINDOW] / rule 19 [R-ONE-MECH].** No windowed floor,
  temperature boxcar or CT-scoped `reliability_floor` row was added. The
  mechanism is a leg of the existing bridge under its existing D-2 id, not a new
  floor stacked on the same phenomenon.
* **Closed routes stay closed.** The NYCA/East spin gate, the J/K ladders, the
  h14-21 peak-window floors, `td_loss_factor` as the C1 instrument and the
  West/Panhandle topology split are untouched.
* **Rule 16 [R-ALLYEARS].** One bundle, `--year 2023 2024 2025`, sequential within
  each invocation; control and arm run as separate concurrent invocations.
* **Gas seam.** The keeper's `nyiso_downstate_ct_gas_daily=True` /
  `nyiso_downstate_ct_gas_basis=False` seam is inherited unchanged by the replay.

---

## 5. What is next

The block-commitment candidate is closed. The lane's open question is now
**start frequency**, and the evidence points at one place.

* nyiso-88 §3 measured the real fleet **at the money**: DA-when-running minus own
  SRMC of −$1.39 / +$5.82 / +$3.49 per MWh, with 68 / 52 / 50 % of its energy
  *below* its own SRMC. A fleet that sits on the margin is one whose **start**
  decisions are decided by small errors, while its run durations — set by the
  commitment block once started — stay right. That is exactly the asymmetry
  measured here: run length correct, run count 2–5× short.
* The 50 % of measured energy sitting *below* its own SRMC is the specific thing
  a merit-order LP structurally cannot produce, and it is roughly the size of the
  gap. Whatever admits it — day-ahead self-scheduling against a forecast rather
  than a realized price, start-cost recovery over a multi-hour block making a
  below-SRMC hour rational, or unit-level reliability commitment finer than the
  published ladder nyiso-83 already measured at +0.11 TWh — is a **start**
  mechanism, not a duration one.
* Loading-when-on is a real but secondary term (0.70–0.77) and should not be
  chased before the start term; it is partly downstream of which hours the fleet
  is committed in.

**Not folded in here, still open:** the nyiso-88 §5 bench multi-class collapse
(cross-ISO scorer defect, needs its own lane and owner scoping) and the
minimum-energy screen for the CT heat-rate derive (nyiso-89 §5b).
