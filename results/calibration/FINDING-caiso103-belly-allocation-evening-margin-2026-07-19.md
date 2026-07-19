# FINDING (caiso-103): the DA-allocation shape is FLEET-SIZE-INVARIANT (r >= 0.994 across a 3.5x fleet) while the overnight second cycle and the RD book are NOT (flat-absolute / system-sized) — the belly allocation-schedule mechanism is designed and owner-gated (M1, NO solve); the evening Q1 margin decomposition [+ caiso-92 re-derive] sections follow

**Session 2026-07-19 (CAISO-103 — the caiso-102 §7 re-charter: priority 1 =
the belly allocation mechanism design (owner-gated BEFORE any solve),
priority 2 = the evening CT-rung composition decomposition, priority 3 = the
caiso-92 offer-surface re-derive citing issue #2562). Derive-first: the only
LPs run are the same-machine repro of the PROMOTED caiso-102-hourfix keeper
recipe (`scripts/probes/_caiso102_repro_A.py` — the recipe now solves the
keeper bytes since the loader fix is in code; gitignored `caiso102_repro_A`,
un-registered per the FINDING-caiso92b protocol) [and the caiso-92 re-derive
adjudication leg if the artifact moves — its own section]. NO belly mechanism
was built or solved; the design goes to the §3 owner ask
(`docs/handoffs/caiso-103-belly-allocation-ask-2026-07-19.md`). Instruments
(committed, NEW): `scripts/probes/_caiso103_alloc_stats.py` (the allocation
statistics), `scripts/probes/_caiso103_evening_margin.py` (the Q1 marginal
economics decomposition).**

## 1. The allocation statistics (channel-design grain the caiso-102 windows did not carry)

`_caiso103_alloc_stats.py` on the committed Daily Energy Storage Report
market_output (LESR only — the caiso-98/99/100 basis), EIA-860 monthly fleet
via `load_eia860_storage` (PS excluded — the caiso-99 envelope's exact
denominator), `actual_lmp_hourly_CAISO.parquet` for window-λ context. Clock:
TRADE_DATE+HOUR hour-ending physical labels, hod = HOUR−1, 25th hour and
Feb-29 dropped (the `_caiso102_charge_channels` convention; NOT the
issue-#2562 filled-frame family).

- **(A) The fleet-normalized DA-allocation shape is fleet-size-invariant.**
  Mean IFM charge rate by hod ÷ monthly fleet MW: cross-year pairwise
  r(2023,2024)=0.998, r(2023,2025)=0.994, r(2024,2025)=0.996 while the fleet
  grew 4.4 → 15.4 GW; per-hod CV ≤ 0.06 in the belly core (hod 9-14: 0.01,
  0.03, 0.03, 0.03, 0.03, 0.06), ≤ 0.15 at hod 7-8/15, 0.26-0.51 in the thin
  overnight shoulder. hod-share of annual IFM charge (2025): hod 8/9 =
  6.2/10.4 %, hod 10-14 = 13.9/15.9/16.3/14.7/11.0 %, hod 15/16 = 4.7/1.7 %,
  overnight ramp hod 2-3 ≈ 1.2-1.5 % each, evening/late ≈ 0. 2023/2024 within
  ~1 pp per hod.
- **(B) Window share of daily IFM charge** (p25/p50/p75 across days):
  belly .619-.671/.722-.769/.786-.829; morning .057-.078/.115-.142/.219-.250;
  overnight .003-.017/.024-.063/.055-.126 (2023 highest — the commissioning-
  year fleet); pm-shoulder p50 .020-.041; evening + late ≡ 0 in every year.
  Charge-weighted DA λ by window (2025): overnight 41.6, morning 22.8, belly
  16.0, pm-shoulder 11.8 — the DAM buys the non-belly windows at a $6-26
  premium over the belly, the FINDING-caiso102 §3 obligation-conduct
  signature at the DA layer.
- **(C) SOC trajectory (RTD SOC hod-mean ÷ fleet MWh):** trough at hod 7
  (0.278/0.192/0.124), peak hod 15-16 (0.793/0.781/0.766). The normalized
  trough DEEPENS as the fleet grows — the AS/positioning SOC floor is not
  proportional to fleet energy. Mean trough→hod-10 rebuild 3.6/6.8/9.7
  GWh/day.
- **(D) The overnight second cycle does NOT fleet-scale.** Overnight (hod
  0-5) RTD charge 0.334/0.360/0.357 TWh — flat in absolute terms across the
  3.5× fleet; ÷ fleet-MWh-yr it FALLS 0.049 → 0.031 → 0.022. And it is
  DA-scheduled (IFM overnight 0.331/0.362/0.366 ≈ RTD in every year) — the
  second cycle is DAM conduct too, not an RT phenomenon.
- **(E) The RD book does not fleet-scale either**: per-MW belly-window IFM RD
  award 0.170/0.119/0.090 — the reg-down requirement is system-sized, the
  fleet's share of it saturates.

Design consequences: (A)/(B) give the DA-allocation-profile schedule the
same forward-story class as the caiso-99 envelope (measured per-MW conduct
shape × model-endogenous scale) with stronger stability evidence than the
envelope's own derivation; (D)/(E) argue AGAINST building the AS-obligation
SOC term from a shape×fleet construction (it would overbuild the second
cycle in every forward year — its driver is the system AS requirement, not
the fleet size).

## 2. The mechanism design (M1) — owner-gated, NOT solved

Full design, rule-12/13/19/24/25 statements, D-2/C8 implications, and the
caiso-76/99/100/101 interaction analysis:
`docs/handoffs/caiso-103-belly-allocation-ask-2026-07-19.md`. Shape summary:
per solve-day scheduled-volume variable `S[d]`, fleet-battery floor rows
`Chg[h,d] >= alloc_share[hod] × S[d]` + day cap `Σ_h Chg[h,d] <= S[d] /
da_frac` — every charged MWh buys the measured allocation bundle except a
free slice bounded to the measured RT-margin share (16-24 %); volume stays
endogenous (S=0 feasible; no objective change), so the caiso-100 volume-
collapse failure mode is structurally excluded while the hour-grain charge
stops bidding the belly up (the DAM/RT split the measured channels show).
M2 (window-share bands) documented as the weaker fallback; M3 (SOC term)
measured-DEFERRED on (D)/(E). No flag, no solve, nothing registered for this
lane; the B-leg (single delta vs `caiso102_repro_A`, pre-registered gates
incl. the ±5 % volume-holding band that is the mechanism's own claim) waits
on the ask.

## 3. Priority 2 — the evening Q1 margin decomposition: the FIRM IMPORT BLOCKS are price-setting in the tight hours the code documents them as inframarginal

Baseline: same-machine `caiso102_repro_A` (solved this session on the
post-hourfix code) reproduces the caiso-102-hourfix keeper ladder
DIGIT-FOR-DIGIT (belly +6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1, overnight
+0.8/−0.0/+1.4; C1 grid matches the registered bundle) — valid FINDING-caiso92b
baseline. `_caiso103_evening_margin.py <repro>` on the aligned clock, Q1 =
deepest evening resid-quartile (454-457 h/yr; mean resid −36.6/−25.5/−15.4):

1. **Marginal-class attribution** (interior dispatch = strictly inside unit
   bounds = price-setting in an LP): `import` is marginal in **0.99/0.97/1.00**
   of Q1 hours with 3.6-4.3 GW at interior — the single most-marginal supply
   in exactly the hours the model under-prices. (CC_REGULAR interior in
   ~0.9 of hours but only ~430-460 MW; CT_PEAKER 0.45/0.20/0.16.)
2. **The import rung is never exhausted**: CA-inbound corridors carry
   5.0-6.2 GW mean unused headroom in Q1; total import saturated in **0 %**
   of Q1 hours, links-at-limit 0.0. The margin has effectively unlimited
   sub-CT-priced import depth to serve instead of climbing the rung.
3. **Committed-CC headroom is NOT the substitute**: 0.22-0.24 GW — an order
   of magnitude below the import depth.
4. **The CT rung entry price** (monthly p10 of λ over CT-active plant-hours:
   ann-mean 59.0/47.1/54.7) sits ABOVE the Q1 λ by a median
   +1.3/+3.6/+13.1 $/MWh — the model's tight-hour clearing stops exactly one
   rung short of the CT prices reality pays.
5. **Battery timing is secondary**: the caiso-99 envelope binds in 37 % of Q1
   hours in 2023 but only 16 %/8 % in 2024/25; Q1 discharge runs 1.7-2.9 GW
   below the envelope cap on average — the fleet is economically idle, not
   capability-bound.
6. **Hub separation is the smoking gun**: in Q1 hours ACTUAL CAISO RT clears
   ≈ AT/ABOVE the measured intertie hub LMP (mean −2.3/+4.0/+6.7 vs
   max(MALIN, PALOVRDE); median −0.7/+2.6/+4.8) while the MODEL's λ sits
   **−39.8/−18.9/−8.5 BELOW the same measured hubs** (median
   −23.4/−12.2/−8.0). Reality's tight-evening margin prices at/above the
   tie; the model's prices one-to-two rungs below it.

**Root cause (tranche-level attribution):** the marginal import units in Q1
are the two FIRM/CONTRACTED blocks — `DSW_solar_PV` (interior 0.98/0.96/1.00
of Q1 hours, 1.5-2.1 GW) and `PNW_hydro_base` (0.98/0.96/1.00, 1.3-1.8 GW).
Under the keeper's `caiso_perhub_firm_base` these deliberately KEEP their
static contract-cost ladder prices ($28 / $48, Tier-3 proxies) while the
spot tranches ride the measured hubs — and `transmission.py`'s own comment
documents why: the blocks proxy long-term specified-source contracts (BPA
firm hydro over COI; desert-SW solar PPAs over Path-46) that are
"scheduled at contract cost and flow largely independent of the hourly spot
spread — they are INFRAMARGINAL, so CAISO's clearing price stays domestic
even while 3-6 GW imports flow", and RA-import must-offer conduct is
self-schedule or ≤$0 bids in the availability assessment hours (CPUC
D.20-06-028). The LP contradicts that driver: an elastic offer at contract
cost makes the block MARGINAL wherever demand lands inside its partial-
dispatch range — which is ~every Q1 hour — so the model (a) pins tight-
evening λ at the contract-cost rung instead of the hub/CT level, and (b)
**economically withholds 1.7/2.5/2.3 GW of contracted firm capability in Q1**
(availability − dispatch, per-hod p99 capability proxy) that the real
self-scheduled contracts flow. The two halves of the evening residual — the
λ under-price AND the aligned-clock under-import (−0.5/−0.3/−1.4 TWh,
FINDING-caiso102 §4) — are ONE defect: price-taking volume treated as
price-elastic at the margin.

This is the same structural class as the belly defect (§1-2): both lanes'
residuals are DA-fixed/contracted volumes the single-market LP lets
re-optimize against the RT margin — battery charge on the demand side
(belly), firm import contracts on the supply side (evening). The candidate
fix (owner-gated, NOT built): offer the firm blocks as price-takers (≤$0 /
−ε bids on their existing caiso-73 measured shaped availability) so they
flow whenever λ ≥ 0 and the margin moves to the hub-priced tranches / the
domestic CT rung — see
`docs/handoffs/caiso-103-evening-firm-import-ask-2026-07-19.md`. NOT a CT
floor (caiso-91b untouched), NOT an import throttle (it INCREASES import
flow toward the measured volume), NOT a caiso-95-artifact patch (the §4
aligned measurement is the basis), and it RETIRES two Tier-3 fitted contract
costs from the price-formation path (DOF ledger shrinks by two rows).

## 4. Priority 3 — caiso-92 offer-surface re-derive (issue #2562)

(appended after the re-derive runs — the gitignored public-bids corpus is
refetched on this container first)

## 5. Issue #2546

No owner ruling appeared this session (no comments on the issue); carried
unchanged.
