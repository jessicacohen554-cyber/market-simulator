# ERCOT enrollment-driven forward load-resource RRS-UFR credit (forward analogue of the measured NP3-911 cleared RRS-UFR MW)

**Date:** 2026-06-27
**Branch:** `claude/load-resource-rrs-forecast-r1tuwm`
**Status:** lever BUILT, tested, default-off (rides on `ercot_load_resource_reserve`),
ERCOT-gated, legacy/measured path byte-identical behind the flag, pure-LP. Closes
G4 of `docs/forecast-methodology-gaps-2026-06.md` — the **last measured AS input on
the supply side**. The multi-product co-opt (c132c7a), RTOLCAP reserve-supply cap +
ORDC adder (300b89c), forward AS requirement (G3, 55d3af6 / run163) and endogenous
storage energy-vs-AS (G5, ea8c656 / run164) were already forward-native; this
gives the load-resource RRS series its forward analogue too.
**Reads first:** `docs/forecast-methodology-gaps-2026-06.md` G4,
`docs/ercot-multiproduct-as-coopt-2026-06.md`,
`docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md`,
`docs/ercot-storage-as-endogenous-2026-06.md`.

---

## The gap (what was measured)

The co-opt credited ERCOT's load-side Responsive Reserve by **reading the measured
NP3-911 cleared RRS-UFR MW** (`scarcity.ercot_load_resource_reserve_mw`, the
`rrsufr_mw` column of `ercot_<year>_as_up_mw.parquet`). RRS-UFR — Responsive Reserve
provided by **Load Resources** via high-set under-frequency relays — is by ERCOT
protocol an exclusively load-side service (~0.8–0.9 GW today, capped ~1.4 GW). It is
real reserve supply the co-opt's thermal+storage headroom rows omit, so without the
credit the LP clears reserve lower on the ORDC curve than reality and prices a
scarcity adder in non-scarce hours. But the credit was the measured cleared series —
a future year has no NP3-911 report, so it had no forward analogue.

## What this build is

`lr_rrs(t) = enrolled_DR_MW(year) x availability_shape(t)` — an **enrollment-driven
forecast** of load-side RRS-UFR participation, wired as the forecast branch of the
existing load-resource credit:

1. **Enrollment trajectory** (`scarcity.ercot_lr_rrs_enrolled_mw`, constants
   `ERCOT_LR_RRS_ENROLL_*`). Load-resource RRS-UFR participation is a growing
   market/policy trend (large flexible loads — LNG, refining, data-center/crypto,
   industrial DR — increasingly register as Load Resources). Linear growth off the
   present ~0.9 GW anchor (900 MW at 2025) at 60 MW/yr, saturating at the
   protocol-bounded ~1.4 GW cap. A forward-reproducible trajectory that responds to
   changed conditions — never the measured cleared MW pinned to a price (#12).
2. **Availability shape** (`scarcity.ercot_lr_rrs_availability_shape`, constant
   `ERCOT_LR_RRS_AVAILABILITY_HOD`). A deterministic hour-of-day shape **normalized
   to a mean of exactly 1** so it redistributes — never rescales — the enrolled
   level: Load Resources (large industrial facilities) are most available to be
   tripped during weekday daytime/evening operating hours, modestly less so in the
   deep overnight. Tiled across the 8760-h clock with `np.tile` (no hour loop).
3. **Mode-aware selector** (`scarcity.ercot_load_resource_reserve_credit_mw`). The
   single seam both co-opt input builders read: **backcast** returns the measured
   NP3-911 realization (byte-identical to the legacy path, the validation target);
   **forecast** returns the enrollment forward. So the dispatch validated in
   backcast is the dispatch forecast (#10), and the credit grows with DR enrollment
   forward.
4. **Wiring.** `ercot_reserve_coopt_inputs` (single lumped product) swaps the
   measured read for the selector; `ercot_multiproduct_reserve_coopt_inputs`
   (the run163/164 stack) now nets the credit off the **RRS** product's
   reserve-balance RHS, **after** the demand curve is sized to the gross
   requirement peak (so the steep tail is preserved — only the RHS drops). Both
   take an optional `sim_year` the runner threads from the evolving forecast year
   (defaults to `config.weather_year`; in backcast they coincide).

**Three supply credits compose without double count.** Load resources are neither
thermal/storage cleared reserve `R` nor part of RTOLCAP (the on-line **generation**
responsive capability the 300b89c cap bounds), so the RRS-requirement reduction sits
outside both the headroom rows and the cap. The endogenous storage AS (ea8c656) is a
distinct supply competing on the battery power cap. The three add — thermal headroom
(capped at RTOLCAP), storage AS (capped at RTOLCAP, which already includes online
batteries), load-resource RRS (requirement reduction, outside RTOLCAP) — with no
overlap (unit-tested `test_backcast_reduces_only_rrs_by_measured`).

## Honesty gate / validation

The enrollment forecast comes from a forward DR-enrollment trend, validated
**against** — never pinned **to** — the measured NP3-911 realization
(`scripts/probes/load_resource_rrs_split.py`):

| year | measured mean | enrolled fcst | fcst/meas |
|------|---------------|---------------|-----------|
| 2023 | 884 MW | 780 MW | 0.88x |
| 2024 | 904 MW | 840 MW | 0.93x |
| 2025 | 787 MW | 900 MW | 1.14x |

The monotonic enrollment trend reproduces the present ~0.86 GW level within
0.88–1.14x **without** tracking the year-to-year clearing wiggle (2025 dipped to
787 MW; the trend does not chase it). Forward it grows 960 → 1200 → 1400 MW
(2026 → 2030 → 2035), saturating at the protocol cap. Nothing reads the LMP, RTSPP,
MCPC or the measured cleared MW on the dispatch path forward. **Not retuned to the
broad-May residual** (that is the separate energy-base / merit-order track, per
`docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md`).

**Forward response:** DR enrollment grows → more load-side reserve supply → fewer
scarcity hours — automatic, no measured award needed.

## Tests (`tests/test_ercot_load_resource_rrs_forward.py`)

* `TestEnrollmentTrajectory` — anchor, linear growth, cap saturation, ~0.9 GW today.
* `TestAvailabilityShape` — mean exactly 1, length/tiling, daytime > overnight.
* `TestForwardCredit` — annual mean equals enrolled, grows with enrollment.
* `TestModeAwareSelector` — backcast byte-identical to measured; forecast = forward;
  year defaults to weather_year.
* `TestSingleProductCredit` / `TestMultiProductCredit` — the credit lowers the
  (RRS) reserve-balance RHS, leaves the demand curve and the other products
  untouched, and is byte-identical with the flag off.

All co-opt/scarcity/storage suites pass; every new parameter defaults off, so the
legacy and NYISO/PJM/MISO paths are byte-identical.

## Run / dashboard

`scripts/archive/run_165.py` = the run164 recipe + `ercot_load_resource_reserve=True`.
Solved 2023/2024/2025; the acute/tail incidence vs run164 and the
measured-vs-modeled load-resource RRS table are recorded on the backcast dashboard
(bundle `165`).
