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

## 5. A/B results (2023 probes) — the markdown family is REFUTED for the circle; the missing structure is the block's INFLEXIBILITY

Two variants, each keeper + the low leg as the single delta, vs the zero-delta
keeper reconstruction (C3a +3.9 %, C3b 0.133, C3c 171 h reproduced exactly):

| 2023 | keeper | v1 (cross-fleet rank) | v2 (plant-anchored + P0-gate) | RT actual |
|---|---|---|---|---|
| C3a lw | +3.9 % | +2.1 % | **+0.6 %** | — |
| C3b | 0.133 | 0.128 | 0.125 | — |
| C3c h | 171 | 171 | 171 | 311 DA |
| trough h < $15 | 112 | 245 | 192 | 1,493 |
| trough h < $20 | 860 | 1,268 | **1,472** | 2,645 |
| median daily spread | $13.5 | $13.3 | $12.7 | $35.3 |
| spread days > $24.25 | 81 | 82 | **67** | 247 |
| storage throughput | 0.55 TWh | 0.56 | **0.51** | — |
| coal annual Δ | — | −2.1 TWh | −2.9 TWh | — |

* **Levels move decisively toward reality** (v2 C3a-2023 +0.6 %, the $15–20
  trough band substantially fills) — the measured LSL markdown is a real
  price-formation ingredient.
* **The spread target moves the WRONG way in both variants** (median 13.5 →
  12.7; viable-arbitrage days 81 → 67; storage 0.55 → 0.51 TWh): the model's
  committed tranche is the marginal segment at mild-day EVENINGS too, so
  repricing it lowers both ends of the day. v2's P0-online gate and
  plant-position mapping fixed v1's specific artifacts (peak-rung erosion,
  offline-plant undercutting) but cannot fix this — it is inherent to
  repricing a tranche that plays both the LSL-block and mid-merit roles.
* **The merit-order shuffle persists** (coal −2.4/−0.5 TWh PRB/lignite, CT
  +1.5, CC +3.5 annual in v2): cheap committed blocks out-compete coal for
  dispatch, which reality's committed-STATE bidding cannot do (both fleets run
  at their committed levels; the margin competition happens above them).

**Determination.** In reality the cheap LSL bids coexist with wide daily
spreads because the block is INFLEXIBLE — must-take while the unit is on; its
bid never sets the margin. The model needs the STATE, not (only) the PRICE:
the P1-native commitment-bridge construction (`caiso_ra_mustoffer` /
`caiso_ra_p1_floor_fleet` — min-down + startup-restart economics detected from
the model's OWN P0 run pattern, physics-gated per rule 18, forward-native by
construction) applied to the ERCOT gas-CC fleet, with `min_load_frac` = the
MEASURED committed-CC LSL/HSL capacity-weighted p50 (0.574; CT 0.744, ST_GAS
0.205 — this session's derive from the same disclosure corpus). Keeper-probe
pre-check: 902 CC plant-nights/yr cycle off overnight between run-days
(~1.07 GW mean capacity) — the overnight analogue of the midday gap the CAISO
bridge was built for. The composition (bridge + markdown) is probed by
`scripts/probes/_ercot62b_bridge_probe.py` (rule-16 monkeypatch diagnostic —
the ISO-neutral bridge internals routed onto ERCOT with zero repo mechanisms);
the real `ercot_gas_commitment_bridge` gate + D-2/D-4 declarations are built
only on a positive probe. The low-curve markdown itself stays in the codebase
default-off (rule 1 — real, measured, correctly clamped; it composes with the
bridge the moment the state structure exists).

## 6. ERCOT-62b: the state-side probe result and the chartered next lever

With the spoofed bridge composed on the markdown (startup-aware OFF — the
screen's run-margin test refuses every anchor in the model's flat troughs,
the first probe arm's silent no-op; and note the double-import trap: patch
``scripts.run_calibration``, not the top-level alias):

| 2023 | keeper | v2 markdown | 62b bridge+markdown | RT |
|---|---|---|---|---|
| C3a lw | +3.9 % | +0.6 % | **+0.3 %** | — |
| trough h < $10 | 29 | 43 | **143** | 681 |
| trough h < $15 | 112 | 192 | **292** | 1,493 |
| median daily spread | $13.5 | $12.7 | **$13.7** | $35.3 |
| storage throughput | 0.55 TWh | 0.51 | **0.59** | — |
| evening HE18/19 discharge | 193/397 MW | 190/381 | **214/443** | — |
| coal annual Δ | — | −2.9 TWh | −3.3 TWh | — |

The bridge floors 39,446 unit-hours (8.26 TWh floor volume, D-2
``ra_mustoffer_bridge``; slack unchanged). First variant where the circle
moves the right way: troughs deepen AND batteries discharge more at the
evening peak. Still a fraction of the gap (viable-arbitrage days 68 vs 247),
and the coal→gas merit shuffle persists — coal's take-or-pay block carries
the same state-not-price gap and needs co-treatment.

**Chartered next lever (ERCOT-63): the real `ercot_gas_commitment_bridge`** —
own gate + config (measured per-class min-load fractions: CC 0.574, CT 0.744,
ST_GAS 0.205), D-2/D-4 declarations and forced-energy budget, the
startup-aware screen re-derived for ERCOT economics (or dropped with cause),
coal-side committed-state reconciliation (rule 19), composed with the
low-curve markdown; full-span 2023-2025 + zero-forcing twin + LOYO before any
promotion talk.
