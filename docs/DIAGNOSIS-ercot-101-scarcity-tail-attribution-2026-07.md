# ERCOT-101 — the 2023–2025 scarcity-tail residual is an attributed measured-input bound, not a fixable miss

**Session 2026-07-24. Keeper: `2026-07-23-ercot100-netrev-margin-keeper`
(NOT-YET, C6 unattested). Successor to ERCOT-100 (net-revenue-margin offer form
promoted to keeper).** This lane closes the measurable 2024 tail question,
attributes the 2023/2025 RT-conduct residual with the honest bound, and tees up
the C6 governance attestation. It changes NO solve input — every number is from
the committed keeper sidecars + committed measured corpora (all no-LP).

Probes (all no-LP): `scripts/probes/ercot101_price_decomp.py` (exact scorer-basis
band decomposition), `ercot101_sced_wall_quantiles.py` (extended SCED-wall
quantiles), + the re-baselined ERCOT-99 toolkit
(`ercot99_{model_offer_curve,reach_gap,intrahour_bound}`) run on the MARGIN keeper.

## 0. The reframe (confirmed)

The failing gates decompose into ONE physical residual per year:

| gate | 2023 | 2024 | 2025 | what fails |
|------|------|------|------|-----------|
| C3a mean LMP | **−27.1% FAIL** | −8.5% PASS | −8.3% PASS | 2023 only |
| C3b shape NRMSE | **0.531 FAIL** | 0.142 PASS | 0.106 PASS | 2023 only |
| C3c tail count | **70/181 FAIL** | **12/53 FAIL** | **0/31 FAIL** | all three |

So the load-bearing 2023 C3a/C3b failure and the 2023 C3c failure are the SAME
residual (the >$300 tail, §1); 2024/2025 fail ONLY the supporting C3c tail-count
gate (their means/shapes pass). Every other gate (C1 16/16, C2, C4, C5a, C7, C8)
PASSES.

## 1. Lane B — 2023 C3a/C3b/C3c is one residual: the >$300 tail

Exact load-weighted band decomposition on the scorer's own basis
(`ercot101_price_decomp` — model zonal LP dual demand-weighted over zones+hours vs
the zonal settlement-LZ actual on the same measured demand weights; reproduces the
official C3a −27.1% / rt_lw $64.12):

| actual band $/MWh | hrs | actual mean | model mean | contrib to gap | % of −$17.6/MWh gap |
|---|---|---|---|---|---|
| [0,30) | 6150 | 19.3 | 24.7 | +3.61 | **−20.5%** (model over-predicts cheap) |
| [30,80) | 1948 | 44.7 | 40.1 | −1.13 | 6.4% |
| [80,200) | 344 | 116.6 | 70.3 | −2.24 | 12.8% |
| [200,300) | 42 | 249.1 | 99.7 | −0.91 | 5.2% |
| **[300,1000)** | 85 | 567.1 | 211.8 | −4.89 | **27.9%** |
| **[1000,∞)** | 62 | 2373.9 | 1244.7 | −12.19 | **69.4%** |

**97% of the mean-price gap is the >$300 tail** (27.9 + 69.4). The mid-merit
[80,200) under-prediction (12.8%) is almost exactly offset by the cheap-band
[0,30) OVER-prediction (−20.5%), so net of the tail the model's mean is right —
the entire load-bearing miss lives above $300. C3b (monthly NRMSE) is the monthly
image of the same tail (the Aug/Sep heat-wave months).

**It is hub-level scarcity, not congestion.** At the >$200 actual hours the
load-zone actual sits only +$15 (p50) / +$28 (mean) above HB_HUBAVG — the tail is
a system-wide scarcity price, not a zonal-congestion artifact a reduced network
misses.

**Why it is unfixable with measured constructions** (`ercot99_model_offer_curve`,
re-baselined on the margin keeper): at the Aug missed hours the model clears
$93–184 with only a ~480 MW cheap cushion below $200, while actual RT is
$318–2100. The marginal is ST_GAS/CT_PEAKER — units that offered ~$25–130 in the
measured DAM/merit basis but **re-offered $500–5000 in real time**. The only 2023
offer corpus on disk is the DAM disclosure, whose energy offers are measured-cheap
(wall p50 $327; the model tail already forms $211–1244 in the >$300 bands, i.e.
ABOVE the DAM wall). **No 2023 SCED/RT re-offer disclosure exists.** The residual
is real-time re-offer conduct beyond the measurable merit — rule 13 forbids a
residual adder, and there is no forward-reproducible measured input to close it.
Intra-hour reach ceiling: 123/181 (the rest are 15-min transients an hourly LP
smooths, `ercot99_intrahour_bound`).

## 2. Lane A — 2024 is cheap-up-to-p90: an attributed bound, not an offer-depth fix

The 2024 C3c miss is 12/53 (need ≥27). Two independent measurements resolve it to
an attributed bound.

**(a) The measured SCED wall is cheap up to p90.** `ercot101_sced_wall_quantiles`
re-reads the exact 60-Day SCED corpus the frozen ladder is built from
(tail_days + control_days), at extended quantiles. Top net-load bin, CC 2024:

| quantile | p50 | p90 | p95 | p97 | p99 | p99.9 |
|---|---|---|---|---|---|---|
| CC $/MWh | 41 | **115** | 150 | 397 | 435 | 8233 |

The frozen ladder caps at **p90** (LADDER_QUANTILES max = 0.9), where CC is $115 —
below the model's own repriced wall. Only the p95–p99 band is expensive, and it is
(i) **sample-day-selection-biased** (the corpus is tail-days, so its high
quantiles are scarcity-conditioned re-offers), and (ii) **VOLL-adjacent
scarcity re-offers** that are the ORDC settlement overlay's domain — putting them
in the energy merit double-counts the scarcity rent. Per the handoff's own Lane A3
criterion ("cheap up to p90 → attributed bound"), 2024 is an attributed bound.

**(b) The wall is repriced ABOVE the marginal (depth, not height), and 1/3 of
misses are unreachable.** `ercot99_model_offer_curve` on the margin keeper: the
surface reprices ~8 GW at the missed hours, but it sits above the model marginal
(~$70, with a 706 MW cushion to $200) — the binding constraint is the depth of
cheap supply below the wall, not the wall's height, so raising the p90 cap does
not make it marginal. `ercot99_reach_gap`: only ~10 of 45 missed hours sit in the
top net-load bin; **15 sit below p80** (moderate net load — transients / local
events a net-load-conditioned surface structurally cannot form). The actual 2024
tail is $1058, ORDC/conduct-set beyond any merit wall.

**Why not extend the ladder (rules 1/23).** The apply asserts `rt_q == ladder_q`
(offer_surfaces.py:1169), so extending RT quantiles forces re-deriving the DAM
cleared-share wall too — coupling the load-bearing 2023 year into the change. The
extension is residual-motivated (rule 23 freezes the derive against residuals),
rests on sample-day-biased quantiles, and blurs the merit/ORDC boundary (rule 1:
a number reached through an unreal mechanism is not a win). Congestion at the 2024
tail is small (LZ−hub +$7 p50 / +$18 mean).

## 3. Lane C — 2025 is RT-only scarcity the DA/SCED-merit basis cannot form

2025 C3c is fully collapsed (0/31, need ≥16). `ercot99_reach_gap`: model clears
p50 $72 / max $141, catches 0. DA energy merit is cheap at the tail hours (DA p50
$91). The SCED wall is the same shape (cheap to p90, VOLL-adjacent above). The
largest LZ−hub congestion of the three years sits here (+$17 p50 / **+$64 mean**) —
a settlement-point tail above system lambda that a copperplate/reduced-network LP
structurally cannot form (a network-representation bound, distinct from offer
depth; the reduced-network split is its own charter). Same attributed family as
2023/2024. NB the margin form moved 2025 C3a −6.1→−8.3% and C3b 0.091→0.106 (still
PASS) — a 2025 RT-ladder re-derive would risk tripping C3a past −10%, another
reason not to pursue it.

## 4. Determination — the honest route off NOT-YET is CALIBRATED-WITH-CAVEATS

No measured construction closes the tail: 2023 has no RT offer source; 2024's
measured wall is cheap up to p90 and its expensive tail is biased/ORDC-domain;
2025 is RT-only scarcity + congestion. Forcing C3c to PASS would require a
residual-tuned adder (rule 13), a ladder-quantile extension motivated by the
residual (rules 1/23), or cross-applying the 2024/25 RT ladder to 2023 (no source)
— all pre-registered FORBIDDEN. Per rule 1, the tail stays attributed, not tuned.

The realistic route is CALIBRATED-WITH-CAVEATS via the C6 governance attestation +
an exceptions ledger reclassifying the three price gates as **accepted
measured-input limitations**. The draft (§5) is proven to score
CALIBRATED-WITH-CAVEATS (8 gates PASS, C3a/C3b/C3c ledgered 3/3 within budget, C6
PASS) — pending OWNER sign-off (governance is not self-attested).

## 5. Draft exceptions ledger (per-caveat, for owner review)

Five entries collapsing to three ledgered criteria (within the ledger budget of
3). Full text in `results/calibration/ercot_netrev_margin/calibration_attestation.json`
once signed; the draft lives in `docs/handoffs/ercot-101-governance-attestation-draft-2026-07.md`.

* **C3a / price_mean / 2023** — 97% of the mean gap is the >$300 tail (§1); RT
  re-offer conduct beyond the DAM disclosure; no 2023 SCED source; rule 13 forbids
  tuning.
* **C3b / price_shape / 2023** — monthly image of the same 2023 tail; same root.
* **C3c / price_tail / 2023** — 70/181 within the 123/181 intra-hour ceiling;
  hub scarcity (congestion +$15); unmeasured 2023 RT wall.
* **C3c / price_tail / 2024** — measured SCED wall cheap up to p90; p95–p99
  biased/ORDC-domain; wall above the marginal (depth); 1/3 of misses moderate-net-load.
* **C3c / price_tail / 2025** — RT-only scarcity; DA merit cheap ($91); largest
  congestion (+$64) above system lambda a reduced network cannot form.

## 6. What stays for a future lane (NOT this session)

* The West/Panhandle topology split (named lever, own charter) — the reduced-network
  congestion bound surfaced in 2025 (§3).
* Real-time re-offer conduct is unmeasured for 2023 and structurally absent from a
  perfect-foresight hourly LP; only a forward re-offer model (not a backcast
  overlay) could form it, and no such source exists.
