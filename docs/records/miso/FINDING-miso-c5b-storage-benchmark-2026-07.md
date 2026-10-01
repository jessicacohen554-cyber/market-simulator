# FINDING — MISO C5b storage throughput (+1330%): benchmark basis artifact, no adder warranted

**Date:** 2026-07-06. **Lane:** Wave-3 MISO L-14 (gap register G-23 storage item).
**Question (work item):** the miso-41 keeper FAILs C5b in 2025 at **+1330.1%** (model 3.4995 TWh
discharged vs actual 0.2447 TWh). Ground the pumped-storage per-ISO throughput adder and/or
`battery_dispatch_adder` in a citable market/physical source (rules 5/13), or write the finding
that no defensible source exists and leave the adders alone.

**Verdict: no adder. The FAIL is a measurement-basis mismatch, not a model cost error.** The
EIA-930 "actual" is battery-only; the model side is battery + 2,417 MW of pumped storage. The
model's PS throughput is *consistent with the measured PS net-energy behavior* — an adder sized
to close this residual would suppress real, measured pumped-storage arbitrage, the exact
mis-measured-target failure that retired PJM's fitted $10 adder
(`constants.PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` history note). No solve was run; no dashboard
registration applies (no run produced).

## 1. The comparison basis is misaligned (verified in the raw data)

- **Model side** (`render_calibration_html._model_storage_twh`): sums discharge over **every**
  storage unit — li-ion **plus** pumped storage. The MISO PS fleet from EIA-860 is **2,416.8 MW /
  24,168 MWh**: Ludington 1,978.8 MW (MISO-East zone aggregate), Taum Sauk 408 MW (MISO-Plains),
  30 MW (MISO-South). Batteries are 87.7 / 141.7 / 801.9 MW (2023/24/25).
- **Actual side** (`_actual_storage_twh`, series `battery` / `pumped_storage` / `battery_discharge`):
  `data/raw/eia-930-hourly/MISO hourly.parquet` carries **only `NG: BAT`** — there is no
  `NG: PS` column. Verified in the source-of-truth balance files
  (`data/raw/eia-930/EIA930_BALANCE_{2023,2024,2025}_*.parquet`): MISO's
  "Net Generation (MW) from Pumped Storage" column (raw, imputed and adjusted) is **all-null in
  every scored year**. MISO simply does not report a PS series to EIA-930.
- So C5b 2025 compares **model BAT+PS (3.50 TWh)** against **actual BAT-only (0.2447 TWh**, series
  begins Feb-2025, 8,424 non-null hours). 2023/24 are SKIPPED (no BAT series yet), so the one
  scored year is exactly the year the basis mismatch is total.
- **No hydro double-count on either side:** MISO's `NG: WAT` is the balance files'
  "Hydropower **Excluding** Pumped Storage" (2025: 9.839 TWh balance vs 9.880 TWh hourly extract;
  WAT has zero negative hours). Ludington/Taum Sauk output is absent from EIA-930 MISO entirely —
  not folded into WAT.

## 2. The model's PS throughput matches the measured PS energy balance

Pumped-storage gross discharge is not directly published, but its **net generation is measured**
(eGRID, `data/raw/fleet-egrid/`): Ludington + Taum Sauk net = **−0.940 TWh (2023)**,
**−1.109 TWh (2024)**. For a pure pumped-storage plant, net = −P(1−RTE) and gross discharge
G = |net|·RTE/(1−RTE):

| basis | 2023 implied gross discharge | 2024 |
|---|---|---|
| RTE 0.73 (Ludington design, Consumers Energy/DOE PSH) | 2.54 TWh | 3.00 TWh |
| RTE 0.80 (model constant, DOE/Sandia mid-band) | 3.76 TWh | 4.44 TWh |
| **model total discharge (miso-41, BAT+PS)** | **2.82 TWh** | **2.92 TWh** |

The model sits **inside the measured-implied band** — the LP is not over-cycling the PS fleet.
Even a *perfect* model (BAT = actual 0.245 + PS at its measured-implied ~2.5–3.0 TWh) would score
**≈ +1,000–1,200%** against the battery-only actual. C5b as currently scored is unpassable for
MISO by construction; the +1330% measures the benchmark's coverage gap, not model skill.

## 3. Adder adjudication (rules 5/13)

- **Pumped-storage adder — NO defensible source; leave `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`
  empty for MISO (resolves 0.0).** PSH variable O&M is < $1/MWh (NREL ATB; DOE/Sandia Energy
  Storage Handbook) and cycling degradation is negligible (30k+ cycle mechanical life) — neither
  moves TWh-scale throughput. The one real suppressor of PS cycling is reserve/regulation duty,
  which is a **measured power-reservation channel** (the ERCOT `reserve_storage_as_power`
  analogue), not a $/MWh throughput price — exactly the PJM adjudication recorded in
  `constants.py`. And per §2 there is no genuine over-cycling residual to price anyway: any
  nonzero MISO PS adder would be a fit to a mis-measured target.
- **`battery_dispatch_adder` — citable sources exist, but enabling it here is not scoreable;
  leave 0.0 this session.** Cycling degradation is a real, citable cost (~$15–25/MWh li-ion,
  NREL ATB 2024 cycle-life basis; $25–50/MWh in Xu, Zhao, Zheng, Litvinov & Kirschen 2018, IEEE
  TPS 33(2)). But against the current battery-only benchmark the C5b record FAILs at any adder
  value (the 3.26 TWh gap is ~93% pumped storage), so a value could only be "validated" by
  tuning to the residual — forbidden. Enable it only after the basis fix below, scored against
  the aligned BAT-vs-BAT comparison.
- **`storage_vintage_ramp` — the larger grounded battery-side lever, same gate.** 660.2 of the
  801.9 MW of 2025 MISO batteries have 2025 CODs (Mar–Nov, EIA-860 Operating Month); the keeper
  runs `storage_vintage_ramp=False`, so the model holds the year-end battery fleet online all
  year (~2× the true fleet-year MW). This is measured physical availability (the CAISO COD-ramp
  analogue, admissible under rule 13), and together with the degradation adder it is the honest
  battery-side package — but it is unscoreable until C5b compares batteries to batteries.

## 4. Recommended fix (rubric/scorer infrastructure — outside this lane's file ownership)

C5b/C5c should compare like-for-like per BA-year: when a BA reports **battery-only** storage to
EIA-930 (no PS series — MISO; also any BA whose PS column is all-null), score **model battery-only
discharge** against `NG: BAT`, and mark the PS portion UNSCOREABLE (or score it separately against
the eGRID net-energy-implied band of §2). The bundle's `storage.parquet` already carries `tech`
(`li_ion` / `pumped_storage`), and the run payload/bench builder
(`scripts/render_calibration_html.py::_model_storage_twh/_actual_storage_twh`) is where the split
lands. Owned by the rubric-infrastructure lane, not L-14 — flagged to the owner via this finding.
Until then, the MISO C5b row should be read as SKIPPED-in-substance (basis-mismatched), the same
way PJM's C5b is recorded as having "no clean scoreable actual"
(`docs/multi-iso/pjm-ps-cycling-diagnosis-2026-06.md`).

## 5. Rule-13 admissibility note on §2's use of measured data

The eGRID net-generation figures are used here only to **adjudicate the benchmark** (is the model
over-cycling? no) — they set no model input, no bound, no adder. The RTE-implied gross-discharge
band would regenerate for a forward year from forward drivers (fleet RTE × forecast net-energy
duty) and is cited for diagnosis, not fed back into the solve.
