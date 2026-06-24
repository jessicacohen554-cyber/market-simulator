# MISO miso8 campd-binning — run summary

> **ABLATION / SUPERSEDED.** This is the binning-only, **pre-timezone-fix** point.
> The combined keeper `miso8 tz-localclock` (PR #853 — this binning **plus** the
> MISO UTC-vs-local clock fix) is on main and supersedes it. Kept only to isolate
> the per-plant binning effect. **Clock caveat:** solved on the old UTC demand
> clock, so the diurnal/shape comparison vs main's now-local-clock benchmark
> shows a ~5–6h phantom phase error (the artifact the tz fix removed), not a model
> result — only the year-mean LMP level (clock-independent) is a valid read here.

**Determination: NOT-YET.** Governance gate unattested (no
`calibration_attestation.json`); plus real MODEL MISSes (scarcity tail, family
volumes, CO2) that are NOT caused by the binning change. Registered as the new
best-structure MISO build — the per-plant offer-curve representation every other
non-ERCOT ISO already uses.

## What this run is

The structural step MISO was missing: it moved off the legacy equal-width
`aggregate_fleet` heat-rate path onto **per-plant CAMPD tranche binning**
(`MISO` added to `CAMPD_BINNING_ISOS`). The runner now synthesizes one LP unit
per plant via `fleet_to_bins`, each split into must-run / committed / economic /
peaking tranches forming a rising offer curve, sized from the new
`data/raw/_processed-legacy/thermal_tranches_MISO.csv` (CAMPD years 2023–25):

- **44 coal plants** get a measured online Pmin (~20–30% of nameplate) — a real
  per-plant take-or-pay floor, so coal holds its overnight/morning baseload
  instead of cycling to zero (the legacy path forced coal `pmin=0` with a coarse
  ~45% must-run class default).
- **CC plants** get a per-plant committed band (~45% capacity-weighted) instead
  of the coarse 30% class default, so CC no longer under-runs at minimum load.

Solved on current main, so it also carries the all-ISO **biomass measured
must-run** change (#844): biomass is injected as a fixed EIA-923 profile and the
raw biomass LP units are dropped, so biomass no longer over-runs and displaces
gas.

Config mirrors the prior keeper `miso7` reserve-coopt build:
`--energy-reserve-coopt --priced-interchange --reference-price-interface
--miso-firm-imports`. P1 only. All three testing years (2023/24/25).

## Result (system LMP level, $/MWh)

| year | miso8 model | actual | Δ | legacy miso7 |
|------|------------:|-------:|------:|------------:|
| 2023 | 31.49 | ~31.79 | −0.9% | −8.8% |
| 2024 | 27.99 | ~30.80 | −9.1% | −15.9% |
| 2025 | 39.34 | ~42.85 | −8.2% | −13.4% |

The per-plant coal floor + biomass must-run pull the LMP **level** materially
closer to actual on all three years — **C3a mean-LMP and C3b price-shape now
PASS** (2023 is near spot-on). This is the headline.

## Where the miss lives (none of it the binning)

- **Scarcity tail absent (C3c).** Model 0 h >$200 every year vs actual
  30/37/88. The reserve/scarcity co-optimization is structurally present but
  stays inert on the perfect-foresight LP. The dominant remaining LMP-level
  driver. Pre-existing, MISO-wide (same as miso7).
- **Import/export-node seam (C1/C2 volumes).** 2025 net interchange sign-flips
  (model +8.7 TWh net **export** vs actual −19 TWh net **import**), so domestic
  generation over-fills and **2025 coal +23%**; 2024 over-imports instead.
  Energy-balance drift exceeds ±3 TWh tol in all years. This is the priced-
  interchange/seam calibration, not the fleet binning.
- **No zonal price separation.** North = Central (12 GW N↔C placeholder link
  never binds). Pre-existing.
- **CO2 (C5a)** tracks the gas under-dispatch.

## PRB note (separate lever, not the next fix)

`COAL_SIGMOID_DEFAULTS` (scenarios.py) has no MISO entry, so the PRB passthrough
stays the flat scalar (full delivered fuel cost, no gas-keyed discount), unlike
ERCOT/PJM. A MISO PRB sigmoid is a legitimate offer-curve lever, but: (1) it is
offer-curve tuning, downstream of this structural change (rule #1); (2) it must
be **derived** from CAMPD/EIA-923, never fit to the residual (rules #11/#12);
and (3) a cheap-gas PRB **discount** would lower coal offers → more coal → push
the already-low LMP further from actual, the wrong direction for MISO's current
miss. So it is a low-priority follow-up, not blocking.

## Coordination

The sibling MISO demand/renewable **timezone-alignment** fix (demand on UTC,
renewables on local) had **not** landed on `origin/main` at solve time. When it
merges, re-solve this config so the keeper reflects both changes.
