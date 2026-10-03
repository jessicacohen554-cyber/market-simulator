# FINDING — NWPP-NEXT-23 phase 0 (zero LP): the NW-vs-anchor gap is a measured spread, not a model price error

Probe: `scripts/probes/_nwppnext23_price_level_phase0.py` (§A–§E). Inputs: the keeper
`2026-10-03-nwpp-next-22b-w0` committed `hourly/system_<Y>` and `unit_marginal_<Y>`, its seam flows
(`flows.parquet` read from the keeper legs by full SHA, `68cb702e` … `41a7bfb0`), the registry, and the measured
MALIN intertie LMP, ELAP_BCHA, and the labelled NW WEIM imbalance benchmark (R-9). MALIN / BCHA / WEIM are
validation series only. No LP.

## §A. The anchor against its own source, hour by hour

Zero-flow anchor = `(HH + basis) × HR[y] × (CAISO net load / mean)`. Means match by construction (2023–25).

| seam / year | anchor sd | measured sd | hourly r | hod-profile r |
|---|---:|---:|---:|---:|
| COI 2023 | 18.5 | 36.2 | 0.547 | 0.899 |
| COI 2024 | 15.2 | 28.2 | 0.540 | 0.916 |
| COI 2025 | 14.5 | 16.4 | 0.784 | 0.973 |
| BC 2024 | 6.0 | 17.1 | 0.520 | 0.786 |

The flat annual HR on a net-load shape **over-prices CAISO's night** (hod 21–04: +4 to +12 $/MWh above MALIN) and
under-prices the ramps (hod 06–07, 18–19: −4 to −19). The handoff's question is answered yes, but the effect is
small against §B.

## §B. Export-hour decomposition (the keeper's COI / BC export hours, means, $/MWh)

`(anchor − hurdle) − NW_model = (anchor − measured anchor) + (measured anchor − NW measured) + (NW measured − NW model) − hurdle`

| seam / year | export h | anchor − meas | **meas spread** | NW meas − NW model | model flow / measured, MW |
|---|---:|---:|---:|---:|---|
| COI 2023 | 3,633 | +2.75 | **+11.75** | +4.24 | 2,328 / 326 |
| COI 2024 | 6,114 | +3.87 | **+9.38** | +4.31 | 2,384 / 492 |
| COI 2025 | 5,374 | +1.94 | **+10.96** | +1.41 | 2,318 / 654 |
| BC 2023 (Jun–Dec) | 4,633 | −2.16 | **+41.49** | +4.89 | 2,210 / 1,378 |
| BC 2024 | 7,972 | +0.59 | **+2.52** | +10.12 | 1,624 / 870 |
| BC 2025 | 4,799 | +2.20 | **+5.06** | +0.10 | 1,054 / 523 |

**Reading.** On COI, 60–75 % of the gap is the **measured** MALIN − NW spread, which the real market carried with a
few hundred MW of flow. The anchor adds $2–4 and the NW model price $1–4. The NW price level is not the main error.
On BC 2024, the NW model price is the largest term (−$10, the all-hours 2024 price gap, C3a −27 %).

## §C. Who sets the NW price

Hydro is the marginal unit in 99.4–99.8 % of NWPP-NW/OR marginal unit-hours, every year, at an offer of $1.4/MWh. The
NW price is therefore the hydro water value (the energy-budget dual), not a gas offer, in export and non-export hours
alike.

## §D. Price-taker on the keeper's NW price, measured caps (TWh, export +)

- H0 is the keeper: hurdle 3.0.
- H1 adds the CARB unspecified-import obligation on NW→CA exports: `CARB_UNSPECIFIED_IMPORT_EF` 0.428 × the measured
  CARB auction price, $7.2–15.1/MWh.
- H2 sets the NW→CA hurdle to CAISO's own registered PNW delivered basis, `CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]`:
  ×1.05 + $5.

| COI | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Σ\|err\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H0 keeper | 13.43 | 17.03 | 16.51 | 17.79 | 6.39 | 12.34 | 8.96 | 39.3 |
| H1 +GHG | 8.50 | 10.37 | 12.28 | 14.85 | 0.33 | 3.22 | 0.59 | 13.3 |
| H2 PNW basis | 10.81 | 14.01 | 14.65 | 16.70 | 3.79 | 9.62 | 6.02 | 25.0 |
| H1+H2 | 6.54 | 7.74 | 10.60 | 13.71 | −0.93 | 1.79 | −1.00 | 17.2 (sign flips 2023/25) |
| actual | 7.03 | 15.26 | 12.11 | 12.50 | 1.13 | 2.15 | 3.03 | |

Applying the same frictions to NEVP is refuted. NEVP already under-exports in 2021–25: H0 3.95 / 9.00 / 5.47 against
measured 7.56 / 9.08 / 9.40 (2023–25). Under H1, NEVP goes net import in 2023 and 2025 (−1.30 / −0.62). The NEVP→CISO
leg does not behave like spread arbitrage.

Swapping in the measured anchor (a DIAGNOSTIC overlay, never an input) barely moves COI: 2023 7.31 against 8.57 on the
same hours, 2024 13.11 against 12.34, 2025 11.48 against 8.96. **No anchor reconstruction can close the COI
overshoot.**

## §E. The measured record's own flow-vs-spread response (validation, never a source)

Measured COI flow (MW, export +) by measured MALIN − NW spread:

| spread $/MWh | ≤ −10 | −10…−5 | −5…0 | 0…5 | 5…10 | 10…15 | 15…20 | 20…30 | > 30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | −504 | −288 | −208 | 1 | 132 | 289 | 496 | 647 | 787 |
| 2024 | −474 | −136 | −35 | 103 | 348 | 486 | 617 | 569 | 825 |
| 2025 | −366 | −174 | −58 | 194 | 483 | 634 | 657 | 699 | 567 |

Two facts follow:

1. **The zero crossing sits at a spread of $0–5.** It is not at $14–17. A full unspecified GHG wedge on the marginal
   MW (H1) is therefore contradicted by the measured response, which is consistent with CAISO's EF-0 PNW tranches.
   H1's fit is the right total for the wrong reason.
2. **The flow saturates at about 600–800 MW, even at spreads above $20–30.** The measured caps are 2,800–5,100 MW, and
   the price-taker exports at the cap once the spread clears the hurdle. The measured response is a slope, not a step.
   BC shows the same saturation: about 1,400–1,700 MW at spreads above $30.

So no single hurdle reproduces the measured response. A frictional hurdle moves the zero crossing, but the overshoot
is the **depth**: how much of the CISO-share OTC is economically available to spread trade.

## Rule tests

- **H1.** Rule 13: admissible, because the CARB price is projected forward. Rule 19: conflicts with CAISO's side of
  the same seam, where the PNW tranches carry EF 0. §E refutes it on the marginal MW. Not proposed.
- **H2.** Rule 19: aligns this side with CAISO's registered basis for the same physical path. Rules 5 and 25: the
  constant is a physical delivery basis, not a tuned curve. Its source is recorded only as "measured" (FINDING-caiso167
  §ii), and the PNW EF row reads "needs-citation" in `parameter-citations.md`. It moves the zero crossing to about
  $6.7, past §E's $0–5. Partial (Σ|err| 39 → 25 TWh).
- **Depth.** A measured economic-depth limit on the CISO leg (the §E saturation) would be read off measured flow. That
  is the rule-13 line: an envelope sized on the outcome. It is not proposed without a forward driver. One candidate
  driver: CAISO OASIS ITC DAM schedules net of the CISO leg (the non-economic share of the OTC).

## Routed

- **Owner card** (NEXT-23). H2 alone, as a default-off key, or close the price-level lever without a solve.
- **C3a 2024 −27 %.** This is the NW model price in all hours (−$9.9 against the WEIM benchmark), set by hydro water
  value (§C). It is a separate lever from the seam.
