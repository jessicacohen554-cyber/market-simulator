# RESULT — R-CAISO-2: CC gross-net identity repair (2026-09-25)

PRECOMMIT: `PRECOMMIT-r-caiso-2-2026-09-25.md` (pin `640c9fe3`).

## Headline

**Run `2026-09-25-caiso-r2-cc-gross` (bundle `rcaiso2_ccid_span`, 2022–2025) — DETERMINATION CALIBRATED.**
It is PROMOTED on the owner instruction of 2026-09-25 ("Is this a recommended keeper candidate? If so plz
promote"). The outgoing keeper `2026-09-24-caiso-r-inputs-vintage` was NOT-YET on one row.

| | outgoing | R-CAISO-2 |
|---|---|---|
| C1 2023 CC_REGULAR (band ±5.27) | −5.36 FAIL | **−5.14 PASS** |
| C1 2022 / 2024 CC_REGULAR | +0.25 / −1.24 | +0.64 / −0.89 |
| C1 CT_PEAKER 2022 / 2023 / 2024 | −1.44 / −1.74 / −2.22 | −1.48 / −1.79 / −2.30 |
| C3a mean LMP vs RT 2022 / 23 / 24 / 25 | +7.3 / +4.4 / +7.6 / +9.4 % | +7.1 / +4.2 / +7.2 / +9.0 % |
| C3b NRMSE 2022 / 23 / 24 / 25 | 0.092 / 0.084 / 0.131 / 0.118 | 0.090 / 0.083 / 0.129 / 0.115 |
| C4 gas r / NRMSE 2023 | 0.884 / 0.297 | 0.883 / 0.298 |
| C3c | 2024 ledgered | 2024 ledgered (0 h vs 35 h) |
| C2, C6, C8 | PASS | PASS |

C1 is 18/18 (free 12/12). The DOF ledger is 9/6, unchanged. There is no `authorized_price_tuning` block, and
the offer curves are unchanged.

Model TWh, arm − outgoing (P1):

| year | CC_REGULAR | import | CT_PEAKER | Pastoria 55656 |
|---|---:|---:|---:|---|
| 2022 | +0.390 | −0.329 | −0.049 | 1.30 → 1.84 (actual 3.29) |
| 2023 | +0.218 | −0.168 | −0.050 | 1.41 → 1.81 (actual 4.34) |
| 2024 | +0.349 | −0.261 | −0.075 | 1.03 → 1.64 (actual 4.01) |

The direction is the one stated ex ante (§5): CC_REGULAR up, imports and CT down in every year. The size
was not a criterion.

## The mechanism

This is an input correction on a path the keeper already arms (`measured_cc_heat_rates`):

- **Physics:** CAMPD gross output ÷ EIA-923 net output must be at least 1.0 for a fully metered combined
  cycle, because gross equals net plus station service.
- **The defect:** the deriver's boundary guard admitted ratios down to 0.90. Its "empty gap" claim was
  measured on SOCO, which has no row in that range.
- **What CAISO carried:** 12 rows in [0.90, 1.0). The main one is Pastoria 2020–25. From 2020 the
  Phase-1 steam turbine drops out of CT001/CT002's CEMS gross load: the per-unit rate goes 7.1 → 8.8
  while CT004 holds 7.45 and output is unchanged.
- **The fix:** those rows now carry the flag `gross_below_net` and fall back to the pooled rate, then to
  eGRID. Zero new ScenarioConfig fields and zero free parameters.
- **Other ISOs:** only CAISO's artifact was re-derived (rule 25). Other ISOs' `ok` rows below 1.0
  (ERCOT 14, MISO 10, NEISO 6, NWPP 5, NYISO 6, PJM 23, SPP 1, SOCO 0) are routed to their own lanes.

## Still open (rule 14: not absorbed)

1. **Pastoria remains about −2.4 TWh/yr** at its eGRID 7.69 rate. It is the largest standing CC miss. The
   heat-rate repair recovered roughly 0.4–0.6 TWh/yr of it; the rest is a separate object (candidates:
   tolling/contract dispatch, gas-delivery point, SP15_rest topology).
2. **Dec 2022–Mar 2023 over-import.** Imports run +1.4–1.8 TWh/month over actual, with a matching CC
   deficit, in the western gas-price-spike window.
3. **2019–2021 (Task A) stopped at phase 0.** The supply-consistent demand derive failed its guard.
   Owner decision (a) or (b) is owed, per INTAKE-i-caiso §1. 2019–20 also have no intertie hub series
   and no LMP/tail references.

## Retrievability (rule 34(e))

- **Composite:** `rcaiso2_ccid_span` (slim set + hourly + attestation + metrics + diagnostics), its
  sidecar and its payload are committed on `main` with this lane.
- **Per-year legs:** gitignored in the parent (rule 32(d)). They were pulled locally and verified.
- **Shard commits (provenance only, rule 33(d)):** 2022 `d287541d`, 2023 `d417e53a`, 2024 `0b159ca1`,
  2025 `2976d224`.
- **Shards:** all archived.
- **Cost if a leg is ever needed again:** about 22 min of LP each.

## Promotion housekeeping

- **Done:** keeper shard, `calibration-complete.json` re-key, status part, matrix shard stamp and §5.2
  header.
- **NOT done — `prune_iso_runs.py --iso CAISO --force-uncite`:** the session's auto-mode permission
  classifier refused this command. The outgoing `2026-09-24-caiso-r-inputs-vintage` sidecar, payload and
  bundle `rcaiso_inputs_span` are therefore still on `main`, and `audit_keepers.py` E13 fails until the
  owner runs that command.
