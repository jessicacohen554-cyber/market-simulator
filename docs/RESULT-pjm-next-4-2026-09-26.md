# RESULT — PJM-NEXT-4: the measured 2019 mid-curve table (card 1); card 2 data-blocked (2026-09-26)

Run **`2026-09-26-pjm-next-4-midcurve2019`**. Bundle `results/calibration/pjmnext4_c1_span`, 2019–2025, one shard per
year at `7394a279`, composed at zero LP.

- **Control:** the keeper `2026-09-26-pjm-next-3-unitfuel`'s committed bundle (rule 29(b) form 4, G-DRIFT all INERT).
- **Pre-registration:** `docs/PRECOMMIT-pjm-next-4-card1-midcurve-2019-2026-09-26.md`.
- **Status:** **PROMOTED 2026-09-27** on the owner's ruling ("If structural integrity improves but gates regress that may still be a keeper"). The outgoing keeper `2026-09-26-pjm-next-3-unitfuel` was pruned (rule 35); `audit_keepers` and `check_promotion_completeness` pass.

## 1. What changed

One data artifact and no solve-path code: the PJM mid-curve surface gains a **2019** table.

- **Source:** PJM DataMiner2 `energy_market_offers` 2019, 12 month-files, 10.66 M rows.
- **Method:** `derive_pjm_offer_midcurve.py --merge-into-existing` adds 2019 only. Every 2020–2025 table and the
  pooled forward ladder stay byte-identical (21/21 canonical-sha).
- **Premise correction:** 2020–2022 already had year-own tables since pjm-h9c. The handoff's "2019–2022 read pooled"
  was stale. Only 2019 was on the pooled blend.
- **Publisher gap, carried as published:** 2019-11-08 → 12-05 serves about 138 fewer units per hour.

## 2. Determination (same scorer, same benchmark)

Both runs are NOT-YET. The training span 2023–2025 is **byte-identical**, so C1 CC_REGULAR 2024 −9.33 still fails.
The only differences are in 2019:

| 2019 | keeper | arm | pre-registered |
|---|---|---|---|
| C1 COAL_BIT | +13.98 FAIL | **+25.84 FAIL** | +0.5 to +2.5 (direction ✓, size 5× larger) |
| C1 CC_REGULAR | −0.58 PASS | **−8.54 FAIL** | falls ✓ |
| C1 CT_PEAKER | −3.97 | −4.67 | — |
| C3a mean LMP (RT) | +10.7 % FAIL | **+7.6 % PASS** | 0 to −2 pts (moved −3.1) |
| C3b NRMSE | 0.125 | **0.099** | no direction |

- **2020–2025:** class energy and load-weighted LMP identical to 3 decimals, as expected by construction. This also
  confirms the rule-36 per-year replays reproduce the keeper.
- **Other criteria:** C2, C4, C6 and C8 PASS; C3c CAVEAT (all unchanged).
- **Legitimacy diagnostics:** 42 fail rows vs 40 for the keeper. The two added rows are D4 2019 rows in the same
  families, and C8 stays PASS.

## 3. What it says

- **The coal over-run is not a mid-curve-table defect.**
  - 2020–2022 over-run coal (+10.5 / +20.7 / +8.1 TWh) on their own measured tables.
  - Giving 2019 its own table makes 2019 worse.
- **Why the move is so large.** The pooled blend placed coal econ ($26.68 cap-weighted) a hair under CC econ ($27.20).
  PJM's own 2019 offers put coal at $25.05, clearly ahead, so about 8 TWh of CC flips to coal. The large move shows how
  thin the 2019 merit order is.
- **Where to look next:** the coal rung itself. The 2019 coal econ mc_base is $21.8/MWh. Candidates are delivered coal
  price, the passthrough sigmoid centre (pjm-170 measured it $1.18/MMBtu low) and committed/min-load behaviour. This
  is not a table problem.
- **Structural reading (rules 1 and 14):** the arm replaces an estimate (a 2020–2025 blend applied to 2019) with the
  publisher's own year. It is the more faithful input even though C1 2019 worsens and C3a 2019 improves.

## 4. Card 2 — CC_REGULAR 2024: DATA-BLOCKED (no solve)

There is no admissible daily east-PJM hub commodity series (Transco Z5/Z6-non-NY, Tetco M3, Eastern Gas South, Cove
Point):
- EIA's free ICE natgas workbooks stop at 2017.
- The EIA NGWU daily table carries four points, none of them in PJM.
- The repo's Transco Z6 series is NYC delivery, which is a rule-14 boundary misalignment for NJ/MD/VA, and it carries
  the NGI licence flag.

A licensed hub index is the owner's call (PRECOMMIT §6).

## 5. Card 3 — owner-blocked, not acted on

- (a) The F2 full outage-extract re-derive.
- (b) `retiree_cems_cap`: delete or repair (rule 26).

## 6. Governance and retrievability

- **Attestation:** `scripts/gen_pjmnext4_attestation.py`. DOF ledger carried verbatim, zero entries added, zero config
  deltas, `authorized_price_tuning.used = false`.
- **Retrievability:** the composite's committed file set is on this branch → `main`. The per-year legs (with dispatch
  parquets) sit gitignored on this session's local disk. They will not survive the session. Leg SHAs are in
  `.gitignore` as provenance only. **Promotion from this state costs zero re-solves** because the registered composite
  is on `main`. Recovering the per-year dispatch parquets would be a 7-shard re-solve (~20 min each, run in parallel).
- **Shards:** all 8 are archived (7, plus a 2021 relaunch after the first 2021 shard stalled idle having pushed
  nothing).
- **Leftover branches for the owner to clear:** `claude/pjmnext4-c1-{2019,2020,2022,2023,2024,2025,2021b}`.
