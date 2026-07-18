# ERCOT Session 2 — within-gas merit order (ledgered) + grounded 2023 RTORDPA adder

**Date:** 2026-06-22. **Branch:** `claude/ercot-offer-curve-2023-adder-049nt9`
(off `main`). **Keeper baseline:** run143 / run143_redo re-baseline
(`results/calibration/run143_redo`, the local-30 outage re-solve).
**Reads:** `docs/ercot-offer-curve-merit-order-session-prompt.md`,
`docs/ercot-reserve-supply-scarcity-handoff-2026-06.md`,
`docs/ercot-run131-lmp-decomposition-2026-06.md`.

Two tracks, both grounded in measured ERCOT inputs, neither fit to a residual.

---

## TRACK 1 — the within-gas merit-order swap is the energy-only-LP limitation (LEDGERED)

**The miss (run143_redo, model vs grid-delivered EIA-923−BTM TWh).** The model
over-runs CC_REGULAR and under-runs ST_GAS + CT_PEAKER in all three years, worst
in the Apr/May/Oct shoulder; the CC over-run ≈ the ST_GAS+CT under-run (a
within-gas substitution, net gas family volume ~unchanged → C2 gas passes). It
FAILs C1 fuel-mix every year and is pre-existing (unchanged by the price-only
reserve-curve work).

### The decisive cheap check (no solve): the measured DAM offer stack

`scripts/probes/_ercot_offer_stack_meritorder.py` dumps the **measured** ERCOT
60-Day DAM Disclosure energy offers (Gen Resource Data → tidy via
`scripts/data/parse_ercot_dam_offers.py`) for CC vs ST_GAS vs CT_PEAKER, per-resource
median across resources, in the shoulder months, normalized both as raw $/MWh
and as the model's heat-rate-multiplier space. **The question the prompt poses:
do the measured offers order ST_GAS/CT below CC in the shoulder?**

**Shoulder (Apr/May/Oct) measured offer, per-resource median:**

| band | 2023 | 2024 (gas $2.19) | 2025 |
|---|---|---|---|
| **Min Gen ($/MWh)** | CC 15.7 ‹ CT 27.0 ‹ ST 52.0 | CC 7.3 ‹ CT 22.4 ‹ ST 47.1 | CC 20.2 ‹ CT 38.1 ‹ ST 71.0 |
| **econ_low ($/MWh)** | CC 14.0 ‹ CT 23.7 ‹ ST 34.2 | CC 12.3 ‹ CT 20.8 ‹ ST 24.8 | CC 19.5 ‹ CT 35.4 ‹ ST 58.3 |
| **econ_high ($/MWh)** | CC 23.0 ‹ CT 25.9 ‹ ST 39.4 | CC 20.8 ≈ CT 21.0 ‹ ST 78.0 | CC 27.4 ‹ CT 35.4 ‹ ST 164.7 |

**The measured offers order CC *cheapest* on energy at every band in every
year.** CC's lower heat rate (7.16 vs CT 10.65, ST 10.75 MMBtu/MWh) and lower VOM
make it structurally cheaper per MWh at *any* gas price — there is no gas price
at which the measured offers flip ST_GAS/CT below CC. So:

- **The energy-only LP is CORRECT to clear CC first.** Pushing ST_GAS/CT *below*
  the measured curve to force them on is a markup — barred by the run131 honesty
  gate. Re-ordering the merit stack with a measured offer change is impossible
  because the measured stack already has CC first.
- The model's effective CC bands (base+keeper deltas: committed 0.87, econ_low
  0.92, econ_high 1.21) sit at/above the measured CC multipliers
  (mingen 0.46, econ_low 0.93) except CC **econ_high** (model 1.21 vs measured
  ~1.68): the model marks the *top* of CC's curve slightly below measured. But
  even raising CC econ_high to the measured 1.68 (offer ≈ $28 at 2024 gas) keeps
  CC below CT econ_low ($29) and ST min-gen ($47); it cannot transfer the volume
  to ST/CT in an energy-only LP (the displaced MW go to other CC units' far
  cheaper econ_low), and it risks an LMP regression in the at-actual 2023/24
  shoulder. **Not the fix.**

### Conclusion — ledger, do not tune

The within-gas swap is the **energy-only-LP structural limitation**: real ST_GAS
and CT_PEAKER run at part-load for **local-reliability / AS / RUC commitment**
(CPS steamers, Cedar Bayou; non-CEMS small peakers — Ector County, Permian
Basin, Pearsall), which an energy-only zonal dispatch cannot see; the served
energy lands on the genuinely-cheapest unit (CC). This is the rubric's documented
CT_PEAKER limitation class. It is **ledgered as an ACCEPTED MEASURED-INPUT
LIMITATION** (`calibration_attestation.json`), not tuned away. The measured
offer-stack check above is the grounding the prompt's gate #1/#2 demand, now
reproduced for all three years (not just the suggested 2024 spot check).

C1 ledger entries: CC_REGULAR (2024/25), ST_GAS (2023/24/25), CT_PEAKER
(2023/24/25). Volumes are byte-identical to run143_redo (Track 2 is a post-solve
price overlay), so these stay the pre-existing FAILs, now reclassified CAVEAT.

---

## TRACK 2 — the grounded, backcast-able 2023 RTORDPA reliability-deployment adder

**Mechanism.** A regime-gated, post-solve, **additive** overlay that adds the
measured **`rtordpa`** (Real-Time ORDC + Reliability-Deployment Price Adder) to
the model system price. Implemented as
`market_sim.results.scarcity.ercot_rtordpa_overlay_series` + a `--ercot-rtordpa-overlay`
flag (`KEEPER_RTORDPA=1` on the keeper probe); the per-zone price in
`system.parquet` gets the gated adder and a `rtordpa_overlay` audit column.

- **Read per-year from the parquet, never a 2023 hard-code:**
  `data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet` column `rtordpa`
  (exogenous, NEVER fit to LMP). This is exactly what makes it backcast-able.
- **`rtordpa` ONLY, not `rtorpa`.** The co-opt already produces an ORDC adder
  ≈ RTORPA endogenously (the reserve-balance dual, the `reserve_price` column);
  `rtordpa` is the *reliability-deployment* component the model has no mechanism
  for, so adding it is additive, not double-counting (verified below).
- **Regime gate** keyed on the RTC+B go-live (2025-12-05, which retired the
  ORDC/RTORPA/RTORDPA adders): years ≤ 2024 fully pre-RTC+B; 2025 pre-RTC+B only
  through Dec 4 (hours ≥ `RTCB_GOLIVE_HOUR`=8112 zeroed — matching the measured
  series' own NaN tail); 2026+ RTC+B → overlay inert. NaN/missing → 0.

### Backcast-able-on-2022 proof (2022 NOT in the solve set)

`python scripts/data/fetch_ercot_ordc_reserves.py --years 2022` built
`data/raw/ercot/ercot_2022_ordc_reserves_hourly.parquet` (8760/8760 coverage,
rtordpa mean $1.7/h, max $1752). The overlay loader applies to 2022 **unchanged**
(demand-clock mean $1.73/h, 12 h>$200) with zero code change — proof the
mechanism generalizes. 2022 is validated as DATA only and is **not** added to the
solve set.

### Result — `results/calibration/run145_rtordpa` (registered `2026-06-22-run145-rtordpa-overlay`, PROBE)

3-year re-solve of the run143_redo recipe + the overlay. `system.parquet` carries
both the overlaid `price` and a raw `rtordpa_overlay` audit column, so base vs
overlay is recoverable from one solve
(`scripts/probes/_ercot_rtordpa_overlay_check.py`).

| year | avg base→overlay (actual) | h>$200 base→overlay (actual) | h>$500 base→overlay (actual) |
|---|---|---|---|
| 2023 | 35.2 → **35.9** (48.4) | 89 → **91** (181) | 51 → **53** (104) |
| 2024 | 25.4 → 25.6 (26.8) | 33 → 33 (53) | 23 → 23 (16) |
| 2025 | 32.5 → 32.9 (32.5) | 1 → 1 (31) | 0 → 0 (3) |

- **Additive, no double-count (verified).** Base = run143_redo exactly. The
  co-opt's endogenous ORDC adder (`reserve_price`, all-hours mean
  $12.4/$5.6/$0.03 for 2023/24/25) stands in for RTORPA (measured all-hours mean
  $0.95/$0.20/$0.07); `rtordpa` is the distinct reliability-deployment series
  overlaid on top.
- **The split, stated.** In the 181 actual-2023-tail hours the measured
  reserve-adder stack is rtorpa $36.7 + rtoffpa $26.4 + **rtordpa $21.7** = ~$85/h
  (the handoff's "$85"). The prompt scopes the overlay to **rtordpa only**
  (rtorpa ≈ the co-opt's own adder; rtoffpa is offline) — so it adds ~$21.7/h in
  the tail (demand-wtd $0.75/h annually), lifting 2023 toward actual. The
  residual (avg toward 48.4, tail toward 181) is the **energy-scarcity base
  (~$138/h)** — the separate, deferred **reserve-supply lever** (online RTOLCAP
  re-scope), plus the rtorpa/rtoffpa components the ORDC-only co-opt under-fires.
  The overlay does not paper over that base.
- **Near-inert in 2024/25 (confirmed).** +$0.23/+$0.37 on the average, tail
  unchanged — their measured rtordpa is tiny, so the regime-gated overlay is the
  intended no-op there.
- **C3 price improves at C1/C2 volume parity.** C3a 2023 −11.7%→−9.7%; C3b 2023
  NRMSE 0.399→0.371. Volumes byte-identical to run143_redo (post-solve overlay),
  so C1/C2 stay the pre-existing CAVEATs.

---

## Determination & gates

`scripts/calibration_verdict.py results/calibration/run145_rtordpa`:
**NOT-YET**, identical to the current ERCOT keeper
(`run144-local-band`): the caveat budget is exceeded by the two pre-existing
HARD caveats (C1 fuel-mix within-gas + C2 coal cheap-gas gradient), both now
ACCEPTED MEASURED-INPUT LIMITATIONs (not MODEL MISSes). No regression vs the
keeper; the Track-2 overlay improves the 2023 price criteria at volume parity,
and the Track-1 ledger is strengthened with the measured offer-stack grounding.

**Out of scope / parallel (unchanged):** the reserve-supply lever (online RTOLCAP
re-scope) owns the hollow P90–P99 band and the 2023 energy base; the 2024-Jan
winter-storm tail and the global storage-AS credit stay documented
(un-modelable / rejected).

## Reproduce

```bash
# Track 1 — measured offer-stack merit-order check (no solve):
python scripts/data/parse_ercot_dam_offers.py --input-dir data/raw/ercot \
  --glob '60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2024_*.parquet' \
  --output-dir data/raw/_processed-legacy --output-name ercot_dam_offers_2024.parquet
python scripts/probes/_ercot_offer_stack_meritorder.py \
  data/raw/_processed-legacy/ercot_dam_offers_2024.parquet

# Track 2 — 3-year re-baseline + regime-gated RTORDPA overlay (~13 min, sequential):
KEEPER_RTORDPA=1 python scripts/probes/_keeper_2023as_run.py run145_rtordpa 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
python scripts/probes/_ercot_lmp_shape_score.py results/calibration/run145_rtordpa
python scripts/probes/_ercot_rtordpa_overlay_check.py results/calibration/run145_rtordpa
python scripts/calibration_verdict.py results/calibration/run145_rtordpa

# Backcast-ability proof (DATA only — 2022 NOT in the solve set):
python scripts/data/fetch_ercot_ordc_reserves.py --years 2022
```

