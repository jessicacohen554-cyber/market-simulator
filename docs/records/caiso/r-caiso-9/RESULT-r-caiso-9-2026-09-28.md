# RESULT — R-CAISO-9: SD import cap floored at the static 1,436 MW; Object 2 censuses (2026-09-28)

**PROMOTED `2026-09-28-caiso-r9-sd-floor`** (bundle `rcaiso9_A_span`, 2022–2025), CALIBRATED, under the standing
direction "promote if a good candidate".
- Fold: `2026-09-28-caiso-r9-fold` (bundle `rcaiso9_A_tp_2019_2021`), stamped to the keeper. NOT-YET, reported only
  (rule 30(c)).
- Pruned per rule 35(a): `2026-09-27-caiso-r8-partial-year` and `2026-09-27-caiso-r8-fold`. Year set unchanged
  (2019–2025). `audit_keepers.py --iso CAISO` PASS after the prune.
- Complete marker re-keyed (`rekeyed_2026_09_28_rcaiso9`); matrix shard and §5.2 header re-stamped.

## Object 1 — `caiso_import_cap_floor_static`

- The per-year `SP15_rest → SDGE` cap is now `max(LCT cap, 1,436 MW)`. The floor is the link's own baked static TTC,
  so there are zero new numbers.
- It is a declared rule-14 reconciled estimate (owner ruling "Floor at static 1,436").
- **LA Basin census:** the per-year LA cap falls below the static 12,008 MW in 2019 (11,150) and 2020 (11,897).
  - Taken to the owner as a decision card. Ruling: **"SD only"**.
  - No measured LA import census exists, and LA binds only 17 h in 2019 and 0 h in 2020.
- **G-DRIFT** (zero LP, `results/calibration/_rcaiso9/gdrift_input_identity.json`): matched pre-registration exactly.
  - The 2019–21 SDGE TTC (386 / 718 / 635 → 1,436 MW) is the only LP input moved in any year.
  - Pin → HEAD moves nothing.
  - Addendum at the rebase base `baf382bd`: every new hunk is INERT for CAISO.

### Results against the pre-registered directions (PRECOMMIT §4)

| quantity | 2019 | 2020 | 2021 | pre-registered | outcome |
|---|--:|--:|--:|---|---|
| SDGE unserved, MWh | 419,683 → **222** | 12,125 → **0** | 2,259 → **0** | down | ✓ |
| SDGE mean price, $/MWh | 388.8 → **43.2** | 53.6 → **35.1** | 59.6 → **52.3** | down | ✓ |
| hours SDGE − SP15_rest > $0.01 | 7,155 → **1,456** | 2,584 → **311** | 3,835 → **235** | down | ✓ |
| C3a 2021 | | | +13.5 → **+12.5 %** | down | ✓ (still FAIL) |
| C3b 2021 | | | PASS → **PASS** | stays PASS | ✓ |
| C3c 2021, h > $200 | | | 108 → **90** | down | ✓ |
| C1 CC_REGULAR, TWh | +20.4 → **+22.9** | +24.8 → **+25.1** | +10.1 → **+10.4** | sign not registered; \|Δ\| ≤ 1 expected | **2019 exceeds expectation (+2.5 TWh)** |
| C4 gas NRMSE | 0.575 → 0.570 | 0.530 → 0.528 | 0.387 → 0.383 | not registered | small improvement |
| 2022–2025 | | | | no movement | ✓ hourly system and class sidecars **byte-identical** |

- **2019 C1 expectation miss.** SDGE load that was previously unserved or served by in-pocket peakers at ~$389 is now
  imported from SP15_rest, where CC_REGULAR is marginal. So the fix adds CC energy to a year already +20 TWh over.
  This is reported at full magnitude. It is not a reason to reject the mechanism (rule 1): the 2019 over-dispatch is
  the standing 2019–20 CC-excess object (no hub print; STOP stands).

## Object 2 — the next 2022–25 lever (zero LP; `scripts/probes/_rcaiso9_object2_census.py` → `results/calibration/_rcaiso9/object2_census.json`)

**(a) C4 2025 (NRMSE 0.2987 vs ≤ 0.30).**
- The miss is CC_REGULAR's diurnal swing. The model runs −1.0 to −1.2 GW low at h8–16 and +0.5 to +0.7 GW high at
  h18–23. Removing the mean hour-of-day bias alone would bring NRMSE 0.299 → 0.267.
- Midday CC_REGULAR per-plant split (mean MW, h9–16):

  | component | MW |
  |---|--:|
  | units CEMS shows on, model off | −947 |
  | both on, model loaded lower | −668 |
  | model over | +793 |

- Decommitment is the larger part. That is the RA-bridge coverage question (caiso-284 "belly gas"). Raising
  `caiso_ra_min_load_frac` is DO-NOT-RETEST.
- **No admissible lever proposed.** The zero-LP split is now on record for a successor.

**(b) 2021 DSW evening gap (−2.9 GW at h17–22).**
- It is mostly **not** the unprinted Jan–Apr hours:

  | hours | DSW gap, TWh |
  |---|--:|
  | printed evening (1,494 h) | −3.82 |
  | unprinted evening (696 h) | −2.44 |
  | unprinted, all hours (Jan–Apr) | −8.01 |

- In the printed evening hours the model's SP15_rest price is **$68.9**, against measured DAM TH_SP15 **$77.8** and
  PALOVRDE **$77.0**. The DSW hub input is $79.1, so priced imports sit out of merit.
- The 2021 model price shape is too flat: evenings $8.9 low, midday $3.0 high.
- This is a price-formation object in 2021, not a hub-coverage object. Any fix must be one config across all scored
  years (rule 1). Nothing was armed.

## Retrievability (rule 34(e))

- On `main`: `rcaiso9_A_span` and `rcaiso9_A_tp_2019_2021` (slim set, hourly sidecars, attestation, diagnostics).
- The per-year legs are gitignored, local-only. Provenance SHAs (not a recovery route; rule 33(d)):

| year | shard commit |
|---|---|
| 2019 | `4bd557130eca922b753dcef8a92899b756760bb9` |
| 2020 | `2f7db31370726a68c20095b1acef8c8eb430e966` |
| 2021 | `e8b53b58aeb8fa2d37c9bb2ccfc675a248ce6eab` |
| 2022 | `e0d95f03bdd001da9b0f821baaafc5600ea105bc` |
| 2023 | `02256dfa434072670df16c71c16b8285455cf3bd` |
| 2024 | `01caa703ef0f160b3bd7c7acb48b1ec07f03cbfd` |
| 2025 | `87cca3f5c36a98e89ea76939382b56c3e8f7aca2` |

- Any leg not on `main` costs a ~20 min re-solve.

## Leftover branches for the owner to delete

- `claude/r-caiso-8`, `claude/r-caiso-8-A-2019` … `-A-2025`
- `claude/r-caiso-9-A-2019` … `-A-2025`
