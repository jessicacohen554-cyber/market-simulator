# MISO scarcity tail (C3c) — external validation of the ledgered residual + forecast-mode ORDC note

**Date:** 2026-07-20. **Session:** miso-82 (`claude/miso-82-frontier-declaration`).
**Status:** docs-only lane finding — NO solve, NO intake, quarantine untouched.
**Companion:** `docs/multi-iso/miso-scarcity-tail-diagnosis.md` (the 2026-07-02
root-cause + event anatomy; this doc adds the external-literature validation and
the current-keeper empirical confirmation).

## Why this exists

The MISO keeper (`2026-07-20-miso-81-phantom-outage`) is NOT-YET on exactly two
ledgered fails: **C3a-2025** (−14.8%) and **C3c** (model 0/6/0 scarcity hours vs
actual RT 30/37/88 for 2023/24/25). The owner asked the sharp question — *could
layering scarcity pricing close C3c, and where are the missing scarcity hours?*
This doc records the answer, now grounded in primary-source literature (a
deep-research pass, 24/25 claims confirmed at 3-0 adversarial votes, 17 primary
sources) and in the miso-81 keeper's own hourly output.

## 1. The current-keeper empirical confirmation (no re-solve)

Taking the miso-81 keeper's committed `hourly/system_2025.parquet` and the
Indiana-Hub actual tail (`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`),
in the **88 actual RT>$200 hours of 2025** the model prices:

| model price in those 88 hours | value |
|---|---|
| median (energy) | **$50** |
| 90th pct | $83 |
| 99th pct | $125 |
| max (energy) | $157 |
| reserve adder fires | **2 of 88** hours |
| energy+reserve > $200 | **1 of 88** hours |
| load-shed (slack>0) | **0** hours |

The model is not sitting *just under* the $200 threshold waiting for a nudge —
it clears at mid-merit gas (~$50) while the market hit $200–$1,783. The DA column
in those same hours is decisive: e.g. hour 6425 **RT $1,598 / DA $99**; hour 2274
RT $876 / DA $52; hour 5849 RT $810 / DA $53. The *day-ahead* market — which has
full unit commitment, ramp modeling and network — never saw ~90% of these. A
deterministic perfect-foresight hourly LP ≈ the DA market, so it cannot
manufacture them.

This reproduces the 2026-07-02 bind-gate diagnosis on the current keeper: MISO's
deliverable reserve stays ≥11 GW against a ~4.4 GW requirement in every event
hour; the LP always re-times energy to relieve any zonal shortfall for ≤$23/MWh,
always cheaper than the $200 ORDC step, so the shortage steps never engage.

## 2. What the literature says MISO's tail actually is

The decisive external finding: **MISO's scarcity tail is not an emergent
marginal-cost outcome even in MISO's own clearing engine.** It is an
administrative stepped Operating Reserve Demand Curve (ORDC) built from Reserve
Constraint Penalty Factors (RCPF), co-optimized natively inside the SCED LP.

- **ORDC / RCPF structure (2023–2025 window):** two energy steps at
  **$1,100 / $2,100/MWh** anchored to a **$3,500/MWh VOLL**; per-product reserve
  curves — Spinning $65 (0–10% short) / $98 (>10%), Regulation ~$140 avg (2024
  $139.76, varies monthly with gas), Short-Term Reserves multi-step up to $500
  (raised from $100 in Nov 2022). Sources: MISO BPM-002 Attachment B §5.4;
  Potomac Economics (IMM) 2024 MISO State-of-the-Market Appendix; OSTI 2424806.
- **The tail is a stochastic-risk demand curve, not a dispatch output.** MISO's
  ORDC is itself derived from a **Monte-Carlo loss-of-load-probability (LOLP)
  simulation** over net-load and generator-outage/derate uncertainty in a
  **10–30 minute lead window**, scaled by a $35,000/MWh Operating Reserve Target
  Cost. Source: MISO Scarcity Pricing White Paper (March 2024) §3.2.1.
  **This is the crux:** the real MISO tail prices *probabilistic short-term
  risk*, which a perfect-foresight hourly LP structurally does not contain. The
  mechanism producing the real tail is an uncertainty calculation, not a
  supply/demand crossing our LP can reach.
- **ELMP (Extended LMP, live 2015)** is a pricing-only engine on single-interval
  DA (1h) / RT (5min) dispatch: an LP relaxation approximating convex-hull
  pricing (binary commitment relaxed to [0,1]) that lets online — and, during
  scarcity/constraint violations, *offline* — fast-start units set price. It
  changes pricing, not commitment/dispatch. Sources: MISO 2014 ELMP Design
  Overview; optimization-online #7800; Potomac 2024 SOM.

## 3. The limitation is documented and universal (not a MISO-specific gap)

- **23 of 23** surveyed operational/production-cost models default to hourly +
  deterministic; only 11 support sub-hourly, only 8 stochastic (Oikonomou et al.,
  arXiv 2101.02303).
- Deterministic perfect-foresight LPs **systematically under-produce the price
  spike tail**: PyPSA-Eur's 2022 hindcast reproduced *no* intra-day spikes even
  with dynamic fuel prices (arXiv 2606.16486); deterministic rolling-horizon PCMs
  "systematically under-predict RT prices" in storage systems
  (IOPscience 10.1088/2753-3751/ae3f34).
- Techniques that narrow the miss are **modest**: limited-foresight rolling-horizon
  moved multi-year hourly-price SMAPE only 21.3% → 20.8%. The real closers are
  stochastic Monte-Carlo over outages/forecast-error, 5-minute resolution, or
  embedding the administrative ORDC directly.
- Scarcity **binds rarely** — MISO had operating-reserve shortages on **7 days in
  fall 2025** (Potomac IMM Fall 2025 Quarterly) — so studies typically price
  energy + reserve/capacity adequacy via the ORDC rather than replicating the RT
  tail hour-for-hour.

## 4. Conclusion — the ledgered tail is at the representation frontier

"Layering scarcity pricing" for MISO = embedding the published ORDC/RCPF as a
post-solve reserve-demand-curve adder (the NYISO/NEISO RCPF mechanism). §1 shows
it would fire in ~2 of 88 hours because the model's reserves do not go short; §2
explains why at the mechanism level — MISO's ORDC prices *probabilistic* risk our
perfect-foresight LP does not experience. To actually reproduce the tail you would
have to manufacture the uncertainty (an LOLP/forecast-error-inflated reserve
requirement or a stochastic net-load draw) — either out of representation
(perfect-foresight hourly) or a fit to the residual, which CLAUDE.md rules #1/#10
forbid. This is why {C3a-2025, C3c} is **ledgered irreducible**, and the finding
is now externally grounded rather than asserted.

The reachable structure has already been built on record: reserve deliverability
(miso-39), Midwest sub-regional reserves (miso-71), measured reserve requirements
(miso-56) — each adopted per rule #1 even though the residual did not move. No
untried *admissible* pricing layer closes C3c.

## 5. Forecast-mode note — MISO VOLL/ORDC parameter change (forward years only)

MISO is mid-reform. The $3,500 VOLL / $1,100–$2,100 two-step ORDC above is correct
for the **2023–2025 backcast window** (and the 2024 SOM). For **forecast-mode**
runs pricing MISO scarcity, the FERC-approved parameters differ:

- **VOLL raised $3,500 → $10,000/MWh** — FERC-approved, **effective 2025-09-30** —
  serving as the LMP/MCP price cap and administrative load-shed price.
- **New $6,000/MWh ORDC upper limit** (below the $10,000 VOLL cap), letting prices
  rise toward VOLL as reserves deplete.
- **Two ORDC floor steps lowered to $600 / $1,100/MWh.**
- The $35,000/MWh figure is the **LOLP-scaling reserve target cost**, distinct
  from the $10,000 VOLL price cap — do not conflate.

Sources: MISO Nov 2024 Updated Shortage Pricing White Paper; MISO April 2024 MSC
Scarcity Pricing White Paper (VOLL & ORDC). **Action for the forecast lane:** when
MISO forecast scarcity is priced (forward `mode="forecast"` years spanning
2025-09-30+), use the $10,000/$6,000/$600-$1,100 parameters, not the backcast
$3,500/$1,100-$2,100 curve. This note is filed for the forecast program; it does
NOT change any backcast keeper (the 2023–2025 window is entirely pre-reform).

## Sources (primary, deep-research verified 2026-07-20)

- MISO BPM-002 Attachment B §5.4 (market-wide ORDC construction inside SCED)
- MISO Scarcity Pricing White Paper, March/April 2024 (LOLP-derived ORDC; VOLL/ORDC reform)
- MISO Updated Shortage Pricing White Paper, Nov 2024 ($35,000 target cost; $6,000 cap)
- MISO 2014 ELMP Design Overview
- MISO / optimization-online #7800 (ELMP as convex-hull LP relaxation)
- Potomac Economics (MISO IMM) 2024 State-of-the-Market Appendix; Fall 2025 Quarterly
- OSTI 2424806 (MISO co-optimized energy+reserve SCED)
- Oikonomou et al., arXiv 2101.02303 (23-model PCM survey; perfect-foresight limitation)
- PyPSA-Eur 2022 hindcast, arXiv 2606.16486 (spike-tail under-production; rolling-horizon SMAPE)
- IOPscience 10.1088/2753-3751/ae3f34 (deterministic rolling-horizon RT under-prediction)

Coverage caveat: the pass did not surface vendor-specific docs for
PLEXOS/Aurora/GE MAPS/PROMOD/Dayzer/EnCompass/Ascend (vendor pages
unreliable/paywalled); the 23-model survey is the closest proxy. The MISO
market-design and generic-LP-limitation evidence is primary-sourced and strong.
