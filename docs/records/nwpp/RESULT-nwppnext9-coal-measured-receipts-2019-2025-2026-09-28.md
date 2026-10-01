# RESULT — NWPP-NEXT-9: same-year measured receipts on the monthly coal pile — REJECTED (owner, 2026-09-29)

**Arm:** keeper #15 (`2026-09-28-nwppnext8-coal-monthly-pile`) plus `coal_monthly_pile_measured_receipts=true`.
Precommit: `docs/records/nwpp/PRECOMMIT-nwppnext9-coal-measured-receipts-2019-2025-2026-09-28.md`.
**Solve:** seven year-isolated shards at pin `677273fb`. Every hard stop passed.
**Owner ruling (decision card):** "Reject, keep #15". Keeper #15 stands.

## 1. Headline

| | Keeper #15 | Receipts overlay |
|---|---|---|
| Determination | NOT-YET on {dispatch_corr}, 1 record | NOT-YET on {dispatch_corr}, **3 records** |
| C1 / C2 / C6 / C8 | PASS | PASS |

**C4 (hourly r / NRMSE vs EIA-930; floor r ≥ 0.70, NRMSE ≤ 0.30).**

| Year | Coal, keeper #15 | Coal, arm | Gas, keeper #15 | Gas, arm |
|---|---|---|---|---|
| 2019 | 0.733 / 0.223 | 0.728 / 0.255 | 0.750 / 0.224 | 0.708 / 0.245 |
| 2020 | 0.762 / 0.157 | 0.770 / 0.149 | 0.831 / 0.180 | 0.828 / 0.188 |
| 2021 | 0.792 / 0.182 | 0.768 / 0.182 | 0.854 / 0.151 | 0.827 / 0.154 |
| 2022 | 0.741 / 0.219 | **0.695 / 0.229 FAIL** | 0.880 / 0.177 | 0.858 / 0.183 |
| 2023 | 0.695 / 0.283 FAIL | **0.648 / 0.252 FAIL** | 0.844 / 0.163 | 0.824 / 0.153 |
| 2024 | 0.739 / 0.211 | **0.664 / 0.256 FAIL** | 0.891 / 0.125 | 0.872 / 0.148 |
| 2025 | 0.721 / 0.242 | 0.721 / 0.242 (identical) | 0.854 / 0.196 | 0.854 / 0.196 |

**C1 annual volume error (model − actual, TWh; every row still PASS).**

| Record | Keeper #15 | Arm |
|---|---|---|
| COAL_BIT 2023 | +4.73 | **+0.72** |
| COAL_PRB 2020 | +2.14 | **+0.48** |
| COAL_PRB 2024 | +3.51 | **+2.02** |
| COAL_PRB 2023 | +4.00 | +3.12 |
| COAL_BIT 2021 | +4.59 | +3.57 |
| COAL_BIT 2020 | +1.04 | +1.78 (worse) |
| CC_REGULAR 2023 | −2.25 | +1.86 |
| CC_REGULAR 2024 | +4.61 | +5.55 (worse, band 8) |

## 2. What happened (the finding this lane leaves)

- **Volume is more accurate.** Realised supply cut 2023 coal by 4.9 TWh (BIT −4.00, PRB −0.88), and gas rose. The
  annual coal error at PacifiCorp's yards fell sharply.
- **Timing got worse**, and the reason is structural, not noise.
  - 2023 January coal is unchanged: 5.48 TWh against EIA-930's 4.40.
  - Bridger's January ceiling (Dec stock plus Jan receipts, 1.85 TWh) never binds.
  - The cut came out of Jul–Oct instead: model 3.99 / 4.26 / 3.12 / 2.81 against actual 4.49 / 4.65 / 3.74 / 4.02 TWh.
  - A perfect-foresight LP facing less coal spends it in the dear-gas months.
  - The real operator did the opposite. With the pile at a record low (Jan 2023), it refused to draw it further and
    rebuilt stock through spring.
- **Rule-14 reading.** The accurate input exposed a missing behaviour; it did not create one. What is missing is
  **operator inventory management**, a stock the utility will not draw below. Volume is no longer the issue.
- **The obvious form is refuted.** "The pile never drops below the least it has held" was tested at phase 0 and fails
  on data: Bridger drew 0.33 Mt below its prior minimum in 2022 (PRECOMMIT §0).
- **2025 is byte-identical** to keeper #15 at the class level, as predicted (no 2025 receipts file). This is an
  empirical confirmation of the G-DRIFT audit (§4a).

## 3. Disposition

- **Code.** The flag stays, default off and backcast-only, with 13 tests. It remains available to combine with a future
  inventory-behaviour mechanism.
- **Matrix.** The NWPP cell is `R` (rejected, owner 2026-09-29).
- **Registration.** Registered locally as `2026-09-28-nwppnext9-coal-measured-receipts`, then pruned on the owner's
  ruling via `prune_iso_runs.py` (rule 31 trigger (i); MISO-276 precedent) so `audit_keepers` E13 stays green.
  - This doc carries every number above. The official verdict JSON matched the zero-LP recompute record for record.

## 4. Retrievability (rule 34(e))

- **Leg SHAs (provenance only; shard branches are transport and are cut on merge):**
  2019 `dcacf67e` · 2020 `1dd76666` · 2021 `f0deef4c` · 2022 `8e31113e` · 2023 `57871421` · 2024 `0ab8c08e` ·
  2025 `2caa5233`.
- **Nothing lands on `main`**, because the run was declined. A re-promotion would cost a full re-solve: 7 shards, ~1 h
  each for 2020–2025 and ~2.5 h for 2019.

## 5. Routed (for NWPP-NEXT-10)

1. **C4 coal 2023 (r 0.695 on keeper #15) is still the only failing record.** The NEXT-9 census names its driver as a
   PacifiCorp coal-supply shortfall plus conservation of a record-low pile. Receipts are 2022 → 2023 Bridger
   105.1 → 86.6, Hunter 58.8 → 39.2 and Huntington 56.0 → 26.5 TBtu.
   - The missing structure is inventory-management behaviour.
   - Any mechanism needs a measured, forward-regenerable identification (rules 5 / 13 / 21), for example a published
     utility fuel-inventory target (PacifiCorp IRP or rate-case days-of-burn policy).
   - Do not re-test S_min (refuted by 2022) or measured receipts alone (this lane).
2. Colstrip 2020 availability, SNV residual shed, internal-link over-flow, the Bridger coal tranche row, and solve time
   are carried unchanged from HANDOFF-nwppnext9.
3. **Stale provenance hash:** re-derived in this lane (only `source_sha256` moved; TWh identical; not on the
   solve surface).
