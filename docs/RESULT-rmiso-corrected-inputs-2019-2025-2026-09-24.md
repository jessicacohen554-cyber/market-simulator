# RESULT — R-MISO: MISO 2019–2025 re-solved on corrected backcast inputs. Registered, NOT promoted; train tier leaves CALIBRATED → escalated.

```
LANE    : R-MISO (AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.3)
PREREG  : docs/PRECOMMIT-rmiso-corrected-inputs-2019-2025-2026-09-24.md (A pinned 6a8d1794; B §9 pinned bef12b51)
KEEPER  : 2026-09-24-miso-268-coal-yard (2020-2025) — unchanged
RUN A   : 2026-09-24-rmiso-corrected-inputs   (results/calibration/rmiso_span)   keeper + F1 defaults + short-gas + unit-partial
RUN B   : 2026-09-24-rmiso-arm-b-mid          (results/calibration/rmiso_b_span) A + mid_vintage_exit_carry
VERDICT : both NOT-YET full span 8/4/1/3; train 2023-2025 NOT-YET 8/5/1/2 (keeper CALIBRATED 8/7/1/0)
```

Offer-curve multipliers byte-identical to the keeper in every year of both runs (sorted-JSON sha256
`c5ab11d9b26d2abf`); DOF added 0. Scores below are on the final regenerated MISO bench parts; the keeper
re-scores unchanged on them (train CALIBRATED, full 8/5/1/2), and run A's train-tier fails persist on the
pre-lane committed parts, so the regression is model-side.

## 1. Gate table, per year

| crit | year | keeper miso-268 | run A | arm B |
|---|---|---|---|---|
| C1 | 2019 | — | FAIL COAL_BIT -13.17 TWh | PASS |
| C1 | 2020 | PASS | PASS | PASS |
| C1 | 2021 | PASS | FAIL CC_REGULAR -9.33 TWh | FAIL CC_REGULAR -10.37 TWh |
| C1 | 2022 | PASS | PASS | FAIL CC_REGULAR -9.75 TWh |
| C1 | 2023 | PASS | FAIL CC_REGULAR -10.38 TWh | FAIL CC_REGULAR -10.38 TWh |
| C1 | 2024 | PASS | PASS | PASS |
| C1 | 2025 | SKIPPED | SKIPPED | SKIPPED |
| C2 | 2019 | — | PASS | PASS |
| C2 | 2020 | PASS | PASS | PASS |
| C2 | 2021 | PASS | PASS | PASS |
| C2 | 2022 | PASS | PASS | PASS |
| C2 | 2023 | PASS | PASS | PASS |
| C2 | 2024 | PASS | PASS | PASS |
| C2 | 2025 | SKIPPED | SKIPPED | SKIPPED |
| C3a | 2019 | — | FAIL +15.6% | FAIL +12.5% |
| C3a | 2020 | FAIL +13.4% | FAIL +14.2% | FAIL +13.0% |
| C3a | 2021 | PASS +4.9% | PASS +7.6% | PASS +6.5% |
| C3a | 2022 | PASS -8.4% | PASS -5.3% | PASS -7.7% |
| C3a | 2023 | PASS +4.9% | FAIL +10.0% | FAIL +10.0% |
| C3a | 2024 | PASS -0.1% | PASS +2.2% | PASS +2.2% |
| C3a | 2025 | PASS -0.6% | PASS +0.7% | PASS +0.7% |
| C3b | 2019 | — | PASS NRMSE 0.178 | PASS NRMSE 0.148 |
| C3b | 2020 | PASS NRMSE 0.170 | PASS NRMSE 0.176 | PASS NRMSE 0.166 |
| C3b | 2021 | FAIL NRMSE 0.309 | FAIL NRMSE 0.325 | FAIL NRMSE 0.316 |
| C3b | 2022 | PASS NRMSE 0.134 | PASS NRMSE 0.112 | PASS NRMSE 0.127 |
| C3b | 2023 | PASS NRMSE 0.090 | PASS NRMSE 0.129 | PASS NRMSE 0.129 |
| C3b | 2024 | PASS NRMSE 0.104 | PASS NRMSE 0.106 | PASS NRMSE 0.106 |
| C3b | 2025 | PASS NRMSE 0.109 | PASS NRMSE 0.109 | PASS NRMSE 0.109 |
| C3c | 2019 | — | SKIPPED | SKIPPED |
| C3c | 2020 | SKIPPED | SKIPPED | SKIPPED |
| C3c | 2021 | SKIPPED | SKIPPED | SKIPPED |
| C3c | 2022 | CAVEAT | CAVEAT | CAVEAT |
| C3c | 2023 | CAVEAT | CAVEAT | CAVEAT |
| C3c | 2024 | CAVEAT | CAVEAT | CAVEAT |
| C3c | 2025 | CAVEAT | CAVEAT | CAVEAT |
| C4 | 2019 | — | PASS | PASS |
| C4 | 2020 | PASS | PASS | PASS |
| C4 | 2021 | PASS | PASS | PASS |
| C4 | 2022 | PASS | PASS | PASS |
| C4 | 2023 | PASS | PASS | PASS |
| C4 | 2024 | PASS | PASS | PASS |
| C4 | 2025 | PASS | PASS | PASS |
| C8 | 2019 | — | PASS | PASS |
| C8 | 2020 | PASS | PASS | PASS |
| C8 | 2021 | PASS | PASS | PASS |
| C8 | 2022 | PASS | PASS | PASS |
| C8 | 2023 | PASS | PASS | PASS |
| C8 | 2024 | PASS | PASS | PASS |
| C8 | 2025 | PASS | PASS | PASS |

C6 governance PASS in all three. Full span: keeper NOT-YET 8/5/1/2 · A NOT-YET 8/4/1/3 · B NOT-YET 8/4/1/3.
**Train tier 2023–2025: keeper CALIBRATED 8/7/1/0 → A and B NOT-YET 8/5/1/2** (C1 2023 CC_REGULAR
−10.38 TWh vs ±8; C3a 2023 +10.0 % vs ±10 %).

## 2. Class TWh, arm B minus keeper (2019: level, no keeper year)

| year | COAL_PRB | COAL_BIT | COAL_LIGNITE | CC_REGULAR | CC_CHP | CT_PEAKER | ST_GAS | nuclear | import | LW price Δ $/MWh |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 (level) | 155.5 | 77.7 | 8.4 | 104.1 | 17.0 | 10.6 | 15.2 | 97.6 | 53.5 | 29.72 |
| 2020 | +3.04 | +0.44 | -0.50 | -6.28 | -3.70 | -0.08 | -1.30 | +1.05 | -0.27 | -0.08 |
| 2021 | +1.17 | -3.64 | -0.56 | -4.93 | -2.99 | +0.57 | -1.26 | +1.02 | +0.34 | +0.65 |
| 2022 | -1.25 | -1.86 | -0.01 | -4.66 | -3.17 | +0.37 | -0.69 | +3.33 | +0.24 | +0.51 |
| 2023 | -4.49 | -1.58 | +0.09 | -2.64 | +0.36 | +2.90 | +0.76 | +0.40 | +2.64 | +1.67 |
| 2024 | -0.91 | +1.64 | +0.02 | -6.61 | +0.35 | +1.58 | +1.89 | -0.02 | +1.43 | +0.75 |
| 2025 | +0.61 | +0.97 | -0.01 | -1.31 | -0.23 | +0.90 | -1.51 | +0.00 | +0.14 | +0.59 |

## 3. Structural gates (PRECOMMIT §5)

* **S-1 recipe:** PASS. Every leg is keeper + exactly the declared flips (six in A, seven in B). Each was
  checked in its shard and re-checked here: vintage = solve year, pinned input sha256s, and hydro classifier.
* **S-2 slack:** **FAIL.** 2023 has new slack (3.0 GWh, hours 5654–5656, 24 Aug), and 2024 grows
  26.9 → 42.7 GWh (hours 5700–5706, 26 Aug). Every slack hour sits inside a declared MISO Max Gen event, at
  that event's emergency-tier price floor ($1,000 in 2023, $500 in 2024). So the corrected
  outage envelope pushes the LP onto its emergency-priced supply during the declared emergencies, but
  this is still new unserved energy. Identical in A and B.
* **S-3 G-DRIFT:** PASS; no LIVE hunk beyond PRECOMMIT §3.
* **Determinism:** B's 2023–2025 legs reproduce A's to 0.0000 TWh per class, the same price and the same slack.

## 4. What moved, and why (zero-LP localization; routed, not absorbed)

1. **2019–2022 mid-vintage-year retirees (fixed by B).** Under the vintage default, a plant that retires
   during year Y is absent from both of vintage_Y's sheets. Without the carry, the model is missing
   3.1 / 1.0 / 1.5 / 2.8 GW in 2019–2022 (Coffeen, Havana, Duck Creek, Duane Arnold, Dolet Hills,
   Palisades, E D Edwards, Meramec). B turns 2019 C1 COAL_BIT from −13.17 TWh FAIL into a PASS and restores
   Duane Arnold (+4.1 TWh nuclear, 2020). **This carry must accompany the F1 vintage default in every ISO;
   routed to F1 / all R-lanes.**
2. **CC_REGULAR under-dispatch in 2021–2023 (open).** CC_REGULAR is −4.9 / −4.7 / −2.6 TWh vs the keeper, which
   takes C1 from ≈ −7.3 to −9.8 / −10.4 TWh against the ±8 band. In 2023, vintage_2023 carries 1.36 GW less LP
   CC_REGULAR than the canonical snapshot (raw gas_cc −488 MW: Magnolia Power −679, Edwardsport −481,
   Cottonwood +565), while the CC heat rate falls 9.07 → 8.88. The cause is fleet membership, not heat rates.
   The short-gas windows (1.0–1.4 % of gas MW-h) push the same way. Not separated by a solve.
3. **Mean price (C3a)** rises +0.5 to +1.7 $/MWh in most years. It fails 2023 (+10.0 %) and does not close
   2020 (+13.0 %); 2019 is +12.5 %. **C3b 2021** stays FAIL (0.316).
4. **Unit partial-derate family: armed and inert** (0 windows every year). In 2023 the deriver detects 55
   plateaus on 33 baseload coal units. The shared `outage_detect.filter_revealed_outages` then drops every one,
   because a derated unit RUNS in high-load hours. This is a cross-ISO deriver defect (the same filter serves
   SPP/NWPP/SOCO) and is routed out of lane.
5. **Maxgen 2021:** 100 unit windows, 4.69 GW, MISO-South over Uri (the deriver now reads the chunked hub
   record); 2023–2025 byte-identical. C3b 2021 does not improve.
6. **Standard-unitroute / short-coal extracts do not reproduce at HEAD.** This is the same drift F2 found:
   2023/24/25 lose −22/−19/−30 windows (New Ulm, Waterford); short-coal 2019–22 gains +11/+8/+3/+8. F1 did not
   cause it, and no source data changed, so both were left as committed (rule 23). Open.

## 5. Census deltas (phase 0)

Class-table heat rate: 95–100 % of thermal MW in 2019–2022 pre-F1 → **0.3–0.7 %** here (mostly oil; residual =
F1's 36-plant list). 2019 retirees at class-table rates: 9,766 → 896 MW. 2019 inputs landed: hub LMPs, BA
interchange, the seam ladder, and 2017 coal receipts. Before these landed, three seam mechanisms were silently off in 2019.

## 6. Recommendation and promotion

**Not recommended for automatic promotion.** Under PRECOMMIT §5 the train tier left CALIBRATED and S-2
failed, so this is **escalated to the owner**, per the pre-registered rule. On structure, **arm B is the more
faithful MISO model**: year-matched EIA-860 with its mid-year retirees, plant-specific measured heat rates,
2019 coverage and granular outages. Its gate regressions are two near-band 2023 cells plus
2021/2022 CC_REGULAR. The owner's standard ("if structural integrity improves but gates regress that may
still be a keeper") makes B the candidate to rule on. A is superseded by B.

## 7. Where the bytes are

* **In this lane's branch (lands on `main` at merge):** both runs' registered file sets (slim bundle, `hourly/` sidecars,
  attestation, diagnostics), their sidecars and payloads, and the MISO bench parts 2019–2025. Promoting B from
  here costs **zero re-solves**. The run page needs only the committed set.
* **Per-year full legs** (with `dispatch/<Y>_P1.parquet`): on local disk (gitignored, rule 31) and on shard
  branches `claude/rmiso-<Y>[-b]` / `claude/rmiso-b-<Y>`. Leg SHAs are in the attestations, as provenance only
  (rule 33(d)): those branches are cut when this lane's PR merges. A later **unit-level** re-analysis
  of a leg would cost a re-solve (~20–60 min per year).
* **Shards:** all 17 archived after their bytes were verified here (7 A, 3 A-relaunch, 7 B). The three stranded
  A legs are recorded in PRECOMMIT §8.
