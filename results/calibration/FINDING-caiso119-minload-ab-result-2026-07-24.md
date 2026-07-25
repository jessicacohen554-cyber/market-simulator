# FINDING — caiso-119 A/B RESULT: the measured min-load correction (`caiso_ra_min_load_frac` 0.26 → 0.570) is STRUCTURALLY CORRECT but DISPATCH-NEAR-INERT — belly gas moves −28 / +59 / +52 MW across 2023–25, closing 8–10 % of the gap at best, with no KILL gate tripped. The floor records explain why on the bytes: the RA must-offer bridge owns only **23–24 k of ~1.33 M floored cells (1.8 %)** and ~0.4 GW annual-average, and its level is capped, so raising the fraction re-floors almost nothing. The remaining belly gap is only ~250–600 MW grid-delivered — too small to drive C5a/C4. Attribution instead lands on a much larger, cleanly-diagnosed defect: **CT_PEAKER is PRICED OUT** (present, 3.5 GW demonstrated capability, 0.44 TWh vs 4.33 TWh actual). Keeper UNCHANGED (2026-07-24)

Companion to `FINDING-caiso119-gas-basis-adjudication-2026-07-24.md` (the basis
refutation that re-scoped this lane). Gates were **pre-registered before either
arm finished**: `results/calibration/caiso119_ab_pregistered_gates.md`.

**Arms** (same HEAD `f28340b`, same box, three years):

- `caiso119_base_A` — `replay_keeper` of the `2026-07-23-caiso-netrev-margin-keeper`
  recipe, no delta. *(A container restart killed its 2025 leg; that leg was
  re-solved alone as `caiso119_base_A_y2025` on the same HEAD/recipe and merged.
  Its 2023/2024 legs are the original run's.)*
- `caiso119_minload_B` — the SAME recipe plus ONE delta,
  `caiso_ra_min_load_frac` 0.26 → **0.570** (measured; see §4 of the companion).

---

## 1. Result — near-inert, no gate tripped

Belly = hod 10–15; reference is CEMS gross (an UPPER bound on grid-delivered).

| year | window | CEMS | BASE | MINLOAD | gap closed |
|---|---|---|---|---|---|
| 2023 | belly | 5,087 | 4,178 | 4,150 | **−3 %** |
| | evening | 9,749 | 10,243 | 10,238 | 1 % |
| | duck b/e | 0.52 | 0.41 | 0.41 | — |
| 2024 | belly | 4,435 | 3,688 | 3,747 | **8 %** |
| | evening | 8,444 | 8,948 | 8,915 | 7 % |
| | duck b/e | 0.53 | 0.41 | 0.42 | — |
| 2025 | belly | 3,535 | 3,023 | 3,075 | **10 %** |
| | evening | 6,627 | 7,230 | 7,201 | 5 % |
| | duck b/e | 0.53 | 0.42 | 0.43 | — |

**Pre-registered gate tally: 11 pass / 4 fail.**

- **P1 (belly gap closed ≥ 40 %) FAILS all three years** — the delta's purpose.
- P2 (duck ratio rises) passes 2024 and 2025, fails 2023.
- **K1 / K2 / K4 all PASS every year** — no overshoot, no volume breach, evening
  not made worse. The delta is safe; it simply does very little.

Note the direction is *right* in 2024/2025 (belly +59 / +52 MW, evening −33 /
−29 MW — gas moving from evening to belly, exactly the intended rotation) and
marginally wrong in 2023. The magnitude is ~10 % of what would be needed.

## 2. WHY — the floor records settle it (this is the load-bearing part)

The probe `_caiso119_floor_scope_diag.py` reads each arm's own committed
`floors/<year>_P1.npz` — the exact per-unit, per-hour `min_gen` handed to P1,
with a mechanism id per cell. Two hypotheses were pre-stated: **H1 narrow scope**
(the bridge floors too few unit-hours for the level to matter) vs **H2 slack
floor** (it floors many, but the LP was already above them).

Floored MW by mechanism, annual-average / belly-average:

| mechanism | 2024 BASE ann | 2024 MIN ann | 2024 BASE belly | 2024 MIN belly | cells |
|---|---|---|---|---|---|
| `firm_import` (12) | 3,304 | 3,304 | 1,220 | 1,220 | 15,988 |
| `nuclear_mustrun` (1) | 2,077 | 2,077 | 2,077 | 2,077 | 17,520 |
| `chp_steam` (2) | 924 | 924 | 924 | 924 | 1,266,096 |
| **`ra_mustoffer_bridge` (7)** | **387** | **424** | **951** | **1,046** | **24,463** |

**H1 is confirmed, with a twist.** The RA must-offer bridge — the *only*
mechanism `caiso_ra_min_load_frac` governs — owns **24,463 of 1,324,067 floored
cells (1.8 %)** and ~0.4 GW annual-average. The 1.27 M-cell bulk is
`chp_steam`, a structural, D-2-exempt steam-host floor that the delta cannot
touch. So a +119 % change in the fraction produced a **+0.7 % change in
average floored MW per cell (44.2 → 44.5)** and a −0.2 % change in floored-cell
count.

The twist: the bridge's floor level is **capped**, so raising `min_load_frac`
pushes units into the cap rather than lifting the floor. Belly floored MW moved
only 951 → 1,046 (+95 MW) in 2024 and 1,027 → 1,110 (+83 MW) in 2025 — which is
almost exactly the belly gas movement observed (+59 / +52 MW). The mechanism is
fully accounted for; nothing is unexplained.

**Correction to an interim read made mid-session:** the "99.2 % of floored cells
bind" statistic is dominated by `chp_steam` and `nuclear_mustrun` (both
structural and exempt) and says nothing about the RA bridge. It should not be
quoted as evidence about commitment.

**C8 forced-energy is comfortable, contrary to the caiso-118b guardrail worry.**
Forced gas = `chp_steam` 0.92 GW (exempt) + `ra_mustoffer` 0.42 GW against
~6.1 GW of model gas → merchant forced share ≈ **7 %**, far inside the 30 % cap.
There was never a C8 risk here, because there was never 10 GW of forcing to add.

## 3. Disposition (per the pre-registered doc, honoured verbatim)

Outcome = "PRIMARY partially met, no KILL", whose pre-registered disposition is:
**register as a PROBE, keep the measured value, open the root-cause lane.**

- **The measured 0.570 STAYS.** Rule 14: the accurate input is kept even when the
  fit does not improve; rule 13/18/25: it is never tuned back toward 0.26, which
  is how 0.26 got there in the first place. It is also now *demonstrably* safe —
  three years, no KILL gate tripped.
- **NOT promoted to keeper.** It does not close its PRIMARY gate.
- **The belly-commitment lane is DOWNGRADED, not redirected.** With the CEMS
  basis restored, BASE belly gas is short by 910 / 747 / 512 MW on a *gross*
  reference; grid-delivered (netting parasitic/steam-host load) puts the true
  hole at roughly **250–600 MW**. That is too small to be the driver of the
  standing C5a and C4 FAILs. Chasing it further is low-yield.

## 4. Where the yield actually is — CT_PEAKER, attributed to cause C (PRICED OUT)

`FINDING-caiso119-gas-basis-adjudication-2026-07-24.md` §5 named the defect;
this session attributed it against the three candidate causes.

Model CT_PEAKER, 2024, from `caiso119_base_A/dispatch/2024_P1.parquet`:

- **80 plants, 834 tranches; all 44 bench CT_PEAKER facilities present** → not
  ABSENT (cause A refuted).
- **Fleet peak dispatch 3,542 MW; 588 of 834 tranches produce output** → not
  DERATED (cause B refuted).
- **Total energy 0.436 TWh vs 4.33 TWh actual (10 %)** → **PRICED OUT (cause C)**.

Per plant (model vs CEMS actual, TWh): Panoche 0.019 / **1.42**, Sentinel 0.077 /
0.48, Walnut Creek 0.082 / 0.32. The units are in the fleet with real capability
and simply never clear.

**Why this is the lane worth taking, and the caiso-118b idea may be right after
all — aimed at the wrong class.** CAISO's RA must-offer obligation covers
peakers, and units like Panoche are exactly the out-of-market-committed
capacity that obligation exists to hold. The model treats them as pure merchant
and prices them out. So the commitment-paradigm thesis survives — but its
missing energy is ~4 TWh in **CT_PEAKER**, not ~1 GW in CC belly.

It is also the most plausible live explanation for **C3c (price tail / scarcity)
FAIL**: a model that never starts its peakers cannot form a peaker-set tail, and
a price that never reaches peaker offers never starts them — the same closed loop
caiso-118b correctly identified, in the class where the energy actually is.

**Guardrail for whoever takes it (rules 1/13/14).** Attribution says "priced
out", which admits both a legitimate fix (a real RA/reliability commitment
mechanism on the peaker fleet, keyed on a published obligation) and an
illegitimate one (marking peaker offers down until 4 TWh appears). Only the
first is admissible. Any peaker mechanism needs a cited D-4 window, must clear
the C8 budget or the v2.2 grounded-above-budget path, and must not be sized to
the residual.

## 5. Carry-forward

**DO-NOT-REDO (new):**
- **`caiso_ra_min_load_frac` as a belly-volume lever.** Measured on the bytes:
  the bridge owns 1.8 % of floored cells and its level is capped. No value of
  this parameter moves the belly materially.
- **Quoting the ~99 % floor-binding rate as evidence about commitment** — it is
  `chp_steam` + `nuclear_mustrun`, both structural and D-2 exempt.

**Live:**
- CT_PEAKER priced-out, cause C attributed (§4) — the recommended next lane.
- DAM outage overlay (`caiso_dam_outages`) — a rule-14 improvement worth its own
  single-delta arm, but its crosswalk is 34/90 accepted → 29 plants / 9.78 GW,
  all CC, **zero peakers**, so it cannot touch §4.
- The RA must-offer QUANTITY gate remains a measured no-op (bridged CC fleet
  13.7–13.8 GW pmax, inside the published 15.6–19.1 GW obligation).

## 6. Reproduction

```
scripts/probes/_caiso119_ab_score.py          # the gate table in §1
scripts/probes/_caiso119_floor_scope_diag.py  # the mechanism decomposition in §2
scripts/probes/_caiso120_ct_peaker_attribution.py   # the §4 attribution
```
