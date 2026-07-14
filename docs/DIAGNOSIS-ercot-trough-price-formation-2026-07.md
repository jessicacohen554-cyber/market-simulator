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

## 7. ERCOT-63: the real bridge built and probe-adjudicated — the STATE ALONE closes what the composition was credited with; the markdown stays off

The real mechanism (`ercot_gas_commitment_bridge`, this session): the CAISO
bridge internals (§5) behind an own ERCOT gate — merchant gas-CC only,
`min_load_frac` = the measured committed-CC LSL/HSL cap-weighted p50 (0.574),
physical (< min-down) restart bar + economic (≥ min-down) startup-restart
bridging on the model's own P0 duals, the economic leg bounded to ONE DA
operating day (`DA_COMMITMENT_HORIZON_HOURS`, tariff-cited), P1-native at the
shared P0→P1 seam in both orchestrators. D-2 id `gas_commitment_bridge` (17)
with a D-3 ablation entry; cited D-4 window (self-windowing: floors exist
only inside P0-detected idle gaps ≤ one DA day; measured incidence
overnight-dominated — the 902 CC plant-nights/yr driver). Recorded
adjudications:

* **Class scope — CC only.** CT_PEAKER is physics-inert for the economic leg
  (min-down 1-2 h < `RA_BRIDGE_ECON_MIN_DOWN_HOURS`; rule 18 — the real
  market cycles fast-start iron off overnight) and its measured committed
  band ≈ the model's (ERCOT-61); ST_GAS is rule-19-excluded (its committed
  state is the all-hours `gas_st_netload_drag` floor's, and the class is C8
  grounded-above-budget at ~33 % — a second floor would stack mechanisms on
  one phenomenon). CT 0.744 / ST_GAS 0.205 recorded unused.
* **Startup-aware screen — dropped with cause, not re-derived.** Its anchor
  test prices run margins off the model's own duals; ERCOT's modelled
  troughs are the +$5-7-overpriced, spread-flattened quantity under repair
  (§2), so margins are circularly thin and the screen refuses every anchor
  (the 62b no-op). Re-deriving a lower threshold "for ERCOT economics" would
  be a scalar tuned until anchors survive — a residual-fitted knob (rules
  13/20). The phantom-micro-run failure mode it guards is bounded by
  measurement instead: the real gate's 2023 floored-gap distribution is
  p10/p50/p90 = 2/6/14 h with 0 gaps > 24 h — day-run-anchored overnight
  bridging, not belly-chopping fragments.

**2023 probe ladder** (rule-16 throwaways vs the byte-faithful ercot59
keeper reconstruction — C3a +3.9 %, C3b 0.133, C3c 171 h reproduced exactly;
note the ercot59 base's `ercot_storage_as_deployment` raises the storage
baseline vs the §6 ercot56-based rows, and its defining delta was missing
from meta.json — meta-writer fixed this session):

| 2023 | keeper | bridge ALONE | bridge+markdown | RT |
|---|---|---|---|---|
| C3a lw | +3.9 % | +3.1 % | **+0.3 %** | — |
| C3b | 0.133 | 0.131 | 0.125 | — |
| C3c h | 171 | 171 | 171 | 311 DA |
| trough h < $10 | 27 | 107 | 143 | 681 |
| trough h < $15 | 101 | 228 | 277 | 1,493 |
| trough h < $20 | 861 | 1,202 | 1,541 | 2,645 |
| median daily spread | $13.5 | **$14.9** | $13.5 | $35.3 |
| spread days > $24.25 | 81 | **85** | 69 | 247 |
| storage throughput | 0.65 TWh | **0.74** | 0.67 | — |
| HE18/19 discharge | 205/437 MW | **243/505** | 225/474 | — |
| coal annual Δ | — | −1.37 TWh | −3.30 TWh | — |
| slack | 7.5 GWh | 7.5 | 7.5 | — |

* **The real gate reproduces the 62b monkeypatch row** (bridge+markdown C3a
  +0.3 %, <$10 143 h — identical) with the residual differences traced to
  the known construction deltas (CC-only scope, DA-horizon cap, ercot59
  base): the bridge floors 37,788 unit-hours / 7.91 TWh vs the spoof's
  39,446 / 8.26. C8: gas-CC at-floor 6.5 % (bridge-attributed 5.6 %) vs the
  30 % cap. The DA-horizon cap was isolated with a fourth rung
  (`bridge_md_nohorizon`, the 62b-exact uncapped construction): only 35
  gaps > 24 h exist to drop (0.31 TWh), and uncapping moves nothing
  measurable (C3a identical, <$15 277 → 288 h, spread +$0.1, storage
  +0.01 TWh) — the tariff-grounded one-operating-day bound keeps the
  declared D-4 window exact at zero fit cost. Kept on.
* **The new information is the bridge-ALONE rung the 62b probe never ran:
  the state alone wins every circle target** — spread median 13.5 → 14.9,
  viable-arbitrage days 81 → 85, storage 0.65 → 0.74 TWh, HE18/19 discharge
  205/437 → 243/505 MW, troughs deepening (101 → 228 h < $15), C3a/C3b
  improving, C3c and slack untouched. Composing the markdown back on
  RE-INSTATES its §5 failure signature even with the state present: the
  spread compresses back to 13.5, viable days fall to 69 (below the
  keeper's 81), storage gives back half the gain, and the merit order
  overshoots (CT_PEAKER 6.38 → 7.77 TWh vs 7.10 actual; CC_REGULAR 139.7 →
  143.8 vs 141.7 actual). The composition's C3a gain is bought by
  mis-pricing the committed tranche's ABOVE-floor (mid-merit) capacity at
  the LSL bid — the right number through a wrong mechanism (rule 1). **The
  markdown stays default-off; the candidate is the bridge alone.** (The §5
  "state, not price" determination lands stronger than filed: the state is
  not merely necessary — for the circle it is sufficient, and the
  tranche-wide LSL reprice is refuted even in composition. The remaining
  admissible price-side lever for the still-open trough-depth gap — model
  228 h < $15 vs RT 1,493 — is a FLOOR-SCOPED markdown: the measured LSL
  bid applied only in the bridge's own floored plant-hours, where the
  tranche genuinely plays its LSL role. Enumerated for ERCOT-64; not built
  this session.)
* **Coal reconciliation (charter step 4) — resolved by measurement, no coal
  mechanism needed.** The keeper OVER-dispatches coal vs the committed
  actuals (PRB 48.87 vs 45.09 TWh; lignite 16.93 vs 15.33) while
  under-dispatching CC_REGULAR (139.74 vs 141.74): the model was papering
  the missing overnight gas-CC committed state WITH coal. The bridge-alone
  shuffle (−1.37 TWh, spread across coal committed AND econ tranches, all
  above coal's own floors) moves every class TOWARD its measured actual —
  CC_REGULAR lands within 0.1 TWh of actual — and coal remains ABOVE its
  actual after it. The 62b −3.3 TWh row was the composition's (markdown
  competition on top); the state's own displacement is a correction, not a
  defect. Rule 19 is satisfied with no new mechanism: coal's committed
  state stays owned by its existing take-or-pay/must-run floors
  (untouched), and the committed-state energy returns to the class
  measurement says holds it.

## 8. ERCOT-64: the FLOOR-SCOPED LSL markdown is PROVABLY INERT — the LSL price-side enumeration closes; the lane is NOT at frontier (the negative-price epoch pair remains)

The §7 enumerated price-side lever was built this session
(`ercot_offer_surface_lowcurve_floorscoped`, own gate, rule 24): the measured
committed-CC LSL bid (the frozen ERCOT-62 `binned_committed_p50` quantiles —
NOT re-derived) applied to the gas-CC committed tranche ONLY in the bridge's
own floored plant-hours, keyed on the BRIDGE FLOOR MASK (never the v2
P0-online gate, which is False in bridged gaps by construction), the floor
computed ONCE and shared across the P1 fleet and bid hooks
(`pipeline.commitment.build_ercot_gas_bridge_p1_preps`; forecast parity in
`runner.py`). Mutually exclusive with the refuted tranche-wide v2 (rule 19,
enforced loud). Probe (rule-16 2023-only throwaway,
`scripts/probes/_ercot64_ladder_probe.py`, deleted): keeper rung reproduces
the promoted ercot63-gas-bridge byte-exactly (C3a +3.1 %, C3b 0.131, C3c
171 h, trough <$10/15/20 = 107/228/1,202 h, spread $14.9, arb-days 85,
storage 0.74 TWh, HE18/19 243/505 MW).

**Result: the fs_markdown rung is EXACTLY the keeper.** The mechanism fired
(40 committed tranches marked down over all 37,788 bridge-floored
plant-hours) and moved NOTHING: price max |Δ| = 0.0 across all zone-hours,
per-unit annual dispatch max |Δ| = 0.0 MWh, every score/trough/spread/storage
metric identical.

**Failure anatomy — inert by construction, not by accident.** The bridge's
floor target is `min(0.574 × plant_pmax, tranche_pmax)`; the committed
tranche's capacity share is below 0.574 for every bridged plant (median
committed share ~25 %), so the target clips at the tranche bound on ALL 40
floored rows and the floor lands exclusively on committed rows. In every
floored gen-hour the LP bound is therefore `min_gen = pmax × availability`
— the tranche is exactly pinned (measured: max `P − floor` = 0.0 over all
37,788 hours, in BOTH the keeper and the markdown rung — no headroom exists
anywhere in the window; the apparent sub-1.0 floor/annual-cap ratios on 24
rows are availability derates, not headroom). A variable pinned between
equal bounds contributes no degree of freedom, so its objective coefficient
can affect neither the solution nor any dual: the markdown is provably a
no-op on its entire declared window. The window where the tranche genuinely
plays its LSL role is precisely the window where its bid cannot price — the
model already reproduces the measured "the LSL block never sets the margin"
inflexibility (§5) through the STATE alone, and reality's cheap LSL bid is
inert in the model for the same reason it coexists with wide spreads in
reality.

**The LSL / offer-lower-tail price-side enumeration is now CLOSED,
exhaustively:** (a) the top leg is adopted (peak rungs); (b) the econ
lower-body is clamp-inert — the keeper's delta-adjusted ramp already sits
at/below the measured band medians (§4); (c) the tranche-wide committed-LSL
markdown is refuted — it reprices above-floor mid-merit capacity and
compresses the spread (§5, §7); (d) the floor-scoped committed-LSL markdown
is inert — the only capacity it touches is pinned (this section). Any
committed-LSL markdown variant must scope its window somewhere between (c)
and (d), i.e. it either leaks onto mid-merit capacity (refuted) or touches
only forced volume (inert). No admissible offer-level change to the gas
committed/lower tail remains for the trough gap. The mechanism stays in the
codebase default-off as the recorded closure (zero fitted scalars — not a
rule-26 re-armable knob); its unit tests pin the mask/scope mechanics.

**Lane status — NOT at frontier: one named admissible pair remains, the
NEGATIVE-PRICE EPOCH formation.** The remaining trough-depth gap re-measured
on the keeper (2023): RT spent 1,493 trough hours < $15 (137 of them
NEGATIVE); the model 228, and its floor is $0 by construction (renewable
MC = 0, `negative_renewable_offers=False` in the keeper) — the deepest RT
epochs are UNREPRESENTABLE, not merely under-produced. The model already
forms 2,651 zonal wind-marginal epochs (some zone's dual ≤ $0.01) where a
negative keep-running offer would price: (i) `negative_renewable_offers`
(existing registry field, unprobed on ERCOT) — the PTC keep-running bid is
statutory market structure (a PTC-subsidized wind unit is whole down to
≈ −$PTC), forward-native and measured, the exact CAISO lever-audit
"KEEP offer mechanism" precedent; (ii) its reach is bounded by the OPEN VRE
under-curtailment lane (2026-07-07 step-2 diagnosis: the reduced West→North
corridor is a too-wide relief valve; the sanctioned WP-B curtailment-share
driver `ercot_wtx_curtailment_driver` was built but is NOT in the keeper
recipe) — the epoch COUNT and its propagation to the load-weighted hubs is
that lane's topology question. Chartered as ERCOT-65: probe (i) on the
keeper, with (ii) as its enabling co-lane; no offer parameter may be tuned
to the C3c scarcity tail (separately open, G-22 ledger).

## 9. ERCOT-65: the negative-price epoch pair adjudicated — BOTH §8 premises measured wrong; the vintage scoping built and probe-inert; the wtx driver discovered ALREADY LIVE in the keeper (recorder defect, fixed); the trough/spread lane is AT FRONTIER pending the West topology split

Probes (rule-16 2023-only throwaways vs the byte-faithful ercot63-gas-bridge
reconstruction — C3a +3.1 %, C3b 0.131, C3c 171 h, spread $14.9, storage
0.74 TWh reproduced exactly; `_ercot65_ladder_probe.py`, scored with
`_ercot65_epoch_anatomy.py` + the h<$0 band added to
`_ercot62_lowcurve_analyze.py`; bundles deleted).

**Premise correction 1 — the model's wind offer was never $0.** §8 asserted
"renewable MC = 0 … the deepest RT epochs are UNREPRESENTABLE". Measured
false: every ERCOT backcast prices wind at the FLAT ``-ira_ptc_wind =
-$26/MWh`` on every MW (`policy.ira.compute_dispatch_credits`;
`negative_renewable_offers=False` only disables the separate CAISO REC-floor
mechanism). The keeper's 2,651 "wind-marginal epochs (dual <= $0.01)" sit AT
-$26.00, not $0 — and they are PANHANDLE-ONLY: 2,577 h < $0 in Panhandle,
zero in every other zone (West included: min $0.00), epoch breadth mean 1.02
zones. The LW price never goes negative because the epochs never leave the
one bottled zone; in RT's 147 negative lw-hours the model prices median
$13.99 (never < $0, never even wind-marginal outside Panhandle). Negative
prices are fully REPRESENTABLE; what is missing is the SYSTEM-LONG /
West-bottled state, not the bid.

**Premise correction 2 — the WP-B curtailment driver is ALREADY LIVE in the
keeper.** The "built but NOT in the keeper recipe" belief (§8, the ERCOT-65
charter, and every entry since ercot-53) traces to a run_config recorder
defect: `run_year` applies the generic ``prb_overrides`` channel LAST, and
the keeper-lineage metas carry ``coal_prb_sigmoid_overrides.
ercot_wtx_curtailment_driver: true`` (the owner's 2026-07-07 backcast
default-ON), which stomps the meta-writer's coerced top-level ``False``
kwarg — so every solve since ercot42's promotion has had the West/Panhandle
VRE ceiling ACTIVE (probe logs print "West/Panhandle VRE ceiling active";
keeper wind dispatch/potential mean 0.949 ≈ the ceiling mean 0.9488) while
`run_calibration_full`'s recorder applied its late tri-state re-override in
the OPPOSITE order and wrote ``driver: false`` into run_config.json. Five
sibling keys in the same overrides dict (drag, zonal-gas, reserve-forward…)
record truthfully; the wtx boolean was the single divergent key. FIXED this
session (recorder now mirrors the live order and warns loudly on channel
conflicts, live path warns symmetrically); the keeper + ablation-twin
``run_config.json`` corrected to what actually ran (annotated
``_record_corrections``), and the keeper DOF ledger gains the depth pair
(wind 0.1004 / solar 0.1637) it had silently omitted — the one
outcome-anchored DOF, owner-accepted 2026-07-07. Solves untouched. The
"wtx composition" rung is accordingly BYTE-IDENTICAL to the keeper (price
max |Δ| 0.0, wind/solar annual Δ 0.000 TWh): there is nothing to compose —
the co-lane's driver leg is vacuous, and the [3e] under-curtailment /
zero-negative-reach gap measured here is the gap WITH the driver on.

**The build — `wind_ptc_vintage_offers` (the §8 lever (i), correctly
scoped) — is real structure and probe-INERT.** The flat -$26 pays the PTC
to vintages whose 10-year §45 window expired (27/32/40 % of TX wind
nameplate in 2023/24/25 — EIA-860 vintages; in reality they bid ~$0). The
mechanism replaces the flat offer with ``-PTC_statutory(year) x
eligible_share[zone, month]`` (statutory $28/29/30 for 2023-25, IRS
notices; measured EIA-860 share, month-precise aging, rule-13
forward-native; solar stays $0 — ITC, and the CAISO $20 REC value is
rule-25 CAISO-scoped). Probe verdict: per-unit dispatch max |Δ| = 0.0 MWh
— the wind bid's LEVEL never changes dispatch while wind runs at/below its
bound with every alternative supply more expensive — and the ONLY price
movement is the Panhandle epoch dual -26.00 → -27.03 (its fleet is 96.5 %
in-window; $1.03 deeper, load-weighted invisible). West's structurally
distinct blend (-$14.8, 52.8 % eligible — the old CREZ fleet) never prices
because West wind is NEVER marginal (the §8/step-2 relief valve). Every C3
score, trough band, spread, arb-day, storage and slack/dump metric is
identical to the keeper. Verdict: correct structure, kept in the codebase
default-off as the recorded closure (zero fitted scalars, unit-tested,
D-5 forecast parity); REFUTED as a trough-depth lever in the current
topology — the marginal-bid depth is not the binding constraint.

**Lane adjudication — AT FRONTIER (offer side closed; the remaining lever
is structural and owner-gated).** The trough/spread family's admissible
enumeration is now exhausted on record: the LSL/lower-tail price side
closed at ERCOT-64 (§8); the negative-band offer side closes here (the
PTC bid was already present at full depth; its honest vintage scoping is
dispatch-inert and price-inert outside a $1 one-zone shift; a deeper
uniform bid has no admissible basis, and the CAISO REC value is
rule-25-barred). What separates the model's 9 lw-hours < $1 from RT's 147
negative lw-hours is epoch FORMATION and REACH: reality's negative epochs
are system-long or broadly-bottled states the 8-zone reduction cannot
enter — its West→North 7,300 MW relief valve exports the West surplus
(West wind is never curtailed-marginal) and its Panhandle epochs stay
demand-weighted-invisible. The one named forward-admissible mechanism is
the **West/Panhandle topology split** (step-2 handoff §"recommended next
step" option 1: represent the chronically-binding nodal paths the
reduction collapses), a structural `iso_configs`/`constants` change
requiring owner sign-off — the WP-B ceiling (option 2, already live)
fixes the curtailment VOLUME but, as a bound on the wind variable itself,
can never price an epoch (a ceiling-clipped variable is not marginal; the
ERCOT-64 pinned-variable anatomy, mirrored). Frontier block drafted in
the 2026-07-13 calibration-log entry for owner sign-off; keeper
`2026-07-12-ercot63-gas-bridge` unchanged. The C3c scarcity tail stays
the separate open G-22 item (rule 13).
