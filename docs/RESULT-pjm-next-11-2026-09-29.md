# RESULT — PJM-NEXT-11 (2026-09-29): offered EcoMax falsified; the COAL_BIT over-run is coal's price RESPONSE, and the model's price floor is too high (zero LP)

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix` (bundle `pjmnext8_xf_span`). **Zero LP, zero shards, nothing registered, nothing promoted.** Detail: `docs/FINDING-pjm-next-11-offered-ecomax-2026-09-29.md`.

| card | result |
|---|---|
| 1 — offered EcoMax (owner asked this session to fetch the corpus) | Corpus re-fetched, 2019–2025, 84 month-files. LONG_RUN EcoMax ÷ curve top = 0.923–0.949, flat across hours. Cap effect on C1 ≤ −1.9 TWh, and the year order is wrong. **Falsified as the lever.** The feed has no fuel-conservation or self-schedule field. |
| 2 — 2022 | Explained. PJM's own 2022 LONG_RUN offers were about 2× delivered fuel cost, and the keeper already carries them through the measured floor. The delivered coal/gas ratio was the wrong operand. |
| 3 — C3a/C3b | 2022 confirmed as the tail-compression object. **C3a 2019/2020 are not compression: they are a price-floor excess**, present in every year. C3a passes in 2021 and 2023–25 by cancellation. |
| audit (a) (owner card *"Do both audits here"*) | The over-run is **response, not price**: +17.9 / +11.8 / +15.1 TWh of the +18.8 / +15.7 / +13.7 TWh gap in 2019 / 2021 / 2025. Real coal is much flatter in price than model coal. |
| audit (b) | The model's p10 implied heat rate is 6.9–8.4 vs actual 4.8–5.5 in every year. Real PJM prices below gas cost at the low end; the model does not. |

**Status (unchanged):** training span 2023–2025 NOT-YET on one row (CC_REGULAR 2023, recorded east→south limit). Run-level 2019–2025 NOT-YET, 14 out-of-span rows, reported and non-gating (rule 30(c)).

**OPEN** (not a limit): COAL_BIT 2019/2021, CT_PEAKER 2021, C3a 2019/2020.

**Next test (PJM-NEXT-12):** intake PJM's measured DA self-scheduled MW by fuel and year, and marginal-fuel shares (IMM State of the Market; not in the repo). Then test coal self-scheduling as the operand behind real coal's price-flat output and the low price floor.

**Retrievability:** nothing solved. The offers corpus is gitignored and must be re-fetched (about 75 min with 7 parallel year jobs; a job peaks at about 3.2 GB when saving, so provision swap).
