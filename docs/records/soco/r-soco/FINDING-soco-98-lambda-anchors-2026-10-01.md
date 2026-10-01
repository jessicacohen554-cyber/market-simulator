# FINDING soco-98 — SOCO seam `hr_by_year` anchors from neighbour FERC-714 lambdas (2026-10-01)

**Lane.** soco-98. Zero LP. Owner card → **"(e) Forecast anchors only"**: SOCO rests at NOT-YET (7/4/0/3/0, keeper
`2026-09-30-soco96-measured-oil-burn` unchanged), no calibration build. This is data step 3 of
`FINDING-soco-97-interchange-rule14-phase0-2026-10-01.md` §5: a **forecast-lane input, inert in every backcast**.

## 1. What landed

| Item | Change |
|---|---|
| **R-2** (FINDING-soco-33 §7) | `scripts/data/derive_neighbor_hr_by_year.py`: new anchor kind `ferc714_lambda` (reads the neighbour's own FERC 714 Part II Sch. 6 system lambda through `market_sim.data.ferc714`, annual mean only, filed zeros dropped as filing gaps) and a `SOCO` entry in `NEIGHBOR_LMP_ANCHORS`. `--skip-shapeless` reports a seam-year with no EIA-930 load shape rather than failing; the default stays fail-closed. |
| **R-1** | `scripts/data/derive_neighbor_hr_elasticity.py` drops its global name map and reads the same per-ISO `NEIGHBOR_LMP_ANCHORS`. An ISO with no map now **fails** (NWPP: exit 1; before, exit 0 with an empty table). PJM / MISO coefficients are byte-identical to `main`; only diagnostics were added (`n`, `r2`, unanchored list). |
| **R-3** | `SOCO_MISO` 2023–25 adopts the producer's 9.52 / 10.09 / 9.28 (was hand-computed 9.54 / 10.08 / 9.26), extended to 2019–2022 now that MISO-South zonal LMP covers them. |
| Registry | `INTERFACE_NEIGHBORS["SOCO"]` `hr_by_year` = the producer's output (table §2). `marginal_heat_rate`, limits, hurdles, basis: **unchanged**. No `_HR_GAS_ELASTIC` key registered. |
| Test | `tests/iso/soco/test_soco_lambda_anchors.py` (anchor map, zero-drop, fail-closed, default-off, registry = producer output). |

## 2. The anchors (MMBtu/MWh)

`HR[y] = mean anchor[y] / ((HH[y] + gas_basis) × K[y])`, K = 1.0 (exponent 1, mean-1 shape). HH 2019–22 is the measured
annual mean (pjm-172 path), 2023–25 the trajectory knots. `gas_basis` = 0.0 on the five λ seams, 0.30 on MISO.

| Seam | Anchor | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 7-yr mean | Registered flat |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SOCO_TVA | TVA λ (263) | 8.62 | 8.26 | 8.38 | 9.80 | 8.71 | 10.65 | 9.62 | 9.15 | 11.6 |
| SOCO_MISO | MISO-South RT LMP | 8.63 | 9.24 | 8.86 | 9.04 | 9.52 | 10.09 | 9.28 | 9.24 | 9.63 |
| SOCO_DUK | DEC λ (157) | 9.86 | 8.47 | 8.72 | 12.08 | 9.72 | 11.16 | 11.03 | 10.15 | 11.6 |
| SOCO_SC | Santee Cooper λ (251) | 12.11 | 12.00 | 8.71 | 11.02 | 14.54 | 17.27 | 10.56 | 12.32 | 11.6 |
| SOCO_FPC | DEF λ (234) | — | — | — | — | 8.66 | 9.69 | — | 9.18 (2 yr) | 11.6 |
| SOCO_TAL | Tallahassee λ (140) | — | — | — | — | 7.60 | 7.69 | — | 7.65 (2 yr) | 11.6 |
| SOCO_SCEG | none — Dominion SC files 0.00 every hour | | | | | | | | | 11.6 |
| SOCO_FPL | none — λ ~40 % below peers, basis unresolved | | | | | | | | | 11.6 |

**Read:** the borrowed 11.6 flat (PJM's TVA/Carolinas value) over-prices TVA by ~27 % and DEC by ~14 % against their own
λ, and under-prices Santee Cooper. FPC / TAL lack 2019–22 and 2025 only because the `FLA` EIA-930 extract spans
2023-01..2025-01 (SOCO-33 R-4, still open). JEA files a λ but is not a SOCO EIA-930 counterparty, so it has no block.

## 3. Forward elasticity fits — reported, NOT registered

`derive_neighbor_hr_elasticity.py --iso SOCO --years 2019..2025`, `price = hr_phys × gas + hr_adder`:

| Seam | hr_phys | hr_adder | n | r² | Note |
|---|---:|---:|---:|---:|---|
| SOCO_TVA | 10.01 | −2.58 | 7 | 0.975 | 2024 misses by 1.8 |
| SOCO_MISO | 8.76 | 1.51 | 7 | 0.992 | |
| SOCO_DUK | 12.92 | −8.21 | 7 | 0.960 | 2021 / 2024 miss by ~2 |
| SOCO_SC | 8.70 | 10.07 | 7 | 0.812 | 2024 misses by 4.0 |
| SOCO_FPC, SOCO_TAL | — | — | 2 | 1.000 | exactly identified: not a fit |

Every r² is leveraged by the single high-gas year (2022, $6.42). Two parameters on seven points, one of them carrying
the slope, is not an identified elasticity. The arming lane chooses between the seam-own flat mean (§2) and these fits
(rule 21: either is a ledgered input with this record as its source).

## 4. Inertness (zero LP, G-DRIFT)

Every changed hunk is **INERT**:

- `model/interchange/spec.py` is outside `SURFACE_MODULES` (`config/solve_surface.py`), and `cache_key()` hashes only
  `asdict(config)` + moved surface rows + epochs. **Measured:** all 11 committed `results/calibration/*/run_config.json`
  configs give identical cache keys before and after.
- Every reader of `INTERFACE_NEIGHBORS` is ISO-scoped (`.get(iso)`), and the seam-price paths are gated on
  `reference_price_interface` (False in the SOCO keeper; `REFERENCE_PRICE_DEFAULT_ISOS = {"MISO"}`, which reads only
  MISO's blocks). No forecast year is tabulated, so `neighbor_heat_rate` for 2026+ still returns the flat.
- The two scripts are offline derive producers, not on any solve path.

## 5. Rule checks

- **13 [R-MEASURED]:** the hourly λ is never a seam price; only its annual mean anchors the
  `(HH + basis) × HR × shape` construction — the same use the LMP anchors make. Filed zeros are filing gaps, not prices.
- **14:** λ is the vertically integrated counterpart of an LMP (system incremental cost). It includes Elliott scarcity
  (SC 2022 max $6,219), as the LMP anchors include theirs. With `gas_basis` = 0.0 the Southeast delivered-gas basis is
  carried inside HR; registering a basis later re-derives HR and leaves the constructed annual mean unchanged.
- **25:** no PJM or MISO anchor is reused; `SOCO_MISO` reads MISO-South's own zonal LMP (the same physical seam as
  MISO's `South` block and SPP's `MISO_South`, rule 19).
- **G17:** SOCO's own λ never enters.

## 6. Open (routed, not done here)

- **R-4:** fetch the `FLA` EIA-930 hourly extract for 2019–22 and 2025, then re-run the producer to fill FPC / TAL.
- **FPL basis** (ferc-714 README "Flags") before `SOCO_FPL` can be anchored.
- **Forward HR choice** (§3) and limits (soco-97 §2: direction, corridor, dated FPLNW, TVA) belong to the arming lane.
- **Matrix:** `priced_interchange` / `reference_price_interface` stay `U` (no solve).
