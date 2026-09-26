# RESULT — R-CAISO-5: CC outage-derate basis (X) ± Pastoria CO2 (E); 2019–21 intertie source (2026-09-26)

PRECOMMIT: `PRECOMMIT-r-caiso-5-2026-09-26.md`, pushed at `93a38eac` before any shard. The parent spent zero LP:
8 shards, one per year per arm (rule 36), all at that pin.

## Headline

- **Object 1 — C4 midday loading.** The midday gas gap is an **import diurnal-shape** defect: model net imports
  run +1.5 to +2.3 GW over EIA-930 at h8–16 in every month of 2022–25. No measured-input defect was found in the
  import shape, so no lever is taken on it.
- **One measured-input defect was found and fixed:** phantom CC capacity in full-plant outages (Moss Landing:
  207 MW kept in its all-units-out windows). The arm (X) replaces `unit_outage_lp_capacity_basis` with the
  registered `unit_outage_extract_basis_share`.
- **X is CALIBRATED** and improves C4 in all four years. The move is small: C4 2025 goes 0.299 → **0.297**.
- **XE (X + Pastoria CO2):** see §3.
- **Object 2 — 2019–21 intertie prices.** The STOP stands. No admissible measured hourly source exists (§5).

## 1. X — `2026-09-26-caiso-r5-cc-outage` (bundle `rcaiso5_X_span`), CALIBRATED

| | keeper `r4-intertie-dam` | **X** |
|---|---|---|
| C1 CC_REGULAR 2022 / 23 / 24 (TWh vs actual) | +2.45 / −0.38 / −0.50 | +2.27 / −0.50 / −0.63 |
| C1 CT_PEAKER 2022 / 23 / 24 | −1.27 / −1.66 / −2.32 | −1.21 / −1.59 / −2.26 |
| C3a load-weighted mean LMP vs RT, 2022 / 23 / 24 / 25 | +8.7 / +7.1 / +7.0 / +8.6 % | +8.8 / +7.3 / +7.1 / +9.1 % |
| C3b 2022 / 23 / 24 / 25 | 0.108 / 0.114 / 0.128 / 0.112 | 0.110 / 0.115 / 0.129 / 0.116 |
| C3c >$200 h, 2023 (actual 47) / 2024 (actual 35) | 55 / 0 (ledgered) | 59 / 0 (ledgered) |
| **C4 gas NRMSE 2022 / 23 / 24 / 25** | 0.265 / 0.251 / 0.260 / 0.299 | **0.263 / 0.250 / 0.258 / 0.297** |
| C8 CC_REGULAR forced, 2025 | 8.7 % | 8.6 % |
| Determination | CALIBRATED | **CALIBRATED** |

**Class Δ vs the keeper (TWh):**

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| CC_REGULAR | −0.17 | −0.11 | −0.14 | −0.37 |
| imports | +0.13 | +0.06 | +0.10 | +0.30 |
| CT_PEAKER | +0.05 | +0.08 | +0.06 | +0.12 |

**Moss Landing 2025:** 3.68 → 3.19 TWh (CEMS 2.19). It is **0 MW** in Jan 18–Feb 10 and Dec 14–30 (G-LIVE PASS).

**Stop gates.**

- **G-IDENT PASS.** Each leg differs from the keeper only in the two declared flags, plus new default-off fields
  recorded as False.
- **G-LIVE PASS.**
- **G-FOOT PASS.** CC_REGULAR 2025 −0.37 TWh.

**No load-bearing criterion regresses.** C3a 2025 moves +0.5 pt and C3b 2025 +0.004, both still PASS. The DOF
ledger stays 9/6, offer curves are unchanged, and there is no `authorized_price_tuning` block.

## 2. Why X is small against C4

The removed phantom capacity sits at over-dispatched plants (Moss Landing, Otay Mesa, Sunrise) and is roughly flat
across the day. Its replacement is imports and CT peakers. The C4 error is diurnal and import-driven (PRECOMMIT §1),
so X corrects a real input and moves C4 only 0.001–0.002.
