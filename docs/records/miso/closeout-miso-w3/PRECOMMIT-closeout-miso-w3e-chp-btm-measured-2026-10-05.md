# PRECOMMIT — closeout-MISO-w3e: `miso_chp_btm_measured` stacked on the seam-full-span probe, seven legs, scored as structure vs gates

Written and pushed **before any solve**. The desk chartered this on 2026-10-05 after the w3d census ("big find … new evidence on cell R; build it"). It is not a slot request.

```
CONTROL : probe 2026-10-04-closeout-miso-w3-seam (keeper recipe + miso_seam_neighbour_hourly_full_span=true)
ARM     : control + miso_chp_btm_measured=true (one field, default off, MISO-only, cache-key registered)
NOT ON  : mustrun_chp_btm_holdout (the w3c arm); the two reads stay separate
LEGS    : 2019-2025, one shard per year (rules 32/34/36): replay of closeout_miso_nuc_span with both --set flags
EVIDENCE: FINDING-closeout-miso-w3d-chp-selfuse-census-2026-10-05.md
DERIVE  : scripts/data/derive_miso_chp_btm_share.py, which calls the closeout-CAISO-w6 derive() unchanged.
          ONE definition across ISOs: grid = sales for resale + tolling + outgoing over (gross - station);
          retail counts as host; pooled CY2022-2024; plants with EIA-860 BA = MISO.
          Artifact: chp_btm_share_measured_MISO.csv; 94 of 110 MISO CHP plants covered.
```

## Mechanism

Under `chp_steam_following`, a gas CHP plant's LP capacity is nameplate × (1 − BTM share). Its BTM generation is added back after the solve. Today that share is the sector default (`CHP_BTM_PCT_BY_SECTOR`). Its own comment calls the default residual-identified, and miso-192 found no MISO source for it.

The arm replaces the default with the plant's own EIA-923 Schedules 6/7 share wherever the plant files. Examples:

| plant | measured | default |
|---|---:|---:|
| Midland Cogen 10745 | 5.6 % | 35 % |
| Taft 55089 | 23 % | 70 % |
| Sabine River 10789 | 24 % | 70 % |
| Dearborn 55088 | 2.3 % | 35 % |
| Carville 55404 | 2.0 % | 35 % |

**Rules.**
- Rule 14: measured data replaces an estimate.
- Rule 13: the filing regenerates every year and tracks the host arrangement.
- Rule 19: it replaces the default; it does not stack on it.
- Zero DOF.

## Bench basis (declared side effect)

Under the nyiso-149 principle, which CAISO-w6 already applies, `_btm_frame` pins the bench subtrahend to the measured artifact whenever it exists, independent of the flag. So landing the artifact moves MISO's bench basis: bench CC_CHP rises by about 10–12.6 TWh/yr.

**Scoring basis.**
- The arm is scored on that basis.
- The control is re-scored on the same basis with a zero-LP `--rebuild-benchmark` of its composed span, and is also reported on its original bench.
- The keeper's committed bench parts do not move until they are rebuilt.

On the measured bench, the keeper/control C1 CC_CHP would read about −12.7 to −17.2 TWh, a FAIL in every year. That is what the default carve hides.

## Predictions (fixed now)

**Method.** This is the w3d static first-order reach on the control legs:
- Each plant's added grid MW runs at the plant's own solved utilisation.
- That energy is walked down the merit stack at or below each hour's marginal offer.
- C3a uses the static marginal-offer move × 0.53, the w3 seam arm's realised static→LP ratio.
- This is the lower bound: the upper bound delivers the full bench dE, displacing about 1.1–1.7× more.

| year | CC_REGULAR | ST_GAS | COAL_PRB | COAL_BIT | CT_PEAKER | CC_CHP (control @ measured bench → arm) | C3a |
|---|---|---|---|---|---|---|---|
| 2019 | +0.67 → −1.18 | **−8.42 → −9.76 (FAIL, deeper)** | +6.01 → +4.29 | −1.47 → −2.32 | +2.03 → +1.99 | −17.01 → **−8.96 FAIL** | +6.4 → +4.5 % |
| 2020 | −3.10 → −5.04 | **−6.79 → −8.60 (PASS→FAIL, declared)** | +4.70 → +3.36 | −4.14 → −4.65 | −2.82 → −3.27 | −15.46 → −6.56 | **+10.3 → +8.3 % (FAIL→PASS)** |
| 2021 | **−6.41 → −9.15 (PASS→FAIL, declared)** | −5.00 → −5.66 | +4.99 → +4.12 | −0.68 → −1.10 | −3.69 → −3.92 | −14.59 → −7.65 | −4.9 → −6.4 % |
| 2022 | −2.70 → −5.24 | −5.19 → −6.07 | +5.43 → +4.66 | +5.12 → +4.74 | −3.81 → −4.21 | −15.85 → **−8.00 (on the line)** | −3.7 → −5.6 % |
| 2023 | −0.87 → −2.78 | −1.48 → −2.86 | −0.10 → −1.50 | +1.17 → +0.90 | −4.21 → −5.13 | −14.54 → −4.18 | +4.8 → +3.1 % |
| 2024 | +2.61 → +0.96 | −2.43 → −4.35 | −0.56 → −2.01 | −0.74 → −1.11 | −4.64 → −6.07 | −12.68 → −0.95 | +2.5 → +0.5 % |
| 2025 | +5.58 → +3.46 | −4.25 → −5.79 | −4.31 → −5.51 | +0.63 → +0.17 | −6.09 → −7.42 | −17.18 → −6.63 | −3.8 → −5.9 % |

**Declared ex ante as possible PASS→FAIL:**
- C1 ST_GAS 2020
- C1 CC_REGULAR 2021, which would undo the seam probe's win
- C1 CC_CHP 2019 and 2022

**Declared as possible FAIL→PASS:**
- C3a 2020

**Also declared:** C1 ST_GAS 2019 is expected to fail deeper. Under rule 14, a worse ST_GAS fit with measured data points at the MISO-F1 VLR under-commitment, not at this input.

## Reading rule (structure vs gates; no promotion bar)

The RESULT reports, at full magnitude:
- every scored record that moves, control → arm, on the measured bench, with the control also shown on its original bench;
- the prediction error for each row above;
- the realised static→LP ratio;
- the model's CC_CHP grid delivery against the bench, by plant, for the five named plants;
- C8 / D-2 on the composite, plus the CHP floor binding (`chp_btm_floor_pct`).

A prediction missed by more than 2× is reported as a model-of-the-model failure, not treated as a gate.

**Stop conditions.** Each stops the lane and is reported; none is a promotion gate.
- A shard fails.
- A leg's `run_config.json` does not show both flags.
- G-DRIFT turns up a LIVE hunk on the control path that is not the declared bench pin.
