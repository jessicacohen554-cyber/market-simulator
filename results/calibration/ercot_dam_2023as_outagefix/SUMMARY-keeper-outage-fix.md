# Keeper sidecar — ERCOT (run142): measured-2023 + outage-rule fix

**Bundle:** `ercot_dam_2023as_outagefix` · **Branch:** `claude/ercot-ordc-resfit-agj2i9`
Supersedes run139. run134 recipe + measured 2023 AS + two grounded fixes this
session: the CAMPD outage-rule revealed-availability filter and the ST_GAS
committed-offer restore.

## Headline (monthly LMP MAE, demand-weighted system price vs actual)

| year | run139 (prior) | **run142** | actual avg | run142 avg / tail |
|---|---|---|---|---|
| 2023 | 12.1 | **10.9** | 48.4 (181/104) | 37.6 (110/61) |
| 2024 | 13.2 | **8.9**  | 26.8 (53/16)   | 22.7 (21/14) |
| 2025 | 6.5  | **3.3**  | 32.5 (31/3)    | 31.1 (1/0) |
| mean | 10.6 | **7.7**  | | |

The Oct/Apr VOLL over-fire is gone (Oct-2024 $73.7/17 h>$200 → $25.4/3 h) while
real summer scarcity is preserved (Aug-2024 14 h>$200, max $5000; 2023 Aug $139).

## The two fixes

1. **CAMPD outage-rule revealed-availability filter** (`derive_campd_outages.py`,
   `derive_campd_unit_outages.py`). The CF<5% / event-based detectors cannot tell
   a mechanical outage from a dispatchable coal/CC unit sitting *economically
   idle* (out of merit in cheap-gas shoulder/winter months) and mislabel the
   second as the first — removing ~40-80 GW of available coal/CC in low-demand
   months (ERCOT 2024 Jan 77 / Apr 54 / Oct 40 GW), which the energy+reserve
   co-opt read as a reserve shortfall and priced to VOLL. This was the actual
   mechanism of the long-documented 2024/25 over-fire — **not** the ORDC curve,
   reserve credits, or seasonal LOLP (the NP6-576-ER table is flat). The fix
   keeps a down span as a real outage only if it overlaps the system's high-load
   band (≥ p85 of the year's *exogenous* historical demand, ≥24 h) — the unit was
   down when it would have been called. Economic-idle spans (low-load only) are
   dropped, leaving the unit available so the co-opt keeps it in the reserve
   pool. Summer binding outages survive (2024 Aug 19 GW unchanged); the false
   shoulder/winter mass is cut to ~summer levels. Signal = the model's own demand
   input → no circularity with the LMP, no price target fitted.

2. **ST_GAS committed-offer restore** (run141, adopted). The run134 cooldown set
   ST_GAS `committed=0.525` (half every other class), making gas-steam a baseload
   price-taker that ran 97% of hours and over-dispatched +27% (19 vs measured 15
   TWh) — an offer markup masking the over-fire. Restored to cost (~0.91): ST_GAS
   falls toward measured, the displaced energy goes to CC_REGULAR.

## Known tradeoffs / refinements (honest)

* **Thin tails.** The fix cools avg strongly but under-captures the mild tail
  (2024 21 vs actual 53 h>$200; 2025 1 vs 31). The MAE gate favors run142, but a
  less-aggressive percentile (p80) or a net-load signal would recover tail.
* **Annual-p85 under-weights winter.** Winter-storm hours fall below the
  summer-dominated annual p85, so winter outages are over-cut and the 2024 Jan
  storm is under-fired. A per-season percentile or net-load (load − wind − solar,
  which spikes in winter) is the recommended refinement.
* **2023 remains under** (37.6 vs 48.4) — structurally out-of-market (~42% of
  2023 $, run140); no ORDC lever reaches it. Summer tail preserved (Aug $139).
* **Cross-ISO.** The rule is shared; only ERCOT's outage CSVs were regenerated
  here. Other ISOs need their CSVs regenerated and keepers re-gated by owners.

## Provenance (measured, not fitted)

Measured 2023 storage AS 1.25 GW (`build_ercot_as_by_restype_from_60day.py`) +
load RRS-UFR 884 MW (`build_ercot_as_2023.py`, DAMASAGG-reconciled). ASPLAN AS
plan 2023 8.6 / 2024 7.6 / 2025 7.5 GW. VOLL/X/μσ/curve-shift/floors at published
values; `scarcity.py` un-fitted to price residuals.
