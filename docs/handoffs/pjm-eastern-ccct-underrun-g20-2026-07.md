# PJM G-20 — eastern CC/CT under-run: root-cause diagnosis

**Date:** 2026-07-11. **Branch:** `claude/pjm-eastern-ccct-underrun-j0wejg`.
**Scope:** diagnosis only — no keeper change, no fitted adder, no measured-input
edit (rules 1/11/13/14). Single-year **2024** diagnostic probes off the
committed pjm-97 keeper config (`results/calibration/pjm97_measured_interfaces`,
`meta.json` replay); 2024 is a **train** year so no holdout is touched (rule 22).
Probes are throwaway (rule 16) — never registered.

**Question handed to G-20 (pjm-97 attestation `residuals_note`):** the eastern
CC/CT UNDER-RUN — Dominion CC −81%, EMAAC CT −83%, SWMAAC CC −93% in the worst
cells — framed as "an offer/commitment problem plus a Dominion seam-inflow
through-corridor structural effect, not a transmission-limit problem."

## Headline

The eastern under-run is **not closable by any admissible seam / deliverability
/ commitment-posture lever** — every candidate that moves imports or exports
**wheels power through the eastern pockets instead of running their gas**,
because eastern gas is uncompetitive against corridor-delivered western coal
within the *loose, unmapped* internal eastern links, and **CC_REGULAR carries no
min-gen floor** (it dispatches purely economically). Three candidate mechanisms
are ruled out below with A/B evidence. The only admissible fixes left are (a)
measured hourly limits on the currently-unmapped eastern links (no published
series exists on those boundaries — the rule-14 blocker already noted in
`constants.PJM_INTERFACE_LINK_MAP`), or (b) an **out-of-market local reliability
commitment (must-run) floor** in the eastern MAAC pockets grounded in measured
CEMS committed operation. (b) is the recommended next build (§5).

## 1. The corridor, quantified (base pjm-97 config, 2024, P1)

Per-link net flow (TWh/yr; + = from→to):

| link | net TWh | note |
|---|---|---|
| AEP_Ohio→Dominion | **+35.0** | binds ~94% of hours at the measured 4,050 MW cap |
| West_APS→Dominion | +18.3 | static 3,000 MW seed (unmapped, no measured series) |
| PJM_external→Dominion (seam) | **+21.4** | southern seam inflow |
| Dominion→SWMAAC | **+25.6** | Dominion RE-EXPORTS north (unmapped SWMAAC↔DOM link) |
| Central_PA→EMAAC | +38.3 | the corridor into EMAAC ("Average Eastern" envelope) |
| SWMAAC→EMAAC | +11.0 | unmapped 5,000 MW seed |

Dominion imports **74.7 TWh** gross (AEP 35 + West_APS 18 + seam 21) and
re-exports **25.6 TWh** north — a through-corridor, exactly as the attestation
named it. Eastern gas (TWh): **Dominion CC 30.1 / CT 0.9**, **EMAAC CC 48.5 /
CT 1.9**, **SWMAAC CC 5.6 / CT 0.4** — all depressed while Central_PA CC (84.9)
and AEP_Ohio CC (91.1) over-run. Class *totals* are fine (C1 free 11/12); this
is a **spatial** residual, not a scored-criterion failure.

## 2. Deliverability (CETL) does NOT bind — ruled out

The `local_capacity_constraints` mechanism caps a pocket's **net** import at its
deliverability limit. PJM publishes CETL (`data/raw/capacity-deliverability/pjm/
pjm.csv`, `import_limit`). Measured against the modeled hourly net import:

| pocket | CETL (2024) | model net import: mean / p95 / max MW | binds? |
|---|---|---|---|
| EMAAC | 8,594 | 3,101 / 7,007 / 11,930 | only top ~3% of hours |
| SWMAAC | 7,947 | 3,337 / 4,910 / 6,188 | **never** (max < CETL) |
| Dominion | *(no import_limit row)* | 5,611 / 8,841 / 12,120 | n/a — no published CETL |

The eastern pockets import **within** their deliverability. A CETL constraint is
near-vacuous (SWMAAC never binds, EMAAC ~3% of hours) and Dominion has no CETL
row at all. **Deliverability is not the lever.** (The PJM CSV also lacks the
`peak_load` rows and a plant→area membership crosswalk the mechanism needs, so it
is not even wired for PJM — but the binding test above shows wiring it would not
help.)

## 3. Firm seam export — moves exports, does NOT run eastern gas — ruled out

The measured firm PTP/JOA schedule exports PJM→NYISO ~8.8 TWh/yr (2024 NYIS tie
−8.82 TWh); the model clears **~0** under the pjm-97 seam ladder (EMAAC external
−0.1 TWh). `firm_export_floor_by_year` (NYISO 1,400 MW in 2024) exists but the
ladder **displaces** it (`transmission.py:4305`, rule 19).

Two A/B probes tested restoring it:

| probe | EMAAC ext | Dominion ext | EMAAC CC | Dominion CC | SWMAAC CC |
|---|---|---|---|---|---|
| base (ladder) | −0.1 | +21.4 | 48.5 | 30.1 | 5.6 |
| ladder OFF (firm floors + spread import) | **−5.6** | 15.2 | 47.8 | 29.0 | 6.2 |
| firm-export kept under ladder | −0.1 | 21.2 | 48.7 | 30.7 | 5.8 |

- **Ladder-off** restores the NY export (−5.6 TWh) but **eastern gas is flat/down**
  — the forced export is served by wheeling *more* western power through the
  corridor (western seam export drops AEP −22.5→−14.9, ComEd −29.3→−25.1; the
  export is redistributed, not generated locally).
- **Keeping the firm floor under the ladder** (prototyped, then reverted) is a
  near **no-op**: the export envelope (`inject_pjm_seam_flow_limit(export)`)
  neutralizes the firm floor when the ladder reprices the bands, so EMAAC export
  stays ~0.

Either way, restoring the measured firm export **does not run eastern gas**. Ruled
out as the eastern-gas fix. (The under-export vs measured NY is a real *seam*
fidelity gap, but it is orthogonal to the eastern under-run.)

## 4. Reducing the Dominion seam over-import — also wheels through — ruled out

The model imports **+21.4 TWh** into Dominion vs a measured southern total of only
**+14.7 TWh** (Carolinas DUK+CPLE+CPLW +6.43, TVA +5.84, LGEE +2.40), of which
~9 TWh routes to Dominion. Ladder-off cuts Dominion's seam import to 15.2 TWh
(closer to measured) — yet **Dominion CC falls** (30.1→29.0): the freed Dominion
demand is met by pulling *more* from the AEP corridor, not by Dominion gas. Same
wheel-through. The southern ladder + p95 envelope are measured (rule 13) and are
**not** touched.

### Why every lever wheels through

`CC_REGULAR` carries **≈ 0 min-gen floor in every zone** (floor-array audit of the
2024 P1 solve: the per-plant "committed" tranche is a low-*price* offer, not a
forced *quantity*). So eastern CC runs only when economic, and within the loose
unmapped eastern links (`SWMAAC↔Dominion`, `West_APS→Dominion`, `SWMAAC→EMAAC` —
all static seeds, no measured series) corridor coal is always cheaper. Shifting
imports/exports just re-routes the cheap power; nothing forces the local unit on.

## 5. Recommended fix (next build — needs owner sign-off)

**An out-of-market local reliability commitment (must-run) floor on the eastern
MAAC CC/CT, grounded in measured CEMS committed operation** — the real market
structure (PJM commits local gas for LDA/voltage reliability, paid via bid-cost
recovery / RMR, *out of market* so the hub LMP is untouched). This is the
`coal_mustrun_per_plant` pattern extended to CC (a `cc_mustrun_per_plant` min-gen
from each eastern unit's same-year CEMS min-stable-when-online) — rule-13
admissible (measured, forward-regenerating), with the rule-12 triple native
(driver = measured commitment; window = the hours the unit historically ran;
forward story = CEMS-derived committed share).

**Guardrails it must clear before it is a keeper:**
- Rule 15 forced-energy budget (CC is ≥ 2% of load ⇒ gated): the floor must stay
  under the 30%/15% caps, or clear the rubric-v2.2 grounded-above-budget path
  (D-1 shape + D-4 window). A CEMS-committed floor binding overnight when the
  unit's own CF ≈ 0 is a rule-12 bug by definition.
- Must be **eastern-scoped by the measurement**, not a hardcoded zone tuple
  (rule 18): the CEMS floor self-targets units that actually committed, so
  western CCs that already run economically get a non-binding floor.
- D-2/D-4 attribution rows + ablation twin + DOF ledger (rules 20/21).
- Scored leave-one-year-out within 2023–2025 before promotion (rule 22).

The alternative — measured hourly limits on the unmapped eastern links — stays
**data-blocked**: `PJM_INTERFACE_LINK_MAP` already records that SWMAAC→EMAAC,
SWMAAC→Dominion and West_APS→Dominion "have no published series on their
boundary." Tuning their static seeds to the residual is forbidden (rule 11) and
is the transmission route the attestation explicitly rules out.

## 5b. Build (2026-07-11 follow-up session) — `cc_mustrun_per_plant`

The §5 recommendation was built as ``ScenarioConfig.cc_mustrun_per_plant``
(default **off**; rule 20 on-registry):

- **Level** = the plant's EXISTING committed tranche (CEMS minimum stable load,
  `thermal_tranches_PJM.csv committed_pct`) — the tranche becomes a forced
  QUANTITY, its offer price untouched (rule 19: no second floor stacked).
- **Window** = the plant's top ``online_frac`` fraction of hours ranked by
  system load — the measured CEMS synchronization fraction, now emitted for the
  gas committed groups (CC_REGULAR / CT_PEAKER) by
  `scripts/derive_thermal_tranches.py` (same estimator the coal step-3a
  forcing already publishes; the 139 gas `online_frac` cells were patched into
  the committed artifact with every existing column frozen, rule 21 — a full
  regen today drifts the CAMPD-derived columns, so only the new column landed).
- **Attribution**: new `MECH_CC_MUSTRUN_PER_PLANT` (id 15) — merchant
  reliability commitment, D-2 gated (NOT exempt), auto-ablated in zero-forcing
  twins via `MECH_ABLATION_FIELDS`; D-4 declared windows (CC_REGULAR all-hours
  — a committed CC is synchronized around the clock inside its window; the
  load-ranked placement relaxes the deepest troughs — CT_PEAKER h7-22, so
  overnight CT binding is caught); D-5 parity row (mode-independent, applied
  in the shared fleet builder).
- Rule 18: self-targeting — only plants with a measured `online_frac` +
  committed tranche carry the floor; western CCs that run economically see a
  non-binding bound. Parameter-based (share + fraction), UNLIKE the
  quarantined `ct_mustrun_per_plant` probe (which pins observed net-gen MWh).
- Zero fitted scalars in the delta ⇒ the rule-22 LOO clause (cross-validating
  TUNED changes) is vacuous, as it was for the pjm-97 promotion itself.

Run lineage: single-year 2024 throwaway probe (never registered, rule 16) to
verify the floor runs eastern gas + budget/D-4, then the full 2023–2025 bundle
`pjm98_cc_mustrun` + its `-ablation` twin (`scripts/run_pjm98_cc_mustrun.py`).
Keeper swap remains the owner's decision (§5 over-forcing risk sign-off).

## 6. What was NOT changed

Keeper unchanged (`2026-07-10-pjm-97-measured-interfaces`; keeper swaps are the
owner's). No measured input edited, no fitted adder, no transmission limit tuned.
A `pjm_firm_export_with_ladder` prototype (restore the firm export floor under the
ladder) was built and A/B-probed (§3), found to be a no-op under the ladder, and
**reverted** (rule 26 — an ineffective knob is not left in-tree).
