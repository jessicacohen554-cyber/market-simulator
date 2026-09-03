# PRE-REGISTRATION — nyiso-183 (`ravenswood-availability` lane): is Ravenswood's model availability a MIS-BOOKING, or is its OFFER too cheap?

**Session:** nyiso-183, NYISO backcast-calibration track, 2026-09-03.
**Branch:** `claude/nyiso-183-ravenswood-availability-b8jbex`, fresh off
`origin/main` at `3f254f17`.
**Keeper at entry:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**,
target grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST
MEASUREMENT.** Every bar, every stop condition, every admissible and forbidden
repair form below is fixed here in advance. No number produced by this session's
own instrument exists at the time of writing.

---

## §0 — DISCLOSURE: every read held at writing time

Stated so a reader can judge what could have contaminated the bars below. All of
it is **inherited record or source code**; **no score, metric, residual or
solve output of this session's own making exists**, and `metrics.json` /
`legitimacy_diagnostics.json` of any bundle were **not** opened.

**Inherited findings, read in full or in the cited part:**

1. `docs/FINDING-nyiso181b-stgas-floor-overgeneration-2026-09-03.md` — in full.
   Supplies: the C1-2023 miss is ONE PLANT (Ravenswood 2500, +5.472 / +2.787 /
   +1.618 TWh over its own CAMPD meter, the other ten `ST_GAS` plants netting
   −2.365 TWh); the excess is **economic, not forced** (5.631 of 6.328 TWh in
   or at the money; the floor touches 0.699 TWh at unit grain, 0.0099 at plant
   grain); the floor must NOT be cut; model availability ÷ measured CF by plant
   in 2023 (Danskammer 39.2×, Ravenswood 11.3×, Port Jefferson 7.8×, Arthur
   Kill 4.8×, Northport 2.4×, Barrett 1.3×, Bowline 1.3×, Greenidge 1.07×); the
   rule-17 violation (0.316 / 0.268 / 0.049 TWh in metered-off hours); the D-2 /
   C8 grain under-count (escalated, not mine).
2. `docs/FINDING-nyiso177-availability-basis-root-cause-2026-09-02.md` — in
   full. Supplies: `(2500, ST_GAS)` availability **0.772 / 0.465 / 0.297** on
   the keeper path against **0.129 / 0.097 / 0.111** on the unguarded per-unit
   path; the G2 over-booking (`ST_GAS` booked share 0.536 / 0.560 / 0.501 on the
   keeper, 0.794 / 0.742 / 0.688 on the unguarded arm, against a 0.10–0.15
   EFOR+planned norm); G1's 2×2 (the `_FLEET_GROUP_OVERRIDE` de-stack); G3
   FAILED on both legs; the **rejection of the unguarded arm** (B1: grade 3,
   fails 4, load-weighted price 38.01 / 40.49 / 62.00 against actual RT 32.25 /
   38.12 / 66.43); §7.5's unmade `unit_layup_csv_for_iso` resolver extension.
3. `results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md`
   — in full. The repair template and the evidentiary standard (a plant
   convicted only on **median when-available CF exactly 0.000 in every hour
   block of every year**), and its rule-1 disposition (the fit got worse and the
   repair was promoted anyway).
4. `docs/FINDING-nyiso178-offer-side-idling-2026-09-02.md` §4 only. Supplies the
   guard's class-level census: **449 `ST_GAS` windows / 221,016 window-hours
   REMOVED at mean `out_of_merit_share` 0.989**, against **450 windows /
   362,736 window-hours KEPT at mean 0.173 / median 0.000**, and the three
   fail-safe exits (0.8083 priced-below-frac, 0.1917 unidentified, 0.0000
   unpriceable). **This is the single most bar-relevant read and it cuts
   AGAINST hypothesis A**: at class grain the guard's statistic demonstrably
   separates. §3 G1 below is written knowing that, and is deliberately a
   **per-unit** test of the same thing.
5. `docs/FINDING-nyiso179-st-gas-offer-position-2026-09-03.md` §1 only. The
   offer-POSITION type was refuted at class grain (G1 `NOT-OFFER-GOVERNED`: the
   model dispatches only 0.767 / 0.522 / 0.740 of the `ST_GAS` its own offer
   puts in the money) and the 2025 top-decile deficit decomposes 62 % onto the
   model's own price level (owner-court), 25 % onto offer position, 13 % onto
   dispatch against its own signal.
6. `docs/mechanism-testing-matrix.md` §5.5 (the NYISO header + the full
   nyiso-181 lever queue).

**Source code, read:** `scripts/data/derive_campd_unit_outages.py` (the detector
loop, ll. 1780–1960, and the sidecar writer); `scripts/lib/outage_detect.py`
(`filter_revealed_outages` and the `FULL_STOP_OVERRIDE_*` comment block,
`MeritOrderPanel` / `out_of_merit_share` / `is_economic_layup`,
`build_merit_order_panel`'s docstring, `filter_merit_order_layup`, and the
`MERIT_*` constant block); `src/market_sim/data/outages.py`
(`unit_outage_derate_factors`, `unit_outage_csv_for_iso`,
`_unit_outage_factors_from_events`'s docstring).

**Artifacts, read at header/metadata grain only:**
`data/raw/campd-unit-outages-perunitmerit-NYISO.csv` (header + first row + row
count), `…-layup-perunitmerit-NYISO.csv` (same), `…-perunitmerit-NYISO.meta.json`
(the full `derive_invocation`), the keeper's `run_config.json`
(outage/attribution fields + `git` + `resolved_inputs.campd_unit_outages`), the
keeper bundle's `hourly/` file listing, `frontend/data/backcast/keepers/NYISO.json`
(promotion + determination notes).

**Reproducibility state, established at writing time:** **PR #4656 is CLOSED,
NOT MERGED**, its head branch `claude/nyiso-180-per-generator-dispatch-j20rof`
is **deleted from `origin`**, and no `unit_hourly_*.parquet` for any NYISO
bundle exists on `main` or in this working tree. **Every nyiso-181 dispatch-side
number is therefore currently UNREPRODUCIBLE** and is treated below as
*inherited testimony*, never as this session's own measurement. §4 G4c and §5
state exactly what that costs.

---

## §1 — RULE 19 `[R-ONE-MECH]`, DISCHARGED BEFORE ANY PROPOSAL

**Question: which armed mechanism OWNS the outage-vs-lay-up decision for NYISO
`ST_GAS` on this keeper?**

The keeper's availability envelope for `(2500, ST_GAS)` is
`outages.unit_outage_derate_factors(..., per_unit_crosswalk=True,
merit_order_guard=True)`, which reads exactly one file —
`data/raw/campd-unit-outages-perunitmerit-NYISO.csv` (sha256
`45bc4f7c…`, confirmed in the keeper's `resolved_inputs`). Everything that
decides what is IN that file is decided inside
`derive_campd_unit_outages.main()`'s per-unit loop, in this fixed order:

| # | stage | code | what it decides | keeper setting |
|---|---|---|---|---|
| 1 | detector | `detect_outages_eventbased` (non-coal) | is there a dead span at all | `ST_GAS_CF_PEAK`, committed |
| 2 | revealed-availability filter | `filter_revealed_outages` | dead span that ran through its own tight hours ⇒ **not** an outage | `high_load_pctl` 0.85, `min_inmerit_hours` 24 |
| 2b | **full-stop override** | same function | span with mean CF < `FULL_STOP_OVERRIDE_CF` (0.02) for ≥ `FULL_STOP_OVERRIDE_DAYS` (5) d is **kept as mechanical** whatever the mask says | committed |
| 3 | **merit-order guard** | `filter_merit_order_layup` | span out of merit for ≥ `MERIT_OOM_FRAC` (0.90) of its hours ⇒ **ECONOMIC LAY-UP**, leaves the envelope | `merit_order_guard=True` — **armed on this keeper** |
| 4 | consumer-side floor | `unit_outage_derate_factors` | rows with `duration_days < UNIT_OUTAGE_MIN_DAYS` (5) dropped; CTs excluded | committed |

**ANSWER: stage 3, `campd_outage_merit_order_guard`, OWNS the decision, and it
owns it LAST.** Stages 1, 2 and 2b can only propose a window as mechanical;
stage 3 alone can take a proposed window back out of the envelope. No other
armed mechanism writes availability for this class:
`campd_per_unit_attribution` decides *routing* (which bin a unit's conduct lands
in), not outage-vs-lay-up — nyiso-177 G1 measured it moves `(2500, ST_GAS)` by
at most 0.012. `unit_outage_short_windows`, `unit_partial_outage_windows`,
`unit_outage_fleet_status_scope`, `unit_outage_mixed_gas_routing`,
`unit_outage_lp_capacity_basis` and `historic_outage_overlay` are all
**default-off and OFF on this keeper** (verified in `run_config.json`).
`nysdec_peaker_rule_availability` and the nuclear availability family are
class-disjoint from `ST_GAS` by construction.

**Rule 19 consequence, binding on this session: any repair must CONSTRAIN
STAGE 3, never add a stage 5.** A new availability mechanism stacked on stage
3's residual is forbidden by §5 F4 below, whatever it does to any gate.

**And one structural fact is recorded here, before it is measured, because it is
read off the code rather than off data:** stage 3 can and does **overrule stage
2b**. `filter_revealed_outages`'s own comment states the codebase's
discriminator in terms — *"economic idling backs down but rarely fully STOPS for
weeks: a sustained CF < 0.02 dead stop is the mechanical-outage signature at any
duration"* — and then `filter_merit_order_layup` runs afterwards and may
reclassify that very span as lay-up on a statistic that carries **no
availability information at all** (`HR × delivered fuel` vs the p90 of running
SRMC: it measures whether the unit is EXPENSIVE, not whether it was BROKEN).
Whether that is a defect **in fact** is §4 G1's job, and §0 item 4 is the
committed evidence that at class grain it is **not** — which is why G1 is a
per-unit test with a pre-declared bar, not an argument.

---

## §2 — THE MEASUREMENT (Phase 0, NO SOLVE)

Per NYISO `ST_GAS` unit (facility × unit id) and per year 2023 / 2024 / 2025,
entirely from committed bytes:

* **what the extract books** — `campd-unit-outages-perunitmerit-NYISO.csv`
  window-hours, and the resulting `unit_outage_derate_factors` hourly envelope
  on the keeper path;
* **what the guard removed** — `campd-unit-outages-layup-perunitmerit-NYISO.csv`
  window-hours and each row's own `out_of_merit_share`;
* **what the unguarded path would book** — the same builder with
  `merit_order_guard=False` (reads `campd-unit-outages-perunit-NYISO.csv`);
* **what the meter did** — CAMPD unit-level `grossLoad` for the same unit-hours;
* **the guard's own panel**, rebuilt at its committed constants
  (`build_merit_order_panel(iso="NYISO", year, …, rcc_pctl=MERIT_RCC_PCTL)`), to
  obtain each unit's hourly `srmc` and the ISO-year `rcc`.

**Instrument check G0, run BEFORE any gate.** The rebuilt envelope must
reproduce nyiso-177 §2.1/§2.3's published mean availabilities for
`(2500, ST_GAS)`: keeper path **0.772 / 0.465 / 0.297** and unguarded per-unit
path **0.129 / 0.097 / 0.111**, each to within **±0.005**. **If G0 fails the
session STOPS and reports an instrument failure** — no gate below is scored on
an unvalidated instrument (the nyiso-180 §8.1 / nyiso-181 §6.1 discipline:
repair the instrument, never the threshold).

---

## §3 — THE TWO PRE-DECLARED HYPOTHESES

Both are graded at full magnitude. **They are NOT exclusive** and the session
will not force a single winner.

* **(A) MIS-BOOKING.** Ravenswood's keeper availability is wrong: windows that
  are mechanical outages are being reclassified as economic lay-up by stage 3,
  so the LP is handed ~0.64 of a capacity-year that did not physically exist.
  **Prediction:** the guard's own evidence statistic fails to separate
  Ravenswood's DOWN hours from its RUNNING hours (G1), and the reclassified
  volume is material (G2).
* **(B) OFFER.** Ravenswood is genuinely available and its model offer is too
  cheap relative to the rest of downstate steam, so it displaces Northport /
  Barrett / Bowline. **Prediction:** the merit POSITION is wrong — the model's
  Ravenswood offer sits materially below its own measured SRMC, and/or below
  the downstate-steam peer median while its measured SRMC is above that median
  (an inversion) (G4).

**Ex-ante statement of what B being true would mean, recorded so it cannot be
retro-fitted:** nyiso-179 refuted the offer-POSITION type **at class grain**
(§0 item 5). B here is the **within-class, per-plant** version of that question,
which nyiso-179 did not test. If G4 fires, that is a genuinely new object and
this session will say so; if G4 does not fire, nyiso-179's class-grain refutation
simply extends to the plant and B is dead.

---

## §4 — THE GATES, WITH BARS FIXED NOW

### G1 — DISCRIMINATION: does stage 3's evidence separate DOWN from RUNNING at Ravenswood?

The guard removes a window on the evidence *"this unit was out of merit for
≥ `MERIT_OOM_FRAC` = 0.90 of the span."* That is evidence for lay-up **only if
the same condition does not also hold while the unit is demonstrably available
and generating.** So compute, per Ravenswood `ST_GAS` unit and year, on the
guard's own panel and at its own committed constants:

* `oom_down` = mean `out_of_merit_share` over the unit's guard-REMOVED windows;
* **`oom_run`** = the identical statistic evaluated over the hours the unit was
  **actually RUNNING** (`grossLoad / peak ≥ REAL_RUN_CF`, the panel's own
  revealed-run threshold), i.e. the share of its running hours in which its
  own `srmc` exceeded that hour's `rcc`.

**BAR — G1 FIRES (statistic NON-DISCRIMINATING at Ravenswood) iff the
capacity-weighted `oom_run` over Ravenswood's `ST_GAS` units is ≥ 0.90 —
`MERIT_OOM_FRAC` itself, no new number — in ≥ 2 of the 3 years.**

Reading: if Ravenswood runs while ≥ 90 % out of merit, then "≥ 90 % out of
merit" is a state in which this unit demonstrably **does** generate, so it
cannot be the reason it did not. The test would then have sensitivity 1 and
specificity 0 **for this unit** and carry no positive evidence — and the guard's
own charter is fail-safe: it *"can only ever REMOVE windows it has positive
measured evidence against"*.

**Reported alongside, not gated:** the same pair for every other NYISO `ST_GAS`
unit, and the separation `oom_down − oom_run`, so a reader sees whether
Ravenswood is special or the class is.

### G2 — MATERIALITY of the reclassification

`share_reclass` = (mean keeper-path availability − mean unguarded-path
availability) for `(2500, ST_GAS)`, per year — the capacity-year share stage 3
hands back.

**BAR — G2 FIRES iff `share_reclass` ≥ 0.40 in 2023.** (Inherited testimony
puts it at 0.772 − 0.129 = 0.643; the bar is set well below so G2 tests the
inherited number rather than assuming it, and G0 is what validates the
instrument that produces it.)

### G3 — SELECTIVITY: is the proposed repair a repair, or the rejected arm in disguise?

**Scored ONLY if G1 and G2 both fire.** For whichever admissible repair form
(§5 R1 / R2) G1 grounds, compute with **no solve**, from the two CSVs plus the
rebuilt panel:

* `sel_stgas` = (guard-removed `ST_GAS` window-hours the repair RESTORES to the
  mechanical envelope) ÷ (all guard-removed `ST_GAS` window-hours);
* `sel_fleet` = the same ratio over **every** NYISO unit the guard touched.

**BARS, both must hold for the repair to be proposed:**

* **`sel_fleet` ≤ 0.75.** Above that the repair is materially "turn the guard
  off", which is nyiso-177's B1 leg — **already tested and rejected** (grade 3,
  fails 4, price 38.01 / 40.49 / 62.00 against actual 32.25 / 38.12 / 66.43).
  **This pre-registration declares in advance that nyiso-177's rejection of the
  unguarded arm STILL BINDS and that this session will NOT re-propose it**: if
  `sel_fleet > 0.75`, stop condition S3 fires, hypothesis A is recorded
  **UNREPAIRABLE-BY-THIS-ROUTE**, and no arm is built.
* **at least one NYISO `ST_GAS` unit keeps ≥ 1 guard-removed window**, i.e. the
  repair is not a class-wide disarm dressed as a per-unit rule.

### G4 — hypothesis B: the merit POSITION

* **G4a (measured, no solve).** Ravenswood's panel `srmc` against the downstate
  `ST_GAS` peer set's `srmc` (Arthur Kill 2490, Astoria 8906, Northport 2516,
  Barrett 2511, Bowline 2625), load-weighted over 2023.
* **G4b (measured, no solve).** Ravenswood's panel `srmc` against the hourly
  `rcc` — the share of hours it is genuinely in merit.
* **G4c (needs the model's own offer).** The model's `mc` for Ravenswood's
  `ST_GAS` tranches against its measured `srmc`.

**BAR — G4 FIRES (B is a material carrier) iff EITHER**
(i) the model's Ravenswood `mc` sits **≥ $5/MWh below** its own measured `srmc`,
load-weighted over 2023 (G4c), **OR**
(ii) Ravenswood's model `mc` sits **≥ $5/MWh below** the downstate-steam peer
median `mc` **while** its measured `srmc` is **above** the peer median measured
`srmc` — a measured merit-position inversion (G4c + G4a).

**G4c requires `unit_hourly`, which does not exist on `main` (§0).** Pre-declared
resolution, so the outcome is not chosen after seeing it: if a control replay is
run (§6), G4 is scored in full. **If no replay is run, G4 is recorded
`PARTIALLY TESTED` on G4a+G4b alone and hypothesis B is NOT adjudicated** — it
is neither confirmed nor refuted, and this session will say exactly that rather
than resolving it by assertion.

### G5 — NON-EXCLUSIVITY and the displacement prediction

If G1+G2 fire, the session states, **before any solve**, the prompt's own
prediction as a falsifiable expectation: removing manufactured Ravenswood
volume will **deepen** the other-ten-plant deficit rather than close the class
cell, because that deficit is −5.197 / −6.776 / −7.957 TWh economically with
Ravenswood held out (inherited testimony). **A worse 2024/2025 `ST_GAS` cell is
therefore a PRE-DECLARED EXPECTED OUTCOME of a correct repair, not a
falsification of it** (rule 1 `[R-STRUCT]`, the nyiso-140 precedent). It is
reported at full magnitude and the disposition goes to the owner.

---

## §5 — ADMISSIBLE AND FORBIDDEN REPAIR FORMS, FIXED IN ADVANCE

### Admissible

* **R2 — DISCRIMINATING-POWER PRECONDITION on stage 3 (the primary form).**
  `filter_merit_order_layup` may reclassify a window as economic lay-up only
  when the unit's own **running** hours are out of merit for **less than**
  `MERIT_OOM_FRAC` of them. For a unit that runs while out of merit at or above
  that share, the statistic has no discriminating power and the guard's
  fail-safe direction applies: the window is **KEPT as mechanical**.
  **Zero new constants** — it reuses `MERIT_OOM_FRAC` at its committed value and
  the panel's own `REAL_RUN_CF` run test. **Zero new `ScenarioConfig` fields** —
  it is a correctness constraint inside the existing armed mechanism, not a new
  mechanism (rule 19). **Forward-admissible** (rule 13): it regenerates for any
  year from CAMPD operation + delivered fuel prices, uses no measured outcome,
  and would respond to changed conditions.
* **R1 — STAGE-2b PRECEDENCE (secondary).** A window the full-stop override
  rescued — mean CF < `FULL_STOP_OVERRIDE_CF` for ≥ `FULL_STOP_OVERRIDE_DAYS`
  continuous days — is a mechanical outage by the deriver's **own stated
  signature** and is not eligible for stage-3 reclassification. Zero new
  constants. **PRE-DECLARED CAVEAT, recorded because it weakens R1:** that
  signature's stated premise (*"economic idling backs down but rarely fully
  STOPS for weeks"*) was written about **baseload coal**, and a downstate
  seasonal steam unit plainly **can** sit dead for months while remaining
  available. **R1 is therefore proposed ONLY if ≥ 0.50 of the guard-removed
  `ST_GAS` window-hours sit in windows that stage 2b would have overridden AND
  R1 independently clears G3.** Otherwise R1 is recorded as inadmissible on its
  own premise and is not built.

### Forbidden (each named now, so a later temptation is already answered)

* **F1** — any per-plant hardcoded exclusion, exemption or override for
  Ravenswood, in `data/`, `scripts/` or a config dict. Rule 24 `[R-REGISTRY]`
  names this class explicitly and nyiso-177 G1 removed exactly such a dict
  (`outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}`) from this very path.
* **F2** — any availability haircut, multiplier, cap or blend whose value is
  chosen against a residual, a price gap or the C1-2023 cell. Rule 21
  `[R-DOF]` / rule 5 `[R-NO-MAGIC]`.
* **F3** — re-arming the **unguarded** per-unit extract wholesale. Tested and
  rejected at nyiso-177 (its G1/G3 and the B1 leg); §4 G3's `sel_fleet` bar is
  the operational form of this prohibition.
* **F4** — a NEW availability mechanism stacked on stage 3's residual, or any
  new `ScenarioConfig` scalar. Rule 19 `[R-ONE-MECH]` / rule 24.
* **F5** — moving or sweeping ANY detector constant: `MERIT_OOM_FRAC`,
  `MERIT_RCC_PCTL`, `MERIT_HR_MIN/MAX`, `FULL_STOP_OVERRIDE_CF/DAYS`,
  `HIGH_LOAD_PCTL`, `MIN_INMERIT_HOURS`, `UNIT_OUTAGE_MIN_DAYS`,
  `REAL_RUN_CF`, `ST_GAS_CF_PEAK`. Rule 23 `[R-FROZEN-DERIVE]`.
* **F6** — any same-year hourly availability gate, any pin of a unit to its
  observed CEMS generation, any input rescaled so the model's OUTPUT lands on
  the actuals. Rule 13 `[R-MEASURED]`. **This is named specifically because a
  same-year availability gate WOULD close C1-2023 and has NO forward analogue.**
* **F7** — deleting or narrowing the `ST_GAS` reliability floor, or any
  `ST_GAS` volume-buying lever. nyiso-181 DO-NOT-REDO, and §5.2 of that finding
  shows it closes 2023 by breaking 2024 and 2025.
* **F8** — touching C3a-2025 (owner-court, `DECISION-CARD-nyiso148` Q1), the
  D-2/C8 grain under-count (escalated to the scorer lane, code-generic across
  six ISOs), any non-NYISO matrix shard (rule 25 / 28), or any year outside
  2023–2025 (rule 22: NYISO holds neither `complete` nor `final`, the holdout
  freeze is ACTIVE, 2019 and H1-2026 are NEVER GRANTED, and **no marker is
  requested by this session**).

---

## §6 — STOP CONDITIONS (each fires on its own terms, whatever the residual)

* **S0** — G0 fails ⇒ STOP, report an instrument failure, score nothing.
* **S1** — no detector constant moved or swept, in any branch of this session.
* **S2** — **G1 does NOT fire** ⇒ hypothesis A has no mechanism-level grounding
  by this route; **no availability repair is proposed**, and the session reports
  A as refuted-at-Ravenswood together with §0 item 4's class-grain evidence.
* **S3** — **G3's `sel_fleet` > 0.75, or no `ST_GAS` unit keeps a guard window**
  ⇒ the repair is the rejected unguarded arm in disguise; **no arm is built**,
  and A is recorded UNREPAIRABLE-BY-THIS-ROUTE.
* **S4** — no new `ScenarioConfig` field, no CLI knob, no env var, no
  per-plant dict (rules 19 / 24).
* **S5** — if a repair clears G1+G2+G3, the A/B is **2023 + 2024 + 2025 in ONE
  invocation, years SEQUENTIAL** (rules 16, 12), at most 2 concurrent
  invocations, and is scored **leave-one-year-out within 2023–2025** before any
  promotion is proposed.
* **S6** — the secondary items (`mustrun_layup_window_mask`; the NYC
  persistent-base limb membership review) are **sized only**. Neither is armed
  or proposed unless nyiso-140's evidentiary standard is met on its own source
  data; `mustrun_layup_window_mask` is additionally excluded from this object by
  construction, since nyiso-181 established Ravenswood's excess is **not
  forced**.

**CONTROL AND REGISTRATION (rule 15).** The A/B control is the **committed
keeper bundle**, whose same-HEAD bit-identity nyiso-177's `G-CONTROL` computed
(0 of 52,560 hourly zonal prices differing, all three years). **If any
LP-relevant code has landed on `main` since the keeper's `basis_sha`
`d06e6866`, a control leg is solved and its bit-identity re-verified; a
bit-identical control replay is an INSTRUMENT and registers nothing.** Any
non-control solve that completes is registered on the backcast dashboard **this
session**, keeper or rejected probe.

---

## §7 — WHAT THIS SESSION WILL NOT BE ABLE TO CLAIM

Recorded now so it is not discovered later as a convenience.

1. **If no replay is run, hypothesis B is not adjudicated** (§4 G4c). The
   session will say "PARTIALLY TESTED", not "refuted".
2. **G1 is an identification test, not a physical one.** It can show the guard's
   evidence does not separate down-hours from run-hours at Ravenswood; it cannot
   prove any particular window was a mechanical outage. No instrument in this
   repository can, absent a published NYISO outage schedule the lane does not
   hold.
3. **The over-booking is not repaired by anything here.** nyiso-177 G2 fires on
   the keeper (booked share 0.536 / 0.560 / 0.501 against a 0.10–0.15 norm) and
   R1/R2 both move the envelope the OTHER way — they RESTORE windows to the
   mechanical envelope, so a successful repair makes the booked share **worse**
   against that norm while making the classifier's evidence sounder. **That
   tension is stated here, in advance, as a cost of the repair rather than a
   discovery about it.**
4. **Any A/B degradation in 2024 / 2025 is expected** (§4 G5) and will be
   reported at full magnitude with the disposition put to the owner, never
   withheld and never compensated by a second lever.
