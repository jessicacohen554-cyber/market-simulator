# FINDING — ERCOT-134 Phase 2: the ERCOT-116 A/B on the current keeper. The measured coal availability is measured-correct (impossible plant-hours −83/−86/−91 %) and rejected again on level (+6.5/+9.6/+11.4 TWh, G1 1/21) — the merit bias is BIGGER than predicted. The fresh BASE is promoted keeper.

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot134 / ercot116-regate ·
**Pre-commit** `docs/PRECOMMIT-ercot134-coal-avail-regate-2026-07-28.md`,
pushed (with the Phase-1 diagnosis and the probe) **before any solve** ·
**Runs** `2026-07-28-ercot116-regate-base` (**PROMOTED KEEPER**, owner
sign-off this session) and `2026-07-28-ercot116-regate-arm` (**REGISTERED
REJECTED PROBE**) · **Synthesis**
`docs/DIAGNOSIS-ercot134-coal-availability-pin-2026-07-28.md`.

## 1. Verdict against the pre-registered gates

| gate | result |
|---|---|
| **G0** validity | **PASS** — BASE: no COAL redistribution line, flag false, min-config floor armed 10 plants/2,164 MW 3/3. ARM: `COAL plant-grain redistribution — 10 crosswalked plant(s)` 3/3 (class targets 0.827/0.787/0.757), flag true, bite +6.1/+8.8/+11.9 TWh |
| **B1** BASE currency | rubric profile IDENTICAL to committed keeper; G1 **20/21** (vs 19/21 — the Sandy Creek repair flips 2025 `<$15` to PASS); BASE 2025 coal +0.674 vs committed keeper; Sandy Creek 2025 = 0.778 TWh (CAMPD 0.697) |
| **M1** un-pinning | ceiling-pin share 31.0/32.6/44.6 % → **28.1/27.9/38.6 %** |
| **M2** declaration alignment | 2025 six-plant model/COP ratios 0.77–0.99 → **0.95–1.13** (Martin Lake 1.45, see §3) |
| **M3** impossible hours | **22,633/24,627/30,697 → 3,846/3,462/2,622** (−83/−86/−91 %) |
| **M4** over-run | coal 66.928/67.248/73.652 vs actual 60.420/57.617/62.214 = **+6.5/+9.6/+11.4 TWh**; C1 16/16→15/16 free 12/12→11/12 (COAL_PRB 2025 +8.92 out of band); C3a −27.2/−8.0/−8.2 → **−35.3/−14.7/−13.2 %**; C3b 0.529/0.141/0.106 → 0.645/0.207/0.150 (2024 flips FAIL); C3c 68/12/0 → 47/6/0 |
| **M5** G1 signature | BASE **20/21**; ARM **1/21** — over-loaded in EVERY band of EVERY year (+6 to +18 pp); only 2023 `<$15` passes (0.566 vs actual 0.552, itself an overshoot past actual from below) |

**Decision-rule outcome:** G0 passed → M1–M5 reported in full, both bundles
registered with hand-written sidecar definitions, matrix cell updated, full
rubric scored on both. The ARM is **not promotable** (G1 1/21; C1 FAIL; C3a
FAIL all years) so the surprise branch did not fire. **No tuning anywhere.**

**On the BASE promotion vs the pre-commit's no-promotion clause, stated
openly:** the pre-commit's "no promotion in any branch" was written against
ERCOT-116 adoption — arming the coal envelope without an owner ruling — and
that clause is honoured: the ARM is rejected and the flag stays default-off.
The BASE promotion is a different act: a zero-config-delta keeper re-basis
onto the corrected committed tree (the ercot97→ercot98 precedent), executed
under an explicit owner instruction received mid-session, AFTER the
pre-commit was pushed ("Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still
be a keeper."), and scored strictly no-worse on the same scorer before the
promotion was made.

## 2. Predictions — 6 of 8 confirmed, and the two misses are the finding

| # | predicted | actual | |
|---|---|---|---|
| 1 | G0 passes, ARM bites | armed 3/3, +6.1/+8.8/+11.9 TWh | ✓ |
| 2 | BASE profile identical, G1 19/21±1, 2025 coal +0.3–1.5, Sandy ~0.9–1.1 | identical; 20/21; +0.674; Sandy 0.778 (just under range) | ✓ |
| 3 | ARM pin < 25 % every year | **28.1/27.9/38.6 %** | ✗ **miss** |
| 4 | ARM 2025 ratios into 0.95–1.05 | 0.95–1.13, Martin Lake 1.45 | partial |
| 5 | impossible −≥50 % every year | −83/−86/−91 % | ✓ (exceeded) |
| 6 | over-run +4–13 TWh monotone; C1 out 2025; C3a −≥3 pp; C3c falls | +6.5/+9.6/+11.4; C1 15/16; C3a −8.1/−6.7/−5.0 pp; C3c 47/6/0 | ✓ |
| 7 | ARM G1 ≤ BASE, landing 14–19/21 | **1/21** | ✗ **miss** (direction right, size wrong) |
| 8 | ARM fails on level, rejected probe | rejected | ✓ |

**The prediction-3 miss.** I anchored "<25 %" to ERCOT-116's published
"ceiling pin halved 43/41/50 → 20/16/17 %", which is an **energy-on-flat-top**
statistic; my probe's pin is **plant-hours at the availability bound**. On the
plant-hour basis the pin only eases ~3–6 pp, because with the ceiling raised
to the declaration coal is still cheap enough to run flat-out in many hours —
being at ceiling **in merit** is legitimate; the defect metric is the
impossible-hours count, which collapsed. Successors should treat the two pin
statistics as non-interchangeable.

**The prediction-7 miss is the result.** I predicted the over-loading would
cost a few bands; it costs **all of them**. At matched RT price the un-pinned
coal fleet runs 6–18 pp hotter than the real fleet in every band of every
year. The merit bias the estimate absorbs is not a band-local defect — it is a
uniform mispricing of coal relative to gas across the entire mid-merit range,
exactly ERCOT-116 §4.2's displacement signature (corr(dCoal, dGas) −0.93 to
−0.97), now sized on the current keeper with the min-config floor armed.

**Martin Lake's 1.45 model/COP overshoot (prediction-4 partial)** is worth a
line: the plant-grain redistribution pins the **class-hour mean** to the
measured fraction and water-fills per plant, so a plant whose model pmax
exceeds its declared rating can land above its own declaration while the
class total is right. Reported for the successor lane; not acted on.

## 3. What the A/B establishes

1. **The measured envelope is correct and the model cannot yet carry it.**
   Both facts, measured on one A/B: the input eliminates 83–91 % of the
   physically-impossible operation, and arming it breaks level, price and
   loading-shape everywhere because the coal-vs-gas merit ranking underneath
   is wrong (rule 14's discovered-bug reading, confirmed a second time, on
   the current recipe).
2. **The bias is uniform across price bands, not band-local.** Any successor
   mechanism that targets a single band (another level lever) is refuted in
   advance — this is the take-or-pay/committed share, sigmoid-floor,
   delivered-fuel-price territory named in the ERCOT-116 finding, i.e. the
   low/mid tranche structure or the gas side of the ranking.
3. **The BASE promotion closes the reproducibility gap.** The keeper is again
   solvable byte-for-byte from the committed tree, Sandy Creek 2025 is no
   longer falsely dark, and G1/C1 improve as a side-effect of the corrected
   measured input — no config delta, no new DOF.

## 4. Constraints honoured

Rule 22: span exactly {2023, 2024, 2025}. Rule 16: full span, one bundle per
arm, years sequential, arms sequential. Rule 15: both runs registered
in-session, hand-written definitions; retention pruned
`2026-07-24-ercot110-coal-dam-availability` and
`2026-07-24-ercot111-coal-econ-marginal`. Rule 26: matrix cell + header
updated in-session. Rules 13/19: nothing tuned against the over-run; no new
mechanism built. Owner decisions surfaced not decided: ERCOT-116 adoption
(sized here, still un-ruled), San Miguel registration. The ARM's
`legitimacy_diagnostics.json` and the BASE's carried
`calibration_attestation.json` (DOF ledger unchanged 11/8) are committed in
their bundles. Closed lanes stayed closed (DIAGNOSIS-ercot134 §12 list).

## 5. Environment parity

Fresh container, ercot115–132 baseline matched: no gtc-limits clean partition
("static TTC kept" 3/3), `hydro-plant-modes` WARNING, benign
`ercot_wtx_curtailment_driver` prb-stomp WARNING, no confirmed-retirements
partition. Pinned tests 36/36; `ScenarioConfig().cache_key()`
`603c2498bf71d21d` at session start and end.
