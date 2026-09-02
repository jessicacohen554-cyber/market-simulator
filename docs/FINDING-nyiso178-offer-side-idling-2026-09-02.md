# nyiso-178 — the `ST_GAS` availability envelope is NOT binding in ANY year, in EITHER direction: the brief's offer-side type is CONFIRMED on the LP's own envelope, the merit guard's non-effect is DIAGNOSED, and the natural offer-shape successor is REFUTED before a solve

**Session:** nyiso-178, NYISO backcast-calibration track, 2026-09-02.
**Keeper: UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`** (bundle
`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target
grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**ZERO SOLVES.** No parameter touched, no band swept, no arm built, no run
registered — **by the pre-registration's own stop condition S3, which fired.**
**Gates:** `results/calibration/PREREG-nyiso178-offer-side-idling.md`, committed
with the probe at `31180c9b` **before either ran**, including its §5 amendment
(two construction defects found by CODE READING, corrected before any execution).
**Machine artifact:** `results/calibration/_nyiso178_offer_side_idling.json`;
probe `scripts/probes/nyiso178_offer_side_idling.py`.

---

## 1. The one-paragraph answer

nyiso-177 §7.1 sized an over-booked `ST_GAS` outage envelope (0.50–0.56 of the
bin-capacity-year against a 0.10–0.15 EFOR+planned norm) and handed it forward
with a **stated type**: an offer-side object. **The type is confirmed, and by a
stronger measurement than the one that proposed it.** Against the **exact
envelope the LP carries** — built by calling the engine's own
`bins_to_fleet` → `generators_to_fleet_arrays` on the keeper's own
`ScenarioConfig`, not reconstructed by hand — the model's `ST_GAS` sits at its
own ceiling in **0 / 0 / 4 hours of 8,760**, at a mean utilisation of
**0.391 / 0.315 / 0.286**, and **never in a single hour of the top price decile
of any year**. The over-booking therefore constrains nothing: it cannot be
causing the 2023 over-run (there is 60 % headroom) and it is **not** causing the
2025 under-run either (**2.2 GW of already-derated headroom sits unused at a
mean price of \$176/MWh**). That closes the whole measured-availability-input
family as a lever against `ST_GAS` **in both directions**, with a stated re-open
condition — the same disposition nyiso-173 reached for CC, now established for
steam. What the session does **not** deliver is the repair: the natural
successor, an `ST_GAS` duty curve mirroring the adjudicated
`chp_layup_duty_curve`, is **REFUTED on its own pre-registered gate** (G3
`NEITHER`) and was not built. The object survives, re-typed and much better
bounded.

---

## 2. The year signature, which is what the gates were shaped around

Disclosed in PREREG §0.1 as the one quantity measured before the gates were
written. Model P1 `class_hourly` against the committed `classFull` benchmark:

| year | model TWh | actual TWh | delta | C1 |
|---|---|---|---|---|
| 2023 | 11.999 | 8.141 | **+3.858** | **FAIL** |
| 2024 | 9.799 | 9.913 | −0.115 | pass |
| 2025 | 10.014 | 13.712 | **−3.698** | pass |

**The model's `ST_GAS` is FLAT (12.0 → 9.8 → 10.0) while the market's CLIMBS
(8.1 → 9.9 → 13.7).** C1-2023 is the over-shooting end of a **response** defect,
not a standalone level error, and any instrument that buys 2023 by cutting steam
further would deepen a 2025 miss that is already the same size with the opposite
sign. That is why the arm's gate A3 was written as "must move toward actual in
2023 **and** 2025 both".

---

## 3. G1 — **OFFER-SIDE**, and the instrument had to be repaired to say so honestly

### 3.1 The probe-construction repair, disclosed

PREREG §5.3 already corrected §5.2's envelope from a difference to a product
(`availability = (1 − WEFOR(age) − DERATE(age)) × ufac`, `fleet/arrays.py:1097`).
**That corrected reconstruction was still invalid, and its own output said so:**
the model's `ST_GAS` dispatch **exceeded** it at p99 (1.025 / 1.062 / 1.065),
which a ceiling cannot do. Rather than gate on a bound the data had just
falsified, the envelope was rebuilt by **calling the engine** —
`load_or_synthesize_bins` → `bins_to_fleet` → `generators_to_fleet_arrays` on the
keeper's exact `ScenarioConfig` — so the envelope is the LP's own array, not an
approximation of it. **The swap is conservative in the right direction:** the
exact envelope (mean availability 0.384 / 0.364 / 0.416) is *tighter* than the
overlay-only upper bound (0.468 / 0.443 / 0.501), i.e. it makes the OFFER-SIDE
branch **harder** to reach, not easier. The hand reconstruction is reported
alongside so the correction is auditable rather than asserted.

### 3.2 The measurement

| year | LP `ST_GAS` cap | mean availability | envelope | model | actual | **hours AT envelope** | mean util | p99 | max |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 8,902 MW | 0.384 | 29.96 TWh | 12.00 | 8.14 | **0** (0.00 %) | 0.391 | 0.860 | 0.940 |
| 2024 | 8,902 MW | 0.364 | 28.40 TWh | 9.80 | 9.91 | **0** (0.00 %) | 0.315 | 0.870 | 0.900 |
| 2025 | 8,902 MW | 0.416 | 32.43 TWh | 10.01 | 13.71 | **4** (0.05 %) | 0.286 | 0.872 | 1.000 |

**G1 ⇒ OFFER-SIDE** on its pre-registered bar (< 1 % of hours at the envelope in
every year; the AVAILABILITY-SIDE branch needed ≥ 5 % in any year).

### 3.3 The decisive line — the envelope does not bind in the SCARCITY hours either

Utilisation by **actual RT LBMP decile** (report, not gate). 2025:

| decile | mean price | envelope MW | model MW | util | p95 util |
|---|---|---|---|---|---|
| 0 | \$20.29 | 3,821 | 689 | 0.178 | 0.297 |
| 5 | \$48.46 | 3,799 | 1,313 | 0.316 | 0.648 |
| 7 | \$69.95 | 3,790 | 1,603 | 0.368 | 0.819 |
| 8 | \$94.89 | 3,563 | 1,429 | 0.359 | 0.865 |
| **9** | **\$176.25** | **3,658** | **1,442** | **0.359** | 0.874 |

**In the top three deciles of 2025 the model's `ST_GAS` output is FLAT — 1,603 →
1,429 → 1,442 MW — while the price rises from \$70 to \$176 and the envelope
holds at ~3.6–3.8 GW.** The measured fleet also saturates, but ~1,100 MW higher:
2,547 / 2,328 / 2,597 MW average (CAMPD **gross**, so ~4–6 % above a net basis;
the level comparison carries that caveat, the G3 shares below do not). **2.2 GW
of already-derated, in-envelope steam goes unoffered or over-priced at
\$176/MWh.** No availability input can reach that: an input can only *lower* the
envelope, and it would have to remove more than the entire unused headroom before
it began to bind.

### 3.4 Robustness — the tightest defensible envelope, and it does NOT flip the verdict

The LP's `ST_GAS` bins carry a **stamped `online_year` of 2010** (the CAMPD bin
synthesis), not their EIA-860 vintages, so `THERMAL_AVAILABILITY`'s escalation
past its 30-year onset **never fires** for a NY steamer built 1951–1977. A reader
could reasonably object that the envelope is therefore too loose. Re-scaling the
statistical layer to each plant's true capacity-weighted EIA-860 vintage:

| year | availability | hours at envelope | mean util | top-decile util |
|---|---|---|---|---|
| 2023 | 0.312 | 154 (1.76 %) | 0.481 | 0.631 |
| 2024 | 0.294 | 234 (2.67 %) | 0.391 | 0.501 |
| 2025 | 0.338 | 296 (3.38 %) | 0.352 | 0.440 |

**Even on that counterfactual — tighter than anything the LP actually runs — the
verdict is `MIXED`, never `AVAILABILITY-SIDE`.** The stamped-vintage fact is
reported as a real data-fidelity gap (§7), not used as a lever.

### 3.5 The standing instrument limit, stated

`class_hourly` carries a **class aggregate**; per-generator model dispatch is in
no keeper artifact (the standing nyiso-172 §2.5 / nyiso-173 limit). So "at the
envelope" is measured on the class, and an individual bin could be at its own cap
while the class is not. That caveat is materially weakened but not removed by the
size of the gap: the unused headroom is **2.2 GW of a 3.7 GW class envelope**, not
a marginal bin.

---

## 4. G2 — **DISCHARGED**: the guard is working exactly as designed, and that is precisely why it removes nothing

`campd_outage_merit_order_guard` is keeper-armed and exists to take economically
idle windows out of the mechanical-outage envelope, yet `booked_share` moves
0.536 → 0.534 / 0.560 → 0.560 / 0.501 → 0.501. The reason is now measured, over
the `ST_GAS` windows the guard **KEPT**, attributed across the three fail-safe
exits its own code defines (`outage_detect.MeritOrderPanel.is_economic_layup`):

| exit | share of kept window-hours |
|---|---|
| priced, `out_of_merit_share` **below** `MERIT_OOM_FRAC` | **0.8083** |
| unit **unidentified** by the panel | 0.1917 |
| span **unpriceable** | 0.0000 |
| no panel for the year | 0.0000 |

**Single cause 0.81 ≥ the 0.80 bar ⇒ DISCHARGED.** The guard is not broken and it
is not inert: it **removed 449 `ST_GAS` windows / 221,016 window-hours**, at a
mean `out_of_merit_share` of **0.989** — near-certain lay-ups. What it kept is
**450 windows / 362,736 window-hours** whose measured `out_of_merit_share` has
mean **0.173** and **median 0.000**: in the median kept window the unit was *in
merit in every priceable hour* and was off anyway. Against a fail-safe test that
removes a window only on positive evidence at `MERIT_OOM_FRAC = 0.9`, with the
reference clearing cost set at the `MERIT_RCC_PCTL = 0.9` quantile of running
SRMC, those windows read **mechanical** and are correctly kept.

**The conclusion, stated plainly: the residual over-booking is NOT reachable by
this guard at its committed constants, and it is not a defect in the guard.** No
constant was touched or swept (stop condition S1; rule 23 `[R-FROZEN-DERIVE]`).
The 19.2 % unidentified leg is four units — `2480:2`, `2682:9`, `2682:10`,
`8906:CT0001` — carried as a named remainder, not a proposal.

---

## 5. G3 — **NEITHER**: the offer-SHAPE hypothesis is REFUTED, and stop condition S3 fires

The pre-specified arm was an `ST_GAS` duty curve — the class sibling of the
**adjudicated keeper** `chp_layup_duty_curve` (nyiso-149), disjoint by class
scope, zero new price constants. It was conditional on G3 finding the defect in
the offer's **shape**: the model running steam as baseload where the market runs
it as a peaker. Measured within actual-RT-LBMP bands, on shares (basis-invariant):

| year | model bottom-half share | measured | ratio (bar ≥ 2.0) | model top-decile | measured |
|---|---|---|---|---|---|
| 2023 | 0.383 | 0.345 | **1.108** | 0.156 | 0.190 |
| 2024 | 0.358 | 0.319 | **1.121** | 0.146 | 0.181 |
| 2025 | 0.365 | 0.317 | **1.152** | 0.126 | 0.150 |

The model is **consistently but only marginally** more bottom-heavy than the
market — 1.11–1.15× against a bar of 2.0 — and it is **less** top-heavy in every
year, not more. **G3 ⇒ NEITHER** (the SHAPE branch fails on the ratio; the LEVEL
branch fails too — the max per-band departure from the annual ratio is 0.181 /
0.190 / **0.389**, so 2025 is not uniform, and the model is not top-heavy).

**S3 fires: the arm is not built and no solve is spent.** That is the session's
most valuable negative: a well-precedented, zero-DOF, structurally attractive
instrument is refuted for **zero solves** on a bar fixed before it was measured.

**What the band table says instead** (reported, not gated): the error is close to
a **multiplicative level in 2023** — ratio 1.233 / 1.366 / 1.454 / 1.390 / 1.367
/ 1.305 / 1.300 / 1.194 / 1.140 / **1.009**, i.e. the model is over everywhere
and converges to the market exactly at the top — and a **top-weighted deficit in
2025** — 0.919 / 0.858 / 0.750 / 0.716 / 0.667 / 0.664 / 0.626 / 0.629 / 0.614 /
**0.555**. Whatever carries this moves the class's whole offer *position* between
years, and it hurts most where price is highest. It is not a duty-role
misallocation.

---

## 6. G4′ — **DISCHARGED**: no unattributed `ST_GAS` forcing channel

Every armed candidate from the list fixed in PREREG §5.1 either carries an
`ST_GAS` D-2 row or is inert for the class from committed bytes. Eleven are
armed: `reliability_floor` (+ its plant exclusions), `nyiso_gas_commitment_bridge`
(+ six legs, all attributed under the bridge's own D-2 id), `chp_steam_following`
and `chp_layup_duty_curve` (both **CHP-class scope only** — `ST_GAS` is excluded
by construction in `campd_bins.fleet_to_bins`). **No D-2 `ST_GAS` mechanism was
absent from the fixed candidate list**, so the list did not miss a channel either.

Forced share, **report only** (PREREG §5.1 disclosed the ≥ 95 % bar as vacuous
before it could be exploited):

| year | forced TWh | forced share | `reliability_floor` | bridge |
|---|---|---|---|---|
| 2023 | 2.474 | 0.177 | 2.360 | 0.114 |
| 2024 | 2.800 | 0.237 | 2.638 | 0.162 |
| 2025 | 2.457 | 0.198 | 2.291 | 0.166 |

Roughly **80 % of the class's energy is economic clearing**, not forcing — which
is what makes §3's headroom an offer statement rather than a floor statement.

---

## 7. G5 — a rule 19 `[R-ONE-MECH]` availability STACK is **FLAGGED**, and it is also **PROVABLY INERT**

`ST_GAS` unavailability is derived by **two mechanisms for one phenomenon,
multiplied**: an age-escalated statistical NERC-GADS layer
(`THERMAL_AVAILABILITY["ST_GAS"] = (0.06, 0.21, 0.003, 30, 0.04, 0.002, 30)`) and
the measured CAMPD window overlay. **Neither relief field is set** —
`wefor_residual`, `gas_st_wefor_base_override` and `wefor_residual_groups` are all
`None` in the keeper — so the two compose with no reconciliation. The exact
decomposition, 2023:

| plant | LP MW | overlay `ufac` | × statistical | = composed |
|---|---|---|---|---|
| 2480 Danskammer | 497.3 | 0.222 | 0.814 | 0.181 |
| 2490 Arthur Kill | 876.6 | 0.855 | 0.810 | 0.693 |
| 2500 Ravenswood | 1,724.8 | 0.786 | 0.816 | 0.641 |
| 2511 E F Barrett | 372.2 | 0.684 | 0.828 | 0.567 |
| 2516 Northport | 1,592.2 | 0.527 | 0.821 | 0.433 |
| 2517 Port Jefferson | 385.0 | 0.925 | 0.811 | 0.750 |
| 2527 Greenidge | 104.5 | 0.964 | 0.809 | 0.780 |
| 2625 Bowline Point | 1,159.6 | 0.148 | 0.838 | 0.124 |
| 2682 S A Carlson | 45.0 | 0.000 | — | 0.000 |
| 8006 Roseton | 1,222.0 | 0.057 | 0.872 | 0.050 |
| 8906 Astoria | 923.2 | 0.177 | 0.873 | 0.155 |

Two things are true at once and both are reported. **(a) It is a genuine rule-19
stack.** The statistical layer is the one `arrays.py:690`'s own comment calls
"fitted to ERCOT's once-through steamers and > 2× every other thermal class", and
NYISO does not set the override that exists for exactly that. **(b) It is
provably inert against this object.** G1 shows the composed envelope is never
binding, so relieving the stack raises a ceiling the model does not reach — it
would move **zero** `ST_GAS` energy. Stop condition S6 forbade an
availability-loosening arm ex ante; **G1 now converts that guardrail from an
argument into a measurement**, which is the stronger form.

**Nothing here was touched.** `THERMAL_AVAILABILITY` is read, never edited or
swept (rule 23); `gas_st_wefor_base_override` was NOT set — a value chosen here
would be a value chosen against a known residual (rule 21 `[R-DOF]`).

---

## 8. Lines CLOSED by this session

* **(a) The measured-availability-input family as a lever against NYISO
  `ST_GAS`, in BOTH directions.** The envelope is unreached in 0 / 0 / 4 hours of
  8,760 and carries 2.2 GW of unused headroom at \$176/MWh. Tightening it cannot
  cure the 2023 over-run (it is 60 % slack) and loosening it cannot cure the 2025
  under-run (the slack is already there). The nyiso-173 disposition for CC, now
  established for steam. **Re-open condition, measurable and stated:** a future
  keeper whose `ST_GAS` utilisation actually reaches its own envelope.
* **(b) The merit-order guard as a repair for the residual over-booking.** Its
  non-effect is now attributed to a single cause at 0.81 — kept windows are
  priced windows the unit sat out while *in* merit — rather than suspected. The
  guard removed 449 windows / 221 kh at mean out-of-merit 0.989; the rest carry
  no positive evidence. Not a defect, and not reachable at committed constants.
* **(c) The `ST_GAS` duty curve (the `chp_layup_duty_curve` class sibling) as
  this object's successor.** Refuted on G3 for zero solves. The model's steam is
  1.11–1.15× more bottom-heavy than the market's against a 2.0 bar, and *less*
  top-heavy in every year. This is not a duty-role defect and a duty curve is the
  wrong instrument for it.

## 9. Handed forward, none scoped here

1. **THE OBJECT, RE-TYPED AND MUCH BETTER BOUNDED.** It is an offer **position**
   object, not an offer **shape** object and not an availability one. Its
   signature is now precise: a near-uniform multiplicative over-offer in 2023
   (band ratios 1.23→1.01, converging exactly at the top) and a top-weighted
   under-offer in 2025 (0.92→0.555), with the class saturating at ~1,450 MW above
   \$70/MWh against a ~3,650 MW envelope and a ~2,500 MW measured fleet. **The
   next lever is whatever moves the class's offer POSITION between years** —
   candidates a successor should enumerate first (rule 19): the downstate
   zonal gas basis and `dual_fuel_switching` in the dear hours, the `peak` band's
   un-grounded 4.2 multiplier (nyiso-169b recorded the CC/CHP `peak` 2.25 as an
   F-class constant with **no NYISO measurement behind it**; `ST_GAS`'s 4.2 is in
   the same position), and `gas_st_committed_hr_mult` 1.32. **`gas_st_startup_cost`
   stays DO-NOT-REDO** (nyiso-172, two independent refusals).
2. **THE MISSING RUNG remains unspent, and its cost is now specified.** PREREG §4
   deprioritized nyiso-177 §7.2's guard-alone-on-incumbent-routing leg as ladder
   bookkeeping for a settled disposition; S3 then freed the solve budget, and the
   rung was still not taken because it is **not a flag**: `campd_attribution_selectors`
   forces `merit_guard` False without `per_unit` **by design** (the rule-19 pair
   guarantee), and both resolvers (`thermal_tranche_csv_for_iso`,
   `outages.unit_outage_csv_for_iso`) only name a `-perunitmerit-` companion. The
   rung needs: a `-merit-` **pair** derived on incumbent routing (both artifacts,
   same basis — trap (b)), both resolvers extended to name it, and the selector
   relaxed *while preserving the pairing invariant* (which the change strengthens
   rather than weakens). That is an API change plus a solve, not a flag flip.
3. **`mustrun_layup_window_mask` (NYISO `U`) now has its census measured.** The
   matched companion `campd-unit-outages-layup-perunitmerit-NYISO.csv` holds
   **449 `ST_GAS` windows / 221,016 window-hours in 2023–2025 at mean
   out-of-merit 0.989**. `outages.unit_layup_csv_for_iso` still resolves only the
   unsuffixed name, so the resolver extension nyiso-177 §7.5 named is still
   required. Whether arming the mask is worth it is untouched here — but note it
   masks **must-run floors** inside lay-up windows, and G4′ measures 80 % of this
   class's energy as economic rather than forced, which bounds what it can move.
4. **A DATA-FIDELITY GAP, newly named:** the LP's `ST_GAS` bins carry a stamped
   `online_year` of **2010** while the EIA-860 fleet carries 1951–1977, so
   `THERMAL_AVAILABILITY`'s age escalation never fires for NYISO steam. §3.4
   bounds its effect (`MIXED`, never `AVAILABILITY-SIDE`) and this session
   proposes nothing — under G1 it is a ceiling nobody reaches. It matters for any
   future lane that *does* make the envelope binding.
5. **C3a-2025 (−11.2 %) is UNMOVED** and remains owner-court
   (`DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending). Not opened.

---

## 10. Honest expected value

**What is delivered.** The chartered question is answered, and answered against a
*better* instrument than the one that posed it: the brief's stated type is
confirmed on the LP's own envelope rather than on a hand reconstruction, and the
confirmation is robust to the tightest counterfactual envelope that can be
defended. Three lines are closed on measurement, one of them (the
availability-input family) closing a whole lever class in both directions with a
stated re-open condition. Two pre-registered construction defects were found by
code reading and corrected **before any execution**, one of which would have
biased G1 toward the brief's preferred answer. A third defect was caught by the
probe's own output — the corrected reconstruction was falsified by a p99
utilisation above 1.0 — and the instrument was replaced rather than the gate
softened. A structurally attractive, precedented successor was refuted for zero
solves on a bar fixed in advance.

**What is NOT delivered, stated without softening.** **No keeper, no candidate,
no run, no repair.** C1-2023 `ST_GAS` is exactly where nyiso-177 left it: named,
sized at +3.86 TWh, and open. The over-booking itself is **not repaired** — it is
now shown to be *inert*, which is a different and lesser result than fixing it,
and a reader should not mistake "the envelope does not bind" for "the envelope is
right": it is still 3.5–5× a documented norm, and it remains wrong on the merits
even though nothing downstream currently depends on it. The missing rung is still
unspent. §9's re-typed object is a **specification, not an identification** — no
mechanism is proposed with measured grounding behind it, and the next session
inherits the same open gate this one did.

## 11. Governance

* **Rule 1 `[R-STRUCT]`** — no residual was consulted in choosing what to
  measure; the one quantity read before the gates were written is disclosed in
  PREREG §0.1. No mechanism was adopted or rejected on whether it moved a fit.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals. Measured series are
  used as the comparison basis for shares, never fed back as an input.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — zero parameters touched.
  `MERIT_OOM_FRAC`, `MERIT_RCC_PCTL`, `THERMAL_AVAILABILITY`, every offer band
  and every hr-mult were read and never written or swept. No artifact re-derived.
* **Rule 19 `[R-ONE-MECH]`** — G4′ enumerates the forcing channels and finds none
  unattributed; G5 flags an availability stack and declines to pull it.
* **Rule 15** — **no solve ran, so nothing is registered on the dashboard.** By
  design (stop condition S3), not omission.
* **Rule 22 `[R-HOLDOUT]`** — every year read is 2023 / 2024 / 2025. NYISO is
  absent from both `complete` and `final`; **no marker was requested**; the
  holdout spend freeze is untouched.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only. No other ISO's artifacts were read or
  written; only the NYISO matrix shard is edited.
* **Rule 28 `[R-MECH-MATRIX]`** — four NYISO cells annotated, **no verdict moves
  and no field changed** (§12).
* **Closed lines respected** — `gas_st_startup_cost` not armed;
  `campd_per_unit_attribution` / `campd_outage_merit_order_guard` neither
  re-tested nor reverted; the unguarded basis and `--no-fullstop-override` not
  re-derived; **no C3c lever opened**; C3a-2025 not opened.

## 12. Matrix (rule 28 b)

Four NYISO cells annotated; **every verdict unchanged**, no field touched.
`campd_outage_windows` stays **`K`**, `campd_outage_merit_order_guard` stays
**`K`**, `offer_curve_by_group` stays **`K`**, `mustrun_layup_window_mask` stays
**`U`**. Guard passes (`scripts/check_mechanism_matrix.py` exit 0), shard passes
`node --check`.
