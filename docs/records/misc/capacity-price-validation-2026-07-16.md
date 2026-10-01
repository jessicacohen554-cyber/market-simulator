# Capacity demand-curve validation — refreshed sections (RC-1C) — 2026-07-16

**Session.** RC-1C of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.3 F-5, prereq
4a/4b): MISO seasonal RBDC grain + NYISO multi-vintage curve wiring, with a
per-ISO curve-eligibility gate. This document **refreshes §3.3 (NYISO) and §3.4
(MISO)** of the prior validation reports
(`capacity-price-validation-2026-07-12.md` / `-2026-07-14.md`) — the PJM/NEISO
sections are unchanged (their model side still reads the registry reference, so
their Pass-1/Pass-2 numbers are byte-stable). Regenerate every table below with:

```
uv run python -m scripts.validate_capacity_prices --markdown
```

**HARD RULES honored.** Comparison only — no curve parameter touched, no
multiplier fitted, no adder introduced (rules 1/13/23). Published demand-curve
parameters and clearing prices are validation observables, never fit targets.
Delivery years ≥ 2026 (and NYISO's 2026-published 2025/26 spot) are greyed/locked
and **excluded from every verdict** (rule 22). **No LP was solved; nothing is on
any dashboard.** No holdout year was solved or scored — the numbers below are read
off the committed `capacity-market` raw CSVs and the shipped pricing seam.

---

## §3.3 (refreshed) — NYISO, PER-VINTAGE Pass 1B (2023/24, 2024/25)

**Curve-eligibility note (enforced in code, not prose).** NYISO is
**curve-INELIGIBLE for the flip**: its ICAP→UCAP translation-factor pairing (R5a)
is adjudicated but owner sign-off is **pending**
(`nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md` §3, Option D stands).
`constants.resolve_capacity_curve_eligible("NYISO")` returns **False**, so the
model's retirement / entry / storage screens price NYISO on its **fixed** anchor
even with `capacity_market_clearing` on and a vintage resolved. Pass 1 below is a
**diagnostic that validates the instrument** (the published-curve transcription),
independent of eligibility — a scoreable NYISO Pass 1 does **not** make NYISO
flip-eligible.

Each delivery year is now scored on its **own** published vintage (Annual Reference
Value, max clearing price, reference-point price) via
`resolve_demand_curve_vintage` — no frozen single-vintage anchor held across years
(the prior report's "only one vintage on disk, no scoreable year" is superseded).

**Pass 1B — curve price vs cleared spot, at the published position.**

| Delivery yr | Cleared $/kW-yr | Pub net-CONE | Model net-CONE | Reserve pos | Model curve | Resid | %err |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2020/2021 | 19.3 | — | — | — | — | — | — |
| 2021/2022 | 50.2 | — | — | — | — | — | — |
| 2022/2023 | 36.6 | — | — | — | — | — | — |
| 2023/2024 | 49.3 | 74.1 | 74.1 | 1.040 | 49.3 | +0.0 | +0% |
| 2024/2025 | 41.6 | 72.3 | 72.3 | 1.051 | 41.6 | +0.0 | +0% |
| _2025/2026_ | _51.4_ | _50.5_ | _50.5_ | _0.998_ | _51.4_ | _+0.0_ | _⛔ locked_ |

**Pass 1A — normalized SHAPE reproduction (price ÷ net-CONE at the published cap).**

| Delivery yr | Published cap frac | Model cap frac | Shape resid |
|---|--:|--:|--:|
| 2023/2024 | 2.069 | 2.069 | +0.0% |
| 2024/2025 | 2.337 | 2.337 | +0.0% |
| _2025/2026_ | _3.792_ | _3.792_ | _+0.0%_ |

**Findings.**
- **Scoreable, and the instrument is faithful per vintage.** 2023/24 and 2024/25
  reproduce their own cleared spot to **0%** at the published position, and the
  shape (cap fraction) to **0%** — the transcription is exact, and the model
  net-CONE now tracks each year's own Annual Reference Value (74.1, 72.3) rather
  than a frozen 50.5. This is the per-vintage anchoring prereq 3 wanted; the
  ±10-15% frozen-anchor level error the prior report flagged for NYISO is removed.
- **Sparse years handled explicitly (no interpolation).** 2021/22 and 2022/23
  publish **no** Annual Reference Value and **no** price cap (only a reference-point
  price + IRM), so they are **non-scoreable** — reported with dashes, priced on a
  flat anchor (reference × 12) in the model, never interpolated onto the later
  sloped curve (rule 13).
- **2025/26 locked** (2026-published SOM spot, rule 22) — greyed, excluded.
- NYISO cleared **at/below net-CONE every scoreable year** (positions 1.04-1.05,
  long side) — the curve correctly reads a persistently-long, cheap ICAP market.

---

## §3.4 (refreshed) — MISO, SEASONAL RBDC Pass 1 (PY2025-26)

The prior report's verdict was "**NOT VALIDATED at annual grain — needs the CR-3
seasonal split**." That split is now implemented (RC-1C). MISO's PRA clears
seasonally and the market settles capacity as a seasonal **SUM**
(`Σ_season ACP_season[$/MW-day] × days_season`); the shipped seam
(`SeasonalRBDC` / `seasonal_rbdc_price_per_firm_mw_yr`) reproduces that
construction. Each season's North/Central cleared price is placed on that season's
own model RBDC to recover its implied reserve position. daily net-CONE = 79,800 ÷
365 = **218.63 $/MW-day** (the flat requirement point; MISO publishes the seasonal
gross-CONE caps and the annual net-CONE, not a separate seasonal net-CONE).

| Season | Days | Cleared $/MW-day | if-all-yr $/kW-yr | Gross-CONE cap $/MW-day | Model cap frac | Implied reserve pos | Contribution $/MW-yr |
|---|--:|--:|--:|--:|--:|--:|--:|
| summer | 92 | 666.50 | 243.3 | 1384.4 | 6.332 | **0.988** | 61,318 |
| fall | 91 | 91.60 | 33.4 | 1399.6 | 6.402 | 1.029 | 8,336 |
| winter | 90 | 33.20 | 12.1 | 1415.1 | 6.473 | 1.042 | 2,988 |
| spring | 92 | 69.88 | 25.5 | 1384.4 | 6.332 | 1.034 | 6,429 |

**Annualized (seasonal SUM) = 79,071 $/MW-yr vs published North/Central net-CONE
79,800 $/MW-yr (−0.9%).**

**Findings.**
- **Scoreable at seasonal grain, and the pattern reproduces.** Summer's implied
  reserve position is **short** (0.988, near the cap) while fall/winter/spring sit
  **long** (1.03-1.04, near the zero-cross) — the observed **summer-at-cap /
  other-seasons-near-zero** concentration reproduces directionally, exactly the
  RC-1C expectation.
- **The seasonal SUM lands on net-CONE (−0.9%).** This is the headline: the annual
  capacity revenue a resource clearing all four seasons earns is ≈ net-CONE,
  concentrated in summer. The **old annual approximation** mis-annualized summer's
  $666.50/MW-day as if it ran all 365 days (the "if-all-yr" column: 243 $/kW-yr,
  ~3× net-CONE); the seasonal grain replaces that distortion.
- **One-position limit (documented, not a defect).** The model holds ONE annual
  accredited position and feeds it to all four seasons — it has no seasonal
  accreditation basis (seasonal firm MW), so its own-fleet (Pass-2-style) price
  cannot reproduce the concentration: it **over-states** at a short annual position
  (all four seasons priced near their gross-CONE caps) and **under-states** at a
  long one. This fleet-independent Pass 1 reproduces the concentration precisely
  *because* it uses each season's own published position; a Pass 2 (one annual
  position) cannot. Seasonal fleet accreditation is a future item — it is **not**
  invented here (rule 13). MISO has no capacity hindcast, so there is no Pass 2.
- **Pre-RBDC years are vertical-at-CONE.** PY2021/22-2024/25 used a vertical demand
  curve capped at CONE (FERC ER23-2977), now represented as vertical-at-CONE
  vintages anchored on North/Central gross CONE (LRZ 1-7 mean: 91.86 / 91.06 /
  103.04 / 123.50 $/kW-yr) with no sloped shape — replacing the prior hold-first
  stand-in that served them the PY2025-26 sloped RBDC (which invented slope).

---

## What this session changed vs the prior reports

| Section | Prior verdict | Refreshed (RC-1C) |
|---|---|---|
| **§3.3 NYISO** | "NOT VALIDATED (data-limited) — only one vintage on disk" | Scoreable per vintage (2023/24, 2024/25 at 0% shape/price resid); sparse 2021-22/2022-23 explicit; **curve-INELIGIBLE for the flip** (R5a, enforced in code) |
| **§3.4 MISO** | "NOT VALIDATED at annual grain — needs CR-3 seasonal" | Scoreable at **seasonal grain**; summer-short/others-long concentration reproduces; seasonal SUM = net-CONE (−0.9%); one-position limit documented |
| PJM / NEISO | (P-2A/N-5) | **Unchanged** (registry-reference model side, byte-stable) |

**Not touched (out of scope, unchanged from prior):** the PJM Pass-2 long-position
blocker, the ICAP↔UCAP basis anchor, and every gate item other than prereq 4. No
default was flipped (`capacity_market_clearing` stays default-off for all ISOs).

*Produced 2026-07-16 (RC-1C). No LP solved. No holdout year read or scored.
Nothing registered on any dashboard. Comparison only (rules 1/13/23).*
