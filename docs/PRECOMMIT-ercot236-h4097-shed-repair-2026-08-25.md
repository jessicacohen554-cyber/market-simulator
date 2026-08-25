# PRECOMMIT — ercot-236: the h4097 manufactured-shed object — diagnosis bars, conditional repair spec, and the conditional (24, 33] re-bracket, fixed before any solve

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** the ercot-235
promotion addendum's NAMED SUCCESSOR ("the h4097 manufactured-shed object …
the one bounded object between this keeper and a clean C3a-2023 PASS") under
the owner's standing 2023-DISCRETE-CONFIG charter (verbatim in the ercot-235
log entry: solve 2023 for its own ECRS-era conditions; rule-16 waiver
INVOKED; Q-B/R-A superseded by the owner for 2023-targeted rounds — cited,
not re-derived). · **Keeper (2023):** `2026-08-25-235-2023-discrete-k24`
(bundle `results/calibration/ercot235_r10`); the cross-year
`2026-08-25-234-eastex-identity` untouched as the 2024/2025 reference.
· **Scorer validation (this session, before this precommit):**
`ercot226_official_score.py --bundle results/calibration/ercot235_r10
--years 2023` reproduces **−13.5 % / 0.186 / 180 exactly**; the
`--validate-keeper` expectation re-pointed to the current keeper (ercot-234
precedent) and passing.

**Discipline:** years = {2023} ONLY; ERCOT-only (rule 25); solves sequential
(rule 12 — one 2023 solve peaks ~11 GB of 15); every solve precommitted here
or in a recorded amendment BEFORE it runs; kills direction-blind; every
completed run registered (rule 15 — winner sidecar-mapped, non-winner grid
points keep committed point-score JSON under the ercot-235 pattern); scratch
prefix `results/calibration/ercot236_*` (gitignore rule added with this
precommit); no CI jobs; repair must be STRUCTURAL — never an hour mask, a
shed-hour exemption, or any h4097-keyed constant.

## 0. The object (facts carried in, none re-measured)

At k_peak > 24 on the ercot-235 discrete-2023 surface, the reshaped price
path manufactures exactly ONE new shed hour — h4097, June 20 17:00 CPT on
the model clock — growing with k: R11 (k=27) shed {4097}; R8 (k=30)
35.95 MWh; R9 (k=45) 310.87 MWh. The killed R8/R9 land INSIDE both 2023
bands (−9.3 %/0.119; +0.8 %/0.189), so the band is reachable once the object
is repaired. The r1–r9/r11 grid bundles were local to the dead container;
only their committed `ercot235_point_score.json` records remain.

## 1. Phase-0 basis (ZERO-SOLVE — keeper `ercot235_r10` committed sidecars, read this session)

Measured from `hourly/system_2023.parquet`, `storage_2023.parquet`,
`reserve_family_2023.parquet`, `adaptive_2023.parquet` at h4085–4105:

- **h4097 is the year's deepest scarcity hour at k=24:** lw price
  **$4,778.26**, ordc_adder $7.71 ⇒ **energy λ = $4,770.55**, all 7 zones
  price-coupled (identical zonal prices — no transmission separation).
  Demand peak 78.4 GW at h4095–4096; window h4093–4100 prices $211 → $4,778
  → $212.
- **The zero-solve crossing prediction (H-OFFER):** the h4097 marginal
  energy offer scales with k_peak, so it crosses VOLL ($5,000 — the model's
  slack cost AND ERCOT's system-wide offer cap, `iso_configs`: "ERCOT VOLL:
  $5,000/MWh — matches the day-ahead system-wide offer cap") at
  **k\* = 24 × 5000/4770.55 = 25.15** — INSIDE the measured shed onset
  interval (24, 27]: R10 (k=24) clean, R11 (k=27) shed. An LP whose
  remaining supply at one hour is offered above the slack cost sheds by
  OPTIMALITY — physically-available capacity goes undispatched because its
  tuned offer exited the admissible domain. Growth with k follows: deeper
  tranches cross the cap as k rises (35.95 MWh at k=30 → 310.87 at k=45).
- **Sanity check carried from the campaign:** the round-3 precommit
  amendment PROMISED a "max peak-tranche offer $/MWh (must stay ≤ VOLL
  $5,000)" report; the sweep driver never implemented it (verified: no such
  key in any committed `ercot235_point_score.json`). This session implements
  that report (§4 side reporting).
- **Storage at the window (keeper):** discharging 603/1,025/707 MW at
  h4096–4098, charge 0; NonSpin held collapses to 46–416 MW through the
  event; ORDC shortfall 4.7–5.8 GW; adaptive event floor $0 across the
  window. No zero-solve evidence for or against the storage hypothesis — it
  is adjudicated by D-1 below, not assumed.

**Competing hypotheses fixed ex ante** (the handoff names H-STORAGE as
likely; phase-0 arithmetic favors H-OFFER; the A/B decides):

- **H-OFFER** — tuned peak-band offers cross VOLL at h4097; the LP prefers
  slack (VOLL) to supply offered above VOLL. Repair class: offer-domain cap
  (§3).
- **H-STORAGE** — the higher price path re-times storage cycling and leaves
  SOC empty at the June-20 evening ramp. Repair class: would need its own
  spec (amendment; §3 does NOT cover it).
- **H-RESERVE** — the co-opt holds reserves through the shed (the ercot-223
  signature: Δheld == shed exactly). Repair class: would need its own spec
  (amendment).

## 2. D-1: the diagnosis solve and its bars (ONE 2023-only solve)

**Solve D:** `replay_keeper.py results/calibration/ercot235_r10 --out-dir
results/calibration/ercot236_diag_k30 --years 2023 --set
offer_curve_by_group=<r10 dict with peak/phys_peak/peak_ladder multipliers
scaled ×30/24>` — i.e. the R8 point (k_peak = 30, k_eh = 1) re-solved at
HEAD. Local probe bundle (gitignored).

**Bar D-0 (reproduction):** the 2023 shed hour set must be exactly
**{4097}**. Shed MWh and officials are REPORTED against R8's committed
record (35.95 MWh; −9.3 %/0.119/180) with no bar — HEAD has moved since the
campaign (absorbed merges), so magnitude drift is reported, not gated. If
the shed set is NOT {4097}, STOP: no repair is built; the drift is diagnosed
and carded before anything else runs.

**Bar D-1 (mechanism attribution, from the k=24 keeper vs k=30 diag
sidecars at h4097 — the energy-balance decomposition):** with demand
identical by construction, the shed must be paid for by a supply component.
Compute Δ = (k=30 diag) − (k=24 keeper) at h4097 for: total thermal MW
(`class_hourly` sum over thermal classes), storage discharge − charge
(`storage`), wind+solar (`class_hourly`), and reserve held MW per family
(`reserve_family`). Attribution verdict (direction-blind; tolerance ±20 % of
the diag shed MWh):

- **O1 CONFIRMS H-OFFER** iff Δthermal ≤ −(shed − tol) (thermal supply the
  k=24 solve dispatched at this hour goes UNDISPATCHED at k=30 while the
  zone sheds at price = VOLL — by LP optimality undispatched headroom at a
  $5,000 price means its offer ≥ $5,000) AND every zone prices ≥ $4,999 at
  h4097 (no transmission separation — rules out an import-limited shed).
- **S1 CONFIRMS H-STORAGE** iff Δ(discharge − charge) ≤ −(shed − tol) at
  h4097 with the h4080–4096 cycling visibly re-timed (reported).
- **R1 CONFIRMS H-RESERVE** iff Δheld (any family, or the sum) ≥ +(shed −
  tol) at h4097 (the ercot-223 Δheld == shed signature).
- Mixed outcomes (no single component ≥ 80 % of the shed): report the full
  decomposition and STOP for an amendment naming the joint mechanism before
  any repair is built.

Window reporting h4085–4105 for all four components both runs (the handoff's
A/B), whatever the verdict.

## 3. The repair spec — CONDITIONAL on O1 (H-OFFER confirmed)

**The structural statement (rule 1):** ERCOT caps every SCED energy offer at
the system-wide offer cap (SWCAP; $5,000/MWh in 2023 — PUCT's post-Uri
Phase-1 HCAP, which the energy-only design sets equal to VOLL, per the
existing `iso_configs` citation). A submitted offer above $5,000 cannot
exist; and firm-load shed is an EEA emergency action, never an economic
outcome of a high offer — SCED dispatches every offered MW before load is
shed. The model's tuned offer surface (tranche multipliers × heat rate ×
fuel) has no such cap, so a large enough multiplier walks implied offers
past VOLL and manufactures economically-optimal shed with no market
analogue. The repair brings the model's offer domain back to the market's:

- **New `ScenarioConfig` field `ercot_offer_swcap_clip: bool = False`**
  (default OFF — every existing bundle replays byte-identically; ERCOT-only
  gate, rule 25). Registered surface (rule 24): armed via the run's
  `run_config`.
- **New constant `ERCOT_SWCAP_SHED_TIEBREAK_EPS = 0.01` ($/MWh,
  `constants.py`, cited):** the clip level is `voll − eps`, keeping dispatch
  STRICTLY preferred to shed at the cap (an offer clipped to exactly VOLL is
  LP-degenerate against slack; the ε is a tiebreaker in the R-EPSILON
  storage-ε class, not a fitted value).
- **Seam:** `pipeline/solve.py::run_energy_solve` — `mc_base` clipped at
  entry (P0 sees the same admissible offer domain; the P0 bit-identity proof
  is already forfeited on this lineage, ercot-188/E2) and the fully-
  assembled P1 `mc_bid` clipped LAST (after markup, additive adjusts and the
  bid-max target), so "no thermal energy offer above the cap" is the
  invariant the LP actually receives. Flag-off paths byte-identical (a
  `None`-guard clip, the seam family's existing pattern).
- **No window, no hour selection, no h4097 reference anywhere in the code
  path** — the cap is an offer-domain constraint applied to all 8,760 hours
  identically; rule 17 is satisfied by construction (driver: the PUCT SWCAP;
  window: every hour, by market design; forward story: regenerates from the
  configured cap in any forecast year).
- **Unit test** (`tests/`, trivial-case-first): 1 gen, 1 zone, 24 h; a gen
  offered above VOLL sheds with the flag off and dispatches with it on.

If D-1 lands S1 or R1 instead, §3 is VOID: the session records the verdict
and precommits the alternate repair in an amendment before building
anything.

## 4. Verification legs and the conditional re-bracket (the handoff's priority B)

All solves 2023-only, sequential, replayed from the r10 meta with `--set`;
kills evaluated by the ercot-236 scorer (the ercot-235 per-point scorer
adapted — same official basis, same kill definitions, same baseline
`results/calibration/ercot234_eastex_identity` for cross-campaign
comparability, PLUS each point reports vs the r10 keeper, h4097 slack
explicitly, and the §1 max-offer report: max zonal energy λ (price −
ordc_adder), count of hours λ ≥ $4,999, and the clipped-tranche share when
the clip is armed).

- **V-0 (inertness at the keeper): k=24 + clip.** PASS bar: official 2023
  scores IDENTICAL to the keeper (−13.5 % / 0.186 / 180) and shed set empty.
  Rationale: the keeper's max energy λ is $4,770.55 < $4,999.99, so the clip
  must be a no-op at k=24 up to marginal-tie reshuffle; a moved official is
  a STOP (the clip is not the mechanism §3 claims).
- **V-1 (the repair leg): k=30 + clip.** PASS bar: 2023 shed set EMPTY;
  officials reported against R8's (−9.3 %/0.119/180; expected ≈ equal — the
  unclipped run's shed hour already priced at VOLL, so the price path is
  near-identical and only the ~36 MWh of dispatch returns).
- **Re-bracket grid (runs ONLY if V-0 and V-1 both pass): k_peak ∈ {27, 33}
  + clip** (30 + clip is V-1; the handoff precommits {27, 30, 33} in
  (24, 33]). KILLS per PRECOMMIT-ercot235, unchanged: **G-SHED-NEW** (any
  2023 shed hour — the keeper set is empty, so any shed kills),
  **G-OFFSEASON** (any off-season month lw-price > $5/MWh further from
  actual than the ercot-234 baseline's), **G-COAL148** (2023 coal rise vs
  the ercot-234 baseline > 0.5 TWh).
- **Selection (fixed ex ante):** among ALL clean clip-armed candidates
  {27, 30, 33} and the incumbent keeper (k=24), **min |official C3a-2023|,
  tiebreak lower C3b-2023**. A candidate beating the incumbent is REGISTERED
  (rule 15) with the clip flag and k in its run_config, the DOF ledger
  carried (k_peak stays the ONE residual-identified scalar, re-selected on
  the repaired surface — n_residual unchanged at 7; the clip is a structural
  cap, not a fitted parameter), and put to the owner under the standing
  signature ("If structural integrity improves but gates regress that may
  still be a keeper"), recorded exactly as the ercot-235 promotion addendum
  did. If NO candidate is clean or none beats the incumbent, the keeper
  stands and the k→C3a response curve is reported (priority C).
- **Side reporting per point:** monthly lw table, band coverage vs actual
  77/43/59, G-SPUR banded AND lidless (the ercot-225 gate card is STILL
  AWAITING SIGN-OFF since 2026-08-21 — re-surfaced to the owner in this
  session's report; no gate file edited), C3c tail count, coal TWh vs both
  baselines, h4097 slack, max energy λ.

## 5. Matrix and registration duties (fixed now)

- Rule 28(c): `ercot_offer_swcap_clip` is a new solve-affecting
  `ScenarioConfig` field ⇒ its mechanism row is added to
  `docs/codebase-site/data/mechanism-matrix.js` + a cell line in EVERY ISO
  shard in the SAME commit (ERCOT tested this session; the other five ISOs
  `U` — untested, rule 25: the verdict never transfers).
- Rule 28(b): the ERCOT cell verdict is stamped in
  `docs/codebase-site/data/mechanism-matrix/ERCOT.js` in this session,
  whatever the outcome (K/R/I per the D-1/V legs).
- Rule 15: winner registered same-session via the calibration-report path;
  non-winner points keep committed `ercot236_point_score.json` under
  `KEEP_REQUIRED_UNMAPPED_BUNDLES` entries (the ercot-235 pattern).
  `.gitignore` gains `results/calibration/ercot236_*/` alongside this
  precommit.
- Rule 27: every pushed file ≥300 lines blob-verified after push.
- Amendments: each solve round's result is RECORDED in this file before the
  next round runs — never silently applied.

## ROUND RESULTS (amendments below — none at initial push)

### AMENDMENT 1 — D-0/D-1 measured (recorded before any V-leg ran): O1 CONFIRMS H-OFFER

**D-0 (reproduction): PASS, exact.** The diag solve (`ercot236_diag_k30`,
k=30 at HEAD) reproduces R8's committed record to the digit: shed set
**{4097}**, magnitude **35.948 MWh** (R8: 35.95), officials **−9.3 % /
0.119 / 180** — zero HEAD drift since the campaign.

**D-1 (attribution): O1 — H-OFFER CONFIRMED.** The h4097 energy-balance
decomposition (k=30 diag minus k=24 keeper; `ercot236_d1_diagnosis.json`):

- **Δthermal = −48.28 MW** — thermal supply the k=24 solve dispatched at
  this hour goes UNDISPATCHED at k=30 while every zone prices exactly
  **$5,000.00 = VOLL** (zone min = max = 5000.0; no transmission
  separation). By LP optimality, undispatched headroom at a $5,000 price
  carries an offer ≥ $5,000 — the offer domain, not capacity, is what ran
  out. |Δthermal| = 134 % of the shed, clearing both the −(shed − tol) bar
  and the single-component-≥ 80 % reading.
- **Δ(net storage discharge) = +12.33 MW** — storage discharges MORE at
  k=30, the OPPOSITE of H-STORAGE's starvation signature. S1 REFUTED.
- **Δrenewables = 0.0.** Balance closes exactly:
  −48.28 + 12.33 = −35.95 = −shed.
- **Δ(total reserve held) = 0.0** — R1 REFUTED. Reported color: the co-opt
  swaps exactly 35.95 MW from NonSpin to RegUp at the boundary (net zero);
  a reallocation at the cap, not withholding.
- The §1 max-offer report on the diag point: max energy λ **$5,000.0**,
  hours λ ≥ $4,999: **1** (h4097 itself — the shed hour prices at VOLL).

The §1 zero-solve crossing prediction (k\* = 25.15 ∈ (24, 27]) stands
corroborated. **§3 is LIVE**: the repair was built exactly as specified
(commit 63750d3 — `ercot_offer_swcap_clip` default off,
`ERCOT_SWCAP_SHED_TIEBREAK_EPS` 0.01, the two `run_energy_solve` clips,
unit tests 7/7, matrix row + shard cells). Two recorded deviations, neither
substantive: (a) the non-ERCOT shard cells are stamped `·` (n/a) per the
ISO-exclusive convention (the `ercot_tie_zonal_interchange` precedent), not
`U` as §5 sketched — the mechanism is ERCOT-gated, so n/a is the truthful
mark; (b) the repair CODE was committed (default-off, byte-identical off,
provably inert on every existing bundle) before this amendment's push, to
keep the tree clean under the session's push discipline — ARMING waited for
this verdict, no solve with the flag on preceded it. The §4 V-legs launch
next, gated mechanically (V-0 STOP on any moved official; V-1 STOP on any
shed; re-bracket only after both pass).
