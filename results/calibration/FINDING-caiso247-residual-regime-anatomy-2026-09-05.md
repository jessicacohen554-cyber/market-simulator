# FINDING — caiso-247: the CAISO C3a residual is NOT a hub-basis residual. On the corrected node-complementarity definition the hub-marginal regime carries **4.0 % / 3.6 %** of the 2024 / 2025 gap on **3.9 % / 5.7 %** of the weight (CR **1.03 / 0.64**) — the handoff's own ACQUITTAL falsifier fires, and caiso-202 §C's ~5 % survives its instrument's repair. The carriers are the DOMESTIC surface (DOM_GAS 47 / 40 %, CC_REGULAR + CC_CHP), **BIOMASS** (18 / 18 % of the gap on 7 % of the weight, mean residual **+$9.85 / +$7.84 /MWh** — a NEW named object), and a storage bucket that is largely a loss-surface artifact. ZERO SOLVES. **5 of 10 predictions FALSIFIED**, including the headline.

**Session caiso-247, 2026-09-05.** Branch
`claude/caiso-backcast-calibration-247-zxaba3` off `main` `c9f1d26e`. Keeper
**`2026-09-05-caiso-246-b1-spot`** (`caiso246_b1_spot_coverage`, `git_sha`
`900402b`), **NOT-YET**, C3a the sole load-bearing FAIL at **+3.9 / +12.3 /
+11.4 %**. Pre-registration:
`PRECOMMIT-caiso247-residual-regime-anatomy-2026-09-05.md` (`004c0d39`, pushed
to `origin` before the probe was written and before any cell of the object was
computed). No `complete` / `final` marker; holdout freeze ACTIVE; **every read
stayed inside 2023–2025. NOTHING ARMED — no field, no flag, no solve, no
promotion; the keeper is unchanged.**

---

## §1 — HEADLINE

Queue item A, taken as ranked. Every zone-hour of 2023–2025 is labelled by what
sets the model's price and the C3a gap is decomposed by month × regime on the
caiso-131 §2 / caiso-140 §A common-weight convention, so the cells sum
**exactly** to the reconstructed gap. **All five gates pass.**

**The C3a gap by regime** (`_caiso247_residual_regime_anatomy.json`; weight
share and gap share of the reconstructed gap; **CR** = gap share ÷ weight
share, so CR = 1 means the regime is *not* a carrier, only where the hours
are):

| 2025 (gap $3.151/MWh) | weight | gap $ | gap share | **CR** | mean residual |
|---|--:|--:|--:|--:|--:|
| HUB_FITTED | 0.7 % | +0.050 | 1.6 % | 2.18 | +6.85 |
| HUB_MEASURED | 4.9 % | +0.065 | 2.1 % | 0.42 | +1.32 |
| **DOM_GAS** | **52.4 %** | **+1.267** | **40.2 %** | 0.77 | +2.42 |
| **DOM_OTHER (biomass)** | **7.3 %** | **+0.568** | **18.0 %** | **2.49** | **+7.84** |
| STORAGE | 31.3 % | +1.151 | 36.5 % | 1.17 | +3.68 |
| UNRESOLVED | 3.4 % | +0.049 | 1.6 % | 0.47 | +1.47 |

| 2024 (gap $3.781/MWh) | weight | gap $ | gap share | **CR** | mean residual |
|---|--:|--:|--:|--:|--:|
| HUB_FITTED | 0.2 % | −0.004 | −0.1 % | −0.48 | −1.81 |
| HUB_MEASURED | 3.7 % | +0.155 | 4.1 % | 1.10 | +4.18 |
| **DOM_GAS** | **64.6 %** | **+1.781** | **47.1 %** | 0.73 | +2.76 |
| **DOM_OTHER (biomass)** | **6.9 %** | **+0.683** | **18.1 %** | **2.60** | **+9.85** |
| STORAGE | 21.6 % | +1.087 | 28.7 % | 1.33 | +5.04 |
| UNRESOLVED | 3.0 % | +0.080 | 2.1 % | 0.70 | +2.66 |

| 2023 — the C3a-PASSING control (gap $1.307/MWh) | weight | gap $ | gap share | **CR** |
|---|--:|--:|--:|--:|
| HUB (fitted + measured) | 10.9 % | +0.495 | **37.8 %** | **3.46** |
| DOM_GAS | 60.1 % | **−0.189** | −14.5 % | −0.24 |
| DOM_OTHER (biomass) | 2.5 % | +0.194 | 14.8 % | 5.98 |
| STORAGE | 22.8 % | +0.726 | 55.5 % | 2.44 |

**Three results.**

1. **The hub is acquitted on the scored statistic.** `CR(HUB)` is **1.026 in
   2024 and 0.642 in 2025** — the hub-marginal regime carries its proportional
   share, or less. The PRECOMMIT §2 P-5 falsifier is explicit about what that
   means: *"CR(HUB) < 1.0 → the Palo Verde hub + adder chain is ACQUITTED and
   the object is the domestic offer surface."* It fires in 2025 and 2024 sits
   on the window's bottom edge. It survives both robustness variants: G-ORDER
   (DOM_GAS ahead of HUB) gives 1.188 / 0.583, and the tol = 0.75 variant gives
   0.959 / 0.516.
2. **caiso-202 §C's ~5 % survives the repair of its own instrument.** caiso-244
   §3.6 showed caiso-202's marginal-hour test under-counted hub-marginal hours
   by 4× (< 5 % → 18–23 % of hours), which left open whether its **gap-share**
   acquittal survived. On the like-for-like **positive-part** basis caiso-202
   used, the import legs carry **3.6 % (2024) / 5.1 % (2025)** of the positive
   gap against its ~5 % / ~5 % — reproduced on a NEW keeper, a corrected
   marginal-hour definition and an independent estimator. The hour count was
   wrong; the gap attribution was right.
3. **A new named object: BIOMASS.** `DOM_OTHER` is 96 % / 86 % biomass — **184
   units, 847.3 MW**, offering at a near-flat **mc mean $33.32 / median
   $31.13** (2025), i.e. parked in the middle of CAISO's own price
   distribution, which is why so small a fleet is marginal so often. It
   price-sets in **6.9 % / 7.3 %** of the load-weighted zone-hours and the
   model runs **+$9.85 / +$7.84 per MWh** over the actual RT in exactly those
   hours — the **largest mean residual of any regime** — and it **strengthens**
   under the wider tolerance (CR 2.60 → 3.62 in 2024, 2.49 → 3.79 in 2025). It
   has never been named in this lane: caiso-202 §C folded it into "unmatched".
   (The 184 biomass units sit inside the 3,230 MW of CAISO capacity carrying no
   `plant_group`; the rest of that set is Diablo Canyon — 2,240 MW at mc $2.50
   — and 27 oil units, 142.7 MW at mc ≈ $228. Neither is a carrier.)

**The determination is unchanged.** Nothing was armed and no run was
registered (no solve, so nothing to register under rule 15 — the caiso-244 /
caiso-245 precedent). C3a is not moved and **no direction is claimed: the
count of consecutive favourable directions stays at five.**

---

## §2 — GATES, ALL SCORED (PRECOMMIT §1.4)

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **G-BENCH** (recomputed `rt_lw` vs committed, ≤ 0.01) | 54.1748 / 54.17 | 34.6475 / 34.65 | 34.4233 / 34.42 | **PASS** |
| **G-RECON** (caiso-244's own gate, new keeper) | PASS, gross | PASS, gross | PASS, gross | **PASS** |
| **G-GAP** (\|hourly − printed\| ≤ 1.00) | 1.3071 vs 2.12 → 0.813 | 3.7812 vs 4.27 → 0.489 | 3.1507 vs 3.94 → 0.789 | **PASS** |
| **G-CLASS** (UNRESOLVED ≤ 12 % of weight) | 3.7 % | 3.0 % | 3.4 % | **PASS** |
| **G-ORDER** (P-5 verdict stable under DOM_GAS-first) | — | 1.026 → 1.188 (same verdict) | 0.642 → 0.583 (same verdict) | **PASS** |

The stop rule (PRECOMMIT §3) was not reached in any year.

---

## §3 — PREDICTIONS, SCORED AGAINST INTEREST

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-RECON passes all three on the gross basis | passes all three, gross | **HOLDS** |
| P-2 | G-GAP holds; hourly BELOW printed by 0.3–1.0 | below by 0.813 / 0.489 / 0.789 | **HOLDS** |
| P-3 | UNRESOLVED ≤ 12 % of weight every year | 3.7 / 3.0 / 3.4 % | **HOLDS** |
| **P-4** | HUB carries 20–34 % of weight each year; 2025 largest | **10.9 / 3.9 / 5.7 %**; **2023** largest | **FALSIFIED**, badly — see §4.1 |
| **P-5** | **CR(HUB) ∈ [1.0, 1.8] in BOTH 2024 and 2025** | **1.026** (bottom edge) / **0.642** | **FALSIFIED on the 2025 leg — the registered ACQUITTAL branch** |
| P-6 | HUB_FITTED ≥ 25 % of the total HUB gap in 2025 | **43.4 %** (0.050 of 0.115) | **HOLDS — and is nearly empty**, see §4.3 |
| **P-7** | 2023 CR(HUB) within ±0.4 of the 2024/2025 mean | **3.461** vs mean **0.834** (+2.63) | **FALSIFIED — in the direction OPPOSITE to the registered concern**, §4.2 |
| P-8 | 2025 Apr–Jul > December, and DOM_GAS > HUB inside Apr–Jul | **1.617 vs 0.711**; **0.643 vs 0.087** | **HOLDS on both legs** |
| **P-9** | STORAGE 5–20 % of 2025 weight | **31.3 %** | **FALSIFIED** — and the cause is measured, §4.4 |
| **P-10** | every 2024/2025 regime CR ∈ [0.6, 2.2] — i.e. the residual is a LEVEL and no carrier is named | DOM_OTHER **2.60 / 2.49**; HUB_FITTED −0.48 (2024); HUB_MEASURED 0.42, UNRESOLVED 0.47 (2025) | **FALSIFIED — a carrier IS named: biomass** |

**5 hold, 5 falsified**, the headline discriminator among the falsified. None
is argued away below.

---

## §4 — DISCLOSURES AGAINST INTEREST

### §4.1 — P-4 was wrong by a factor of 3–5, and the reason is my registration, not the data

I registered the HUB **weight share** at 20–34 % by carrying caiso-244 §3.6's
**hour** share (19.9 / 17.7 / 23.0 %) across to a **load-weighted zone-hour**
share. Two things break that, both knowable before the fact:

* **the load weighting** — the hub price is identified at its landing zone
  (NP15 / SP15_rest), which together carry well under half of CAISO load;
* **the zonal loss surface** — the keeper runs `caiso_zonal_loss_surface`
  (caiso-164), so a hub-marginal landing zone prices ZP26 / LA_BASIN / SDGE at
  `λ_L/(1 − loss)`, 0.4–1.2 $/MWh away, and my frozen 0.05 reach test cannot
  see it. At tol = 0.75 the HUB weight share rises to 14.5 / 9.3 / 12.7 % —
  still nowhere near the registered window.

I under-thought the estimator, not the market. **It does not rescue the
verdict**: CR is scale-free, so the acquittal is measured on whatever weight
HUB actually carries, and it reads ≤ 1.03 in both failing years on all three
variants.

### §4.2 — P-7 is falsified in the direction that STRENGTHENS the acquittal

I registered the concern that 2023's CR(HUB) might be **below** the failing
years', which would have made the hub the thing separating the passing year
from the failing ones. It is **3.461** — four times higher. In the year C3a
**passes**, the hub regime carries 37.8 % of a small ($1.31) gap; in the years
it **fails**, ~4 % of a large one. The hub is where the residual is *least*
concentrated exactly when the residual is worst. That is the opposite of the
hub-carrier reading and it was not the outcome I set up to find.

### §4.3 — P-6 holds and is nearly empty

HUB_FITTED (the two fitted $28 / $48 firm prices) carries **43.4 %** of the
HUB gap in 2025, above the 25 % I registered, with CR 2.18 — the strongest
form of "the fitted prices are live" available on the scored statistic. But
HUB itself is **3.6 %** of the gap, so HUB_FITTED is **1.6 %**, or
**$0.050/MWh** of a $3.15 gap. The December cell is where it concentrates
(+0.049 of the year's +0.050), which is caiso-245 §3(b)'s 101 `DSW_solar_PV`
hours seen on the residual. **Item B stays exactly what caiso-245 called it —
a G-26 honesty item, not a C3a lever** — and this measurement is the first
that bounds it: the honesty question is worth 1.6 % of the gap.

### §4.4 — The STORAGE bucket is largely a loss-surface artifact, and it contaminates the DOM_GAS/STORAGE split

`STORAGE` is a **residual** label: it is assigned only when no unit
price-matches. At tol = 0.05 it takes 31.3 % of 2025's weight; at tol = 0.75
it collapses to **3.4 %** and its contribution flips from **+1.151 to −0.125**,
while DOM_GAS rises from 0.524 → 0.752 weight and 1.267 → **2.032** gap. Most
of the "storage" bucket is domestic-gas-marginal hours displaced out of the
0.05 window by the zonal loss surface. **The honest statement is therefore:
DOM_GAS + STORAGE together carry 75.8 % (2024) / 76.7 % (2025) of the gap, and
the split between them is tolerance-dependent and should not be quoted.** The
two conclusions that ARE robust across both tolerances and both priority
orders are the HUB acquittal and the biomass concentration.

### §4.5 — 11–38 % of the printed C3a gap is a WEIGHT-BASIS term, and this is NOT offered as a reduction of C3a

The rubric's C3a model side is `Σ_z p_z·D_z / Σ_z D_z` with `p_z` the zone's
own demand-weighted mean (`render_calibration_html.py` L2175), which reduces
to a **MODEL-demand-weighted** hourly mean; its actual side (`rt_lw`) is a
**MEASURED-load-weighted** hourly mean. This probe weights both sides by the
measured load, so the entire G-GAP difference is that basis term, measured:

| year | weight-basis term | share of printed gap | model demand | measured load |
|---|--:|--:|--:|--:|
| 2023 | +0.804 | **37.9 %** | 207.4 TWh | 218.2 TWh |
| 2024 | +0.493 | **11.5 %** | 212.2 TWh | 223.5 TWh |
| 2025 | +0.788 | **20.0 %** | 205.6 TWh | 224.0 TWh |

The model dispatches grid-delivered load; `rt_lw`'s weights are measured system
load, 5–8 % larger. **Nothing here proposes changing the rubric, and the
printed C3a stands exactly as scored** — the certified statistic is the
certified statistic, and a residual is not smaller because a different
weighting would report it smaller. It is filed as an owner ask (§7.4),
alongside caiso-244 §4.5's D-2 class-total basis question, because it is a
like-for-like question about the scorer and not about the model.

### §4.6 — What the price-match test cannot do

`mc = λ` is a **necessary** condition for marginality, not a sufficient one, so
DOM_GAS / DOM_OTHER can OVER-identify (a unit at a bound whose offer coincides
with λ). Without a unit-level replay there is no better test, and the
sensitivity in §4.4 is the honest bound on how much the classification moves.
The HUB test does not share the weakness — it is a complementarity state from
the caiso-244 reconstruction, which passes G-RECON.

### §4.7 — CT_PEAKER's residual is NEGATIVE, and 2023's DOM_GAS is negative overall

In the hours CT_PEAKER price-matches, the model runs **−$7.79 (2023) / −$2.38
(2024) / −$1.63 (2025)** per MWh **BELOW** actual. 2023's whole DOM_GAS cell is
**−0.189**. This is the opposite sign to the annual gap and it means the
domestic surface is not uniformly hot: the CC family carries it (CC_REGULAR
+$2.63, CC_CHP +$4.30 per MWh in 2025) while the peaking family sits under the
actual. Any future "the gas surface is too high" arm has to survive that split.

---

## §5 — MONTH × REGIME, 2025 (gap $/MWh, cells sum to the month)

| month | total | HUB_F | HUB_M | DOM_GAS | biomass | STORAGE | UNRES |
|---|--:|--:|--:|--:|--:|--:|--:|
| Jan | −0.088 | −0.001 | −0.012 | −0.079 | +0.054 | −0.041 | −0.010 |
| Apr | +0.407 | 0.000 | +0.042 | +0.118 | +0.085 | +0.161 | +0.001 |
| May | +0.378 | 0.000 | +0.017 | +0.135 | +0.060 | +0.162 | +0.005 |
| Jun | +0.410 | 0.000 | +0.012 | +0.156 | +0.038 | +0.191 | +0.014 |
| Jul | +0.422 | 0.000 | +0.017 | +0.234 | +0.029 | +0.119 | +0.022 |
| Sep | +0.317 | −0.000 | +0.005 | +0.126 | +0.091 | +0.081 | +0.015 |
| **Dec** | **+0.711** | **+0.049** | +0.018 | **+0.355** | +0.061 | **+0.218** | +0.010 |

**December, the standing object, is now attributed**: 50 % DOM_GAS, 31 %
STORAGE, 9.4 % HUB — and it is the largest single month, consistent with
caiso-245 §3(a)'s "a level common to both regimes", now measured on the
residual rather than on the model price. **Apr–Jul (1.617) is bigger than
December (0.711)** and is DOM_GAS + STORAGE almost entirely (0.643 + 0.632
against HUB's 0.087).

---

## §6 — WHAT THIS DOES NOT DO

It arms nothing and changes no keeper. It does not touch items B / C / E / G,
the transport adder (D), the CT_PEAKER volume miss (F), the SoCalGas OFO arm,
the DOF-provenance instrument, or any other ISO's shard. It does not measure
**why** biomass is $8–10/MWh hot — that is the object it hands the next
session, not one it closes. It does not adjudicate the DOM_GAS/STORAGE split
(§4.4). It does not propose a rubric change (§4.5).

---

## §7 — WHAT THE QUEUE SHOULD LOOK LIKE NOW

1. **NEW, ranked first: the BIOMASS offer surface.** 18 % of the gap in both
   failing years, +$7.8–9.8/MWh mean residual, robust to both robustness
   variants, on **847 MW** of nameplate that has never been examined in this
   lane — a fleet small enough that its offer LEVEL, not its volume, is the
   whole mechanism.
   The next session should be a PHASE-0 on how those 184 units' offers are
   built (fuel cost basis, VOM, any `_DEFAULT_HR_MULT_BY_GROUP` fallback for a
   blank `plant_group`) before any arm is proposed.
2. **Items C and B are DEMOTED as C3a objects.** The import seam carries 4 %
   of the gap and the two fitted prices 1.6 %. Form (ii)'s OASIS re-fetch
   (caiso-245 §6) is still the right way to ground the north firm block's
   ENERGY basis as a structural matter under rule 1 — it is simply not where
   the scored residual lives, and it should not be funded as a C3a lever.
3. **The domestic gas surface (items E / F) stays live** but has to reckon with
   §4.7: CC is hot, CT is cold.
4. **Owner ask, new:** the C3a weight basis (§4.5).
5. Carried: caiso-246 §7 entire, caiso-245 §8, caiso-244 asks E/F, caiso-243
   §9 items 5–7.

---

## §8 — DO-NOT-REDO ADDS

1. **The hub-basis reading of the C3a residual is CLOSED for 2024 and 2025.**
   CR(HUB) ≤ 1.03 on all three variants; never re-propose the Palo Verde hub +
   adder chain, the import seam level, or the two fitted firm prices as the
   *carrier* of the C3a gap without new evidence that overturns this
   measurement. (They remain live as **structural** objects under rule 1.)
2. **Never quote the caiso-244 §3.6 hour share as a weight or gap share.**
   18–23 % of HOURS is 3.9–5.7 % of the load-weighted zone-hours and ~4 % of
   the gap (§4.1).
3. **Never quote this probe's DOM_GAS / STORAGE split as a result.** It is
   tolerance-dependent (§4.4); only their SUM (76 %) and the HUB and biomass
   cells are robust.
4. **Never quote the §4.5 weight-basis term as a reduction of C3a.** The
   printed gap stands as scored.
5. **caiso-202 §C's gap attribution is CONFIRMED, not superseded** — it was its
   marginal-HOUR count that caiso-244 repaired, not its ~5 % gap share.
6. caiso-246 §8, caiso-245 §7, caiso-244 §7, caiso-243 §10, caiso-242 §9,
   caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 stand in full.

---

## §9 — DELIVERABLES

`PRECOMMIT-caiso247-residual-regime-anatomy-2026-09-05.md` (`004c0d39`, pushed
first); `scripts/probes/_caiso247_residual_regime_anatomy.py` +
`results/calibration/_caiso247_residual_regime_anatomy.json`; this finding; the
calibration-log entry; the evidence-only appends to the CAISO matrix shard
(`import_hub_pricing`, `measured_offer_surface`) — **no cell verdict moves; no
mechanism was tested.** No run registered (zero solves). Keeper unchanged.

**Next number: caiso-248.**
