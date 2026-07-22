# CAISO reserve co-optimization A/B — finding (2026-07-06, L-10, issue #1492)

**Mechanism:** the CAISO per-generator energy+reserve co-optimization
(`reserve_config._caiso_design`), the reserve design CAISO was the only
registered ISO to lack. Spin + Non-Spin contingency products (BAL-002-WECC-3
`max(MSSC, 6% load)`, half/half) co-drawn on one ramp10-bounded pergen R pool;
shortfalls priced at the published tariff §27.1.2.3.5 scarcity demand curves
(spin 10% of the $1,000 soft bid cap flat; non-spin 50/60/70% at 70/210 MW).
Default-off flag `caiso_reserve_coopt`. Zero parameters fitted (rules 5/23).

**A/B:** both bundles replayed from caiso-51 at HEAD; only the reserve flags
differ. `caiso59_reserve_ab_base` = OFF, `caiso59_reserve_coopt` = ON.

## Result — real but largely INERT (the MISO lesson, confirmed)

On the real fleet the pergen pool = 1103 units → 11 (zone, fuel-class) R
columns, **Σ ≈ 12.9 GW deliverable 10-min ramp vs a ~2.2 GW requirement**. The
perfect-foresight LP clears the requirement from ramp-deliverable headroom in
almost every hour. Reserve prices fire in **~100 hours of 2023 only** (clearing
price up to **$800/MWh = spin $100 + non-spin $700** — confirms the co-opt sums
the two products' shortfall duals into the LMP, tariff §27.1.2.4), and are
**fully idle in 2024/2025**.

| year | C3a (vs RT) | Δ mean LMP vs A | C3c DA-expr >$200 (model vs actual) | Δ tail vs A | reserve-priced hrs (max) |
|---|---|---|---|---|---|
| 2023 | +20.3% | **+$0.47** | 483 h vs 41 h DA / 21 h RT — FAIL | +16 zone-h / 0 sys-h | 100 ($800) |
| 2024 | +35.3% | +$0.00 | 0 h vs 52 h DA — FAIL | 0 | 0 |
| 2025 | +42.7% | −$0.00 | 0 h vs 0 h — PASS | 0 | 0 |

## The ~455h-vs-21h driver question → NEGATIVE

The 2023 over-tail (model **483 h** DA-expressible vs **21 h** RT / 41 h DA
actual) is **not** a missing-reserve-scarcity-pricing gap. Adding the published
CAISO reserve co-optimization leaves it at 483 h (C3c unchanged, +16 zone-hours,
0 net system-hours) and moves the mean only +$0.47 (2023) / $0.00 (2024–25). The
over-tail is owned by the evening-merit / RA-commitment-uplift gap
(`FINDING-caiso-evening-merit-2026-07-04.md`), not by absent reserve co-opt.

## Disposition (rule 1)

Kept (default-off): a structurally-correct market mechanism stays in regardless
of the flat residual — the inertness is a supply-scoping/granularity result, not
grounds to revert. **Next increments** (each shrinks the pool's dominance over
the requirement, where it would begin to bind): storage reserve (dominant CAISO
AS provider, unbacked by the pergen builder today) → hydro (`ramp10 = 0`) →
regulation. NOT-YET determination is the governance-unattested probe status
(C6), not a mechanism failure.
