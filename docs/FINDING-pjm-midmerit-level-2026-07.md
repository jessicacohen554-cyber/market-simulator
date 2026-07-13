# FINDING — PJM G-22 lever C: the mid-merit level split — CT fast-start offers ARE under-priced, coal offers are NOT (and the net-virtual clamp carries a structural phantom)

**Date:** 2026-07-13. **Session:** G-22 lever C (mid-merit offer LEVEL — fix
the C1 coal/peaker overshoot that blocks the net-virtual-depth run from
becoming a keeper). **Baseline pair:** `2026-07-11-pjm-98-cc-mustrun`
(keeper) and `2026-07-12-pjm-102b-net-only` (net DA-virtual depth, no
surfaces; re-solved this session as
`results/calibration/pjm102b_net_only_rebuild`, a rule-16 throwaway, for the
hourly decomposition below). **Candidate:** pjm-103 (§4).

## 1. What exactly blocks the keeper (sharper than the §6 prose of the DA-depth finding)

Scored per-criterion (calibration_verdict, rubric v2.4), net-only's failures
are much narrower than "C1 overshoot":

- **C1 FAIL is 2023-only**: CT_PEAKER +8.57 TWh and COAL_BIT +9.55 TWh vs the
  ±8.0 TWh band (out by 0.57 / 1.55). **2024 is already fully in-band**
  (CT +5.0, BIT +7.3, CC +2.2). 2025 classes are SKIPPED (preliminary
  EIA-923 vintage).
- **C2 FAIL 2025 coal +9.9%** vs the keeper's own pre-existing +5.8% FAIL —
  the virtual layer adds ~+4 pp; de-regression needs ≈ −5.6 TWh of 2025
  coal-family energy.
- C3a / C3b / C4 / C5a / C7 / C8 all PASS on net-only (the G-22 price target
  is met by the measured depth alone).

## 2. The demand side is not neutral: the net-DEC clamp carries 10–17 TWh/yr of one-sided phantom energy

The committed net form (`net(λ) = Σ DEC≥λ − Σ INC≤λ`, net-negative tail
**clamped to zero**) never injects supply — but it also never nets out. At
the ACTUAL DA prices, the measured curves clear:

| year | clamped net (TWh) | unclamped net (TWh) |
|---|---|---|
| 2023 | +10.3 | −0.6 |
| 2024 | +14.8 | −0.9 |
| 2025 | +17.2 | +1.3 |

The real DA virtual position nets to ≈ ZERO over a year; the clamp keeps
only the DEC-dominated half, so **even a perfectly-priced stack must
physically over-generate by ~10–17 TWh/yr** against the RT-physical C1/C2
benchmarks. The model's own cleared DEC energy is 13.9/17.5/21.1 TWh — the
offer-level lever can address only the **+3.6/+2.7/+3.9 TWh over-clearing
vs the actual-DA equilibrium**, not the clamp's structural floor. 2024
demonstrates the floor can pass C1 when its class incidence spreads; 2023
misses by 0.6/1.6 TWh. (Mechanism-design follow-up filed in §6 — NOT
re-litigated here.)

## 3. Where the over-clearing lives, and what the measured offer corpus says about each class

Hourly decomposition of the 2023 rebuild (model-cleared DEC minus the
actual-DA-equilibrium clearing, by hour-of-day):

- **The excess is an EVENING-PEAK phenomenon: hours 16–20 carry +3.06 of the
  +3.60 TWh**, where the model dual is $32–34 vs actual DA $38–43.
- Overnight (hours 0–5) the model *under*-clears (−1.0 TWh): model troughs
  ($27–28) already sit ABOVE the actual DA ($19–22). There is no
  cheap-trough problem to fix — raising trough offers would move AWAY from
  the actual price duration curve.
- By dual band, the excess concentrates at $25–40 (+3.4 TWh) — the
  evening-shoulder margin.

Against the measured mid-curve surface (`pjm_offer_midcurve_condbinned.json`,
36 months of DataMiner2 submitted offers, within-unit share ladders,
implied-HR-mult × delivered-gas-day normalization):

- **LONG_RUN (coal / gas-steam, 216 units): the model's bituminous offers are
  AT or ABOVE the measured level in every year.** Measured bin-0 body
  (share 0.05→0.95 × mean bin gas): ≈ $25→$34.5 (2023), $22→$31 (2024),
  $22→$36 (2025). Model BIT econ band (band mults 0.6556→1.2664 × F923
  delivered coal $3.08/3.03/2.94 × sigmoid ff ≈ 0.94/0.83/1.23 + VOM 4.5):
  ≈ $26→$42 (2023), $23→$38 (2024), $32→$54 (2025). The implied flat
  passthrough that would land the model ON the measured level is
  ≈ 0.74/0.66/0.79 — *below* the keeper's fitted curve, nearly flat in gas.
  **A coal offer RAISE is therefore refuted by the measured submitted
  offers** (rules 1/13/14): the 2023 BIT +9.55 and 2025 coal C2 residuals
  are not an offer-level defect — they are the §2 phantom demand landing on
  a measured-consistently-priced class (plus whatever real self-scheduling /
  availability structure the model still misses). Both the keeper's fitted
  `coal_bit_passthrough_floor=0.65` override and a MISO-style
  `coal_econ_srmc_bound` clamp are *equally* unsupported by the measured
  level — neither is armed. (The archived first-principles docs already
  called the 0.65 floor "the ungrounded knob"; re-anchoring the sigmoid to
  this corpus — which would LOWER coal offers — is follow-up root-cause
  work, not a lever against this residual.)
- **CT_FAST (fast-start CTs, 1,064 units): the model IS under-priced, by
  ~2×.** Measured fast-start offers run ~18–38 × the delivered-gas day
  (≈ $50–100/MWh at typical gas); the model's CT_PEAKER econ band is
  1.05–1.27 × HR 11.7 ≈ 12.3–14.9 implied-HR mults. The gap is the
  fuel-price-INVARIANT start/no-load recovery component (the exact
  NEISO/NYISO/MISO finding — "the bare marginal HR is the COST, not the
  OFFER"), which an HR multiplier cannot express and which the pjm-101/102
  HR-multiplier surfaces over-expressed (CT −12 TWh crush, C3a +12%).

## 4. The pjm-103 candidate (one lever, measured, existing mechanism)

`scripts/probes/_pjm103_midmerit_level_probe.py` — pjm-98 keeper recipe +
the committed net DA-virtual form +:

- `tranche_startup_amortization=True` — CT_PEAKER/CT_CHP econ+peak tranches
  (and CC duct peak) carry the cited NREL start cost (constants
  `CT_STARTUP_PARAMS`, NREL/SR-5500-55433) amortized into the P1 bid.
- `tranche_startup_measured_runs=True` — amortization horizon = the plant's
  CAMPD-measured median start-to-stop run
  (`campd_ct_run_lengths_PJM.csv`, derived this session by
  `scripts/derive_campd_ct_run_lengths.py --iso PJM`; rule-13 measured
  market-behaviour parameter, re-derives only on CAMPD updates).
- `tranche_startup_conditional_runs=True` — the v4 condition-keyed horizon
  (`campd_ct_run_bands_PJM.csv`, same derive `--condition-bands`): tight-hour
  engagements are measured shorter commitment blocks, so start recovery in
  the evening-peak hours (exactly the §3 excess window) amortizes over fewer
  hours.

Zero fitted scalars; every input is a published cost table or a
CAMPD-measured statistic; coal untouched; the pjm-99/101 surfaces stay off.

## 5. pjm-103 results (`2026-07-13-pjm-103-ct-faststart`)

The CT leg does exactly what the measured basis predicted — and exposes the
coal top as the remaining gap. Per-class TWh (pjm-103 | net-only | actual):

| year | CT_PEAKER | COAL_BIT | CC_REGULAR | cleared DEC |
|---|---|---|---|---|
| 2023 | **23.01** \| 30.23 \| 21.66 | 113.87 \| 112.57 \| 103.03 | 323.2 \| 320.0 \| 325.7 | 13.2 \| 13.9 |
| 2024 | **21.30** \| 29.03 \| 24.02 | 113.80 \| 112.44 \| 105.10 | 340.6 \| 337.4 \| 335.1 | 16.4 \| 17.5 |
| 2025 | **33.90** \| 41.52 \| 23.82 | 137.66 \| 136.46 \| 125.43 | 331.9 \| 328.9 \| 330.4 | 20.0 \| 21.1 |

- **CT_PEAKER is fixed in every gated year** (2023 +1.35, 2024 −2.72 —
  in-band; 2025 +10.1 down from +17.7) with **no crush** (the pjm-101/102
  surfaces put 2023 CT at −10.9): the fuel-invariant start/no-load
  amortization is the right instrument and the right size.
- **C3a stays PASS and tightens** (2023 +4.5%, 2024 −0.6%, 2025 −6.7%
  MW-weighted vs actual DA); C3b 2023 tips to a marginal FAIL (NRMSE 0.202)
  — re-scored at pjm-104.
- **The substitution effect moves COAL_BIT further out** (2023 +10.85,
  2024 +8.71 vs ±8.0; C2 2025 coal +12.3% on the EIA-930 family basis):
  the retreating CTs hand the evening DEC demand to coal — only ~1 TWh/yr
  of the phantom uncleared; the rest re-routed to coal/CC. C1 now fails on
  COAL_BIT alone.

The coal body is measured-consistent (§3), but the model's coal TOP is not
measured at all: the within-plant peak tranche (~top 15% of each coal plant,
priced 1.044 × base HR ≈ $35) lives exactly in the 0.95–1.0 share belt the
decile-sampled surface never measured — and the pjm-99/A' findings place the
real $35–83+ price formation in that belt. pjm-104 measures it and floors
coal/steam (LONG_RUN) rows only:

- `derive_pjm_offer_midcurve.py` share grid extended with 0.975/0.995 (the
  s05–s95 medians reproduce identically; re-derived from the refetched
  36-month corpus).
- `ScenarioConfig.pjm_offer_midcurve_segments=("LONG_RUN",)` — a rule-19
  scope so the floor prices ONLY coal/gas-steam econ+peak rows; CT_FAST
  stays owned by the startup amortization (the pjm-101/102 CT
  double-pricing cannot recur), CC_LIKE by the keeper curve.

## 5b. pjm-104 results (`2026-07-13-pjm-104-coal-top`) — 2023 closes fully; the phantom re-routes to CC in 2024; the lever is exhausted

The extended surface settles the "wall" question first: **there is no coal
wall.** LONG_RUN tops out at s0.995 ≈ 10.2–11.6 × the bin's gas
(≈ $36 in 2023, $37 in 2025) — at/below the model's coal peak in every
year. What the scoped floor DOES lift is the lower/mid econ belt (+$1–2 in
2023/24), and that is enough to re-price coal out of the trough/shoulder
DEC service:

| year | CT_PEAKER | COAL_BIT | CC_REGULAR | ST_GAS | coal fam | cleared DEC | LMP (model \| DA) |
|---|---|---|---|---|---|---|---|
| 2023 | +3.45 ✓ | **+1.85 ✓** | +2.27 ✓ | +0.30 ✓ | +1.5% | 12.4 | 31.26 \| 29.33 |
| 2024 | −1.44 ✓ | **+2.60 ✓** | **+9.07 ✗** | −3.60 ✓ | +2.1% | 16.0 | 30.00 \| 29.79 |
| 2025 | (+10.59) | (+9.79) | (+3.10) | (−0.76) | +8.0% | 19.8 | 40.99 \| 43.71 |

(deltas vs actual, ✓ = inside the ±8 TWh C1 band; 2025 ungated.)

Verdict (calibration_verdict, registered): **2023 C1 ALL-PASS, C3b returns
to PASS, C3a PASS (2024 mean within 0.2%), C4/C5a/C8 PASS** — and two new
misses: **C1 2024 CC_REGULAR +9.07** and **C7 2023 CT_PEAKER diurnal shape**
(profile r 0.88, off-peak CV ratio 0.495 — the repriced CTs run flatter
off-peak than actual, the economic layer suppressed onto the reliability
floors). C2 2025 coal improves to +10.2% (keeper +5.8%).

**Determination: the mid-merit offer LEVEL is exhausted as an instrument —
and it worked.** Three iterations (net-only → pjm-103 → pjm-104) each
re-priced a class onto its measured basis and each moved the C1 miss to the
next-cheapest class: CT+coal (net-only) → coal (pjm-103) → CC (pjm-104).
Every mid-merit class now sits on a measured or cited basis (CT: NREL start
cost over CAMPD horizons; coal: measured offer-surface floor over F923
delivered cost; CC: the keeper curve, whose measured CC_LIKE s85–s95 belt
is the one remaining unmeasured top), and the model's cleared DEC energy is
within ~1 TWh/yr of the actual-DA-price equilibrium — i.e. the clearing is
now price-consistent. What remains is §2's arithmetic: the clamp's
one-sided ~10–17 TWh/yr must land on some class, and 2024's 15–16 TWh
cannot fit inside every ±8 TWh band simultaneously once no class is
mispriced enough to absorb it. **The C1 blocker is the mechanism form
(clamp), not the offer level.** Fixing it by further offer raises would
push classes above their measured offer levels — rule 1 forbids reaching
the number through a mechanism that isn't real.

Keeper recommendation: **stays pjm-98.** The session's two structural
pieces — the CT fast-start amortization (v3/v4, PJM artifacts) and the
LONG_RUN-scoped measured mid-curve floor — are keeper-line structure
(measured, forward-native, zero fitted scalars) and should ride along with
whatever resolution the owner picks for the clamp (§6.1), which is the
actual gate to a net-virtual keeper.

## 6. Follow-ups filed (root causes, not levers — §5b order of importance)

1. **The net-virtual clamp's one-sided phantom (§2).** The measured annual
   net position is ≈ 0; the clamped form carries +10–17 TWh. Candidate
   design: symmetric net form — render the net-negative (INC-dominated)
   tail as bounded net-supply blocks so the annual net returns to ≈ 0 —
   would relieve C1/C2 class totals by construction, at the cost of
   re-opening the "financial positions in the physical mix" question the
   pjm-102 determination settled for the INC side. Needs its own
   adjudication + solve; NOT slipped into this session.
2. **PJM bituminous sigmoid re-derivation from the measured offer corpus**
   (would retire the fitted 0.65 floor / 1.32 ceil with measured flat-in-gas
   anchors ≈ 0.66–0.79 — and LOWER coal offers, so it must land together
   with the structure that actually prices the evening margin, or it will
   worsen the very residual G-22 tracks). Related open issue: #1347 (D-8
   weak identification of sigmoid anchors).
3. **The extreme-tail maxes** (actual $200–500 vs model $97–271) stay the DA
   reserve/ORDC + seam layer — untouched here, per the charter.
4. **C7 2023 CT_PEAKER off-peak shape** (new in pjm-104): with the CT
   economic layer correctly repriced, the class's off-peak profile flattens
   onto its reliability floors (CV ratio 0.495). The economic half is now
   right; the flat half points at the eastern CT floor windows / the missing
   real off-peak CT variability (reserve deployments, load-following) — a
   commitment/AS phenomenon, not an offer level.
5. **The measured CC_LIKE top belt** (s85–s95 ≈ 7.3–13.0 × gas vs the
   keeper's fitted econ_high 1.5 ≈ 9.6): the one mid-merit top still on a
   fitted basis. A CC_LIKE-scoped floor is the same construction as
   pjm-104's LONG_RUN scope — but under the clamp it would only push the
   2024 phantom to the next class; sequence it AFTER §6.1.
