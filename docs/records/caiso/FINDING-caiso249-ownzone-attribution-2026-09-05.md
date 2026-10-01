# FINDING — caiso-249: the STORAGE residual bucket is **NOT** a loss-surface artifact. The delivery-factor correction is decisively material (96 % of DF-import zone-hours need it) yet the bucket does not shrink — **43.4 % / 55.0 %** of the 2024 / 2025 gap. In those hours the nearest own-zone thermal offer sits **ABOVE** λ in 65–70 % of the load-weight at a median of only **+$0.21 / +$0.44**: no thermal unit is marginal, and the price is set by inter-temporal (storage / hydro) duals. **The DOM_GAS/STORAGE split still moves 32 points between tolerances and remains unquotable.** The HUB acquittal survives on a better instrument but its published numbers are SUPERSEDED. ZERO SOLVES. **5 of 10 predictions FALSIFIED.**

**Session caiso-249, 2026-09-05.** Branch
`claude/caiso-backcast-calibration-247-zxaba3` off `main` `c234d4da`. Keeper
**`2026-09-05-caiso-246-b1-spot`** unchanged, NOT-YET, C3a +3.9 / +12.3 /
+11.4 %. Pre-registration:
`PRECOMMIT-caiso249-ownzone-loss-adjusted-attribution-2026-09-05.md`
(`3f1b97a8`, pushed before the estimator was coded and before any cell was
computed). Holdout freeze ACTIVE; every read inside 2023–2025. **Nothing armed
— no field, no flag, no solve, no promotion. C3a is not moved and no direction
is claimed.**

---

## §1 — THE RESULT

caiso-248 left `STORAGE` — a **residual** label, assigned when no unit
price-matched — carrying 43.2 % / 53.3 % of the gap. PRECOMMIT §0.1 diagnosed
the cause from the code: caiso-247/248 matched units against **every** CA
zone's dual inside 0.05 $/MWh while the keeper runs `caiso_zonal_loss_surface`,
whose own relation is `λ_y = λ_x·(1+dev_y)/(1+dev_x)` — 0.4–1.5 $/MWh apart at
CAISO levels with nothing congested. This session replaced that with **own-zone
complementarity** (exact; unit and dual in the same zone, no delivery factor
between them) plus a **delivery-factor import pass** using the measured
`CAISO_loss_surface.csv` deviations.

**The diagnosis was right about the mechanism and wrong about the consequence.**

| 2025, gap $3.151/MWh | caiso-248 | **caiso-249** |
|---|--:|--:|
| DOM_GAS | 40.2 % | **37.0 %** |
| STORAGE | 53.3 % | **55.0 %** |
| HUB | 3.6 % | **5.1 %** |
| DOM_OTHER | 1.0 % | 1.2 % |
| UNRESOLVED | 1.9 % | 1.6 % |

| 2024, gap $3.781/MWh | caiso-248 | **caiso-249** |
|---|--:|--:|
| DOM_GAS | 47.1 % | **43.3 %** |
| STORAGE | 43.2 % | **43.4 %** |
| HUB | 4.0 % | **7.8 %** |
| DOM_OTHER | 2.6 % | 2.4 % |
| UNRESOLVED | 3.2 % | 3.1 % |

**G-DF says the correction did real work**: 14,946 (2024) / 10,608 (2025)
zone-hours were reclassified through the delivery-factor pass, and in
**97.1 % / 96.1 %** of them the RAW `|λ_z − λ_z'|` was outside the 0.05 window
while the DF-corrected residual was inside. The loss surface *was* the barrier
the old estimator kept hitting. **It simply was not what put the hours in the
bucket.** Own-zone matching is stricter than the old ISO-wide match — it
removes spurious cross-zone coincidences — and the DF pass adds genuine ones
back. The two roughly cancel; the bucket does not move.

**What the bucket actually is** (post-registration characterisation, §4): in
`STORAGE` zone-hours the nearest **available own-zone domestic offer** sits
**above** λ in **64.7 / 65.7 / 69.8 %** of the load-weight, at a median wedge of
only **+0.27 / +0.21 / +0.44 $/MWh**, with ~50 % inside ±$0.75 and a long tail
(p90 +18.3 / +21.1 / +8.8). λ is sitting **just under the thermal offer stack**.
That is the signature of a price set by something cheaper than the cheapest
available thermal unit — storage discharge opportunity cost, hydro water value,
an import or a renewable at the margin — **not** of a failed match. caiso-202
§C called this cell "unmatched (storage/hydro inter-temporal duals)" and put it
at 22 % / 19 %; on this instrument it is **43–55 %**.

---

## §2 — GATES

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| **G-FLEET** (new) | **FAIL** — see §4.1 | PASS | PASS |
| **G-CONSERVE** (cells sum to gap; gap = caiso-248's) | PASS (1.3071) | PASS (3.7812) | PASS (3.1507) |
| **G-BENCH** | PASS | PASS | PASS |
| **G-RECON** | PASS (gross) | PASS (gross) | PASS (gross) |
| **G-DF** (≥ 60 % raw-outside-TOL) | PASS 66.6 % | PASS 97.1 % | PASS 96.1 % |
| **G-ORDER** (HUB-first CR reproduces caiso-247's ±0.01) | — | **FAIL** 0.86 vs 1.026 | **FAIL** 0.74 vs 0.642 |

G-CONSERVE reproduces caiso-248's `gap_hourly` **to the fourth decimal in all
three years**, which is the proof that only the labelling moved.

---

## §3 — PREDICTIONS, SCORED AGAINST INTEREST

| # | registered | measured | verdict |
|---|---|---|---|
| **P-1** | G-FLEET passes all three years | 2023 **FAILS** (`phantom ['fuel:oil']`) | **FALSIFIED** — §4.1 |
| P-2 | G-CONSERVE holds; gap exactly 1.3071 / 3.7812 / 3.1507 | exact in all three | **HOLDS** |
| **P-3** | G-ORDER: HUB-first CR reproduces 1.026 / 0.642 to ±0.01 | **0.86 / 0.74** | **FALSIFIED** — the HUB cell is reported as CHANGED, not confirmed (§4.2) |
| **P-4** | STORAGE falls to 5–25 % of the gap in both failing years | **43.4 % / 55.0 %** — 2025 rose | **FALSIFIED**, and the registered meaning fires: *the loss surface was NOT the main barrier and the residual is genuinely unattributed — a much worse position, and the honest one* |
| **P-5** | DOM_GAS rises to 60–85 % (2024) / 55–80 % (2025) | **43.3 % / 37.0 %** — it FELL | **FALSIFIED** |
| P-6 | No new named object > 10 % of the gap outside {DOM_GAS, HUB, STORAGE} | DOM_OTHER 2.4 / 1.2 %, UNRESOLVED 3.1 / 1.6 % | **HOLDS** — no new object, as registered |
| P-7 | G-DF material, ≥ 60 % raw-outside-TOL | 66.6 / 97.1 / 96.1 % | **HOLDS** |
| P-8 | CC-hot / CT-cold survives | CC_REGULAR +2.82 / +2.51, CC_CHP +4.62 / +4.10; CT_PEAKER −5.29 / −2.92, CT_CHP −16.22 / −14.80 | **HOLDS — and sharper** on own-zone matching |
| **P-9** | tol = 0.75 moves the DOM_GAS share < 15 points | **+31.7 (2024), +32.7 (2025)** | **FALSIFIED** — the registered consequence stands: **no DOM_GAS number may be quoted** |
| P-10 | HUB ≤ 8 % of the gap in both failing years | 7.8 % / 5.1 % | **HOLDS** (2024 barely) |

**5 hold, 5 falsified.** The headline repair failed; the negative it produced
is the result.

---

## §4 — DISCLOSURES AGAINST INTEREST

### §4.1 — G-FLEET failed in 2023, on my own documented false positive, and I am NOT re-running it to a pass

The new G-FLEET gate flags a fleet family whose fuel appears in the detected
injected-must-run set. In 2023 it flags `fuel:oil` — because caiso-248's shape
detector flags the 2023 `oil` klass (**65 MWh total, 2 distinct levels**) as a
monthly step profile by coincidence. caiso-248 §5.4 documented that exact false
positive **before this run**, so it is a known artifact, not a surprise.

**The fleet is nonetheless correct**: `derived_run_year_inputs` consumes only
`"biomass" in injected`, and `oil` is not in the solver's
`_INJECTED_MUSTRUN_CLASSES`, so no oil unit was dropped and none should have
been. The *check* mislabels; the *fleet* is right.

The right implementation is to key the phantom test on the solver's
authoritative `_INJECTED_MUSTRUN_CLASSES` tuple rather than on the shape
heuristic. **I have not applied that here**, because I only saw the failure
after registering the gate, and changing a gate to convert its own failure into
a pass is precisely the move the pre-registration exists to prevent. **2023 is
reported with the gate FAILED as written**, and the fix is filed as §6 item 3
for a session that registers it in advance.

### §4.2 — The HUB acquittal survives, but caiso-247's published HUB numbers are SUPERSEDED

G-ORDER failed: under caiso-247's own HUB-first ordering the hub CR is now
**0.86 (2024) / 0.74 (2025)**, not 1.026 / 0.642. The cause is the same repair —
the landing-zone reach test is now delivery-factor corrected, so the hub label
reaches zone-hours it previously could not (HUB weight 3.9 % → 7.5 % in 2024,
5.7 % → 10.9 % in 2025).

**The verdict direction is unchanged and, if anything, firmer**: CR ≤ 1 in both
failing years under every variant measured here (0.86 / 0.74 HUB-first;
HUB_MEASURED 1.16 / 0.53 domestic-first), and HUB is 7.8 % / 5.1 % of the gap.
**But the specific numbers 1.026 / 0.642 must no longer be quoted** — they were
measured on an estimator that could not see across the loss surface. Reported
as a change, exactly as the gate required.

### §4.3 — The correction made the lane's position WORSE, and that is the finding

Before caiso-247 the lane believed the residual was plausibly a hub-basis
object. caiso-247 acquitted the hub and named biomass. caiso-248 withdrew
biomass. caiso-249 now shows the largest cell is **not an estimator artifact**
either. **Over three sessions the attributed share of the C3a gap has gone
down, not up.** The honest statement of where the residual sits is: ~40 % on
the domestic gas offer surface, ~50 % in hours where **no thermal unit is
marginal at all**, ~5 % on the import seam — and the boundary between the first
two moves 32 points with the matching tolerance.

### §4.4 — The wedge measurement is a DESCRIPTION, not a new labelling rule

PRECOMMIT §3's stop rule forbids reaching for another labelling rule after a
falsified P-4. The wedge statistics in §1 are a post-registration
*characterisation of a registered cell* (the caiso-247 group-characterisation
convention) — they relabel nothing, change no cell, and are excluded from every
scored prediction. They are reported because they make the next object
concrete.

### §4.5 — Own-zone matching can still over-identify

`mc = λ` is necessary, not sufficient: a unit sitting at a bound whose offer
coincides with its own zone's dual is counted. Own-zone matching removes the
*cross-zone* coincidences the old estimator had but not this one. The tol
sensitivity (§3 P-9) is the honest bound, and it is large.

### §4.6 — What did NOT change

`gap_hourly` (G-CONSERVE, to four decimals), the month totals, the CC-hot /
CT-cold split, the weight-basis disclosure (caiso-247 §4.5), and the demotion
of the import seam and the two fitted firm prices as C3a objects.

---

## §5 — MONTHS (2025, $/MWh contribution)

December: DOM_GAS **+0.296**, STORAGE **+0.373**, HUB +0.027, of a +0.711
month — the December slab is now **more than half** an hours-where-no-thermal-
unit-is-marginal phenomenon. Apr–Jul: DOM_GAS +0.602 against STORAGE **+0.813**
(2024: +0.591 vs +1.012). **Both of the lane's standing month objects are
majority-STORAGE on this instrument**, which is a different picture from
caiso-247's (which had them majority-DOM_GAS) and follows entirely from the
own-zone restriction.

---

## §6 — THE QUEUE

1. **NEW, ranked first: what sets λ when no thermal unit is marginal?** 43–55 %
   of the gap. The wedge says λ sits just under the thermal stack (median
   +$0.21 / +$0.44, ~50 % inside ±$0.75, long tail). The candidates are
   storage discharge opportunity cost, hydro water value, and the import /
   renewable margin — all **inter-temporal or zero-MC duals with no offer to
   match against**. A phase-0 should reconstruct storage and hydro duals from
   the committed sidecars (both are committed) and test whether λ equals the
   storage discharge opportunity cost in those hours. Zero LP.
2. **The DOM_GAS/STORAGE boundary stays unquotable** until item 1 resolves
   (P-9: 32 points between tolerances). No DOM_GAS number should be cited from
   caiso-247, -248 or -249.
3. **Fix G-FLEET's phantom test** to key on the solver's
   `_INJECTED_MUSTRUN_CLASSES` rather than the shape heuristic — registered in
   advance, not applied retroactively (§4.1).
4. **The CC-hot / CT-cold split** (caiso-247 §4.7, reconfirmed and sharper
   here) — still live, still needs a functional-form charter.
5. **Demoted, unchanged:** the import seam (5.1 / 7.8 % of the gap) and the two
   fitted firm prices — structural objects under rule 1, not C3a levers.
6. **Owner ask, carried:** the C3a weight basis (caiso-247 §4.5).

---

## §7 — DO-NOT-REDO ADDS

1. **The STORAGE residual bucket is NOT a loss-surface artifact.** Never
   re-propose a loss/delivery-factor repair of the price match as the way to
   resolve it — measured here with the correction applied and G-DF passing at
   96 %.
2. **Never quote caiso-247's HUB CR 1.026 / 0.642.** Superseded by 0.86 / 0.74
   (§4.2). The acquittal direction stands; the numbers do not.
3. **Never quote any DOM_GAS share from caiso-247/248/249** — 32 points of
   tolerance sensitivity (§3 P-9).
4. **Never quote caiso-247's month-by-regime split** — Apr–Jul and December are
   majority-STORAGE on the own-zone instrument, not majority-DOM_GAS (§5).
5. caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7, caiso-244 §7,
   caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8,
   caiso-230 §9 stand in full.

---

## §8 — DELIVERABLES

`PRECOMMIT-caiso249-ownzone-loss-adjusted-attribution-2026-09-05.md`
(`3f1b97a8`, pushed first); `scripts/probes/_caiso249_ownzone_attribution.py` +
`results/calibration/_caiso249_ownzone_attribution.json`; this finding; the
calibration-log entry; an evidence-only append to the CAISO matrix shard.
**No cell verdict moves; no mechanism was tested; no run registered; keeper
unchanged.**

**Next number: caiso-250.**
