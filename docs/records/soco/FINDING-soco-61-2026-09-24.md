# FINDING — SOCO-61 (2026-09-24): a 313 MW CC turbine that did not run in 2024 was modelled fully available; outaged, promoted

**Lane** SOCO-61 · **DATA PROFILE** soco · **Model** Opus (rule 27 — scope wrote `src/` and `scripts/`).
**Control of record** `2026-09-23-soco60-boundary-span`, rule 29 (b) form 4. Its per-plant legs were
recovered at zero LP; all 12 hourly sidecars were byte-identical to the committed composite.
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-61-2026-09-24.md`, pushed at `1d7edc1b` before any LP.
Addendum A (rebase + G-DRIFT) was written before any leg was read.
**Run** `2026-09-24-soco61-dark-unit` (bundle `results/calibration/soco61_dark_unit_span`). **PROMOTED
TO KEEPER 2026-09-24** on the owner's standing ruling (§6).

---

## 1. HEADLINE

1. **Object: (1) the thin 2024 CC_REGULAR margin and (2) CC per-plant error.** Of the three routed
   leads, only one had a measured input behind it:

   | lead | finding |
   |---|---|
   | CC capability | E B Harris, H A Franklin and Central Alabama run **below** their measured capability, so their overshoot is economic. |
   | Coal availability | Coal runs at 0.35–0.70 of its model availability. The under-dispatch is merit order (SOCO-56); there is no availability lever. |
   | ST/CC fuel separation | Still has no forward-regenerable input. Not opened. |

2. **Lindsay Hill (55271) was the one exception.** Its unit CT3 (313.1 MW) filed all 8,784 hours of
   2024 dark, but the model carried it fully available. The per-unit outage deriver skips a
   never-producing unit, and the `eia923_netzero` hook is plant-grain, so CT3 fell through both.
3. **The repair.** New registered field `campd_dark_unit_year_windows` and deriver flag
   `--dark-unit-years`, with zero free parameters and every condition categorical. The deriver adds
   one full-year window when all of these hold:
   - the unit's own CAMPD id is dark for every hour of the year;
   - the same id produced in an adjacent year;
   - a peer unit at the plant ran.

   The new `-perunitdark-` extract is the `-perunit-` extract re-derived byte-identically, plus one row.
4. **Result:**
   - No gate status moves.
   - 2024 CC_REGULAR goes +4.43 → **+3.14 TWh**, share +2.7 → **+2.2 pp**, so its margin widens 0.3 → 0.8 pp.
   - CC per-plant Σ\|model − 923\| in 2024 goes **11.07 → 9.28 TWh**.
   - Lindsay Hill goes 3.485 → **1.651 TWh**, against 1.752 TWh EIA-923.
   - **12 of 12 predictions landed in band.**
5. **Worse, reported:** 2024 CT_PEAKER +1.73 → **+2.36 TWh** (+0.7 → +1.0 pp). The turbine's energy
   partly moves to peakers, as predicted.

## 2. PREDICTIONS (PRECOMMIT §5)

| # | prediction | outcome |
|---|---|---|
| P1 | 2023 and 2025 sidecars match the keeper's | **CONFIRMED**. Content is identical; bytes differ only because the legs were written with pyarrow 24.0.0 vs the keeper's 25.0.1. |
| P2 | Lindsay Hill 1.40–2.02 TWh | **CONFIRMED**, 1.651 |
| P3 | CC −0.66…−1.85; CT +0.32…+1.29; PRB +0.22…+0.88; ST +0.10…+0.39; BIT 0…+0.15 | **CONFIRMED**: −1.288 / +0.628 / +0.405 / +0.220 / +0.031 |
| P4 | CC_REGULAR +2.58…+3.77 TWh, +1.96…+2.44 pp, PASS | **CONFIRMED**, +3.14 / +2.2 |
| P5 | CT_PEAKER ≤ +3.02 / ≤ 1.2 pp, PASS | **CONFIRMED**, +2.36 / +1.0 |
| P6 | C4 coal NRMSE 0.228–0.238, r 0.83–0.85 | **CONFIRMED**, 0.235 / 0.843 (gas 0.111 / 0.952) |
| P7 | C8 2024 ST_GAS 0.150–0.168 | **CONFIRMED**, 0.161 |
| P8 | CC per-plant Σ\|m − 923\| 7.6–10.2 | **CONFIRMED**, 9.281 |
| P9 | every status unchanged, grade 5/5/0 | **CONFIRMED** |
| P10 | 2024 unserved 0; 2025 267.4 MWh | **CONFIRMED** |
| P11 | DOF `n_residual` 1 | **CONFIRMED**: 13 entries / 1 residual (`wefor_multiplier`, inherited) |
| P12 | surface 185 rows, only `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` moved | **CONFIRMED** (asserted per leg) |

The greedy re-stack was accurate this time: it predicted a −1.853 TWh cut at Lindsay Hill, and the LP
cut 1.834 TWh.

## 3. RULE 19 / GOVERNANCE

- **Rule 19 [R-ONE-MECH], at unit grain.** Fleets were rebuilt with `fleet_only`, each side in its own
  process. 2023 and 2025 are 0 keys moved on every grain. In 2024 only `availability` moves, on the four
  `p55271` tranches. `min_gen` is 0 on those tranches.
- **Benchmark:** the shared inputs `eia923-ed8b34e900d9`, `eia930-af1df2c6e425` and
  `campd-eecf72fbab56` are identical to the keeper's. The bench parts did not move.
- **Attestation:** `calibration-attestation/v1`, `exceptions []`, all four governance assertions true.
  `gen_soco61_attestation.py` runs on top of `gen_soco60b_attestation.py`, so every inherited claim is
  re-verified. It also checks by execution:
  - the extract path and sha256 the run read;
  - that the extract adds exactly one row over `-perunit-`;
  - the CAMPD evidence, recomputed from raw.
- **Price:** no `authorized_price_tuning` key, and every offer band is 1.0. The scorer's literal
  `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` certifies no price and is not SOCO's determination.
- **Tests:** 28 targeted tests pass. The `tests/unit/{data,config}` failure set is identical to main's
  (25).

**Census of other dark unit-years:** Walton Discover 2B, Baconton CT1 and four Walton Bainbridge oil CTs.
All are CT peakers, which the outage overlay excludes by convention, so none is added.

## 4. ROUTED

1. **2023 is now the thin year.** ST_GAS −2.3 pp and CT_PEAKER +2.2 pp both have 0.7–0.8 pp margins.
   This lane does not touch 2023.
2. **CC economic over-dispatch** remains 9.3 TWh, led by E B Harris (+2.0) and H A Franklin (+1.5).
   These plants run below capability at full `mc` merit, and no admissible input reaches them.
3. **2024 CT_PEAKER** worsened by 0.63 TWh, the replacement energy for CT3.
4. **Other ISOs:** each needs its own `-perunitdark-` census (rule 28(d)); every other shard's cell is
   seeded `U`.

## 5. WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: zero.** Three shards ran 8–9 min each and were archived after fetch, checkout and
  verification.
- **On `main` once this PR merges:**
  - the keeper bundle `results/calibration/soco61_dark_unit_span` (17 files, rule-15 shape);
  - its sidecar and run payload;
  - the `-perunitdark-` extract.

  **A re-promotion from that state costs zero re-solves.**
- **Per-plant legs** are gitignored with 0 files tracked, on this container only. Their SHAs are
  provenance: 2023 `4cc73989`, 2024 `b13d473e`, 2025 `418c7be6`. Cost any later need for them as a
  re-solve of ~9 min per year.
- **Leftover shard branches the owner must remove** (a session cannot delete refs):
  `claude/soco61-arm-{2023,2024,2025}`, and from the earlier collision `claude/soco60-arm-*` and
  `claude/soco60-armB-*`.

## 6. THE PROMOTION — EXECUTED

The owner's standing ruling was restated during this lane: *"Is this a recommended keeper candidate? If so
plz promote. If structural integrity improves but gates regress that may still be a keeper.."* The run
was recommended (§1) and promoted. Rule 35 was executed in order:

1. **(b)** Enumerated the year union across SOCO's sidecars: {2023, 2024, 2025}.
2. **(c)** Confirmed the incoming run covers that union.
3. **(e)** Wrote `keepers/SOCO.json` and rebuilt `build_status --iso SOCO`. `audit_keepers` E1 passes.
4. **(a)** Ran `prune_iso_runs --iso SOCO --keep 2026-09-20-soco53g-prb-own-iso --force-uncite`, which
   removed `2026-09-23-soco60-boundary-span`.

**Standing E13, and a question to the owner:** `2026-09-20-soco53g-prb-own-iso` is still unruled. The
standing recommendation is to **decline** it, so the next promoting session can prune it.

## Log entry

```
## soco-61 — 2026-09-24

A 313 MW CC TURBINE THAT DID NOT RUN IN 2024 WAS MODELLED FULLY AVAILABLE.
Tenaska Lindsay Hill (55271) CT3 filed all 8,784 CAMPD hours of 2024 dark (0
operating hours; 642 / 308 GWh in 2023 / 2025). The per-unit outage deriver
skips a never-producing unit and the eia923_netzero hook is plant-grain, so the
keeper carried it fully available and the plant ran +1.73 TWh over EIA-923.

PHASE 0 MEASURED THE THREE ROUTED LEADS FIRST. The big over-dispatched CC
plants (E B Harris, H A Franklin, Central Alabama) run BELOW their measured
capability -- economic, not availability. Coal runs at 0.35-0.70 of its model
availability -- merit order, no availability lever. ST/CC fuel separation still
has no forward-regenerable input. Lindsay Hill was the only over-dispatched CC
plant whose model capability exceeded what it delivered.

THE REPAIR: new field campd_dark_unit_year_windows + deriver flag
--dark-unit-years (categorical, zero free parameters): one full-year window
when a unit's own id is dark every hour of the year, produced in an adjacent
year, and a peer ran. The -perunitdark- extract is the -perunit- extract
re-derived BYTE-IDENTICALLY plus one row.

RESULT (run 2026-09-24-soco61-dark-unit, PROMOTED, three year-isolated shards
composed at zero LP): 2023/2025 identical to the keeper; 2024 Lindsay Hill
3.485 -> 1.651 TWh (actual 1.752). No status moved: C1 14/14 / free 10/10,
C2/C4/C6/C8 PASS, C3 unscorable, grade 5/5/0, DOF 13/1. 2024 CC_REGULAR +4.43 ->
+3.14 TWh, share +2.7 -> +2.2 pp (margin 0.3 -> 0.8 pp); CC per-plant
sum|model-923| 11.07 -> 9.28 TWh; C4 2024 coal NRMSE 0.240 -> 0.235. WORSE:
2024 CT_PEAKER +1.73 -> +2.36 TWh. 12/12 predictions in band.

ROUTED: 2023 ST_GAS / CT_PEAKER are now the thinnest rows (0.7-0.8 pp); the CC
economic over-dispatch (E B Harris +2.0, H A Franklin +1.5) has no admissible
input. Outgoing keeper 2026-09-23-soco60-boundary-span pruned (rule 35). E13 for
2026-09-20-soco53g-prb-own-iso still unruled (recommendation: decline).
Records: docs/handoffs/PRECOMMIT-soco-61-2026-09-24.md,
docs/handoffs/FINDING-soco-61-2026-09-24.md, scripts/gen_soco61_attestation.py,
scripts/probes/soco61_compose_span.py, scripts/probes/_soco61_phase0.py.
```
