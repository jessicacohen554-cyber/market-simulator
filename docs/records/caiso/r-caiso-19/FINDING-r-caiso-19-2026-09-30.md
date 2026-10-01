# FINDING R-CAISO-19 — fold DSW import residual 2019–21 (2026-09-30)

Zero LP. Owner card 2026-09-30: "Fold DSW residual". Keeper `2026-09-30-caiso-r18-dswgas` (2022–25, CALIBRATED,
single ledgered C3c 2024) and its fold `-touchpoints` (2019–21, NOT-YET, reported only, rule 30(c)) are unchanged.

**Outcome: no admissible lever. Nothing was built and nothing was solved** (handoff step 3). The next link goes to the
owner as a decision card.

## 1. Decomposition (R-CAISO-18 legs, P1)

- Source: the legs' `unit_hourly` / `system` read from their shard commits (RESULT-r-caiso-18 §Retrievability,
  provenance only).
- Measured basis: EIA-930 DSW corridor net import (`derive_caiso_import_tranches.corridor_net_import`).
- Probe: `docs/records/caiso/r-caiso-19/p0_dsw_decomposition.py`. TWh.

| Year | Model | EIA-930 | Gap | Firm PV block | Gas (CCGT + CT + scarcity) | Clean rungs | Gap h0–5 | h6–17 | h18–23 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2019 | 31.4 | 44.7 | −13.3 | 19.1 | 12.3 | **0.0** | −3.8 | −5.3 | −4.2 |
| 2020 | 21.3 | 41.9 | −20.6 | 17.2 | 4.1 | **0.0** | −7.3 | −6.3 | −6.9 |
| 2021 | 29.9 | 40.9 | −11.0 | 12.6 | 1.5 | 15.8 | −2.1 | −2.6 | −6.3 |
| 2022 | 35.1 | 36.8 | −1.7 | 14.4 | 0.1 | 20.6 | +1.0 | +1.2 | −4.0 |
| 2023 | 24.4 | 29.4 | −5.0 | 10.7 | 0.5 | 13.1 | −1.4 | +1.0 | −4.6 |
| 2024 | 26.4 | 29.3 | −2.8 | 13.8 | 0.2 | 12.5 | −1.7 | +2.0 | −3.2 |
| 2025 | 26.5 | 31.2 | −4.7 | 13.6 | 0.1 | 12.9 | −3.1 | +1.7 | −3.3 |

- **The residual is the absent clean rungs.** In 2021–25 the four clean rungs carry 12.5–20.6 TWh, and the gas tranches
  carry only 0.1–0.5 TWh (2022–25). In 2019–20 the clean rungs carry 0 MW, and the gap (13.3 / 20.6 TWh) is the same
  size as what they carry in the keeper years.
- **The gap is spread across the clock in 2019–20**, as the clean rungs are in the keeper years (overnight, daytime and
  late evening). In 2022–25 the only residual is the evening (h18–23, −3 to −5 TWh), which is the known evening
  under-price, not this lane.
- **2021:** Jan–Apr carry 7.8 of the 11.0 TWh gap (by month: −2.95 / −1.49 / −2.25 / −1.11). These are the four
  unprinted months, so the cause is the same.

## 2. The gas tranches are priced correctly (rule 19)

| Year | SP15 λ | DSW_CCGT offer | DSW hub | offer − hub | DSW_CCGT TWh / capability |
|---|--:|--:|--:|--:|--:|
| 2019 | 38.5 | 38.4 | 28.1 (formula) | 10.3 | 7.10 / 15.4 |
| 2020 | 34.8 | 40.3 | 30.0 (formula) | 10.3 | 3.55 / 15.4 |
| 2022 | 86.1 | 97.5 | 83.0 (raw) | 14.5 | 0.12 / 15.4 |
| 2024 | 34.0 | 50.4 | 33.4 (raw) | 17.0 | 0.21 / 15.4 |
| 2025 | 34.7 | 46.9 | 32.5 (raw) | 14.4 | 0.07 / 15.4 |

- The offer is hub + $4.00 Path-46 wheel + border carbon × 0.37/0.428 + ε in every year. The 2019 carbon term is
  $6.3/MWh, which implies about $17/t, the 2019 allowance level.
- The formula hub is gas × marginal heat rate × load shape. It carries neither a wheel nor GHG, just as the OASIS print
  excludes GHG. **There is no double count.**
- The gas blocks already run more in 2019 (7.1 TWh) than in any keeper year (≤0.4 TWh). Repricing them is not the route
  to the keeper years' DSW volume, and any cut to the wheel or carbon term would be a fitted haircut (rule 13).

## 3. Can any clean rung be armed in 2019–20 without a raw print? No.

| Rung | Arming condition | With only the formula hub |
|---|---|---|
| surplus (caiso-87) | raw hub < 6.97 × SoCal citygate + $2.5 | The formula hub is itself gas × heat rate. The trigger would compare two gas constructions, so it would reflect heat-rate and basis differences, not a measured surplus. **Inadmissible.** |
| daytime (caiso-94) | hod 6–21, raw hub finite, surplus trigger OFF | Same trigger. **Inadmissible.** |
| late evening (caiso-269) | per-(month × hod) median of measured DA − raw hub spread within (−2, +4) | No raw hub, so no spread. **No instrument.** |
| overnight (caiso-93) | hod 0–5 and raw hub finite | The finite-print gate was written to exclude reference-filled hours ("pricing continuity, not clean-attribution evidence"). The no-wedge evidence is the measured 2022–25 spread. In 2019–20 the WEIM DSW footprint was smaller (AZPS and NEVP; SRP joined 2020-04; later TEPC, PNM and others). Arming it would carry 2022–25 behaviour into years that have no measurement. That is a transfer, not a measured input (rules 13/14). |

**Measured sources searched, none usable:**
- OASIS GroupZip serves nothing before 2021-04-27, and the SingleZip ~39-month retention is past (`lmp-data/CAISO`
  README).
- `nwpp-weim` holds WEIM LMPs and transfers for 2023–25 only.
- The ICE daily on-peak index was refused in R-CAISO-12: no hourly data, and it needs a per-year fitted basis
  (matrix `import_hub_pricing`).

**Constraints respected:**
- The depth tables (p95 corridor net import) could be derived for 2019–20, but depth is not what blocks the rungs.
- The clean-rung percentiles are K and are not re-sized (rule 1).
- `caiso_import_solar_shape` stays R.

## 4. Decision rule

Handoff step 3 applies: there is no admissible lever, so nothing is built and the next link goes to the owner as a
decision card. The keeper and fold are untouched, so rule 35 has nothing to prune and the §5 backstop does not arise.

## Retrievability (rule 34(e))

No solve and no bundle. The R-CAISO-18 legs this reads are named by SHA in RESULT-r-caiso-18 (provenance only).
