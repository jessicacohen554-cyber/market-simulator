# PRE-REGISTRATION (pjm-161): the PJM measured-outage EVENT CAP

**Session:** pjm-161 (PJM 2022 validation-touchpoint root cause)
**Date:** 2026-08-14
**Branch:** `claude/pjm-2022-validation-rootcause-5xr041`
**Status at time of writing:** Phase 0 COMPLETE, **zero LP solves**. Neither arm
has solved. Committed and pushed BEFORE either arm runs (the pjm-143 / pjm-158
precedent), so every prediction below is falsifiable.

**Holdout posture (rule 22 [R-HOLDOUT]).** The freeze is ACTIVE and untouched;
`final` is EMPTY. **No out-of-training year is solved, scored or registered in
this session.** Both arms are `--year 2023 2024 2025`, one invocation, years
sequential (rules 16 / 12). Every 2022 number quoted below is a READ of the
already-committed, already-registered `2026-08-05-pjm-2022-touchpoint` bundle
and of raw measured inputs — the same posture pjm-157 §1 and pjm-158 §1 took.

---

## §0 — Phase 0 in one table (all measured, no LP)

| # | question | measured answer | probe |
|---|---|---|---|
| **A** | Where does the 2022 `+18.28 TWh` `CC_REGULAR` excess GO? | The energy balance CLOSES. Model **physical** generation is right (−0.90 TWh vs EIA-930 net gen); the model's extra sinks are **+11.12 TWh of net virtual DEMAND** and +2.15 TWh of demand, offset by an **18.22 TWh export shortfall**. The composition is wrong, not the total. | `_pjm161_energy_balance.py` |
| **B** | Is the DA-virtual layer's 2022 clearing a phantom? | **NO — and this OVERTURNS the in-sample reading.** Cleared at actual 2022 DA prices, the raw measured curve's own rule-13 anchor is **+12.25 TWh**, not ≈ 0. The LP clears **+11.12**, a deviation of **−1.13 TWh — the SMALLEST of all four years** (in-sample −6.70 / −4.93 / +0.70). The layer is behaving correctly by its own standard; what is wrong is that a **Day-Ahead financial position is being served as physical RT energy**. | `_pjm161_virtual_2022.py` |
| **C** | Is C3b's 0.206 the C1 object in price space? | **NO — they are separable.** 74.9 % of 2022's C3b squared error is **December alone**; dropping that one month takes NRMSE **0.196 → 0.110**, better than any in-sample year. Within December, the 96-hour **Winter Storm Elliott** window (23–26 Dec, 13 % of the hours) carries **115 %** of the monthly gap — the rest of December is *over*-priced by +$7.78. Elliott contributes only **1.10 of the 19.07 TWh** annual gas excess (5.8 %), and the virtual layer's December position is only **+0.28 of its +11.12 TWh**. | `_pjm161_c3b_months.py`, `_pjm161_december.py` |
| **D** | Why does the model miss Elliott? | Model load in the window is **EXACT** (mean 114,443 MW, max 135,328 — identical to 930). The model runs **+11.5 GW more gas** than actual (48,547 vs 37,093 MW mean; +16.8 GW at the peak), takes **zero** unserved energy, produces **zero** hours > $200 in-window against an actual RT 34, and prices **$100.58 against $494.58**. It sails through the event because it never loses the capacity the event took. | `_pjm161_december.py` |
| **E** | Does the availability envelope carry the event? | **NO — it carries its INVERSE.** The CAMPD overlay asserts **15,555 MW** out during Elliott, its **lowest level of the year**, against an annual mean of 32,726 MW and PJM's own published **31.1 / 35.8 / 27.1 GW forced** (40.7 GW total on 25 Dec). | `_pjm161_outage_inversion.py` |
| **F** | Is that a 2022 artifact or standing? | **STANDING, every year.** corr(derated MW, net load) = **−0.701 / −0.680 / −0.714 / −0.772** (2022/23/24/25) and the top-1 % net-load hours carry only **0.376 / 0.306 / 0.216 / 0.245×** the annual-mean derate. PJM's *published* forced series has the physically correct sign in every year (event/annual = 2.84 / 1.53 / 1.91 / 1.30). | `_pjm161_outage_inversion.py` |

**The mechanism behind E/F, stated once.** The CAMPD detector infers
unavailability from **zero generation**. It therefore cannot see an outage at a
unit that would not have run anyway, and a unit in economic layup **runs** when
prices spike. The detected envelope is a **lower bound** on unavailability whose
error is largest exactly in scarcity — so it hands the LP the most capacity in
the tightest hours. This is the SHAPE consequence of the neiso-63 layup finding
that the holdout freeze itself rests on, which had only ever been stated as a
LEVEL defect. It also **falsifies, for PJM, the documented ground on which
`correlated_forced_outage` is coerced off in backcast mode** — "a backcast's
measured CAMPD overlays carry the real cold events" (mechanism-matrix, FFR-1D).
They carry the inverse.

**Annual levels agree; only the shape is wrong.** CAMPD annual-mean derate
32.7 / 35.9 / 31.2 / 29.2 GW against PJM's published **total** 35.1 / 33.3 /
33.0 / 35.9 GW — within ~7 % except 2025. This is not a level dispute.

---

## §1 — going off-queue, and why (rule 27 [R-MECH-MATRIX])

PJM's lever queue was declared EMPTY at pjm-153 and the lane is PARKED PENDING
OWNER (pjm-155) on `state_carbon_pricing` and the G-20b memo. **This session goes
off-queue by necessity.** The queue was cleared on 2026-08-04; the 2022
touchpoint was spent on 2026-08-05 and the Phase-0 measurements above are newer
than the clearing. Neither parked item addresses what Phase 0 found.

**`state_carbon_pricing`, adjudicated as the prompt required.** It is
sign-matched to 2022 (RGGI would move `CC_REGULAR` **down**, and 2022 is the
year the model is **+18.28 TWh up**) and it is genuinely year-varying in the
right way — Virginia was a RGGI member in 2021–2023 and left on 2024-01-01, and
pjm-146's K3 audit confirms the membership test already reproduces that exit
exactly (`va_expected` 1.0 in 2023, 0.0 in 2024/25, 719 units). **But it is not
this session's lever, on the evidence.** pjm-146 measured `CC_REGULAR`
−16.06 / −13.84 TWh in-sample against keeper errors of −3.45 / +0.32; arming it
would take 2023 to roughly −19.5 TWh, four times outside the ±8 TWh band. That
is the textbook "fixes the held-out year, breaks the training years" signature,
and pjm-146 already named the real defect — **the CC→coal substitution
elasticity** — as the successor. Arming the allowance price to close 2022 would
be closing a residual with a lever whose own magnitude is known-wrong. Left
PENDING OWNER, unchanged, and NOT tested here.

**Cells not re-opened** (adjudicated `R`/`I`/`G`, no new evidence offered
against them): item 15 seam amplitude, item 8 `st_gas_mustrun_p25_level`,
item 10 `winter_citygate_daily`, item 7, the diurnal-amplitude family
(items 12–13), `measured_offer_surface`.

**`dam_availability_rebasis` is `G` for PJM and this is NOT a re-test of it.**
pjm-145 refused `pjm_dam_availability` *as built* on two measured grounds, both
attaching to its RESTORE direction: (i) it is ~entirely a restore leg (restore
364/364/360 covered days, remove 0/0/5), and (ii) 66.0/66.6/68.4 % of that
restore is **structural-zero resurrection** — units the finer CAMPD record holds
at zero, revived to λ by the water-fill's `_flat` branch. pjm-145 itself named
three re-open routes; **route (3) is "the event-window-cap form (ERCOT-148/149
shape, PJM-identified)"**, which is exactly what is pre-registered here, on
Phase-0 evidence that did not exist when the cell was set.

---

## §2 — the mechanism

`ScenarioConfig.pjm_measured_outage_event_cap` (new, default **off**,
PJM + backcast gated). Two deltas from the refused overlay, each answering one
refusal ground:

1. **TOTAL-outage basis** — `forced + maintenance + planned`
   (`PJM_OUTAGE_ALL_TYPES`) instead of the unplanned-only
   `PJM_OUTAGE_DEFAULT_TYPES`. The model's incumbent envelope *includes* planned
   outages, so comparing it against an unplanned-only target is a definitional
   mismatch — and that mismatch is what mechanically produced pjm-145's
   restore-on-364-of-365-days, i.e. ground (i).
2. **REMOVE-ONLY** — the cap deepens a class-day toward the measured level and
   **never restores**. `ad == 0 ⇒ new == 0`, so the `_flat` resurrection branch
   is **unreachable by construction**, i.e. ground (ii) cannot arise.

Composition with the incumbent is **min() on availability** — the ERCOT-148/149
precedent, and for the same reason: where two measured layers conflict, the one
that is not an inference wins on the hours it is deeper. The CAMPD unit-grain
overlay keeps sole ownership of **which** units are out (rule 19
[R-ONE-MECH]); this only adds the residual class-day depth the operator's own
record says is missing. `__post_init__` **refuses** arming both PJM overlays.

**DOF (rule 20 [R-DOF]): zero new free parameters.** The MW is PJM's published
`gen_outages_by_type` aggregate; the covered classes and the capacity
denominator are `data.pjm_outages` as-shipped; no threshold is introduced and
none is re-valued. The DOF ledger gains one **measured-external** entry
(18 → 19 on the pjm-146 count basis) at unchanged `n_residual`.

**Rule 13 [R-MEASURED]:** an operator-published, forward-looking outage forecast
posted daily with a 7-day horizon. It regenerates for a forward day and responds
to conditions. It is an INPUT (availability), never an offer, a price, or a
model outcome fed back.

**Known, measured, UNCORRECTED boundary (rule 14's document-the-misalignment
clause).** PJM publishes ONE whole-fleet aggregate, so any non-fossil outage MW
inside it is charged to the fossil-thermal denominator. It is **not** corrected
by a scale factor — a factor tuned to close it would be a fitted parameter
(rules 13 / 21 / 24). Its size is measured ex ante in
`results/calibration/_pjm161_removeonly_exante.json` and reported with the
result whatever it is.

---

## §3 — arms

Both arms solve at **HEAD on this branch**, `--year 2023 2024 2025` in one
invocation, years **sequential** (rule 12: 15 GB RAM + 4 GB swap against
pjm-156's measured ~16 GB/year peak — concurrency licence does not override an
OOM), single delta between them.

| arm | command |
|---|---|
| **CONTROL** `pjm161_ctl_A` | `uv run python scripts/replay_keeper.py results/calibration/pjm152_collapse_A --out-dir results/calibration/pjm161_ctl_A` |
| **TREATMENT** `pjm161_evcap_B` | same `+ --set pjm_measured_outage_event_cap=true` |

The control is solved rather than assumed: this session cannot verify
solve-identity against the pjm-158 basis from git (neither `9f394e41` nor
`bc9e6dbf` is present in this clone), so the keeper bundle is not accepted as a
control on assertion.

---

## §4 — falsifiable predictions

**P1 — LIVENESS.** The cap binds on ≥ 40 class-days per year and removes
≥ 300 MW-year-mean of capacity. **FALSIFIED** below either bar, in which case
the mechanism is inert, the A/B cannot evaluate it, and Phase 0 stands as a data
statement only.

**P2 — NO RESURRECTION (code correctness, guaranteed by construction).**
`max(availability_arm − availability_control)` over every (unit, hour) is
**exactly 0.0**. **FALSIFIED** by any positive value — which would mean the
remove-only claim is false and the arm inherits pjm-145's ground (ii).

**P3 — PRICES RISE, most where the model is tightest.** Removing availability in
stress hours must raise the dual there, so C3a mean LMP moves **UP** in all three
years and the hourly price MAE against actual RT falls in at least the year with
the largest negative C3a (2025, −9.2 % vs DA). **FALSIFIED** if C3a moves DOWN in
≥ 2 of 3 years.

**P4 — THE TAIL FILLS IN.** C3c hours > $200 rise in all three years.
**FALSIFIED** if the count falls in ≥ 2 years. *Note the asymmetric risk that
makes this a real test: 2023's C3a is already +2.9 % vs DA, so P3 and P4 both
push the one year with the least headroom in the wrong direction.*

**P5 — `CC_REGULAR` FALLS.** Less gas available in tight hours means less gas
dispatched, so Δ`CC_REGULAR` (arm − control) is **negative in all three years**.
Against keeper errors of −3.45 / +0.32 / +3.96 TWh this **improves 2024 and 2025
and DEGRADES 2023** — pre-registered as a cost, not hidden.

**P6 — THE ENVELOPE'S SHAPE INVERSION NARROWS.** corr(model unavailable MW, net
load) moves toward zero in all three years from the control's −0.68 / −0.71 /
−0.77. **FALSIFIED** if it moves further negative in any year. This is the
prediction that tests the *stated mechanism* rather than the fit.

---

## §5 — decision rule (rule 1 [R-STRUCT] governs; the fit does not)

The question is **not** which arm has the lower MAE.

1. **The input is more accurate than the one it deepens, and that is decided
   before the solve.** An operator's own published outage record beats a
   zero-generation inference that is provably a lower bound and provably
   inverted in scarcity (§0 E/F). Rule 14 [R-ACCURATE] therefore says: if the
   fit gets **worse**, keep the accurate input, say so plainly, and open the
   root cause — do **not** bury the error back in the inference.
2. **Promotion requires more than a better number.** A promotion candidate must
   (a) pass P2 exactly, (b) show no load-bearing criterion moving PASS → FAIL
   that this pre-registration did not license, and (c) be scored
   **leave-one-year-out within 2023–2025** before it lands.
3. **If gates regress, the arm is registered and NOT promoted**, the matrix cell
   records the measured outcome, and the keeper stands.
4. Either way §0's Phase-0 findings stand on their own — they are no-solve
   measurements of committed inputs and artifacts.

---

## §6 — what this session will NOT do

Solve, score or register any out-of-training year (rule 22; the freeze is
ACTIVE, `final` is EMPTY, and nothing here needs 2022 to be re-run). Arm
`state_carbon_pricing` (§1). Re-open items 15 / 8 / 10 / 7 / 12–13 or
`measured_offer_surface`. Introduce any scale factor, haircut or blend weight to
reconcile the published aggregate's fleet boundary (§2). Disarm
`pjm_da_virtual_bids` — pjm-158 adjudicated that under rule 1 and this session
adds evidence to that escalation rather than pre-empting it (§0 B). Touch
another ISO's matrix shard (rule 25 [R-ISO-SCOPE]).
