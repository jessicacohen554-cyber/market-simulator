# AEO2025 verification — hardcoded vs. API-fetched (2026-07-11)

**Purpose.** Resolve the standing `TODO: verify against AEO Table 13` at
`constants.py:914` (`HENRY_HUB_TRAJECTORIES`). This session (P-0C, forecast
driver data intake) fetched the real AEO2025 tables via the EIA Open Data API
v2 (`scripts/fetch_eia_aeo.py` → `data/raw/eia-aeo/eia_aeo2025_fuel_prices.csv`
→ `scripts/curate_eia_aeo_fuel_prices.py`) and diffs them against the
hand-typed constants. **`HENRY_HUB_TRAJECTORIES` is unchanged in this
session** — re-deriving it (and adding the new coal/oil trajectories) is
P-1D's job, cited to this data change per CLAUDE.md rule 23.

Source: EIA AEO2025 API, `tableId=13` (Natural Gas Supply, Disposition, and
Prices), series `prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu` ("Natural Gas : Henry
Hub Spot Price", 2024 $/MMBtu), all three scenario cases. Fetched
2026-07-11.

## 1. Henry Hub — the TODO this resolves

### "mid" path (AEO Reference case ↔ `ref2025`)

| year | hardcoded | AEO2025 fetched | diff | diff % |
|---|---|---|---|---|
| 2024 | 2.19 | 2.192 | +0.002 | +0.1% |
| 2025 | 3.52 † | 2.879 | −0.641 | −18.2% |
| 2026 | 3.40 | 2.737 | −0.663 | −19.5% |
| 2027 | 3.20 | 2.618 | −0.582 | −18.2% |
| 2028 | 3.30 | 2.728 | −0.572 | −17.3% |
| 2029 | 3.40 | 2.893 | −0.507 | −14.9% |
| 2030 | 3.50 | 3.080 | −0.420 | −12.0% |
| 2031 | 3.55 | 3.226 | −0.324 | −9.1% |
| 2032 | 3.60 | 3.703 | +0.103 | +2.9% |
| 2033 | 3.65 | 4.102 | +0.452 | +12.4% |
| 2034 | 3.70 | 4.336 | +0.636 | +17.2% |
| 2035 | 3.80 | 4.427 | +0.627 | +16.5% |
| 2036 | 3.90 | 4.424 | +0.524 | +13.4% |
| 2037 | 4.00 | 4.372 | +0.372 | +9.3% |
| 2038 | 4.05 | 4.309 | +0.259 | +6.4% |
| 2039 | 4.10 | 4.244 | +0.144 | +3.5% |
| 2040 | 4.15 | 4.268 | +0.118 | +2.8% |
| 2041 | 4.20 | 4.345 | +0.145 | +3.4% |
| 2042 | 4.25 | 4.420 | +0.170 | +4.0% |
| 2043 | 4.30 | 4.555 | +0.255 | +5.9% |
| 2044 | 4.40 | 4.639 | +0.239 | +5.4% |
| 2045 | 4.45 | 4.697 | +0.247 | +5.5% |
| 2046 | 4.50 | 4.783 | +0.283 | +6.3% |
| 2047 | 4.55 | 4.831 | +0.281 | +6.2% |
| 2048 | 4.65 | 4.828 | +0.178 | +3.8% |
| 2049 | 4.70 | 4.806 | +0.106 | +2.2% |
| 2050 | 4.80 | 4.803 | +0.003 | +0.1% |

† 2025 in `HENRY_HUB_TRAJECTORIES` is deliberately the **realized historical**
Henry Hub spot annual average ($3.52), not AEO2025's own 2025 projection
($2.88 — AEO2025 assumptions were frozen Dec 2024, before the actual 2025
price came in higher). This is documented in the constant's own comment and
is correct as-is; it is not part of the discrepancy below.

**Finding.** The endpoints (2024, 2050) match almost exactly — the hand-typed
curve was clearly anchored on AEO2025's first and last published points.
**The shape in between does not match.** The real AEO2025 Reference case dips
to a 2027 trough (~$2.62, LNG-export-driven near-term softness) before
climbing through the early 2030s to a ~$4.4-4.8 plateau, then eases slightly.
The hardcoded curve instead ramps up roughly monotonically from 2026. The
practical effect: the hardcoded curve **overstates** gas prices by 12-20%
through 2026-2031, then **understates** them by up to 17% through 2033-2036.
Both directions matter for dispatch (understating late-2020s gas suppresses
coal-to-gas switching and marginal price in gas-set hours in the near term;
overs​tating mid-2030s gas has the opposite effect there).

### "low" path (AEO High Oil and Gas Supply ↔ `highogs`)

Same pattern, smaller magnitude: hardcoded ramps 2.70→3.05 roughly
monotonically; fetched dips to a 2027 trough (~$2.03) then rises to a
~2035-2036 local high (~$2.81-2.82) before easing to $2.83 by 2050. Diff
range: −$0.66 (2026) to +$0.41 (2035). Full series in
`data/raw/eia-aeo/eia_aeo2025_fuel_prices.csv` (`scenario=highogs`).

### "high" path (AEO Low Oil and Gas Supply ↔ `lowogs`)

Not currently populated in `HENRY_HUB_TRAJECTORIES` under a distinct
comparison here — the fetched series is landed (`scenario=lowogs`) and ready
for P-1D; see the raw CSV for the full 2024-2050 series (spot check: 2026
$3.02 → 2035 $6.29 → 2050 $8.02, a materially steeper high-case ramp than
implied by scaling the mid case, reflecting AEO's own supply-constrained
dynamics rather than a fixed multiplier on Reference).

## 2. Coal — newly landed, no prior AEO-cited series existed

The model does not currently derive coal prices from AEO at all:
`COAL_PRICE_BASE` is a set of per-ISO backcast-period delivered $/MMBtu
anchors (2023-2025, cited to EIA AEO **2024** — one edition stale — and
EIA-923), escalated forward at a flat `COAL_PRICE_ESCALATION = 0.01`/yr
(constants.py:1225). This session lands the real AEO2025 national
delivered-to-electric-power coal price (`metric=delivered_electric_power`,
2024 $/MMBtu) plus a national minemouth price and a 5-region minemouth
breakout ($/short ton — Table 65 has no by-region $/MMBtu figure).

| year | model flat-1%/yr (PJM 2.30 anchor) | AEO2025 delivered-to-electric-power (national, Reference) |
|---|---|---|
| 2025 | 2.300 | 2.430 |
| 2030 | 2.417 | 2.239 |
| 2035 | 2.541 | 1.959 |
| 2040 | 2.670 | 2.065 |
| 2045 | 2.806 | 2.057 |
| 2050 | 2.950 | 2.361 |

**Finding.** AEO2025's own national coal price to the power sector is
essentially **flat-to-slightly-declining** in real terms (CAGR −0.11%/yr,
2025-2050) — not rising. The model's flat +1%/yr assumption pushes the 2050
price ~25% above the AEO-implied level. Direction of the error is
"structural coal is modeled as getting relatively more expensive over time
when AEO's own outlook says roughly flat" — worth a citation update at
minimum (the source says "EIA AEO 2024 coal supply module" for the 1%
figure; AEO2025's module gives a different, lower, number). Re-deriving
`COAL_PRICE_BASE`'s forward escalation from this data (a new
`COAL_PRICE_TRAJECTORIES`, replacing the flat 1%/yr per plan item P-1D#1) is
recommended.

## 3. Oil — newly landed, unit mismatch flagged (no conversion performed here)

The model's oil fuel cost is a single flat scalar, `OIL_PRICE_PER_MMBTU =
18.0`, cited to measured PJM ISO-monthly delivered oil prices (2023-2025),
**not** an AEO series — a different kind of input (ISO-specific measured
delivered cost vs. a national commodity benchmark) held flat forward rather
than escalated at all. This session lands three AEO2025 series in their
**native published units** (no Btu-content conversion attempted here, to
avoid introducing a new derived assumption inside a diff report):

| metric | unit | 2026 | 2035 | 2050 |
|---|---|---|---|---|
| WTI crude spot | 2024 $/b | 79.11 | 80.09 | 89.27 |
| electric-power distillate fuel oil | 2024 $/gal | 3.22 | 3.20 | 3.54 |
| electric-power residual fuel oil | 2024 $/gal | 2.04 | 2.55 | 2.67 |

**Finding.** `electric_power_distillate`/`electric_power_residual` are the
two series a fuel-cost re-derivation should use (they're the actual
generator-delivered products, not the upstream crude marker); converting to
$/MMBtu needs a cited EIA heat-content factor (distillate ≈ 138,690 Btu/gal,
residual ≈ 149,690 Btu/gal, EIA heat-content documentation) — left for P-1D
since that's a derivation step, not a fetch/diff step. At face value,
distillate ÷ 138,690 Btu/gal × 1,000,000 ≈ $23/MMBtu (2026) and residual ÷
149,690 × 1,000,000 ≈ $14/MMBtu (2026) — both materially different from the
flat $18/MMBtu (residual notably cheaper, distillate notably pricier),
consistent with the model's own comment that PJM's measured range is
"~$17-23/MMBtu" spanning both products. Not a contradiction, but a
reminder that a single flat scalar averages over two products with a real
~$9/MMBtu spread.

## 4. What this session did and did not do

- **Did:** fetch AEO2025 gas/coal/oil price series via the EIA API v2 (real
  registered key from repo `.env`, not a scrape); land them as a new
  `eia-aeo-fuel-prices` clean datatype (schema + curate script + test, see
  `data/raw/eia-aeo/README.md`); produce this diff.
- **Did not:** change `HENRY_HUB_TRAJECTORIES`, `COAL_PRICE_BASE`,
  `COAL_PRICE_ESCALATION`, or `OIL_PRICE_PER_MMBTU`. No `constants.py` edits
  in this session (CLAUDE.md rule 23 — a re-derivation cites this data
  change, it doesn't happen inside the intake session that produced the
  data).

## 5. Recommendation for P-1D

1. Re-derive `HENRY_HUB_TRAJECTORIES` (all three paths) directly from
   `data/clean/eia-aeo-fuel-prices` — the shape mismatch above is large
   enough (up to ~20%) to matter for dispatch, not just a citation nicety.
2. Add `COAL_PRICE_TRAJECTORIES` (replacing the flat 1%/yr) from the
   `delivered_electric_power` national series; keep the existing per-ISO
   `COAL_PRICE_BASE` anchors for the 2023-2025 backcast window (measured,
   correct) and switch only the *forward escalation* to the AEO-implied
   path.
3. Add an oil forward path from `electric_power_distillate` /
   `electric_power_residual`, with a cited Btu-content conversion, as a
   fuel-mix-weighted replacement for the flat $18/MMBtu (or keep the flat
   scalar for the base year and escalate it at the AEO-implied real rate —
   either is more defensible than fully flat).
4. Note the regional coal minemouth series (`minemouth_by_region`, Table 65)
   is in $/short ton, not $/MMBtu — a heat-content conversion (coal rank
   dependent) is needed before it's comparable to the per-ISO
   `COAL_PRICE_BASE` figures.
