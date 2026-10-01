# FINDING — NYISO-NEXT-16 phase 0: where the 2022 C3b error sits — 2026-09-30

- **Session:** NYISO-NEXT-16 (orchestrator; zero LP).
- **Keeper read:** `2026-09-30-nyisonext15-landing-band-span` (bundle `results/calibration/nyisonext15_span`), plus the per-plant sidecars of its 2022 and 2025 legs (`8433152e`, `eedd688c`).
- **Probe:** `scripts/probes/nyisonext16_phase0.py` → `results/phase0/nyiso/_nyisonext16_phase0.json`. The gas block is a `fleet_only` rebuild of the keeper's `(n_gen, 8760)` fuel-price array (no LP; none of the gas-path files changed between the keeper's `4c98e6dd` and `c8a93df6`).

## 1. C3b 2022 by month (model − RT actual, load-weighted, $/MWh; share of squared error)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| error | −11.3 | −18.5 | +1.9 | +20.3 | +24.1 | +6.6 | +8.3 | +0.1 | +7.6 | +10.7 | +15.8 | −31.6 |
| share | 0.04 | 0.11 | 0.00 | 0.14 | 0.19 | 0.01 | 0.02 | 0.00 | 0.02 | 0.04 | 0.08 | 0.33 |

Two objects, with opposite signs:

- **Winter under-pricing (Dec, Feb, Jan: 48 % of the squared error).** It sits downstate and in Capital: Dec model − measured DA is Capital_Hudson −43.9, Lower_Hudson −19.8, NYC −19.7, Long_Island −30.7. About three-quarters of the Dec gap comes from the measured top-decile hours (model 163 vs 252). The same object carries 2025: Jan −28.1 and Feb −21.5, zone errors −20 to −44.
- **Shoulder over-pricing (Apr, May, Nov: 41 %).** It is almost entirely Upstate_West: model − measured +36.3 / +50.2 / +32.7, while the downstate zones sit within ±9. Upstate median in May is 79 vs 24 measured; Capital_Hudson is 82 vs 93.

## 2. The shoulder object is CENTRAL EAST, and a zonal DF projection cannot carry it

- The measured price step in 2022 sits at E → F: May is Mohawk Valley 33 vs Capital 98, and Nov is 26 vs 83.
- The posted `CENTRAL EAST - VC` limit in 2022 is very low: Apr 1,365, May 1,154, Oct 1,156, Nov 703 MW. In 2024–25 it is 2,475–3,172 MW.
- The measured E→F spread rises with CE loading. Where CE flow is ≥ 0.85 of its posted hourly limit the spread is 44.1; below 0.70 it is 15.0 (2022). The share of hours at ≥ 0.85 is 72.6 / 59.0 / 41.1 / 11.5 / 14.3 % in 2021–2025.
- The model's link carries the TOTAL EAST p90 envelope (NEXT-14) and binds 5 % of May 2022 hours at 3,325 MW, so Upstate_West couples to Capital. The marginal Upstate resource is budgeted hydro (mc 1.4), whose water value is the gas-set price.

**The distribution-factor construction was tested and fails ex ante.** The construction is `CE = α·TE`, fitted by through-origin OLS on measured hourly flows (α = 0.489 / 0.484 / 0.436 / 0.543 / 0.531), giving cap(t) = min(envelope, CE posted limit(t) / α).

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| measured TE above the envelope, % h | 10.0 | 10.0 | 10.2 | 10.1 | 10.2 |
| measured TE above the DF cap, % h | 32.6 | 29.7 | 14.9 | 10.3 | 10.6 |
| E→F spread near the DF cap / elsewhere | 16.4 / 12.7 | 36.5 / 34.3 | 11.5 / 7.9 | 8.1 / 1.5 | 14.2 / 4.2 |

- The market moved more TOTAL EAST than the projected cap allows in about a third of 2021–22 hours. A physical cap is not exceeded that often.
- In 2022 the projection does not find the binding hours: the spread is the same near the cap as away from it.
- The CE share of TE varies too much for one zonal link to carry CE. Variants tried: an intercept, and fitting only in the binding regime (CE ≥ 0.85 or 0.90 of limit). Each is exceeded in 30–37 % of 2021–22 hours.
- **Not solved** (rule 1 (c): no limit is chosen by where the gates land). The remaining structural route is topological (a separate E→F element), which is a design task, not a lever.

## 3. The model's delivered gas (keeper, 2022 / 2025)

- **Pass order.**
  1. The hub overlay gives every gas unit one Iroquois-Z2 reference series: Transco monthly plus a flat annual spread (+1.78 in 2022, +1.38 in 2025), on the Transco Z6 NY daily shape.
  2. The zonal basis then adds each zone's SOM annual offset (Upstate_West −3.07).
  3. NYC/LI CT_PEAKER go on the Transco daily index plus LDC transport.
  4. The dual-fuel cap is applied last.
- **Upstate_West inherits the New England winter shape.**
  - 2022: Jan 9.67 and Dec 7.84 $/MMBtu, against the Tenn Z4 annual 5.75 on the Henry Hub shape (3.71 and 4.86).
  - The spring months are **cheaper** than that construction: Apr 4.90 vs 5.93, May 6.17 vs 7.47, Nov 3.82 vs 4.78.
  - In 2025 summer the model sits at 0.24–0.80 against about 2.4.
  - **So gas does not explain the spring overshoot**, which runs the other way.
  - This is the phantom nyiso-150 measured (Jan 2025 $11.01 vs about $3.5).
- **Downstate cold-day spikes reach the reference at full magnitude, then the oil cap removes them.**
  - 76 % of downstate gas capacity is dual-fuel: NYC 80 %, Long_Island 91 %, Capital_Hudson 61–64 %.
  - The cap sits at about $25 in Dec 2022 and about $19 in Jan 2025.
  - The Elliott weekend (Dec 24–26) is interpolated across a trading gap (31.5 → 15.2), as is Jan 2025's MLK gap. That object is the adjudicated `nyiso_hub_gap_month_level` cell (R); it is not re-opened here.

## 4. What this makes testable

- **`nyiso_iroquois_winter_spread` (cell R, nyiso-150) has new evidence.** It was refused because "the LP prices the four mainland zones as ONE COUPLED BLOCK (the internal west→east cutset never binds), so no fuel-side mechanism can create the winter downstate premium".
- NEXT-14 removed that premise. The cutset link now binds 16.9 / 27.2 / 17.3 / 8.9 / 12.8 % of P1 hours (2021–2025).
- The rule-14 defect the flag repairs is measured in §3:
  - Upstate_West's gas moves onto its own hub (the SOM annual level on the Henry Hub shape) instead of the New England winter shape.
  - The eastern reference carries the measured annual Iroquois–Transco spread in the months the Algonquin scarcity signal puts it, capped at the Algonquin ceiling.
  - Zero free parameters.
- Construction check (zero LP): the flag's series resolve in all five years, so it cannot fall through inert. Each zone's annual mean equals its measured SOM value (Upstate_West 3.38 / 5.75 / 1.82 / 1.83 / 2.94).
