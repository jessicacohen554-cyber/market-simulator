# ASSESSMENT miso-233 — the hourly neighbour anchor on MISO's SECOND seam (SPP) is PROMOTED. **DETERMINATION CALIBRATED**, C3c the single ledgered caveat.

**KEEPER → `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`), promoted from
`2026-09-06-miso-232-hourly-seam` under the miso-227 promotion rule. Rule 22: 2023–2025.
DOF ledger **unchanged at 41/2**.
Pre-registration: `PRECOMMIT-miso233-spp-hourly-seam-2026-09-07.md` (pushed at `79f73030`
before the screen); screen result: `ADDENDUM-miso233-screen-2026-09-07.md` (pushed at
`e852c85c` when the span launched, before any span year's bundle existed).

---

## 0. Provenance, stated first — and it is different from the predecessor's

**The screen PASSED.** All four pre-registered structural gates cleared on the 2023 screen
before the span was spent, and the promotion rests on that. This is stated first because
the *predecessor* keeper's provenance is the opposite and travels forward unsoftened: the
miso-231 screen was **KILLED on its pre-registered G-1 bar by 0.0183**, the bar was not
moved, and miso-232's span existed only by **OWNER RE-CHARTER**. Nothing here re-reads that
as a gate pass.

## 1. Phase 0 — zero LP — FALSIFIED the lever queue's own hypothesis

The MISO lever queue's item 1 asked whether the deep PJM bands (`k = 6-8`) under-clear in
MISO's cheap hours and cost the repaired decile slope its magnitude. Reconstructing every
seam from the keeper's **own committed sidecars** (miso-231's readout-B instrument extended
to all seams; harness `corr(reconstruction, committed imports)` = **+0.924 / +0.946 /
+0.971**) says they do not:

| seam | ladder it clears against | reconstructed slope d1−d10 | MEASURED seam slope |
|---|---|---:|---:|
| **PJM** | HOURLY neighbour (repaired, miso-231/232) | **+2,377 / +2,611 / +2,704** | +1,319 / +1,052 / +815 |
| **SPP** | INCUMBENT fixed MISO-hub Q-Q ladder | **−414 / −481 / −553** | +317 / +466 / −50 |
| **South** | INCUMBENT fixed MISO-hub Q-Q ladder | **−919 / −1,135 / −827** | +72 / +60 / +646 |

PJM is **already steeper than measured**; its cheapest decile loses only **194 / 194 /
271 MW** to the deliverability envelope, and the exact attribution identity
(`width = cleared + lost_to_envelope + lost_to_merit + lost_to_both`) puts the deep bands'
contribution at **+1,229 / +597 / +316 MW** — present, not missing. What cancels the repair
is the two seams the hourly form never covered, both carrying the exact defect miso-226
named: a FIXED ladder cleared against the model's own price leaves merit when MISO's price
falls, which is when MISO imports.

Probes: `_miso233_seam_slope_anatomy_phase0.py`, `_miso233_allseam_slope_attribution_phase0.py`,
`_miso233_spp_hourly_phase0.py`; JSON beside each.

## 2. The single delta, and why it was possible only now

`miso_seam_neighbour_hourly_spp=true` on the miso-232 recipe, via `replay_keeper --set`.
SPP band `k` is offered at `pi_k(t) = spp_hub(t) + delta_k` against the measured SPP **NORTH**
hub DA. A **SUB-GATE** of `miso_seam_neighbour_hourly_ladder`, refused without its parent and
applied only when the parent overlay took (rule 19 `[R-ONE-MECH]`). `delta_k` comes from the
**byte-identical incumbent Q-Q estimator** on the MISO-minus-SPP spread and is **pinned to
that derive by test**; zero fitted parameters.

Queue item 3 recorded the blocker — SPP and South ride the incumbent anchor "for want of a
measured hourly price series". **Lane SPP-14 landed one on 2026-09-06**
(`actual_lmp_hourly_zonal_SPP.parquet`, 8,754 of 8,760 hours in each of 2023–2025, from SPP's
own portal), so rule 14 `[R-ACCURATE]` applies directly: the incumbent SPP anchor is an
**estimate** standing in for the neighbour's price, and the measured price now exists. The
derive ran because its **source data landed**, never because a residual moved (rule 23).

**G-DRIFT** `451e6109..b7ff89ca`: 36 files, +27,692 / −26,341 — **every hunk classified
INERT** (PRECOMMIT §5), the bulk being main's registration of SPP as the seventh ISO.
Corroborated by measurement: MISO's `surface_stamp` reads `moved: {}`. The keeper's committed
bundle was the control (form 4). **No control solve was spent.**

## 3. The screen — one year, gates that were not the residual

Screen year **2023**, named on the mechanism's own measured footprint (5,279 disagreeing
band-hours, 54.5 % of hours, 2.0476 TWh moved — the maximum on every sub-measure), **not**
on the residual (2024's gap is larger).

| gate | bar (fixed ex ante) | measured | verdict |
|---|---|---|---|
| G-1 confinement | slack ≤ 0.0000 TWh, dump 0, must-take within 0.05 TWh | slack 0.0000, dump 0.0000, all four classes 0.000 | **PASS** |
| G-2 footprint scale | \|Δ gross imports\| ≤ 1.5 TWh | **−0.597 TWh** | **PASS** |
| G-3 direction | `corr(imports, own price)` may not rise > +0.05 | **−0.1042** | **PASS** |
| G-4 no collateral flip | zero PASS→FAIL, real scorer in memory | **0 flips** | **PASS** |

The decile slope was placed under `reported_not_gated` in the PRECOMMIT precisely so it could
not select the arm. The screen bundle is **DELETED** (rule 29(c)); every number it produced is
in the addendum and `_miso233_screen_gates.json`.

## 4. The determination

| criterion | tier | verdict |
|---|---|---|
| C1 fuel mix | LOAD | **PASS — 16/16 all-class, 12/12 free-class** |
| C2 system volume | LOAD | PASS |
| C3a mean LMP | LOAD | PASS |
| C3b price duration/shape | LOAD | PASS |
| C3c price tail / scarcity | SUPP | **CAVEAT (ledgered, non-downgrading — rubric v3.3)** — 3/7/11 h vs 30/37/88, unchanged |
| C4 dispatch correlation | SUPP | PASS |
| C6 governance | PROT | PASS |
| C8 forced-energy share | PROT | **PASS — CT_PEAKER grounded above budget, all three years** |

2025 C1 and C2 are **SKIPPED** on the preliminary EIA-923 vintage and are not read as evidence.

## 5. What the mechanism did across the span — the open item miso-232 named MOVES

All from the committed `hourly/` sidecars. The model side reproduces miso-232's published
values exactly (keeper slope 138.7 / 111.2 / 680.9 against its published +139 / +111 / +681),
so the instrument is the same one.

| year | statistic | keeper | **arm** | MEASURED |
|---|---|---:|---:|---:|
| 2023 | decile slope d1−d10, measured hub price | +138.7 | **+402.4** | +1,218.0 (summed seams) / +1,318.6 (PJM seam) |
| | corr(imports, own model price) | +0.1754 | **+0.0712** | — |
| | corr(imports, measured price) | −0.0823 | **−0.1095** | −0.136 |
| | cheap-hour (<$20, n=1,230) imports | 4,892.6 MW | **5,024.2** (+132) | — |
| | gross imports | 44.763 TWh | **44.166** (−0.60) | — |
| 2024 | decile slope | +111.2 | **+631.9** | +914.1 / +1,052.2 |
| | corr, own price | +0.1644 | **+0.0818** | — |
| | corr, measured price | −0.0636 | **−0.1145** | −0.039 |
| | cheap-hour (n=2,111) imports | 3,321.6 MW | **3,497.0** (+175) | — |
| | gross imports | 29.751 TWh | **29.344** (−0.41) | — |
| 2025 | decile slope | +680.9 | **+1,026.8** | +1,189.0 / +815.3 |
| | corr, own price | +0.0368 | **−0.0386** | — |
| | corr, measured price | −0.0852 | **−0.1128** | −0.059 |
| | cheap-hour (n=395) imports | 2,606.3 MW | **2,762.5** (+156) | — |
| | gross imports | 21.504 TWh | **20.616** (−0.89) | — |

- **The slope's magnitude moves in every year**, from 11 / 12 / 57 % of the measured
  summed-seam value to **33 / 69 / 86 %**. That is the open item miso-232 left as its
  non-claim 1, and it moves because the *un-repaired* seam was the object, not the repaired one.
- **`corr(imports, own price)` falls in every year** and crosses zero in 2025 — the direction
  the mechanism's arithmetic asserts.
- **Redistribution, not addition**, again: gross imports fall 0.60 / 0.41 / 0.89 TWh while
  imports in the hours the measured seam flows most rise 132 / 175 / 156 MW.
- **Confinement holds:** slack 0 / 0.0196 / 0 TWh (the 2024 value is the keeper's
  pre-existing one) and dump 0.0000 in every year.

**A comparator discrepancy, disclosed rather than papered over.** miso-232 published its
measured column as +1,303 / +1,384 / +948 MW. On the committed series this session could
**not reproduce those three numbers exactly** — the same instrument gives +1,318.6 / +1,052.2
/ +815.3 for the measured PJM seam and +1,218.0 / +914.1 / +1,189.0 for the summed measured
seams. The model side matches miso-232 to 0.1 MW, so the difference is in which measured
flow series is called "measured", not in the scoring. Both of this session's bases are quoted
above and the predecessor's column is **not** restated as if it had been reproduced.

## 6. Collateral — G-4 on the full span

`scripts/screen_collateral_gate.py` against the keeper's committed verdict: **ZERO PASS→FAIL
flips.** Of the 16 scored C1 cells **11 move toward actual and 5 away**:

| C1 cell (TWh, model − actual) | keeper | arm | move |
|---|---:|---:|---|
| CT_PEAKER 2023 / 2024 | −3.29 / −2.28 | **−3.05 / −1.93** | toward |
| COAL_PRB 2023 / 2024 | −2.00 / −3.66 | −1.77 / −3.44 | toward |
| COAL_BIT 2023 / 2024 | −3.06 / −3.68 | −2.95 / −3.56 | toward |
| CC_REGULAR 2024 | +4.09 | +3.76 | toward |
| CC_CHP 2023 · ST_GAS 2024 · COAL_LIGNITE 2024 · ST_CHP 2023 | | | toward |
| **CC_REGULAR 2023** | −6.31 | **−6.45** | **away** |
| **ST_GAS 2023** | +0.29 | +0.41 | away |
| CC_CHP 2024 · ST_CHP 2024 · COAL_LIGNITE 2023 | | | away (≤0.013) |

All four C2 family rows move toward actual (2023 gas −14.07 → −13.80, coal −5.59 → −5.25;
2024 gas −6.85 → −6.76, coal −8.00 → −7.66). The gated C3a moves **away** in 2023
(+2.05 → +2.12 %) and 2024 (+1.05 → +1.14 %) and toward in 2025 (−2.52 → −2.36 %), all far
inside band. **CT_PEAKER forced share** is 41.2 / 26.4 / 23.6 %, still above the 15 % cap, so
C8 passes only through rule 18's grounded route (D-4 off-window PASS; class D-1 profile r
0.976 / 0.983 / 0.982, cv ratio 1.756 / 1.553 / 1.633), as it did for the keeper.

## 7. Pre-committed NON-CLAIMS, carried onto the determination basis

1. **This does not close the slope-magnitude gap — it removes ONE of the two cancelling
   seams. SOUTH IS UNTOUCHED and is the LARGER remaining contributor** (−919 / −1,135 /
   −827 MW). That is a **data boundary, not a decision**: SOCO and TVA are not organised
   markets and publish no hub or nodal price.
2. **The admissibility statistic does NOT support this arm.** `corr(measured SPP seam flow,
   MISO DA − SPP hub DA)` = +0.041 / −0.020 / +0.050, against `corr(flow, MISO DA)` of
   −0.216 / −0.377 / +0.082 and the PJM spread's +0.240 / +0.265 / +0.194. The spread is
   uninformative about this seam's hourly flow; it **removes** a wrong-signed response rather
   than supplying a right-signed one. The case is rule 14 plus rule 1's instruction that a
   structurally-correct mechanism is not judged by the residual.
3. **`corr(imports, measured price)` OVERSHOOTS in 2024 and 2025** (−0.1145 / −0.1128 against
   a measured −0.039 / −0.059), having improved in 2023 (−0.1095 against −0.136).
4. **The CC_REGULAR-2023 give-back gets slightly worse** (−6.313 → −6.445 TWh) — named in the
   screen addendum **before** the span, not discovered after it.
5. **The `SPPNORTH_HUB` anchor is a rule-14 reconciliation of a collapsed link**, named on
   topology before any ladder was derived. `SPPSOUTH_HUB` was computed as a sensitivity and
   selected nothing.
6. **C3c is UNTOUCHED** and stays the designated frontier (2026-07-20).
7. **The predecessor's owner-recharter provenance travels forward.**

## 8. Rule 15 — keeper-only retention

MISO carries exactly one registered run. `2026-09-06-miso-232-hourly-seam` was pruned via
`scripts/prune_iso_runs.py --iso MISO --force-uncite` (sidecar, payload and bundle together);
narrative citations to it dangle by design and git history is the record. The keeper's
`hourly/` sidecars are committed.

## 9. Governance

Rule 1 `[R-STRUCT]`: structure first — the arm was proposed on rule 14 and the owner-ruled
seam form, its gates were structural and STOP-only, and the target residual was never gated.
Rule 12: years sequential, solved in-session (~55 min, ~12 GB + swap), never on CI. Rule 13
`[R-MEASURED]`: the SPP hub DA is a published market price with the same forward analogue the
PJM border price carries. Rule 14 `[R-ACCURATE]`: measured input replaces an estimate; the
collapsed-link misalignment is declared. Rule 15: registered and pruned in this session.
Rule 16: one invocation, one bundle, all three years. Rule 19: a sub-gate refused without its
parent, displacing the incumbent SPP ladder and never stacked. Rule 21: 41/2. Rule 22:
2023–2025; MISO holds no `complete` marker and no holdout year was touched. Rule 23: the SPP
derive ran on new source data, never on a residual; the PJM ladder was not re-derived.
Rule 24: one registered field, in `run_config.json` and in the cache key. Rule 25: MISO only.
Rule 27: every pushed blob verified against local. Rule 28(b)/(c): the field is registered in
its family's matrix row, the MISO cell and keeper/gates stamps and the §5.4 header are
re-stamped, `check_mechanism_matrix.py --base origin/main` clean. Rule 29: phase 0, a screen
that passed, G-DRIFT, keeper as control, screen bundle deleted before merge.

**Open after this promotion, named and not started:** the **South** seam (the larger
remaining cancelling seam, blocked on the absence of any published SOCO/TVA price); the
2024/2025 correlation overshoot; the CC_REGULAR-2023 give-back; and C3c, which needs its own
charter.
