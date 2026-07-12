# DIAGNOSIS — ERCOT binding-regime price formation: the trough side (ERCOT-62, 2026-07-12)

**Task (the ERCOT-61 §5 hand-back, this session).** Close the binding-hour
storage/price-formation circle endogenously: flat modelled evening/morning
spread ↔ battery under-discharge at binding hours ↔ thermal (ST_GAS) over-serve
(ERCOT-58 §4 → ERCOT-60 §7.3 → ERCOT-61 §6). Candidate levers, in the filed
order: (1) DA-commitment thinness (`gas_st_commitment_ceiling`, the ERCOT-61 §4
recorded derive basis); (2) the G-22 DA-shoulder conditional-offer-distribution
lane.

**Answer in one line: lever 1 FAILS identification (a second rule-13 dead end,
recorded below); the circle's real defect is measured to be on the TROUGH side
of the daily price curve — the model prices its price floors ~$5–7 above the
real market at overnight/midday hours in every month — and the admissible
closing mechanism is the conditional-offer-distribution lane's LOW leg
(`ercot_offer_surface_lowcurve`), the exact mirror of the adopted top-of-curve
surface, built this session.**

Probes (rule-16 2023-only throwaways, NEVER registered):
`scripts/probes/_ercot62_lowcurve_probe.py` (keeper + the low leg as single
delta) vs the zero-delta keeper reconstruction (byte-faithful: C3a +3.9 %, C3b
0.133, C3c 171 h reproduce the keeper exactly). A/B analysis:
`scripts/probes/_ercot62_lowcurve_analyze.py`.

## 1. Lever 1 — the ST_GAS commitment ceiling fails identification (rule-13 dead end)

The ERCOT-61 §4 recorded operating rule was reproduced exactly from unit-level
CAMPD (steam-units-only basis incl. the Parish/Davis split units; committed
capability = online units × month-conditional p95; rating = annual p98 of run
hours): 2023 hourly r = 0.806, fit `frac = 0.0179·nl_GW − 0.310`, deciles
0.039 → 0.767, binding-hour committed capability 5,897 MW vs measured gross
4,006 MW (the corrected ERCOT-58 §4 basis). The rule is real *within 2023*.
It does not survive the admissibility tests:

* **Not year-stable on any tested axis.** At fixed absolute net-load the
  committed fraction differs up to ~30× across years at the low end (nl
  16–20 GW: 2023 0.005–0.04 vs 2025 0.176–0.19) and *crosses* around ~38 GW
  (2023 above 2025 at high nl: 0.61 vs 0.44 at 44–48 GW). Same failure on the
  within-year rank axis, the year-max-normalized axis, and the daily-peak
  net-load axis (commitment-for-the-peak physics; 52–60 GW day-peak day
  frac: 2023 0.696 / 2024 0.585 / 2025 0.451). The 2025 posture is flatter
  everywhere — consistent with 13.7 GW of batteries serving the peaks and a
  higher-gas year, i.e. a year-level *economic* posture component no
  net-load-family driver carries. Rule 12's driver requirement fails.
* **A frozen pooled curve manufactures phantom tightness.** Applied to the
  keeper's own 2023 hourly dispatch, the pooled absolute curve clips
  5.5 TWh (4.8 TWh in binding hours) — versus 0.56 TWh for the (inadmissible)
  honest own-year envelope — because pooling smears 2024/25's flat posture
  onto 2023. That is the ercot57 phantom-scarcity failure class re-created by
  a mis-specified driver: NOT built.
* **The hourly measured commitment state is inadmissible outright.** The repo
  has already adjudicated the category: "commitment state is not an
  availability event" (`derive_ercot_thermal_dam_availability.py`, the
  ercot57 intake — OFF-but-startable units count as available). It has no
  forward analogue, it double-governs the phenomenon the P0/P1 passes +
  startup costs + drag floor already model (rule 19), and it would replay the
  exact posture whose error is the residual under investigation — the
  dispatch being validated would no longer be the dispatch being forecast.
* **It is not the carrier anyway.** Even the inadmissible hourly envelope
  binds the keeper's 2023 dispatch for only 0.46 TWh at binding hours
  (~18 % of the ~2.6 TWh binding excess), evening-peaked but small —
  confirming ERCOT-61 §4's "NOT the excess's carrier".

**Determination: rule-13 dead end, the mirror of ERCOT-60's morning-discharge
dead end.** No admissible measured input exists for a ST_GAS commitment
ceiling; the year-level posture economics must close endogenously or not at
all. The `gas_st_commitment_ceiling` is struck from the lever list.

## 2. The measured re-scoping: the missing spread is at the BOTTOM of the day

Model (keeper reconstruction) vs measured HB_HUBAVG, 2023, load-weighted
hourly system price:

* **Median daily top4−bottom4 spread: model $13.5 vs RT $35.3 / DA $34.3.**
  Days with spread > $24.25 (≈ the battery round-trip hurdle: $10 adder +
  $14.25 derived cycling cost): model 81 vs RT 247. This is the measured form
  of "the binding constraint is the flat modelled spread" (ERCOT-60 §7.2).
* **The gap is in the troughs, not the peaks.** Median price by hour-of-day:
  the model's evening peak is ~right (hod 18: 34.8 vs RT 29.0–32.6) while its
  overnight floor is +$5 (22.6–23.0 vs 17.7–20.1) and its midday +$6
  (25.8–29.9 vs 18.9–23.3). By month the deficit is universal (median daily
  spread Jan: model 10.8 vs RT 29.5; Mar: 12.7 vs 38.6) — not a scarcity-tail
  phenomenon.
* **Band occupancy names the missing epochs.** Overnight+midday 2023: RT
  spent 1,493 h below $15 (137 negative) — the model 111 h (0 negative). In
  the RT<$15 hours the model prices $19.5–20.6 median: it has NOTHING priced
  between ~$0 and its all-hours-p50 gas bands.

## 3. The measured mechanism: the offer distribution's lower tail (committed fleet)

The 60-Day DAM disclosure (the SAME corpus, netload-binning and normalization
as the adopted `ercot_offer_surface_conditional`) shows where reality's
$0–15 supply lives — the committed fleet's cheap segments:

* **Online gas offers ≤$15 exist in every net-load decile**: 2.6–3.6 GW
  (≤$20: 3.7–8.0 GW), measured from the ON-status resources' submitted
  curves, 2023.
* **The committed (LSL) block is bid FAR below SRMC, and conditionally.**
  Committed CC Min-Gen-Cost multiplier, capacity-weighted p50 per net-load
  bin (edges .80/.90/.97): **0.585 / 0.370 / 0.282 / 0.133** vs the model's
  committed band ~1.0 — cycling-avoidance / stay-on bidding, deepening with
  tightness. (CT_PEAKER 1.32–1.44 and ST_GAS 1.32–1.52 measured ≈ the model's
  bands — consistent with ERCOT-61's measured-corroborated ST_GAS offers; the
  clamp leaves them untouched.)
* **The lower economic body carries an always-posted cheap tail.** Committed
  lower-body (rel < 0.67) multiplier p10 ≈ 0.65 / p25 ≈ 0.84, bin-stable.
* **The model's baked bands are the measured all-hours p50s** (the
  `offer_curve_dam_hrmults.json` lineage) — the p50 collapse deleted BOTH
  tails of the distribution. The adopted surface restored the upper tail in
  tight bins (clamped ≥); the lower tail was still missing (the marginal rows
  at the model's over-priced troughs are exactly the gas `econc*` ramp rungs
  and `committed` tranches — 139k/21k CC row-hours at 2,324 over-priced
  trough hours).

**Why this closes the circle endogenously:** restoring the measured cheap
committed segments lets the trough dual fall onto them (reality's $10–20
epochs), the daily spread widens from below, the (unchanged, $10-adder)
perfect-foresight arbitrage crosses its round-trip hurdle on ~3× more days,
batteries charge the troughs and discharge the binding hours, and the
binding-hour thermal excess narrows by conservation — no storage floor, no
thermal suppression, no fitted scalar.

## 4. The build: `ercot_offer_surface_lowcurve` (the conditional-offer-distribution LOW leg)

Mechanics mirror the adopted top leg exactly, with the clamp reversed:

* **Derive** `scripts/derive_dam_offer_hrmults.py --low-curve-binned` →
  frozen `data/raw/_validation-source/offer_curve_dam_lowcurve_condbinned.json`
  (its own artifact; the adopted top-surface JSON stays byte-stable, rule 23).
  Per gas class × net-load bin, capacity-weighted quantile ladders of
  per-resource median multipliers, **committed (online) resources only**:
  `binned_committed` (Min-Gen-Cost / LSL block, p25/p50/p75) and
  `binned_low_ladder` (lower-body incremental curve, p10/p25/p50). The
  committed-only basis is deliberate and asymmetric to the top leg (an OFF
  unit's cheap segments are not in the cleared stack; its scarcity wall is
  posted regardless).
* **Apply** `fleet.build_ercot_offer_surface_lowcurve_markdown`: P1-only
  additive markdown at the same `mc_bid_adjust` seam (P0 run lengths, startup
  coupling and every floor byte-identical), gas `committed`/econ-ramp rows
  only (peak rungs are the top leg's — disjoint, rule 19; coal untouched —
  take-or-pay/passthrough governs its low bids). Rows are rank-mapped
  capacity-weighted onto the measured quantile axis (heterogeneity-preserving,
  the top leg's rung construction); ratio clamped ≤ 1 (a markdown can only
  lower; ST/CT committed bands measured ≈ model → byte-identical); rows
  ranked past the ladder's top quantile untouched (their half of the band
  belongs to the top leg); repriced energy part floored at $1/MWh.
* **Zero fitted scalars** (rules 13/20/21): trigger = within-year net-load
  percentile (forward-native), levels = measured QSE quantiles, frozen
  against residuals. Tests: `tests/test_ercot_offer_surface_lowcurve.py`.

## 5. A/B result (2023 probe)

*(filled by `_ercot62_lowcurve_analyze.py` — see the calibration-log entry for
the adjudicated numbers and disposition)*
