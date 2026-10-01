# Capacity demand-curve re-validation after the P-2B basis migration — 2026-07-14

**Session.** N-5 / P-2B implementation (R1–R6) of the accreditation-basis memo
(`docs/handoffs/accreditation-basis-memo-2026-07-12.md` §4.2). This re-runs the
P-2A validation (`docs/handoffs/capacity-price-validation-2026-07-12.md`) against
the migrated code — Option A per-ISO published-basis consistency for PJM: the
UCAP-$ curve anchor (R1), the published-FPR requirement (R2), the ELCC-class
supply ledger (R3), and the basis-consistent payment seam (R4). **No LP was
solved**; Pass 2 restates the frozen 2021–2025 PJM hindcast ledger on the adopted
accreditation basis (the memo's §3.1 decomposition, automated through the shipped
resolver — a re-statement of a fixed fleet, never a re-tune, rules 1/13).
Reproduce with:

```
uv run python -m scripts.validate_capacity_prices --markdown
```

Governance (rule 22) is unchanged from P-2A: delivery years ≥ 2026 are locked
(greyed, excluded from every verdict); no dashboard artifact (capacity evolution
is forecast-mode only).

---

## 1. Verdict (lead)

- **The two damage terms P-2A quantified both closed to the memo's targets.**
  The migration removed the anchor-basis error entirely and cut the position
  error by roughly two-thirds, exactly as the memo's decomposition predicted —
  and it did so through published market-design parameters, not a fit.
- **The curve still pays $0 on the hindcast fleet, and that is now the honest
  residual.** With the basis errors gone, the remaining PJM length is the
  retirement miss (the model retires too little), owned by its own lane
  (G-30/G-31). The flip stays gated (P-2A §7 prerequisite 2 — position
  calibration — is still open).

## 2. Pass 1B — the anchor collapse (R1)

The uniform −22/−28 % anchor residual P-2A flagged is gone: the curve is now
scaled by the published **UCAP** net-CONE (77.431 $/kW-yr = 212.14 $/MW-day ×
365/1000) instead of the ICAP-annual 60.396, so it lands on the basis the auction
clears in.

| Delivery yr | Cleared $/kW-yr | Model curve | %err (P-2A) | %err (now) |
|---|--:|--:|--:|--:|
| 2025/2026 | 98.5 | 90.7 | **−28 %** | **−8 %** |
| _2026/2027_ (locked) | _120.1_ | _120.1_ | _−22 %_ | _+0 %_ |

Shape is untouched (Pass 1A still exact — 1.552 vs 1.552 for 2026/27), as it must
be: R1 moved only the dollar anchor. The residual that remains (−8 % on 2025/26)
is the frozen single-vintage net-CONE (the 2026/27 anchor held against a
2025/26 year whose own UCAP net-CONE was ≈83.5), a CR-2 follow-up, not a basis
error.

## 3. Pass 2 — the position collapse (R2 + R3)

Restating the frozen PJM hindcast ledger on the adopted basis — thermal at the
published ELCC class ratings (R3: coal .83, gas-CC .74, gas-CT .60, …) instead of
(1 − EFORd), and the requirement on the published FPR of each delivery year (R2:
2025/26 = 0.9380, plus the pre-reform-year fallback) — collapses the accredited
reserve position from **1.29–1.36** to **1.06–1.15**:

| Cal yr | Delivery yr | Firm MW | Req MW | Pos (P-2A) | Pos (now) | Model $ | Cleared | %err |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| 2021 | 2021/2022 | 148,825 | 135,677 | 1.292 | **1.097** | 0.0 | 51.1 | −100 % |
| 2023 | 2023/2024 | 153,805 | 133,876 | 1.363 | **1.149** | 0.0 | 12.5 | −100 % |
| 2024 | 2024/2025 | 157,815 | 138,879 | 1.349 | **1.136** | 0.0 | 10.6 | −100 % |
| 2025 | 2025/2026 | 159,134 | 150,605 | 1.296 | **1.057** | 0.0 | 98.5 | −100 % |

Of the P-2A excess, ≈ two-thirds was the basis mismatch (now removed) and ≈ one
third is real fleet error (the retirement miss). Every restated position lands in
the memo's predicted band (≈ 1.11–1.19; 2021/2025 a touch below as their FPR/ELCC
mix lands them nearer 1.06–1.10) — **still long**, still past the curve's ~1.045
zero-cross, so the curve still returns **$0** in every year including the 2025/26
shortage that cleared near the cap. This is the memo's explicit expectation: the
migration does not make the curve payable on the current hindcast fleet — the
remaining length is the retirement miss, which must not be laundered through
accreditation.

## 4. What did / did not change

- **Changed (PJM only):** the curve $ anchor (R1), the requirement construction
  (R2), the thermal + storage supply accreditation (R3), and the per-unit payment
  basis (R4). NEISO / NYISO / MISO anchors, curves, and positions are byte-
  identical (their bases are untouched — R5 leaves their pairing audits as
  citation-gated gap rows).
- **Did not change:** the curve SHAPES (Pass 1A exact everywhere); the flip
  default (`capacity_market_clearing` stays OFF — this session clears P-2A §7
  prerequisite 1, not 2–4); any backcast dashboard artifact (none — forecast-mode
  machinery); any LP solve.

## 5. Residual routing (post-migration)

| Term | P-2A magnitude | Now | Owner |
|---|---|---|---|
| Curve shape | ≈0 % | ≈0 % | — (validated) |
| ICAP↔UCAP anchor basis (PJM) | −22 % | **0 %** | closed by R1 |
| Requirement basis (mixed vintage) | ~−1 % | **0 %** | closed by R2 |
| Thermal supply basis (UCAP vs ELCC) | ~+18 % position | **0 %** | closed by R3/R4 |
| Frozen single-vintage net-CONE | ±10–15 % | ±8 % | CR-2 follow-up |
| Model accredited position too long | pays $0 | still $0 (≈1/3) | retirement calibration (G-30/G-31) |

Every remaining residual routes to an open lane — none is closed by bending a
published parameter (rules 1/11/23).
