# RESULT — NYISO-NEXT-16: `nyiso_iroquois_winter_spread` under the cutset link — 2026-09-30

- **Session:** NYISO-NEXT-16 (orchestrator; no LP in this container).
- **Pre-registration:** `docs/records/nyiso/PRECOMMIT-nyiso-next16-winter-spread-2026-09-30.md` (merged in PR #6909 before any shard; pin `38ea5423e3f7ff992f2a8ae69bf3fa2bde25f2b4`).
- **Phase 0:** `docs/records/nyiso/FINDING-nyiso-next16-c3b-2022-phase0-2026-09-30.md`.
- **Owner cards:** "Re-test, 5 yrs", then "Promote (override)".
- **Outcome:** keeper `2026-09-30-nyisonext16-winter-spread-span` (2022–2025) plus stamped `2026-09-30-nyisonext16-winter-spread-2021`. **Span CALIBRATED** (C3c the lone ledgered caveat). 2021 NOT-YET.

## 1. Gates (arm vs the NEXT-15 keeper's committed bundles, form 4)

Record: `results/phase0/nyiso/_nyisonext16_gates.json`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2(a)** east-zone annual gas − SOM annual, $/MMBtu (UW) | +0.054 (0.000) | −0.182 (0.000) | +0.068 (0.000) | −0.086 (0.000) | −0.558 (0.000) |
| **G-2(b)** DJF max-zone mean \|ΔLMP\| vs keeper, $/MWh | 9.47 | 11.74 | 2.88 | 6.07 | 10.19 |
| **G-3** link at its bound, % of h (band 1–50) | 17.6 | 18.6 | 14.8 | 5.4 | 3.1 |
| **G-4** Upstate_West h ≤ $0 | 0 | 0 | 0 | 0 | 0 |
| **G-5** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| **G-6** P1 load slack, GWh (keeper) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| **G-7** new D-4 rows (year, mechanism, plant) | none | none | none | bridge × CC_REGULAR 54574 | bridge × CC_REGULAR 55405 |

**Two gates fail. Neither is hidden.**

- **G-2(a) fails as drafted.**
  - The gate anchored every zone to its SOM annual. The east zones instead sit on the EIA Transco series plus the SOM spread.
  - The arm's east-zone annual equals the keeper's to 4 dp in every year (e.g. 2025 Capital_Hudson 5.4619 in both).
  - The miss is the pre-existing EIA-Transco vs SOM level gap, not the construction. Upstate_West, the zone the flag moves off the New England shape, conserves its SOM annual exactly.
- **G-7 fails.**
  - New: 2024 plant 54574 at 0.0047 TWh, and 2025 plant 55405 at 0.0015 TWh.
  - Cleared: 2022 plant 54574 and 2023 plant 8906.
  - Net D-4 failure count is 8 vs 8 on the span and 2 vs 3 in 2021.
- Under the pre-registered rule this was not promotable. The owner ruled "Promote (override)".

## 2. Reported (not gating)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C3a, keeper → arm | +11.4 → +11.1 % | +3.2 → +2.6 % | +5.6 → +5.4 % | −1.6 → −1.1 % | −9.2 → −8.6 % |
| C3b NRMSE, keeper → arm | 0.169 → 0.178 | **0.200 → 0.159** | 0.146 → 0.132 | 0.158 → 0.117 | 0.164 → 0.147 |
| price MAE $/MWh, keeper → arm | 11.89 → 11.72 | 26.50 → 24.98 | 9.56 → 9.34 | 9.45 → 8.77 | 24.96 → 23.75 |
| C8 ST_GAS forced share, keeper → arm | 22.9 → 19.9 % | 17.0 → 15.4 % | 11.6 → 12.1 % | 18.0 → 14.7 % | 14.4 → 12.9 % |
| DJF Capital_Hudson − UW spread: arm / keeper / measured DA | 3.5 / 3.1 / 21.2 | 8.1 / 6.4 / 50.4 | 2.4 / 2.1 / 15.3 | 3.4 / 3.0 / 11.1 | 7.1 / 6.5 / 27.2 |
| NYC ST_GAS TWh: keeper → arm (EIA-923) | 4.06 → 3.93 (1.98) | 5.03 → 4.79 (2.27) | 8.65 → 7.86 (2.56) | 5.38 → 5.16 (2.77) | — |

- No criterion goes PASS → FAIL in any year. Dispatch correlation (C4) rises every year.
- The winter east–upstate spread barely moves ($0.2–4 against a measured $10–50). The CENTRAL EAST object is untouched, as predicted (PRECOMMIT §6).

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `70700d0e22ab1fafce3371130ced144065456ccd` | 17 |
| 2022 | `b776d58d1e5fd2457c12da1a060cc9b7c94a1426` | 17 |
| 2023 | `a78d46de16dedf30bdfe67bf9e66a0a640a72057` | 17 |
| 2024 | `7c83b4fdfea151e94310a302c8ff36ef8240a112` | 17 |
| 2025 | `f2fe82ba5a2967b7111a1f2b7ba34ef079c93489` | 17 |

- **Retrievability.** The keeper bundle `nyisonext16_span` and the 2021 bundle land on `main` with this PR. The 2022–2025 legs are gitignored (rule 32 (d)). Recovering a leg not on `main` costs a re-solve (~5–7 min of LP per year).

## 4. What remains

1. **2021 C3a +11.1 %.** This is the owner's "fix 2021 first" block on the `complete` marker. The driver is Upstate_West shoulder over-pricing, the CENTRAL EAST object. The DF cap fails ex ante (FINDING §2), so the structural route is a separate E→F element, which is a design task.
2. **The two new bridge conduct rows** (plants 54574 and 55405), and ST_GAS plant 8906.
3. **2025 peak formation** (C3a −8.6 %). The downstate oil cap (about $19–25) flattens the winter gas spikes, and the trading gaps are interpolated (`nyiso_hub_gap_month_level` R).
4. **NYC steam** (2023 7.86 vs 2.56 TWh) and the in-city commitment requirement (MyNYISO access is owner-held).
5. **The `complete` marker.** The span reads CALIBRATED, but the owner's ruling holds the marker until 2021 clears.
