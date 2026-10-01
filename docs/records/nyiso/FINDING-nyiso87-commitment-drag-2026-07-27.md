# NYISO commitment drag — replacing the h14-21 must-run with min-run commitment (nyiso-87)

**Date:** 2026-07-27 · **Session:** nyiso-87 · **Branch:**
`claude/nyiso-gas-commitment-bridge-6n8p2h` · **PR:** #3012 ·
**Premise:** `docs/FINDING-nyiso-calibration-reconciliation-2026-07-27.md`
(nyiso-86 §2 wedge, §3 interchange, §4 floors/CHP) and
`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §7 ·
**Keeper at session start:** `2026-07-26-nyiso-81-floor-rederive`
(determination NOT-YET; no calibration-complete marker, so 2023-2025 only).

**Owner directive (2026-07-27), which this session executes:**

> The h14-21 peak-hour must-run is INACCURATE — turn it off. The model is
> under-running gas through the belly/peak and serving those hours with
> imports; real NYISO gas runs there because of RA commitment, AS provision,
> and economic must-run with MINIMUM RUN DURATIONS — units drag at min-load so
> they are ready to respond to peaks. Replace the windowed floors with
> commitment physics and TRY INCREASING MIN RUN DURATION. Every floor we have
> added was a compensation for this missing commitment drag.

---

## 1. What was turned off, and what was deliberately left on

NYISO carried **13 enabled** reliability-floor limbs. Ten of them belong to
five h14-21 evening ramp families; three are unwindowed.

| ramp family | zone / class | limbs | disposition |
|---|---|--:|---|
| `NYC_ST_ev` | NYC ST_GAS | 2 | **OFF** (peak window) |
| `NYC_CT_ev` | NYC CT_PEAKER | 2 | **OFF** (peak window) |
| `LI_CT_ev` | Long_Island CT_PEAKER | 2 | **OFF** (peak window) |
| `LI_ST_ev` | Long_Island ST_GAS | 2 | **OFF** (peak window) |
| `CH_ST_ev` | Capital_Hudson ST_GAS | 2 | **OFF** (peak window) |
| — | NYC ST_GAS persistent 24 h base | 1 | KEPT |
| — | Long_Island ST_GAS persistent 24 h base | 1 | KEPT |
| — | Capital_Hudson ST_GAS hot step (31.1 °C, unwindowed) | 1 | KEPT |

**Why the three survivors stay.** The directive names the *peak-window*
must-run. The two in-city persistent bases have a 24-hour driver (NYC/LI
voltage-and-local-reliability commitment) and bind in all hours by
construction, not in an asserted afternoon box; the Capital_Hudson limb is an
unwindowed hot-day steam step, also not a peak-hour rule. They are in scope for
a later arm only if the bridge is shown to reproduce them too — flagged to the
owner rather than removed on a reading of the directive it does not make.

**The wiring problem this exposed, and the fix.** `NYC:ST_GAS:tmax` is *three*
registry rows — the persistent base plus the two `NYC_ST_ev` knots — and the
override key was only `"<ZONE>:<CLASS>:<driver>"`, so the peak window could not
be disabled without also killing the always-on base. `apply_reliability_floor_
overrides` now takes an optional fourth segment naming a `ramp_group`
(`"NYC:ST_GAS:tmax:NYC_ST_ev"`), with `_none` selecting the ungrouped step
limbs; the four-segment form wins where both match, and every existing
three-segment override is unchanged. The arm-A override is named once, in
`iso_configs.NYISO_PEAK_WINDOW_FLOORS_OFF`, so the arms, any keeper and the
test all cite one object.

Rule 23 [R-FROZEN-DERIVE] trigger: the **owner's adjudication of the
mechanism**, not a residual moving. Rule 19 [R-ONE-MECH] is satisfied by
SUBSTITUTION — every bridge arm runs with these limbs off, never stacked on
them.

---

## 2. The replacement: `nyiso_gas_commitment_bridge`

P1-native, injected at the P0→P1 seam (`pipeline/solve.py::run_energy_solve`)
like the CAISO RA and ERCOT gas-CC bridges, and — like them — **never
triggering a P2 pass**. It runs the shared ISO-neutral detector
(`model/commitment.py::caiso_ra_mustoffer_min_gen`) on the model's OWN base-cost
P0 run pattern and duals, so no measured generation enters and the mechanism
regenerates in a forecast year (rules 13 [R-MEASURED] / 18 [R-PHYSICS]).

Three legs, each separately gated so the arms can attribute them:

1. **Physical restart bar** — a gap shorter than the unit's min-down always
   bridges.
2. **Economic bridge** (`nyiso_gas_bridge_startup`, default on with the gate) —
   a gap at/over min-down bridges when re-paying the published startup cost
   exceeds the net cost of holding at min-load, priced at the model's own P0
   duals; bounded to one DA operating day (`nyiso_gas_bridge_da_horizon`).
3. **Minimum run duration** (`nyiso_gas_bridge_min_run`) — the owner's named
   ask, and a leg neither existing bridge had. A detected P0 run shorter than
   the unit's minimum run is extended to it, the extension hours the unit was
   OFF are floored at minimum stable load, and the **extended** blocks then
   define the run pattern the gap bridges scan — so an extension that reaches
   the next run CLOSES that gap instead of it being bridged a second time
   (rule 19). `min_run_hours=None` is byte-identical, so CAISO and ERCOT are
   untouched.

### 2.1 Class scope is physics, measured on the real fleet

Eligibility gates on unit physics, never a class-name tuple (rule 18). Measured
by rebuilding the actual NYISO keeper fleet (`run_year(fleet_only=True)`, no
LP) and resolving each row through the bridge's own parameter resolver:

| class | resolvable base tranches | capacity | min-down | startup p50 | bridged? |
|---|--:|--:|---|--:|:--:|
| CC_REGULAR | 22 | 3,141 MW | 4 / 6 / 8 h | $50/MW | **yes** |
| ST_GAS | 11 | 1,215 MW | 8 / 12 h | $35/MW | **yes** |
| CC_CHP | 18 | 1,459 MW | 4–8 h | $50/MW | no — cogen |
| CT_PEAKER | 17 | 224 MW | 1 h | $20/MW | **never** |
| CT_CHP | 13 | 144 MW | 1 h | $20/MW | **never** |
| ST_CHP | 3 | 138 MW | 8–12 h | $35/MW | no — cogen |

The CT classes are excluded by their own physics twice over: a 1 h min-down is
below `RA_BRIDGE_ECON_MIN_DOWN_HOURS` (4 h) so the economic leg refuses them,
and a gap can never be shorter than a 1 h min-down so the physical leg is
unreachable. The `*_CHP` groups are excluded by the detector regardless
(cogens follow their steam host). This is the rule-18 guarantee the charter
asked for, and it is pinned by test rather than asserted.

### 2.2 The measured parameters

NYISO publishes no 60-Day-DAM equivalent of the ERCOT disclosure that
identifies `min_load_frac` there, so
`scripts/data/derive_campd_gas_commitment_params.py` reconstructs the same
LSL/HSL ratio from unit CONDUCT in EPA CAMPD, using the WP-3 loading-when-on
construction (`derive_thermal_tranches.py::_CHP_STEAM_LEVEL_ON_PCTILE`) and the
`derive_cc_committed_pct.py` p5-of-online-hours minimum-stable statistic:

```
HSL_proxy = p99.5 of pooled grossLoad          (robust maximum sustained load)
online    = grossLoad >= max(1 MW, 0.05 x HSL_proxy)
LSL_proxy = p5 of grossLoad over ONLINE hours  (min stable load, ex-transients)
lsl_frac  = LSL_proxy / HSL_proxy
class     = capacity-weighted p50 of lsl_frac across units
```

Taking numerator and denominator from the same meter makes the ratio
independent of the nameplate/outage crosswalk. Measured, NYISO 2023-2025
(78 units, artifact
`data/raw/_processed-legacy/campd_gas_commitment_params_NYISO.csv`):

| class | units | capacity | `min_load_frac` (p25 / p75) | run hours cap-wtd p25 / p50 / p75 | run hours equal-wtd p25 / p50 / p75 |
|---|--:|--:|---|---|---|
| CC_REGULAR | 35 | 7,162 MW | **0.523** (0.514 / 0.677) | 11 / 21 / 133 | 9 / 17 / 44 |
| ST_GAS | 43 | 7,605 MW | **0.239** (0.210 / 0.291) | 3 / 13 / 89 | 2 / 3 / 6 |

Three things worth recording:

- **Outside cross-check.** The CC value, reconstructed purely from conduct,
  lands within 9 % of ERCOT's independently *published* LSL/HSL cap-weighted
  p50 of 0.574. The construction is not self-referential.
- **The two classes genuinely differ by more than 2×**, which is why the bridge
  runs the detector once per class instead of once for both. NYISO's large
  oil/gas boilers turn down far deeper than a combined cycle (Bowline
  0.17-0.21, Roseton 0.19-0.25, Northport ~0.29).
- **The run-length statistic must be capacity-weighted.** Equally weighted, the
  ST_GAS class reads a 3 h median — because E F Barrett's 16-21 MW fast units
  (which the model classes ST_GAS at *plant* level) contribute ~5,000 runs of
  2-3 h against a 585 MW Bowline unit's 38 h. A min-run constraint floors
  committed MW, not committed unit-count, so the capacity-weighted column is
  the identification one, and it is the same weighting `min_load_frac` uses.

**What the measurement says about the owner's "try increasing min run
duration":** it supports the ask for CC and contradicts it for steam. The
published CC table is 5-10 h against a measured capacity-weighted p25 of 11 h
and p50 of 21 h — the table *under*-states NYISO conduct. The gas-steam table
is 24-48 h against a measured p50 of 13 h — it *over*-states it. A caveat cuts
against reading either as a constraint: an OBSERVED run length is an upper-ish
bound on a minimum-run CONSTRAINT (a unit that ran 21 h because it was economic
does not prove a 21 h floor), so the low percentiles bound the constraint from
the side it lives on. Arm C therefore starts at the class-table values and the
sweep probes upward; no keeper value is chosen from a residual (rules 5/13/23).

---

## 3. Arms

All arms are 3-year (2023-2025) single-invocation bundles, years sequential,
at most two invocations concurrent (rules 12/16). Every arm is a
`scripts/replay_keeper.py` single-delta replay of the nyiso-81 keeper recipe on
THIS HEAD, into its own `--out-dir`, so the comparator is a same-HEAD
zero-delta control and never the registered keeper's metrics.

| arm | bundle | delta vs CONTROL |
|---|---|---|
| CONTROL | `nyiso87_control` | none (same-HEAD zero-delta) |
| A | `nyiso87_a_floorsoff` | `NYISO_PEAK_WINDOW_FLOORS_OFF` |
| B | `nyiso87_b_bridge_phys` | A + bridge, physical min-down leg only |
| C | `nyiso87_c_bridge_full` | B + economic leg + min-run at class-table values |
| C-MEAS | `nyiso87_cmeas_minrun` | C with min-run at the MEASURED p50 (CC 21 h, ST_GAS 13 h) |
| D | `nyiso87_d_wedge_probe` | `td_loss_factor` = 0.0251 — see §5, a labelled probe only |

Registered run ids: `2026-07-26-nyiso-87-control`,
`2026-07-27-nyiso-87-arm-floors`, `-arm-b`, `-arm-c`, `-cmeas-measured`,
`-arm-d`.

---

## 4. Results

**Headline: the owner's hypothesis holds, and C1 — NYISO's load-bearing FAIL —
closes on commitment physics with `td_loss_factor` still 0.0.** All six arms
are registered on the dashboard.

### 4.1 The gate board across the lane

| arm | C1 2023 CC_REGULAR | C3a 2023 | C3c 2025 | C5a 2025 | determination |
|---|---|---|---|---|---|
| CONTROL | **−4.11 TWh** FAIL | +2.6 % | 9h / 42h | +8.1 % | NOT-YET |
| A (windows off) | −3.32 FAIL | +4.9 % | 8h | +7.7 % | NOT-YET |
| B (+ physical bar) | −3.20 FAIL | +4.3 % | 6h | +7.5 % | NOT-YET |
| C (+ econ + min-run, tables) | **−2.89 PASS** | +3.3 % | 6h | +7.7 % | NOT-YET |
| **C-MEAS (measured min-run)** | **−2.78 PASS** | +3.1 % | 6h | +7.6 % | NOT-YET |
| D (`td_loss_factor`, probe) | PASS | +7.2 % | **18h** | **+14.2 % FAIL** | NOT-YET |

C1's band is ±min(2 % load, 8) ≈ ±2.94 TWh, so arm C passes with ~0.05 TWh of
margin and C-MEAS with ~0.16 TWh. C3c FAILs in every arm and is the *sole*
remaining blocker — down from C1 + C3c at session start.

### 4.2 The seam moved, under a mechanism with no seam wiring

The nyiso-86 §3 defect (pinned monthly import volume bought in the wrong hours)
improves monotonically across the whole ladder, converging on the measurement
from **both** ends:

| 2023 | CONTROL | A | B | C | C-MEAS | actual |
|---|--:|--:|--:|--:|--:|--:|
| imports hod01-03 (belly) | 3,048 | 2,959 | 2,841 | 2,806 | 2,797 | **2,596** |
| imports hod16-18 (peak) | 2,381 | 2,508 | 2,683 | 2,708 | 2,713 | **2,857** |
| within-month r | +0.072 | +0.086 | +0.106 | +0.107 | +0.108 | — |
| internal diurnal price swing | $7.45 | $8.70 | $8.10 | $8.32 | $8.36 | — |

Nothing in the bridge touches the interchange node. This is §3's causal claim
confirmed by construction: the model bought its quota overnight because its
internal price shape was too flat, and holding committed gas at min-load
through the belly re-prices those hours. The swing is still far short of the
real $22.5 (§3's target), which is why C3c stays open.

### 4.3 CT_PEAKER: the boxcar was hurting the shape it was supposed to fix

Per-year D-1, `profile_r` / `cv_ratio` (cv_ratio 1.0 = model volatility equals
the CEMS actual):

| arm | 2023 | 2024 | 2025 |
|---|---|---|---|
| CONTROL | 0.82 / 5.12 | 0.85 / 4.24 | 0.92 / 2.37 |
| A | 0.89 / 2.80 | 0.93 / 1.84 | 0.95 / 1.24 |
| B | 0.88 / 2.84 | 0.93 / 1.85 | 0.95 / 1.34 |
| C | 0.87 / 1.94 | 0.93 / 1.18 | 0.95 / 1.25 |
| **C-MEAS** | **0.88 / 1.38** | **0.93 / 1.07** | **0.95 / 1.15** |
| D (floors still on) | 0.83 / 4.52 | 0.85 / 3.51 | 0.94 / 1.80 |

The h14-21 floor was CT_PEAKER's **only** forcing mechanism (D-2: 81.3 / 86.1 /
48.3 % → 0.0 / 0.0 / 0.0 % once removed), and removing it improved the class's
shape in every year on both statistics. C-MEAS lands cv_ratio within 7-38 % of
the measured volatility — for a class **the bridge never floors**. That is the
strongest single result of the lane: a boxcar was buying volume at the cost of
shape, and replacing it with commitment physics elsewhere in the merit order
fixes the shape of a class the replacement does not touch. Arm D, which keeps
the floors on, stays bad (4.52 / 3.51 / 1.80) — the control on that claim.

As predicted, CT_PEAKER's **volume** collapses 1.42 → 0.46 TWh against a 2.26
TWh actual. Reported, not patched: whether a peaker AS/commitment story returns
is a separate rule-17 charter for the owner (§6).

### 4.4 D-2: substitution, and LESS total forcing

2023 forced energy on the three merchant gas classes, by mechanism id:

| arm | CT_PEAKER | ST_GAS | CC_REGULAR | total |
|---|--:|--:|--:|--:|
| CONTROL | 0.928 (`reliability_floor`, 81.3 %) | 3.525 (`reliability_floor`) | 0.010 | **4.463** |
| A | — | 2.963 (`reliability_floor`) | — | 2.963 |
| B | — | 2.971 + 0.033 (`bridge`) | 0.280 (`bridge`) | 3.284 |
| C | — | 2.946 + 0.195 (`bridge`) | 1.043 (`bridge`) | 4.184 |

The `reliability_floor` id gives up CT_PEAKER entirely and part of ST_GAS; the
`nyiso_gas_commitment_bridge` id picks up CC_REGULAR and a little ST_GAS —
attribution shift, not new forcing, exactly as the charter predicted. And the
**total falls** (4.46 → 4.18 TWh) while C1 flips to PASS and every class's
shape improves. Less forcing, better fit, better shape.

### 4.5 Min-run: the measurement disagrees with the class tables in BOTH directions

The floor-segment length distribution is where the identified values prove
themselves:

| segments > 24 h | 2023 | 2024 | 2025 | | 16-24 h band | 2023 | 2024 | 2025 |
|---|--:|--:|--:|---|---|--:|--:|--:|
| arm C (class tables) | 46 | 55 | 105 | | arm C | 256 | 392 | 196 |
| **C-MEAS (measured)** | **8** | **8** | **0** | | **C-MEAS** | **532** | **569** | **412** |

Arm C's long tail is gas steam's class-table 24-48 h min-run holding boilers
online roughly twice as long as NYISO's fleet actually does. Replacing it with
the measured 13 h removes the tail; raising CC from 5-10 h to the measured 21 h
fills the 16-24 h band with genuine commitment blocks. Total floored volume
goes *up* slightly (1.25-1.37 vs 1.18-1.21 TWh/yr) while the pathological holds
disappear — the mechanism doing less of the wrong thing and more of the right
one, which no volume metric would have surfaced.

So the owner's "TRY INCREASING MIN RUN DURATION" is **supported by the
measurement for CC and contradicted for gas steam**. C-MEAS moves them in
opposite directions accordingly, and is better than arm C on every gate.

### 4.6 LOYO (rule 22)

The bridge carries **no parameter fitted to any year**: `min_load_frac` and the
min-run hours are pooled 2023-2025 CAMPD statistics, and the three legs are
physics (min-down, startup cost, the restart inequality on the model's own
duals). Every arm scores all three years in one bundle, so the per-year tables
above ARE the leave-one-year-out view, and the direction is consistent in every
year for every arm:

- CT_PEAKER `cv_ratio` improves in 2023, 2024 and 2025 (§4.3).
- Import belly falls and peak rises in all three years.
- C1's per-class cells stay in band in 2023 and 2024 (2025 is vintage-SKIPPED).

No year carries the gain; there is no in-sample/held-out split to overfit.

---

## 4b. Verdict on the candidate

**C-MEAS is the structurally-faithful run of the lane** and the rule-1 keeper
candidate: it replaces an owner-adjudicated-inaccurate boxcar with commitment
physics, closes the load-bearing C1 FAIL without touching demand, forces LESS
in total than the run it would replace, improves every class's diurnal shape,
and every parameter it adds is measured rather than fitted.

Two things stand between it and promotion, and neither is discretionary:

1. **No governance attestation.** C6 is UNATTESTED on every probe in this lane,
   which caps the determination regardless of the other gates. A keeper needs
   `calibration_attestation.json` with the DOF ledger (by UNION with the
   existing keeper's) citing the two `min_load_frac` values and the two
   min-run values to `campd_gas_commitment_params_NYISO.csv`.
2. **C3c still FAILs**, so the determination is NOT-YET either way. Promoting
   C-MEAS changes which run carries NYISO's NOT-YET, not the determination.

The C1 margin is also thin (~0.16 TWh of ±2.94) and should be treated as such.

---

## 5. Arm D: `td_loss_factor` is refuted as the instrument

The charter's arm D closes the C1 2023 level miss with `td_loss_factor`, on the
nyiso-86 §2.1 demand-basis wedge (+2.08 % of load in 2023, +2.94 % in 2024
between `923 gen + measured NI` and the EIA-930 demand the model serves). That
section explicitly left one thing open: *"pin the wedge's decomposition (losses
vs. NYISO-invisible small generation — the Gold Book NYCA energy line is the
cross-check) before choosing the value."*

**That cross-check has already been run, and it refutes the instrument.**
`docs/nyiso-td-loss-resolution-2026-06.md` records it: Gold Book Table I-2
Note 1, verbatim in all three books, states *"All results in the Section I
tables include transmission & distribution losses"*, and the actual NYCA Annual
Energy on that loss-inclusive basis is **147,050 GWh for 2023 — equal to the
EIA-930 NYIS demand the model serves, to the GWh** (2024: 150,938 vs 150,460,
0.3 %). The demand the model serves is therefore *already* loss-inclusive net
energy for load. Setting `td_loss_factor > 0` would add the loss volume a
second time.

Consequences, stated plainly:

- The **wedge is real** — nyiso-86 measured it correctly — but it is **not
  identified as T&D losses**. Whatever it is (NYISO-invisible small generation,
  BTM self-supply metered at the plant by EIA-923, station service, a seam
  accounting boundary), `td_loss_factor` is the wrong name for it, and applying
  it would be a fitted adder with no forward analogue — rule 1 [R-STRUCT] and
  rule 13 [R-MEASURED] both forbid reaching the C1 number that way.
- Arm D is therefore run and registered as an explicitly labelled **diagnostic
  probe**. **It is not a keeper candidate on this evidence** — and the run
  produced INDEPENDENT physical corroboration of the refutation.

**What arm D actually showed.** At `td_loss_factor` = 0.0251 demand rises
147.05 → 150.74 TWh and the gate board moves further than any other arm: C1
PASSES, and C3c improves more than anywhere else in the lane (2025 model tail
9h → **18h** against 42h actual, 0.21× → 0.43×; 2023 clears entirely). On a
fit-first reading it is the best run of the session.

**But C5a breaks.** 2025 CO2 goes +8.1 % → **+14.2 %** vs eGRID — out of the
commercial band, a MODEL MISS — with 2023/2024 also climbing to +7.4/+7.5 %.
That failure is the informative result: if the extra 3.7 TWh were real load the
NYISO fleet serves, burning it would not push measured-plant-rate CO2 four
points past its band. The emissions check independently says what the Gold Book
says from the other direction.

Set against C-MEAS — which flips the same C1 cell on commitment physics with
`td_loss_factor` at 0.0 and leaves C5a at +7.6 % — this is precisely the
comparison rule 1 exists for: two runs both flip the load-bearing criterion,
one through a structurally-grounded mechanism, one through an input the
evidence says is already in the data. The better-fitting one is the wrong
answer.
- **Open item for the C1 lane:** decompose the wedge against the Gold Book
  NYCA energy line and the EIA-923 BTM/sector split, and name a
  correctly-identified instrument for whatever survives. Until then C1's
  load-bearing FAIL has no admissible instrument, and the determination stays
  NOT-YET regardless of what the bridge does to the shape.

---

## 6. Do-not-reject warnings honoured

Recorded up front so the results section cannot quietly violate them:

- **C3c will likely worsen.** More online capacity at the peak means more
  headroom under the $258 mainland roof. C3c is roof-blocked (nyiso-85 §7d),
  not tightness-blocked. Per rule 1, a structurally-correct commitment
  mechanism STAYS even if C3c degrades; the movement is recorded, never acted
  on by reverting.
- **The monthly balance bound.** With net interchange pinned monthly
  (`NYISO_IMPORT_RECON_BAND_FRAC` = 0.02) and every non-gas class pinned, the
  bridge can move annual gas-family volume by at most ~±0.8-0.9 TWh. It cannot
  close the 2023 −4.11 TWh C1 cell alone, and is not judged on that cell.
- **CT_PEAKER collapses in arm A** and the bridge must not rescue it (rule 18).
  The collapse is reported honestly; whether a peaker AS/commitment story
  returns is a separate rule-17 charter for the owner, not something to patch
  with a re-armed floor here.
