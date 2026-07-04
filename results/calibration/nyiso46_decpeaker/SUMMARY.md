# NYISO 46 — NYSDEC 227-3 peaker-rule availability overlay (registered, NOT promoted; best NYISO probe)

nyiso-45 (measured-run fast-start amortization + generator-level oil screen)
plus the **NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay**
(`--nysdec-peaker-rule`): the curated unit-level compliance schedule
(`data/raw/reference/nysdec-227-3-peaker-compliance.csv` — extracted from the
on-disk NYISO Gold Book Tables IV-3..IV-6, 2023/2024/2025 vintages, per-unit
citations in every row) zeroes each restricted unit's availability inside its
effective ozone-season (May 1 – Sep 30) windows:

- **Phase 1 (2023-05-01):** Coxsackie GT (gas CT bin), South Cairo (to its
  2024-03-31 retirement), Northport GT1, Port Jefferson GT1, Shoreham 1 & 2,
  Glenwood GT03 (all raw oil units; the LIPA three carry the Part-227-3
  reliability notification — operate only as directed by PSEG LI), 74th St
  GT1/GT2.
- **Phase 2 (2025-05-01):** Astoria GT01, Arthur Kill GT1, 59th St GT1.
- **Documented but NEVER restricted:** the Gowanus 2&3 / Narrows 1&2 barges —
  their compliance plans are ozone-season shutdown from 2025-05-01, but the
  NYISO 2023-Q2 STAR designation kept them in operation (initial period to
  2027-05-01); the NYPA 2030 statutory phase-out rows are record-only.

Availability ONLY, never an offer/price change — the same rule-#12
admissibility class as the CAMPD outage windows (exogenous regulatory
availability event, forward-valid through the 2030 NYPA phase-out; the
windows come from the REGULATION, not from CAMPD idleness).

## Result (vs nyiso-45)

Dispatch delta ≈ nil **by construction** — the restricted units are
rarely-run oil raw units plus ~50 MW of small gas CTs, while the big model
over-runners (Bayonne / Equus / Edgewood / Bayswater LM6000s, vintage
2001–04) are 227-3-compliant and the restricted barges are STAR-designated.
CT_PEAKER 2024 4.54 TWh / ST_GAS 7.77 (C1-2024 −3.31 TWh still FAILs), C3a
−14.4/−14.2/−12.4%, C3b 0.199/0.194/0.191, C2-2025/C5a/C4/C6 PASS, C7/C8
FAIL — all as nyiso-45. The mechanism stands on its measured regulatory
basis (rule #1), not residual movement, and this run is the **most
structurally faithful NYISO probe** (best-so-far basis).

Determination: **NOT-YET** (C1-2024 + C7 + C8 HARD FAILs). Keeper stays
`2026-07-03-nyiso-41-hub-prices`. Open items: the LI/NYC delivered-fuel
basis (LDC citygate/interruptible premium — the residual CT over-run), the
C7/C8 reliability-floor forced-share root cause, the Iroquois Z2 winter hub,
the reserve-scarcity frontier, and the per-interface external flows/ratings
ask (see `calibration_attestation.json`).

## Reproduce

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --nyiso-import-hub-prices --nyiso-iroquois-winter-spread \
  --tranche-startup-amortization --tranche-startup-measured-runs \
  --oil-primary-bin-fuel --nysdec-peaker-rule \
  --out-dir results/calibration/nyiso46_decpeaker
```
