# FF-2B — NEISO capacity-hindcast PRE-REGISTERED bands (2026-07-19)

**Pre-registration, filed BEFORE the run (governance gate).** This file records
the score bands NEISO's **first** capacity-hindcast pair
(`neiso-2021-2025-fixed` + `neiso-2021-2025-curve`) will be graded against,
committed **before** the run bundles so no band can be moved after seeing a
result (CLAUDE.md rules 1/11/14; plan §7.6 "bands are never widened"). NEISO has
never had a capacity hindcast (capacity-clearing flip memo 2026-07-16 §1.4/R-7:
"no NEISO capacity hindcast exists at all"), so this pair makes its flip-gate
items 3–4 gradeable for the first time.

## Bands (the standard T-R battery — NOT widened for NEISO)

The bands are exactly `scripts/score_capacity_hindcast.py::BANDS` (plan §1.4)
plus the T-R10 no-inversion guard — the same battery every scored ISO
(ERCOT/PJM/MISO) uses. NEISO is scored on the identical bars; nothing here is
relaxed for a new ISO.

| Metric (score.json key) | Band | Rule |
|---|---|---|
| `thermal_gw_retired_total` | \|err\| ≤ 10 % of actual | T-R1 |
| `thermal_gw_retired_perfuel` | \|err\| ≤ 20 % of actual (per fuel) | T-R1 |
| `retire_recall` | ≥ 0.70 | T-R1 |
| `false_retire_frac` (raw **and** IS-2020) | ≤ 0.15 | T-R1 / T-R8 |
| `retire_timing_years` | ≤ 1.5 yr mean abs | T-R1 |
| `add_gw_frac` (wind/solar/gas) | \|err\| ≤ 15 % | T-R2 |
| `add_gw_frac` (storage) | \|err\| ≤ 25 % | T-R2 |
| `techmix_share_pp` | ≤ 5 pp | T-R2 |
| `co2_2025_frac` | \|err\| ≤ 10 % | T-R3 |
| `T-R10a` (first-mover recall) | no fuel with actual>0 retires 0 in-window | T-R10 |
| `T-R10b` (zero-real accumulation) | ≤ 0.5 GW forced on a zero-actual fuel | T-R10 |
| I5 (no retire-and-reenter), I13 (no sawtooth) | must hold both legs | invariants |

Curve-ON leg additionally reports the per-vintage clearing-position trace
(fixed vs curve), but the **pass/fail battery above is identical** for both
legs — the pair measures whether arming the CR-1 sloped demand curve changes
the retirement/addition record, not a different scorecard.

## NEISO-specific context (reported, does NOT move a band)

NEISO is a **small-turnover** system over 2021–2025 (built target
`data/raw/_validation-source/capacity_actuals_neiso.csv`, 2026-07-19):
retirements ≈ **1.0 GW** (coal 0.5, gas_ct 0.21, gas_cc 0.10, oil 0.08, biomass
0.06), additions ≈ **3.0 GW** (solar 1.95, storage 0.64, wind 0.22, gas_ct
0.16). Consequences, pre-registered so they are read as expected rather than as
a pass/fail surprise:

- **Low retirement signal.** With ~1.0 GW retired across the window, the
  `retire_recall` and `false_retire_frac` metrics are computed on a small base;
  a single mid-size unit swings them. They are reported with raw counts so the
  base is visible; the bands are **not** loosened for the thin base.
- **Per-fuel retirement fractions on <0.3 GW fuels** (gas_ct, gas_cc, oil,
  biomass) are high-variance by construction; the total-GW band (10 %) is the
  primary retirement bar, per-fuel (20 %) secondary, exactly as for the other
  ISOs.
- **Additions are VRE/storage-dominated** (2.8 of 3.0 GW), so the add battery
  is effectively a wind/solar/storage test; the storage 25 % band applies to
  the 0.64 GW storage line.
- **CO₂-2025** is graded against the same 10 % band; NEISO's small thermal fleet
  makes it sensitive to a single CC's dispatch, reported not re-banded.

## Quarantine / provenance

Plain hindcast, EIA-860 **2020 vintage**, evolve 2021→2025: **2021 seeds** (the
rule-22 `{2021}` hindcast allowance — NEISO carries a calibration-complete
marker in `frontend/data/backcast/calibration-complete.json`, verified present
2026-07-19, so the allowance holds), **2022 is bridged (evolved, never solved,
data never read)**, **2023–2025 scored**. `--fuel-variant realized`. Nothing
here touches 2019 / H1-2026 / a locked test. Registered on the
forecast-validation dashboard only — never the backcast registry (plan §7.5).

## Pair definition

```
scripts/run_capacity_hindcast.py --iso NEISO --fuel-variant realized \
    --out-dir results/hindcast/neiso-2021-2025-fixed
scripts/run_capacity_hindcast.py --iso NEISO --fuel-variant realized \
    --capacity-market-clearing \
    --out-dir results/hindcast/neiso-2021-2025-curve
scripts/score_capacity_hindcast.py --bundle results/hindcast/neiso-2021-2025-fixed
scripts/score_capacity_hindcast.py --bundle results/hindcast/neiso-2021-2025-curve
```

The fixed leg is the harness default (`capacity_market_clearing` off); the curve
leg arms the CR-1 sloped demand curve for NEISO only
(`capacity_market_clearing_by_iso={"NEISO": True}`, the scalar stays off).
