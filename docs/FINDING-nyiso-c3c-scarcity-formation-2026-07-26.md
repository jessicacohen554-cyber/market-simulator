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

## 4. Result — the idle-headroom framing is REFUTED, and the reason is a ceiling

The nyiso-83 obligation probe (2024, vs the same-HEAD zero-delta control) settles
it. **The gate works exactly as designed — and it still cannot move C3c.**

| quantity (NYC zone, 2024) | control | probe | 
|---|--:|--:|
| reserve-dual hours > \$0 | 6 | **7,003** |
| reserve-dual mean | \$0.010 | **\$10.96** |
| reserve-dual max | \$28.1 | **\$43.8** |
| C3c hours > \$300 (any zone) | 0 | **0** |

Online-gating the published NYC + LI 10-minute families takes the locational
reserve constraint from *essentially never binding* (6 hours) to **binding in
~80 % of all hours**. So the idle-headroom diagnosis of §3 was **correct about
the binding** — idle capacity really was satisfying the load-pocket requirement
for free — and **wrong about the consequence**. The tail did not move by a
single hour.

**Why: the J/K locational demand curves are capped at \$25/MW.** The published
NYC and Long Island 10-minute and 30-minute reserve demand curves are
**\$25/MW** (Ancillary Services Manual §6.8 items 9, 10, 14, 15 — the same value
carried in `NYISO_RCPF_LOCATIONAL` and in the new LI family). A family whose
maximum penalty is \$25/MW can contribute at most ~\$25/MW of scarcity rent to
the LBMP no matter how deeply short the pocket is. The observed dual peaks at
\$43.8 precisely because the *nested* tiers ($40 SENY/NYC/LI, \$500, \$775) sit
above it — but nothing in the J/K stack approaches the \$300 gate.

**Therefore the J/K ladders are structurally incapable of producing the C3c
tail, and no further work on them can close it.** This is a ceiling, not a
calibration gap. The tail has to come from the tiers whose published penalties
are large enough to reach it — **NYCA 10-min/30-min (\$750) and 10-min spin
(\$775), and East 10-min (\$775)** — i.e. from **system- and East-tier**
reserve-supply tightness, not from load-pocket formation.

That redirects the lane. The remaining leads are the ones that act on those
tiers: the NYCA-tier reserve-supply tightness in
`nyiso-overrun-underrun-2026-07.md` §3, and the 2025 LI steam OOM commitment
growth (SOM 2025 +68 %, light-load VOLTAGE-driven, 73 days) — which is a
**commitment** driver, not a reserve-pricing one, and so would reach C3c only
indirectly by changing what is online when the NYCA/East tiers bind. Note also
that **2024 is the weakest year to test C3c on** (the keeper's own model tail is
0 there); the 2025 arm (keeper 9 h vs actual 42 h) is the informative one and is
where any successor should measure.

## 4a. Collateral result — the obligation is NOT a substitute for the floor

The same probe answers the charter's rule-19 substitution question, negatively:

| 2024 | control | probe | Δ |
|---|--:|--:|--:|
| ST_GAS TWh | 8.710 | 5.810 | **−2.900** |
| ST_GAS evening mean MW | 1,392 | 1,001 | −391 |
| ST_GAS overnight mean MW | 731 | 409 | −322 |
| ST_GAS evening/overnight ratio | 1.905 | **2.449** | +0.544 |

Dropping the eight NYC/LI `ST_GAS` floor limbs and replacing them with the
published in-pocket obligation **costs 2.9 TWh of downstate steam** — against a
2024 gap that was already −3.02 TWh, roughly doubling it. The displaced energy
goes to `CC_REGULAR` (+1.47), `CT_CHP` (+0.68), `CC_CHP` (+0.45) and
`CT_PEAKER` (+0.11), summing to +2.90 — an exact downstate ST→CC/CT merit
substitution at constant total energy.

The cause is not that the mechanism fails to bind (it binds in 80 % of hours).
It is that the obligation is written on the *pocket*, not on *steam*: its
eligible set is in-pocket steam **∪** fast-start GT (faithfully, per the
instrument), so the LP satisfies 620 MW of published requirement with the
**cheapest** in-pocket online capacity — the CTs and CCs — and lets the
expensive boilers go. The p25-derived floor forced steam *specifically*; the
published reserve requirement does not.

**Shape, however, improves**: the obligation's steam is *more*
evening-concentrated than the floor's (ev/ng 1.905 → 2.449), which is the
direction the charter's acceptance criterion #3 asks for. The mechanism is
shape-faithful and level-insufficient.

**Disposition.** This is the outcome the instrument survey flagged as most
likely: the published reserve ladder is **not** the instrument that drives
in-city steam. The real driver is the non-public Con Edison load-pocket
procedure — the one the MMU itself reports it cannot see (41–42 % of NYC
reliability commitments "unverified"). So:

- the **rule-19 substitution is refuted** — the obligation cannot replace the
  NYC/LI `ST_GAS` floor limbs, and the floor stays;
- this is **not** a rule-1 [R-STRUCT] violation. The mechanism is not being
  rejected because a residual moved the wrong way; it is being rejected as a
  *substitute* because it provably does not act on the class it was required to
  replace. Rule 19 asked for replacement-or-reconciliation, and replacement has
  now been tested and failed;
- the **published LI ladder is a separate question** (a rule-14 omission fix
  that stands on its own) and is isolated by the `nyiso83_probe_lionly_2024`
  arm rather than being judged through the substitution's failure.

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
