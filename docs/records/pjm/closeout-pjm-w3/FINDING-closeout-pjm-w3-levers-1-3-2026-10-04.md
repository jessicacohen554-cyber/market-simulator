# FINDING — closeout-PJM-w3 phase 0, levers (1)–(3): no admissible charter without an owner ruling (ZERO LP)

Lane `closeout-PJM-w3`, desk direction 2026-10-04 (stacked on the Elliott probe recipe). Elliott lever (4): see
`FINDING-closeout-pjm-w3-elliott-identity-2026-10-04.md`.

## (1) C1 COAL_BIT 2019–21 (+19.73 / +12.74 / +16.72 TWh): no new evidence, so not chartered

The owner's standing ruling (R-55) is "find a mechanism to get it to decommit". The closeout-PJM-decommit lane
(#7159, R-56) measured every structural decommitment form on CEMS. It identified a measured CAMPD no-load,
`heatInput = a + b·gross`, with R² 0.96–0.98 on 0.96–0.99 of capacity. It priced start-up and min-down, and
measured the dark-spell share. Its result:
- Every form large enough to close 2019–21 removes as much or more coal in the 2023/24 controls.
- The three-part form (a1) takes 1.2–3.3 TWh off the fail years and 4.5–6.1 TWh off the controls.
- At real zonal DA prices it removes 5.7–13.9 TWh off the fail years and 11.5–13.6 TWh off the controls.
- So real-fleet decommitment is not year-discriminating at equal economics. The carrier is year-specific conduct.

Measured CEMS on/off and low-load data are exactly what that lane used (B0, B4), so a re-test is barred (rule 28).
The other measured route, PJM's DataMiner energy offers, is already adjudicated: `measured_offer_surface` is R,
and the coal offer-margin cells are instrument-blocked because the corpus is unit-masked. **Re-open trigger:** a
year-varying measured driver of coal commitment conduct. Candidates are unit-identified offers, which are not
public, or coal contract or take-or-pay terms by plant-year. The second is admissible only through the R-3
receipts/stocks overlay, which acts in the opposite direction (it holds coal on).

## (2) C1 CC_REGULAR 2022 (+8.59 TWh on the Elliott recipe): passes only with an owner ruling

On the Elliott recipe the bar is −0.59 TWh, against −0.96 on the keeper. From the closeout-PJM-cc22 reach table
(#7166 §3):

| candidate | 2022 CC Δ | admissibility |
|---|---|---|
| (A) `mustrun_online_frac_per_year`: own-year CEMS CC window instead of the 2023–25 pooled window for 2020–22 (existing field, zero src) | −0.28 to −0.37 | **admissible** (rule-14/17 vintage repair; its coal sibling is K) |
| (B) nuclear rating basis: the R-35 monthly CF rows clip at 1.0 in **January and December of every year** (winter ratings above the model's pmax); model nuclear is −0.78 TWh vs the 923 bench in 2022 | ≤ −0.37 | needs an **owner ruling**: a capacity-basis change to a frozen derive (rule 23). The honest form is a nuclear winter-rating basis, not an un-clip, because availability cannot exceed 1 |
| **(A) + (B)** | **−0.65 to −0.74 → +7.85 to +7.94: PASS** | (A) admissible; (B) owner-gated |
| (A) alone | +8.22 to +8.31: still FAIL | — |

With the keeper as base the bar is −0.96, and (A)+(B) misses. The flip therefore depends on the Elliott probe being
the base, and FINDING-elliott-identity §5 questions that base.

## (3) C3a/C3b 2025: closed

R-37 ("Documented FAIL; no re-open") stands. No new evidence: the online-gated reserve pool frontier candidate is
the only open object, and `pjm_reserve_pergen_sync` (R, DO-NOT-REDO) already tested the tightest product definition.

## Owner asks (via desk)

1. **Elliott card:** rule on the probe with the §5 disclosure (compensating errors).
2. **Nuclear winter-rating basis (B):** is a seasonal nuclear rating (EIA-860 winter capability) admissible as the
   denominator, so the Jan/Dec CF rows stop clipping (rule 14)? It would ride with (A) on one 7-shard solve.
3. **Firm export schedules, 23–24 Dec 2022** (data), for the Elliott export half.
