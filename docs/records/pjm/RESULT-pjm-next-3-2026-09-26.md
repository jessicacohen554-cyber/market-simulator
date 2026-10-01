# RESULT — PJM-NEXT-3: per-unit fuel routing of outage windows (card 2) + phase 0 on cards 1/3/4 (2026-09-26)

Run **`2026-09-26-pjm-next-3-unitfuel`** (bundle `results/calibration/pjmnext3_c2_span`, 2019–2025, one shard per year
at `54849585`, composed at zero LP). Control: keeper `2026-09-25-pjm-next-2-joint`'s committed bundle (rule 29(b) form 4;
G-DRIFT hunk-by-hunk INERT, PRECOMMIT §4). **PROMOTED 2026-09-26** on the owner's ruling ("If structural integrity
improves but gates regress that may still be a keeper"); the outgoing keeper was pruned (rule 35).

Pre-registration: `docs/PRECOMMIT-pjm-next-3-card2-unit-fuel-routing-2026-09-26.md`. Zero-LP cards 1/3/4:
`docs/FINDING-pjm-next-3-phase0-cards-1-3-4-2026-09-26.md`.

## 1. Card 2 — the mechanism

`unit_outage_unit_fuel_routing` (default False; zero free parameters). At a plant whose steam generators burn different
fuels in the solved year's EIA-860 vintage, each CAMPD window now derates its **own** generator's fuel slice. Before
this, one facility tag routed every unit's window to one slice. Companion `campd-unit-outages-memberrepair-unitfuel-PJM.csv`
(sha `ab6e163c`) = the membership-repaired extract with 66 re-tags: Montour 3149 (2023, 2024) and Brunner Island 3140 (2019).

## 2. Determination (same scorer, same benchmark)

Both NOT-YET. **Zero criterion flips.** The training span still fails only C1 CC_REGULAR 2024.

| row | keeper | new keeper | predicted |
|---|---|---|---|
| C1 CC_REGULAR 2024 | −10.07 FAIL | **−9.33 FAIL** | 0 to +2 TWh ✓ (+0.74) |
| C1 COAL_BIT 2024 | +3.62 | **+0.93** | −2 to −4 ✓ (−2.69) |
| C1 ST_GAS 2023 | +5.22 | **+2.63** | −1.5 to −3 ✓ (−2.59) |
| C1 CC_REGULAR 2023 | −2.71 | −1.90 | — |
| C1 ST_GAS 2024 | +1.73 | +2.79 | — |
| C1 COAL_BIT 2019 | +12.91 FAIL | **+13.98 FAIL** | +0.5 to +1.5, against interest ✓ (+1.07) |
| C3a mean LMP 2023 / 2024 | +4.2 / −2.0 % | +4.7 / −1.7 % | PASS both |
| C3b NRMSE 2019 / 2023 / 2024 | 0.126 / 0.120 / 0.119 | 0.125 / 0.121 / 0.120 | PASS both |
| 2020, 2021, 2022, 2025 | | class energy identical | inert by construction ✓ |

Slack and dump 0.0 in every year. C2, C4, C6, C8 PASS; C3c CAVEAT (unchanged).

## 3. Cards 1, 3, 4 (zero LP; details in the FINDING)

- **Card 1** — CC_REGULAR 2024: the deficit sits in RGGI-state (NJ/DE/MD) and Dominion plants. They run the right
  hours but at low load. Their econ offers ($34.5 EMAAC, $38.2 SWMAAC) sit above the model's east prices (~$30.5)
  because of RGGI (+$9.7, `K`) and the MD/VA state-average delivered gas basis (+$0.95/+$0.63). The 8-zone network
  carries a W→E spread about a quarter of the actual one. No lever is ready. A hub-commodity gas basis is data-blocked.
- **Card 3** — COAL_BIT 2021: commitment is right, but units load ~10 CF points too high. The coal econ rung ($32.9)
  clears ahead of CC econ ($37.0). The 2019–2022 mid-curve floors read the POOLED ladder. Follow-on: year-own 2019–2022
  offer tables (DataMiner serves 2021).
- **Card 4** — the interface freeze is inert (the seam ladder covers 2019–2025). The 2019/2020 over-shoot is the
  flat-stack trough (`G`).
- **Card 5 (F2 overwrite)** and **card 6 (`retiree_cems_cap`)**: owner questions, not acted on.

## 4. Governance and retrievability

- **Attestation:** DOF ledger carried verbatim; `authorized_price_tuning.used = false`
  (`scripts/gen_pjmnext3_attestation.py`).
- **Retrievability:**
  - The composite's slim set is committed on `main` with this PR.
  - The per-year legs (with dispatch parquets) are gitignored on local disk.
  - Leg SHAs are recorded in `.gitignore` as provenance only. Treat any leg recovery as a re-solve.
- **Shards:** all 9 archived (7 + 2 relaunches after an OOM on disk-starved swap and a permission stall). Leftover
  branches for the owner to clear: `claude/pjmnext3-c2-{2019..2025}`.
