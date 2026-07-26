# NYISO C3c scarcity formation — where the missing tail is, and what it is not (nyiso-83)

**Date:** 2026-07-26 · **Session:** nyiso-83 (in-city commitment adjudication lane) ·
**Basis:** the nyiso-81 keeper's committed hourly sidecars
(`results/calibration/nyiso81_floor_rederive/hourly/system_<year>.parquet`) — **no
LP replay**, no new solve. · **Status:** partial diagnosis. It localizes the
residual and **refutes one framing**; the leading structural hypothesis is now
under test by the nyiso-83 obligation probe rather than asserted here.

## 0. The residual

C3c gates the count of hours the LP's **max zonal dual** exceeds the per-ISO
threshold (`TAIL_THRESHOLD["NYISO"] = $300`, `scripts/calibration_verdict.py`)
against the committed RT hourly actual tail. The keeper:

| year | model h > $300 | actual RT h > $300 |
|---|--:|--:|
| 2023 | 3 | 10 |
| 2024 | 0 | 12 |
| 2025 | 9 | 42 |

This is a **current-main property**, not a keeper artifact: the drifted control
(`2026-07-26-nyiso-79-control`) reproduces 3/0/9 identically. The gap widens
with the year, and 2025 is the worst cell (9 vs 42).

## 1. The tail the model *does* produce is entirely Zone K

Recomputed per zone from the keeper's own hourlies (max-zonal-dual basis, the
gated quantity):

| year | Capital_Hudson | Lower_Hudson | NYC | **Long_Island** | Upstate_West | any-zone |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 0 | 0 | 0 | **3** | 0 | 3 |
| 2024 | 0 | 0 | 0 | **0** | 0 | 0 |
| 2025 | 0 | 0 | 0 | **9** | 0 | 9 |

**Every scarcity hour the model produces is a Long Island hour.** NYC, the
Lower Hudson and upstate never clear $300 in any training year. Whatever is
missing is therefore not "a bit more of the same" — the model has no NYC/SENY
scarcity-formation channel that reaches the threshold at all.

The load-weighted price confirms the tail is compressed rather than merely
sparse — it never approaches the threshold in any year:

| year | p99 | p99.9 | max |
|---|--:|--:|--:|
| 2023 | \$59 | \$122 | \$130 |
| 2024 | \$108 | \$168 | \$174 |
| 2025 | \$173 | \$208 | \$296 |

## 2. What this evidence does NOT show — a correction worth recording

An earlier reading of the same sidecar treated the **zone-identical**
`reserve_price` column (12.5 / 28.1 / 177.3 max, identical across all five
zones *and* the external node in every year) as evidence that the locational
reserve families never bind while the NYCA families do.

**That inference is unsupported and must not be built on.** The writer
(`scripts/run_calibration_full.py`, the `system_<year>.parquet` block) computes
a single system-wide series `rp` and assigns `"reserve_price": rp` inside the
per-zone loop — the column is **broadcast by construction**, so it is identical
across zones in every run of every ISO and carries no locational information
whatsoever. The per-family duals (`DispatchResult.reserve_price_by_family`) are
**not** in the committed sidecar, so **locational binding cannot be tested from
the keeper bundle** — it needs a replay that persists them.

What the system series *does* support: the NYCA-tier curve is entered but never
deeply — 22 / 6 / 66 hours with a non-zero dual, peaking at \$12.5 / \$28.1 /
\$177.3 against published RCPF max penalties of \$750–775. So system-wide
reserve shortage is priced, mildly, and is far from the curve's deep steps.

## 3. The leading structural hypothesis (now under test, not asserted)

The candidate root cause is the one the `nyiso_synchronised_reserve` docstring
already names for the NYC peaker case: the locational reserve families draw
**idle-allowed** headroom (`sum_g P + R <= sum_g cap`), so any idle downstate
capacity satisfies a load-pocket requirement at zero cost and the RCPF never
prices. If that holds at the J/K ladder level, no amount of downstate tightness
can produce a locational shortage dual, and the only scarcity that can ever
reach the tail is the NYCA-tier one — which is exactly the shape §1 shows.

This session built the mechanism that tests it directly:
`nyiso_incity_commitment_obligation` (commit `fa9fc78`) re-classes the published
NYC + LI 10-minute families onto an **online-gated** in-pocket class, and
`nyiso_li_locational_reserve` adds the Zone-K ladder that was absent entirely.
The nyiso-83 2024 A/B probe (vs a same-HEAD zero-delta control, because the
replay environment's solver/pandas versions differ from the keeper's recorded
ones) is the test. **Its outcome — including a null result — belongs in this
document's §4 before the hypothesis is treated as settled.**

## 4. Result

*(To be completed by the probe. If the tail does not move, the idle-headroom
framing is refuted for the J/K families and the lane's next lead is the
NYCA-tier reserve-supply tightness noted in
`nyiso-overrun-underrun-2026-07.md` §3 plus the 2025 LI steam OOM commitment
growth — SOM 2025 +68 %, light-load VOLTAGE-driven, 73 days — which is a
commitment driver rather than a reserve-pricing one.)*

## 5. Standing note for whoever picks this up

- The `reserve_price` sidecar column is **not** per-zone. Any future locational
  claim needs `reserve_price_by_family` persisted from a replay; do not repeat
  the §2 mistake.
- 2025 is where the residual concentrates (9 vs 42) and is also where the
  measured NYCA reserve dual actually bites (66 hours, \$177 peak) — a 2025-led
  diagnosis will see the most signal, but any mechanism change is still scored
  leave-one-year-out within 2023–2025 (rule 22) before promotion.
- No out-of-training year was touched: NYISO carries no calibration-complete
  marker, so 2022 / 2019 / ≤2021 / H1-2026 remain quarantined.
