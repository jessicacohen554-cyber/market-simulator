# MISO 2025 import starvation — root cause and the measured seam-ladder fix

**Date:** 2026-07-07. **Lane:** L-14 MISO, gap register G-23 residual
(re-attributed after the miso-45 CC-capacity cap closed the C1 core).
**Baseline:** keeper `2026-07-07-miso-45-cc-capacity` — 2025 gross imports
**3.4 TWh** vs actual net imports **19.0 TWh**, with the displaced energy
served by +22 TWh of PRB coal (the C2 sysvol FAIL in a dear-gas year). This
doc records the measured diagnosis, why the seam's spot-spread price
mechanism is the root cause, the structural fix (measured per-seam Q-Q band
ladders, the NEISO audit-C-6 pattern), and its admissibility. Zero
parameters fitted to any residual (rules 1/11/23).

## 1. Measured anatomy of MISO's interchange (EIA-930 BA-to-BA, in-repo)

Net import by counterparty, TWh (+ = MISO imports; `MISO interchange
hourly.parquet`):

| DIBA | 2023 | 2024 | 2025 | model seam |
|---|---|---|---|---|
| PJM | +33.49 | +27.11 | +24.60 | PJM |
| IESO | +7.44 | +5.17 | +3.42 | PJM (pooled) |
| SOCO | +5.24 | +5.43 | +5.82 | South |
| AECI | +1.02 | +3.07 | +3.89 | South |
| SPA | +1.81 | +2.07 | +1.69 | SPP |
| MHEB | +5.39 | +3.00 | **−0.99** | Manitoba firm block |
| SWPP | −0.85 | −2.44 | −0.73 | SPP |
| LGEE | −2.15 | −2.50 | −2.12 | South |
| TVA | −13.48 | −17.85 | −16.62 | South |
| **total** | **+37.9** | **+23.1** | **+19.0** | |

The eastern (PJM+IESO) seam is the whale: +40.9 / +32.3 / +28.0 TWh. South
nets a reliable −9 to −12 TWh export (SOCO/AECI import inside it, TVA/LGEE
export); SPP nets ≈ 0; Manitoba flipped to net *export* in drought-2025
(the model's firm block carries the measured +224 MW import but has no
export path — a known ~2-3 TWh boundary limitation, recorded below).

## 2. Why the seam starves: measured flow is not spot-spread arbitrage

Joint statistics of the measured PJM-proper flow against the measured
hub-mean RT LMP spread (MISO − PJM, `actual_lmp_hourly_{MISO,PJM}.parquet`):

| year | net TWh | flow p10/p50/mean MW | hours flow>0 | mean spread | corr(flow, spread) | import MWh at spread≤0 | at spread≤$2 |
|---|---|---|---|---|---|---|---|
| 2023 | +33.5 | 1744 / 3810 / 3824 | 99.5% | +3.35 | +0.06 | 31% | 46% |
| 2024 | +27.1 | 1053 / 3054 / 3090 | 97.9% | +1.27 | +0.10 | 38% | 52% |
| 2025 | +24.6 | 865 / 2727 / 2809 | 97.5% | **−0.04** | +0.06 | 46% | 56% |

Three facts kill the spot-spread mechanism as the seam's price model:

1. **The flow is an around-the-clock scheduled base** — importing in
   97.5-99.5% of ALL hours at 2.8-3.8 GW mean (firm PTP transmission
   service, grandfathered agreements, JOA firm flow entitlements, DA
   financial schedules), not a flow that switches with the hourly spread.
2. **Hourly flow is uncorrelated with the hourly spread** (r ≈ +0.06): in
   2025 the annual mean RT spread is **$0.00** and 46% of the import MWh
   moved in hours where MISO was *cheaper* than PJM — yet 24.6 TWh flowed.
3. **The hurdle dead-band deletes half the real flow by construction**:
   46-56% of measured import MWh moves at spreads inside/below the $2
   hurdle, exactly the hours a hurdle-gated arbitrage seam clears nothing.

So in 2023 (spread +3.35) the formula seam happened to deliver (model net
−30.5 vs −37.9 actual), but as the spread compressed to zero through
2024-2025 the modeled seam starved toward nothing (2025: −1.2 net model vs
−19.0 actual; 3.4 TWh gross) while the real scheduled base kept flowing.
This is a *representation* error in the seam's price formation, not a level
mis-anchor: the `hr_by_year` levels and the border re-anchor are measured
and fine; the clearing RULE (import only when spread > hurdle) is what
contradicts the measured seam.

The SPP seam proves the counterfactual: MISO's measured RT premium over SPP
averaged +$8 to +$16/MWh — a pure spread seam would import ~35 TWh/yr over
its 4 GW interface — yet the measured SPP seam nets ≈ 0. The measured
(month × hour-of-day) deliverability envelopes (`miso_seam_flow_limit`,
already in the keeper) correctly police that side. The envelopes are not
the starvation; the price rule on the PJM seam is.

## 3. The fix: measured per-seam Q-Q band ladders (`miso_seam_measured_ladder`)

`scripts/derive_miso_seam_ladders.py` — the NEISO audit-C-6 closure pattern
(`derive_neiso_import_tranches.py`) applied to MISO's three priced seams on
their existing 8-band structure. For each seam and direction, band *k*'s
price is the measured MISO **DA** hub LMP quantile whose exceedance duration
equals the measured duration of the seam flowing deeper than the band's
midpoint (external transactions schedule in the DA market):

    import band k:  pi_k    = Quantile_DA(1 − P[flow >  L_k])
    export band k:  sigma_k = Quantile_DA(    P[flow < −L_k])
    L_k = (k − 0.5) × interface_limit / 8

The ladder is the seam's *revealed supply curve*: the deep firm base rungs
price low (the 2025 PJM base band at $21.82 — flowing in ~99% of hours, its
revealed reservation price is the DA distribution's cheap tail), the
marginal rungs price high ($121.91 at the 7 GW depth), so the LP —
still clearing every band **economically against its own hourly internal
price** — reproduces the measured flow duration curve when its internal
price distribution is faithful. Band capacities, the measured seam
envelopes, the $2-hurdle-free static prices (the ladder embeds delivery
costs), Manitoba's firm block: all unchanged. Registry:
`interchange_config.MISO_SEAM_LADDER_BY_YEAR`; injector:
`transmission.inject_miso_seam_ladder_prices` (runs last among the seam
price overwrites; displaces `miso_pjm_border_anchor` /
`miso_pjm_lmp_import_pricing` on the rows it covers — alternatives, never
stacked).

**Offline P9 validation (measured-DA-driven, the derivation sanity check):**

| seam | 2023 sim vs act TWh | 2024 | 2025 | duration RMSE |
|---|---|---|---|---|
| PJM | +40.7 / +40.9 | +32.2 / +32.2 | **+28.0 / +28.0** | 270-290 MW |
| SPP | +1.0 / +1.0 | −0.4 / −0.4 | +1.0 / +1.0 | ~145 MW |
| South | −9.3 / −9.4 | −11.7 / −11.8 | −8.9 / −9.0 | 130-155 MW |

Hourly correlation is weak by construction (the measured flow is
price-decorrelated — §2), so the *duration curve* is the honest reproducible
structure; hourly placement inside it is carried by the (month × hod)
envelopes and the model's own price shape. That is the same representation
bound the scarcity-tail diagnosis records for RT transients: a mechanism
tuned to reproduce hour-by-hour scheduled flow would fail rule 13.

## 4. Admissibility (rules 11/13/14/23) and what this is NOT

- **Measured-behaviour identification, frozen formula, zero fitted
  parameters** (rule 23): every number is a quantile of a measured series
  (EIA-930 flows × MISO DA LMP) at a structurally fixed depth grid; the
  ladders re-derive only when the source data extends. Nothing reads a model
  residual; the derive script never sees a solve.
- **Rule-13 test:** the ladder regenerates for a forward year (the pooled
  2023-2025 ladder printed by the derive script is the persistent revealed
  seam structure; forecast years keep the gas-elastic reference-price
  formula — the same two-track design as `hr_by_year`), and it responds to
  changed conditions (the LP clears bands on its own price: a tighter model
  year imports deeper along the same ladder, a cheap year backs the base
  off). Contrast the REJECTED `miso_firm_import_floor` (min_gen pin of p10
  measured flow — flows regardless of model prices, rule-13-forbidden): the
  ladder *prices*, never forces; at internal prices below $21.82 even the
  2025 base band backs off.
- **Precedent:** the NEISO keeper's C-6 measured ladders (same construction,
  registered 2026-07-06) and the accepted measured seam envelopes / measured
  border-hub pricing already on the MISO seam.
- **Rule-14 boundary notes:** (a) IESO pools into the PJM seam per
  `MISO_SEAM_DIBA` — one eastern seam; its surplus-baseload economics land
  in the cheap base bands; a split seam would need an IESO HOEP intake
  (open follow-up). (b) The coupling anchor is the hub-mean DA (in-repo
  canonical), not the border-zone LMP; the PJM western-border DA series
  ($28.86/$28.56/$41.45) is the per-band interpretability anchor in the
  derive output. (c) Same-seam no-wash ordering (every export band below
  the seam's cheapest import band) holds naturally in all years; cross-seam
  counterflow (import PJM while exporting South) is real wheel-through,
  bounded by the measured envelopes. (d) Manitoba-2025's measured net
  EXPORT (−0.99 TWh) is outside the firm block's representation (import
  only, +224 MW measured firm delivery) — a ~2-3 TWh known gap on that
  seam, out of scope here (the block is a separate accepted mechanism).

## 5. Result (run `2026-07-07-miso-46-seam-ladder`, miso-45 recipe + the ladder, full span)

See the dashboard entry `2026-07-07-miso-46-seam-ladder` and
`docs/calibration-log.md` (2026-07-07 MISO entry) for the scored result and
the keeper disposition; headline numbers are recorded there once, not
duplicated here (single source of truth).

Expected mechanics, recorded before the solve: the base bands restore the
firm import base (up to the envelope), displacing the marginal domestic
unit — in 2025 that margin is the +22 TWh PRB coal over-run, so C2 coal
should fall toward the actual while gross imports rise toward the measured
~24 TWh (net toward −19 with the South export sinks restored by their own
ladder). C3a mean LMP is NOT expected to close (the cheap base bands cannot
raise the internal level; the 2025 level miss belongs to the coal-sigmoid
C-1 ledger (#1347) and the G-20e scarcity boundary). If coal's remaining
over-run after the import fix is the sigmoids' cheap-gas-keyed discounts,
that stays an OPEN root-cause on #1347 — the sigmoids re-derive only on a
source-data change (rule 23), never against this residual.
