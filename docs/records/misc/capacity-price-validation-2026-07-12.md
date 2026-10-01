# Capacity demand-curve validation vs auction history — 2026-07-12 (P-2A / CR-2)

**Session.** P-2A of `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
(§3.3 CR-2 / §2 T3.1). Validates the CR-1 sloped capacity demand curves
(`config.constants.MARKET_DESIGN`, landed default-off in P-1B) against published
auction outcomes for the five capacity-market ISOs.

**Deliverable.** `scripts/validate_capacity_prices.py` (+
`tests/test_validate_capacity_prices.py`) and this report. The script
deterministically regenerates every table below (and a machine-readable
`results/capacity-price-validation/validation.json`) from the committed P-0B data;
reproduce with:

```
uv run python -m scripts.validate_capacity_prices --markdown
```

**HARD RULES honored.** Comparison only — no curve parameter was touched, no
multiplier fitted, no adder introduced (rules 1/13/23). The published demand-curve
parameters and clearing prices are validation observables, never fit targets.
H1-2026 forward-edge rows (delivery year ≥ 2026, and NYISO's 2026-published 2025/26
spot) are shown _greyed/italic_ and **excluded from every verdict** (rule 22). No LP
was solved; nothing is registered on any dashboard.

---

## 1. Verdict (lead)

- **The curve SHAPES are faithful — reproduced essentially exactly.** The
  implemented normalized curves land on the ISOs' published (cap ÷ net-CONE) points
  to within rounding: PJM 1.552 vs 1.552, NEISO 1.600 vs 1.600 every constant-ratio
  year, NYISO 3.792 vs 3.792. CR-1 transcribed the published instruments correctly
  (as rule 13 requires). **PASS.**
- **The PJM 2024/25 → 2025/26 spike DIRECTION reproduces.** Fed the auctions' own
  (fleet-independent) reserve positions, the fixed curve turns the observed supply
  tightening into a price jump of the right sign and order of magnitude
  ($0 → ~$217/MW-day model vs $29 → $270/MW-day actual). **PASS (directional).**
- **The clearing-price *level* residual is the DOLLAR ANCHOR, not the shape.** PJM
  runs a uniform **−22 to −28 %**, which is precisely PJM's **≈0.78 ICAP↔UCAP
  factor** (the #1532 basis flag) plus the single-vintage frozen net-CONE. NEISO is
  **±11–24 %** from the frozen FCA18 anchor vs each year's real net-CONE. These are
  order-of-magnitude reproductions, not fits.
- **DECISIVE BLOCKER — the model's own accredited position is far too long.** On the
  PJM hindcast fleet the accredited reserve position is **1.29–1.36**, well past the
  curve's 1.045 zero-cross, so the curve pays **$0 capacity in every year** — including
  the 2025/26 shortage year that actually cleared near the cap. A structurally-correct
  curve fed a wrong position produces a wrong price.
- **RECOMMENDATION: keep `capacity_market_clearing` DEFAULT OFF for all five ISOs.**
  The curve is validated as an *instrument*; it is not yet wired to a trustworthy
  *position* or a basis-consistent *anchor*. Flipping it on today would let fleet
  error zero out capacity revenue in the retirement/entry/storage screens (rule 1).
  **No default flip this session → no T1.7 / tornado re-run** (those are gated on a
  flip). Prerequisites for a future flip are itemized in §7.

---

## 2. Method

For each ISO the tool runs two passes (details in the script docstring).

- **Pass 1 — curve isolated from the fleet.** The auction is placed on the ISO's
  *own published* demand curve using only published quantities (that year's net-CONE,
  price cap, curve x-positions, clearing price), so **curve error is isolated from
  fleet error** (the plan's explicit instruction). Two views:
  - **1A shape** — the implemented curve's price *fraction of net-CONE* at the
    published cap position vs the published fraction. Pure shape, no dollars, no
    circularity.
  - **1B price** — the implemented curve's dollar price at the published cleared
    reserve position vs the published clearing price.
- **Pass 2 — curve on the model's own hindcast fleet.** For the only non-ERCOT
  hindcast that exists (PJM), the model's accredited reserve position per solved year
  is recovered from the persisted evolution ledger (`firm_mw / requirement`, the exact
  basis `capacity.capacity_reserve_position` uses) and fed to the curve.

All prices are annualized to **$/kW-yr** (UCAP basis, as published). Where a year's
own price cap was not published (PJM 2025/26), the model's normalized cap fraction
stands in for the *position inversion only* (flagged) — it never enters a shape score.

---

## 3. Pass 1 — curve vs auction, at the published fleet-independent position

### 3.1 PJM (RPM Base Residual Auction, $/MW-day → $/kW-yr)

**Pass 1B — curve price vs cleared price.**

| Delivery yr | Cleared $/kW-yr | Pub net-CONE | Model net-CONE | Reserve pos | Model curve | Resid | %err | Note |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| 2015/2016–2024/25 | 10.6–60.1 | — | 60.4 | — | — | — | — | pre-2025/26: no published curve params that year (position not reconstructable) |
| 2025/2026 | 98.5 | 83.5 | 60.4 | 1.007 | 70.8 | −27.7 | **−28 %** | cap fraction model_shape_proxy |
| _2026/2027_ | _120.1_ | _77.4_ | _60.4_ | _0.990_ | _93.7_ | _−26.4_ | _−22 %_ | _⛔ locked_ |

**Pass 1A — normalized SHAPE reproduction (price ÷ net-CONE at the published cap).**

| Delivery yr | Published cap frac | Model cap frac | Shape resid |
|---|--:|--:|--:|
| _2026/2027_ | _1.552_ | _1.552_ | _+0.0 %_ |
| _2027/2028_ | _1.375_ | _1.552_ | _+12.9 %_ |

The shape is exact for 2026/27 (the vintage CR-1 transcribed). The −22 to −28 %
price residual is **not shape** — it is the **$ anchor basis**: PJM publishes net-CONE
both as **212.14 $/MW-day** (the demand-curve reference the VRR curve is drawn around,
= 77.4 $/kW-yr) and as **60,396 $/MW-yr UCAP** (= 60.4 $/kW-yr); the two differ by
PJM's ≈0.78 ICAP↔UCAP factor. The model scales its (correct-shape) curve by the
UCAP-annual 60.4 while the auction clears against the 77.4 reference — so every point
lands ≈22 % low. This is exactly the #1532 basis ambiguity the P-2B session is
chartered to adjudicate; it is **not corrected here** (rule 23). The 2025/26 extra
gap on top is the frozen single-vintage anchor (60.4 held for a year whose real UCAP
net-CONE was 66.0).

### 3.2 NEISO (Forward Capacity Auction, $/kW-month → $/kW-yr)

| Delivery yr | Cleared $/kW-yr | Pub net-CONE | Model net-CONE | Reserve pos | Model curve | Resid | %err |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2020/2021 | 63.6 | 139.7 | 108.9 | 1.045 | 49.7 | −13.9 | −22 % |
| 2021/2022 | 55.6 | 96.5 | 108.9 | 1.035 | 62.8 | +7.2 | +13 % |
| 2022/2023 | 45.6 | 97.9 | 108.9 | 1.044 | 50.8 | +5.2 | +11 % |
| 2023/2024 | 24.0 | 98.2 | 108.9 | 1.063 | 26.7 | +2.7 | +11 % |
| _2026/2027_ | _31.1_ | _88.3_ | _108.9_ | _1.054_ | _38.4_ | _+7.4_ | _⛔ +24 %_ |

Shape is exact (cap fraction 1.600 = published starting-price/net-CONE every scored
year; 2025/26 legitimately publishes 1.660). The ±11–24 % price residual is the
**frozen FCA18 anchor** (108.9 $/kW-yr) standing in for each year's real net-CONE
(96–140). Note NEISO cleared **below net-CONE every year** (positions 1.03–1.06, on
the long side) — the curve correctly reproduces a persistently-long, cheap capacity
market. This is a genuine order-of-magnitude PASS.

### 3.3 NYISO (ICAP spot, $/kW-month → $/kW-yr)

Only the **2025-2026** vintage of the ICAP demand curve is on disk (P-0B captured one
vintage), and it is **locked** (2026-published SOM). Every earlier year has a spot
price but no per-year Annual Reference Value, so **no NYISO year is scoreable** in
Pass 1B. Pass 1A confirms the anchor matches the published ARV exactly (model 3.792 =
published 3.792; net-CONE 50.55 = ARV 50.55). Directionally, NYCA spot cleared **at or
below net-CONE every year** (1.6–4.3 vs 4.21 $/kW-month) — consistent with the
model's long-side curve, but not a scored result. **NOT VALIDATED (data-limited).**

### 3.4 MISO (seasonal PRA, $/MW-day → $/kW-yr)

| Delivery yr | Cleared (summer) | Pub net-CONE | Model net-CONE | Reserve pos | Model curve | Resid | %err |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2025/2026 | 243.3 | 73.3 | 79.8 | 0.970 | 127.4 | −115.9 | −48 % |

MISO's PRA is **seasonal**, and the model curve is **annual** — a grain mismatch that
makes MISO not slope-scoreable today. The 2025/26 summer cleared at the gross-CONE
cap ($666.50/MW-day) while the other three seasons cleared **$0.3–33/MW-day**:

| Delivery yr | Summer | Fall | Winter | Spring | ($/kW-yr) |
|---|--:|--:|--:|--:|---|
| 2023/2024 | 3.6 | 21.6 | 6.9 | 3.6 | |
| 2024/2025 | 10.9 | 5.5 | 0.3 | 12.4 | |
| 2025/2026 | 243.3 | 33.4 | 12.1 | 25.5 | |

An annual curve cannot represent a market whose price is concentrated in one season.
The anchor itself is fine (model 79.8 vs published 73.3, +9 %). **NOT VALIDATED at
annual grain — needs the CR-3 seasonal split.**

### 3.5 CAISO

Bilateral RA, no central auction or demand curve. `MARKET_DESIGN["CAISO"]` keeps the
**fixed proxy** (90 $/kW-yr) in *both* modes, so the gate is a **no-op for CAISO** —
CPM designations all cleared at the soft-offer cap (a regulatory ceiling, not price
discovery). Nothing to slope-validate; the proxy remains the documented low-fidelity
member of the registry.

---

## 4. Pass 2 — the decisive fleet-position blocker (PJM)

Fed the model's **own** accredited reserve position from the PJM 2021–2025 realized
hindcast:

| Cal yr | Delivery yr | Peak MW | Firm MW | Req MW | Reserve pos | Model curve | Cleared | %err |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| 2021 | 2021/2022 | 149,590 | 175,270 | 135,677 | **1.292** | **0.0** | 51.1 | −100 % |
| 2023 | 2023/2024 | 147,605 | 182,528 | 133,876 | **1.363** | **0.0** | 12.5 | −100 % |
| 2024 | 2024/2025 | 153,121 | 187,378 | 138,879 | **1.349** | **0.0** | 10.6 | −100 % |
| 2025 | 2025/2026 | 160,560 | 188,698 | 145,626 | **1.296** | **0.0** | 98.5 | −100 % |

The model's accredited fleet sits **29–36 % above** its adequacy requirement — far
right of the curve's 1.045 zero-cross — so CR-1 would pay **zero capacity revenue in
every year**, including the 2025/26 shortage that actually cleared near the cap. Two
compounding causes, both known:

1. **The model retires too little** (this plan's baseline PJM hindcast miss: thermal
   retirements −63 %), so the fleet stays structurally long.
2. **The accreditation basis** — the requirement carries the `icap_to_ucap_ratio`
   0.77 correction while the supply is counted at UCAP firm — the very
   requirement/supply basis pairing #1532 flags — inflates the position further.

This is exactly why Pass 1 isolates the curve from the fleet: **the curve is fine; the
position it would be fed is not.** The sloped curve's whole purpose is to make the
capacity price *respond to the position* — which is only an improvement once the
position is trustworthy.

---

## 5. Regime-reproduction verdict (PJM spike)

**Does PJM's 2024/25 → 2025/26 spike direction reproduce? YES (directional /
order-of-magnitude).** Two independent lines:

1. **Fleet-independent placement (Pass 1B).** 2025/26 cleared *above* net-CONE
   (position 1.007, short side) → the monotone curve returns a high price; the
   pre-spike years cleared *below* net-CONE (long side) → low price. The sign of the
   move is built in.
2. **Cleared-quantity series (illustrative).** As published cleared UCAP falls
   147.5 GW → 135.7 GW, the reserve position tightens 1.088 → 1.001 and the model
   curve price jumps **$0 → $217/MW-day**, reproducing the actual **$28.92 → $269.92**
   spike direction and order of magnitude (the model under-levels the top by the same
   ≈0.78 basis factor):

   | Delivery yr | Cleared MW | Reserve pos | Model $/MW-day | Cleared $/MW-day |
   |---|--:|--:|--:|--:|
   | 2023/2024 | 144,871 | 1.069 | 0.0 | 34.13 |
   | 2024/2025 | 147,479 | 1.088 | 0.0 | 28.92 |
   | 2025/2026 | 135,684 | 1.001 | 216.9 | 269.92 |
   | _2026/2027_ | _134,205_ | _0.990_ | _256.8_ | _329.17_ |

   (Requirement anchored once off the 2026/27 cap-plateau clearing — illustrative:
   the true requirement drifts with the IRM year to year, which is why the long
   pre-spike years read as flat $0 here rather than their actual $30–165 floor-priced
   levels. The exhibit demonstrates *direction*, not levels.)

The spike is a **market-structure** phenomenon — a fixed sloped curve makes a modest
supply tightening produce a large price move — and CR-1 reproduces that structure.
What it cannot yet reproduce is the *level*, for the anchor/basis and fleet reasons
above.

---

## 6. Residual discussion — where every gap lives

The clearing-price residual decomposes cleanly into four independent terms, none of
which is a curve-shape defect:

| Term | Magnitude | Owner / fix | In scope here? |
|---|---|---|---|
| **Curve shape** | ≈0 % | — (validated correct) | — |
| **ICAP↔UCAP anchor basis** (PJM) | ≈ −22 % (the 0.78 factor) | #1532 / P-2B adjudication | No (rule 23) |
| **Frozen single-vintage net-CONE anchor** | ±10–15 % | CR-2 follow-up: per-forecast-year net-CONE | No |
| **Model accredited position too long** | pays $0 vs real | retirement calibration + CR-3.1 marginal-ELCC + #1532 requirement basis | No |
| **Seasonal (MISO) / single-vintage (NYISO) coverage** | not scoreable | CR-3 seasonal; NYISO curve-vintage intake | No |

Every residual routes to an existing plan item or open flag — none is closed by
bending a published parameter (rule 1/11/23).

---

## 7. Recommendation memo — `capacity_market_clearing` default per ISO

**Recommendation: keep the gate DEFAULT OFF for all five ISOs.** Per-ISO rationale:

| ISO | Curve validated? | Flip default ON now? | Why |
|---|---|---|---|
| **PJM** | Shape ✓; level blocked | **No** | Fleet position (1.29–1.36) is past the zero-cross → curve pays $0; ON would zero capacity revenue in all three screens. Anchor basis (#1532) unresolved. |
| **NEISO** | Shape ✓; level ±20 % | **No** | Curve is the best-behaved, but the gate is a single global bool — it cannot be ON for NEISO while OFF for PJM. No NEISO hindcast yet to check its own position (Pass 2). |
| **NYISO** | Not validated | **No** | Only one (locked) curve vintage on disk; no scoreable year. |
| **MISO** | Not validated | **No** | Seasonal PRA vs annual curve — grain mismatch; needs CR-3. |
| **CAISO** | N/A (fixed proxy) | No-op | Gate does nothing for CAISO (no demand curve); no reason to move the global default for it. |

**This is not a rejection of CR-1.** The mechanism is structurally faithful — the
sloped curve reproduces the published instruments exactly and reproduces the PJM spike
*direction*. The gate stays off because the curve is not yet wired to a trustworthy
*input*: a sloped curve is only better than a flat price once the accredited position
it reads is near reality. Flipping on today would substitute a fleet-error-driven $0
for the fixed net-CONE screen input — worse, not better (rule 1).

**Prerequisites for a future flip (ordered):**

1. **#1532 accreditation-basis adjudication (P-2B).** Resolves both the PJM $ anchor
   (ICAP vs UCAP) and the requirement/supply basis pairing that makes the model
   position ≈30 % too long. This is the gating dependency — it sits next in Wave 2.
2. **Accredited-position calibration** — the retirement-miss fix (so the model fleet
   is not structurally long) + **CR-3.1 marginal-ELCC** (P-2C), so the accredited
   position lands near the real auction's position. Re-check with a PJM Pass-2 rerun.
3. **Per-forecast-year net-CONE anchoring** (CR-2 follow-up) so a 2026–2050 run does
   not hold one vintage's net-CONE flat for 25 years.
4. **MISO seasonal split (CR-3)** and **NYISO curve-vintage intake** before those two
   ISOs are curve-eligible at all.

When those land, re-run this validation; a flip becomes justified for an ISO only once
its Pass-2 position lands in the priced region of its own curve and its anchor basis
is reconciled. **Because no flip is recommended, the T1.7 net-CONE ladder and the
tornado capacity entries are unchanged and were not re-run** (per the plan, those
re-runs are gated on an ON flip).

---

## 8. What this session did / did not do

- **Did:** built the comparison tool + tests; produced the per-ISO-year tables, the
  spike-regime verdict, the residual decomposition, and this recommendation.
- **Did not:** touch any curve parameter, anchor, or multiplier; solve or score any
  LP; register anything on a dashboard; solve/score any 2022 or H1-2026 data (all
  ≥2026 delivery rows greyed and excluded). No default was flipped.
- **Data provenance:** every number traces to the P-0B `capacity-market` raw CSVs
  (`data/raw/capacity-market/{demand-curve,auction-price}/…`) and the committed PJM
  hindcast evolution ledgers (`results/hindcast/pjm-2021-2025-realized/…`). The
  implemented curve is read through the production seam
  (`MarketDesign.capacity_price_per_firm_mw_yr` / `evaluate_demand_curve`), so the
  tool tests the shipped code path, not a re-implementation.
