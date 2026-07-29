# PRE-REGISTRATION — pjm-137 `measured_ct_heat_rates` for PJM (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document does
not contain cannot be quoted as a pass. Format follows
`PREREG-pjm136-zonal-loss-surface-2026-07-28.md`, **mirrored, not copied**.

Chartered by `FINDING-pjm137-dominion-congestion-is-subzonal-2026-07-29.md`
(this session's M1/M2/M3/M4 measurements, all no-LP), which **closed** the
question `FINDING-pjm136` §5 handed forward. pjm-136 asked a successor to *"make
an internal PJM constraint actually price, or prove it can't."* M2/M4 prove it
can't: only **3.1–6.3 %** of PJM's day-ahead congestion rent is inter-zonal,
`AEP-DOM` is **0.04–0.24 %** of it, the hot-hour constraints are Loudoun-County
facilities with **both ends inside `PJM_Dominion`**, and there is **more price
separation inside the Dominion zone than across the DOM–AEP boundary**
(1.30 / 1.42 / 1.16×).

With the congestion route closed, `measured_ct_heat_rates` is the **only named
lever remaining** in the PJM lever queue for the CT leg (matrix §5.3 item 2,
cell **U**). It is chartered here **as a rule-14 `[R-ACCURATE]` accuracy
correction, not as a fix for the Dominion residual** — and §4 pre-registers it
as **INERT on that residual**, with the arithmetic, before any solve.

**Promotion is NOT pre-granted** and is not requested by this session. It
remains a separate owner act, and (rule 22 `[R-HOLDOUT]`) a structural mechanism
change is scored leave-one-year-out within 2023–2025 before any promotion.

---

## §1 — the delta, exactly

`ScenarioConfig.measured_ct_heat_rates: False → True` for PJM. **One existing
field, no new mechanism, no new code path.** The flag is already built and
already a keeper elsewhere (NYISO, nyiso-89); what PJM lacks is the *artifact*.
This session generates it with the existing frozen derive, unmodified:

```
PYTHONPATH=. .venv/bin/python scripts/data/derive_campd_ct_heat_rates.py --iso PJM
  → data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv
```

Per plant, over pooled 2023–2025 CAMPD:

```
cap      = p95 of the unit's gross load
loaded   = hours with grossLoad >= 0.80 x cap   (>= 50 such hours)
hr_gross = sum(heatInput) / sum(grossLoad) over `loaded`
hr_net   = hr_gross / parasitic_factor(plant)
plant    = generation-weighted mean of its units' hr_net
```

and the loader (`fleet.campd_bins.measured_ct_heat_rates`) applies only
`flag == "ok"` rows — a plant outside the physical simple-cycle band
(6.0–25.0 MMBtu/MWh net) is written with its measured value and a flag and is
**excluded**, keeping its eGRID rate. That band is a meter-integrity guard, not
a tuning knob, and this session does not touch it.

**What it replaces and why that is more accurate (rule 14 `[R-ACCURATE]`).** The
non-ERCOT fleet loader otherwise gives every combustion turbine its eGRID
**plant-average ANNUAL** heat rate. For a peaker that number blends startup
fuel, part-load hours and shutdown tails into the figure that sets its offer;
and at a mixed steam/CT facility eGRID publishes one rate for the whole plant,
so the turbines inherit the boilers' number. The measured loaded rate is the
rate at which the machine actually converts fuel to power at load — a physical
characteristic, rule-13 `[R-MEASURED]` admissible as an INPUT (it regenerates
for a forward year from the same pipeline and responds to a retrofit or a new
unit's design rate), and nothing in it is fitted to any residual.

**Scope boundaries, fixed here:**
- **Zero DOF.** No free parameter is added; `n_residual` is unchanged. The
  derive is frozen (rule 23 `[R-FROZEN-DERIVE]`) and re-derives only on a CAMPD
  vintage change.
- Rule 19 `[R-ONE-MECH]` — this owns the **CT_PEAKER loaded heat rate** only.
  `CT_CHP` is deliberately outside the derive's scope (a cogen turbine's metered
  heat input serves process steam), and nothing else in the offer path moves.
- Rule 25 `[R-ISO-SCOPE]` — the artifact is derived from **PJM's own plants**.
  NYISO's keeper verdict is not transferred; PJM's cell is decided by PJM's A/B.
- The **congestion deficit is not addressed by this delta and is not claimed
  to be.** §4.

## §2 — PRIMARY (P1): construction fidelity, pre-computed

**P1 — the applied rates must equal the derive's measured rates.** For every
plant the artifact flags `ok`, the fleet's `heat_rate` in arm B must equal the
artifact value, and in arm A must equal the eGRID value. Verified by a
**pre-solve fleet-build check** (build the PJM fleet twice, flag off and on, and
diff the CT_PEAKER heat rates) — because `measured_ct_heat_rates` has no
explicit `solve_and_persist` kwarg and rides `replay_keeper.py`'s generic
`prb_overrides` channel, so that the flag actually reaches the fleet build is a
gate, not an assumption (the ERCOT-65 defect class).

**P2 — the re-pricing must be material and two-signed.** Pre-computed from the
committed benchmark's own 76-plant PJM `CT_PEAKER` roster against eGRID 2023
`PLHTRT`, before any solve: **39 of 72** plants with both rates move by more than
**0.5 MMBtu/MWh**, in **both directions** (largest: O H Hutchings −29.4,
Forked River −13.9, Woodsdale −7.4; Galion +5.2, Bowling Green +4.6, Darby
+3.4). Energy-weighted the ISO moves **−0.254 MMBtu/MWh**, i.e. about
**−$0.89/MWh** on the CT offer at $3.50/MMBtu. A delta that changes almost
nothing has not fired; a delta that moves every plant one way would be a
multiplier in disguise and is not what the measurement says.

Per-zone energy-weighted Δ (MMBtu/MWh), pre-computed:

| zone | plants | Δ | zone | plants | Δ |
|---|---|---|---|---|---|
| PJM_SWMAAC | 5 | **−1.331** | PJM_EMAAC | 13 | −0.183 |
| PJM_AEP_Ohio | 17 | −0.327 | **PJM_Dominion** | **9** | **−0.168** |
| PJM_ATSI | 7 | −0.296 | PJM_West_APS | 6 | −0.149 |
| PJM_Central_PA | 3 | −0.046 | PJM_ComEd | 12 | **+0.212** |

**P3 — the off-state must be byte-identical.** Arm A must reproduce the
committed `pjm136_lossurf_B` class hourlies exactly (K5 below).

## §3 — pre-registered kills

**K1 — the C3c standing kill, named first because it is the thinnest margin in
the keeper.** C3c passes by **1 hour** (2024: 10 h vs RT 18 h, 0.56× against a
0.5× floor) and **2.5 hours** (2025: 32 h vs 59 h, 0.54×). This delta cuts CT
offers ISO-wide by ~$0.89/MWh energy-weighted, and CTs are the units that set
the top of the stack — so a *reduction* in tail hours is the mechanically
expected direction and a flip back to FAIL is live. **Reported explicitly and in
the headline either way.** Pre-registered disposition (rule 1 `[R-STRUCT]`): a
C3c flip does **NOT** retire the mechanism — a measured input that is more
accurate than the estimate it replaces stays in even when the fit worsens, and
the response is to find the real root cause, never to revert (rule 14, explicit
on this). It **does** block any promotion recommendation from this session.

**K2 — C1 fuel-mix must be reported per class, not just pass/fail.** The keeper
is 16/16 with free 12/12. CT_PEAKER volume moves by construction here; any class
crossing its band is recorded with its margin.

**K3 — no fabricated cheapness.** No plant in the applied map may fall outside
the derive's own 6.0–25.0 MMBtu/MWh band (the loader already enforces this via
`flag`), and the count of excluded plants is reported. If more than **10 %** of
the roster's energy is excluded by the band, the artifact is too noisy to apply
and the delta is retired.

**K4 — no load shedding.** Slack and dump must be **exactly zero** in both arms,
all three years.

**K5 — arm-A identity.** Arm A must reproduce the committed `pjm136_lossurf_B`
class hourlies to **0.000000000 MW** on all classes, every hour, all three
years. A non-identical control invalidates the A/B.

**K6 — solve cost is recorded, not gated.** This delta changes coefficient
*values* only — no new rows, no new columns — so it should be free. Whatever it
costs is reported.

## §4 — the expected magnitude, pre-computed, and INERT pre-registered

**This delta is pre-registered as unable to close the Dominion CT leg.** The
nine Dominion CT plants are **all pure-CT facilities** — none is a mixed
steam/CT site, which is the pathology this mechanism exists to fix — so their
eGRID plant rates are already within 0.04–0.72 MMBtu/MWh of their measured
loaded rates, except Gravel Neck which measures **higher** (+2.40). Energy
weighted, Dominion moves **−0.168 MMBtu/MWh ≈ −$0.59/MWh**.

Against that, `FINDING-pjm137` §3 measures the model's Dominion price deficit in
the hours the real CT fleet runs at **−$10.28 / −$16.23 / −$38.21 /MWh**, of
which **52–63 %** is congestion §2/§4 of that finding prove is intra-zonal and
unreachable. **A $0.59/MWh offer cut does not close a $10–38/MWh price gap.**

**A result in which Dominion CT_PEAKER barely moves is the expected outcome and
is published as a PASS of the PRIMARY**, exactly as pjm-134's, pjm-135's and
pjm-136's INERT verdicts were. If P1/P2 hold and Dominion does not move, the
determination is **ACCURACY-CORRECT, INERT-ON-THE-DOMINION-LEG**, and that
adjudicates matrix cell `measured_ct_heat_rates` × PJM on PJM's own evidence
(rule 28 duty b) rather than leaving it open for a fourth session to re-propose.

**No-feedback ceiling (binding on this session and any successor):** there is
nothing in this mechanism to re-parameterise, and nothing may be added. **No
multiplier, blend, scale factor, floor, cap, per-plant override or band widening
may be applied to the derived heat rates**, in this session or a successor,
whatever the result. The physical band (6.0–25.0) is a meter-integrity guard and
is not a knob; the loaded-window definition (0.80 × p95, ≥ 50 h) is the shipped
derive's and is not re-tuned here. The artifact re-derives **only** when CAMPD
publishes new or revised vintages (rule 23 `[R-FROZEN-DERIVE]`), never because a
residual moved.

## §5 — arms, protocol, and what is reported either way

| | arm A (control) | arm B (delta) |
|---|---|---|
| bundle | `results/calibration/pjm137_control_A` | `results/calibration/pjm137_ctheatrate_B` |
| recipe | `pjm136_lossurf_B` verbatim (`replay_keeper.py`) | + `--set measured_ct_heat_rates=true` |
| years | 2023 + 2024 + 2025, one invocation (rule 16) | same |
| order | sequential, years sequential within each (rule 12) | |

`legitimacy_diagnostics.json` is generated with `--json-out` for **both** arms
before scoring (without it C7/C8 have no committed contract). Both arms are
registered on the backcast dashboard (rule 15) and the `measured_ct_heat_rates`
matrix cell is updated in this session (rule 28 duty b), **including if the
verdict is INERT or REJECTED**. D1/D2 are expected to FAIL in both arms —
pre-existing and long-standing, not this delta.
