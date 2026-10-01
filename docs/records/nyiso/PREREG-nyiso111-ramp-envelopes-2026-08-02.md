# PRE-REGISTRATION — nyiso-111: the pjm-140 `ramp_envelopes` transfer, single-delta `ramp_limits=True` on the nyiso-109 keeper

**Date:** 2026-08-02 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16
`[R-ALLYEARS]`, one bundle per arm) · **Committed and pushed BEFORE the arm
solved.** · Keeper under test: `2026-08-01-nyiso109-zonal-margin-anchor`
(bundle `results/calibration/nyiso109_zonalanchor_B`).

---

## §1 — what is being armed, and why it is on-queue

**Lever:** `ScenarioConfig.ramp_limits = True` — the plant-group hourly
ramp-envelope rows (`model/lp/rows.py::_build_ramp_rows`,
`data.fleet.build_ramp_groups`). **Matrix row `ramp_envelopes`, NYISO cell
`U`.** This is a **cross-ISO queue transfer**: PJM promoted it to keeper at
pjm-140 (2026-07-30) — the first keeper in any ISO to carry `ramp_limits=True`
— on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` grounds. It has never been
tested at NYISO. Rule 28(d) `[R-MECH-MATRIX]`: PJM's `K` says nothing about
NYISO, and **no PJM parameter is imported** — the envelope artifact is derived
from NYISO's own CAMPD conduct in this session.

**The defect it addresses, stated as a structural claim and not as a fit
claim.** With the flag off, the NYISO LP asserts that every thermal plant can
move from any output to any other output in one hour. That is false of the
real fleet, and NYISO's own CEMS record says so:
`scripts/data/derive_campd_ramp_envelopes.py --iso NYISO` (the frozen,
ISO-generic derive; rule 23 `[R-FROZEN-DERIVE]`) over NY CAMPD 2023-2025 writes
**77 rows / 48 well-observed plants**, with measured max 1-hour up-move
fractions of **CC median 0.49 × pmax (p90 0.82), ST 0.42 (p90 0.47), CT 0.92
(p90 0.94)**. The bound is the **MAX** observed move, never a quantile: it can
only remove moves the real fleet never made.

**Zero new degrees of freedom.** No new `ScenarioConfig` field, no code change,
no new parameter. One boolean flips; the MW it admits are a measurement.

## §2 — the pre-check, run BEFORE this pre-registration was written

pjm-140's all-ISO lesson is binding and is honoured here: *a MAX-based envelope
cannot be pre-checked with a p99-based excess statistic — pre-check a bound
against the bound.* The aggregate/class-level test is therefore reported as
**uninformative, not as support**: comparing each ramp bucket's class-aggregate
hourly move against the *sum* of its members' envelopes fires in **1 hour of
26,280** across all three years, exactly as that lesson predicts.

The bound-against-the-bound test — the same statistic pjm-140's promotion
rested on — does fire. On the keeper's own per-plant dispatch, with groups and
envelopes taken from the **live loader** (so the MW compared against are
exactly the rows the LP would impose, gross→net parasitic rebasis and pruning
included):

| 2023 | value |
|---|--:|
| enveloped groups / capacity | **62 groups, 21,809.0 MW** |
| group-transitions | 543,058 |
| transitions crossing the measured envelope | **5,226 (0.9623 %)** |
| infeasible ramping carried | **225,117.4 MWh** (up 119,178.1 / dn 105,939.3) |
| by family (crossings, infeasible MWh) | CC_REGULAR 2,778 / 162,063.4 · CC_CHP 1,274 / 31,204.2 · ST_GAS 398 / 21,361.2 · ST_CHP 615 / 7,731.8 · CT_PEAKER 161 / 2,756.8 |

For scale against the ISO that promoted it: PJM's superseded keeper crossed in
**0.393 / 0.463 / 0.319 %** of 1,699,246 transitions carrying **555,882 /
587,079 / 536,940 MWh/yr**. NYISO's crossing *rate* is **2.1–3.0× PJM's**, and
its infeasible ramping is ~0.45 % of NYISO thermal energy against ~0.07 % of
PJM's — i.e. relative to its own fleet NYISO is ramping infeasibly ~6× harder.

Probe: `scripts/probes/_nyiso111_ramp_envelope_precheck.py` →
`results/calibration/_nyiso111_ramp_precheck.json`.

**This is a one-sided test.** Crossings PROVE the rows would bind; their
absence would not prove inertness. It is evidence that the mechanism is live at
NYISO, and nothing more.

## §3 — falsifiable expectations, declared in advance

Stated so that a null result is a *recorded prediction*, not a retro-fit:

1. **Price effect: expected SMALL and of ambiguous sign.** pjm-140 solved
   near-inert on price (its chartered DJF morning price rise moved +$0.07 /
   +$0.05 / +$0.03 against a pre-registered ceiling of +$5.55/+$13.44) and
   PREREG secondary 1 was refuted outright. This arm is **not** predicted to
   close the compressed-amplitude defect
   (`docs/mechanism-testing-matrix.md` §5.5; nyiso-110), whose dominant
   component nyiso-110 measured to be missing reserve-price formation and
   adjudicated `G`. Any amplitude movement is a **reported by-product**, never
   the case for the arm.
2. **Infeasible ramping: expected to fall sharply** (pjm-140: −90.8 / −89.1 /
   −84.6 %). A residual is by design — the availability-edge widening is the
   row's only slack.
3. **Direction on the peak:** the mechanism removes traversal freedom into the
   peak hour, so if anything moves it should move the peak UP and the trough
   UP. Because C3a-2025 already sits at −9.64 % against a ±10 % band and
   C3a-2023 at +7.51 %, a large upward level move is a **risk to 2023**, and
   that risk is what kill P1 exists to adjudicate honestly.

## §4 — construction gates (K1–K6). All must pass or the arm is VOID.

- **K1 — single delta.** The arm's recorded `scenario_config` differs from the
  control's in exactly one key: `ramp_limits` `false → true`.
- **K2 — control integrity.** The same-HEAD zero-delta control reproduces the
  committed nyiso-109 keeper's class-hourly dispatch to **≤ 1.0 MW** max
  class-hour delta in all three years. (HEAD carries the pjm-146 RGGI landing,
  documented inert at defaults; K2 tests that claim on NYISO rather than
  assuming it.)
- **K3 — liveness.** The loader arms **≥ 40 groups and ≥ 15 GW** of enveloped
  capacity in every year. Below that the arm is INERT by construction and is
  registered as such.
- **K4 — artifact provenance.** `campd_ramp_envelopes_NYISO.csv` is the frozen
  derive's own output at this HEAD, unedited by hand; re-running the derive
  reproduces it.
- **K5 — span.** Both bundles cover **[2023, 2024, 2025]** in one bundle each
  (rule 16), and no out-of-training year is solved (rule 22 `[R-HOLDOUT]`; the
  holdout spend freeze is ACTIVE and is not touched).
- **K6 — effectiveness.** The arm's own infeasible-ramping MWh falls by
  **≥ 70 %** against control in every year. Below that, the rows are not doing
  what the mechanism claims and the arm is adjudicated INERT/mis-specified
  rather than promoted.

## §5 — kill gates (P1–P5). Any firing ⇒ NOT promotable; the run still registers (rule 15).

- **P1 — C3a band.** C3a leaves ±10 % in any year that passes on the keeper
  (all three do: +7.51 / −0.55 / −9.64 %).
- **P2 — C1.** All-class falls below 14/14 or free-class below 10/10.
- **P3 — C3c.** The model's >$300 hour count moves FURTHER from actual in any
  year (keeper 3/0/7 against actual 10/12/42). C3c is NYISO's one ledgered
  caveat; an arm that deepens it is not promotable whatever else it fixes.
- **P4 — C8 forced share.** Any material class crosses its budget, or a class
  currently grounded by a cited `D4_WINDOWS` entry loses that grounding.
- **P5 — feasibility.** Any load-shed slack or dump energy appears in any zone
  in any hour. A bound that pushes the LP against feasibility is a
  mis-specified constraint, not a physics fix.

## §6 — no-tuning clause (binding)

Following pjm-140 PREREG §5 verbatim in spirit: **the envelope may not be
tuned.** No quantile swap, no tightening, no scaling, no per-class override, no
re-derivation in response to this arm's result. There is no second version of
this lever — if the max-based envelope is the wrong bound, a binding ramp
representation needs a *different* mechanism with its own charter and its own
identification. Rule 23 `[R-FROZEN-DERIVE]`: the artifact re-derives only when
NY CAMPD updates.

## §7 — promotion rule, decided in advance

- **All K pass, no P fires, infeasible ramping down ≥ 70 %:** the arm is a
  candidate for promotion on the **standing structural-integrity standard**
  (rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`), the same ground pjm-140 was
  promoted on — *the model currently acts on a capability the fleet does not
  have.* Gate movement is reported either way and is not the case for the arm.
- **Any P fires:** registered as a rejected probe with the trade on the record;
  keeper unchanged.
- **K3 or K6 fails:** registered as INERT / mis-specified; keeper unchanged;
  matrix cell records the measurement so nobody re-runs it.

## §8 — reproduction

```
PYTHONPATH=.:src python scripts/data/derive_campd_ramp_envelopes.py --iso NYISO
PYTHONPATH=.:src python scripts/probes/_nyiso111_ramp_envelope_precheck.py --years 2023
# control (zero delta) and arm (single delta), per-year invocation chain:
PYTHONPATH=.:src python scripts/replay_keeper.py results/calibration/nyiso109_zonalanchor_B \
    --out-dir results/calibration/nyiso111_control_A --years <Y> [--reuse-solved <prev>]
PYTHONPATH=.:src python scripts/replay_keeper.py results/calibration/nyiso109_zonalanchor_B \
    --set ramp_limits=true \
    --out-dir results/calibration/nyiso111_rampenv_B --years <Y> [--reuse-solved <prev>]
```
