# RESULT — R-NEISO: NEISO 2019–2025 re-solved on corrected backcast inputs (2026-09-24)

**Run:** `2026-09-24-r-neiso-inputs-2019` · bundle `results/calibration/rneiso_span` (2019–2025) ·
**Control:** keeper `2026-09-22-hydro-5-neiso-ror` (`hydro5_neiso_ror_span`, 2020–2025), rule 29(b) form 4 ·
**Pre-registration:** [`PRECOMMIT-r-neiso-2026-09-24.md`](PRECOMMIT-r-neiso-2026-09-24.md), pinned
`c265c1c30ce0e51bffa5e0e5f5db76eafe54ae3e` before any shard launched.

## 1. Headline

| scope | keeper | R-NEISO |
|---|---|---|
| full span (keeper 2020–25 / R-NEISO 2019–25) | **CALIBRATED** (C3c ledgered) | **NOT-YET** — C1 fuel-mix FAIL |
| same span as keeper, 2020–2025 | CALIBRATED | NOT-YET (C1 2021, 2022) |
| **train tier 2023–2025** (the ISO determination, rule 30(c)) | CALIBRATED | **CALIBRATED** (same lone C3c caveat) |
| grade summary (full span) | scored 8 / target 7 / ledgered 1 / fails 0 | scored 8 / target 6 / ledgered 1 / fails 1 |

One load-bearing regression, confined to the held-out years: **CC_REGULAR under-generates in 2019, 2021
and 2022** (−4.66 / −3.17 / −3.12 TWh vs EIA-923, band ±2.8–3.1 TWh). 2023–2025 hold. Every other
criterion is PASS in every year; C3c is unchanged; C6 PASS (attested, multipliers byte-identical); C8 PASS.

Scored against the **committed** benchmark parts for 2020–2025 (the parts registration regenerated
were reverted to `HEAD`, so keeper and re-solve are read against one benchmark — §6). 2019's part is new.

## 2. Per-year criteria (keeper → R-NEISO; one cell where unchanged)

| year | C1 | C2 | C3a | C3b | C3c | C4 | C8 |
|---|---|---|---|---|---|---|---|
| 2019 | — → **FAIL** | — → PASS | — → PASS | — → PASS | — → PASS | — → PASS | — → PASS |
| 2020 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 2021 | PASS → **FAIL** | PASS | PASS | PASS | PASS | PASS | PASS |
| 2022 | PASS → **FAIL** | PASS | PASS | PASS | CAVEAT | PASS | PASS |
| 2023 | PASS | PASS | PASS | PASS | CAVEAT | PASS | PASS |
| 2024 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 2025 | SKIPPED | SKIPPED | PASS | PASS | CAVEAT | PASS | PASS |

Price (annual mean bias vs RT / hourly NRMSE), keeper → R-NEISO: 2019 — / +7.2 %, 0.107; 2020 +7.7 → +5.3 %,
0.128 → 0.123; 2021 +7.5 → +1.5 %, 0.129 → 0.118; 2022 −1.2 → −3.1 %, 0.086 → 0.092; 2023 −0.2 → 0.0 %,
0.084 → 0.095; 2024 +2.8 → +2.9 %, 0.150 → 0.156; 2025 +1.6 → +3.1 %, 0.059 → 0.065. C4 gas r: 2019 0.944;
2020–2025 within ±0.007 of the keeper. C3c tail hours unchanged (model 0 h in every year).

## 3. Class generation (TWh, P1): actual · keeper · R-NEISO

| year | CC_REGULAR | coal (BIT+PRB [+bare COAL]) | ST_GAS | CT_CHP (model) | CT_PEAKER |
|---|---|---|---|---|---|
| 2019 | 43.84 · — · **39.18** | 0.47 · — · 0.72 **[+2.09]** | 0.23 · — · 1.79 | — · 1.11 | 0.46 · — · 1.56 |
| 2020 | 46.07 · 47.04 · 44.70 | 0.17 · 0.07 · 0.30 **[+1.12]** | 0.32 · 0.13 · 1.17 | 0.36 → 1.07 | 0.62 · 0.27 · 0.21 |
| 2021 | 50.82 · 51.28 · **47.65** | 0.58 · 0.37 · **2.11** | 0.26 · 0.45 · **1.96** | 0.43 → 1.08 | 0.54 · 1.18 · 0.81 |
| 2022 | 51.24 · 51.06 · **48.12** | 0.35 · 0.72 · **2.93** | 0.21 · 0.23 · 0.34 | 0.45 → 1.08 | 0.64 · 1.95 · 1.74 |
| 2023 | 52.46 · 52.67 · 51.21 | 0.21 · 0.16 · 0.64 | 0.24 · 0.16 · 1.33 | — | 0.47 · 0.44 · 0.38 |
| 2024 | 56.74 · 57.03 · 56.12 | 0.26 · 0.13 · 0.40 | 0.12 · 0.06 · 0.75 | — | 0.59 · 0.85 · 0.80 |
| 2025 | 58.26 · 57.86 · 57.46 | 0.29 · 0.22 · 0.48 | 0.31 · 0.06 · 0.09 | — | 0.65 · 1.58 · 1.67 |

## 4. Root cause of the C1 miss (rule 14 — the accurate input stays; the defect is elsewhere)

The CC energy did not vanish: it moved onto the capacity the corrected fleet restored.

1. **Coal.** The keeper's canonical 2025ER fleet carried **108 MW of coal in every year** (one Merrimack
   unit at 14.2 MMBtu/MWh). The vintages carry both Merrimack units (438.5 MW), Bridgeport Harbor 3
   (257.6 MW to 2021-05) and Schiller (95 MW, 2019–20) at **measured CAMPD rates of 10.3–10.8**. In the
   high-gas years (2021 $3.72, 2022 $6.45 HH) the LP now runs them far above their real duty — 2.1 / 2.9
   TWh against 0.58 / 0.35 actual. Merrimack is a winter-reliability unit at 4–9 % CF (neiso-69). The
   input is right; what is missing is whatever keeps real New England coal off the margin (its delivered
   coal price and commitment economics). **Successor, not absorbed.**
2. **ST_GAS.** Restored Middletown (562), Newington (8002) and New Haven Harbor (6156) steam units take
   the ST_GAS fleet from 179–278 MW to 434–1,382 MW. The keeper's **ST_GAS offer bands are 0.754 / 0.811 /
   0.850** — set on price through the authorized channel when that class was a sub-300 MW sliver. On the
   corrected fleet those cut bands make ~1 GW of old steam cheap: 1.2–2.0 TWh vs 0.2–0.3 actual. Per
   rule 1(c) this lane did not touch the multipliers; re-deriving them on the corrected fleet is an owner
   decision (the channel's own conditions (b)/(c): ex ante, one config, not swept).
3. **Bare `COAL` class (a reporting defect, found here).** Bridgeport Harbor's coal rows read from the
   2019/2020 vintage tables do not resolve a coal supply class, so 2.09 / 1.12 TWh of model coal lands in
   a bare `COAL` class that the committed benchmark does not carry and C1 does not score. The regenerated
   benchmark parts add a `COAL` group; the committed ones do not. **Successor:** route vintage-table coal
   rows through the curated supply map (the partial-exit channel's `_register_partial_exit_coal_supply`
   already does it for its own rows).

2023–2025 hold because the restored coal and steam capacity is smaller there (Bridgeport and Schiller
retired; the ST_GAS fleet is 434–835 MW rather than 1.3–1.4 GW) and the 2023–24 gas price is lower.

## 5. What the inputs changed (phase-0 census, PRECOMMIT §5)

EIA-860 source 2019–2024 `vintage_<Y>` (was canonical); thermal MW 2019 23,488 → 25,326; mean unavailable
MW +261 to +348 from the short-gas family alone; class-table heat rate: **GenConn Middletown 57068 (oil,
187.6–194 MW) in every year** plus ≤1 MW, both absent from every eGRID vintage and every measured artifact.
The mid-vintage carry restored Pilgrim (2019, 674 MW nuclear) and **Mystic (2024, 1,493 MW)**, which the
F1 default had silently dropped (PRECOMMIT §3b — a cross-ISO defect in the F1 foundation, fixed here,
inert for every registered run). Partial-derate family: 0 NEISO windows, inert. Std extract +18/+20/+4
windows in 2019–2021 (F2 finding 5).

## 6. Registration, benchmark, matrix

- Registered `2026-09-24-r-neiso-inputs-2019` with `--no-prune`; the keeper is untouched and still the
  designated keeper. **The registration commit (bundle + sidecar + payload + 2019 bench part) is held on a
  separate draft PR stacked on this lane's PR**: `audit_keepers --check` E13 (rule 35(f)) fails any ISO
  carrying a registered run that is neither its keeper nor stamped to it, so the run can only reach `main`
  together with a promotion (which re-stamps the keeper and prunes the outgoing one). On a hold ruling the
  draft is closed and nothing reaches `main`. `bench/NEISO/2019.json.gz` is new. Registration also rewrote the committed 2020–2025
  parts (new plants joined the plant view; a `COAL` group; builder fingerprint `fb56b7e445d9 → f979bd82fd43`);
  those were **reverted to `HEAD`** so the keeper's determination is untouched, and both runs are scored on
  one benchmark. The scorer flags the 2020–2025 parts STALE at HEAD for both runs alike (builder drift that
  predates this lane).
- Attestation: keeper governance and DOF ledger inherited verbatim (8 entries / 6 residual);
  `offer_curve_by_group` SHA-256 byte-identical; **zero free parameters added** (`scripts/gen_rneiso_attestation.py`).
  `build_dof_ledger.py` would regenerate only 6 entries (dropping the hand-curated fossil offer-level scalar
  and the coal sigmoid entry), so it was not applied.
- Matrix (NEISO shard): `eia860_vintage_tracks_solve_year`, `measured_{coal,st,cc}_heat_rates`,
  `unit_outage_short_windows_gas`, `mid_vintage_exit_carry`, `partial_plant_exit_carry` **U → O**;
  `unit_outage_short_windows` stays **R** with the partial shape recorded armed-inert.

## 7. Retrievability (rule 34(e)) and shards (rule 33)

The composite is committed in its rule-15 shape (`results/calibration/rneiso_span`, 47 files, 7.9 MB) with
its sidecar and payload on the draft registration PR (§6) — that is everything a promotion needs,
**zero re-solves**; it reaches `main` when that PR merges with the promotion. Leg provenance (shard branches
are transport, rule 33(d)/(f)): 2019 `b00a0866`, 2020 `51e65f9a`, 2021 `015bd2ae`, 2022 `d35619ab`,
2023 `995972c8`, 2024 `e5927a0b`, 2025 `131dd041`. All seven shards archived after fetch + checkout +
`shard_check.py` PASS. Leftover refs `claude/rneiso-2019` … `claude/rneiso-2025` need the owner to remove
them (a session cannot delete refs).

## 8. Recommendation and the promotion question

**Recommend: do not promote as-is; promote after the two named successors.** The inputs are the correct
ones and the owner ordered them. The train tier stays CALIBRATED, so the ISO headline would not move
(rule 30(c)). But C1 fails in three held-out years, and the cause is identified and fixable: coal
economics and the ST_GAS bands were cut on the wrong fleet. Promoting now carries a known held-out C1 regression.
Rule 1 cuts the other way: a more faithful fleet that fits worse can still be the keeper. That trade is
the owner's to make.

**Owner: promote `2026-09-24-r-neiso-inputs-2019` to NEISO keeper (replacing `2026-09-22-hydro-5-neiso-ror`), or hold it?**
