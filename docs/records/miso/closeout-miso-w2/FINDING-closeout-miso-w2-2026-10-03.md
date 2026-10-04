# FINDING — closeout-MISO-w2: CC_REGULAR 2021 is the fall-2021 coal-conservation object; the L3/L4 retest on the nuclear-repaired keeper charters nothing (L4a clears its bars only through a merchant-scope violation). No PRECOMMIT, no solve; keeper unchanged.

```
LANE     : closeout-MISO-w2 (desk charter 2026-10-03, session_01ERkBTm23ZAP4CTZnJVD9Ss; plan §3.3)
KEEPER   : 2026-10-03-closeout-miso-nuc-r (results/calibration/closeout_miso_nuc_span), unchanged
LP       : none (sidecar reads, fleet-only rebuilds, the wave-1 bid-stack census)
BARS     : BARS-phase0-l3l4-retest-2026-10-03.md (cb1dfe00, committed and pushed before any new-keeper number)
PROBES   : scripts/probes/_closeout_miso_w2_cc2021_decomp.py   -> results/phase0/miso/_closeout_miso_w2_cc2021_decomp.json
           scripts/probes/_closeout_miso_w2_l3l4_retest.py     -> results/phase0/miso/_closeout_miso_w2_l3l4_retest.json
           scripts/probes/_closeout_miso_w2_l4a_scope_diag.py  -> results/phase0/miso/_closeout_miso_w2_l4a_scope_diag.json (post-hoc, labelled)
CELLS    : coal_econ_two_sided R, coal_prb_committed_split R, coal_prb_committed_dispatchable R (evidence added, verdicts unchanged)
```

## 0. Where MISO stands (keeper, rubric v3.20)

NOT-YET on four rows: C1 ST_GAS 2019 −8.71 TWh (routed, R-15), **C1 CC_REGULAR 2021 −8.15 TWh**, **C3a 2020 +10.2 %**
($24.21 vs $21.97), C3b 2021 0.219. C3c 2019/2021 carry ledgered model-class caveats; 2020 PASS.

Plan §3.3 queue at this lane's start:

| step | state |
|---|---|
| 0a `derive_actual_tail` | **DONE** (wave 1, 2026-10-02; C3c 2019/20/21 scored CAVEAT/PASS/CAVEAT and live in status) |
| 0b Max Gen registry | owner-gated (R-15 OATI PDF; R-17 "no owner downloads today", deferred) — no new ask |
| 1 L1 transport | CLOSED (miso-299) |
| 2 L3 + L4 census | killed by wave 1 on the miso-280 keeper; **retested here** (rule 28 new evidence: the R-43 nuclear repair moved both sides of the gate) |
| 3 full span | carries only what passes |

## 1. C1 CC_REGULAR 2021: decomposition (zero LP)

Keeper `class_hourly_2021` vs EIA-923 monthly (the benchmark's own `bench_multiclass.e923_class_monthly` chain,
gross, keeper class labels), and keeper vs the outgoing W0 keeper's sidecars (`d57c02e7:results/calibration/w0_miso_span`).
TWh, model − EIA-923:

| month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CC_REGULAR | +0.11 | −0.71 | +0.55 | +1.11 | +1.00 | +0.45 | **+2.26** | **+2.06** | **−2.72** | **−3.32** | **−2.89** | **−1.49** |
| COAL_PRB | −0.00 | +0.26 | −0.35 | +0.04 | +0.29 | +0.85 | **−2.05** | **−2.31** | **+1.62** | **+2.87** | **+2.40** | **+1.67** |
| COAL_BIT | −0.45 | −0.10 | −0.15 | +0.10 | −0.15 | +0.19 | −0.99 | −1.23 | +0.27 | +0.80 | +0.54 | +0.02 |
| nuclear (keeper − W0) | +0.13 | +0.04 | +0.15 | −0.18 | +0.61 | +0.30 | −0.62 | +0.13 | +0.08 | −0.00 | **+1.07** | **+1.18** |
| CC_REGULAR (keeper − W0) | −0.06 | −0.02 | −0.07 | +0.02 | −0.20 | −0.13 | +0.36 | −0.04 | +0.01 | +0.02 | **−0.67** | **−0.55** |

Reading:
- **Sep–Dec carries the miss.** CC_REGULAR is −10.4 TWh under while coal is +10.4 TWh over (PRB +8.6, BIT +1.6). This is the
  fall-2021 coal conservation (IMM: reference-level adders on 18 → 8 GW of coal), the same object that carries 60 % of
  the C3b 2021 SSE (RESULT-miso294 Part B).
- **Jul–Aug is its mirror.** CC is +4.3 over and coal −6.6 under where the pooled B/12 budget limb binds (wave 1 §R-3:
  removing B/12 releases +8.9 TWh of summer coal).
- **The nuclear repair** (R-43, rule 14) moved CC_REGULAR by −1.32 TWh, 92 % of it in Nov–Dec, where nuclear rose +2.25 TWh.
  Out-of-merit fall coal masked the nuclear over-statement there; with measured nuclear, the conservation residual
  surfaces in C1.
- The C1 row (scorer basis, −8.15) and this class-label basis (−3.6) differ by benchmark membership and grid-delivered
  netting. The monthly shape is the evidence, not the level.

**Route.** Every admissible lever on this object is adjudicated:
- the R-3 receipts + stock take ceiling (wave 1: K1 binds the fall; K2/K3 fail because, under rule 19, it can only
  replace B/12 by releasing summer and 2022 coal);
- the cumulative pile family `coal_fuel_inventory_monthly_pile` / `_take_floor` (R, miso-289/290);
- per-year transport and the gas form (R, miso-298/299/300).

Nothing new is admissible here. CC_REGULAR 2021 belongs on the same ledger row as the fall share of C3b 2021: *fall-2021
coal conservation*. It is not a separate lever.

## 2. C3a 2020: the L3/L4 census retest

Same census code as wave 1 (`_closeout_miso_l3l4_census.py`, unchanged), re-pointed at the new keeper by a wrapper.
Keeper reproduction exact (static KEEPER arm ΔP 0 in every year). Bars B1–B4 as committed in cb1dfe00:
- **B1** 2020 static q1–q4 **and** all-hours ΔP ≤ −$0.13. This is the plan gate's 2.9× margin applied to the new need of
  −$0.043.
- **B2** every coal C1 row 2019–25 stays in ±8 TWh after the 0.27 LP conversion.
- **B3** C3a stays within ±10 % in every other year.
- **B4** CC_REGULAR 2021 is not below −8.65 TWh.

| arm | 2020 ΔP q1–q4 / all | B1 | B2 | B3 | B4 CC_REG 2021 |
|---|---:|---|---|---|---:|
| L3 (registered two-sided) | −1.16 / −1.51 | pass | **FAIL** PRB 2019 +8.45, 2021 +8.05 | **FAIL** 2021 −12.1 % | **−13.25 FAIL** |
| L3flag | −1.24 / −1.61 | pass | **FAIL** PRB 2019 +8.93, 2021 +8.50 | **FAIL** 2021 −12.4 % | **−13.65 FAIL** |
| L4a | −0.195 / −0.193 | pass | pass | pass | −8.58 pass |
| L4b | +0.91 / +0.72 | **FAIL** | pass | pass | −7.36 pass |
| L3+L4a | −1.31 / −1.66 | pass | **FAIL** PRB 2019 +9.13, 2021 +8.58 | **FAIL** 2021 −12.4 % | **−13.73 FAIL** |
| L3+L4b | −0.26 / −0.75 | pass | pass | **FAIL** 2021 −11.5 % | **−12.12 FAIL** |
| L3stack (rule 19, record only) | −0.39 / −0.54 | — | pass | pass | **−9.84 FAIL** |

The registered L3 form still fails on the new baseline. The nuclear repair lowered PRB 2019 headroom only partly
(+4.56 vs +6.40), and the arm's own gas displacement now drives CC_REGULAR 2021 and C3a 2021 out.

### 2.1 L4a clears the bars numerically, but not on structure

L4a, as the wave-1 census constructs it, splits each coal committed band at the plant's measured night p50:
- The **hold** slice keeps the keeper's committed offer.
- The **cycling** slice bids VOM + incremental HR × spot share × delivered fuel. The spot share is 1 − EIA-923 Page 5
  contract share, so the slice carries the sunk-fuel discount.

Two defects:

1. **Merchant scope.** The keeper's committed-band take-or-pay discount is `coal_committed_takeorpay_regulated` (K).
   It applies only to EIA-860 rate-regulated plants, because MISO SOM Table 7 shows merchants offering economically
   (74–93 %). L4a applies the spot-share discount to every split plant, including about 1 GW of merchant PRB committed
   band (cycling 7.30 GW PRB, of which 6.31 GW is regulated). That reverses an adjudicated conduct scope on one slice:
   rule 19, and rule 1's non-selective clause.
2. **Not a cycling representation.** The "cycling" slice bids below its own hold slice (PRB cap-weighted $6.45 vs the
   keeper's committed $8.75). The LP therefore never cycles it ahead of the hold. Coal's low-load marginal share barely
   moves (2020 q1–q4: 0.188 → 0.191, against the IMM's 0.40; 2021 falls 0.411 → 0.393). It does not move toward the
   IMM share, which is the plan's own diagnosis of the miss: the price falls because cheaper coal energy shifts the
   whole stack (q5 −$0.19), not because coal enters the low-load margin.

**Post-hoc diagnostic** (labelled; not a candidate arm, no bar applied): `_closeout_miso_w2_l4a_scope_diag.py` keeps
L4a's slice bid on regulated plants only, and gives merchant slices full delivered fuel at incremental HR.

| year | L4a ΔP all-hours | L4a regulated-only | regulated-only, avg HR (split construction alone) |
|---|---:|---:|---:|
| 2019 | −0.178 | +0.013 | +0.088 |
| 2020 | **−0.193** | **+0.013** | +0.074 |
| 2021 | −0.121 | +0.041 | +0.069 |
| 2023 | −0.201 | −0.137 | −0.077 |

In 2019–2021, **all** of L4a's price reach comes from the merchant discount extension. The regulated-scope kernel
moves 2020 the wrong way (+$0.013). **L4a: NOT CHARTERED.**

## 3. The rest of the queue

| lever | reading | state |
|---|---|---|
| L5 PTC-vintage wind offers / negative renewable offers | The MISO wind column already bids flat −PTC (`compute_dispatch_credits`), yet the keeper has **0.0 %** of 2020 hours below $10 (actual 2.8 %; miso-296 §2), so wind is never marginal at zonal grain; the West/Plains congestion that would make it marginal is G (`internal_congestion_split`). `wind_ptc_vintage_offers` can only raise the wind offer (expired vintages bid ~$0): wrong sign. `negative_renewable_offers` at $20 is CAISO-scoped (rule 25). | not chartered (sign / rule 25); cells stay `·` |
| L6 VLR pocket | blocked on a published MW | G |
| 0b Max Gen registry | owner download deferred (R-17) | waits |
| 3 full span | nothing passed, so a span would be the keeper recipe | not run (rule 29: no control solves) |

**The plan §3.3 queue is exhausted for C3a 2020 and C1 CC_REGULAR 2021.** No PRECOMMIT and no shard. The keeper is
unchanged.

## 4. What the desk can take to the owner

MISO's four open rows now fall into three structural objects. Each has its admissible levers adjudicated:

| row | object | why no lever |
|---|---|---|
| C1 ST_GAS 2019 −8.71 | MISO-South VLR out-of-merit steam | pocket limit unpublished (G); routed R-15 |
| C1 CC_REGULAR 2021 −8.15 and C3b 2021 0.219 (fall share) | fall-2021 coal conservation (+ Feb Uri on C3b, routed) | R-3 ceiling fails K2/K3 (wave 1); pile family R |
| C3a 2020 +10.2 % (0.2 pt over) | low-load level shift; ~4.4 pts West/Plains congestion | congestion split G; every coal-offer arm fails structure or bars (§2) |

A ruling is needed to move MISO further:
- sign these as model-class frontier rows (the miso-281 ruling keeps "routed" ≠ PASS); or
- admit an object this lane cannot: a published VLR pocket limit (L6), RO-1 for the congestion split, or a measured
  stock path beyond R-3's non-cumulative form.
