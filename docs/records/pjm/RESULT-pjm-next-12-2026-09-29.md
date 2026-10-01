# RESULT — PJM-NEXT-12 (2026-09-29): coal self-scheduling falsified as the COAL_BIT lever; coal was the price-setter behind C3a 2019/2020 (zero LP)

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix`. **Zero LP, zero shards, nothing registered or promoted.** Detail: `docs/records/pjm/FINDING-pjm-next-12-selfsched-marginal-2026-09-29.md`.

| card | result |
|---|---|
| 1 — intake | PJM IMM SOM §3, 2019–2025, is now in `som-competitive-conduct` (105 PJM rows). It covers the DA offer must-run share by unit type, RT marginal-unit shares by fuel, and the RT LMP fuel components. |
| 1 — self-scheduling | **Falsified.** Coal's must-run share is lowest in 2021 (18.7 %) and highest in 2023/24 (27.6 / 29.6 %), the opposite of what the hypothesis needs. A must-run block is a floor, not a cap, and a floor is already armed (`coal_mustrun_per_plant` K). No design card, no solve. |
| 2 — marginal fuel | Coal set 24–26 % of RT LMP in 2019/2020 vs 7–14 % in 2021–25. That discriminates **C3a 2019/2020** but not the COAL_BIT over-run. Real prices sit below efficient-CC gas cost in 26–45 % of hours; the model's do in 0–3 %, in every year. |
| 3 — sigmoid fallback | Not run: the intakes were reachable. |

**Status (unchanged):** training span 2023–2025 NOT-YET on one row (CC_REGULAR 2023, east→south limit). Run-level 2019–2025 NOT-YET, 14 out-of-span rows (reported, non-gating, rule 30(c)).

**OPEN** (not limits): COAL_BIT 2019/2021/2025, CT_PEAKER 2021, C3a 2019/2020 and the all-year sub-gas-cost floor.

**Next tests (PJM-NEXT-13):**
1. Coal **availability** vs dispatch: compare the model's per-plant-month available MW with CAMPD monthly max output, by year.
2. **Production-area gas** (replacement cost) vs the keeper's delivered-cost gas.
3. The model's coal-set LMP share, reconstructed from band hourlies, vs the IMM's.

**Retrievability:** nothing solved. The SOM PDFs are re-fetchable from the URLs in the raw README; the probe runs in about 1 min from committed files.
