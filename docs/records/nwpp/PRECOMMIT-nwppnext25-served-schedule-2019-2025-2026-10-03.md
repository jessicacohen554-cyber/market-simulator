# PRECOMMIT — NWPP-NEXT-25: served schedule placed at its reporting members' zones, 2019–2025

Written before any solve. Phase 0: `FINDING-nwppnext25-cc-served-schedule-phase0-2026-10-03.md`. Owner card
2026-10-03: "Build and solve".

## The arm

Keeper `2026-10-03-nwpp-next-24-head` (bundle `results/calibration/nwppnext24_span`), replayed with one key:
`--set nwpp_served_schedule_zonal_attribution=true`. Nothing else changes. Seven year-isolated shards, one per
year (rule 36). The replay source is `nwppnext24_span`, committed at the pin.

## What the arm changes, and what it cannot change

- **Changes:** zonal demand only, as the served schedule's measured legs move to the member's zone.
- **System demand is unchanged by construction.** The P1 five-zone demand must equal the keeper's:
  272.855 / 274.572 / 268.646 / 277.900 / 262.091 / 271.480 / 284.095 TWh, ±0.05.
- **Expected P1 zonal demand, TWh (±0.10):**

| year | NW | OR | INLAND | EAST | SNV |
|---|---:|---:|---:|---:|---:|
| 2019 | 117.58 | 38.54 | 40.33 | 44.95 | 31.46 |
| 2020 | 118.53 | 39.85 | 40.32 | 46.12 | 29.76 |
| 2021 | 112.68 | 46.31 | 40.00 | 44.74 | 24.91 |
| 2022 | 118.41 | 47.51 | 41.79 | 44.66 | 25.53 |
| 2023 | 108.44 | 48.06 | 40.91 | 40.16 | 24.51 |
| 2024 | 109.93 | 51.03 | 40.64 | 43.42 | 26.45 |
| 2025 | 114.24 | 51.58 | 40.80 | 49.16 | 28.30 |

## Gates (set ex ante)

- **(a) Governance.**
  - The `scenario_config` diff against the keeper's year config is exactly
    `[('nwpp_served_schedule_zonal_attribution', None|False, True)]`.
  - Zero free parameters; DOF ledger unchanged.
  - C6 must pass. The attestation extends `scripts/gen_nwppnext24_attestation.py` with this one structural key.
- **(b) Verdict diff vs the keeper on the same bench render.** Every record is reported at full magnitude. The
  hypothesis records:
  - C1 CC_REGULAR 2019 / 2024 (+12.17 / +14.90 TWh FAIL; band 8.00);
  - C4 gas 2019 / 2023 / 2024 (r 0.651 / 0.534 / 0.789);
  - seam net exports (COI, NEVP, BC) against measured.

  Watch list:
  - CC 2025 (+7.99 PASS, knife-edge);
  - EAST 2021–2022 (already below PACE);
  - C3a 2025 (−1.6 % PASS) and C3a/C3b 2023 / 2024;
  - C4 coal every year (PASS).
- **(c) Rule 20 / legitimacy.** D-2 forced energy 0 in every class-year. D-1 failure count reported against the
  keeper's 13.

## Promotion rule

Per the owner's standing ruling, promote if structural integrity improves, even if a gate regresses. This arm
places a measured schedule at its physical location (rules 14 and 19). Every regression is reported at full
magnitude, and the promotion goes on one owner card. The close-out desk (session_01ALecU5Wjde4tkbLrnMExT9)
serialises the slot.

## G-DRIFT against the keeper's pin (23beba2a)

Main moved from b54e1d84 to 3bec7bd4: NEXT-24's records, probes and attestation script, with no src change. The
hunks this branch adds on the backcast path:

| hunk | class |
|---|---|
| `_diba_legs_export` `tz=` defaulting to Pacific | INERT, byte-identical for every caller |
| `nwpp_served_schedule_zone_interchange` | read only when armed |
| the `load_demand` branch | gated |
| the `NWPP_MEMBER_LOCAL_TZ` constant | read only when armed; declared on the solve surface at its live hash, so no key moves |
| threading in `runner` / `run_calibration*` | INERT off |
| the raw back-fill | read only by the armed function; the keeper's served schedule reads BA totals and the CISO/BPAT legs, which are unchanged |

Every hunk is INERT for the keeper recipe; the only LIVE hunk is the armed key itself. Control: the keeper's
committed bundle.
