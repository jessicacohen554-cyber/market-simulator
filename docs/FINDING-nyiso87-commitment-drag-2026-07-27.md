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
| C-sweep | `nyiso87_c*_minrun*` | C with longer min-run (probe arms) |
| D | `nyiso87_d_*` | `td_loss_factor` — see §5, a labelled probe only |

*(Results table filled in below as arms complete.)*

---

## 4. Results

*(pending — arms solving)*

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
  probe**, to quantify the sensitivity and bound how much of the C1 cell is a
  level effect. **It is not a keeper candidate on this evidence.**
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
