# ERCOT-99 — offer formation at high net load: why the measured wall is never marginal

**Session 2026-07-23. Baseline keeper: `2026-07-23-ercot98-np6-hsl-fullspan`
(NOT-YET; C3a 2023 −33.5 %, C3b 0.647, C3c 42/181 h · 12/53 · 0/31).** Successor to
ERCOT-98, which refuted the RE / AS-holdout / W-P deliverability suspects and attributed
the 2023 summer tail to offer formation at high net load. This lane measures the reach
gap — why the offer wall the keeper already carries never becomes marginal at the missed
hours — and bounds what an hourly LP can recover.

All probes are no-LP unless noted; every number is from committed inputs / the keeper's
committed hourly sidecars. Probes: `scripts/probes/ercot99_intrahour_bound.py`,
`ercot99_reach_gap.py`, `ercot99_model_offer_curve.py` (+ `ercot99_reanalyze_offer.py`),
`ercot99_real_dam_wall.py`.

## 1. The honest denominator: intra-hour reachability ceiling

C3c scores a **count** (model tail hours vs actual, band [0.5×, 2×]); 2023 PASS needs
≥ 90 model tail hours (actual 181). An hourly perfect-foresight LP prices the hourly-mean
RT, so a tail hour whose mean clears $200 only on a single 15-minute spike is a transient
it structurally cannot reach. Splitting the missed hours by how many of their four
15-minute HB_HUBAVG intervals exceed $200 (`ercot99_intrahour_bound.py`, reconstructed on
the committed CST clock — reproduces the 181 exactly):

| year | actual tail | model caught | sustained-missed (≥3/4) | **reach ceiling** | transient (≤1/4) | current C3c |
|------|------------|--------------|--------------------------|-------------------|-------------------|-------------|
| 2023 | 181 | 40 | 83 | **123** | 14 (10 %) | 42 |
| 2024 | 53  | 8  | 29 | **37**  | 6 (13 %)  | 12 |
| 2025 | 31  | 0  | 25 | **25**  | 2 (6 %)   | 0  |

**Transients are a minor ceiling (6–13 %).** The 2025 collapse (0/31) is NOT transients —
25 of 31 are sustained. Real reachable room exists in all three years; C3c PASS (≥90 in
2023) is inside the ceiling (123). The reachable hours live in the Aug/Sep heat wave.

## 2. The reach gap is DEPTH, not bin-miss

`ercot99_reach_gap.py` (net-load reconstructed from the sidecar — validated: the p97 bin
count is exactly 263 h, matching the surface's logged binding count):

* **92 of 141 missed hours are already in the top net-load bin (≥p97)** where both the
  conditional peak surface and the cleared-share econ floor fire. The wall IS repriced
  there; the model still clears **$70 mean**. 49 hours sit below p97 (a secondary
  bin-conditioning issue), but the dominant miss is depth.
* Model clearing at the missed hours: **p50 $56, p90 $91, max $128** — it never reaches
  $150, let alone $200.

`ercot99_model_offer_curve.py` reconstructs the keeper's P1 offer curve without a solve
(monkeypatch-captures the built fleet + `mc_base` + the summed offer-surface `mc_bid_adjust`,
aborts before the LP; startup markup omitted — a ≤$2 lower bound, cross-check below). Over
the 141 missed hours (`ercot99_reanalyze_offer.py`, clearing = thermal generation = total −
wind − solar, since wind/solar are separate LP variables):

* **Cross-check passes:** reconstructed marginal offer p50 $53.9 vs sidecar hub p50 $55.9,
  |Δ| p50 $1.9 — the reconstruction is faithful.
* Supply-curve shape (mean MW/hr): **$0–50 → 58,263 MW**, $50–100 → 3,015, $100–200 →
  1,257, $200–500 → 1,580, $500–1000 → 347, $1000–VOLL → 1,100. The stack is a flat cheap
  block (~58 GW < $50) with a thin sliver above.
* Thermal clearing 58,086 MW sits at the top of the cheap block → marginal $54–59, with a
  **4.5 GW cushion of cheap capacity ($50–200) above the margin** that must be crossed
  before price can reach $200.

## 3. Why the mechanisms don't reach the cushion

Decomposing `mc_bid_adjust` at the missed hours by tranche:

* **Conditional PEAK surface reprices peak rungs by +$1,076 mean** (to $200–5000) — but
  they sit ABOVE the 4.5 GW cushion, so they are never marginal.
* **Cleared-share ECON floor adds only +$5.4 mean** — it is essentially inert at the
  scarcity hours, so the econ cushion (`econc04/econc05` rows of CC_REGULAR/CT_PEAKER)
  stays at cost.

The suppressor is the **commitment-loading STATE weight**
(`ercot_offer_surface_cleared_share_state`). Its CC series is **w = 0.00 (median) at the
missed hours** (`ercot_commitment_loading_state.json`, 2023) — it fully stands the econ
wall down, on the design premise that RUC/self-committed capacity prices near cost.

## 4. The measured prices contradict that premise

At the 141 missed hours (committed HB_HUBAVG actuals):

* **actual RT p50 $488 / mean $706** (energy-offer-driven: ERCOT-98 measured RTORPA p50
  ≈ $1, so this is SCED λ, not reserve scarcity).
* **actual DA p50 $327 / mean $566** — 93/141 had DA > $200. The DAM cleared HIGH too, yet
  the model misses it ($56).
* The DAM *energy merit* is cheap: `ercot99_real_dam_wall.py` reconstructs the 2023 DAM
  offer stack (coverage 132/141; disclosure spans Nov 2022–Oct 2023) — thermal offered
  ~40 GW, 97.5 % of it < $200, marginal award ~$23–27, but the full-stack max offer is
  $5000 and the DA MCP was $327. So the DAM cleared high because **demand consumed the
  cheap stack and reached the expensive top**, not because gas merit was expensive.

Loaded-at-scarcity capacity therefore prices HIGH (DA $327, RT $488), not near cost. The
state weight's w→0 stand-down is the wrong sign at scarcity: it prices the model's online
gas at cost exactly where reality priced it at the wall.

## 5. The measured-data constraint (what bounds the fix)

The **only 2023 offer corpus on disk is the DAM disclosure** — the 60-Day SCED
(real-time) disclosure is 2024/2025 sample-days only, so the `_rt` ladder is year-scoped
OFF for 2023 and no 2023 RT ladder can be derived. The DAM energy offers are genuinely
cheap; the RT scarcity price is set by real-time re-offers (gas offering $200–5000 in RT
when it offered ~$25 in DA) that were never disclosed for 2023. So merit-repricing to the
measured 2023 offer quantiles cannot by itself reach the RT wall — the residual belongs to
real-time offer formation, and its 2023 measurement does not exist.

Two candidate levers were tested:
1. **The state-weight stand-down** (§3–4) — CONFIRMED as the suppressor. It prices the
   econ wall down at scarcity on a premise the price data falsifies.
2. **AS-contamination of the ladder** (hypothesis) — REFUTED for CC. Re-deriving the
   above-boundary ladder excluding AS-committed MW (`ercot99_as_contamination.py`) leaves
   the CC ladder essentially unchanged and *lowers* its p90 (bin ≥p97: $93 → $54 at median
   gas); only a 6-GWh CT sliver is expensive. The DAM CC offers are genuinely cheap, not
   AS-contaminated. So the wall level cannot be raised by decontamination.

_Levers not available:_ a 2023 RT ladder (no data); any residual-tuned adder/offset
(rule 13); a room-pin to RTOLCAP (ERCOT-79). Cross-applying the 2024/2025 RT ladder to
2023 is the forecast methodology (2026 has no SCED either) but the measured CC RT ladder is
itself cheap (p50 $57, p90 $157), so it does not close the depth gap.

## 6. The mechanism: cleared-share state weight OFF

The state weight `w_c(t) = clip((online_cap − gross)/(online_cap − cleared), 0, 1)` is the
unloaded fraction of above-DA online capability; the floored bid is `base + w·(wall − base)`.
At scarcity `gross → online_cap` so `w → 0` and the row is priced at COST. The measured DA
($327) and RT ($488) at those hours prove the loaded capacity clears at the wall, not cost —
so cost-pricing it is the wrong sign. Turning the weight off prices it at the measured DAM
offer wall instead (`base + (wall − base)`), a structurally more faithful floor (still
bounded by the DAM ladder's own cheap level — the RT scarcity offers are unmeasured for 2023,
§5).

**Probe A — 2023-only, `ercot_offer_surface_cleared_share_state=false`
(`results/calibration/ercot99_probeA_state_off`):**

| metric | keeper (ercot98) | Probe A (state off) |
|--------|------------------|---------------------|
| C3c tail count (settle) | 44/181 (0.24×) | **77/181 (0.43×)** |
| C3c energy-only | 42 | 70 |
| caught (settle) | 41 | 67 |
| C3a (settlement basis, this scorer) | −22.7 % | **−16.1 %** |
| phantom (model>200, actual≤200) | 3 | 10 |

The gain is **entirely in the ≥p97 bin** (reach-gap: bin-3 catches 38 → 61, missed-hour
mean hub $70 → $133; bins 0–2 unchanged — no moderate-day over-lift). It is a real,
scarcity-located improvement, and it does not reach C3c PASS (needs 90) — the residual
above it is the unmeasured 2023 RT re-offer wall (§5), which per rule 1 stays attributed,
not tuned.

**Full-span candidate `2026-07-23-ercot99-state-off-fullspan`** (keeper config,
`cleared_share_state` True → False, single flag; run_config verified). Official
`calibration_verdict` vs the ercot98 keeper:

| criterion | keeper (ercot98) | candidate (state off) |
|-----------|------------------|-----------------------|
| C3a mean LMP 2023 | −33.5 % | **−26.3 %** |
| C3b NRMSE 2023 | 0.647 | **0.520** |
| C3c tail 2023 | 42/181 (0.23×) | **70/181 (0.39×)** |
| C3c tail 2024 | 12/53 | 12/53 (unchanged) |
| C3c tail 2025 | 0/31 | 0/31 (unchanged) |
| C1 / C2 / C4 / C5a | PASS | PASS |
| C7 (D-1) / C8 (D-2) | PASS | PASS |
| DOF ledger | 9 entries / 8 residual | 9 / 8 (no new DOF) |
| determination | NOT-YET (C6 gov) | NOT-YET (C6 gov) |

**Why only 2023 moves (and why that satisfies LOYO).** 2024/2025 use the SCED/RT ladder
(`ercot_offer_surface_cleared_share_rt=True`, mode replace), which is measured 2024/2025
and — by design — is NOT state-weighted; only 2023 (no RT ladder, DAM-basis wall) carries
the state weight. So the flip reprices 2023 alone and leaves 2024/2025 byte-identical
(identical C3c/C3a confirm it). The change adds no fitted parameter and no year-specific
tuning (DOF ledger unchanged), so the classic leave-one-year-out is degenerate: the 2023
correction is justified by 2023's OWN measured DA/RT prices, and 2024/2025 are untouched —
there is no in-sample-gain / held-out-degradation trade to overfit.

**Disposition.** Keeper UNCHANGED (`2026-07-23-ercot98-np6-hsl-fullspan`, NOT-YET) pending
owner adjudication. The candidate is the structurally more faithful run (it removes the
state weight's falsified cost-pricing of loaded-at-scarcity gas), registered as the
successor; promotion is the owner's call. It does not clear C3c — the residual is the
unmeasured 2023 RT re-offer wall and the depth of the cheap merit stack, both bounded by
what the measured DAM offers contain (§5), not a thing to tune.
