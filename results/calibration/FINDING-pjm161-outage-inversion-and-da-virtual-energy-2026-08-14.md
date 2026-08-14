# FINDING (pjm-161): the PJM 2022 touchpoint fails for TWO separable reasons, and neither is a tuning residual

**Session:** pjm-161 · **Date:** 2026-08-14 · **Branch:**
`claude/pjm-2022-validation-rootcause-5xr041`
**Pre-registration:** `results/calibration/PREREG-pjm161-measured-outage-event-cap-2026-08-14.md`
(committed and pushed at `0e27e43`, **before either arm solved**)

**Holdout posture (rule 22 [R-HOLDOUT]).** The freeze is ACTIVE and untouched;
`final` is EMPTY. **No out-of-training year was solved, scored or registered.**
Both arms are `--year 2023 2024 2025`, one invocation, years sequential
(rules 16 / 12). Every 2022 number below is a READ of the already-committed,
already-registered `2026-08-05-pjm-2022-touchpoint` bundle or of raw measured
inputs — the posture pjm-157 §1 and pjm-158 §1 established. **This session does
not spend 2022 and does not ask to.**

---

## §0 — the verdict in one table

| object | what it is | status |
|---|---|---|
| **C1** `CC_REGULAR` **+18.28 TWh** | The DA-virtual layer clears **+11.12 TWh of net virtual DEMAND**, and — the finding that overturns the in-sample reading — **that is not a phantom.** The raw measured curve's own rule-13 anchor at actual 2022 DA prices is **+12.25 TWh**, so the LP sits **1.13 TWh** from its own admissibility reference, the **smallest deviation of any year**. PJM's real 2022 Day-Ahead market held ~12 TWh of net virtual demand and the model reproduces it faithfully — then, having only ONE price and ONE energy balance, **serves a financial position as physical energy**. | **ROOT CAUSE IDENTIFIED, NOT FIXED.** Architecture, inside the owner-closed price-formation frontier; escalated with new evidence (§2). No lever pulled. |
| **C3b 0.206** | **74.9 % of the squared error is December alone**; dropping that one month takes NRMSE **0.196 → 0.110**, better than any in-sample year. Inside December the **96-hour Winter Storm Elliott window carries 115 %** of the monthly gap. The model prices it **$100.58 against $494.58** while running **+11.5 GW more gas than actual** (+16.8 GW at peak), taking **zero** unserved energy and producing **zero** hours > $200 against an actual RT 34. It sails through because the availability envelope never takes the capacity the event took: **15,555 MW out, the lowest level of the year**, against PJM's own published **31.1 / 35.8 / 27.1 GW forced**. | **ROOT CAUSE IDENTIFIED AND A LEVER TESTED** in-sample (§3). |

**The two are separable, measured, not asserted.** Elliott contributes **1.10 of
the 19.07 TWh** annual gas excess (5.8 %), and the virtual layer's December
position is **+0.28 of its +11.12 TWh**. C3b is not C1 seen in price space, and
C1 is not C3b seen in energy space.

---

## §1 — Phase 0(a): the 2022 energy balance, closed

`scripts/probes/_pjm161_energy_balance.py` → `_pjm161_energy_balance.json`.

Closed on ONE internally consistent book — EIA-930's own identity
`Demand = NetGen − TotalInterchange` — because the bench mixes three
measurement systems (930 telemetry, EIA-923 `classFull`, the CAMPD census) that
disagree by 15 TWh in 2022 and were the trap pjm-157 fell into.

| TWh, 2022 | model | EIA-930 | Δ |
|---|---:|---:|---:|
| demand | 810.188 | 808.040 | +2.15 |
| **net generation** | 827.625 | 839.641 | **−12.02** |
| **net export** | 13.421 | 31.643 | **−18.22** |

and the composition of the generation side:

| TWh, model − 930 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| gas | **+20.07** | +2.41 | +8.12 | +20.20 |
| coal | −14.22 | −8.10 | −8.27 | −3.12 |
| oil | −2.72 | −2.71 | −4.14 | −5.32 |
| nuclear | +0.59 | −1.03 | −1.70 | −1.50 |
| net export | **−18.22** | −12.37 | −12.15 | +5.21 |

*Basis caveat on the 2025 export row, stated because it is the one cell that
disagrees across sources.* PJM's own tie-line file
(`PJM_2025_import_export_act_sch_interchange.csv`) integrates to **32.93 TWh**
of net export in 2025 against EIA-930's **17.97 TWh** — a 15 TWh disagreement
between two measured records that does not appear in any other year (2022:
31.78 vs 31.64; 2023: 40.09 vs 39.87; 2024: 33.18 vs 32.56). On the tie-line
basis the model under-exports in 2025 too (23.18 vs 32.93, −9.74). Nothing in
this finding rests on the 2025 export cell, and it is logged as an open
data-provenance item rather than resolved here.

**Where the +22.3 TWh goes.** The model's **physical** generation in 2022 is
essentially right — **−0.90 TWh** against 930 net generation. Its total is not
the problem; its **sinks and its composition** are. The extra sinks are
**+11.12 TWh of net virtual demand** and +2.15 TWh of demand; the missing sink
is **18.22 TWh of exports**. The identity closes exactly:
`−0.90 = +2.15 + 11.12 − 18.22 + 4.02 (storage + losses)` to within the loss
term the model carries and 930 embeds (~2.8–3.4 TWh in every year).

**Two corrections to hypotheses this session tested and dropped, stated against
interest:**

* **Hydro is NOT a −7 TWh hole.** PJM's EIA-930 `NG: WAT` never goes negative in
  any year (min 18–147 MW), so pumping sits in Demand and `WAT` is conventional
  hydro **plus pumped-storage generation, gross**. The right comparison is model
  hydro + PS discharge (13.82 TWh) against `WAT` 15.96 — a **−2.1 TWh** gap, and
  year-invariant (−1.7 to −2.2). The apparent −7 came from netting PS charging
  on one side only.
* **2022 is NOT simply "the standing under-export defect amplified".** It is the
  worst year (−18.22 vs −12.37 / −12.15), but the export gap **absorbs** the
  extra generation rather than causing the extra gas: a model that exported
  correctly would need 18.22 TWh **more** generation, not less. The gas excess
  is a displacement of coal + hydro/PS + oil, and on the basis C1 actually
  scores (EIA-923 `classFull`) 2022 coal is **dead on, −0.01 TWh**.

---

## §2 — Phase 0(c): the DA virtual layer — the in-sample reading was incomplete

`scripts/probes/_pjm161_virtual_2022.py` → `_pjm161_virtual_2022.json`. Same
helper functions, same reference series and same attribution chain as
`_pjm158_virtual_gain.py` / `_pjm158_virtual_basis.py`; only the year set and
the bundle each year's committed duals are read from differ.

| TWh, `+` = net virtual DEMAND | **2022** | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| anchor @ actual DA (the rule-13 reference) | **+12.25** | −0.76 | −1.62 | +0.20 |
| anchor @ actual RT | +18.15 | +5.08 | +3.00 | +6.78 |
| OBSERVED (the LP's own clearing) | **+11.12** | −7.45 | −6.55 | +0.91 |
| **deviation from the DA anchor** | **−1.13** | −6.70 | −4.93 | +0.70 |

**pjm-158 established that the layer's admissibility invariant — net ≈ 0 cleared
at actual DA — is unreachable in this LP. 2022 shows the invariant is not an
invariant at all.** "≈ 0" is a property of the 2023–2025 window, not of the
curve: in 2022 the measured, submitted PJM DA bid curves genuinely cleared
**+12.25 TWh of net virtual demand** at the actual DA price. The model
reproduces that to **1.13 TWh — its best year, not its worst.**

**So the layer is not misbehaving; the architecture is.** A virtual position is
closed out in real time and contributes **zero** annual physical energy. The
model carries one price and one balance, so the position becomes physical MWh
that some generator must produce. Applying pjm-158's own measured channel
(§5.2: ~80 % of a virtual-volume change lands on physical generation,
predominantly `CC_REGULAR`), the 2022 position accounts for **≈ +8.9 TWh of the
+18.28 TWh C1 miss — 49 % — from a mechanism whose in-sample contribution to the
same class has the OPPOSITE SIGN.**

**This is the prompt's "year-varying driver modelled as a constant", and the
constant is not a parameter — it is the architectural assumption that the annual
net DA virtual position is zero.** It is ≈ 0 in every training year and +12.25
TWh in 2022.

**Consequence for pjm-158's warning, which was already the right one.** pjm-158
told the owner that the keeper's near-cancellation is "a coincidence of two
large opposing errors" and that improving PJM's price shape would move the layer
*toward* phantom demand. 2022 is that warning realized without any price
improvement at all: the two terms simply stopped opposing each other.
**ESCALATED, NOT LEVERED.** Nothing is disarmed here — pjm-158 adjudicated that
under rule 1 (disarming degrades every price gate and removes real measured DA
depth) and this session adds evidence to the escalation rather than pre-empting
it. The named root cause is unchanged: **the LP represents one price, gated as
real-time, and the layer needs a Day-Ahead one.**

---

## §3 — Phase 0(b) + (d): C3b is Winter Storm Elliott, and the availability envelope inverts

### §3.1 — the month, then the 96 hours

`_pjm161_c3b_months.py` → `_pjm161_c3b_months.json`. C3b is a **12-month
load-weighted price NRMSE**, so "which bands carry it" is answered month by
month.

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| NRMSE | **0.196** ¹ | 0.158 | 0.117 | 0.138 |
| worst month | **Dec** | Feb | Jul | Jun |
| its share of squared error | **74.9 %** | 55.9 % | 34.7 % | 61.2 % |
| its residual $/MWh | **−42.25** | +12.12 | −7.52 | −17.16 |
| NRMSE dropping that month | **0.110** | 0.109 | 0.103 | 0.093 |

¹ this probe's own reconstruction; the scorer publishes 0.206 on the same
legacy equal-hour basis (2022's bench carries no `rt_lw_mon`). The decomposition
is unaffected.

`_pjm161_december.py` → `_pjm161_december.json`:

| 2022 | hours | model $/MWh | actual RT | residual |
|---|---:|---:|---:|---:|
| December | 744 | 67.86 | 111.93 | **−44.07** |
| **Elliott 23–26 Dec** | **96** | **100.58** | **494.58** | **−394.00** |
| December ex-Elliott | 648 | 63.02 | 55.24 | **+7.78** |

**13 % of the month's hours carry 115 % of its gap** — the other 648 hours are
*over*-priced by $7.78, the same "too dear at the bottom" signature the matrix
records in-sample.

### §3.2 — why the model misses it

Not load: model demand in the window is **exact** (mean 114,443 MW, max 135,328
— identical to EIA-930). Not scarcity pricing machinery either: the model simply
never becomes short.

| Elliott 23–26 Dec 2022 | model | actual |
|---|---:|---:|
| gas dispatched, mean | **48,547 MW** | 37,093 MW |
| gas dispatched, peak | **65,124 MW** | 48,291 MW |
| hours > $200 in-window | **0** | 34 (RT) |
| hours > $1000, whole year | **0** | 18 (RT) |
| max price | $555 | $3,543 |
| unserved energy in-window | **0.0000 TWh** | — |

### §3.3 — THE FINDING: the CAMPD outage envelope is ANTI-CORRELATED with scarcity

`_pjm161_outage_inversion.py` → `_pjm161_outage_inversion.json`. Derated MW from
exactly the windows the model consumes (`campd-unit-outages-PJM.csv` +
`-short-`):

| MW | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| annual mean derate | 32,726 | 35,851 | 31,234 | 29,248 |
| top-1 % net-load hours | 12,299 | 10,985 | 6,754 | 7,157 |
| bottom-50 % hours | 41,409 | 43,147 | 39,632 | 39,138 |
| **ratio top-1 % / annual** | **0.376** | **0.306** | **0.216** | **0.245** |
| **corr(derate, net load)** | **−0.701** | **−0.680** | **−0.714** | **−0.772** |
| named winter event | Elliott | Feb snap | Heather | Enzo |
| event mean derate | **15,555** | 20,404 | 13,054 | 7,205 |
| event / annual | **0.475** | 0.569 | 0.418 | 0.246 |

Against PJM's **own published** `gen_outages_by_type` record for the same days:

| MW | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| published forced, annual mean | 9,332 | 7,653 | 7,698 | 10,531 |
| published forced, event mean | **26,474** | 11,710 | 14,667 | 13,696 |
| **event / annual (published)** | **2.84** | **1.53** | **1.91** | **1.30** |
| published TOTAL, annual mean | 35,135 | 33,298 | 32,973 | 35,870 |

**Elliott, day by day, from PJM's own feed:** forced outages
11,914 → **31,078** → **35,844** → 27,058 MW across 23–26 Dec, 40,723 MW total
on 25 Dec. The model's envelope for the same four days: a flat ~15.6 GW.

**Three statements, each measured:**

1. **The inversion is standing, not a 2022 artifact.** corr is negative and the
   top-1 % ratio is below 1 in **every** year. PJM's *published* forced series
   has the physically correct sign in every year (1.30–2.84×). The two records
   disagree about the SIGN of the relationship between tightness and
   unavailability.
2. **It is a SHAPE defect, not a level dispute.** Annual means agree within ~7 %
   (32.7 / 35.9 / 31.2 / 29.2 GW modelled vs 35.1 / 33.3 / 33.0 / 35.9 published)
   except 2025.
3. **The cause is in the detector's construction.** CAMPD infers unavailability
   from **zero generation**, so it cannot see an outage at a unit that would not
   have run anyway, and a unit in economic layup **runs** when prices spike. The
   envelope is a **lower bound** whose error is largest exactly in scarcity.

This is the **SHAPE** consequence of the neiso-63 economic-layup finding that
the holdout freeze itself rests on — which had only ever been stated as a LEVEL
defect (23–46 % of CC capacity-year booked out against a ~10–15 % real norm).
It also **falsifies, for PJM, the documented ground on which
`correlated_forced_outage` is coerced off in backcast mode** — "a backcast's
measured CAMPD overlays carry the real cold events" (mechanism-matrix, FFR-1D).
They carry the inverse. *(Measured for PJM only; no verdict transfers,
rule 25 [R-ISO-SCOPE]. The other five ISOs are untested and the concept is worth
a census.)*

---

## §4 — the lever: `pjm_measured_outage_event_cap`

Design, admissibility, DOF and the pjm-145 `G` reconciliation are in the
pre-registration §1–§2 and are not repeated. Two points belong here because they
were **decided by measurement during the session**, not before it:

**The ex-ante probe rejected the first design.** `_pjm161_removeonly_exante.py`
measured a **class-grain** cap (the shape `pjm_dam_availability_series` hands
back — one fleet availability FRACTION per class) and found it degenerates under
a remove-only rule into "every class ceilinged at the fleet mean": it bound on
**282 / 297 / 305 of 364 days** for **4,839 / 5,282 / 6,272 MW** year-mean. That
is a level bulldozer that would flatten the real availability differences
*between* classes — not an event cap. It was **discarded before any solve**.

**The implemented form is FLEET grain.** The published FLEET outage MW is
compared against the model's own FLEET outage MW, and one scalar per day
`mu = (cap_sum − published_out) / available_mw` deepens every covered unit
proportionally, preserving relative availability and every zero:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| binding days (of 364/365 covered) | **98** | **61** | **110** |
| removed MW, year-mean | 1,412 | 711 | 1,848 |
| removed MW, on binding days | 5,261 | 4,255 | 6,131 |
| removed MW, max | 15,854 | 11,565 | 14,496 |
| restore days | **0** | **0** | **0** |
| median bind ratio | — | 0.952 | — |

3–8× smaller than the class-grain form and concentrated on a quarter of days.
**P1 (liveness) clears** (bars: ≥ 40 days, ≥ 300 MW).

**P2 (no resurrection) PASSES EXACTLY**, verified on the real
`generators_to_fleet_arrays` path with a control/arm fleet build:
`max(availability_arm − availability_control) = 0.000000000000` over every
(unit, hour). The `_flat` branch that carried 66–68 % of pjm-145's lift is
unreachable by construction.

**The boundary, stated and NOT corrected.** PJM publishes ONE whole-fleet
aggregate; the cap compares it against the model's **fossil-thermal** outage MW
only. In the fleet-grain form that is **conservative** — requiring a fossil-only
number to reach a whole-fleet total makes the cap fire less often and less
deeply than a fossil-only published number would — so what it applies is a
**lower bound** on the correction. No scale factor closes the gap, because a
factor tuned to it would be a fitted parameter (rules 13 / 21 / 24). Measured in
`_pjm161_removeonly_exante.json`: the model's own asserted fossil-thermal outage
already averages **41.7 / 43.2 / 41.2 GW** against PJM's whole-fleet published
**33.3 / 33.0 / 35.9 GW**, which is the neiso-63 level over-count visible
directly — and is why a *level* correction is not what this mechanism is for.

---

## §5 — a THIRD term, already repaired, that a 2022 re-spend would have to carry

The registered touchpoint's `run_config.json` reads
`pjm_seam_measured_ladder = True`, but at its solve date —
**2026-08-05** — `PJM_SEAM_LADDER_BY_YEAR` carried **only 2023–2025**. The gate
in `model/interchange/import_nodes.py` is
`iso == "PJM" and config.pjm_seam_measured_ladder and year in
PJM_SEAM_LADDER_BY_YEAR`, so with no 2022 key the ladder was **inactive** and the
run fell through to `inject_reference_price_firm_export` — a *different* seam
mechanism from the one the keeper's own 2023–2025 years used. pjm-160 derived
and landed the 2019 / 2021 / 2022 ladders **two days later, on 2026-08-07**
(calibration-log `pjm.md`, "B2 EXECUTED"), on the frozen formula with no new
parameter.

**So the touchpoint's −18.22 TWh export shortfall — the worst of the four years
— is in part a year-keying artifact that HEAD has already repaired.** That is
the single largest thing a 2022 re-spend would change.

**And the honest prediction is that it makes C1 WORSE, not better.** Exports are
a sink: an extra TWh exported is an extra TWh generated, and PJM's marginal
class in 2022 is `CC_REGULAR`. The in-sample years, which *do* run the ladder,
still clear ~12 TWh under the measured net export (27.50 / 20.42 vs 39.87 /
32.56), so a repaired 2022 would plausibly move from 13.42 toward ~20 TWh of
export — roughly **+5 to +7 TWh onto a class already +18.28 TWh over**. The
magnitude is uncertain; the **direction is not**.

Stated plainly: **there is no combination of the two identified objects that
makes 2022 pass.** Removing the DA-virtual phantom energy is worth about
−8.9 TWh on `CC_REGULAR`; repairing the seam is worth about +5 to +7 the other
way. A 2022 re-spend is therefore **not a route to a passing touchpoint**, and
it should not be requested as one.

---

## §6 — is the 2022 object closed?

**PARTIALLY CLOSED, and the two halves are in different states.**

| | status | why |
|---|---|---|
| **C3b** | **root cause CLOSED; the repair is TESTED in-sample and its verdict is §7** | The failure is 96 hours of Winter Storm Elliott, the cause is an availability envelope that inverts in scarcity, the inversion is measured in every year, and a zero-DOF mechanism built on PJM's own published record addresses it. |
| **C1** | **root cause IDENTIFIED, NOT CLOSED — and not closable by a lever** | The dominant term is a Day-Ahead financial position served as physical energy by an LP that carries one price. That is architecture, inside PJM's owner-declared-closed price-formation frontier (pjm-142), already escalated by pjm-158 and re-escalated here with the out-of-sample evidence that its in-sample near-cancellation was a coincidence of the training window. No parameter closes it, and any parameter that appeared to would be closing a residual (rule 20 [R-DOF]). |

**What a 2022 re-spend would discriminate — and what it would not.** It would
measure the seam repair's true magnitude (§5) and, with the two identified terms
subtracted, reveal whether a **third** object exists. It would **not** produce a
passing 2022, for the arithmetic in §5. **This session does not request the
spend**: the freeze is active on an unrelated and still-open basis, and the two
questions worth asking of 2022 are both better asked after the DA/RT
architecture question is answered, because that answer changes the largest term.

**What the owner is being asked for.** Nothing on 2022. One thing only: a
decision on the **DA-virtual architecture question** pjm-158 escalated, now with
the out-of-sample measurement that makes it concrete — the layer's C1
contribution is the annual net DA virtual position, a real market quantity that
was ≈ 0 in 2023–2025 and **+12.25 TWh in 2022**, and the model has no way to
carry it as anything but physical MWh.

---

## §7 — Phase 1: the pre-registered A/B — **the lever is REFUTED as built**

Registered runs: **`2026-08-14-pjm-161-control`** (`pjm161_ctl_A`) and
**`2026-08-14-pjm-161-event-cap`** (`pjm161_evcap_B`). Both `--year 2023 2024
2025`, one invocation, years sequential, single delta.
Probe: `scripts/probes/_pjm161_ab.py` → `_pjm161_ab.json`.

**The control validates the A/B: it reproduces the pjm-152 keeper BYTE-IDENTICALLY
— max |Δ| = 0.000000 TWh across every class and every year.** So HEAD is
solve-identical to the keeper's basis for PJM's backcast path, and the new field
is provably inert at its default (its cache key is byte-stable at default and
distinct when armed; both asserted by test, not comment).

### §7.1 — the scorecard against what was pre-registered

| | prediction | measured | verdict |
|---|---|---|---|
| **P1** | ≥ 40 binding days, ≥ 300 MW/yr | **99 / 61 / 110** days; day-mean fleet outage **41,575→43,003 / 43,196→43,909 / 41,222→43,069 MW** | **PASS** |
| **P2** | `max(avail_arm − avail_ctl) = 0` exactly | **0.000000000000** on the real `generators_to_fleet_arrays` path | **PASS** |
| **P3** | C3a up in all 3 **and** hourly MAE falls in 2025 | mean dual **+0.19 / +0.08 / +0.34** $/MWh (up in all 3 ✓) but MAE **+0.07 / +0.02 / +0.03** — *worse* in all three, 2025 included | **PARTIAL — the MAE clause FAILS** |
| **P4** | C3c hours > $200 rise in all 3 | **3 → 3, 10 → 10, 32 → 32** (actual RT 6 / 18 / 59). Max price **identical** at 258 / 301 / 722 | **FAILED OUTRIGHT** |
| **P5** | Δ`CC_REGULAR` negative in all 3 | **−0.508 / −0.283 / −0.688** TWh | **PASS** |
| **P6** | corr(unavailable MW, net load) moves toward 0 | **−0.674→−0.651, −0.704→−0.690, −0.752→−0.720** (✓) **but the top-1 % net-load unavailable MW is UNCHANGED: 23,160→23,160, 25,403→25,403, 24,222→24,249** | **PASS on the letter, FAILS on the substance** |

### §7.2 — what P4 and P6 together establish

**The cap adds essentially ZERO outage in the hours that matter.** The
correlation narrows only because it adds outage in the *middle* of the load
distribution; in the top 1 % of net-load hours the arm's unavailable MW is the
control's to within 27 MW.

**The cause is the design choice this session made deliberately, and it is now
measured to be wrong.** I moved to the TOTAL-outage basis to answer pjm-145's
ground (i) — and PJM's published *total* is dominated by **planned** outages,
which are **scheduled away from peaks**. On the top-20 peak-net-load days the
published total is 12.2 / 14.0 / 18.0 GW against annual means of 33.3 / 33.0 /
35.9 GW, so the cap simply does not bind there. The **forced** component *is*
correctly signed (event/annual **1.30–2.84** in every year) — but a forced-only
comparison is trivially inert, because the published forced mean (7.7 / 7.7 /
10.5 GW) is far below the model's whole-envelope 41.6 / 43.2 / 41.2 GW and the
cap would never fire.

**So the two halves cannot both be satisfied by a cap.** Comparing like with
like requires the total; targeting scarcity requires the forced component; and a
remove-only rule cannot RESHAPE an envelope, only deepen it.

### §7.3 — the disposition

**No gate regresses.** Both arms score **C1 16/16 · free 12/12**, C2, C3a, C3b,
C3c, C4, C8 all PASS; both read NOT-YET only on the C6 governance gate being
UNATTESTED, which is the ordinary state of a replay bundle (the same state
pjm-158's two arms were registered in). Class errors move mostly favourably —
2025 `COAL_BIT` **+5.357 → +3.477**, 2024 `CC_REGULAR` **+0.322 → +0.039**,
2025 `CC_REGULAR` **+3.957 → +3.268** — against 2023 `CC_REGULAR`
**−3.451 → −3.959** and 2025 `CT_PEAKER` **+3.555 → +4.821**.

**It is NOT promoted, and the better numbers are the reason to be careful, not a
reason to promote.** Under rule 1 [R-STRUCT] a keeper is the most structurally
faithful run, not the one with the better residual, and this mechanism **failed
its own targeting test**: it was built to deepen the envelope where the envelope
is measurably too shallow, and P4/P6 show it does not. Adopting it on a mixed
±0.5 TWh residual improvement, after the test that was supposed to justify it
failed, is precisely the trade rule 1 forbids. **Keeper unchanged at
`2026-08-04-pjm-152-collapse`.**

**Leave-one-year-out (rule 22).** The mechanism has **zero free parameters**, so
nothing is identified against any year and there is no in-sample fitting for
LOYO to detect. The observable LOYO content is per-year consistency, and it is
consistent: the same sign and the same character in all three years (P5 negative
×3, P6 narrowing ×3, P4 null ×3). A zero-DOF mechanism cannot overfit — but it
can be wrong the same way every year, and this one is.

### §7.4 — the named successor, selected by measurement

pjm-145 named three re-open routes for the PJM measured-availability family.
This session took **route (3)** (the ERCOT-148/149 event-cap form) and has now
**refuted it on its own pre-registered predictions**. The measurement points at
**route (1): "restore ceiling composed with the structural-derate registry
(port the ercot137 fix)".**

The reason is exact. The envelope's defect is **shape**, not level: too much
derate at low load, too little at high load, with annual means already within
~7 %. Fixing a shape needs a mechanism that can move capacity in **both**
directions, and remove-only cannot. The only construction that reshapes is one
that also RESTORES — which is what pjm-145 refused, correctly, because 66–68 %
of its lift was structural-zero resurrection. **Route (1) is exactly the repair
that makes restoring safe**: cap each restore at the unit's own structural
ceiling from the derate registry, so a unit the finer measured record holds at
zero can never be revived. That is a real charter with a real prerequisite, and
it is where the next PJM availability session should start.

**A second, independent successor the same measurement exposes:** the model's
availability envelope carries **no planned/forced split**, which is why neither
basis works. A derivation that splits the CAMPD-detected windows into
maintenance-season planned versus event-driven forced would let the forced
components be compared like with like — and would be the input a reshaping
mechanism needs. Neither successor is opened here.
