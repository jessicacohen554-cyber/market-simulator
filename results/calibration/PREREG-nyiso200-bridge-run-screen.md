# PREREG nyiso-200 — the NYISO gas bridge's P0-pattern dependence: a COMMITMENT-REAL RUN SCREEN (the detector's own G-61 path (b) leg), screened ALONE first and then in the THREE-WAY pairing with `nyiso_ct_peaker_bands_measured` + `cc_duct_peaking_row_scoped`

**Session:** nyiso-200 (`claude/nyiso-gas-bridge-min-run-awz5xt`), 2026-09-06.
**Keeper:** `2026-09-06-nyiso-196-extract-basis` (CALIBRATED, grade 7 of 8, fails 0, C3c the lone
ledgered caveat). **Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §3).
**Solves at time of push: ZERO.** This document is pushed before any arm is solved.
**Owner ruling in session (2026-09-06, verbatim):** *"Is this a recommended keeper candidate? If so
plz promote. If structural integrity improves but gates regress that may still be a keeper.."* —
recorded here before the first solve. It is permissive ("may"), not automatic; §7 states how it is
applied.

---

## §0 — Phase 0 (zero LP): what the nyiso-199 stop actually was, and what the object actually is

Record: `results/calibration/_nyiso200_bridge_phase0.json` (`scripts/probes/nyiso200_bridge_phase0.py`).

**0.1 The nyiso-199 §8.3 STOP fired on rows the span scorer skips by construction.** The two new
D-4 unit-conduct convictions (7314 for 3,210 h, 50978 for 352 h, measured median 0.0 MW) are on
plants the benchmark itself flags `ct_only` — EIA-923 net > 1.1× CAMPD gross, so the hourly CAMPD
series is incomplete and the rider must not convict on it. Both carry the flag in the complete 2023
and 2024 vintages (7314 CF 0.184 / 0.214, 50978 0.127 / 0.125) and lose it only in the preliminary
2025 vintage, where `e_ann` falls back to `c_ann` and the ratio computes 1.00 — the nyiso-145 §3
artifact, guarded since nyiso-150 by a **union of the flag across the scored span**. The keeper's
span bundle unions {2023, 2024, 2025} and its committed diagnostics say so in words ("2025: ct_only
vintage guard extended the flag from sibling-year vintages for 9 plant(s): … 50978 … 7314"). The
nyiso-199 screen bundle scored ONE year, so its union was {2025} alone: **2 of 2** of its 2025
failures are on plants the span guard restores; **0** survive; the like-for-like count (0 ≤ the
keeper's 1) would not have fired the PREREG gate. **Scorer-only repair, landed in this session:**
`legitimacy_diagnostics.ct_only_guard_years` unions over the ISO's training span whatever the
bundle's own years (protective direction only; a span keeper re-scores byte-identically; test
`tests/scoring/test_ct_only_bench_flag.py::test_one_year_bundle_unions_over_the_training_span`).

Two further facts about that stop, stated so no one over-reads it: (a) the production verdict
never consults D-4 for `CC_REGULAR` at all — `calibration_verdict._d4_provenance` escalates only
above the 30 % forced-share cap, and the class reads 2.8 / 0.8 / 1.2 % — so the stop was the
PREREG's own stricter "no new D-4 row" gate, not a C8 FAIL the span would have carried; (b) the
series the conviction read is one the benchmark declines to trust, so it is **unscorable, not
exonerating**: the meter cannot say whether 7314 was on in those hours. The P0-pattern dependence
is therefore judged on the model's own economics (§1), not on that meter.

**0.2 The object is real and it is the detector's, not the band's.** Every bridge leg — the min-run
extension, the online-hours state floor, the gap bridges — anchors on the model's OWN P0 run
pattern. P0 is a base-cost LP that pays no startup on a continuous ramp, so it manufactures runs a
real unit commitment would never start (the G-61 diagnosis the CAISO lane already carries). A merit
change moves P0's shape; nyiso-199 measured exactly that — cheaper `CT_PEAKER` offers displaced two
cycling CCs in P0, left them short P0 runs, and `nyiso_gas_bridge_min_run` extended those into 21 h
min-load holds. Under rule 17 `[R-FLOOR-WINDOW]` the min-run leg's driver is *"a started unit stays
online for its minimum run"* and its evidence for "started" is a P0 run; a run whose whole margin
cannot repay one start is one the driver's own economics say the unit would not have started, so an
extension floored on it binds in hours its own driver says the unit is off. That is the defect, and
it exists independently of any meter.

**0.3 The keeper's own bridge footprint (committed D-2 / D-4 rows)** — the repair can only REMOVE
floor, so this is its pre-solve reachability bound, meter-free and residual-free:

| year | `CC_REGULAR` forced TWh (share) | `ST_GAS` forced TWh (share) | **bound TWh** | CC plants floored |
|---|---|---|---|---|
| **2023** | 0.8815 (2.76 %) | 0.1219 (1.02 %) | **1.0034** | 2539 0.534 / 50292 0.116 / 54574 0.037 / 57185 0.019 / 55405 / 56234 / 56940 |
| 2024 | 0.2802 (0.79 %) | 0.2926 (2.70 %) | 0.5728 | 50292 0.079 / 2539 0.052 / 54574 / 55405 / 57185 / 56234 / 56940 |
| 2025 | 0.4080 (1.21 %) | 0.1621 (1.34 %) | 0.5701 | 50292 0.114 / 2539 0.102 / 55405 0.063 / 57185 0.033 / 56940 / 56234 / 54574 |

Neither 7314 nor 50978 is floored by the keeper in any year; they enter the binding set only under
the CT arm. **The screen year by footprint is 2023** (bound 1.0034 TWh, 1.8× either other year).

**0.4 The eligible population and the screen's bar**, from an on-recipe `fleet_only` rebuild (no
LP): 43 / 44 / 44 rows the detector admits (gas_cc + gas_st, non-cogen base tranches with a startup
cost and a positive min-down); net of the keeper's two armed membership exclusions (13 plant codes),
**21 / 22 / 22 `CC_REGULAR` rows (3,859–3,864 MW) at a $50/MW startup and 7 `ST_GAS` rows
(1,298 MW) at $35/MW**. 7314 (22.94 MW base tranche) and 50978 (45.52 MW) are in the population
in every year at min-down 4 h / $50/MW. The bar is the bridge's own registered startup constant —
`_ra_bridge_unit_params`, the CAMPD-bin NREL/SR-5500-55433 value the economic leg already prices —
so **the repair selects no number** (rule 21 `[R-DOF]`, no ledger entry).

## §1 — The repair, and why it is this one

**Field:** `nyiso_gas_bridge_startup_aware` (gated, default off, `_CACHE_KEY_OPTIONAL_FIELDS` +
pinned default + `TIER_TAGS`, registered on the `gas_commitment_bridge` base row per rule 28(c),
CLI `--nyiso-gas-bridge-startup-aware`, consumer `pipeline.commitment._nyiso_gas_bridge_floor`).
When on, the shared detector's **`startup_aware` run screen** (G-61 path (b), registered for CAISO
as `caiso_ra_bridge_startup_aware` and never wired for NYISO) runs before every leg: a detected P0
run is kept only when its P0 energy margin per MW of capacity,
`Σ_t∈run (LMP_P0[zone,t] − MC[g,t]) × dispatch[g,t] / pmax[g]`, covers the unit's own published
per-MW startup cost. Runs failing it are removed BEFORE the min-run extension, the online-hours
floor and the gap scan. The detector logs a per-leg census (runs detected / dropped, P0 hours
de-anchored, units affected) so the screen reads what the mechanism DID.

* **Rule 19 `[R-ONE-MECH]`** — what already floors `CC_REGULAR`: this bridge (D-2 2.8 / 0.8 /
  1.2 %) and nothing else (`reliability_floor` rows are `ST_GAS`; `CT_PEAKER` carries no floor).
  The repair adds no floor; it narrows the run set every existing leg reads. Same detector, same
  D-2 id, same inputs, same constant.
* **Rule 18 `[R-PHYSICS]`** — gates on the unit's own start cost, never a class name.
* **Rule 13 `[R-MEASURED]` — why NOT the measured-conduct gate the nyiso-199 handoff named.** An
  hourly meter test inside the solve ("do not floor this unit in hours its CAMPD series is dark")
  is a one-sided pin to observed CEMS generation with no forward analogue: it fails rule 13's own
  admissibility test, and on 7314 it would read a series the benchmark declines to trust. The
  plant-level form — a conduct-based membership exclusion — was refused ex ante by nyiso-144
  (*"7314 … is a cycler the model's own P0 over-runs, so its forcing is an offer/economics defect
  and excluding it would bury that error in a membership list"*) and again at miso-170. The
  admissible measured membership channels already exist and stay armed (lay-up, reserve duty). The
  run screen is the economics-side repair those rulings pointed to.
* **Forward-native:** regenerates from a forecast year's own P0 duals, objective and startup table.

**Not done and not proposed:** no new offer band, no bridge parameter, no min-run value, no
per-plant list, no cross-ISO change (CAISO's own leg is untouched; its verdict transfers nowhere).

## §2 — Pre-solve gates (zero LP). ALL passed before this document was pushed.

* **F-1 IDENTITY OFF.** The field default is off; `_nyiso_gas_bridge_floor` with the flag absent
  and with it explicitly `False` return the same array; a supplied census dict changes no floor.
  *(tests `TestCommitmentRealRunScreen`, 7 cases, all pass; 131 in the bridge/detector files.)*
* **F-2 THE MECHANISM DOES WHAT §1 SAYS.** A 2 h P0 fragment at $5/MWh margin (margin/MW $10 <
  the $48.6 f-class start) is extended to min-run without the screen and is NOT extended with it;
  the same fragment at $30/MWh ($60/MW) is still extended. *(same tests.)*
* **F-3 POPULATION AND BAR** are the keeper's own (§0.4): no row enters or leaves the eligible set
  and the bar is the registered startup constant. *(phase-0 census.)*
* **F-4 PLUMBING.** The consumer runs AFTER the generic `prb_overrides` channel applies, so
  `replay_keeper --set` reaches it (unlike the `backcast_config`-resolved fields nyiso-199 guards);
  the CLI threads the named kwarg on both `run_calibration_full` and `run_calibration`. The per-leg
  census log line is the fail-loud signal: a screen run whose log carries no census line did not arm.

## §3 — G-DRIFT (rule 29(b)): the keeper's committed bundle is the control

`git diff f7bb76a5..HEAD` on the solve path touches 53 files / 7,569 insertions. Validated
**empirically**, the nyiso-199 §6 way, rather than by reading hunks: the committed keeper-sha
probe record `_nyiso198_rebuild_checks_2024.json` (the keeper recipe's per-plant / per-band LP
`pmax`, 42 leaves) re-run at HEAD on a fresh cache reproduces **0 differing leaves, max |Δ| 0.0**
— the fleet's capacity basis is unchanged. The one changed input under `_validation-source`
(`actual_lmp.json`) adds PJM load-weighted rows only; NYISO's actuals are untouched. Scorer
changes since the keeper sha are a ruff-format pass and the Y-17 bench-staleness fingerprint;
neither moves a score. **Form 4 is valid: no control solve is spent.**

## §4 — The screens: TWO arms × TWO years, named before any solve

Rule 29 names the screen year by the mechanism's own measured footprint, never by the residual.

* **ARM A1 — the repair ALONE**: `{nyiso_gas_bridge_startup_aware: true}` over the keeper recipe.
  The keeper's bridge floor is largest in **2023** (bound 1.0034 TWh) → screen year A = 2023. The
  year the P0-dependence was measured in, and the year every downstream companion is exposed in,
  is **2025** → screen year B = 2025. A1 changes nothing in P0 (the bridge is applied at the P0→P1
  seam), so its P0 pattern is the keeper's own; what it can do is drop phantom anchors on THAT
  pattern. **An A1 that drops zero runs in both years is a valid result** — the repair is then
  inert on the keeper's recipe and live only under a merit change (G-CTRL form 2's inert-year
  logic), and the three-way arm is where it is screened; it is not a reason to skip A1, because a
  non-zero census on the keeper is a finding about the keeper.
* **ARM A3 — the three-way pairing**: `{nyiso_gas_bridge_startup_aware: true,
  nyiso_ct_peaker_bands_measured: true, cc_duct_peaking_row_scoped: true}`. Both partner fields
  sit at cell **R** with the identical re-test condition ("re-arm only paired, with the bridge
  repair"), they push opposite ways (nyiso-198 moved +1.1 to +1.4 TWh INTO `CC_REGULAR`; nyiso-199
  moved it OUT), and they are not additive. Screen years **2023** (the CT arm's footprint year,
  2.627 TWh newly in-the-money) and **2025** (the exposed year: C3a −6.9 % with a ±10 % band, the
  year the CT arm's stop lived in). Neither field is armed alone anywhere in this session.

Order, ONE LP at a time: A1-2023 → A1-2025 → A3-2023 → A3-2025. Each is a throwaway rule-29
probe: never registered, never a keeper, never quoted as a keeper number, **deleted before merge**
(29(c)); every number cited lands in this document's addendum and in
`_nyiso200_screen_gates_<arm>_<year>.json`. Driver:
`scripts/replay_keeper.py results/calibration/nyiso196_extract_basis --years <Y> --out-dir
results/calibration/nyiso200_screen_<arm>_<Y> --set <field>=true …`.

## §5 — Screen gates. Each may KILL its arm; none may promote one; none reads the target residual.

**A1 (repair alone), per year:**

* **S-1 DIRECTION AND BOUND (meter-free).** The bridge's D-2 forced volume
  (`nyiso_gas_commitment_bridge`, `CC_REGULAR` + `ST_GAS`) must NOT RISE, and the fall is
  ≤ the year's bound (1.0034 / 0.5701 TWh). A rise means the screen added anchors, which its
  arithmetic cannot do: STOP.
* **S-2 CENSUS IDENTITY.** The log census names N runs dropped over M units; the change in
  bridge-floored unit-hours (from the bundle's `floors/<Y>_P1.npz`, mechanism 20) must be confined
  to those M units — a floor moving at a unit with no dropped run is a STOP.
* **S-3 CONFINEMENT.** Energy released from de-anchored floors is re-dispatched inside the gas
  family + imports; a non-gas, non-import class moving by > 0.05 TWh is a STOP.
* **S-4 LOAD-BEARING COMPANIONS.** No C1 class cell, C2, C3a or C3b flips PASS → FAIL; C8/D-4
  adds no failure **at the span guard** (like-for-like, this year's rows, `ct_only` unioned over
  the training span as the span scorer does). Removing a fabricated floor at a plant whose meter
  says it was off cannot be a D-4 regression by construction; anything that IS one is a STOP.

**A3 (three-way), per year — the nyiso-199 §4 gates unchanged, plus the two this pairing owes:**

* **S-1** `CT_PEAKER` rises, inside the CT arm's own bound (≤ 2.627 TWh in 2023, ≤ 2.142 in 2025).
* **S-2** gas-family confinement, |gas family total Δ| ≤ |the CT gain|; no non-gas source.
* **S-3** no load-bearing flip: every C1 class cell (**`CC_REGULAR` included — the duct field's
  nyiso-198 S-4 stop is not exempted here**), C2, C3a, C3b. **C3a-2025 is the named risk** (the
  CT arm alone read −9.1 %, the duct arm alone −10.3 % on the full span; the two push opposite ways
  on volume but the SAME way on price). If C3a-2025 fails, A3 is STOPPED at the screen.
* **S-4 THE DEFECT ITSELF, read directly.** From `floors/<Y>_P1.npz`: bridge-floored unit-hours at
  **7314 and 50978** in A3 must be ≤ the keeper's (0 and 0). Any bridge floor at either plant is
  reported at full magnitude; > 0 at either is a STOP — the pairing exists to remove exactly this.
* **C8 / D-4** no new failure at the span guard; D-2 no new failure.

**What is NOT a gate:** "did C1 `CT_PEAKER` / `ST_GAS` / `CC_REGULAR` improve". S-1 is a bound
from the arms' own arithmetic, S-2 is conservation, S-3/S-4 are do-no-harm and the defect's own
identity. A screen that kills an arm is reported as the session's result and the remaining years
are never spent.

## §6 — If the screens clear

If **A3 clears both years**: the span, `--year 2023 2024 2025` in ONE invocation and ONE bundle
(rule 16), registered the same session (rule 15) with a computed attestation (G-CONTROL, G-DELTA
exactly the three fields, G-INPUTS pinning `phys_*` + the EIA-860 duct sheet + the startup table,
G-DOF **+0**, G-ENGAGE the census logged in every year), the NYISO matrix shard re-stamped
(rule 26(b)). If A1 clears and A3 does not, A1's span is NOT spent on its own unless A1's census
is non-zero on the keeper in a screened year — a repair that changes nothing on the keeper has
nothing to register alone; the finding then records where it is live.

## §7 — Promotion, under the owner's standing formula

The ruling is recorded above and it is permissive, not automatic. It is applied exactly as
nyiso-198 §9.4 and nyiso-199 §8.4 applied it: **the structural half first** — zero DOF, every
value from a registered source, the mechanism doing what its arithmetic says, every moved class
toward its actual where it clears — **then the gates at full magnitude**. A determination that
regresses on a load-bearing family with the structure intact is a candidate the formula admits;
one that collapses (both load-bearing families lost, nyiso-198) or that a protective gate refuses on
a defect the arm itself creates (nyiso-199) is not. The recommendation is written before the
disposition is chosen, in the FINDING, and the owner's formula decides.

## §8 — Governance

* Rule 29 `[R-SCREEN]`: phase 0 (zero LP, §0) → F-gates (§2, zero LP) → named screen years (§4)
  → span only if the arm clears (§6). Screen bundles deleted before merge (29(c)).
* Rule 29(b): no control solve; G-DRIFT §3.
* Rules 21 / 23 / 24: zero free parameters, no DOF entry, no derive re-run, the field registered
  in every registry the siblings are in, no env-var or off-registry channel.
* Rule 25 `[R-ISO-SCOPE]`: NYISO-only wiring; CAISO's own `startup_aware` leg and cell untouched.
* Rule 22: 2023–2025 only. No marker requested; `complete` remains withdrawn.
* Rule 26: the field is on the `gas_commitment_bridge` base row (28(c) escape hatch) and NYISO's
  shard cell is re-stamped in this session with the verdict, whatever it is.
* Rule 1 `[R-STRUCT]`: the arms are never judged by whether a residual moved, in either direction.

---

*(nyiso-200, 2026-09-06. Pushed before any arm was solved. Zero solves at time of push.)*
