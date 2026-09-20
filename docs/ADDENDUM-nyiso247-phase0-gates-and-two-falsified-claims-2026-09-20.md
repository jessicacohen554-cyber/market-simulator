# ADDENDUM nyiso-247 — the four ZERO-LP gates PASS, and TWO OF MY OWN PRECOMMIT CLAIMS ARE FALSIFIED

**Session nyiso-247 (ORCHESTRATOR, zero LP).** **Date** 2026-09-20.
**PRECOMMIT** `docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md`, committed and pushed at
**`40316764`** before any number below existed.
**Record** `results/calibration/_nyiso247_fuelinv_phase0.json`,
built by `scripts/probes/nyiso247_fuelinv_phase0.py` (which imports nyiso-246's own `affected`
selector, `weighted_quantiles` estimator and `GRID`, and `derive_nyiso_offer_level_dispersion`'s
`state_windows`, all unchanged — one construction, one identification).

**THIS ADDENDUM IS PUSHED BEFORE A SHARD IS LAUNCHED.** Two claims I made in the PRECOMMIT are
falsified by its own gates. Both are recorded here, at full magnitude, **before** any solve result
exists — which is the only reason G-E was written as a gate that decides nothing.

---

## 1. THE GATES — ALL FOUR PASS

### G-A — THE IDENTITY: **PASS, EXACTLY.**

| year | armed rows | armed MW | max abs slope err | max abs mc move on unarmed rows |
|---|---:|---:|---:|---:|
| 2022 | 329 | 14,943.7 | **0.0** | **0.0** |
| 2023 | 329 | 14,943.7 | **0.0** | **0.0** |
| 2024 | 329 | 14,943.7 | **0.0** | **0.0** |
| 2025 | 329 | 14,943.7 | **0.0** | **0.0** |

Bar was ≤ 1e-4 $/MWh; the measurement is exact. The test is the **per-row slope of `mc` against
delivered fuel**: the keeper's median armed-row slope is **7.7475** MMBtu/MWh (`phys × base_HR`) and
the arm's is **9.5758** (`mult × base_HR`), a difference of **1.8283** = the median
`offer_markup_hr` to machine precision. **The disarm restores full delivered-fuel tracking and does
nothing else.**

### G-B — THE SIGN GUARD: **PASS on all three legs.**

`Q_mod` pooled 2022–2025 on the family's frozen 199-point grid, MMBtu/MWh:

| rank | keeper | **arm** | book | move | gap keeper → arm |
|---|---:|---:|---:|---:|---|
| p10 | −8.4273 | −3.0892 | −16.4739 | +5.3381 | +8.0466 → **+13.3847** |
| p25 | −3.2325 | −0.6075 | −0.6902 | +2.6250 | −2.5423 → +0.0827 |
| **p50** | −0.8485 | **+0.4094** | **+2.0352** | **+1.2579** | −2.8837 → **−1.6258** |
| **p75** | +0.5530 | **+2.0182** | **+11.9281** | **+1.4652** | −11.3751 → **−9.9099** |
| **p90** | +2.8072 | **+5.4709** | **+27.8803** | **+2.6637** | −25.0731 → **−22.4094** |
| p95 | +4.2432 | +9.0831 | +39.7139 | +4.8399 | −35.4707 → −30.6308 |
| p99 | +11.8388 | +23.9533 | +96.7097 | +12.1145 | −84.8709 → −72.7564 |

* **S1 DIRECTION — PASS.** Strictly up at p50, p75 and p90, and in fact at every reported rank.
  **The model's median conditional implied-heat-rate response crosses from NEGATIVE to POSITIVE**
  (−0.8485 → +0.4094): the sign error the object names is closed at the median.
* **S2 NO OVERSHOOT — PASS, with margin.** Max positive excursion over every grid rank ≥ 0.50 is
  **−1.6258** — the arm stays *below* the book at its closest approach (p50) and never crosses.
  No knife-edge.
* **S3 NET CLOSURE — PASS.** Rank-mean `|Q_mod − Q_book|` over the full 199-point grid
  **12.1646 → 11.9268**.

**REPORTED AT FULL MAGNITUDE, because it is the cost of the repair and S3 is what admits it:**
below p50 the fit **WORSENS**, rank-mean `|Q_mod − Q_book|` **6.9868 → 9.0060**, driven by p10
(+8.0466 → +13.3847). The model already sat above the book at the bottom 14.5 % of ranks
(nyiso-246's `r_anchor = 0.145`) and the disarm lifts it further. **S3 passes because the gain above
p50 exceeds that loss on the full grid — narrowly (12.1646 → 11.9268, a 2.0 % closure).** A reader
should take the headline as *"the sign is repaired at and above the median, at a measured cost in
the bottom sixth"*, not as *"the distribution now matches."* §2.2 of the PRECOMMIT said this form
closes the SIGN and no more; the numbers say exactly that.

### G-F — RULE 19: **PASS in substance**, with the reconciliation corrected in §3.

Armed capacity by class (2022, identical in all four years): ST_GAS **7,027.7 MW**, CC_REGULAR
**3,056.6**, CT_PEAKER **2,707.3**, CC_CHP **2,152.0**. The arm **removes** one of the five armed
non-base writers and adds nothing.

---

## 2. FALSIFIED CLAIM #1 — THE DISARM IS **NOT** LEVEL-NEUTRAL. G-E FIRED, AS DESIGNED.

PRECOMMIT §2.2 asserted *"removing it is level-neutral in annual mean by construction."*
**That is WRONG, and G-E exists precisely to catch it before the solve.**

Capacity-weighted mean of the removed term `offer_markup_hr × (anchor_z − G_z(t))` over **all 8760
hours**, $/MWh (negative = the keeper's armed term SUBTRACTS on average, so the disarm RAISES the
offer by that much):

| year | **ISO** | NYC | Long_Island | Capital_Hudson | Upstate_West | Lower_Hudson |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | **−1.4869** | **−4.3599** | +1.2216 | +0.3952 | +0.0026 | −0.0000 |
| 2023 | **−2.0058** | **−4.9298** | −0.0722 | +0.2768 | +0.0215 | +0.0000 |
| 2024 | **−2.7724** | **−5.7275** | −2.0157 | +0.0746 | +0.0038 | −0.0000 |
| 2025 | **−1.5946** | **−5.3573** | +0.6356 | +1.7434 | +0.0476 | −0.0000 |

**So the disarm is a LEVEL INTERVENTION of +$1.49 to +$2.77/MWh on the armed rows, concentrated
almost entirely in NYC at +$4.36 to +$5.73/MWh.** The per-zone anchors are *not* each zone's own
mean delivered gas once `nyiso_zonal_gas_basis` is applied — in NYC the anchor sits materially below
the zone's own delivered mean, so the armed term subtracts there in most hours, not merely in tight
ones. nyiso-246's "antisymmetric about the annual mean" reading holds for the ISO-level series it
was measured on and **does not hold per zone**.

**What this does and does not change.** It changes nothing about the form (rule 1 `[R-STRUCT]`: a
structurally-correct mechanism is never selected or rejected on the residual, and G-E was written to
decide nothing). It changes what the reader must be told: **NYC is a load pocket, so a +$5/MWh level
move on its armed rows is a live C3a exposure in 2023/2024/2025, the years the model currently
PASSES.** That exposure is now on the record **before** the solve, and promotion criteria P2/P3 —
the ISO tier must not degrade and C1/C2 must not cross PASS→FAIL — are the guards that bind it.

## 3. FALSIFIED CLAIM #2 — CT_PEAKER `committed` DOES NOT CLIP TO EXACTLY ZERO

PRECOMMIT §3 G-F reconciliation #2 said CT_PEAKER's `committed` markup *"clips to 0
(`mult = phys = 0.843`)"* and is *"provably untouched."* **Two rows carry a non-zero markup** —
`CT_PEAKER_Capital_Hudson_p2628_committed` (2.0 MW) and `CT_PEAKER_NYC_p55699_committed` (18.0 MW),
**20.0 MW of the class's 346.7 MW of committed capacity**, in all four years.

**The magnitude is float residue, not a mechanism:** the markups are **2.99e-15** and **1.20e-15**
MMBtu/MWh — `max(0, mult − phys)` evaluated at `mult == phys == 0.843` — and the largest absolute
term they produce in any hour of any year is **1.16e-13 $/MWh**. The reconciliation holds in
substance (`nyiso_ct_peaker_committed_measured`'s band is materially untouched, and the disarm
neither stacks on it nor undoes it); it is exact to **1e-13 $/MWh**, not to 0.0, and the PRECOMMIT
overstated it. Recorded rather than quietly re-worded.

## 4. WHAT THE ARMED MECHANISM DOES TO THE PRICE-SETTING RUNG — the number this session exists for

The **peak** band is the rung that sets the price in a scarcity hour, and it is where the markup
multipliers live (CT_PEAKER 3.000, ST_GAS 3.200 above `phys`, against 0.075–0.342 on every econ
band). Capacity-weighted mean of the removed term over the **38 peak rows / 1,544.2 MW**:

| year | all hours | **hours with gas ≥ that year's p90** |
|---|---:|---:|
| 2022 | −4.91 | **−109.00** |
| 2023 | −7.28 | **−49.20** |
| 2024 | −11.12 | **−96.20** |
| 2025 | −0.86 | **−141.08** |

$/MWh. **In the tightest gas decile of every year the armed mechanism removes $49–141/MWh from the
price-setting rung**, independently corroborating nyiso-182's −$188/MWh 2025-top-decile figure on a
different window and a different weighting.

## 5. GATE DISPOSITION

**G-A PASS · G-B PASS (S1, S2, S3) · G-F PASS · G-E reported, decides nothing.**
PRECOMMIT §7 **P1's zero-LP half is met**, so the four year-isolated shards are launched against
this addendum's commit SHA. G-C (loading shape) and G-D (C1/C2) are post-solve and are evaluated in
the RESULT against the bars fixed in the PRECOMMIT — **which are not restated, re-derived or
relaxed here.**
