# FINDING — closeout-infra-bugs: leap-year model clock and the PJM EIA-930 interchange label

Lane: `claude/closeout-infra-bugs`, chartered by the backcast close-out desk (2026-10-05). The two bugs were
reported by closeout-PJM-w3 (`docs/records/pjm/closeout-pjm-w3/RESULT-closeout-pjm-w3-cc22-nuclear-2026-10-04.md`
§4 and the desk charter). Base: `origin/main` 50e616e6. **Zero LP.** Evidence scripts and the census JSON are in
`infra-bugs/` next to this file. The landing proposal is in `PRECOMMIT-closeout-infra-bugs-2026-10-05.md`.

## 1. BUG 1 — leap year: real, but the reported diagnosis is inverted

**The report:** `_hour_to_month_index` uses a 365-day table, so in 2020 and 2024 the hours after Feb 29 are binned
one day early.

**What the code does:** the 365-day table is correct. The model clock drops a leap year's Feb 29 everywhere:
- `utils/hour_calendar.py` defines it that way.
- `eia930.frames._eia_hourly_frame` filters out the local Feb 29, so demand and renewables follow it.
- CAMPD, reserve requirements, PJM ties, outages and SPP gas outage all use the same clock.

So model hour 1416 is Mar 1 00:00 in every year, and `_hour_to_month_index(…)[1416]` = March is right. The measured
monthly CF rows the PJM lane flagged are read correctly.

**The actual bug is the opposite one.** 23 call sites build `pd.date_range(f"{year}-01-01", periods=hours, freq="h")`
as the model clock. 20 of them read a month, day or weekday off it; the other 3 read only the hour of day and are
inert. In a leap year that range *keeps* Feb 29 and stops at
Dec 30 23:00, so from Mar 1 on every model hour is labelled **one day early**:
- **Month-keyed tables:** the first day of each month Mar–Dec reads the previous month (240 h).
- **Day-keyed inputs** (Henry Hub gas day, daily Tmax/Tmin, the NYISO On-Peak weekday/holiday mask): read the
  previous day on every day Mar 1–Dec 31 (7,344 h).
- **Hour-of-day:** unaffected.
- **`run_calibration_full._hour_months`:** gives February 29 days and December 30, so monthly-flat profiles also
  misallocate energy within the month.

**Fix** (branch `claude/closeout-infra-bugs-leapclock`, `dfe60e6e7de13d04759a7d19af39590a5cbfcae0`):
- One helper, `hour_calendar.model_clock(year, hours)`, gives the naive stamp of each model hour with Feb 29
  skipped. All 23 sites use it.
- The two existing tests that assumed an 8784-h leap horizon (`test_nyiso_incity_obligation` July 4,
  `test_pjm_offer_surface_within_season`) are updated. The model never runs 8784 h (rule 8).
- New tests, trivial cases first:
  - 2020-02-28 23:00 → 2020-03-01 00:00 is adjacent;
  - hour 1416 is Mar 1;
  - 2020 and 2024 end on 12-31 23:00;
  - common years equal `date_range`;
  - `model_clock` month = `_hour_to_month_index` = `month_of_hour`;
  - round trip through `hour_index`;
  - Mar 1 2024 is a Friday;
  - a guard forbids the naive form in `src/` and `run_calibration_full.py`.
- Backcast-scoped `SolveEpoch 2026-10-05a` plus a ledger entry in `results/cache.py`.
- The fast lane is green apart from the two updated tests, which now pass.

| Call site | Field | Keeper that arms it |
|---|---|---|
| `eia930/envelopes.py` `pjm_zonal_interchange_envelope` / `pjm_neighbor_interchange_envelope` / `pjm_net_interchange_envelope` (source **and** target clocks) | month | PJM (`pjm_congestion`, `pjm_seam_flow_limit`/`_export_limit`, `pjm_external_net_position_cut`) |
| `eia930/envelopes.py` `measured_gas_floor_profile` | month | CAISO (`caiso_gas_floor_frac` 0.8) |
| `neighbor_price.caiso_hub_measured_gas_reference_price` | month | CAISO (`caiso_intertie_gap_fill_measured_gas`, gap hours only) |
| `fleet/offer_surfaces._ercot_gas_day` (cleared-share, fast-start pool) | day | ERCOT |
| `fleet/offer_surfaces._pjm_midcurve_context` | day | PJM (`pjm_offer_midcurve_conditional`) |
| `reserves/spec.nyiso_onpeak_mask` → LI 30-min requirement | weekday, holiday | NYISO (`nyiso_li_locational_reserve`) |
| `eia930/weather._broadcast_daily_to_hourly` (`iso_zone_tmax`, `neiso_load_weighted_temp`) | day-of-year | temperature-driven reliability-floor specs (CAISO, ERCOT, MISO, PJM, NEISO, NYISO), MISO `temp_derate_classes` CT_CHP/ST_CHP, NEISO coldsnap derate and winter fuel inventory |
| `run_calibration_full._hour_months` → `_must_run_profiles` | month | every ISO (biomass/OTHER injection) |
| `run_calibration_full._hour_months` → `_e930_series_annual_monthly` | month | every ISO (benchmark monthly split; annual unchanged; scoring only) |
| `fleet/offer_surfaces._ercot_offer_*` midcurve/offline-commit, `offer_curves.apply_miso_offer_spread_anchored`, `envelopes.measured_interchange_envelope`, NEISO coldsnap window, CAISO gas-floor window, `weather` hod | day / month / hod | none armed, or hour-of-day only (inert) |

**Not fixed: frozen derive scripts with the same idiom** (rule 23; their products re-derive only on a data update).
These are candidates; none was audited for actual leap exposure:
- `scripts/lib/outage_detect.py:296/685/919` (296 special-cases Feb 29);
- `derive_thermal_tranche_oom_level_mw.py:163/172`;
- `derive_campd_temp_derate_params.py:216/227`;
- `derive_nyiso_offer_level_dispersion.py:134`;
- `reconstruct_eia_generation_profiles.py:169`;
- `build_ercot_as_by_restype_from_60day.py:257`;
- `derive_miso_gas_variable_transport.py:146`.

## 2. BUG 1 census (zero LP; old clock vs `model_clock`; `infra-bugs/leap_clock_census*.py`)

Σ|Δ| is over the 8,760 hours; "share" is Σ|Δ| / Σ|level|.

| ISO-year | Input | Hours moved | Σ\|Δ\| | Share | Max hourly Δ |
|---|---|---|---|---|---|
| PJM 2020 / 2024 | zonal tie envelope, import cap | 5,146 / 4,877 | 0.90 / 1.23 TWh | 3.2 / 2.7 % | 2.08 / 2.20 GW |
| PJM 2020 / 2024 | zonal tie envelope, export cap | 5,586 / 6,898 | 1.39 / 2.81 TWh | 1.5 / 3.0 % | 2.71 / 3.20 GW |
| PJM 2020 / 2024 | seam envelope, import cap | 5,836 / 4,819 | 0.49 / 0.52 TWh | 3.0 / 2.0 % | 1.15 / 1.30 GW |
| PJM 2020 / 2024 | seam envelope, export cap | 5,615 / 5,106 | 0.81 / 0.89 TWh | 1.2 / 1.3 % | 1.60 / 1.74 GW |
| PJM 2020 / 2024 | net-position cut | 3,871 / 2,758 | 0.72 / 0.85 TWh | 2.7 / 5.8 % | 1.89 / 4.31 GW |
| PJM 2020 / 2024 | midcurve gas day | 4,848 / 4,728 | 518 / 618 $/MMBtu·h | 2.2 / 2.4 % | $0.76 / $0.77 |
| ERCOT 2020 / 2024 | offer-surface gas day | 4,848 / 4,728 | 518 / 618 $/MMBtu·h | 3.9 / 4.0 % | $0.76 / $0.77 |
| CAISO 2020 / 2024 | midday gas floor (0.8 × p50 NG) | 240 / 240 | 0.36 / 0.41 TWh | 0.6 / 0.6 % | 4.8 / 7.7 GW |
| CAISO 2024 | measured-gas hub reference (PNW / DSW) | 240 | 1,064 / 1,859 $/MWh·h | 0.4 / 0.7 % | $11 / $22 per MWh |
| NYISO 2024 | LI 30-min requirement (On-Peak mask) | 1,504 | 406 GWh·MW-req | 11.7 % | 270 MW (flip 270↔540) |
| NEISO 2020 / 2024 | load-weighted temperature (coldsnap driver) | 7,344 | 23,381 / 21,560 °C·h | ≈ 3.2 °C mean per moved hour | 12.3 / 12.4 °C |
| all, 2020 / 2024 | zone daily Tmax/Tmin | ≈ 7,000–7,350 per zone | PJM 8 zones 188k / 181k °C·h Tmax | — | 11–26 °C |
| all, 2020 / 2024 | biomass + OTHER must-run | 1,632 | 2–190 GWh per ISO (largest: MISO 2020 0.18 TWh) | ≈ 0.7 % relocated; **annual energy unchanged** | 8–461 MW |

Notes on the census:
- NYISO's keeper carries 2021–2025, so only its 2024 leg is exposed.
- Each ISO's other years are byte-identical under the fix.
- The temperature rows are input deltas. Their MW effect runs through floors and derates that need the fleet,
  and is not computed here.
- For the PJM envelopes, the percentile tables themselves move (the source series was mis-bucketed too), so the
  change is not limited to the 240 boundary hours.

## 3. BUG 2 — the EIA-930 per-DIBA interchange label

The claim was tested on all 24 files under `data/raw/eia-930-interchange/`. Each was correlated (first
differences, shifts ±10 h, winter and summer separately, 2019–2025) against:
- its own BA-hourly `Total interchange` on `UTC time`;
- for PJM, also the PJM tie-line meter. That meter matches PJM's BA-hourly TI at shift 0, r 0.994–0.999.

| File | Verified basis |
|---|---|
| CISO, BPAT, AVA, AVRN, CHPD, DOPD, GCPD, GRID, IPCO, NEVP, PACW, PGE, PSEI, SCL, TPWR | Pacific prevailing hour-ending (as documented) |
| PACE, NWMT, WAUW | Mountain prevailing hour-ending |
| ERCO, SWPP, SOCO | Central prevailing hour-ending |
| ISNE | Eastern prevailing hour-ending |
| MISO | fixed EST hour-ending (as its consumers assume) |
| **PJM** | **UTC hour-BEGINNING labelled `local_time`**, every year 2019–2026, constant across DST |

**PJM evidence.** Differenced against the tie meter's `datetime_beginning_utc`:
- At zero shift, |r| is 0.886 / 0.895 / 0.919 / 0.906 / 0.931 / 0.907 for 2020–2025.
- At every other shift, |r| ≤ 0.22. This lane's own 2023 re-check gives −0.904 at 0 and ≤ 0.15 elsewhere.
- In EST hour-beginning model terms the shift is label − 5 h, as the PJM lane found.

**Second PJM defect.** The per-DIBA sign is inverted from the start of the file through about 2019-10-31 (monthly r
vs the tie meter is −0.89 to −0.99 for Jan–Oct 2019, and +0.90 to +0.98 after). It is not registered; the flip
hour needs pinning first.

**Side note.** PJM's BA-hourly `Total interchange` for 2025 does not track the tie meter (differenced r 0.155).

**Consumers.** Exactly one live consumer reads the PJM file: `scripts/data/derive_pjm_seam_ladders.py::eia930_crosscheck`.
It prints annual TWh per seam as a cross-check; the ladders use the tie meter. Its year bucketing moves by
≤ 0.04 TWh per year. Every other consumer of the interchange family reads a correctly labelled file:
- MISO seam envelopes (`MISO_SEAM_DIBA`; return None for PJM);
- the CAISO corridor clock;
- NWPP legs;
- the ERCO DC-tie;
- the NEISO/MISO derives.

**No registered keeper reads the PJM file.**

**Hypothetical magnitude.** If a PJM (month × hod) p90 envelope were built from this file, the current convention
(label − 1 h as EPT) would misplace 5–13 TWh·h per year of envelope, up to 5.6 GW in one hour (2024). Today it is
a trap for future use, not a live error.

**Fix (lands with this FINDING; solve-surface neutral):**
- `derive_pjm_seam_ladders.pjm_eia930_label_to_est` reads the label as UTC and converts to fixed EST. It has 4
  tests: 05:00 UTC → EST midnight; 2020-01-01 04:00 → 2019; summer fixed offset; spring-forward day stays 24
  distinct hours.
- The interchange `README.md` now documents the PJM clock exception and the 2019 sign window.

## 4. What this finding does not do

It does not re-pull PJM through `fetch_eia930_interchange.py --source bulk`. That needs network access and a
decision; the root cause (EIA submission vs fetch path) is open. It does not register the PJM 2019 sign window, and
it changes no keeper input on `main`.
