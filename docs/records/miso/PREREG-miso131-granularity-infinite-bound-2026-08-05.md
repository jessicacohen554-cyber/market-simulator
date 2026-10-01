# PREREG miso-131 — the coal-ladder GRANULARITY prerequisites, screened ex ante by an INFINITE-GRANULARITY BOUND (no LP)

Session miso-131, 2026-08-05, branch `claude/miso-131-granularity-screens`, off
`origin/main` at `99948c04`. Keeper `2026-08-04-miso-127-onlinepmin` (NOT-YET,
sole FAIL C7 `COAL_PRB` 2025 cv_ratio 0.347 vs 0.5). **Pushed BEFORE the probe
is run and before any adjudicating statistic exists.** Probe (written with this
prereg, run only after both are pushed):
`scripts/probes/_miso131_granularity_infinite_bound.py`; record
`results/calibration/_miso131_granularity_infinite_bound.json`.

**Session-number note.** The inbound owner handoff carried the label
"miso-130". That number is SPENT: the merged PR #3573 session (finding
`FINDING-miso130-c7-night-regime-2026-08-05.md`, log entry, §5.4 queue stamp)
is miso-130 and its log entry names miso-131 next. This session is
**miso-131** and executes the handoff's charter under its real number.

## 0. Contamination — disclosed in full (the miso-128 §0 duty)

This session's author also ran miso-130, so the following numbers were already
measured (descriptive, un-preregistered) and are PRIOR KNOWLEDGE here, never
results of this lane: the July freeze statistic (PRB econ capacity priced below
the model's own July night floor p10 = 21.1/2.8/55.4 % in 2023/24/25; below
night p50 = 30.8/17.4/74.6 %); model July night prices p10/p50 =
26.11/27.86, 20.67/25.86, 31.42/33.87 $/MWh; July gas 2.972/2.429/3.410
$/MMBtu; COAL_PRB July night surplus +2,276/+2,204/+3,454 MW. From miso-129
(committed): step 72.6 MW vs measured amplitude 90.4 MW, median plant ratio
1.175, 41.4 % of capacity with its swing inside one step — re-established at
HEAD by this session before this prereg (bit-identical census, P0a below).
From miso-128 (committed): cv_ratio = R_tot × R_dfrac × R_level;
R_dfrac 0.524/0.549/0.354 is the entire failure; needed 2025 R_dfrac =
0.5/(0.952×1.025) = 0.5124, a 1.447× rise; model absolute amplitude deficit
1,145/858/800 MW.

**The declared PRIOR:** the freeze statistic makes P1 EXPECTED TO KILL — most
of the 2025 ladder appears priced below the wave floor, where no step count can
cycle it. Per the miso-127 Lane B duty this prior is COMMITTED TWO-SIDEDLY: if
P1 fails to kill, the prior is recorded REFUTED and the lane PROCEEDS to P2 —
an expected-kill screen that survives is a licence, not an embarrassment.

## 1. The object and what this prereg adjudicates

miso-129 §3's named-not-chartered object: `offer_curve_smoothing_n` (= 6, exp
1.0, on 100 % of MISO coal capacity) may be too COARSE — 41.4 % of capacity has
its whole measured diurnal swing inside one step. miso-129 recorded three
prerequisites; this prereg screens **prerequisite 1** (granularity, not
something else, carries `R_dfrac`) with a mechanism-independent bound, states
the **prerequisite 2** identification plan (P2, executed only on P1 survival),
and pre-commits the **prerequisite 3** ceiling as a solve-time kill (P3).

**The bound construction (P1).** Granularity's best case is n→∞: the econ band
becomes the continuous linear ramp between its own endpoints (the documented
`exp == 1` limit of `_econ_curve_steps`). For each keeper-payload COAL_PRB
plant, reconstruct the econ band's hourly dispatch response to the keeper's OWN
solved zonal price (the miso-123 clears-against-solved-duals pattern):

* `response_6(P)` — sum of assembled econ steps whose $ offer < P (the current
  ladder, quantized);
* `response_∞(P)` — the piecewise-linear interpolation through the same
  assembled step (cum-capacity, $) points, extended to the band endpoints (the
  n→∞ limit; same endpoints, same capacity, zero new parameters).

Step $ offers = assembled tranche HR × the plant's F923 monthly delivered coal
price (plant-months without a reported row fall back to the ISO PRB
volume-weighted month mean from the same table) + the assembled VOM.
The counterfactual class series is `payload_plant(t) + Δ(t)`,
`Δ = response_∞ − response_6`, clipped to [0, plant's own solved annual max]
(availability proxy; clip incidence reported). Scored against the bench actual
COAL_PRB exactly as D-1 scores (annual hour-of-day mean profile, off-peak
h0–h14 CV ratio). Price-taking is declared as the bound's direction: cycling
coal into the wave softens the wave, so equilibrium feedback can only shrink
the gain — a price-taking cv_ratio that still fails is conclusive; one that
passes licenses the arm, whose A/B then measures the equilibrium number.

## 2. Numbered properties, each with its falsifier

* **P0a (census, already run — protective).** The miso-129 construction census
  reproduces at HEAD: n=6, 48 plants / 38,144.8 MW, 100 % laddered, step
  72.6 MW, median ratio 1.175, 41.4 % share. FALSIFIER: any drift → stop,
  re-derive the census before proceeding. **Measured before this prereg:
  bit-identical. PASS.**
* **P0b (construction validity — protective, gates P1).** The n=6
  reconstruction must reproduce the keeper's own solved behaviour it claims to
  model: per year, corr(hod profile of reconstructed class series, hod profile
  of the keeper's solved payload class sum) ≥ **0.90**, AND the reconstructed
  cv_ratio within **±0.10 absolute** of the keeper's own D-1 cv_ratio
  (0.514/0.529/0.347). FALSIFIER: either bar missed in any year → P1 is
  **VOID** (the construction cannot adjudicate; report, stop, NO verdict — the
  lane stays open for a better construction).
* **P1 (the adjudication — prerequisite 1).** cv_ratio of the n→∞
  counterfactual vs bench, 2025: **KILL the lane if < 0.50** (infinite
  granularity cannot reach the gate even under price-taking, which overstates
  the gain). **SURVIVE if ≥ 0.50** → prerequisite 1 established at screen
  grain; the expected-kill prior of §0 is then REFUTED and recorded so.
* **P1-secondary (protective, two-sided).** If the n→∞ counterfactual drops
  2023 or 2024 cv_ratio below 0.50, granularity is REFUTED AS HARMFUL
  (quantization is currently generating, not suppressing, amplitude in passing
  years) — the lane dies regardless of P1.
* **P1-report (no bars).** The frozen share at the annual grain (capacity with
  zero Δ-response support all year), per year — links the miso-130 July
  statistic to the annual gate. Descriptive only.
* **P2 (identification plan — executed ONLY if P1 survives; prerequisite 2).**
  `offer_curve_smoothing_n` must be identified OFF-residual from MISO's own
  measured unit conduct: the observed number of distinguishable loading levels
  per coal unit from `data/raw/campd-unit-level/*.parquet` hourly grossLoad
  (e.g. distinct occupied deciles of the unit's own operating range on online
  days, capacity-weighted). The derive cites its source data (rule 23), lands
  as a committed artifact, and its n is adopted WITHOUT reference to any C7
  number. FALSIFIER: if the measured level count is ≤ 6 (the fleet already
  bids as many distinct levels as units occupy), the lane dies at P2 — the
  current ladder is measurement-consistent and the defect is elsewhere.
* **P3 (solve-time kill — prerequisite 3, pre-committed now).** In the A/B (if
  reached): if the arm's `R_tot` falls below **0.90** in any year (control
  0.907/0.877/0.952), the arm is REJECTED as re-spending total dispersion for
  organisation. Also standard kills: C1 16/16 holds; COAL_BIT no-overshoot;
  full-balance identity (miso-126(b)); same-HEAD zero-delta control (miso-124);
  LOO within 2023–2025 before any promotion.
* **KILL-4 (unconditional).** Nothing — no n, no share, no parameter — may be
  sized from any Δ measured in this session (rules 1/13/21/24). P2's n comes
  only from the CAMPD conduct derive.

## 3. Rule duties

Rule 15: if every screen kills, this is a no-LP phase and produces no run —
that statement satisfies it. Rule 16/22: 2023–2025 only, one construction over
all three; MISO holds no marker, no holdout year is solved, scored or read.
Rule 19: nothing armed here; an armed arm (post-P2) uses the EXISTING
`offer_curve_smoothing_n/_exp/_mid` fields (no new field), and its licensing
must enumerate the band's existing shapers (take-or-pay discount, measured
online-Pmin band, `coal_econ_srmc_bound` armed on the keeper,
`coal_supply_repricing`, `offer_curve_by_group` econ endpoints) and show
REPLACE-or-RECONCILE, never stacking. Rule 25: MISO-scoped throughout.
Rule 28(b): the tested cell/sub-scalar is stamped in this session whatever the
outcome.
